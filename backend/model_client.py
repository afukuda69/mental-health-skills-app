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
import re
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


def _invoke(mode: str, live_messages: list[dict], mock_fn, *mock_args) -> tuple[str | None, str | None, int]:
    """Run one model call (live or mock) under the 5 s wall-clock limit.

    Returns (raw_text, failure_status, latency_ms). failure_status is None on
    success, else "timeout" or "error". Never raises.
    """
    global _live_calls
    if mode == "live":
        _live_calls += 1
        future = _run_in_thread(_call_openrouter, live_messages)
    else:
        future = _run_in_thread(mock_fn, *mock_args)
    started = time.perf_counter()
    try:
        raw = future.result(timeout=TIMEOUT_S)
    except (FutureTimeout, LLMDeadlineError):
        log.warning("model call timed out after %.1f s (mode=%s)", TIMEOUT_S, mode)
        return None, "timeout", int((time.perf_counter() - started) * 1000)
    except Exception as exc:  # any failure must fall back, never surface
        log.warning("model call failed (mode=%s): %s", mode, type(exc).__name__)
        return None, "error", int((time.perf_counter() - started) * 1000)
    return raw, None, int((time.perf_counter() - started) * 1000)


def acknowledge(skill: str, context: dict) -> AckResult:
    """Return text to show in the acknowledgment slot. Never raises."""
    fallback = FALLBACKS.get(skill, FALLBACKS["breathing"])
    mode = _effective_mode()
    raw, failure, latency_ms = _invoke(mode, build_messages(skill, context), _mock_reply, skill, context, mode)
    if failure:
        return AckResult(fallback, failure, latency_ms, "fallback")

    text = (raw or "").strip()
    if not check_output(text):
        log.info("model output rejected by check_output (mode=%s)", mode)
        return AckResult(fallback, "fallback", latency_ms, "fallback")
    return AckResult(text, "ok" if mode == "live" else "mock", latency_ms, "model")


# --- "Talk it through" chat -------------------------------------------------

CHAT_MAX_WORDS = 60
OFFERABLE = {"breathing", "stop", "reframe"}

# Shown when the chat model fails, times out, returns unusable output, or the
# call cap is reached. The frontend adds links to the three skills under it.
CHAT_FALLBACK = (
    "I can't give a useful reply to that here. This is a coursework prototype and can't assess anything. "
    "You can try one of the skills below."
)

# Separate from BANNED: the chat may ask questions and explain the skills, but
# must not diagnose, prescribe, cheer, or claim to monitor or remember anyone.
CHAT_BANNED = [
    "diagnos", "disorder", "therapy", "therapist", "treatment", "symptom", "clinical",
    "medication", "you should", "you must", "great job", "well done", "amazing",
    "proud of you", "i'm always here", "i am always here", "i remember", "watching over",
    "monitor", "i will keep track",
]

CHAT_SYSTEM_PROMPT = (
    "You are the optional chat in a coursework prototype app that guides three short self-guided skills. "
    "This is not therapy, diagnosis, or a support service, and nobody monitors it. Users are asked to use fictional scenarios. "
    "Answer in plain, calm, non-clinical language, at most 60 words. You may ask one short question. "
    "Only describe the three skills as given below. Never invent techniques, add steps, or change their steps or timing. "
    "Never diagnose, never mention disorders, therapy, or medication, never praise or cheer, never use exclamation marks, "
    "and never claim to remember, watch over, or monitor the user. "
    "If one skill fits what the user describes, you may offer it; the user decides. "
    'Reply with JSON only: {"reply": "<text>", "offer_skill": "breathing" | "stop" | "reframe" | null}.'
)


@dataclass
class ChatResult:
    reply: str
    offer_skill: str | None
    status: str  # ok | mock | fallback | error | timeout
    latency_ms: int | None
    role: str  # model | fallback


