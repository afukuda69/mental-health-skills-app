"""Session persistence, end reasons, feedback, history, and usual-skill derivation."""

import pytest

import sessions
from conftest import rows


def _start(cid, skill="breathing", **kw):
    return sessions.create_session(cid, skill, planned_ms=75000, steps_planned=7, **kw)


def test_create_and_complete_persists_timing():
    _start("s1", entry_choice="tense", setup_ms=6200)
    sessions.end_session("s1", "completed", measured_ms=76120, pauses_ms=0, crisis_ms=0, steps_completed=7)

    (row,) = rows("SELECT * FROM sessions WHERE client_id = 's1'")
    assert row["entry_choice"] == "tense"
    assert row["setup_ms"] == 6200
    assert row["planned_ms"] == 75000
    assert row["measured_ms"] == 76120
    assert row["steps_planned"] == 7 and row["steps_completed"] == 7
    assert row["end_reason"] == "completed"
    assert row["completed"] == 1 and row["exited_early"] == 0
    assert row["started_at"] and row["ended_at"]


@pytest.mark.parametrize("reason", ["stopped", "left"])
def test_early_end_reasons(reason):
    _start("s2")
    sessions.end_session("s2", reason, measured_ms=21000, pauses_ms=3000, crisis_ms=4000, steps_completed=1)

    (row,) = rows("SELECT * FROM sessions WHERE client_id = 's2'")
    assert row["end_reason"] == reason
    assert row["completed"] == 0 and row["exited_early"] == 1
    assert (row["measured_ms"], row["pauses_ms"], row["crisis_ms"]) == (21000, 3000, 4000)


@pytest.mark.parametrize("final", ["completed", "stopped"])
def test_left_never_overwrites_a_final_reason(final):
    _start("s3")
    sessions.end_session("s3", final, measured_ms=75500)
    sessions.end_session("s3", "left", measured_ms=99999)

    (row,) = rows("SELECT end_reason, measured_ms FROM sessions WHERE client_id = 's3'")
    assert row == {"end_reason": final, "measured_ms": 75500}


def test_completed_overwrites_left_after_returning_to_tab():
    _start("s4")
    sessions.end_session("s4", "left", measured_ms=30000)
    sessions.end_session("s4", "completed", measured_ms=75300)

    (row,) = rows("SELECT end_reason, completed FROM sessions WHERE client_id = 's4'")
    assert row == {"end_reason": "completed", "completed": 1}


def test_create_is_idempotent_on_client_id():
    _start("s5")
    _start("s5")
    assert len(rows("SELECT id FROM sessions WHERE client_id = 's5'")) == 1


def test_unknown_end_reason_rejected():
    _start("s6")
    with pytest.raises(ValueError):
        sessions.end_session("s6", "abandoned")


def test_end_unknown_session_returns_none():
    assert sessions.end_session("missing", "completed") is None


def test_feedback_one_per_session():
    s = _start("s7")
    sessions.set_feedback("s7", "didnt_help")
    sessions.set_feedback("s7", "helped")
    assert rows("SELECT rating FROM feedback WHERE session_id = ?", (s["id"],)) == [{"rating": "helped"}]


def test_history_excludes_typed_user_text():
    s = _start("s8")
    sessions.add_message(s["id"], "user", "fictional typed text")
    sessions.add_message(s["id"], "model", "You took seven slow breaths.", "mock", 3)

    (item,) = sessions.get_history()
    assert [m["role"] for m in item["messages"]] == ["model"]
    assert "fictional typed text" not in str(item)


def test_usual_none_without_history():
    assert sessions.get_usual_skill() is None


def test_usual_prefers_most_recent_helped():
    for cid in ("a", "b", "c"):
        _start(cid, skill="reframe")
        sessions.end_session(cid, "completed")
    _start("d", skill="breathing")
    sessions.end_session("d", "completed")
    sessions.set_feedback("d", "helped")
    assert sessions.get_usual_skill() == "breathing"


def test_usual_falls_back_to_most_completed_ties_to_recent():
    _start("a", skill="reframe")
    sessions.end_session("a", "completed")
    _start("b", skill="breathing")
    sessions.end_session("b", "completed")
    assert sessions.get_usual_skill() == "breathing"  # 1-1 tie, breathing is newer

    _start("c", skill="reframe")
    sessions.end_session("c", "completed")
    assert sessions.get_usual_skill() == "reframe"  # 2-1


def test_stopped_sessions_do_not_count_toward_usual():
    _start("a")
    sessions.end_session("a", "stopped")
    assert sessions.get_usual_skill() is None
