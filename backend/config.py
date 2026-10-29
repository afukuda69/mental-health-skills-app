"""Settings read from backend/.env (gitignored) or the process environment.

Adapted from travel-application/backend/config.py. Real environment
variables win over .env values so tests and one-off runs can override them.
"""

import os
from pathlib import Path

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

_env_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

LLM_MODES = {"mock", "live", "mock_error", "mock_timeout", "mock_malformed"}


def _get(key: str) -> str | None:
    value = os.environ.get(key, _env_values.get(key))
    if value is None:
        return None
    value = value.strip()
    return value or None


def get_db_path() -> Path:
    raw = _get("SKILLS_DB_PATH")
    if raw is None:
        return BASE_DIR / "skills.db"
    path = Path(raw)
    return path if path.is_absolute() else BASE_DIR / path


def get_llm_mode() -> str:
    mode = (_get("LLM_MODE") or "mock").lower()
    return mode if mode in LLM_MODES else "mock"


def get_llm_api_key() -> str | None:
    return _get("LLM_API_KEY")


def get_llm_model() -> str | None:
    return _get("LLM_MODEL")


def get_llm_reasoning() -> bool:
    """LLM_REASONING=on lets the model reason before replying. Default off."""
    return (_get("LLM_REASONING") or "off").lower() in ("on", "true", "1", "yes")


def get_mock_chat() -> str | None:
    """LLM_MOCK_CHAT picks a chat fixture in mock mode: auto (default), normal,
    offer, malformed, overlong, banned."""
    return _get("LLM_MOCK_CHAT")


def get_llm_max_calls() -> int:
    raw = _get("LLM_MAX_CALLS")
    try:
        return max(0, int(raw)) if raw is not None else 50
    except ValueError:
        return 50
