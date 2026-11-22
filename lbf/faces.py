"""Visages des personnages cubiques (textures originales générées, transparentes, 512×512).
Expressions lisibles en gros plan comme en plan large : yeux, sourcils, cernes, bouche."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import config

OUT = config.ASSETS / "faces"
INK = (24, 22, 28, 255)
WHITE = (255, 255, 255, 255)
MOUTH = (110, 28, 34, 255)
BAG = (120, 90, 110, 140)
IRIS = {"brun": (92, 60, 38, 255), "bleu": (52, 104, 170, 255), "vert": (62, 120, 80, 255)}
S = 512


def _eye(d, cx, cy, kind, iris):
    w, h = 74, 56
    if kind == "closed":
        d.arc([cx - w / 2, cy - 18, cx + w / 2, cy + 22], 200, 340, fill=INK, width=9)
        return
    if kind == "happy":
        d.arc([cx - w / 2, cy - 6, cx + w / 2, cy + 44], 200, 340, fill=INK, width=10)
        return
    if kind == "wide":
        w, h = 86, 86
    d.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=WHITE, outline=INK, width=6)
    r = 22 if kind != "wide" else 18
    d.ellipse([cx - r, cy - r + 4, cx + r, cy + r + 4], fill=iris)
    d.ellipse([cx - 9, cy - 5, cx + 9, cy + 13], fill=INK)
    d.ellipse([cx + 4, cy - 6, cx + 11, cy + 1], fill=WHITE)
    if kind in ("tired", "half"):
        # paupière lourde
        d.chord([cx - w / 2 - 3, cy - h / 2 - 4, cx + w / 2 + 3, cy + h / 2 + 4], 180, 360, fill=(70, 40, 30, 90))
        d.line([cx - w / 2, cy + 1, cx + w / 2, cy + 1], fill=INK, width=8)
    if kind == "tired":
        for k in (0, 1):  # cernes
            d.arc([cx - w / 2 + 4, cy + 8 + k * 14, cx + w / 2 - 4, cy + 44 + k * 14], 15, 165, fill=BAG, width=7)
    if kind == "smug":
        d.chord([cx - w / 2 - 3, cy - h / 2 - 4, cx + w / 2 + 3, cy + h / 2 + 4], 180, 360, fill=(70, 40, 30, 90))
        d.line([cx - w / 2, cy - 2, cx + w / 2, cy + 4], fill=INK, width=8)


def _brows(d, kind):
    if kind == "angry":
        d.line([150, 150, 225, 182], fill=INK, width=20)
        d.line([362, 150, 287, 182], fill=INK, width=20)
    elif kind == "worried":
        d.line([150, 178, 225, 150], fill=INK, width=18)
        d.line([362, 178, 287, 150], fill=INK, width=18)
    elif kind == "raised":
        d.arc([140, 120, 235, 175], 200, 340, fill=INK, width=16)
        d.arc([277, 120, 372, 175], 200, 340, fill=INK, width=16)
    elif kind == "smug":
        d.line([150, 168, 225, 162], fill=INK, width=18)
        d.arc([277, 128, 372, 180], 200, 340, fill=INK, width=16)
    else:
        d.line([150, 165, 225, 160], fill=INK, width=18)
        d.line([362, 165, 287, 160], fill=INK, width=18)


def _mouth(d, kind):
    if kind == "flat":
        d.line([215, 380, 297, 380], fill=INK, width=12)
    elif kind == "sad":
        d.arc([205, 372, 307, 430], 200, 340, fill=INK, width=12)
    elif kind == "smile":
        d.arc([196, 320, 316, 400], 20, 160, fill=INK, width=12)
    elif kind == "grin":
        d.chord([196, 330, 316, 420], 0, 180, fill=MOUTH, outline=INK, width=8)
        d.rectangle([216, 376, 296, 392], fill=WHITE)
    elif kind == "smirk":
        d.arc([226, 330, 326, 396], 20, 120, fill=INK, width=12)
        d.line([200, 368, 236, 372], fill=INK, width=12)
    elif kind == "o":
        d.ellipse([226, 340, 286, 420], fill=MOUTH, outline=INK, width=8)
    elif kind == "talk":
        d.ellipse([206, 350, 306, 405], fill=MOUTH, outline=INK, width=8)
    elif kind == "shout":
        d.chord([186, 340, 326, 460], 180, 360, fill=MOUTH, outline=INK, width=8)
        d.rectangle([214, 404, 298, 418], fill=WHITE)


EXPRESSIONS = {
    "neutre": ("open", "normal", "flat"),
    "blase": ("tired", "normal", "flat"),
    "fatigue": ("tired", "worried", "sad"),
    "content": ("happy", "raised", "smile"),
    "fier": ("smug", "smug", "smirk"),
    "choque": ("wide", "raised", "o"),
    "colere": ("open", "angry", "shout"),
    "parle": ("open", "normal", "talk"),
    "parle_fier": ("smug", "smug", "talk"),
    "sourire_pro": ("open", "raised", "grin"),
    "dort": ("closed", "normal", "flat"),
}


def make(expr: str, iris: str = "brun") -> Path:
    eye, brow, mouth = EXPRESSIONS[expr]
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{expr}_{iris}.png"
    if p.exists():
        return p
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _brows(d, brow)
    _eye(d, 188, 238, eye, IRIS[iris])
    _eye(d, 324, 238, eye, IRIS[iris])
    _mouth(d, mouth)
    # traits agrandis (×1,3) pour rester lisibles sur un écran de téléphone
    im = im.crop((58, 70, 454, 466)).resize((S, S), Image.LANCZOS)
    im.save(p)
    return p


def make_all() -> list[Path]:
    return [make(e, i) for e in EXPRESSIONS for i in IRIS]


if __name__ == "__main__":
    ps = make_all()
    sheet = Image.new("RGBA", (S * 6, S * 2), (230, 190, 150, 255))
    for k, e in enumerate(list(EXPRESSIONS)[:12]):
        sheet.alpha_composite(Image.open(OUT / f"{e}_bleu.png"), ((k % 6) * S, (k // 6) * S))
    sheet.convert("RGB").resize((S * 3, S)).save(OUT / "_planche.jpg")
    print(len(ps), "visages")
