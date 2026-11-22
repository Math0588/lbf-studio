"""Designs t-shirts v2 — compositions graphiques, ton provocateur, sans nom de compte.
Fichiers d'impression 4500×5400 transparents (version encre foncée pour t-shirts clairs, encre claire pour
t-shirts foncés) + maquettes + planche d'aperçu. Slogans originaux (aucune reprise d'un slogan existant)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

OUT = config.ROOT / "brand" / "boutique_v2"
W, H = 4500, 5400
RED = (239, 35, 60, 255)
BLUE = (22, 73, 255, 255)
ANTON = str(config.FONTS / "Anton-Regular.ttf")
ARCH = str(config.FONTS / "ArchivoBlack-Regular.ttf")


def F(path, size):
    return ImageFont.truetype(path, size)


def fit(d, text, font_path, max_w, start, min_size=80):
    s = start
    while s > min_size and d.textlength(text, font=F(font_path, s)) > max_w:
        s -= 10
    return F(font_path, s)


def center(d, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)
    return y + font.size


def box(d, xy, ink, width=40):
    d.rectangle(xy, outline=ink, width=width)


# ----------------------------------------------------------------------------- compositions


def cerfa(d, ink):
    """Faux formulaire administratif : l'absurde de la bureaucratie, lisible de loin."""
    d.rectangle([250, 250, W - 250, 650], fill=ink)
    center(d, 300, "CERFA N° 2027-404", F(ARCH, 260), (0, 0, 0, 0))
    y = center(d, 760, "DÉCLARATION", F(ANTON, 520), ink)
    y = center(d, y + 40, "D'OPINION POLITIQUE", F(ANTON, 360), ink)
    rows = [("GAUCHE", False), ("DROITE", False), ("JE VEUX JUSTE MANGER", True)]
    y += 220
    for label, checked in rows:
        box(d, [450, y, 850, y + 400], ink, 45)
        if checked:
            d.line([(500, y + 210), (640, y + 350), (900, y - 60)], fill=RED, width=110, joint="curve")
        d.text((1000, y + 10), label, font=fit(d, label, ANTON, W - 1300, 360), fill=RED if checked else ink)
        y += 560
    d.text((450, y + 60), "Signature :", font=F(ARCH, 150), fill=ink)
    d.line([(1350, y + 210), (W - 450, y + 210)], fill=ink, width=20)


def warning(d, ink):
    """Panneau d'avertissement : le repas de famille."""
    tri = [(W / 2, 300), (W - 600, 2100), (600, 2100)]
    d.polygon(tri, outline=ink, width=150)
    center(d, 900, "!", F(ANTON, 1100), RED)
    y = center(d, 2350, "ATTENTION", F(ANTON, 900), ink)
    y = center(d, y + 150, "PARLE POLITIQUE", F(ANTON, 520), RED)
    y = center(d, y + 80, "AU REPAS DE FAMILLE", F(ANTON, 380), ink)
    center(d, y + 120, "Ne pas nourrir après le dessert.", F(ARCH, 170), ink)


def asterisk(top, bottom_note, tag):
    """« SLOGAN* » en très gros sur deux lignes + note qui retourne tout : la claque est en bas."""
    def draw(d, ink):
        lines = top.split("|")
        lines[-1] += "*"
        f = min((fit(d, l, ANTON, W - 300, 1500) for l in lines), key=lambda x: x.size)
        y = 400
        for l in lines:
            y = center(d, y, l, f, ink) + 30
        d.rectangle([300, y + 330, W - 300, y + 380], fill=RED)
        words, cur, out = bottom_note.split(), "", []
        for w in words:
            if len(cur) + len(w) > 22 and cur:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        out.append(cur)
        y += 560
        for l in out:
            y = center(d, y, l, F(ARCH, 270), RED) + 40
        center(d, y + 150, tag, F(ARCH, 200), ink)
    return draw


