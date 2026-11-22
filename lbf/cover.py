"""Couverture 1080×1920 : image 3D du gag + titre court sur bandeau bleu + accent rouge.
Le titre reste dans le recadrage 3:4 de la grille du profil (y 240→1680)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

BLUE, WHITE, RED, INK = (22, 73, 255), (255, 253, 247), (239, 35, 60), (17, 24, 39)


def _fit(draw, text, font_file, max_w, start=150, min_size=60):
    size = start
    while size > min_size:
        f = ImageFont.truetype(str(config.FONTS / font_file), size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(config.FONTS / font_file), min_size)


def make_cover(still: Path, title: str, kicker: str, out: Path) -> Path:
    img = Image.open(still).convert("RGB").resize((1080, 1920))
    d = ImageDraw.Draw(img)
    words = title.upper().split()
    # deux lignes équilibrées au plus
    if len(words) >= 3:
        cut = (len(words) + 1) // 2
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    else:
        lines = [" ".join(words)]
    fonts = [_fit(d, ln, "Anton-Regular.ttf", 880, 170) for ln in lines]
    size = min(f.size for f in fonts)
    f = ImageFont.truetype(str(config.FONTS / "Anton-Regular.ttf"), size)
    line_h = int(size * 1.08)
    band_h = line_h * len(lines) + 70
    y0 = 1640 - band_h
    d.rectangle([0, y0, 1080, y0 + band_h], fill=BLUE)
    d.rectangle([0, y0 + band_h, 1080, y0 + band_h + 16], fill=RED)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text(((1080 - w) / 2, y0 + 30 + i * line_h), ln, font=f, fill=WHITE)
    kf = ImageFont.truetype(str(config.FONTS / "ArchivoBlack-Regular.ttf"), 34)
    kw = d.textlength(kicker.upper(), font=kf)
    d.rectangle([(1080 - kw) / 2 - 22, y0 - 64, (1080 + kw) / 2 + 22, y0], fill=RED)
    d.text(((1080 - kw) / 2, y0 - 58), kicker.upper(), font=kf, fill=WHITE)
    img.save(out, quality=92)
    # aperçu de la grille (recadrage 3:4 centré)
    img.crop((0, 240, 1080, 1680)).save(out.with_name(out.stem + "_grille.jpg"), quality=90)
    return out
