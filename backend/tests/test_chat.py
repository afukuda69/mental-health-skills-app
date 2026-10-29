"""Talk it through: persistence, crisis check first, failure modes, validator,
context privacy, schema migration, delete-all, and the call cap. Model mocked."""

import json
import sqlite3
from unittest.mock import patch

import pytest

import chat
import crisis
import db
import model_client
import sessions
from conftest import rows

VALID = '{"reply": "Paced breathing is 4 seconds in and 6 out, seven times.", "offer_skill": "breathing"}'


def _conv(client) -> int:
    return client.post("/api/conversations").json()["id"]


def _send(client, cid, text):
    return client.post(f"/api/conversations/{cid}/messages", json={"text": text})


# --- persistence ----------------------------------------------------------


def test_conversation_and_messages_persist(client):
    cid = _conv(client)
    data = _send(client, cid, "Fictional: nervous before a presentation").json()
    assert data["crisis"] is False
    assert data["user"]["text"] == "Fictional: nervous before a presentation"
    assert data["reply"]["role"] == "model" and data["reply"]["model_status"] == "mock"
    assert data["reply"]["offer_skill"] == "breathing"

    msgs = client.get(f"/api/conversations/{cid}/messages").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "model"]
    (listed,) = client.get("/api/conversations").json()["conversations"]
    assert listed["first_line"] == "Fictional: nervous before a presentation" and listed["message_count"] == 2
    assert rows("SELECT COUNT(*) AS n FROM messages WHERE conversation_id = ?", (cid,)) == [{"n": 2}]


def test_unknown_conversation_404(client):
    assert client.get("/api/conversations/999/messages").status_code == 404
    assert _send(client, 999, "hi").status_code == 404


# --- crisis check runs before the model ----------------------------------


def test_crisis_phrase_scripted_reply_no_model_call_text_not_stored(client):
    cid = _conv(client)
    with patch.object(model_client, "chat_reply") as reply, patch.object(model_client, "_call_openrouter") as live:
        data = _send(client, cid, "Fictional test phrase: I want to die").json()
    reply.assert_not_called()
    live.assert_not_called()
    assert data["crisis"] is True and data["reply"]["text"] == crisis.SCRIPTED_REPLY
    stored = rows("SELECT role, text, model_status, crisis_flag FROM messages ORDER BY id")
    assert stored == [
        {"role": "user", "text": None, "model_status": None, "crisis_flag": 1},
        {"role": "scripted", "text": crisis.SCRIPTED_REPLY, "model_status": "scripted", "crisis_flag": 1},
    ]
    assert "want to die" not in json.dumps(rows("SELECT * FROM messages"))


# --- every failure mode gives the fixed fallback -------------------------


@pytest.mark.parametrize(
    ("env", "status"),
    [
        ({"LLM_MODE": "mock_error"}, "error"),
        ({"LLM_MODE": "mock_timeout"}, "timeout"),
        ({"LLM_MODE": "mock_malformed"}, "fallback"),
        ({"LLM_MOCK_CHAT": "malformed"}, "fallback"),
        ({"LLM_MOCK_CHAT": "overlong"}, "fallback"),
        ({"LLM_MOCK_CHAT": "banned"}, "fallback"),
    ],
)
def test_chat_failures_fall_back(client, monkeypatch, env, status):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(model_client, "TIMEOUT_S", 0.2)
    cid = _conv(client)
    reply = _send(client, cid, "Fictional: what is STOP for").json()["reply"]
    assert reply["text"] == model_client.CHAT_FALLBACK
    assert (reply["role"], reply["model_status"], reply["offer_skill"]) == ("fallback", status, None)


def test_mock_normal_and_offer_fixtures(client, monkeypatch):
    cid = _conv(client)
    monkeypatch.setenv("LLM_MOCK_CHAT", "normal")
    assert _send(client, cid, "hello").json()["reply"]["offer_skill"] is None
    monkeypatch.setenv("LLM_MOCK_CHAT", "offer")
    assert _send(client, cid, "hello").json()["reply"]["offer_skill"] == "breathing"