def loading(d, ink):
    """Barre de chargement des réponses concrètes."""
    y = center(d, 500, "RÉPONSES", F(ANTON, 900), ink)
    y = center(d, y + 40, "CONCRÈTES", F(ANTON, 900), ink)
    y += 350
    box(d, [350, y, W - 350, y + 600], ink, 60)
    seg = (W - 900) / 10
    for i in range(10):
        x0 = 450 + i * seg
        if i < 9:
            d.rectangle([x0 + 20, y + 100, x0 + seg - 20, y + 500], fill=RED if i == 8 else ink)
    center(d, y + 800, "CHARGEMENT… 99 %", F(ANTON, 450), RED)
    center(d, y + 1350, "depuis 2017", F(ARCH, 200), ink)


def bubble(d, ink):
    """Bulle de BD : la réponse universelle."""
    d.rounded_rectangle([300, 600, W - 300, 3300], radius=500, outline=ink, width=110)
    d.polygon([(1300, 3240), (1900, 3240), (1100, 4300)], fill=ink)
    d.polygon([(1430, 3150), (1780, 3150), (1260, 3900)], fill=(0, 0, 0, 0))
    y = center(d, 1250, "EXCELLENTE", fit(d, "EXCELLENTE", ANTON, W - 1100, 800), ink)
    center(d, y + 80, "QUESTION.", fit(d, "QUESTION.", ANTON, W - 1100, 800), RED)
    center(d, 4500, "(prochaine question ?)", F(ARCH, 200), ink)


def debate(d, ink):
    """Survivant du débat."""
    y = center(d, 500, "J'AI REGARDÉ", F(ANTON, 650), ink)
    y = center(d, y + 30, "UN DÉBAT", F(ANTON, 1000), RED)
    y = center(d, y + 30, "EN ENTIER.", F(ANTON, 650), ink)
    d.rectangle([700, y + 250, W - 700, y + 290], fill=ink)
    center(d, y + 450, "JE NE SUIS PLUS", F(ANTON, 420), ink)
    center(d, y + 900, "LE MÊME.", F(ANTON, 420), ink)


def gps(side):
    def draw(d, ink):
        center(d, 350, "RECALCUL DE L'ITINÉRAIRE…", fit(d, "RECALCUL DE L'ITINÉRAIRE…", ARCH, W - 600, 230), ink)
        arrow_left = side == "gauche"
        x0, x1 = (W - 700, 700) if arrow_left else (700, W - 700)
        d.line([(W / 2, 3000), (W / 2, 1600), (x1, 1600)], fill=RED, width=380, joint="curve")
        tip = [(x1 + (-1 if arrow_left else 1) * -0, 1100), (x1 + (-450 if arrow_left else 450), 1600), (x1, 2100)]
        d.polygon(tip, fill=RED)
        y = center(d, 3250, f"TOUJOURS PLUS À {side.upper()}", fit(d, f"TOUJOURS PLUS À {side.upper()}", ANTON, W - 500, 560), ink)
        center(d, y + 150, "Vous êtes arrivé. Ou pas.", F(ARCH, 190), ink)
    return draw


def cauchemar(chute: str, petit: str = ""):
    """« J'AI FAIT UN CAUCHEMAR » (accroche courante) + chute originale en gros, lune et zZz."""
    def draw(d, ink):
        # croissant de lune
        d.ellipse([W / 2 - 520, 250, W / 2 + 280, 1050], fill=ink)
        d.ellipse([W / 2 - 300, 170, W / 2 + 500, 970], fill=(0, 0, 0, 0))
        d.text((W / 2 + 330, 260), "z", font=F(ANTON, 260), fill=RED)
        d.text((W / 2 + 520, 120), "Z", font=F(ANTON, 360), fill=RED)
        y = center(d, 1250, "J'AI FAIT UN", F(ANTON, 520), ink)
        y = center(d, y + 20, "CAUCHEMAR :", F(ANTON, 760), ink)
        lines = chute.split("|")
        f = min((fit(d, l, ANTON, W - 400, 900) for l in lines), key=lambda x: x.size)
        y += 260
        for l in lines:
            y = center(d, y, l, f, RED) + 20
        if petit:
            center(d, y + 200, petit, fit(d, petit, ARCH, W - 900, 220), ink)
    return draw


