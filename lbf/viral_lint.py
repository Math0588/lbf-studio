"""Contrôle « viral » automatique d'un script avant fabrication (docs/ALGO_INSTAGRAM.md, docs/STYLE_TACLE.md).

Le producteur cloud refuse un script qui ne passe pas : chaque vidéo publiée suit les mêmes codes, sans relecture
humaine. Bloquant : accroche, partage ciblé, longueur, sources, contrôle éditorial. Le reste = avertissements."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import editorial

SOFT_ENDINGS = re.compile(r"\b(en commentaire|dis-moi|dis en commentaire|tague|commente)\b", re.I)


def check(script: dict) -> dict:
    segs = script.get("narration_segments", [])
    block, warn = [], []
    if not segs:
        return {"ok": False, "blocking": ["aucune narration"], "warnings": []}
    first, last = segs[0]["text"], segs[-1]["text"]
    if not first.lower().startswith("dans cette ville, tout le monde vote"):
        block.append("accroche : la 1re phrase doit être « Dans cette ville, tout le monde vote X. »")
    if not re.match(r"envoie[- ]ça", last, re.I):
        block.append("fin : la dernière phrase doit être un partage ciblé « Envoie ça au pote qui… »")
    if SOFT_ENDINGS.search(last):
        warn.append("fin : appel au commentaire (moins fort que l'envoi en message)")
    n = len(segs)
    if not 5 <= n <= 9:
        block.append(f"rythme : {n} phrases (5 à 9 attendues, une pique par plan)")
    long = [s["id"] for s in segs if len(s["text"].split()) > 16]
    if long:
        warn.append(f"phrases longues (>16 mots) : {long}")
    sourced = [s for s in segs if s.get("claim_type") in ("fait_public", "citation_exacte")]
    if len(sourced) < 2:
        block.append(f"ancrage : {len(sourced)} pique(s) sourcée(s) (mèmes/faits connus), 2 minimum")
    if not script.get("claims") and sourced:
        block.append("sources : claims vides alors que des faits/citations sont utilisés")
    said = " ".join(x["text"] for x in segs) + " " + " ".join(
        sc.get("onscreen_text", "") for sc in script.get("scenes", [])) + " " + script.get("title_cover", "")
    if re.search(r"\bsuicid", said, re.I):
        block.append("mot bridé par Instagram (suicide) dans la narration ou à l'écran")
    title = script.get("title_cover", "")
    if not title or len(title.split()) > 5:
        warn.append("titre de couverture : 1 à 5 mots")
    ed = editorial.check({**script, "city_id": script.get("city")})
    if ed["decision"] != "pass":
        block.append(f"éditorial : {ed['decision']} {ed['blocking'] + ed['review']}")
    if ed["notes"]:
        block.append(f"éditorial : {ed['notes']}")
    return {"ok": not block, "blocking": block, "warnings": warn}


if __name__ == "__main__":
    paths = [Path(a) for a in sys.argv[1:]] or sorted(Path("content/scripts").rglob("*.json"))
    bad = 0
    for p in paths:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "narration_segments" not in s:
            continue
        r = check(s)
        if not r["ok"]:
            bad += 1
            print(f"✗ {p} : {r['blocking']}")
    print(f"{len(paths)} fichiers, {bad} refusés")
