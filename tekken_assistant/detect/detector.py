from __future__ import annotations

import numpy as np
from PIL import Image, ImageOps
from tekken_assistant.capture.screen import ScreenCapture
from tekken_assistant.detect.matcher import NameMatcher
from tekken_assistant.detect.ocr import TesseractOcr, find_names
from tekken_assistant.models import Detection, NameHit

HUD_VARIANTS: tuple[tuple[int, int], ...] = (
    (185, 11),
    (200, 6),
    (170, 11),
    (200, 11),
    (170, 6),
)
HUD_UPSCALE = 3


def otsu_threshold(gray: Image.Image) -> int:
    arr = np.asarray(gray, dtype=np.uint8).ravel()
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    total = arr.size
    sum_total = float(np.dot(np.arange(256), hist))
    sum_b = 0.0
    w_b = 0.0
    best_t = 127
    best_var = -1.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += float(t) * float(hist[t])
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var = var
            best_t = t
    return best_t


class ScreenDetector:
    def __init__(
        self,
        capture: ScreenCapture,
        ocr: TesseractOcr,
        matcher: NameMatcher,
        min_name_height_ratio: float = 0.02,
        swap_sides: bool = False,
        hud_top_ratio: float = 0.16,
        hud_side_ratio: float = 0.32,
    ):
        self._capture = capture
        self._ocr = ocr
        self._matcher = matcher
        self._min_ratio = min_name_height_ratio
        self._swap = swap_sides
        self._hud_top_ratio = hud_top_ratio
        self._hud_side_ratio = hud_side_ratio

    def detect(self) -> Detection:
        image = self._capture.grab()
        return self.detect_image(image)

    def detect_image(self, image: Image.Image) -> Detection:
        width, height = image.size
        hits: list[NameHit] = []
        hits.extend(self._hud_hits(image, left=True))
        hits.extend(self._hud_hits(image, left=False))
        if len(self._dedupe(hits)) < 2:
            words = self._ocr.words(image)
            fallback = find_names(
                words, self._matcher, min_height=int(height * self._min_ratio)
            )
            hits.extend(h for h in fallback if h.h >= height * self._min_ratio)
        player, opponent = self._assign(self._dedupe(hits), width)
        if self._swap:
            player, opponent = opponent, player
        return Detection(player=player, opponent=opponent)

    def detect_from_words(self, words: list, screen_height: int) -> Detection:
        hits = find_names(words, self._matcher, min_height=int(screen_height * self._min_ratio))
        player, opponent = self._assign(self._dedupe(hits), screen_width=10000)
        if self._swap:
            player, opponent = opponent, player
        return Detection(player=player, opponent=opponent)

    def _hud_hits(self, image: Image.Image, left: bool) -> list[NameHit]:
        width, height = image.size
        top = int(height * self._hud_top_ratio)
        side = int(width * self._hud_side_ratio)
        strip_top = int(height * 0.065)
        strip_bottom = int(height * 0.11)
        strip_side = int(width * 0.25)
        if left:
            boxes = (
                (0, strip_top, strip_side, strip_bottom),
                (0, 0, side, top),
            )
        else:
            boxes = (
                (width - strip_side, strip_top, width, strip_bottom),
                (width - side, 0, width, top),
            )
        for box in boxes:
            hits = self._ocr_box(image, box)
            if hits:
                x_offset = box[0]
                return [
                    NameHit(
                        name=h.name,
                        x=x_offset + h.x // HUD_UPSCALE,
                        y=h.y // HUD_UPSCALE,
                        h=h.h // HUD_UPSCALE,
                        ratio=h.ratio,
                    )
                    for h in hits
                ]
        return []

    def _ocr_box(self, image: Image.Image, box: tuple[int, int, int, int]) -> list[NameHit]:
        crop = image.crop(box)
        gray = ImageOps.autocontrast(crop.convert("L"))
        gray = gray.resize(
            (gray.width * HUD_UPSCALE, gray.height * HUD_UPSCALE), Image.LANCZOS
        )
        otsu = otsu_threshold(gray)
        for threshold, psm in ((otsu, 6), (otsu, 11), (otsu, 7)) + HUD_VARIANTS:
            bw = gray.point(lambda p, t=threshold: 0 if p > t else 255)
            words = self._ocr.words(bw, psm=psm)
            hits = find_names(words, self._matcher, min_height=30)
            if hits:
                top_y = min(h.y for h in hits)
                top_h = max(h.h for h in hits if h.y == top_y)
                return [h for h in hits if h.y <= top_y + top_h]
        return []

    @staticmethod
    def _dedupe(hits: list[NameHit]) -> list[NameHit]:
        by_name: dict[str, NameHit] = {}
        for hit in hits:
            current = by_name.get(hit.name)
            if current is None:
                by_name[hit.name] = hit
            else:
                by_name[hit.name] = NameHit(
                    name=hit.name,
                    x=min(current.x, hit.x),
                    y=min(current.y, hit.y),
                    h=max(current.h, hit.h),
                    ratio=max(current.ratio, hit.ratio),
                )
        return list(by_name.values())

    @staticmethod
    def _assign(hits: list[NameHit], screen_width: int) -> tuple[str | None, str | None]:
        if not hits:
            return None, None
        if len(hits) > 2:
            hits = sorted(hits, key=lambda h: h.h, reverse=True)[:2]
        ordered = sorted(hits, key=lambda h: h.x)
        if len(ordered) == 1:
            only = ordered[0]
            if only.x < screen_width // 2:
                return only.name, None
            return None, only.name
        return ordered[0].name, ordered[1].name