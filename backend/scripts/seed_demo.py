"""Seed a scratch database with fictional demo data (5 sessions and a profile name).

Refuses to run unless SKILLS_DB_PATH points somewhere other than backend/skills.db.

    SKILLS_DB_PATH=/tmp/skills-demo.db .venv/bin/python scripts/seed_demo.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import config  # noqa: E402

# Resolve the path exactly as the app does (relative paths are under backend/).
raw = os.environ.get("SKILLS_DB_PATH", "").strip()
if not raw or config.get_db_path().resolve() == (BACKEND / "skills.db").resolve():
    sys.exit("Refusing: set SKILLS_DB_PATH to a scratch file (not backend/skills.db).")
raw = str(config.get_db_path())

import db  # noqa: E402
import profile  # noqa: E402
import sessions  # noqa: E402

db.init_db()
if db.get_connection().execute("SELECT COUNT(*) FROM sessions").fetchone()[0]:
    sys.exit(f"{raw} already has sessions; delete it first to reseed.")

now = datetime.now(timezone.utc)
DEMO = [  # (days ago, skill, entry choice, end reason, measured ms, steps planned, steps done, planned ms, rating)
    (4, "breathing", "tense", "completed", 75012, 7, 7, 75000, "helped"),
    (3, "stop", "okay", "completed", 58340, 4, 4, 60000, None),
    (2, "breathing", "overwhelmed", "stopped", 21480, 7, 1, 75000, None),
    (1, "breathing", None, "completed", 75008, 7, 7, 75000, "helped"),
    (0, "reframe", "okay", "completed", 66210, 4, 4, 70000, None),
]
for i, (days, skill, entry, reason, ms, planned_steps, done, planned, rating) in enumerate(DEMO):
    cid = f"demo-{i + 1}"
    started = (now - timedelta(days=days, hours=2)).isoformat(timespec="milliseconds")
    sessions.create_session(cid, skill, entry, 900, planned, planned_steps, started)
    sessions.end_session(cid, reason, ms, 0, 0, done)
    if rating:
        sessions.set_feedback(cid, rating)
profile.update_profile({"display_name": "Alex", "last_checkin": "okay"})
print(f"Seeded {raw}: {len(DEMO)} fictional sessions, display name 'Alex'.")
print(profile.summary())
