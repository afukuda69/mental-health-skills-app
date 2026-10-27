"""SQLite schema and connection helper (raw sqlite3, no ORM).

Schema follows docs/design.md section g, plus the timing and model-status
columns listed under "Changes since 3.1". A session is the conversation
container: its messages are the conversation record.
"""

import sqlite3

import config

DB_PATH = config.get_db_path()

SCHEMA = """
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

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'model', 'fallback', 'scripted')),
    text TEXT,
    model_status TEXT CHECK (model_status IN ('ok', 'mock', 'fallback', 'error', 'timeout', 'scripted')),
    latency_ms INTEGER,
    crisis_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    rating TEXT NOT NULL CHECK (rating IN ('helped', 'didnt_help'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
