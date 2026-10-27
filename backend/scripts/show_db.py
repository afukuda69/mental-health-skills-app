"""Print sessions, messages, and feedback from the SQLite file.

    cd backend && .venv/bin/python scripts/show_db.py            # backend/skills.db
    cd backend && .venv/bin/python scripts/show_db.py path/to.db
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "skills.db"

QUERIES = {
    "sessions": "SELECT id, client_id, skill, entry_choice, end_reason, completed, exited_early, "
    "setup_ms, planned_ms, measured_ms, pauses_ms, crisis_ms, steps_planned, steps_completed, "
    "started_at, ended_at FROM sessions ORDER BY id",
    "messages": "SELECT id, session_id, role, text, model_status, latency_ms, crisis_flag, created_at "
    "FROM messages ORDER BY id",
    "feedback": "SELECT id, session_id, rating FROM feedback ORDER BY id",
}


def main(path: Path) -> None:
    conn = sqlite3.connect(path)
    for name, sql in QUERIES.items():
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        print(f"\n## {name}\n")
        print("| " + " | ".join(cols) + " |")
        print("|" + "---|" * len(cols))
        for row in cur.fetchall():
            print("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    conn.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