DESIGNS = [
    ("cauchemar-tonton", "Tout le monde prend", cauchemar("J'ÉTAIS D'ACCORD|AVEC TONTON.", "(au dessert, en plus)")),
    ("cauchemar-patron", "Ça pique la gauche", cauchemar("MON PATRON|AVAIT RAISON.", "(je me suis réveillé en sueur)")),
    ("cauchemar-isf", "Ça pique la droite", cauchemar("JE PAYAIS|L'ISF.", "(et j'étais content)")),
    ("cauchemar-centre", "Tout le monde prend", cauchemar("J'ÉTAIS D'EXTRÊME|CENTRE.", "(en même temps)")),
    ("cauchemar-tofu", "Ça pique la droite", cauchemar("JE MANGEAIS|DU TOFU.", "(dans une trottinette électrique)")),
    ("cauchemar-merite", "Ça pique la gauche", cauchemar("JE MÉRITAIS|MON SALAIRE.", "(personne ne m'a cru)")),
    ("cerfa-opinion", "Tout le monde prend", cerfa),
    ("attention-repas", "Tout le monde prend", warning),
    ("anticapitaliste", "Ça pique la gauche", asterisk("ANTI|CAPITALISTE", "*sauf l'iPhone, Netflix et les soldes", "(paiement en 4 fois accepté)")),
    ("patriote", "Ça pique la droite", asterisk("100 %|PATRIOTE", "*t-shirt fabriqué à l'autre bout du monde", "(comme le reste)")),
    ("ecolo", "Ça pique la gauche", asterisk("ÉCOLO", "*en SUV, mais électrique le dimanche", "(et en avion l'été)")),
    ("ordre", "Ça pique la droite", asterisk("L'ORDRE|ET LA LOI", "*sauf le code de la route", "(et mes impôts)")),
    ("reponses-concretes", "Tout le monde prend", loading),
    ("excellente-question", "Tout le monde prend", bubble),
    ("debat-entier", "Tout le monde prend", debate),
    ("gps-gauche", "Ça pique la gauche", gps("gauche")),
    ("gps-droite", "Ça pique la droite", gps("droite")),
]


def render(name, fn, ink):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fn(d, ink)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def mockup(design: Image.Image, tee, path: Path):
    Wm, Hm = 1200, 1350
    im = Image.new("RGB", (Wm, Hm), "#E9E6DF")
    d = ImageDraw.Draw(im)
    body = [(320, 220), (470, 165), (530, 215), (670, 215), (730, 165), (880, 220), (1070, 420), (950, 520),
            (880, 460), (880, 1240), (320, 1240), (320, 460), (250, 520), (130, 420)]
    d.polygon(body, fill=tee)
    d.arc([530, 150, 670, 270], 0, 180, fill="#00000044", width=8)
    dz = design.copy()
    dz.thumbnail((440, 560))
    im.paste(dz, ((Wm - dz.width) // 2, 330), dz)
    im.save(path, quality=88)
    return im


def main():
    (OUT / "designs").mkdir(parents=True, exist_ok=True)
    (OUT / "maquettes").mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1200 * 6, 1350 * 3), "#F4F1EA")
    k = 0
    for name, coll, fn in DESIGNS:
        dark_ink = render(name, fn, (17, 24, 39, 255))
        light_ink = render(name, fn, (255, 253, 247, 255))
        dark_ink.save(OUT / "designs" / f"{name}_tshirt-clair.png")
        light_ink.save(OUT / "designs" / f"{name}_tshirt-fonce.png")
        m = mockup(light_ink if k % 2 else dark_ink, "#1A1A1F" if k % 2 else "#F3EBDD",
                   OUT / "maquettes" / f"{name}.jpg")
        if k < 18:
            sheet.paste(m, ((k % 6) * 1200, (k // 6) * 1350))
        k += 1
    sheet.resize((3600, 2025)).save(OUT / "_planche.jpg", quality=85)
    print(k, "designs ->", OUT)


if __name__ == "__main__":
    main()
