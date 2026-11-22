"""Pack de marque : avatar (clair/sombre/32 px), designs t-shirts prêts à imprimer, maquettes honnêtes,
visuels de stories à la une, page de liens mobile. Sources éditables = ce script + fontes OFL."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

OUT = config.ROOT / "brand"
BLUE, WHITE, RED, INK, ECRU = "#1649FF", "#FFFDF7", "#EF233C", "#111827", "#F3EBDD"
ANTON = config.FONTS / "Anton-Regular.ttf"
ARCHIVO = config.FONTS / "ArchivoBlack-Regular.ttf"


def font(p, size):
    return ImageFont.truetype(str(p), size)


def avatar(src: Path) -> None:
    d = OUT / "avatar"
    d.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
    im.resize((1080, 1080), Image.LANCZOS).save(d / "avatar_1080.png")
    im.resize((320, 320), Image.LANCZOS).save(d / "avatar_320.png")
    im.resize((32, 32), Image.LANCZOS).resize((256, 256), Image.NEAREST).save(d / "test_lisibilite_32px.png")
    # version claire : fond blanc cassé, coq bleu (inversion des aplats bleu/blanc)
    px = im.resize((1080, 1080), Image.LANCZOS).convert("RGB")
    light = Image.new("RGB", px.size)
    src_px, dst = px.load(), light.load()
    for y in range(px.height):
        for x in range(px.width):
            r, g, b = src_px[x, y]
            if b > 180 and r < 90:          # bleu → blanc cassé
                dst[x, y] = (255, 253, 247)
            elif r > 200 and g > 200 and b > 200:   # blanc → bleu
                dst[x, y] = (22, 73, 255)
            else:
                dst[x, y] = (r, g, b)
    light.save(d / "avatar_clair_1080.png")
    # aperçu du recadrage rond d'Instagram
    mask = Image.new("L", (1080, 1080), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 1079, 1079], fill=255)
    rond = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    rond.paste(im.resize((1080, 1080)), (0, 0), mask)
    rond.save(d / "apercu_recadrage_rond.png")


def tee_design(pid: str, lines: list[str], ink: str, accent: str, out: Path) -> None:
    """Fichier d'impression 4500×5400 px, fond transparent ; dernière ligne en accent rouge."""
    W, H = 4500, 5400
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sizes = []
    for ln in lines:
        s = 1400
        while d.textlength(ln, font=font(ANTON, s)) > W * 0.9:
            s -= 20
        sizes.append(s)
    size = min(sizes)
    f = font(ANTON, size)
    lh = int(size * 1.08)
    y = int(H * 0.06)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill=accent if i == len(lines) - 1 else ink)
        y += lh
    sig = "LE BORDEL FRANÇAIS"
    fs = font(ARCHIVO, 150)
    w = d.textlength(sig, font=fs)
    d.rectangle([(W - w) / 2 - 40, y + 260, (W + w) / 2 + 40, y + 480], fill=BLUE)
    d.text(((W - w) / 2, y + 285), sig, font=fs, fill=WHITE)
    im = im.crop(im.getbbox())
    im.save(out)


