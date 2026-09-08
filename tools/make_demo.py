from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FRAME = ROOT / "debug_frames" / "live_0.png"
OUT = ROOT / "assets" / "demo.png"

BG = (13, 17, 23)
PANEL_BG = (19, 26, 34)
BAR_BG = (10, 14, 19)
FG = (230, 230, 230)
DIM = (138, 147, 158)
ACCENT = (229, 161, 60)
PLAYER = (126, 196, 106)
OPPONENT = (217, 99, 90)
MONO = (159, 211, 168)
DIR_COLOR = (110, 193, 255)
BTN = {1: (47, 111, 208), 2: (217, 161, 60), 3: (46, 158, 79), 4: (208, 69, 62)}

F = "C:/Windows/Fonts/"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(F + name, size)


def seg(size: int) -> ImageFont.FreeTypeFont:
    return font("segoeui.ttf", size)


def segb(size: int) -> ImageFont.FreeTypeFont:
    return font("segoeuib.ttf", size)


def mono(size: int) -> ImageFont.FreeTypeFont:
    return font("consola.ttf", size)


def sym(size: int) -> ImageFont.FreeTypeFont:
    return font("seguisym.ttf", size)


def chip(d: ImageDraw.ImageDraw, x: int, y: int, label: str, color: tuple) -> int:
    w = d.textlength(label, font=mono(15)) + 12
    d.rounded_rectangle([x, y - 3, x + w, y + 19], radius=5, fill=color)
    d.text((x + 6, y), label, font=mono(15), fill=(255, 255, 255))
    return w


def draw_notation(d: ImageDraw.ImageDraw, x: int, y: int, tokens: list[tuple]) -> int:
    cx = x
    for kind, val in tokens:
        if kind == "dir":
            d.text((cx, y), val, font=sym(17), fill=DIR_COLOR)
            cx += d.textlength(val, font=sym(17)) + 2
        elif kind == "btn":
            cx += chip(d, cx, y, val, BTN[int(val)]) + 3
        elif kind == "sep":
            d.text((cx, y + 1), val, font=segb(14), fill=ACCENT)
            cx += d.textlength(val, font=segb(14)) + 6
        elif kind in ("comma", "plus"):
            d.text((cx, y), val, font=mono(15), fill=DIM)
            cx += d.textlength(val, font=mono(15)) + 1
        else:
            d.text((cx, y), val, font=mono(15), fill=MONO)
            cx += d.textlength(val, font=mono(15)) + 3
    return cx


