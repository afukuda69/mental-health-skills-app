"""The one local profile (controller layer).

Stored: display name, a chosen usual skill, the animate-circle preference,
and the last check-in. Derived on every read, so they change as soon as a
session ends: the learned usual skill (design.md section h) and per-skill
counts. The chat gets only summary(), which holds counts and labels, never
message, reframe, or other conversation text.
"""

import db
import sessions

SKILLS = ("breathing", "stop", "reframe")
LABELS = {"breathing": "Paced breathing", "stop": "STOP", "reframe": "Cognitive reframe"}
CHECKINS = {"tense": "Tense or wound up", "overwhelmed": "Overwhelmed", "okay": "Okay, just want a minute", "skip": "Skipped"}
FIELDS = ("display_name", "usual_skill", "animate_circle", "last_checkin")


def _row(conn) -> dict:
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(row) if row else {k: None for k in ("display_name", "usual_skill", "animate_circle", "last_checkin", "last_checkin_at", "updated_at")}


def _counts(conn) -> dict:
    counts = {s: {"completed": 0, "stopped": 0, "left": 0} for s in SKILLS}
    for r in conn.execute("SELECT skill, end_reason, COUNT(*) AS n FROM sessions WHERE end_reason IS NOT NULL GROUP BY skill, end_reason"):
        if r["skill"] in counts:
            counts[r["skill"]][r["end_reason"]] = r["n"]
    return counts


def get_profile() -> dict:
    conn = db.get_connection()
    try:
        row = _row(conn)
        counts = _counts(conn)
        last_end = conn.execute("SELECT MAX(ended_at) FROM sessions").fetchone()[0]
    finally:
        conn.close()
    learned = sessions.get_usual_skill()
    chosen = row["usual_skill"]
    updated = max([t for t in (row["updated_at"], last_end) if t], default=None)
    return {
        "display_name": row["display_name"],
        "usual_skill": chosen or learned,
        "usual_source": "chosen" if chosen else ("learned" if learned else None),
        "learned_usual": learned,
        "animate_circle": None if row["animate_circle"] is None else bool(row["animate_circle"]),
        "animate_source": "chosen" if row["animate_circle"] is not None else "system",
        "last_checkin": row["last_checkin"],
        "last_checkin_at": row["last_checkin_at"],
        "counts": counts,
        "updated_at": updated,
    }


def update_profile(changes: dict) -> dict:
    """Apply only the keys given. None clears a field."""
    values = {}
    for key, value in changes.items():
        if key not in FIELDS:
            raise ValueError(f"unknown field: {key}")
        if key == "display_name" and value is not None:
            value = value.strip()[:40] or None
        if key == "usual_skill" and value not in (None, *SKILLS):
            raise ValueError("unknown skill")
        if key == "last_checkin" and value not in (None, *CHECKINS):
            raise ValueError("unknown check-in")
        if key == "animate_circle" and value is not None:
            value = 1 if value else 0
        values[key] = value
    now = sessions.now_iso()
    if "last_checkin" in values:
        values["last_checkin_at"] = now if values["last_checkin"] else None
    values["updated_at"] = now
    conn = db.get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")
        sets = ", ".join(f"{k} = ?" for k in values)
        conn.execute(f"UPDATE profile SET {sets} WHERE id = 1", tuple(values.values()))
        conn.commit()
    finally:
        conn.close()
    return get_profile()


def reset_to_learned() -> dict:
    """Drop the choices the user made so the app falls back to what it learned."""
    return update_profile({"usual_skill": None, "animate_circle": None})


def summary() -> str:
    """One line for the chat context: name, usual skill, last check-in, counts. No text."""
    p = get_profile()
    parts = [f"Name: {p['display_name']}." if p["display_name"] else "Name: not given."]
    if p["usual_skill"]:
        parts.append(f"Usual skill: {LABELS[p['usual_skill']]} [{p['usual_skill']}], {p['usual_source']}.")
    else:
        parts.append("Usual skill: none yet.")
    parts.append(f"Last check-in: {CHECKINS[p['last_checkin']]}." if p["last_checkin"] else "Last check-in: none.")
    counts = []
    for skill, c in p["counts"].items():
        bits = [f"{n} {reason}" for reason, n in c.items() if n]
        if bits:
            counts.append(f"{LABELS[skill]} {', '.join(bits)}")
    parts.append(f"Sessions: {'; '.join(counts)}." if counts else "Sessions: none yet.")
    return " ".join(parts)
