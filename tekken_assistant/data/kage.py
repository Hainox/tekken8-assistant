from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from tekken_assistant.models import Combo

BASE_URL = "https://tekken8combo.kagewebsite.com"


def _cache_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data_cache"
    return Path(__file__).resolve().parent / "cache"


CACHE_DIR = _cache_dir()
CACHE_TTL = 24 * 3600.0
REQUEST_TIMEOUT = 12.0


def _cache_path(slug: str) -> Path:
    return CACHE_DIR / f"{slug}.json"


def _read_cache(slug: str) -> tuple[list[dict], float] | None:
    path = _cache_path(slug)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        combos = raw.get("combos", [])
        fetched_at = float(raw.get("fetched_at", 0.0))
        for c in combos:
            Combo(
                label=str(c.get("label", "")),
                notation=str(c.get("notation", "")),
                damage=str(c.get("damage", "")),
                note=str(c.get("note", "")),
                source=str(c.get("source", "kage")),
            )
        return combos, fetched_at
    except Exception:
        path.unlink(missing_ok=True)
        return None


def _write_cache(slug: str, combos: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": time.time(), "combos": combos}
    _cache_path(slug).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_html(url: str, timeout: float = REQUEST_TIMEOUT) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 TekkenAssistant/0.1"},
    )
    response.raise_for_status()
    return response.text


def _notation_from_spans(spans) -> str:
    parts: list[str] = []
    for span in spans:
        token = (span.get("dataname") or "").strip()
        if not token:
            if parts and parts[-1] != "►":
                parts.append("►")
        else:
            parts.append(token)
    while parts and parts[-1] == "►":
        parts.pop()
    return " ".join(parts)


def parse_combos(html: str, limit: int = 4) -> list[Combo]:
    soup = BeautifulSoup(html, "html.parser")
    combos: list[Combo] = []
    for item in soup.select("li.combo-item"):
        spans = item.select("p.comboImg span[dataname]")
        notation = _notation_from_spans(spans)
        if not notation:
            continue
        strongs = [s.get_text(strip=True) for s in item.select("div.powered strong")]
        hits = strongs[0] if len(strongs) > 0 else ""
        damage = strongs[1] if len(strongs) > 1 else ""
        classes = item.get("class", [])
        version = next((c for c in classes if c.startswith("v")), "")
        combo_id = item.get("id", "").replace("combo-", "")
        note_el = item.select_one(".sticky-note, .note")
        note = note_el.get_text(" ", strip=True) if note_el else ""
        label = f"Kage #{combo_id}" if combo_id else "Kage"
        source = "kage" + (f":{version}" if version else "")
        combos.append(
            Combo(
                label=label,
                notation=notation,
                damage=f"{damage} ({hits})" if damage or hits else "",
                note=note,
                source=source,
            )
        )
        if len(combos) >= limit:
            break
    return combos


def fetch_combos(
    slug: str,
    limit: int = 4,
    allow_network: bool = True,
) -> list[Combo]:
    cached = _read_cache(slug)
    if cached is not None:
        combos, fetched_at = cached
        fresh = time.time() - fetched_at < CACHE_TTL
        if fresh or not allow_network:
            return [Combo(**c) for c in combos[:limit]]
    if not allow_network:
        return []
    try:
        html = _get_html(f"{BASE_URL}/combos-{slug}/")
        all_combos = parse_combos(html, limit=50)
        if all_combos:
            _write_cache(
                slug,
                [
                    {
                        "label": c.label,
                        "notation": c.notation,
                        "damage": c.damage,
                        "note": c.note,
                        "source": c.source,
                    }
                    for c in all_combos
                ],
            )
        return all_combos[:limit]
    except requests.RequestException:
        if cached is not None:
            return [Combo(**c) for c in cached[0][:limit]]
        return []
