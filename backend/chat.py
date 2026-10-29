""""Talk it through" conversations (controller layer).

Send flow: the crisis check runs first (scripted reply, no model call, the
typed text not stored, crisis_flag = 1). Otherwise the user's message is
stored and the model gets: a fixed system prompt, one line per skill from
shared/skills.json, the profile summary (name, usual skill, last check-in,
counts), and the last 10 messages of this conversation only.
"""

import json
from pathlib import Path

import crisis
import db
import model_client
import profile
import sessions

SKILLS_PATH = Path(__file__).resolve().parent.parent / "shared" / "skills.json"


class ConversationNotFound(Exception):
    pass


def load_skills() -> list[dict]:
    return json.loads(SKILLS_PATH.read_text(encoding="utf-8"))["skills"]


def create_conversation() -> dict:
    now = sessions.now_iso()
    conn = db.get_connection()
    try:
        cur = conn.execute("INSERT INTO conversations (created_at, updated_at) VALUES (?, ?)", (now, now))
        conn.commit()
        return {"id": cur.lastrowid, "created_at": now, "updated_at": now, "first_line": None, "message_count": 0}
    finally:
        conn.close()


def list_conversations() -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT c.id, c.created_at, c.updated_at, "
            "(SELECT text FROM messages m WHERE m.conversation_id = c.id AND m.role = 'user' AND m.text IS NOT NULL "
            " ORDER BY m.id LIMIT 1) AS first_line, "
            "(SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count "
            "FROM conversations c ORDER BY c.updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _require(conn, conversation_id: int) -> None:
    if conn.execute("SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)).fetchone() is None:
        raise ConversationNotFound(conversation_id)


def get_messages(conversation_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        _require(conn, conversation_id)
        rows = conn.execute(
            "SELECT id, role, text, model_status, offer_skill, crisis_flag, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _add(conn, conversation_id: int, role: str, text, status=None, latency=None, crisis_flag=False, offer=None) -> dict:
    now = sessions.now_iso()
    cur = conn.execute(
        "INSERT INTO messages (conversation_id, role, text, model_status, latency_ms, crisis_flag, offer_skill, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (conversation_id, role, text, status, latency, 1 if crisis_flag else 0, offer, now),
    )
    conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
    return {"id": cur.lastrowid, "role": role, "text": text, "model_status": status, "offer_skill": offer,
            "crisis_flag": 1 if crisis_flag else 0, "created_at": now}


def send_message(conversation_id: int, text: str) -> dict:
    conn = db.get_connection()
    try:
        _require(conn, conversation_id)
        if crisis.matches_crisis_phrase(text):
            user = _add(conn, conversation_id, "user", None, crisis_flag=True)
            reply = _add(conn, conversation_id, "scripted", crisis.SCRIPTED_REPLY, "scripted", crisis_flag=True)
            conn.commit()
            return {"user": user, "reply": reply, "crisis": True}
        user = _add(conn, conversation_id, "user", text)
        conn.commit()
        recent = [
            dict(r)
            for r in conn.execute(
                "SELECT role, text FROM messages WHERE conversation_id = ? AND text IS NOT NULL ORDER BY id DESC LIMIT 10",
                (conversation_id,),
            ).fetchall()
        ][::-1]
    finally:
        conn.close()

    messages = model_client.build_chat_messages(load_skills(), profile.summary(), recent)
    result = model_client.chat_reply(messages)

    conn = db.get_connection()
    try:
        reply = _add(conn, conversation_id, result.role, result.reply, result.status, result.latency_ms, offer=result.offer_skill)
        conn.commit()
    finally:
        conn.close()
    return {"user": user, "reply": reply, "crisis": False}
