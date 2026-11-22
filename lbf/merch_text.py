"""T-shirts « texte seul » — typographie soignée (Archivo variable, Bricolage Grotesque ; licences SIL OFL).
Série « J'ai fait un cauchemar : … » avec chutes originales, sans nom de compte, sans illustration."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

OUT = config.ROOT / "brand" / "boutique_v3"
W = 4500
RED = (239, 35, 60, 255)
ARCHIVO = str(config.FONTS / "Archivo-Variable.ttf")
BRICO = str(config.FONTS / "BricolageGrotesque-Variable.ttf")


def font(path, size, wght=900, wdth=None, opsz=None):
    f = ImageFont.truetype(path, size)
    axes = []
    for a in f.get_variation_axes():
        n = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
        if n == "Weight":
            axes.append(min(max(wght, a["minimum"]), a["maximum"]))
        elif n == "Width":
            axes.append(min(max(wdth if wdth is not None else a["default"], a["minimum"]), a["maximum"]))
        elif n == "Optical size":
            axes.append(min(max(opsz if opsz is not None else a["maximum"], a["minimum"]), a["maximum"]))
        else:
            axes.append(a["default"])
    f.set_variation_by_axes(axes)
    return f


def sized(d, text, maker, max_w, start):
    s = start
    while s > 60:
        f = maker(s)
        if d.textlength(text, font=f) <= max_w:
            return f
        s -= 8
    return maker(60)


def line(d, y, text, f, fill, tracking=0):
    """Texte centré, avec interlettrage optionnel (en % de la taille)."""
    if tracking:
        widths = [d.textlength(c, font=f) for c in text]
        tw = sum(widths) + tracking * f.size / 100 * (len(text) - 1)
        x = (W - tw) / 2
        for c, w in zip(text, widths):
            d.text((x, y), c, font=f, fill=fill)
            x += w + tracking * f.size / 100
    else:
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)
    bb = d.textbbox((0, y), text, font=f)
    return bb[3]


STYLES = {
    # A : grotesque condensée très grasse, esprit streetwear / affiche
    "A": dict(head=lambda s: font(ARCHIVO, s, 900, 62), punch=lambda s: font(ARCHIVO, s, 900, 62),
              small=lambda s: font(ARCHIVO, s, 700, 100), track_head=8),
    # B : Bricolage Grotesque, plus « mode », chute en très gras
    "B": dict(head=lambda s: font(BRICO, s, 800, 75, 96), punch=lambda s: font(BRICO, s, 800, 75, 96),
              small=lambda s: font(BRICO, s, 500, 100, 24), track_head=0),
    # C : mélange : accroche fine espacée, chute condensée énorme
    "C": dict(head=lambda s: font(ARCHIVO, s, 500, 100), punch=lambda s: font(ARCHIVO, s, 900, 62),
              small=lambda s: font(ARCHIVO, s, 600, 100), track_head=25),
}


def cauchemar(chute: str, petit: str, ink, style="A"):
    st = STYLES[style]
    im = Image.new("RGBA", (W, 6000), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 200
    y = line(d, y, "J'AI FAIT UN CAUCHEMAR :", sized(d, "J'AI FAIT UN CAUCHEMAR :", st["head"], W - 700, 420),
             ink, st["track_head"]) + 230
    lines = chute.split("|")
    f = min((sized(d, l, st["punch"], W - 250, 1500) for l in lines), key=lambda x: x.size)
    for l in lines:
        y = line(d, y, l, f, RED) + int(f.size * 0.12)
    if petit:
        y = line(d, y + 180, petit, sized(d, petit, st["small"], W - 1400, 200), ink)
    bb = im.getbbox()
    return im.crop(bb)


SERIE = [
    ("cauchemar-tonton", "J'ÉTAIS D'ACCORD|AVEC TONTON.", "au dessert, en plus."),
    ("cauchemar-patron", "MON PATRON|AVAIT RAISON.", "je me suis réveillé en sueur."),
    ("cauchemar-isf", "JE PAYAIS|L'ISF.", "et j'étais content."),
    ("cauchemar-centre", "J'ÉTAIS D'EXTRÊME|CENTRE.", "en même temps."),
    ("cauchemar-tofu", "JE MANGEAIS|DU TOFU.", "en trottinette électrique."),
    ("cauchemar-merite", "JE MÉRITAIS|MON SALAIRE.", "personne ne m'a cru."),
]


def mockup(design, tee):
    Wm, Hm = 1200, 1350
    im = Image.new("RGB", (Wm, Hm), "#E9E6DF")
    d = ImageDraw.Draw(im)
    body = [(320, 220), (470, 165), (530, 215), (670, 215), (730, 165), (880, 220), (1070, 420), (950, 520),
            (880, 460), (880, 1240), (320, 1240), (320, 460), (250, 520), (130, 420)]
    d.polygon(body, fill=tee)
    d.arc([530, 150, 670, 270], 0, 180, fill="#00000044", width=8)
    dz = design.copy()
    dz.thumbnail((470, 600))
    im.paste(dz, ((Wm - dz.width) // 2, 340), dz)
    return im


def compare():
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (3600, 1350), "#F4F1EA")
    for i, s in enumerate("ABC"):
        dz = cauchemar("MON PATRON|AVAIT RAISON.", "je me suis réveillé en sueur.", (255, 253, 247, 255), s)
        sheet.paste(mockup(dz, "#1A1A1F"), (i * 1200, 0))
    sheet.save(OUT / "_comparaison_polices.jpg", quality=88)


def build(style="A"):
    (OUT / "designs").mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1200 * 6, 1350 * 2), "#F4F1EA")
    for i, (name, chute, petit) in enumerate(SERIE):
        clair = cauchemar(chute, petit, (17, 24, 39, 255), style)
        fonce = cauchemar(chute, petit, (255, 253, 247, 255), style)
        clair.save(OUT / "designs" / f"{name}_tshirt-clair.png")
        fonce.save(OUT / "designs" / f"{name}_tshirt-fonce.png")
        sheet.paste(mockup(clair, "#F3EBDD"), (i * 1200, 0))
        sheet.paste(mockup(fonce, "#1A1A1F"), (i * 1200, 1350))
    sheet.resize((3600, 1350)).save(OUT / "_planche.jpg", quality=88)


# --- Style « R » : proche du t-shirt de référence (minuscules manuscrites + grosses capitales arrondies) ---
FONTS_R = {
    "fredoka": lambda s: font(str(config.FONTS / "Fredoka-Variable.ttf"), s, 700, 100),
    "baloo": lambda s: font(str(config.FONTS / "Baloo2-Variable.ttf"), s, 800),
    "mali": lambda s: ImageFont.truetype(str(config.FONTS / "Mali-Bold.ttf"), s),
    "comic": lambda s: ImageFont.truetype(str(config.FONTS / "ComicNeue-Bold.ttf"), s),
    "patrick": lambda s: ImageFont.truetype(str(config.FONTS / "PatrickHand-Regular.ttf"), s),
    "itim": lambda s: ImageFont.truetype(str(config.FONTS / "Itim-Regular.ttf"), s),
}
COMBOS = {"R1": ("fredoka", "patrick"), "R2": ("baloo", "itim"), "R3": ("mali", "mali"), "R4": ("comic", "comic")}
BLUE = (30, 108, 190, 255)        # bleu « stylo » du t-shirt de référence
BLUE_LIGHT = (110, 175, 245, 255)


def put(d, y, text, f, fill, stroke=0):
    """Dessine centré avec le haut visuel du texte à y ; renvoie le bas visuel."""
    bb = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    w = bb[2] - bb[0]
    d.text(((W - w) / 2 - bb[0], y - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=fill)
    return y + (bb[3] - bb[1])


def cauchemar_ref(petit: str, gros: str, ink, accent, combo="R4"):
    """Mise en page du t-shirt de référence : petite ligne manuscrite / GROS MOT bleu / ... / petite ligne / CHUTE."""
    big, small = (FONTS_R[k] for k in COMBOS[combo])
    im = Image.new("RGBA", (W, 7000), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    gros_lines = gros.split("|")
    fb = min((sized(d, t, big, W - 300, 1100) for t in ["CAUCHEMAR", *gros_lines]), key=lambda x: x.size)
    stroke = max(2, int(fb.size * 0.018))          # un poil plus gras, comme l'original
    fs = small(int(fb.size * 0.60))
    gap = int(fb.size * 0.20)
    y = 100
    y = put(d, y, "j'ai fait un", fs, ink) + gap
    y = put(d, y, "CAUCHEMAR", fb, accent, stroke) + int(gap * 0.8)
    y = put(d, y, "...", small(int(fb.size * 0.62)), ink, max(1, int(fb.size * 0.008))) + int(gap * 0.8)
    y = put(d, y, petit, fs, ink) + gap
    for t in gros_lines:
        y = put(d, y, t, fb, accent, stroke) + int(gap * 0.6)
    return im.crop(im.getbbox())


SERIE_R = [
    ("cauchemar-tonton", "j'étais d'accord avec", "TONTON"),
    ("cauchemar-patron", "mon patron", "AVAIT|RAISON"),
    ("cauchemar-isf", "je payais", "L'ISF"),
    ("cauchemar-centre", "j'étais d'extrême", "CENTRE"),
    ("cauchemar-tofu", "je mangeais", "DU TOFU"),
    ("cauchemar-merite", "je méritais", "MON|SALAIRE"),
]


def compare_ref():
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (4800, 1350 * 2), "#F4F1EA")
    for i, c in enumerate(COMBOS):
        sheet.paste(mockup(cauchemar_ref("mon patron", "AVAIT|RAISON", (17, 24, 39, 255), BLUE, c), "#FFFFFF"), (i * 1200, 0))
        sheet.paste(mockup(cauchemar_ref("j'étais d'extrême", "CENTRE", (255, 253, 247, 255), BLUE_LIGHT, c), "#1A1A1F"),
                    (i * 1200, 1350))
    sheet.resize((2400, 1350)).save(OUT / "_comparaison_ref.jpg", quality=90)


def build_ref(combo="R4"):
    (OUT / "designs").mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1200 * 6, 1350 * 2), "#F4F1EA")
    for i, (name, petit, gros) in enumerate(SERIE_R):
        clair = cauchemar_ref(petit, gros, (17, 24, 39, 255), BLUE, combo)
        fonce = cauchemar_ref(petit, gros, (255, 253, 247, 255), BLUE_LIGHT, combo)
        clair.save(OUT / "designs" / f"{name}_tshirt-clair.png")
        fonce.save(OUT / "designs" / f"{name}_tshirt-fonce.png")
        sheet.paste(mockup(clair, "#FFFFFF"), (i * 1200, 0))
        sheet.paste(mockup(fonce, "#1A1A1F"), (i * 1200, 1350))
    sheet.resize((3600, 1350)).save(OUT / "_planche.jpg", quality=88)


# --- Style « S » : linéale arrondie très grasse, mise en page maison (pas une copie de la référence) ---
# Pourquoi : formes rondes = perçues amicales/ludiques -> le message provocant reste « drôle » (violation bénigne) ;
# graisse forte + grand œil (x-height) = lecture en un coup d'œil dans la rue (fluidité de traitement) ;
# rouge vif sur la chute = attire le regard en premier.
FONTS_S = {
    "nunito": lambda s, w=900: font(str(config.FONTS / "Nunito-Variable.ttf"), s, w),
    "fredoka": lambda s, w=700: font(str(config.FONTS / "Fredoka-Variable.ttf"), s, min(w, 700), 100),
    "baloo": lambda s, w=800: font(str(config.FONTS / "Baloo2-Variable.ttf"), s, min(w, 800)),
    "mplus": lambda s, w=800: ImageFont.truetype(str(config.FONTS / "MPLUSRounded1c-ExtraBold.ttf"), s),
}
RED_DARK_TEE = (255, 76, 92, 255)

SERIE_S_SOFT = [
    ("cauchemar-tonton", "j'étais d'accord|avec tonton.", "au dessert, en plus."),
    ("cauchemar-patron", "mon patron|avait raison.", "je me suis réveillé en sueur."),
    ("cauchemar-isf", "je payais|l'ISF.", "et j'étais content."),
    ("cauchemar-centre", "j'étais d'extrême|centre.", "en même temps."),
    ("cauchemar-tofu", "je mangeais|du tofu.", "en trottinette électrique."),
    ("cauchemar-merite", "je méritais|mon salaire.", "personne ne m'a cru."),
]


# Version « provoc » : une cible par camp -> chaque camp achète le t-shirt qui pique l'autre.
# Règles : personnalités publiques et positions publiques uniquement, pas d'insulte, pas d'accusation inventée.
SERIE_S_V1 = [
    ("cauchemar-glucksmann", "je votais|Glucksmann.", "il faut un cap clair, qu'il disait."),
    ("cauchemar-melenchon", "Mélenchon|était président.", "plus de patron. plus de salaire non plus."),
    ("cauchemar-bardella", "je votais|Bardella.", "et il a répondu à une question."),
    ("cauchemar-macron", "j'étais d'accord|avec Macron.", "en même temps."),
    ("cauchemar-rousseau", "Sandrine Rousseau|m'invitait|au barbecue.", "sans viande. sans barbecue."),
    ("cauchemar-zemmour", "Zemmour|était mon prof|d'histoire.", "on a beaucoup révisé."),
]


def cauchemar_s(chute: str, petit: str, ink, accent, fam="nunito"):
    F = FONTS_S[fam]
    im = Image.new("RGBA", (W, 7000), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = chute.split("|")
    head = "j'ai fait un cauchemar :"
    fh = sized(d, head, lambda z: F(z, 600), int(W * 0.62), 700)        # même taille d'accroche partout
    cap = int(fh.size * 2.5)                                             # chute plafonnée : série homogène
    fb = min((sized(d, t, lambda z: F(z, 900), W - 200, cap) for t in lines), key=lambda x: x.size)
    fp = F(int(fh.size * 0.78), 500)
    y = 100
    y = put(d, y, head, fh, ink) + int(fh.size * 0.55)
    for t in lines:
        y = put(d, y, t, fb, accent) + int(fb.size * 0.14)
    if petit:
        y = put(d, y + int(fh.size * 0.35), petit, fp, ink)
    return im.crop(im.getbbox())


def compare_s():
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1200 * len(FONTS_S), 1350 * 2), "#F4F1EA")
    for i, fam in enumerate(FONTS_S):
        sheet.paste(mockup(cauchemar_s("mon patron|avait raison.", "je me suis réveillé en sueur.",
                                       (17, 24, 39, 255), RED, fam), "#FFFFFF"), (i * 1200, 0))
        sheet.paste(mockup(cauchemar_s("j'étais d'extrême|centre.", "en même temps.",
                                       (255, 253, 247, 255), RED_DARK_TEE, fam), "#1A1A1F"), (i * 1200, 1350))
    sheet.save(OUT / "_comparaison_S.jpg", quality=88)
    big = Image.new("RGB", (1500 * len(FONTS_S), 1100), "#FFFFFF")
    for i, fam in enumerate(FONTS_S):
        dz = cauchemar_s("mon patron|avait raison.", "je me suis réveillé en sueur.", (17, 24, 39, 255), RED, fam)
        dz.thumbnail((1350, 950))
        big.paste(dz, (i * 1500 + (1500 - dz.width) // 2, 80), dz)
    big.save(OUT / "_comparaison_S_zoom.jpg", quality=88)


def build_s(fam="fredoka", serie=None):
    serie = serie or SERIE_S()
    (OUT / "designs").mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1200 * 6, 1350 * 2), "#F4F1EA")
    for i, (name, chute, petit) in enumerate(serie):
        clair = cauchemar_s(chute, petit, (17, 24, 39, 255), RED, fam)
        fonce = cauchemar_s(chute, petit, (255, 253, 247, 255), RED_DARK_TEE, fam)
        clair.save(OUT / "designs" / f"{name}_tshirt-clair.png")
        fonce.save(OUT / "designs" / f"{name}_tshirt-fonce.png")
        sheet.paste(mockup(clair, "#FFFFFF"), (i * 1200, 0))
        sheet.paste(mockup(fonce, "#1A1A1F"), (i * 1200, 1350))
    sheet.resize((3600, 1350)).save(OUT / "_planche.jpg", quality=88)


# Propositions de chutes (ancrées sur les mèmes sourcés dans content/veille/memes_*.json) : 3 par cible.
CHOIX_S = {
    "glucksmann": [("je votais|Glucksmann.", "il faut un cap clair, qu'il disait."),
                   ("Glucksmann|avait un cap clair.", "puis je me suis réveillé."),
                   ("notre gauche,|notre gauche,|notre gauche.", "il l'a dit 7 fois. j'ai compté.")],
    "melenchon": [("Mélenchon|était président.", "plus de patron. plus de salaire non plus."),
                  ("Mélenchon|était calme.", "c'est là que j'ai su que je rêvais."),
                  ("Mélenchon|se présentait|une 5e fois.", "en hologramme, cette fois.")],
    "bardella": [("je votais|Bardella.", "et il a répondu à une question."),
                 ("Bardella|était au Parlement.", "personne ne l'a reconnu."),
                 ("Bardella|acceptait|un débat.", "sans fiches. sans TikTok.")],
    "macron": [("j'étais d'accord|avec Macron.", "en même temps."),
               ("le ruissellement|est arrivé|jusqu'à moi.", "3 centimes. for sure."),
               ("j'ai traversé|la rue.", "toujours pas de boulot.")],
    "rousseau": [("Sandrine Rousseau|m'invitait|au barbecue.", "sans viande. sans barbecue."),
                 ("Sandrine Rousseau|a vu|mon barbecue.", "j'ai été déconstruit."),
                 ("je mangeais|une entrecôte.", "Sandrine Rousseau m'a vu.")],
    "zemmour": [("Zemmour|était mon prof|d'histoire.", "on a beaucoup révisé."),
                ("Zemmour|était optimiste.", "ben voyons."),
                ("Zemmour|m'a lu|500 pages.", "le déclin a duré toute la nuit.")],
}


def planche_choix():
    cell_w, cell_h = 640, 560
    cibles = list(CHOIX_S)
    sheet = Image.new("RGB", (cell_w * len(cibles), cell_h * 3), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    lab = FONTS_S["fredoka"](34, 700)
    for c, cible in enumerate(cibles):
        for r, (chute, petit) in enumerate(CHOIX_S[cible]):
            x0, y0 = c * cell_w, r * cell_h
            if (c + r) % 2:
                d.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill="#F6F4EF")
            dz = cauchemar_s(chute, petit, (17, 24, 39, 255), RED, "fredoka")
            k = 560 / W
            dz = dz.resize((int(dz.width * k), int(dz.height * k)), Image.LANCZOS)
            sheet.paste(dz, (x0 + (cell_w - dz.width) // 2, y0 + 70), dz)
            d.text((x0 + 18, y0 + 14), str(c * 3 + r + 1), font=lab, fill=(29, 78, 216))
    sheet.save(OUT / "_choix_chutes.jpg", quality=90)


def SERIE_S():
    """Série retenue le 22/11 par le propriétaire : choix n° 2, 5, 8, 11, 14, 17 de la planche (2e chute de chaque cible)."""
    return [(f"cauchemar-{cible}", *CHOIX_S[cible][1]) for cible in CHOIX_S]


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "ref":
        compare_ref()
    elif arg == "S":
        compare_s()
    elif arg.startswith("S:"):
        build_s(arg[2:])
    elif arg.startswith("R"):
        build_ref(arg)
    elif arg:
        build(arg)
    else:
        compare()
