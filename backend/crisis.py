"""Supplementary crisis keyword check. Runs before any model call.

The phrase list lives in shared/crisis_phrases.json, the single file the
frontend also reads. This is NOT the app's safety mechanism: the
always-visible Crisis support button is (docs/design.md section f).

Known limits of a fixed phrase list:
- Misses misspellings ("suicde"), indirect phrasing ("I don't see the point
  anymore"), other languages, and anything not typed.
- False positives on quotes and idioms ("end it all" about a project). The
  cost is low: the panel opens and one tap goes back.
- It is not a classifier and does not detect distress.
"""

import json
import re
from pathlib import Path

PHRASES_PATH = Path(__file__).resolve().parent.parent / "shared" / "crisis_phrases.json"

# Shown in place of a model reply when the check matches. Fixed text, never
# generated. It points to the panel and does not claim anyone is watching.
SCRIPTED_REPLY = "Crisis support is open. It lists people you can call or text right now."


def load_phrases() -> list[str]:
    data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
    return [normalize(p) for p in data["phrases"]]


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


_PHRASES = load_phrases()


def matches_crisis_phrase(text: str | None) -> bool:
    if not text:
        return False
    normalized = normalize(text)
    return any(re.search(rf"\b{re.escape(p)}\b", normalized) for p in _PHRASES)