# --- validator -----------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "Paced breathing is 4 in and 6 out.",
        '{"text": "no reply key."}',
        '{"reply": "Fine.", "offer_skill": "grounding"}',
        json.dumps({"reply": " ".join(["word"] * 61) + ".", "offer_skill": None}),
        '{"reply": "You did it!", "offer_skill": null}',
        '{"reply": "This sounds like a disorder.", "offer_skill": null}',
        '{"reply": "You should try therapy.", "offer_skill": null}',
        '{"reply": "Paced breathing is four seconds in and", "offer_skill": null}',
    ],
)
def test_check_chat_output_rejects(raw):
    assert model_client.check_chat_output(raw) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (VALID, ("Paced breathing is 4 seconds in and 6 out, seven times.", "breathing")),
        ('{"reply": "Would you like to hear how STOP works?", "offer_skill": null}', ("Would you like to hear how STOP works?", None)),
        ('```json\n{"reply": "STOP has four short prompts.", "offer_skill": "stop"}\n```', ("STOP has four short prompts.", "stop")),
        (json.dumps({"reply": " ".join(["word"] * 59) + " end.", "offer_skill": "reframe"}), (" ".join(["word"] * 59) + " end.", "reframe")),
    ],
)
def test_check_chat_output_accepts(raw, expected):
    assert model_client.check_chat_output(raw) == expected


# --- context sent to the model -------------------------------------------


def test_model_context_is_prompt_skills_counts_and_last_ten(client):
    for i, reason in enumerate(["completed", "completed", "stopped"]):
        sessions.create_session(f"b{i}", "breathing" if i < 2 else "stop")
        sessions.end_session(f"b{i}", reason)
    s = sessions.create_session("rf", "reframe")
    sessions.add_message(s["id"], "model", "FICTIONAL-ACK-TEXT", "mock", 1)

    cid = _conv(client)
    for i in range(12):
        _send(client, cid, f"fictional message {i}")
    with patch.object(model_client, "chat_reply", wraps=model_client.chat_reply) as reply:
        _send(client, cid, "fictional last message")
    sent = reply.call_args.args[0]

    assert sent[0]["content"] == model_client.CHAT_SYSTEM_PROMPT
    context = sent[1]["content"]
    for line in ("breathing: Paced breathing.", "stop: STOP.", "reframe: Cognitive reframe."):
        assert line in context
    assert "Usual skill: Paced breathing [breathing], learned." in context
    assert "Sessions: Paced breathing 2 completed; STOP 1 stopped." in context
    assert len(sent) == 2 + 10
    assert sent[-1] == {"role": "user", "content": "fictional last message"}
    assert "FICTIONAL-ACK-TEXT" not in json.dumps(sent)


def test_history_summary_has_counts_only():
    s = sessions.create_session("x", "reframe")
    sessions.end_session("x", "completed")
    sessions.add_message(s["id"], "model", "FICTIONAL-PRIVATE-TEXT", "mock", 1)
    summary = sessions.history_summary()
    assert summary == "reframe x1 completed"
    assert "FICTIONAL" not in summary


# --- STOP and reframe sessions -------------------------------------------


def test_stop_and_reframe_sessions_record_like_breathing(client):
    client.post("/api/sessions", json={"client_id": "st", "skill": "stop", "planned_ms": 60000, "steps_planned": 4})
    client.post("/api/sessions/st/end", json={"end_reason": "completed", "measured_ms": 58200, "pauses_ms": 0, "crisis_ms": 4100, "steps_completed": 4})
    client.post("/api/sessions", json={"client_id": "rf", "skill": "reframe", "planned_ms": 70000, "steps_planned": 4})
    client.post("/api/sessions/rf/end", json={"end_reason": "stopped", "measured_ms": 9100, "pauses_ms": 2000, "crisis_ms": 0, "steps_completed": 1})
    got = rows("SELECT skill, end_reason, planned_ms, measured_ms, crisis_ms, pauses_ms, steps_planned, steps_completed FROM sessions ORDER BY id")
    assert got == [
        {"skill": "stop", "end_reason": "completed", "planned_ms": 60000, "measured_ms": 58200, "crisis_ms": 4100, "pauses_ms": 0, "steps_planned": 4, "steps_completed": 4},
        {"skill": "reframe", "end_reason": "stopped", "planned_ms": 70000, "measured_ms": 9100, "crisis_ms": 0, "pauses_ms": 2000, "steps_planned": 4, "steps_completed": 1},
    ]
    assert client.get("/api/usual").json() == {"skill": "stop", "source": "learned"}


