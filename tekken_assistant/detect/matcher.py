from __future__ import annotations

import re
from difflib import SequenceMatcher

from tekken_assistant.models import Character

_NON_ALNUM = re.compile(r"[^a-z0-9]")

EXACT_THRESHOLD = 0.99
_THRESHOLDS: tuple[tuple[int, float], ...] = (
    (2, 0.90),
    (4, 0.85),
    (6, 0.72),
    (10, 0.66),
)


def _threshold(length: int) -> float:
    for max_len, th in _THRESHOLDS:
        if length <= max_len:
            return th
    return 0.62


def squash(text: str) -> str:
    return _NON_ALNUM.sub("", text.lower())


class NameMatcher:
    def __init__(self, characters: dict[str, Character]):
        self._by_key: dict[str, str] = {}
        for name, char in characters.items():
            keys = {name, char.name, *char.aliases}
            for key in keys:
                sq = squash(key)
                if sq:
                    self._by_key.setdefault(sq, name)

    def match(self, text: str) -> tuple[str, float] | None:
        sq = squash(text)
        if not sq:
            return None
        if sq in self._by_key:
            return self._by_key[sq], 1.0
        best_name = None
        best_key = None
        best_ratio = 0.0
        for key, name in self._by_key.items():
            ratio = SequenceMatcher(None, sq, key).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_key = key
                best_name = name
        if best_name is None:
            return None
        if best_ratio >= _threshold(len(sq)) and (
            best_ratio >= 0.92 or sq[:3] == best_key[:3]
        ):
            return best_name, best_ratio
        return None
