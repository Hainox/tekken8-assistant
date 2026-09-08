import json
from pathlib import Path

from tekken_assistant.data.loader import load_characters
from tekken_assistant.models import Character

CHARACTERS_DIR = Path(__file__).resolve().parent.parent / "tekken_assistant" / "data" / "characters"

REQUIRED_FIELDS = {
    "name",
    "aliases",
    "kage_slug",
    "archetype",
    "difficulty",
    "strengths",
    "weaknesses",
    "key_moves",
    "combos",
    "game_plan",
    "tips",
    "threats",
    "counterplay",
}

EXPECTED_COUNT = 42

LIST_FIELDS = {"strengths", "weaknesses", "game_plan", "tips", "threats", "counterplay"}


def test_all_character_files_load():
    characters = load_characters()
    assert len(characters) >= EXPECTED_COUNT


def test_every_character_has_complete_schema():
    for path in CHARACTERS_DIR.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_FIELDS - set(raw.keys())
        assert not missing, f"{path.name}: missing {missing}"
        for field in LIST_FIELDS:
            assert isinstance(raw[field], list) and len(raw[field]) >= 2, (
                f"{path.name}: field {field} must be a non-trivial list"
            )
        assert len(raw["combos"]) >= 3, f"{path.name}: need at least 3 combos"
        assert len(raw["key_moves"]) >= 3, f"{path.name}: need at least 3 key moves"


def test_character_model_converts():
    characters = load_characters()
    assert all(isinstance(c, Character) for c in characters.values())


def test_unique_kage_slugs():
    characters = load_characters()
    slugs = [c.kage_slug for c in characters.values()]
    assert len(slugs) == len(set(slugs))
    assert all(slugs)
