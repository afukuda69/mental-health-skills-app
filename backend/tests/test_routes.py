"""Route-level tests through FastAPI's TestClient. Model always mocked."""

import json
from unittest.mock import patch

import crisis
import model_client
from conftest import rows


def _start(client, cid="r1", **kw):
    body = {"client_id": cid, "skill": "breathing", "entry_choice": "overwhelmed", "planned_ms": 75000, "steps_planned": 7}
    body.update(kw)
    assert client.post("/api/sessions", json=body).status_code == 200


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_end_accepts_beacon_text_plain_body(client):
    _start(client)
    res = client.post(
        "/api/sessions/r1/end",
        content=json.dumps({"end_reason": "left", "measured_ms": 12000, "pauses_ms": 0, "crisis_ms": 0}),
        headers={"Content-Type": "text/plain"},
    )
    assert res.status_code == 200
    assert rows("SELECT end_reason, measured_ms FROM sessions") == [{"end_reason": "left", "measured_ms": 12000}]


def test_end_rejects_bad_reason_and_unknown_session(client):
    _start(client)
    assert client.post("/api/sessions/r1/end", json={"end_reason": "nope"}).status_code == 422
    assert client.post("/api/sessions/zzz/end", json={"end_reason": "completed"}).status_code == 404


def test_acknowledgment_saves_message(client):
    _start(client)
    data = client.post("/api/sessions/r1/acknowledgment").json()
    assert data["status"] == "mock" and data["crisis"] is False
    (msg,) = rows("SELECT role, text, model_status, crisis_flag FROM messages")
    assert msg == {"role": "model", "text": data["text"], "model_status": "mock", "crisis_flag": 0}


def test_acknowledgment_failure_saves_fallback_row(client, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock_error")
    _start(client)
    data = client.post("/api/sessions/r1/acknowledgment").json()
    assert data["text"] == model_client.FALLBACKS["breathing"]
    assert rows("SELECT role, model_status FROM messages") == [{"role": "fallback", "model_status": "error"}]


def test_acknowledgment_context_counts_prior_completed(client):
    for cid in ("p1", "p2"):
        _start(client, cid)
        client.post(f"/api/sessions/{cid}/end", json={"end_reason": "completed"})
    _start(client, "p3")
    with patch.object(model_client, "acknowledge", wraps=model_client.acknowledge) as ack:
        client.post("/api/sessions/p3/acknowledgment")
    assert ack.call_args.args[1] == {"entry_choice": "overwhelmed", "prior_completed": 2}


def test_no_model_call_after_stop(client):
    _start(client)
    client.post("/api/sessions/r1/end", json={"end_reason": "stopped"})
    with patch.object(model_client, "acknowledge") as ack:
        assert client.post("/api/sessions/r1/acknowledgment").status_code == 409
    ack.assert_not_called()


def test_reframe_reflection_stores_no_text(client):
    _start(client, skill="reframe")
    data = client.post("/api/sessions/r1/reflection", json={"text": "Fictional: the meeting might go fine"}).json()
    assert data["crisis"] is False and data["status"] == "mock"
    assert data["text"] == "Another way to see it: it may not be as certain as it feels."
    msgs = rows("SELECT role, text, model_status, crisis_flag FROM messages")
    assert msgs == [{"role": "model", "text": None, "model_status": "mock", "crisis_flag": 0}]
    assert "meeting" not in str(rows("SELECT * FROM messages"))


def test_reframe_reflection_sends_only_the_given_text_to_the_model(client):
    _start(client, skill="reframe")
    with patch.object(model_client, "acknowledge", wraps=model_client.acknowledge) as ack:
        client.post("/api/sessions/r1/reflection", json={"text": "Fictional: maybe it went fine"})
    assert ack.call_args.args == ("reframe", {"text": "Fictional: maybe it went fine"})


def test_crisis_phrase_scripted_reply_without_model_call(client):
    _start(client, skill="reframe")
    with patch.object(model_client, "acknowledge") as ack, patch.object(model_client, "_call_openrouter") as live:
        data = client.post("/api/sessions/r1/reflection", json={"text": "Fictional test: I want to die"}).json()
    ack.assert_not_called()
    live.assert_not_called()
    assert data == {"text": crisis.SCRIPTED_REPLY, "status": "scripted", "latency_ms": None, "crisis": True}
    msgs = rows("SELECT role, text, model_status, crisis_flag FROM messages ORDER BY id")
    assert msgs == [{"role": "scripted", "text": None, "model_status": "scripted", "crisis_flag": 1}]


def test_history_and_usual(client):
    _start(client)
    client.post("/api/sessions/r1/acknowledgment")
    client.post("/api/sessions/r1/end", json={"end_reason": "completed", "measured_ms": 75400})
    client.post("/api/sessions/r1/feedback", json={"rating": "helped"})

    (item,) = client.get("/api/history").json()["sessions"]
    assert item["end_reason"] == "completed" and item["rating"] == "helped"
    assert item["messages"][0]["role"] == "model"
    assert client.get("/api/usual").json() == {"skill": "breathing", "source": "learned"}


def test_feedback_validation(client):
    _start(client)
    assert client.post("/api/sessions/r1/feedback", json={"rating": "great"}).status_code == 422
    assert client.post("/api/sessions/nope/feedback", json={"rating": "helped"}).status_code == 404