def main() -> None:
    img = Image.open(FRAME).convert("RGBA").resize((1600, 900))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # ---------- compact badge (top right) ----------
    bx, by, bw, bh = 1600 - 24 - 268, 18, 268, 54
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=BAR_BG + (235,), outline=(35, 43, 54, 255), width=1)
    d.ellipse([bx + 12, by + bh // 2 - 5, bx + 22, by + bh // 2 + 5], fill=PLAYER)
    d.text((bx + 32, by + 15), "Victor  vs  Steve", font=segb(16), fill=FG)

    # ---------- expanded panel (left) ----------
    px, py, pw, ph = 24, 80, 452, 600
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=12, fill=BG + (238,), outline=(35, 43, 54, 255), width=1)
    # title bar
    d.rounded_rectangle([px, py, px + pw, py + 34], radius=12, fill=BAR_BG + (255,))
    d.rectangle([px, py + 20, px + pw, py + 34], fill=BAR_BG + (255,))
    d.text((px + 12, py + 8), "TEKKEN 8", font=segb(14), fill=ACCENT)
    d.text((px + pw - 12, py + 10), "Слежение включено", font=seg(12), fill=PLAYER, anchor="ra")
    # manual row
    d.text((px + 12, py + 44), "Вручную:", font=seg(12), fill=DIM)
    for i, name in enumerate(("Victor", "Steve")):
        cx = px + 82 + i * 130
        d.rounded_rectangle([cx, py + 40, cx + 118, py + 62], radius=4, fill=BAR_BG + (255,))
        d.text((cx + 8, py + 44), name, font=seg(12), fill=FG)
        d.text((cx + 100, py + 44), "▾", font=sym(12), fill=DIM)
    d.rounded_rectangle([px + pw - 66, py + 44, px + pw - 52, py + 58], radius=3, outline=DIM + (255,), width=1)
    d.text((px + pw - 65, py + 43), "✓", font=sym(12), fill=PLAYER)
    d.text((px + pw - 48, py + 44), "Авто", font=seg(12), fill=DIM)
    # tabs
    tabs = ("Комбо", "План", "Фишки", "Противник", "Словарь")
    tw = pw / len(tabs)
    for i, t in enumerate(tabs):
        active = i == 0
        color = ACCENT if active else DIM
        if active:
            d.rectangle([px + i * tw, py + 72, px + (i + 1) * tw, py + 106], fill=PANEL_BG + (255,))
            d.rectangle([px + i * tw, py + 103, px + (i + 1) * tw, py + 106], fill=ACCENT + (255,))
        d.text((px + i * tw + tw / 2, py + 82), t, font=segb(13), fill=color, anchor="ma")
    # body
    ty = py + 122
    d.text((px + 14, ty), "Victor", font=segb(21), fill=PLAYER)
    d.text((px + 14, ty + 30), "Дэш-стайл · сложность: средняя", font=seg(12), fill=DIM)
    ty += 62
    d.text((px + 14, ty), "КОМБО", font=segb(14), fill=ACCENT)
    ty += 26
    combos = [
        ("Простое BnB", "~68", [("dir", "↘"), ("btn", "2"), ("dir", "»"), ("btn", "3"), ("dir", "↘"), ("btn", "1"), ("dir", "→"), ("btn", "1"), ("plus", "+"), ("btn", "2")]),
        ("Оптимальное", "~86", [("dir", "↘"), ("btn", "2"), ("dir", "»"), ("btn", "3"), ("dir", "↘"), ("btn", "2"), ("dir", "↘"), ("btn", "1"), ("dir", "→"), ("btn", "1"), ("plus", "+"), ("btn", "2")]),
        ("Со стены / Heat", "~89", [("dir", "→"), ("btn", "1"), ("plus", "+"), ("btn", "2"), ("word", "Heat"), ("dir", "↘"), ("btn", "2"), ("dir", "»"), ("btn", "3")]),
    ]
    for label, dmg, tokens in combos:
        d.text((px + 14, ty), "◆ " + label, font=seg(13), fill=FG)
        d.text((px + pw - 16, ty + 1), dmg, font=seg(12), fill=ACCENT, anchor="ra")
        ty += 24
        draw_notation(d, px + 22, ty, tokens)
        ty += 32
    ty += 6
    d.text((px + 14, ty), "КОМБО С САЙТА (kagewebsite)", font=segb(14), fill=ACCENT)
    ty += 26
    d.text((px + 14, ty), "◆ Стенное", font=seg(13), fill=FG)
    d.text((px + pw - 16, ty + 1), "~144", font=seg(12), fill=ACCENT, anchor="ra")
    ty += 24
    draw_notation(d, px + 22, ty, [
        ("dir", "↘"), ("btn", "2"), ("sep", "►"), ("dir", "↓"), ("dir", "↙"), ("dir", "←"),
        ("btn", "1"), ("plus", "+"), ("btn", "2"), ("sep", "►"), ("word", "Dash"),
        ("btn", "3"), ("comma", ","), ("btn", "2"), ("dir", "←"),
    ])
    ty += 32
    d.text((px + 22, ty), "[kage #2299] клик по нотации — копировать", font=seg(11), fill=DIM)

    # glossary hint (bottom right of panel)
    d.text((px + 14, py + ph - 30), "Вкладка «Словарь»: WS, iWR, KBD, CH, Oki…", font=seg(11), fill=DIM)

    # ---------- bottom caption strip ----------
    strip_y, strip_h = 856, 44
    d.rectangle([0, strip_y, img.width, strip_y + strip_h], fill=(10, 14, 19, 200))
    caption = "Оверлей можно перетащить на второй монитор (F7) — или он сам станет прозрачным через 8 секунд без наведения мыши"
    d.text(
        (img.width // 2, strip_y + strip_h // 2),
        caption,
        font=seg(15),
        fill=(255, 255, 255, 255),
        anchor="mm",
    )

    out = Image.alpha_composite(img, overlay).convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)
    print("demo ->", OUT)


if __name__ == "__main__":
    main()
