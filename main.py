from __future__ import annotations

import queue
import threading

from tekken_assistant.capture.screen import ScreenCapture
from tekken_assistant.config import AppConfig, load_config
from tekken_assistant.data.kage import fetch_combos
from tekken_assistant.data.loader import load_characters
from tekken_assistant.detect.detector import ScreenDetector
from tekken_assistant.detect.matcher import NameMatcher
from tekken_assistant.detect.ocr import TesseractOcr
from tekken_assistant.detect.watcher import Watcher
from tekken_assistant.models import Character, Combo, Detection
from tekken_assistant.ui.overlay import OverlayApp


class App:
    def __init__(self) -> None:
        self.config = load_config()
        self.characters: dict[str, Character] = load_characters()
        self.matcher = NameMatcher(self.characters)
        self.queue: queue.Queue = queue.Queue()

        self.force_auto = True
        self.manual_player: str | None = None
        self.manual_opponent: str | None = None
        self.current: Detection = Detection()
        self.kage_cache: dict[str, list[Combo]] = {}
        self._kage_thread: threading.Thread | None = None
        self._rendered_player: str | None = None
        self._rendered_opponent: str | None = None
        self._polling_paused = False
        self._closing = False

        self.ui = OverlayApp(
            roster=list(self.characters.keys()),
            width=self.config.overlay_width,
            height=self.config.overlay_height,
            offset_x=self.config.overlay_offset_x,
            offset_y=self.config.overlay_offset_y,
            secondary_origin=self._secondary_origin(),
            mode=self.config.overlay_mode,
            on_pause_toggle=self.toggle_polling,
            on_swap=self.swap_sides,
            on_manual_set=self.set_manual,
            on_auto_toggle=self.set_auto,
            on_quit=self.quit,
            on_copy=self.on_copy,
            on_mode_change=self.on_mode_change,
        )

        self.watcher: Watcher | None = None
        self.detector = self._build_detector()
        if self.detector is not None:
            self.watcher = Watcher(
                detect=self.detector.detect,
                poll_interval=self.config.poll_interval,
                stable_polls=self.config.stable_polls,
            )
            self.watcher.start(on_update=self.on_detection, on_error=self.on_watch_error)
        else:
            self.ui.set_status(
                "OCR недоступен (установи Tesseract) — ручной режим",
                "#d9635a",
            )
        self._register_hotkeys()

    def _secondary_origin(self) -> tuple[int, int]:
        try:
            import mss

            with mss.mss() as sct:
                monitors = sct.monitors
            idx = self.config.overlay_monitor_index
            if 0 <= idx < len(monitors):
                mon = monitors[idx]
                return int(mon["left"]), int(mon["top"])
        except Exception:
            pass
        return 0, 0

    def _build_detector(self) -> ScreenDetector | None:
        try:
            ocr = TesseractOcr(
                language=self.config.ocr_language,
                min_confidence=self.config.ocr_min_confidence,
                tesseract_cmd=self.config.tesseract_cmd,
            )
            ocr.check()
        except Exception:
            return None
        capture = ScreenCapture(monitor_index=self.config.monitor_index)
        return ScreenDetector(
            capture=capture,
            ocr=ocr,
            matcher=self.matcher,
            min_name_height_ratio=self.config.min_name_height_ratio,
            swap_sides=self.config.swap_sides,
        )

    def _register_hotkeys(self) -> None:
        try:
            import keyboard
        except ImportError:
            return
        keyboard.add_hotkey(
            self.config.hotkey_toggle_overlay,
            lambda: self.queue.put(("hotkey", "overlay")),
        )
        keyboard.add_hotkey(
            self.config.hotkey_toggle_polling,
            lambda: self.queue.put(("hotkey", "polling")),
        )
        keyboard.add_hotkey(
            self.config.hotkey_cycle_mode,
            lambda: self.queue.put(("hotkey", "mode")),
        )

    def run(self) -> None:
        self.ui.root.after(200, self._process_queue)
        self.ui.run()

    def _process_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "detection":
                    self.current = payload
                    self._apply_detection()
                elif kind == "kage":
                    self._apply_kage(payload)
                elif kind == "error":
                    self.ui.set_status(f"Ошибка захвата: {payload}", "#d9635a")
                elif kind == "hotkey":
                    self._handle_hotkey(payload)
        except queue.Empty:
            pass
        if not self._closing:
            self.ui.root.after(200, self._process_queue)

    def _handle_hotkey(self, action: str) -> None:
        if action == "overlay":
            if self.ui.root.state() == "withdrawn":
                self.ui.root.deiconify()
            else:
                self.ui.root.withdraw()
        elif action == "polling":
            self.toggle_polling()
        elif action == "mode":
            self.ui.cycle_mode()

    def on_mode_change(self, mode: str) -> None:
        self.config = self.config.with_(overlay_mode=mode).save()

    def _apply_detection(self) -> None:
        detection = self.current
        player = self.manual_player if not self.force_auto else detection.player
        opponent = self.manual_opponent if not self.force_auto else detection.opponent
        self._rendered_player = player
        self._rendered_opponent = opponent

        player_char = self.characters.get(player) if player else None
        opponent_char = self.characters.get(opponent) if opponent else None
        kage_combos = (
            self.kage_cache.get(player_char.kage_slug, []) if player_char else []
        )
        self.ui.render_player(player_char, kage_combos)
        self.ui.render_opponent(opponent_char)

        if player_char is not None:
            self._maybe_fetch_kage(player_char)

        color = "#7ec46a" if player_char and opponent_char else "#e5a13c"
        self.ui.set_status(f"{player or '?'} vs {opponent or '?'}", color)

    def _apply_kage(self, payload: tuple[str, list[Combo]]) -> None:
        slug, combos = payload
        if combos:
            self.kage_cache[slug] = combos
        character = self.characters.get(self._rendered_player or "")
        if character is None or character.kage_slug != slug:
            return
        shown = combos or self.kage_cache.get(slug, [])
        self.ui.render_player(character, shown)

    def on_detection(self, detection: Detection) -> None:
        if self._closing:
            return
        self.queue.put(("detection", detection))

    def on_watch_error(self, exc: Exception) -> None:
        if self._closing:
            return
        self.queue.put(("error", exc.__class__.__name__))

    def _maybe_fetch_kage(self, character: Character) -> None:
        if not self.config.use_kage_fetch or not character.kage_slug:
            return
        slug = character.kage_slug
        if slug in self.kage_cache or (
            self._kage_thread is not None and self._kage_thread.is_alive()
        ):
            return

        def worker() -> None:
            try:
                combos = fetch_combos(slug, limit=self.config.kage_combo_limit)
            except Exception:
                combos = []
            if not self._closing:
                self.queue.put(("kage", (slug, combos)))

        self._kage_thread = threading.Thread(target=worker, daemon=True, name="kage-fetch")
        self._kage_thread.start()

    def toggle_polling(self) -> None:
        if self.watcher is None or self._closing:
            return
        if self._polling_paused:
            self.watcher.start(on_update=self.on_detection, on_error=self.on_watch_error)
            self._polling_paused = False
            self.ui.set_paused(False)
        else:
            self.watcher.stop()
            self._polling_paused = True
            self.ui.set_paused(True)

    def swap_sides(self) -> None:
        self.config = self.config.with_(swap_sides=not self.config.swap_sides).save()
        if self.detector is not None:
            self.detector._swap = self.config.swap_sides
        self.current = Detection(self.current.opponent, self.current.player)
        self._apply_detection()
        self.ui.set_status("Стороны переключены", "#e5a13c")

    def set_manual(self, side: str, name: str) -> None:
        if side == "player":
            self.manual_player = name or None
        else:
            self.manual_opponent = name or None
        self.force_auto = False
        self.ui.auto_var.set(False)
        self._apply_detection()

    def set_auto(self, enabled: bool) -> None:
        self.force_auto = enabled
        if enabled:
            self.manual_player = None
            self.manual_opponent = None
        self._apply_detection()

    def on_copy(self, notation: str) -> None:
        self.ui.set_status("Скопировано: " + notation[:40], "#9fd3a8")

    def quit(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self.watcher is not None:
            self.watcher.stop()
        self.config.save()
        self.ui.root.destroy()


def main() -> None:
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()


if __name__ == "__main__":
    main()
