"""Session, message, feedback, and history logic (the controller layer).

Routes in main.py stay thin and call these functions. Every function opens
and closes its own connection, following travel-application/backend/controller.py.
"""

from datetime import datetime, timezone

import crisis
import db
import model_client

END_REASONS = {"completed", "stopped", "left"}
RATINGS = {"helped", "didnt_help"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _session_row(conn, client_id: str):
    return conn.execute("SELECT * FROM sessions WHERE client_id = ?", (client_id,)).fetchone()


def create_session(
    client_id: str,
    skill: str,
    entry_choice: str | None = None,
    setup_ms: int | None = None,
    planned_ms: int | None = None,
    steps_planned: int | None = None,
    started_at: str | None = None,
) -> dict:
    """Insert a session. Repeating the same client_id is a no-op, so a
    retried request never creates a duplicate."""
    conn = db.get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions "
            "(client_id, skill, entry_choice, started_at, setup_ms, planned_ms, steps_planned) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client_id, skill, entry_choice, started_at or now_iso(), setup_ms, planned_ms, steps_planned),
        )
        conn.commit()
        return dict(_session_row(conn, client_id))
    finally:
        conn.close()


def end_session(
    client_id: str,
    end_reason: str,
    measured_ms: int | None = None,
    pauses_ms: int | None = None,
    crisis_ms: int | None = None,
    steps_completed: int | None = None,
) -> dict | None:
    """Record how a session ended. Returns None if the session is unknown.

    "left" is sent from pagehide/visibilitychange, which also fires when the
    user only switches tabs. So "left" never overwrites "completed" or
    "stopped", while a later "completed" or "stopped" does overwrite "left".
    """
    if end_reason not in END_REASONS:
        raise ValueError(f"unknown end_reason: {end_reason}")
    conn = db.get_connection()
    try:
        row = _session_row(conn, client_id)
        if row is None:
            return None
        if end_reason == "left" and row["end_reason"] in ("completed", "stopped"):
            return dict(row)
        conn.execute(
            "UPDATE sessions SET ended_at = ?, end_reason = ?, completed = ?, exited_early = ?, "
            "measured_ms = ?, pauses_ms = ?, crisis_ms = ?, steps_completed = ? WHERE client_id = ?",
            (
                now_iso(),
                end_reason,
                1 if end_reason == "completed" else 0,
                0 if end_reason == "completed" else 1,
                measured_ms,
                pauses_ms,
                crisis_ms,
                steps_completed,
                client_id,
            ),
        )
        conn.commit()
        return dict(_session_row(conn, client_id))
    finally:
        conn.close()


def get_session(client_id: str) -> dict | None:
    conn = db.get_connection()
    try:
        row = _session_row(conn, client_id)
        return dict(row) if row else None
    finally:
        conn.close()


def add_message(
    session_id: int,
    role: str,
    text: str | None,
    model_status: str | None = None,
    latency_ms: int | None = None,
    crisis_flag: bool = False,
) -> int:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO messages (session_id, role, text, model_status, latency_ms, crisis_flag, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, role, text, model_status, latency_ms, 1 if crisis_flag else 0, now_iso()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def set_feedback(client_id: str, rating: str) -> bool:
    """Store one rating per session (a second tap replaces the first)."""
    if rating not in RATINGS:
        raise ValueError(f"unknown rating: {rating}")
    conn = db.get_connection()
    try:
        row = _session_row(conn, client_id)
        if row is None:
            return False
        conn.execute("DELETE FROM feedback WHERE session_id = ?", (row["id"],))
        conn.execute("INSERT INTO feedback (session_id, rating) VALUES (?, ?)", (row["id"], rating))
        conn.commit()
        return True
    finally:
        conn.close()


def count_prior_completed(skill: str, before_session_id: int) -> int:
    conn = db.get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE skill = ? AND completed = 1 AND id < ?",
            (skill, before_session_id),
        ).fetchone()[0]
    finally:
        conn.close()


def get_history(limit: int = 50) -> list[dict]:
    """Sessions, newest first, each with its acknowledgment messages.

    Typed user text is never returned (design.md section g); only the
    model, fallback, and scripted lines are.
    """
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT s.id, s.client_id, s.skill, s.started_at, s.ended_at, s.end_reason, "
            "s.measured_ms, f.rating "
            "FROM sessions s LEFT JOIN feedback f ON f.session_id = s.id "
            "ORDER BY s.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        history = []
        for row in rows:
            messages = conn.execute(
                "SELECT role, text, model_status, created_at FROM messages "
                "WHERE session_id = ? AND role != 'user' ORDER BY id",
                (row["id"],),
            ).fetchall()
            item = dict(row)
            item["messages"] = [dict(m) for m in messages]
            history.append(item)
        return history
    finally:
        conn.close()


def get_usual_skill() -> str | None:
    """Derive the usual skill from history (design.md section h):
    1. the skill of the most recent session rated helped
    2. else the skill with the most completed sessions, ties to the most recent
    3. else None
    """
    conn = db.get_connection()
    try:
        helped = conn.execute(
            "SELECT s.skill FROM feedback f JOIN sessions s ON s.id = f.session_id "
            "WHERE f.rating = 'helped' ORDER BY s.id DESC LIMIT 1"
        ).fetchone()
        if helped:
            return helped["skill"]
        most = conn.execute(
            "SELECT skill FROM sessions WHERE completed = 1 "
            "GROUP BY skill ORDER BY COUNT(*) DESC, MAX(id) DESC LIMIT 1"
        ).fetchone()
        return most["skill"] if most else None
    finally:
        conn.close()


class SessionNotFound(Exception):
    pass


class SessionStopped(Exception):
    """No model call is made after Stop exercise (design.md section e)."""


def _require_open_session(client_id: str) -> dict:
    session = get_session(client_id)
    if session is None:
        raise SessionNotFound(client_id)
    if session["end_reason"] == "stopped":
        raise SessionStopped(client_id)
    return session


def acknowledge_session(client_id: str) -> dict:
    """Closing acknowledgment for a finished exercise, saved as a message."""
    session = _require_open_session(client_id)
    context = {
        "entry_choice": session["entry_choice"],
        "prior_completed": count_prior_completed(session["skill"], session["id"]),
    }
    result = model_client.acknowledge(session["skill"], context)
    add_message(session["id"], result.role, result.text, result.status, result.latency_ms)
    return {"text": result.text, "status": result.status, "latency_ms": result.latency_ms, "crisis": False}


def submit_text(client_id: str, text: str) -> dict:
    """Typed text (the reframe in Part 3.3). The crisis check runs first; on
    a match there is no model call, the typed text is not stored, and a
    scripted reply is saved with crisis_flag = 1."""
    session = _require_open_session(client_id)
    if crisis.matches_crisis_phrase(text):
        add_message(session["id"], "user", None, None, None, crisis_flag=True)
        add_message(session["id"], "scripted", crisis.SCRIPTED_REPLY, "scripted", None, crisis_flag=True)
        return {"text": crisis.SCRIPTED_REPLY, "status": "scripted", "latency_ms": None, "crisis": True}
    add_message(session["id"], "user", text)
    result = model_client.acknowledge("reframe", {"text": text})
    add_message(session["id"], result.role, result.text, result.status, result.latency_ms)
    return {"text": result.text, "status": result.status, "latency_ms": result.latency_ms, "crisis": False}
