"""The supplementary phrase check. These tests also document its limits."""

import pytest

import crisis


@pytest.mark.parametrize(
    "text",
    [
        "Fictional: I want to die",
        "fictional: I WANT TO   DIE",
        "fictional: thinking about suicide",
        "fictional: I might hurt myself",
        "fictional: I’m going to end it all",
    ],
)
def test_matches(text):
    assert crisis.matches_crisis_phrase(text) is True


@pytest.mark.parametrize("text", ["", None, "I want to diet", "The meeting went fine"])
def test_no_match(text):
    assert crisis.matches_crisis_phrase(text) is False


def test_known_limits_are_real():
    # Misspellings and indirect phrasing are missed (documented in crisis.py).
    assert crisis.matches_crisis_phrase("fictional: i want to dye") is False
    assert crisis.matches_crisis_phrase("fictional: I don't see the point anymore") is False
    # Idioms are false positives.
    assert crisis.matches_crisis_phrase("Let's end it all and rewrite the project") is True


def test_list_is_loaded_from_shared_file():
    assert crisis.PHRASES_PATH.name == "crisis_phrases.json"
    assert "want to die" in crisis.load_phrases()
