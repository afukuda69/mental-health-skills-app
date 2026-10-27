"""The single wrapper around the language model.

Adapted from travel-application/backend/chat.py::_call_openrouter (httpx,
config from .env, typed errors). Changes for this app (docs/design.md
section e):
- a hard 5 s wall-clock timeout. OpenRouter sends headers and keep-alive
  whitespace early, so httpx's per-read timeout never fires on a slow model;
  the response is streamed and abandoned at the deadline instead
- each call runs on its own thread, so a slow abandoned call never delays
  the next one (docs/evidence/3.2/server-path-diagnosis.md)
- reasoning is turned off by default (LLM_REASONING=on restores it)
- an output check; the prompt alone is not trusted
- any failure returns fixed fallback text instead of an error
- mock modes that simulate success and each failure deterministically
- a cap on live calls per server process (LLM_MAX_CALLS), then mock
"""

import json
import logging
import threading
import time
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from pathlib import Path

import httpx

import config

log = logging.getLogger("model_client")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_S = 5.0
MAX_WORDS = 30

FIXTURES_PATH = Path(__file__).resolve().parent / "tests" / "fixtures" / "mock_responses.json"

# Must match the fallback strings in frontend/src/content/skills.js
# (tests/test_model_client.py checks this).
FALLBACKS = {
    "breathing": "That was seven slow breaths.",
    "reframe": "You've noted another way to look at it.",
}

ENTRY_LABELS = {
    "tense": "tense or wound up",
    "overwhelmed": "overwhelmed",
    "okay": "okay, just wanting a minute",
}

# Lower-case substrings that make an output unusable. Short on purpose; the
# word-count and punctuation checks do most of the work.
BANNED = [
    "diagnos", "disorder", "therapy", "therapist", "treat", "symptom", "clinical",
    "anxiety", "depress", "you should", "you must", "you need to", "try to",
    "great job", "well done", "amazing", "proud of you", "i'm here", "i am here",
    "i remember", "watching", "monitor",
]

SYSTEM_PROMPT = (
    "You write one short acknowledgment for a self-guided exercise app. "
    "Write one or two plain sentences, 30 words at most, in a calm, neutral tone. "
    "Only acknowledge or reflect what the user did or wrote. "
    "Do not give advice, instructions, or new steps. Do not ask questions. "
    "Do not use clinical or diagnostic words, and do not mention therapy. "
    "Do not praise or cheer. Do not use exclamation marks. "
    "Do not say you remember the user or that anyone is watching over them."
)


class LLMNotConfiguredError(Exception):
    """LLM_API_KEY or LLM_MODEL is not set."""


class LLMRequestError(Exception):
    """Network error, non-2xx status, or an unusable response body."""


class LLMDeadlineError(Exception):
    """The response was still arriving when the wall-clock deadline passed."""


@dataclass
class AckResult:
    text: str
    status: str  # ok | mock | fallback | error | timeout
    latency_ms: int | None
    role: str  # model | fallback


_live_calls = 0


def _run_in_thread(fn, *args) -> Future:
    """Run fn on its own daemon thread. A shared pool let abandoned slow calls
    hold every worker, so later calls queued and spent their 5 s waiting."""
    future: Future = Future()

    def run():
        try:
            future.set_result(fn(*args))
        except BaseException as exc:
            future.set_exception(exc)

    threading.Thread(target=run, daemon=True).start()
    return future


def reset_live_call_count() -> None:
    global _live_calls
    _live_calls = 0


def live_call_count() -> int:
    return _live_calls


def check_output(text: str | None) -> bool:
    """True if the model text may be shown to the user."""
    if not text or not text.strip():
        return False
    if len(text.split()) > MAX_WORDS:
        return False
    if "?" in text or "!" in text:
        return False
    # A reply cut off by the token limit can pass every other check
    # (docs/evidence/3.2/live-latency-run1.txt, call 3).
    if not text.rstrip().endswith((".", '."', ".'")):
        return False
    lowered = text.lower()
    return not any(word in lowered for word in BANNED)