def check_chat_output(raw: str | None) -> tuple[str, str | None] | None:
    """Parse and validate a chat reply. Returns (reply, offer_skill) or None."""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("reply"), str):
        return None
    reply = data["reply"].strip()
    offer = data.get("offer_skill")
    if offer not in OFFERABLE and offer is not None:
        return None
    if not reply or len(reply.split()) > CHAT_MAX_WORDS or "!" in reply:
        return None
    if not reply.rstrip("\"'").endswith((".", "?")):
        return None  # likely cut off by the token limit
    lowered = reply.lower()
    if any(word in lowered for word in CHAT_BANNED):
        return None
    return reply, offer


def build_chat_messages(skills: list[dict], profile_summary: str, recent: list[dict]) -> list[dict]:
    """System prompt + skill lines + profile summary + the last 10 messages of this conversation."""
    skill_lines = "\n".join(f"- {s['id']}: {s['label']}. {s['purpose']}" for s in skills)
    context = (
        f"The three skills:\n{skill_lines}\n\n"
        f"About this user, from the local profile (no message text): {profile_summary or 'nothing yet'}"
    )
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "system", "content": context},
    ]
    for m in recent[-10:]:
        messages.append({"role": "user" if m["role"] == "user" else "assistant", "content": m["text"]})
    return messages


def _mock_chat(messages: list[dict], mode: str) -> str:
    fixtures = _load_fixtures()["chat"]
    if mode == "mock_error":
        raise LLMRequestError("Simulated model error (LLM_MODE=mock_error)")
    if mode == "mock_timeout":
        time.sleep(TIMEOUT_S + 1.0)
        return fixtures["normal"]
    if mode == "mock_malformed":
        return fixtures["malformed"]
    choice = (config.get_mock_chat() or "auto").lower()
    if choice not in fixtures or choice == "_note":
        last = messages[-1]["content"].lower() if messages else ""
        if any(k in last for k in ("diagnos", "do i have", "anxiety", "depress", "disorder")):
            choice = "banned"  # the validator rejects it, so the limit fallback shows
        elif any(k in last for k in ("presentation", "nervous", "exam", "help", "suggest", "what should")):
            choice = "offer"
        else:
            choice = "normal"
    return _tailor(fixtures[choice], messages)


def _tailor(raw: str, messages: list[dict]) -> str:
    """Fill a mock reply with the name and usual skill from the profile summary,
    so mock mode shows the same tailoring a live model is asked for."""
    context = messages[1]["content"] if len(messages) > 1 else ""
    name = re.search(r"Name: (?!not given)([^.]+)\.", context)
    usual = re.search(r"Usual skill: (.+?) \[(\w+)\]", context)
    if not usual:  # a new user has no usual skill; don't claim one
        raw = raw.replace("Your usual skill here is <<USUAL>>. I can explain it or either of the other two skills.", "I can explain any of the three skills.")
        raw = raw.replace("your usual skill, <<USUAL>>,", "<<USUAL>>")
    return (
        raw.replace("<<HELLO>>", f"Hi {name.group(1)}. " if name else "")
        .replace("<<USUAL>>", usual.group(1) if usual else "Paced breathing")
        .replace("<<USUAL_ID>>", usual.group(2) if usual else "breathing")
    )


def chat_reply(messages: list[dict]) -> ChatResult:
    """One chat turn. Never raises; any failure gives CHAT_FALLBACK."""
    mode = _effective_mode()
    raw, failure, latency_ms = _invoke(mode, messages, _mock_chat, messages, mode)
    if failure:
        return ChatResult(CHAT_FALLBACK, None, failure, latency_ms, "fallback")
    parsed = check_chat_output(raw)
    if parsed is None:
        log.info("chat output rejected by check_chat_output (mode=%s)", mode)
        return ChatResult(CHAT_FALLBACK, None, "fallback", latency_ms, "fallback")
    reply, offer = parsed
    return ChatResult(reply, offer, "ok" if mode == "live" else "mock", latency_ms, "model")
