"""Photos réelles des politiciens, sous licence libre uniquement (Wikimedia Commons : CC BY, CC BY-SA, CC0,
domaine public), avec auteur et licence pour les crédits. Rangées dans assets/photos/<ville>/ (+ photos.json).

Usage : python -m lbf.photos <ville> [<ville> …]   (dans GitHub Actions : Wikimedia n'est pas joignable partout)
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

from . import config

NAMES = {"glucksmannville": "Raphaël Glucksmann", "macronville": "Emmanuel Macron",
         "melenchonville": "Jean-Luc Mélenchon", "bardellaville": "Jordan Bardella", "marineville": "Marine Le Pen",
         "zemmourville": "Éric Zemmour", "rinerville": "Teddy Riner", "durifville": "Sylvain Durif"}
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "lbf-studio/1.0 (satire video tool; github.com/Math0588/lbf-studio)"}
DIR = config.ASSETS / "photos"


def _licence_ok(lic: str) -> bool:
    l = lic.lower()
    if any(x in l for x in ("nc", "nd", "fair use", "non-free")):
        return False
    return any(x in l for x in ("cc by", "cc-by", "cc0", "public domain", "domaine public", "pd-", "attribution"))


def _clean(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "").strip()[:120]


def fetch(city: str, n: int = 12) -> list[dict]:
    name = NAMES[city]
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f'"{name}"',
              "gsrnamespace": "6", "gsrlimit": "50", "prop": "imageinfo",
              "iiprop": "url|extmetadata|size|mime", "iiurlwidth": "1080"}
    data = json.loads(urllib.request.urlopen(urllib.request.Request(
        API + "?" + urllib.parse.urlencode(params), headers=UA), timeout=60).read())
    cands = []
    for p in data.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        title = p.get("title", "")
        if ii.get("mime") not in ("image/jpeg", "image/png") or not _licence_ok(lic):
            continue
        if ii.get("width", 0) < 700 or ii.get("height", 0) < 700:
            continue
        if re.search(r"signature|logo|carte|map|affiche|poster|tract|graph", title, re.I):
            continue
        last = name.split()[-1].lower()
        if last not in title.lower().replace("é", "e").replace("ë", "e") and last not in title.lower():
            continue                     # le nom doit être dans le titre (pas une photo de groupe où il passe)
        portrait = ii["height"] >= ii["width"] * 0.8
        cands.append((0 if portrait else 1, -ii["width"], {
            "title": title, "url": ii.get("thumburl") or ii["url"], "page": ii.get("descriptionurl", ""),
            "author": _clean(meta.get("Artist", {}).get("value", "")) or "auteur inconnu", "license": lic}))
    cands.sort(key=lambda c: (c[0], c[1]))
    out_dir = DIR / city
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = []
    for _, _, c in cands[:n]:
        f = out_dir / f"{len(kept):02d}.jpg"
        try:
            f.write_bytes(urllib.request.urlopen(urllib.request.Request(c["url"], headers=UA), timeout=60).read())
        except Exception:
            continue
        c["file"] = f.name
        kept.append(c)
        time.sleep(1)
    (out_dir / "photos.json").write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[photos] {city} : {len(kept)} photo(s) libre(s)", flush=True)
    return kept


def credits(city: str) -> str:
    f = DIR / city / "photos.json"
    if not f.exists():
        return ""
    ps = json.loads(f.read_text(encoding="utf-8"))
    return "Photos : " + " ; ".join(f"{p['author']} ({p['license']}, Wikimedia Commons)" for p in ps[:6])


if __name__ == "__main__":
    for c in sys.argv[1:]:
        fetch(c)