def build_messages(skill: str, context: dict) -> list[dict]:
    if skill == "breathing":
        entry = ENTRY_LABELS.get(context.get("entry_choice") or "", "not given")
        user = (
            "Exercise: paced breathing, seven slow breaths. "
            f"How the user said they were at the start: {entry}. "
            "They finished the exercise. "
            f"Earlier finished breathing sessions: {int(context.get('prior_completed', 0))}."
        )
    else:
        user = (
            "Briefly reflect back this alternative way of seeing a thought, "
            f"in the user's own terms: {context.get('text', '')}"
        )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def build_payload(model: str, messages: list[dict]) -> dict:
    payload = {"model": model, "messages": messages, "temperature": 0, "max_tokens": 300}
    if not config.get_llm_reasoning():
        # One plain sentence needs no reasoning; it was ~85% of output tokens.
        payload["reasoning"] = {"enabled": False}
    return payload


def _call_openrouter(messages: list[dict]) -> str:
    api_key = config.get_llm_api_key()
    model = config.get_llm_model()
    if not api_key or not model:
        raise LLMNotConfiguredError("LLM_API_KEY or LLM_MODEL is not configured")
    deadline = time.perf_counter() + TIMEOUT_S
    try:
        with httpx.stream(
            "POST",
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=build_payload(model, messages),
            timeout=TIMEOUT_S,
        ) as response:
            response.raise_for_status()
            body = b""
            for chunk in response.iter_bytes():
                body += chunk
                if time.perf_counter() > deadline:
                    raise LLMDeadlineError("Response still arriving at the deadline")
        return json.loads(body)["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        raise LLMRequestError("Model request failed or returned an unusable response") from None


def _load_fixtures() -> dict:
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def _mock_reply(skill: str, context: dict, mode: str) -> str:
    fixtures = _load_fixtures()[skill]
    if mode == "mock_error":
        raise LLMRequestError("Simulated model error (LLM_MODE=mock_error)")
    if mode == "mock_timeout":
        time.sleep(TIMEOUT_S + 1.0)
        return fixtures["ok"] if isinstance(fixtures["ok"], str) else fixtures["ok"]["default"]
    if mode == "mock_malformed":
        return fixtures["malformed"]
    ok = fixtures["ok"]
    if isinstance(ok, str):
        return ok
    return ok.get(context.get("entry_choice") or "", ok["default"])


def _effective_mode() -> str:
    mode = config.get_llm_mode()
    if mode == "live" and _live_calls >= config.get_llm_max_calls():
        log.warning("LLM_MAX_CALLS (%s) reached: using mock replies", config.get_llm_max_calls())
        return "mock"
    return mode


def acknowledge(skill: str, context: dict) -> AckResult:
    """Return text to show in the acknowledgment slot. Never raises."""
    global _live_calls
    fallback = FALLBACKS.get(skill, FALLBACKS["breathing"])
    mode = _effective_mode()

    if mode == "live":
        _live_calls += 1
        future = _run_in_thread(_call_openrouter, build_messages(skill, context))
    else:
        future = _run_in_thread(_mock_reply, skill, context, mode)

    started = time.perf_counter()
    try:
        raw = future.result(timeout=TIMEOUT_S)
    except (FutureTimeout, LLMDeadlineError):
        log.warning("model call timed out after %.1f s (mode=%s)", TIMEOUT_S, mode)
        return AckResult(fallback, "timeout", int((time.perf_counter() - started) * 1000), "fallback")
    except Exception as exc:  # any failure must fall back, never surface
        log.warning("model call failed (mode=%s): %s", mode, type(exc).__name__)
        return AckResult(fallback, "error", int((time.perf_counter() - started) * 1000), "fallback")
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = (raw or "").strip()
    if not check_output(text):
        log.info("model output rejected by check_output (mode=%s)", mode)
        return AckResult(fallback, "fallback", latency_ms, "fallback")
    return AckResult(text, "ok" if mode == "live" else "mock", latency_ms, "model")
