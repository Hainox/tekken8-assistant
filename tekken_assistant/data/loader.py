from __future__ import annotations

import json
from pathlib import Path

from tekken_assistant.models import Character

CHARACTERS_DIR = Path(__file__).resolve().parent / "characters"


def load_characters(directory: Path = CHARACTERS_DIR) -> dict[str, Character]:
    characters: dict[str, Character] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            character = Character.from_dict(raw)
        except Exception as exc:
            print(f"[loader] пропускаю битый файл {path.name}: {exc}")
            continue
        characters[character.name] = character
    return characters


def roster_names(characters: dict[str, Character]) -> list[str]:
    return list(characters.keys())
