from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Combo:
    label: str
    notation: str
    damage: str = ""
    note: str = ""
    source: str = "local"


@dataclass(frozen=True)
class KeyMove:
    input: str
    name: str = ""
    note: str = ""


@dataclass(frozen=True)
class Character:
    name: str
    aliases: tuple[str, ...] = ()
    kage_slug: str = ""
    archetype: str = ""
    difficulty: str = ""
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    key_moves: tuple[KeyMove, ...] = ()
    combos: tuple[Combo, ...] = ()
    game_plan: tuple[str, ...] = ()
    tips: tuple[str, ...] = ()
    threats: tuple[str, ...] = ()
    counterplay: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict) -> "Character":
        key_moves = tuple(KeyMove(**km) for km in raw.get("key_moves", []))
        combos = tuple(Combo(**c) for c in raw.get("combos", []))
        return cls(
            name=raw["name"],
            aliases=tuple(raw.get("aliases", ())),
            kage_slug=raw.get("kage_slug", ""),
            archetype=raw.get("archetype", ""),
            difficulty=raw.get("difficulty", ""),
            strengths=tuple(raw.get("strengths", ())),
            weaknesses=tuple(raw.get("weaknesses", ())),
            key_moves=key_moves,
            combos=combos,
            game_plan=tuple(raw.get("game_plan", ())),
            tips=tuple(raw.get("tips", ())),
            threats=tuple(raw.get("threats", ())),
            counterplay=tuple(raw.get("counterplay", ())),
        )


@dataclass(frozen=True)
class Detection:
    player: str | None = None
    opponent: str | None = None

    def is_empty(self) -> bool:
        return self.player is None and self.opponent is None


@dataclass(frozen=True)
class OcrWord:
    text: str
    x: int
    y: int
    w: int
    h: int
    conf: float

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2


@dataclass(frozen=True)
class NameHit:
    name: str
    x: int
    y: int
    h: int
    ratio: float
