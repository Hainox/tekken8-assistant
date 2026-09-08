from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


CONFIG_PATH = app_dir() / "config.json"


@dataclass(frozen=True)
class AppConfig:
    poll_interval: float = 2.0
    stable_polls: int = 2
    ocr_language: str = "eng"
    ocr_min_confidence: float = 40.0
    min_name_height_ratio: float = 0.02
    tesseract_cmd: str = ""
    swap_sides: bool = False
    monitor_index: int = 1
    use_kage_fetch: bool = True
    kage_combo_limit: int = 4
    overlay_width: int = 780
    overlay_height: int = 740
    overlay_offset_x: int = 40
    overlay_offset_y: int = 40
    overlay_mode: str = "compact"
    overlay_monitor_index: int = 2
    hotkey_toggle_overlay: str = "f8"
    hotkey_toggle_polling: str = "f9"
    hotkey_cycle_mode: str = "f7"

    @classmethod
    def from_file(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})

    def save(self, path: Path = CONFIG_PATH) -> "AppConfig":
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self

    def with_(self, **changes) -> "AppConfig":
        return replace(self, **changes)


def load_config() -> AppConfig:
    return AppConfig.from_file()
