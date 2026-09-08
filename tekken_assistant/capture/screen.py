from __future__ import annotations

from PIL import Image


class ScreenCapture:
    def __init__(self, monitor_index: int = 1):
        self.monitor_index = monitor_index

    def grab(self) -> Image.Image:
        import mss

        with mss.mss() as sct:
            monitors = sct.monitors
            if len(monitors) <= 1:
                monitor = monitors[0]
            else:
                index = min(max(self.monitor_index, 1), len(monitors) - 1)
                monitor = monitors[index]
            shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
