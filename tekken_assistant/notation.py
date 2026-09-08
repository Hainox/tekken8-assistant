from __future__ import annotations

import re
from typing import Iterator

SEP = " ► "

_DIRECTIONS = {"f", "b", "u", "d", "n", "d/f", "d/b", "u/f", "u/b", "f/f", "b/b"}
_BUTTON_RE = re.compile(r"^\d+(?:\+\d+)*$")
_DIRBUTTON_RE = re.compile(r"^([fbudnFBUDN](?:/[fb])?)\+([\d+]+)$")

_ARROWS = {
    "f": "→", "b": "←", "u": "↑", "d": "↓", "n": "•",
    "d/f": "↘", "d/b": "↙", "u/f": "↗", "u/b": "↖",
}


def _is_direction(token: str) -> bool:
    return token.lower() in _DIRECTIONS


def _norm_direction(token: str) -> str:
    return token if len(token) == 1 else token.lower()


def _convert_step(step: str) -> str:
    out: list[str] = []
    dirs: list[str] = []
    dirs_join = False
    join_comma = False
    last_button = False

    def emit(piece: str, join: bool = False) -> None:
        nonlocal join_comma
        if join and out:
            out[-1] += "," + piece
        else:
            out.append(piece)
        join_comma = False

    def flush_dirs() -> None:
        nonlocal dirs_join
        if dirs:
            emit(",".join(dirs), join=dirs_join)
            dirs.clear()
        dirs_join = False

    for tok in step.split():
        if tok.startswith(","):
            join_comma = True
        subs = [s for s in tok.split(",") if s]
        for si, sub in enumerate(subs):
            if si:
                join_comma = True
            m = _DIRBUTTON_RE.match(sub)
            if m:
                if not dirs:
                    dirs_join = join_comma
                    join_comma = False
                dirs.append(_norm_direction(m.group(1)))
                sub = m.group(2)
            elif _is_direction(sub):
                if not dirs:
                    dirs_join = join_comma
                    join_comma = False
                dirs.append(_norm_direction(sub))
                continue
            if _BUTTON_RE.match(sub):
                if dirs:
                    emit(",".join(dirs) + "+" + sub, join=dirs_join)
                    dirs.clear()
                    dirs_join = False
                else:
                    emit(sub, join=join_comma or last_button)
                last_button = True
                continue
            flush_dirs()
            emit(sub, join=join_comma)
            last_button = False
        if tok.endswith(","):
            join_comma = True
    flush_dirs()
    return " ".join(out)


def to_official(notation: str) -> str:
    if not notation:
        return ""
    steps = re.split(r"►|>", notation)
    converted = [_convert_step(s.strip()) for s in steps]
    return SEP.join(s for s in converted if s)


def _classify(sub: str) -> tuple[str, str]:
    low = sub.lower()
    if low in _ARROWS:
        return ("dir", _ARROWS[low])
    if sub in ("1", "2", "3", "4"):
        return ("btn" + sub, sub)
    if sub.isdigit():
        return ("btnx", sub)
    return ("word", sub)


def _collapse_arrows(arrows: list[str]) -> list[tuple[str, str]]:
    res: list[str] = []
    i = 0
    while i < len(arrows):
        if i + 1 < len(arrows) and arrows[i] == arrows[i + 1] and arrows[i] in ("→", "←"):
            res.append("»" if arrows[i] == "→" else "«")
            i += 2
        else:
            res.append(arrows[i])
            i += 1
    return [("dir", a) for a in res]


def _token_segments(token: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    parts = token.split(",")
    for i, part in enumerate(parts):
        subs = part.split("+")
        kinds = [_classify(s) for s in subs]
        if i > 0:
            prev_dir = bool(items) and items[-1][0] == "dir"
            cur_dir = bool(kinds) and kinds[0][0] == "dir"
            if not (prev_dir and cur_dir):
                items.append(("comma", ","))
        for j, (kind, val) in enumerate(kinds):
            if j and kind.startswith("btn") and items and items[-1][0].startswith("btn"):
                items.append(("plus", "+"))
            items.append((kind, val))
    out: list[tuple[str, str]] = []
    run: list[str] = []
    for kind, val in items:
        if kind == "dir":
            run.append(val)
            continue
        if run:
            out.extend(_collapse_arrows(run))
            run = []
        out.append((kind, val))
    if run:
        out.extend(_collapse_arrows(run))
    return out


def iter_segments(notation: str) -> Iterator[tuple[str, str]]:
    if not notation:
        return
    steps = re.split(r"►|>", notation)
    for si, step in enumerate(steps):
        step = step.strip()
        if si:
            yield (SEP, "sep")
        if not step:
            continue
        for tok in step.split():
            for kind, val in _token_segments(tok):
                yield (val, kind)
            yield (" ", "space")
