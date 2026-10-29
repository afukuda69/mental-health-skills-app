"""SQLite schema, migration, and connection helper (raw sqlite3, no ORM).

Schema follows docs/design.md section g plus "Changes since 3.1". A message
belongs either to an exercise session (acknowledgments, reflections) or to a
"Talk it through" conversation, never both.

Versions (PRAGMA user_version):
  0  Part 3.2: messages.session_id NOT NULL, no conversations table
  1  Part 3.3: conversations table; messages.session_id nullable,
     messages.conversation_id and messages.offer_skill added
"""

import sqlite3

import config

DB_PATH = config.get_db_path()
SCHEMA_VERSION = 1

BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL UNIQUE,
    skill TEXT NOT NULL,
    entry_choice TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    exited_early INTEGER NOT NULL DEFAULT 0,
    end_reason TEXT CHECK (end_reason IN ('completed', 'stopped', 'left')),
    setup_ms INTEGER,
    planned_ms INTEGER,
    measured_ms INTEGER,
    pauses_ms INTEGER,
    crisis_ms INTEGER,
    steps_planned INTEGER,
    steps_completed INTEGER
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- One local profile (id = 1). NULL usual_skill / animate_circle mean "learned" / "follow the system setting".
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    display_name TEXT,
    usual_skill TEXT CHECK (usual_skill IN ('breathing', 'stop', 'reframe')),
    animate_circle INTEGER CHECK (animate_circle IN (0, 1)),
    last_checkin TEXT CHECK (last_checkin IN ('tense', 'overwhelmed', 'okay', 'skip')),
    last_checkin_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    rating TEXT NOT NULL CHECK (rating IN ('helped', 'didnt_help'))
);
"""

MESSAGES_TABLE = """
CREATE TABLE {name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    conversation_id INTEGER REFERENCES conversations(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'model', 'fallback', 'scripted')),
    text TEXT,
    model_status TEXT CHECK (model_status IN ('ok', 'mock', 'fallback', 'error', 'timeout', 'scripted')),
    latency_ms INTEGER,
    crisis_flag INTEGER NOT NULL DEFAULT 0,
    offer_skill TEXT CHECK (offer_skill IN ('breathing', 'stop', 'reframe')),
    created_at TEXT NOT NULL,
    CHECK ((session_id IS NULL) != (conversation_id IS NULL))
)
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _has_table(conn, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _migrate_messages_v1(conn) -> None:
    """Rebuild messages with nullable session_id plus the chat columns, keeping every row."""
    conn.execute(MESSAGES_TABLE.format(name="messages_v1"))
    conn.execute(
        "INSERT INTO messages_v1 (id, session_id, role, text, model_status, latency_ms, crisis_flag, created_at) "
        "SELECT id, session_id, role, text, model_status, latency_ms, crisis_flag, created_at FROM messages"
    )
    conn.execute("DROP TABLE messages")
    conn.execute("ALTER TABLE messages_v1 RENAME TO messages")


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(BASE_SCHEMA)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("BEGIN")
            if _has_table(conn, "messages"):
                _migrate_messages_v1(conn)
            else:
                conn.execute(MESSAGES_TABLE.format(name="messages"))
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            conn.commit()
            conn.execute("PRAGMA foreign_keys = ON")
    finally:
        conn.close()
