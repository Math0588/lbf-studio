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


STRICT = False
HISTOIRE = False  # format « histoire absurde » : 1 point de départ sourcé suffit, gags de situation autorisés   # mode « moquerie de la personne » (activé quand la banque est réécrite)
SITUATION = re.compile(r"^(ici|à la mairie|la mairie|dans la ville|la ville|au conseil municipal)\b", re.I)


def check(script: dict, strict: bool | None = None) -> dict:
    strict = STRICT if strict is None else strict
    histoire = HISTOIRE or any(sc.get("gags") or sc.get("actions") for sc in script.get("scenes", []))
    if histoire:
        strict = False   # format « histoire absurde » : 1 point de départ sourcé, gags de situation voulus
    segs = script.get("narration_segments", [])
    block, warn = [], []
    if not segs:
        return {"ok": False, "blocking": ["aucune narration"], "warnings": []}
    first, last = segs[0]["text"], segs[-1]["text"]
    if script.get("format_v5"):
        return _check_v5(script, segs, block, warn)
    if script.get("format_v4"):
        return _check_v4(script, segs, block, warn)
    # accroche v3 : une phrase « teaser » (≤ 10 mots, l'image la plus absurde de l'histoire, sans l'expliquer)
    # peut précéder « Dans cette ville… » : la promesse tombe dans la 1re seconde (fossé de curiosité)
    teaser = segs[0].get("role") == "teaser"
    if teaser:
        if len(first.split()) > 10:
            block.append("accroche : le teaser doit faire 10 mots maximum")
        first = segs[1]["text"] if len(segs) > 1 else ""
    if not first.lower().startswith("dans cette ville, tout le monde vote"):
        block.append("accroche : la 1re phrase (après le teaser éventuel) doit être « Dans cette ville, tout le monde vote X. »")
    if not re.match(r"envoie[- ]ça", last, re.I):
        block.append("fin : la dernière phrase doit être un partage ciblé « Envoie ça au pote qui… »")
    if SOFT_ENDINGS.search(last):
        warn.append("fin : appel au commentaire (moins fort que l'envoi en message)")
    n = len(segs) - (1 if teaser else 0)
    if not 5 <= n <= 9:
        block.append(f"rythme : {n} phrases (5 à 9 attendues, une pique par plan)")
    long = [s["id"] for s in segs if len(s["text"].split()) > 16]
    if long:
        warn.append(f"phrases longues (>16 mots) : {long}")
    sourced = [s for s in segs if s.get("claim_type") in ("fait_public", "citation_exacte")]
    if len(sourced) < (1 if histoire else 2):
        block.append(f"ancrage : {len(sourced)} pique(s) sourcée(s) (mèmes/faits connus), {1 if histoire else 2} minimum")
    if strict:
        # chaque pique vise le politicien lui-même, sur un truc connu ; peu de gags de situation à décoder
        if len(sourced) < 3:
            block.append(f"personne : {len(sourced)} pique(s) sur des faits/mèmes connus, 3 minimum")
        situ = [x["id"] for x in segs[1:-1] if SITUATION.match(x["text"].strip())]
        if len(situ) > 1:
            block.append(f"personne : trop de gags de situation ({situ}), 1 maximum")
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
    args = [a for a in sys.argv[1:] if a not in ("--strict", "--histoire")]
    if "--strict" in sys.argv:
        STRICT = True
    if "--histoire" in sys.argv:
        HISTOIRE = True
        args = [a for a in args if a != "--histoire"]
    paths = [Path(a) for a in args] or sorted(Path("content/scripts").rglob("*.json"))
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


LIENS = {"mais", "donc", "car", "alors"}


def _check_v4(script: dict, segs: list, block: list, warn: list) -> dict:
    """Format v4 (25/11) : UNE situation précise, accroche qui plonge dedans, chaque réplique découle de la
    précédente (« mais » / « donc », règle des scénaristes de South Park), aucun élément gratuit, jamais la
    formule « Dans cette ville »."""
    first, last = segs[0]["text"], segs[-1]["text"]
    if len((script.get("situation") or "").split()) < 8:
        block.append("situation : décrire la situation précise (lieu, moment, enjeu) dans « situation »")
    if segs[0].get("role") != "accroche" or len(first.split()) > 12:
        block.append("accroche : 1re réplique « accroche » de 12 mots maximum, au cœur de la situation")
    if any(s["text"].lower().startswith("dans cette ville") for s in segs):
        block.append("accroche : formule « Dans cette ville… » interdite en v4 (générique, répétée)")
    sans_lien = [s["id"] for s in segs[1:-1] if s.get("lien") not in LIENS]
    if sans_lien:
        block.append(f"enchaînement : répliques sans lien « mais / donc / car » avec la précédente : {sans_lien}")
    if not re.match(r"envoie[- ]ça", last, re.I):
        block.append("fin : la dernière phrase doit être un partage ciblé « Envoie ça au pote qui… »")
    if not 5 <= len(segs) - 1 <= 9:
        block.append(f"rythme : {len(segs) - 1} répliques après l'accroche (5 à 9)")
    long = [s["id"] for s in segs if len(s["text"].split()) > 16]
    if long:
        warn.append(f"phrases longues (>16 mots) : {long}")
    if not [s for s in segs if s.get("claim_type") in ("fait_public", "citation_exacte")]:
        block.append("ancrage : au moins un fait ou une citation réels et sourcés")
    if not script.get("claims"):
        block.append("sources : claims vides")
    said = " ".join(x["text"] for x in segs) + " " + script.get("title_cover", "")
    if re.search(r"\bsuicid", said, re.I):
        block.append("mot bridé par Instagram (suicide)")
    return {"ok": not block, "blocking": block, "warnings": warn}


def _check_v5(script: dict, segs: list, block: list, warn: list) -> dict:
    """Format v5 « histoire de ville » (modèle validé par le propriétaire, 26/11) : la ville a le caractère du
    politicien (tirée de son vrai tic ou mème), une mini-quête, une chute qui relie tout (rappel), voix posée,
    45-60 s, et un « Partie 2 » à la fin pour faire revenir."""
    if len((script.get("situation") or "").split()) < 8:
        block.append("situation : décrire le caractère de la ville et la mini-quête dans « situation »")
    if not 9 <= len(segs) <= 15:
        block.append(f"rythme : {len(segs)} répliques (9 à 15 pour 45-60 s)")
    if not segs[-1]["text"].lower().startswith("partie 2"):
        block.append("fin : la dernière réplique annonce la suite (« Partie 2 : … »)")
    long = [s["id"] for s in segs if len(s["text"].split()) > 18]
    if long:
        warn.append(f"phrases longues (>18 mots) : {long}")
    if not [s for s in segs if s.get("claim_type") in ("fait_public", "citation_exacte")] or not script.get("claims"):
        block.append("ancrage : au moins un fait ou une citation réels et sourcés")
    said = " ".join(s["text"] for s in segs) + " " + script.get("title_cover", "")
    if re.search(r"\bsuicid", said, re.I):
        block.append("mot bridé par Instagram (suicide)")
    return {"ok": not block, "blocking": block, "warnings": warn}
