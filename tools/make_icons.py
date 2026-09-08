from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
BG = (13, 17, 23, 255)
BORDER = (229, 161, 60, 255)
BTN_COLORS = [(47, 111, 208), (217, 161, 60), (46, 158, 79), (208, 69, 62)]
WHITE = (240, 244, 248, 255)
RED = (208, 69, 62, 255)

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)


def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 246, 246], radius=52, fill=BG, outline=BORDER, width=8)
    return img, d


def make_assistant() -> Image.Image:
    img, d = _base()
    d.text((128, 92), "T8", font=_font("arialbd.ttf", 108), fill=BORDER, anchor="mm")
    for i, color in enumerate(BTN_COLORS):
        cx = 62 + i * 44
        d.ellipse([cx - 17, 168, cx + 17, 202], fill=color)
        d.text((cx, 184), str(i + 1), font=_font("arialbd.ttf", 26), fill=WHITE, anchor="mm")
    return img


def make_stop() -> Image.Image:
    img, d = _base()
    d.ellipse([48, 48, 208, 208], fill=RED)
    w = 18
    d.line([(92, 92), (164, 164)], fill=WHITE, width=w)
    d.line([(164, 92), (92, 164)], fill=WHITE, width=w)
    return img


def save(img: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / name, format="ICO", sizes=SIZES)


def main() -> None:
    save(make_assistant(), "assistant.ico")
    save(make_stop(), "stop.ico")
    print("icons ->", OUT_DIR)


if __name__ == "__main__":
    main()
