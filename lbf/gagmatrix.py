"""Usine à gags : des centaines de scénarios différents par politicien, chacun ancré sur un mème RÉEL et
reconnaissable (vérifié, sourcé), croisé avec une situation du quotidien et un ressort comique.

    mème réel (ce que tout le monde a vu passer)  ×  situation (métro, boulangerie, salle de sport…)
                                                   ×  ressort (escalade, littéralisation, boucle…)

Règles : le mème est nommé dès la 1re phrase (compréhension immédiate) ; jamais deux fois la même combinaison ;
un même mème au plus une fois par semaine et par ville ; les mèmes récents passent en premier ; un mème sans
source vérifiée n'est jamais utilisé. Les nouveaux mèmes de la veille quotidienne s'ajoutent automatiquement."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
import re
from pathlib import Path

from . import config

USED = config.DATA / "gag_matrix_used.json"

SITUATIONS = [
    ("la boulangerie", ["counter", "char"]), ("le métro", ["bus", "crowd"]), ("le bus", ["bus", "char"]),
    ("la mairie", ["tribune", "crowd"]), ("la cantine", ["table", "crowd"]), ("l'école", ["screen", "crowd"]),
    ("la salle de sport", ["char", "screen"]), ("le supermarché", ["counter", "char"]),
    ("le restaurant", ["table", "char"]), ("le stade", ["crowd", "screen"]), ("le parc", ["bench", "tree"]),
    ("le rond-point", ["roundabout", "car"]), ("le permis de conduire", ["car", "gps"]),
    ("l'entretien d'embauche", ["table", "char"]), ("la réunion de copro", ["table", "crowd"]),
    ("la collecte des déchets", ["bin", "char"]), ("les travaux", ["banner", "sign"]),
    ("la panne de courant", ["lamp", "crowd"]), ("la fête municipale", ["arch", "crowd"]),
    ("le marché", ["counter", "crowd"]), ("la livraison", ["car", "char"]), ("le tourisme", ["bus", "screen"]),
    ("les vacances", ["car", "gps"]), ("la visite de la ville voisine", ["gps", "car"]),
    ("le Wi-Fi", ["router_lectern", "screen"]), ("la file d'attente", ["crowd", "sign"]),
    ("le distributeur de billets", ["screen", "char"]), ("la pharmacie", ["counter", "char"]),
    ("le conseil de quartier", ["tribune", "crowd"]), ("l'université", ["screen", "crowd"]),
]
RESSORTS = [
    "escalade : chaque étape est pire et plus absurde que la précédente",
    "littéralisation : la formule du mème est prise au pied de la lettre et devient un objet",
    "boucle : on revient exactement au point de départ, en pire",
    "décalage d'échelle : un détail minuscule devient un projet national, ou l'inverse",
    "promesse contre réalité : l'annonce géante, puis ce qui se passe vraiment",
    "comptage absurde : un chiffre délirant affiché en grand (étiquette rouge)",
    "contamination : toute la ville se met à parler ou à agir comme le mème",
    "électorat cliché : les habitants types de la ville, détaillés et chiffrés (prix, objets, habitudes)",
    "inversion : le service fait exactement le contraire de son rôle, avec fierté",
    "bureaucratie récursive : pour régler le problème, il faut d'abord un formulaire pour le formulaire",
    "épisode raté : le maire tente de corriger le mème et l'aggrave",
    "comparaison : la même situation dans la ville voisine, en une phrase",
]
NAMES = {"bardellaville": "Bardella", "melenchonville": "Mélenchon", "macronville": "Macron",
         "zemmourville": "Zemmour", "marineville": "Marine", "glucksmannville": "Glucksmann"}


BANNED = ("écart", "ecart", "non sourc", "exclu", "à exclure", "a exclure", "non utilis", "ne pas utiliser",
          "vie privée", "vie privee", "judiciaire", "plainte", "procès", "condamn", "affaire", "agression",
          "immigr", "religion", "origine", "couple", "santé")


def _ok(*texts: str) -> bool:
    """Refuse toute entrée marquée écartée/exclue ou qui touche une ligne rouge, quel que soit le champ."""
    s = " ".join(t or "" for t in texts).lower()
    return not any(x in s for x in BANNED)


def memes(city: str) -> list[dict]:
    """Mèmes vérifiés : catalogues de veille + sources vérifiées des scripts (jamais d'élément écarté)."""
    out = []
    for p in (config.CONTENT / "veille" / f"memes_{city}.json", config.CONTENT / "veille" / f"{city}.json"):
        if p.exists():
            for m in json.loads(p.read_text(encoding="utf-8")):
                st = m.get("statut") or m.get("status") or m.get("type") or ""
                res = m.get("resume") or m.get("original_angle") or m.get("subject") or ""
                if m.get("url") and res and _ok(st, res, m.get("type", ""), m.get("reutilisable", "")):
                    out.append({"url": m["url"], "date": str(m.get("date") or m.get("published") or ""),
                                "type": m.get("type") or st,
                                "resume": m.get("resume") or m.get("subject") or m.get("original_angle")})
    scripts = list((config.CONTENT / "scripts" / "bank" / city).glob("*.json")) + \
        list((config.CONTENT / "scripts").glob(f"{city}_pilot_*.json"))
    for f in scripts:
        for s in json.loads(f.read_text(encoding="utf-8")).get("sources") or []:
            if not isinstance(s, dict) or not s.get("url"):
                continue
            st = s.get("statut") or s.get("status") or ""
            note = s.get("used_for") or s.get("usage") or s.get("note") or s.get("titre") or st
            if _ok(st, note) and note and len(note) > 15:
                out.append({"url": s["url"], "date": str(s.get("date") or s.get("published") or ""),
                            "type": st[:60], "resume": note[:300]})
    seen, uniq = set(), []
    for m in out:
        if m["url"] + m["resume"][:40] not in seen:
            seen.add(m["url"] + m["resume"][:40])
            uniq.append(m)
    return uniq


def _used() -> dict:
    return json.loads(USED.read_text(encoding="utf-8")) if USED.exists() else {}


def count(city: str) -> int:
    return len(memes(city)) * len(SITUATIONS) * len(RESSORTS)


def next_candidate(city: str, seed: int | None = None) -> dict | None:
    ms = memes(city)
    if not ms:
        return None
    used = _used()
    city_used = used.get(city, [])
    week_ago = (dt.datetime.now() - dt.timedelta(days=7)).isoformat()
    recent_memes = {u["meme"] for u in city_used if u["at"] > week_ago}
    recent_sits = [u["situation"] for u in city_used[-8:]]
    done = {u["key"] for u in city_used}
    rnd = random.Random(seed if seed is not None else len(city_used))
    from .writer import key_phrase
    # ordre : mèmes à formule reconnaissable, puis les autres ; les plus récents d'abord dans chaque groupe
    ms = sorted(ms, key=lambda m: (key_phrase(m["resume"]) is None, m["date"] and -int(re.sub(r"\D", "", m["date"])[:8] or 0)))
    last_use = {}
    for u in city_used:
        last_use[u["meme"]] = u["at"]
    # 1er passage : mèmes non utilisés depuis 7 jours ; 2e passage : le moins récemment utilisé
    order = [m for m in ms if hashlib.sha1(m["resume"].encode()).hexdigest()[:10] not in recent_memes]
    order += sorted([m for m in ms if m not in order],
                    key=lambda m: last_use.get(hashlib.sha1(m["resume"].encode()).hexdigest()[:10], ""))
    for m in order:
        mk = hashlib.sha1(m["resume"].encode()).hexdigest()[:10]
        sits = [s for s in SITUATIONS if s[0] not in recent_sits]
        rnd.shuffle(sits)
        res = RESSORTS[:]
        rnd.shuffle(res)
        for sit, props in sits:
            for r in res:
                key = hashlib.sha1(f"{mk}|{sit}|{r}".encode()).hexdigest()[:12]
                if key in done:
                    continue
                return {"key": key, "meme_key": mk, "meme": m, "situation": sit, "props": props, "ressort": r}
    return None


def to_synopsis(city: str, c: dict) -> dict:
    name = NAMES.get(city, city)
    return {
        "id": f"gm-{c['key']}", "city": city, "format": "A", "title": c["situation"].capitalize(),
        "anchor": c["meme"]["resume"], "anchor_url": c["meme"]["url"],
        "daily_problem": f"{c['situation'].capitalize()} à {city.capitalize()}.",
        "hook": f"Dans cette ville, tout le monde vote {name}… (le mème réel doit être reconnaissable dès cette phrase)",
        "development_1": f"Ressort imposé : {c['ressort']}.",
        "development_2": "Escalade visuelle avec un détail chiffré en étiquette rouge.",
        "visual_punchline": "Chute visuelle qui retourne le mème contre la situation.",
        "set_needed": c["props"], "cta_idea": "Question précise à commenter ou « Abonne-toi : la suite… ».",
        "comic_mechanism": c["ressort"].split(" :")[0], "sources": [{"url": c["meme"]["url"], "statut": c["meme"]["type"],
                                                                     "usage": "mème réel, idée seulement"}],
    }


def mark_used(city: str, c: dict) -> None:
    used = _used()
    used.setdefault(city, []).append({"key": c["key"], "meme": c["meme_key"], "situation": c["situation"],
                                      "at": dt.datetime.now().isoformat(timespec="seconds")})
    USED.parent.mkdir(exist_ok=True)
    USED.write_text(json.dumps(used, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    for city in NAMES:
        c = next_candidate(city)
        print(f"{city:16} {len(memes(city)):3} mèmes vérifiés → {count(city):5} combinaisons possibles",
              f"| prochain : {c['situation']} × {c['ressort'][:30]} × « {c['meme']['resume'][:50]} »" if c else "")
