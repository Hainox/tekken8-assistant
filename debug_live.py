import json
import time
from pathlib import Path

from tekken_assistant.capture.screen import ScreenCapture
from tekken_assistant.data.loader import load_characters
from tekken_assistant.detect.detector import ScreenDetector
from tekken_assistant.detect.matcher import NameMatcher
from tekken_assistant.detect.ocr import TesseractOcr

LOG = Path(__file__).parent / "debug_live.log"
cfg = json.loads((Path(__file__).parent / "config.json").read_text(encoding="utf-8"))
chars = load_characters()
matcher = NameMatcher(chars)
ocr = TesseractOcr()
det = ScreenDetector(capture=ScreenCapture(monitor_index=cfg["monitor_index"]), ocr=ocr, matcher=matcher)

deadline = time.time() + 600
prev = None
with LOG.open("w", encoding="utf-8") as f:
    while time.time() < deadline:
        try:
            d = det.detect()
        except Exception as exc:
            f.write(f"ERROR {exc}\n")
            f.flush()
            time.sleep(2)
            continue
        key = f"{d.player}|{d.opponent}"
        stamp = time.strftime("%H:%M:%S")
        if key != prev:
            f.write(f"{stamp} player={d.player} opponent={d.opponent}\n")
            f.flush()
            prev = key
        time.sleep(1)
    f.write("DONE\n")