def mockup(design: Path, tee_color: str, out: Path) -> None:
    """Maquette plate et honnête (silhouette dessinée, pas une photo de produit réel)."""
    W, H = 1600, 1800
    im = Image.new("RGB", (W, H), "#E9E6DF")
    d = ImageDraw.Draw(im)
    body = [(430, 300), (620, 230), (700, 290), (900, 290), (980, 230), (1170, 300), (1420, 560), (1260, 700),
            (1170, 620), (1170, 1650), (430, 1650), (430, 620), (340, 700), (180, 560)]
    d.polygon(body, fill=tee_color, outline="#00000022")
    d.arc([700, 200, 900, 360], 0, 180, fill="#00000033", width=10)
    dz = Image.open(design)
    dz.thumbnail((560, 760))
    im.paste(dz, ((W - dz.width) // 2, 470), dz)
    f = font(ARCHIVO, 34)
    d.text((40, H - 70), "Maquette — rendu indicatif, textile non testé (aucun échantillon reçu)", font=f, fill="#555")
    im.save(out, quality=90)


def highlights() -> None:
    d = OUT / "stories_a_la_une"
    d.mkdir(parents=True, exist_ok=True)
    for name, label in [("villes", "VILLES"), ("boutique", "BOUTIQUE"), ("coulisses", "COULISSES"), ("contact", "CONTACT")]:
        im = Image.new("RGB", (1080, 1920), BLUE)
        dr = ImageDraw.Draw(im)
        dr.ellipse([240, 660, 840, 1260], fill=WHITE)
        f = font(ANTON, 150)
        w = dr.textlength(label, font=f)
        dr.text(((1080 - w) / 2, 860), label, font=f, fill=BLUE)
        dr.rectangle([440, 1080, 640, 1100], fill=RED)
        im.save(d / f"{name}.png")


def link_page(shop_url: str | None, coulisses_url: str | None, contact: str | None) -> Path:
    """Page de liens mobile (hébergée gratuitement sur GitHub Pages, dans le dépôt de diffusion)."""
    def btn(label, url, sub):
        if url:
            return f'<a class="b" href="{url}">{label}<small>{sub}</small></a>'
        return f'<div class="b off">{label}<small>bientôt</small></div>'
    html = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le Bordel Français</title><meta name="description" content="La France en 3D. Les politiques prennent cher.">
<style>body{{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#1649FF;color:#FFFDF7;display:flex;justify-content:center}}
main{{max-width:460px;width:100%;padding:28px 18px;text-align:center}}img{{width:112px;height:112px;border-radius:50%;border:4px solid #FFFDF7}}
h1{{font-weight:900;letter-spacing:.5px;margin:12px 0 2px;font-size:26px}}h1 span{{border-bottom:5px solid #EF233C}}p{{margin:4px 0 22px;opacity:.9}}
.b{{display:block;background:#FFFDF7;color:#111827;text-decoration:none;font-weight:800;padding:16px;border-radius:14px;margin:12px 0;font-size:18px}}
.b small{{display:block;font-weight:500;font-size:13px;color:#4b5563;margin-top:3px}}.off{{opacity:.55}}footer{{font-size:12px;opacity:.75;margin-top:26px}}</style></head>
<body><main><img src="avatar_320.png" alt="Coq blasé, logo du compte"><h1>LE BORDEL <span>FRANÇAIS</span></h1>
<p>Liberté. Égalité. N'importe quoi.</p>
{btn("👕 Les t-shirts du compte", shop_url, "Gauche, droite, ou tout le monde prend")}
{btn("🎬 Comment les vidéos sont fabriquées", coulisses_url, "Les coulisses du studio 3D")}
{btn("✉️ Contact & collaborations", f"mailto:{contact}" if contact else None, "Marques, médias, partenariats")}
<footer>Fictions satiriques · villes inventées · @lebordelfrancais</footer></main></body></html>"""
    d = OUT / "page_liens"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html, encoding="utf-8")
    shutil.copy(OUT / "avatar" / "avatar_320.png", d / "avatar_320.png")
    return d / "index.html"


def main(avatar_src: str | None = None) -> None:
    OUT.mkdir(exist_ok=True)
    if avatar_src:
        avatar(Path(avatar_src))
    prods = json.loads((config.CONTENT / "products.json").read_text(encoding="utf-8"))
    dz, mk = OUT / "boutique" / "designs", OUT / "boutique" / "maquettes"
    dz.mkdir(parents=True, exist_ok=True)
    mk.mkdir(parents=True, exist_ok=True)
    for p in prods:
        if p.get("design_generator") == "merch_text":      # série « cauchemar » : python -m lbf.merch_text S:fredoka
            continue
        words = p["slogan"].replace(". ", ".|").split("|")
        lines = [w.strip() for w in words if w.strip()]
        if len(lines) == 1:
            ws = lines[0].split()
            lines = [" ".join(ws[: len(ws) // 2]), " ".join(ws[len(ws) // 2:])]
        for tee, ink in (("ecru", INK), ("noir", WHITE)):
            f = dz / f"{p['id']}_{tee}.png"
            tee_design(p["id"], lines, ink, RED, f)
            mockup(f, ECRU if tee == "ecru" else "#1A1A1F", mk / f"{p['id']}_{tee}.jpg")
    highlights()
    link_page(None, None, None)
    print("pack de marque :", OUT)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
