"""Shared fixtures. Every test gets a fresh temporary SQLite file (never
backend/skills.db), LLM_MODE=mock, and a guard that fails any real network call."""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402
import model_client  # noqa: E402


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LLM_MAX_CALLS", "50")
    model_client.reset_live_call_count()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("Tests must not make real HTTP calls")

    monkeypatch.setattr(httpx, "post", refuse)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as c:
        yield c


def rows(sql, params=()):
    conn = db.get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