# --- delete all ----------------------------------------------------------


def test_delete_all_history(client):
    client.post("/api/sessions", json={"client_id": "d1", "skill": "breathing"})
    client.post("/api/sessions/d1/acknowledgment")
    client.post("/api/sessions/d1/feedback", json={"rating": "helped"})
    _send(client, _conv(client), "fictional")
    res = client.delete("/api/history").json()
    assert res["deleted"] == {"sessions": 1, "messages": 3, "feedback": 1, "conversations": 1}
    for table in ("sessions", "messages", "feedback", "conversations"):
        assert rows(f"SELECT COUNT(*) AS n FROM {table}") == [{"n": 0}]
    assert client.get("/api/history").json() == {"sessions": [], "conversations": []}


# --- call cap ------------------------------------------------------------


def test_chat_call_cap_switches_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_MAX_CALLS", "2")
    msgs = [{"role": "user", "content": "fictional"}]
    with patch.object(model_client, "_call_openrouter", return_value=VALID) as call:
        statuses = [model_client.chat_reply(msgs).status for _ in range(4)]
    assert call.call_count == 2
    assert statuses == ["ok", "ok", "mock", "mock"]


# --- schema migration from Part 3.2 ---------------------------------------

SCHEMA_3_2 = """
CREATE TABLE sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL UNIQUE, skill TEXT NOT NULL,
  entry_choice TEXT, started_at TEXT NOT NULL, ended_at TEXT, completed INTEGER NOT NULL DEFAULT 0,
  exited_early INTEGER NOT NULL DEFAULT 0, end_reason TEXT, setup_ms INTEGER, planned_ms INTEGER, measured_ms INTEGER,
  pauses_ms INTEGER, crisis_ms INTEGER, steps_planned INTEGER, steps_completed INTEGER);
CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL REFERENCES sessions(id),
  role TEXT NOT NULL, text TEXT, model_status TEXT, latency_ms INTEGER, crisis_flag INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL);
CREATE TABLE feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL REFERENCES sessions(id), rating TEXT NOT NULL);
INSERT INTO sessions (client_id, skill, started_at, end_reason, completed, measured_ms) VALUES ('old', 'breathing', '2026-10-27T16:27:46Z', 'completed', 1, 71124);
INSERT INTO messages (session_id, role, text, model_status, latency_ms, created_at) VALUES (1, 'model', 'You took a minute for seven slow breaths.', 'mock', 1, '2026-10-27T16:28:47Z');
INSERT INTO feedback (session_id, rating) VALUES (1, 'helped');
"""


def test_migrates_a_3_2_database_keeping_rows(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_3_2)
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", path)

    db.init_db()
    db.init_db()  # idempotent

    assert rows("PRAGMA user_version") == [{"user_version": 1}]
    assert rows("SELECT client_id, measured_ms FROM sessions") == [{"client_id": "old", "measured_ms": 71124}]
    assert rows("SELECT session_id, conversation_id, text, offer_skill FROM messages") == [
        {"session_id": 1, "conversation_id": None, "text": "You took a minute for seven slow breaths.", "offer_skill": None}
    ]
    assert rows("SELECT rating FROM feedback") == [{"rating": "helped"}]
    assert chat.create_conversation()["id"] == 1
    assert sessions.get_usual_skill() == "breathing"
