"""Légendes, hashtags et métadonnées YouTube optimisés pour la recherche (Instagram + YouTube Shorts).

Ce que la recherche Instagram lit : la légende (surtout le début), le texte à l'écran, l'audio transcrit, les
hashtags, le nom et la bio du compte. Les mots-clés en clair comptent plus que les hashtags, et Instagram limite à
5 hashtags par publication. Donc :
- 1re ligne (≤ 125 caractères, visible avant « plus ») : accroche + mot-clé principal (nom complet du politicien) ;
- une phrase descriptive avec les requêtes réelles : nom complet, parti, « humour politique », « politique
  française », « présidentielle 2027 » (et le sujet d'actualité pour un épisode réactif) ;
- une question de débat (pas d'« écris OUI si… », rétrogradé), un appel à l'envoi ;
- 5 hashtags : politicien, parti, #humourpolitique, #politiquefrancaise, + 1 tournant (actualité / 2027 / parodie).
YouTube : titre ≤ 100 caractères avec mot-clé en tête et #Shorts, description riche en mots-clés, tags.
Pas de « fiction satirique » ni de mention d'IA (décision du propriétaire)."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from . import config

PEOPLE = {
    "bardellaville": {"nom": "Bardella", "full": "Jordan Bardella", "parti": "RN", "parti_long": "Rassemblement national",
                      "avec": "le RN", "tags": ["bardella", "rn"]},
    "marineville": {"nom": "Marine", "full": "Marine Le Pen", "parti": "RN", "parti_long": "Rassemblement national",
                    "avec": "le RN", "tags": ["marinelepen", "rn"]},
    "macronville": {"nom": "Macron", "full": "Emmanuel Macron", "parti": "Renaissance", "parti_long": "Renaissance",
                    "avec": "Renaissance", "tags": ["macron", "emmanuelmacron"]},
    "melenchonville": {"nom": "Mélenchon", "full": "Jean-Luc Mélenchon", "parti": "LFI",
                       "parti_long": "La France insoumise", "avec": "LFI", "tags": ["melenchon", "lfi"]},
    "zemmourville": {"nom": "Zemmour", "full": "Éric Zemmour", "parti": "Reconquête", "parti_long": "Reconquête",
                     "avec": "Reconquête", "tags": ["zemmour", "reconquete"]},
    "glucksmannville": {"nom": "Glucksmann", "full": "Raphaël Glucksmann", "parti": "Place publique",
                        "parti_long": "Place publique", "avec": "Place publique", "tags": ["glucksmann", "placepublique"]},
}
CITY = {"bardellaville": "Bardellaville", "marineville": "Marineville", "macronville": "Macronville",
        "melenchonville": "Mélenchonville", "zemmourville": "Zemmourville", "glucksmannville": "Glucksmannville"}
ROTATING = ["presidentielle2027", "humour", "parodie"]

FIRST_LINES = [
    "Si {full} gérait ta ville… 😭",
    "{full} maire de sa propre ville : on a testé.",
    "Les électeurs de {nom} vont me détester ({full}, {ville}).",
    "{ville} : la ville où {full} décide de tout.",
]
DESCRIPTIONS = [
    "Humour politique en animation 3D : dans {ville}, tout le monde vote {nom}. {full} ({parti_long}) aux "
    "commandes, la politique française comme tu ne l'as jamais vue{topic}. Présidentielle 2027, on s'échauffe.",
    "Parodie de la politique française : {full} et {avec} gèrent une ville entière{topic}. "
    "Humour politique, épisode {num} de {ville}, avant la présidentielle 2027.",
]
QUESTIONS = [
    "Pire ville jusqu'ici : {ville} ou {autre} ? Défends ton camp en commentaire 👇",
    "Qui gérerait le mieux ta ville : {nom} ou {nom_autre} ? 👇",
    "Tu habiterais à {ville} ? Sois honnête 👇",
]
SHARES = ["Envoie ça à ton pote qui vote {nom}.", "Envoie ça à quelqu'un qui défend {nom} à chaque repas de famille."]
NEXT = {"bardellaville": "macronville", "macronville": "melenchonville", "melenchonville": "zemmourville",
        "zemmourville": "marineville", "marineville": "glucksmannville", "glucksmannville": "bardellaville"}


def _pick(seq, key: str, salt: str):
    return seq[int(hashlib.sha1((key + salt).encode()).hexdigest(), 16) % len(seq)]


def _tag(word: str) -> str:
    w = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", w)


def _topic(ep: dict) -> str:
    for k in ("trend_keyword", "topic"):
        if ep.get(k):
            return str(ep[k]).strip()
    tr = ep.get("trend")
    if isinstance(tr, dict) and tr.get("keyword"):
        return str(tr["keyword"]).strip()
    return ""


def shop_line(city: str) -> str:
    """Ligne boutique seulement si le t-shirt de la ville est réellement en vente (jamais de lien mort)."""
    try:
        prods = json.loads((config.CONTENT / "products.json").read_text(encoding="utf-8"))
    except Exception:
        return ""
    for p in prods:
        if city in p.get("cities", []) and p.get("shop_url"):
            return "👕 Le t-shirt « j'ai fait un cauchemar » de l'épisode est en vente : lien en bio."
    return ""


def build(ep: dict) -> dict:
    """Renvoie {caption, hashtags, yt_title, yt_description, yt_tags} pour un épisode."""
    city, key = ep["city_id"], ep["id"]
    who = PEOPLE.get(city, {"nom": city, "full": city, "parti": "", "parti_long": "", "avec": "son équipe", "tags": [_tag(city)]})
    ville = CITY.get(city, city)
    autre_id = NEXT.get(city, city)
    topic = _topic(ep)
    f = dict(who, ville=ville, autre=CITY.get(autre_id, autre_id), nom_autre=PEOPLE.get(autre_id, who)["nom"],
             num=ep.get("episode_number") or "", topic=f", et cette fois : {topic}" if topic else "")
    first = _pick(FIRST_LINES, key, "l").format(**f)
    if topic:
        first = f"{who['full']} face à « {topic} » : on a fait la ville 😭"
    first = first[:125]
    lines = [first, "", _pick(DESCRIPTIONS, key, "d").format(**f), "",
             _pick(QUESTIONS, key, "q").format(**f), _pick(SHARES, key, "s").format(**f)]
    shop = shop_line(city)
    if shop:
        lines += ["", shop]
    fifth = _tag(topic) if topic and len(_tag(topic)) <= 25 else _pick(ROTATING, key, "r")
    tags = []
    for t in [*who["tags"], "humourpolitique", "politiquefrancaise", fifth]:
        if t and t not in tags:
            tags.append(t)
    tags = tags[:5]
    caption = "\n".join(lines) + "\n\n" + " ".join("#" + t for t in tags)
    yt_title = f"{who['full']} gère une ville entière 😭 {ville}"
    if topic:
        yt_title = f"{who['full']} : {topic} 😭 humour politique"
    yt_title = (yt_title[:90].rstrip() + " #Shorts")[:100]
    yt_desc = "\n".join([first, "", _pick(DESCRIPTIONS, key, "d").format(**f), "",
                         "Humour politique français en animation 3D : chaque ville est gérée par un politicien. "
                         "Abonne-toi pour la ville suivante.", "", " ".join("#" + t for t in tags) + " #Shorts"])
    yt_tags = [who["full"], who["nom"], who["parti"], who["parti_long"], "humour politique", "politique française",
               "présidentielle 2027", "parodie politique", "animation 3D", ville] + ([topic] if topic else [])
    return {"caption": caption, "hashtags": tags, "yt_title": yt_title, "yt_description": yt_desc[:4900],
            "yt_tags": [t for t in dict.fromkeys(yt_tags) if t]}
