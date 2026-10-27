"""Model wrapper: mock modes, failures -> fallback, output check, call cap."""

import re
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import model_client

CTX = {"entry_choice": "tense", "prior_completed": 2}
FALLBACK = model_client.FALLBACKS["breathing"]


def test_mock_returns_fixture_text():
    result = model_client.acknowledge("breathing", CTX)
    assert result.status == "mock"
    assert result.role == "model"
    assert result.text == "You came in feeling tense and took seven slow breaths."


def test_mock_error_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock_error")
    result = model_client.acknowledge("breathing", CTX)
    assert (result.text, result.status, result.role) == (FALLBACK, "error", "fallback")


def test_mock_timeout_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock_timeout")
    monkeypatch.setattr(model_client, "TIMEOUT_S", 0.2)
    result = model_client.acknowledge("breathing", CTX)
    assert (result.text, result.status, result.role) == (FALLBACK, "timeout", "fallback")
    assert 150 <= result.latency_ms < 1000


def test_mock_malformed_rejected_by_output_check(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock_malformed")
    result = model_client.acknowledge("breathing", CTX)
    assert (result.text, result.status, result.role) == (FALLBACK, "fallback", "fallback")


def test_reframe_fallback_text(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock_error")
    result = model_client.acknowledge("reframe", {"text": "fictional"})
    assert result.text == "You've noted another way to look at it."


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        " ".join(["word"] * 31),
        "Did that help you breathe more slowly today?",
        "You took seven slow breaths!",
        "This can help with your anxiety disorder.",
        "You should do this every morning.",
        "Great job on finishing all seven breaths.",
        "I remember you came in tense last time.",
        "You completed seven paced breaths, adding to your three",
    ],
)
def test_check_output_rejects(text):
    assert model_client.check_output(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "You came in feeling tense and took seven slow breaths.",
        "Another way to see it: it may not be as certain as it feels.",
        " ".join(["word"] * 29) + " word.",
    ],
)
def test_check_output_accepts(text):
    assert model_client.check_output(text) is True


def test_live_success_records_latency(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    with patch.object(model_client, "_call_openrouter", return_value="You took seven slow breaths.") as call:
        result = model_client.acknowledge("breathing", CTX)
    call.assert_called_once()
    assert (result.status, result.role) == ("ok", "model")
    assert isinstance(result.latency_ms, int)


def test_live_exception_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    with patch.object(model_client, "_call_openrouter", side_effect=model_client.LLMRequestError("x")):
        result = model_client.acknowledge("breathing", CTX)
    assert (result.text, result.status) == (FALLBACK, "error")


def test_live_without_key_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_API_KEY", "")
    result = model_client.acknowledge("breathing", CTX)
    assert (result.text, result.status) == (FALLBACK, "error")


def test_max_calls_cap_switches_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_MAX_CALLS", "2")
    with patch.object(model_client, "_call_openrouter", return_value="You took seven slow breaths.") as call:
        statuses = [model_client.acknowledge("breathing", CTX).status for _ in range(4)]
    assert call.call_count == 2
    assert statuses == ["ok", "ok", "mock", "mock"]


def test_prompt_context_contains_only_the_planned_fields():
    messages = model_client.build_messages("breathing", CTX)
    user = messages[1]["content"]
    assert "tense or wound up" in user and "Earlier finished breathing sessions: 2" in user
    assert "Do not give advice" in messages[0]["content"]


def test_fallbacks_match_frontend_skills_js():
    skills_js = (Path(__file__).resolve().parents[2] / "frontend" / "src" / "content" / "skills.js").read_text()
    match = re.search(r"fallback: '([^']+)'", skills_js)
    assert match and match.group(1) == model_client.FALLBACKS["breathing"]


# Server-path fixes (docs/evidence/3.2/server-path-diagnosis.md)


class _KeepAliveStream:
    """Fake httpx.stream response: whitespace keep-alive bytes that never end,
    like OpenRouter while a slow model is still generating."""

    status_code = 200

    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        return None

    def iter_bytes(self):
        while True:
            time.sleep(0.05)
            yield b"\n         \n"


def test_call_is_abandoned_at_the_deadline_despite_keepalive_bytes(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test/model")
    monkeypatch.setattr(model_client, "TIMEOUT_S", 0.3)
    monkeypatch.setattr(model_client.httpx, "stream", _KeepAliveStream)
    started = time.perf_counter()
    with pytest.raises(model_client.LLMDeadlineError):
        model_client._call_openrouter([{"role": "user", "content": "x"}])
    assert time.perf_counter() - started < 0.6


def test_abandoned_slow_calls_do_not_delay_the_next_call(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setattr(model_client, "TIMEOUT_S", 0.3)
    replies = iter([None] * 5 + ["You took seven slow breaths."])

    def call(_messages):
        reply = next(replies)
        if reply is None:
            time.sleep(2.0)  # slow, abandoned by the app at 0.3 s
            return "You took seven slow breaths."
        return reply

    with patch.object(model_client, "_call_openrouter", side_effect=call):
        statuses = [model_client.acknowledge("breathing", CTX).status for _ in range(6)]
    assert statuses == ["timeout"] * 5 + ["ok"]


def test_reasoning_off_by_default_and_configurable(monkeypatch):
    msgs = [{"role": "user", "content": "x"}]
    assert model_client.build_payload("m", msgs)["reasoning"] == {"enabled": False}
    monkeypatch.setenv("LLM_REASONING", "on")
    assert "reasoning" not in model_client.build_payload("m", msgs)
