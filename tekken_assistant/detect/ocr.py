from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image
from tekken_assistant.models import NameHit, OcrWord
from tekken_assistant.detect.matcher import NameMatcher

_COMMON_TESSERACT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def resolve_tesseract_cmd(explicit: str = "") -> str:
    if explicit:
        return explicit
    found = shutil.which("tesseract")
    if found:
        return found
    for path in _COMMON_TESSERACT_PATHS:
        if Path(path).exists():
            return path
    return ""


class TesseractOcr:
    def __init__(
        self,
        language: str = "eng",
        min_confidence: float = 40.0,
        tesseract_cmd: str = "",
    ):
        import pytesseract

        self._pytesseract = pytesseract
        resolved = resolve_tesseract_cmd(tesseract_cmd)
        if resolved:
            pytesseract.pytesseract.tesseract_cmd = resolved
        self._language = language
        self._min_confidence = min_confidence

    def check(self) -> None:
        self._pytesseract.get_tesseract_version()

    def words(self, image: Image.Image, psm: int = 11) -> list[OcrWord]:
        config = f"--psm {psm}"
        data = self._pytesseract.image_to_data(
            image,
            lang=self._language,
            config=config,
            output_type=self._pytesseract.Output.DICT,
        )
        words: list[OcrWord] = []
        for i in range(len(data["text"])):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            conf = float(data["conf"][i])
            if conf < self._min_confidence:
                continue
            words.append(
                OcrWord(
                    text=text,
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    w=int(data["width"][i]),
                    h=int(data["height"][i]),
                    conf=conf,
                )
            )
        return words


def _group_lines(words: list[OcrWord], tolerance: int) -> list[list[OcrWord]]:
    ordered = sorted(words, key=lambda w: (w.cy, w.cx))
    lines: list[list[OcrWord]] = []
    for word in ordered:
        if lines and abs(word.cy - lines[-1][-1].cy) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])
    for line in lines:
        line.sort(key=lambda w: w.cx)
    return lines


def find_names(
    words: list[OcrWord],
    matcher: NameMatcher,
    min_height: int = 0,
    line_tolerance: int = 12,
) -> list[NameHit]:
    candidates = [w for w in words if w.h >= min_height and len(w.text) >= 2]
    hits: list[NameHit] = []
    for line in _group_lines(candidates, line_tolerance):
        accepted: list[NameHit] = []
        occupied: set[int] = set()
        n = len(line)
        for start in range(n):
            if start in occupied:
                continue
            candidates: list[tuple[float, int, NameHit]] = []
            for span in (3, 2, 1):
                end = start + span
                if end > n or any(i in occupied for i in range(start, end)):
                    continue
                text = " ".join(w.text for w in line[start:end])
                matched = matcher.match(text)
                if matched is None:
                    continue
                name, ratio = matched
                first, last = line[start], line[end - 1]
                hit = NameHit(
                    name=name,
                    x=first.x,
                    y=first.y,
                    h=max(w.h for w in line[start:end]),
                    ratio=ratio,
                )
                candidates.append((ratio, span, hit))
            if not candidates:
                continue
            candidates.sort(key=lambda c: (-c[0], -c[1]))
            ratio, span, hit = candidates[0]
            end = start + span
            accepted.append(hit)
            occupied.update(range(start, end))
        hits.extend(accepted)
    return hits
