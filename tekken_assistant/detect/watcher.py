from __future__ import annotations

import threading
from typing import Callable

from tekken_assistant.models import Detection


class Watcher:
    def __init__(
        self,
        detect: Callable[[], Detection],
        poll_interval: float = 2.0,
        stable_polls: int = 2,
    ):
        self._detect = detect
        self._poll_interval = max(0.5, poll_interval)
        self._stable_needed = max(1, stable_polls)
        self._lock = threading.Lock()
        self._state = Detection()
        self._candidate: Detection | None = None
        self._candidate_count = 0
        self._last_notified: Detection | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def state(self) -> Detection:
        with self._lock:
            return self._state

    def poll(self) -> Detection:
        detected = self._detect()
        with self._lock:
            if detected.is_empty():
                self._candidate = None
                self._candidate_count = 0
                return self._state
            if detected == self._state:
                self._candidate = None
                self._candidate_count = 0
                return self._state
            if detected == self._candidate:
                self._candidate_count += 1
            else:
                self._candidate = detected
                self._candidate_count = 1
            if self._candidate_count >= self._stable_needed:
                self._state = detected
                self._candidate = None
                self._candidate_count = 0
                return self._state
            return self._state

    def start(
        self,
        on_update: Callable[[Detection], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._last_notified = None

        def loop() -> None:
            while not self._stop_event.is_set():
                try:
                    committed = self.poll()
                    with self._lock:
                        changed = committed != self._last_notified
                        if changed:
                            self._last_notified = committed
                    if changed and not committed.is_empty():
                        on_update(committed)
                except Exception as exc:
                    if on_error is not None:
                        on_error(exc)
                self._stop_event.wait(self._poll_interval)

        self._thread = threading.Thread(target=loop, daemon=True, name="tekken-watcher")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5)
        self._thread = None
