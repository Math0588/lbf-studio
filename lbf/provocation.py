"""Leviers de réaction (docs/VIRALITE_SCIENCE.md) : provoquer fort, sans se faire couper la diffusion.

Ce qui pousse l'algorithme : envois en message par compte touché (signal n°1 hors abonnés), temps de visionnage,
commentaires de vrais débats. Ce qui le casse : signalements massifs pour haine, fausses informations, appels au
harcèlement, « commente OUI si… » (engagement bait, rétrogradé par Instagram).

Donc : accroche qui pique en 0 s, roast frontal du politicien, rivalité entre villes/camps, envoi ciblé
(« Envoie ça à ton pote qui vote X »). Jamais : déshumaniser des électeurs, viser un groupe protégé, inventer un
fait, désigner une cible à harceler."""
from __future__ import annotations

import hashlib

NAMES = {"bardellaville": "Bardella", "melenchonville": "Mélenchon", "macronville": "Macron",
         "zemmourville": "Zemmour", "marineville": "Marine", "glucksmannville": "Glucksmann",
         "durifville": "Durif", "rinerville": "Teddy Riner"}
CITIES = {"bardellaville": "Bardellaville", "melenchonville": "Mélenchonville", "macronville": "Macronville",
          "zemmourville": "Zemmourville", "marineville": "Marineville", "glucksmannville": "Glucksmannville",
          "durifville": "Durifville", "rinerville": "Rinerville"}

# Rivalités : chaque vidéo provoque le camp d'en face (débat en commentaires), jamais d'insulte envers des électeurs.
RIVAL = {"melenchonville": "bardellaville", "bardellaville": "melenchonville", "glucksmannville": "melenchonville",
         "durifville": "macronville", "rinerville": "bardellaville",
         "zemmourville": "marineville", "marineville": "zemmourville", "macronville": "bardellaville"}
FANS = {"melenchonville": "insoumis", "bardellaville": "pro-Bardella", "macronville": "macronistes",
        "glucksmannville": "fans de Glucksmann", "zemmourville": "zemmouriens", "marineville": "pro-Marine",
        "durifville": "disciples cosmiques", "rinerville": "fans de Teddy"}
HOOKS_CAMP = ["LES {fans} VONT HURLER", "LES {fans} VONT PLEURER", "LES {fans} : RESPIREZ",
              "{fans}, NE REGARDEZ PAS", "LES {rivaux} VONT ADORER"]
HOOKS_SHORT = [
    "SI TU VOTES {nom}, NE REGARDE PAS",
    "INTERDIT AUX FANS DE {nom}",
    "LES PRO-{nom} VONT ME DÉTESTER",
    "ÇA VA PIQUER CHEZ {nom}",
    "{nom}, C'EST TOI QUI GÈRES ÇA ?",
]
HOOKS = [
    "Les électeurs de {nom} vont me détester",
    "Si tu votes {nom}, ne regarde pas",
    "Interdit aux fans de {nom}",
    "On a visité la ville de {nom}… aïe",
    "{nom}, c'est toi qui gères ça ?",
    "La ville la plus absurde de France ?",
    "Ça va piquer chez {nom}",
    "Personne ne nous croira",
]
SHARE_TITLES = [
    ("Envoie ça à ton pote qui vote {nom}", "et abonne-toi pour la ville suivante"),
    ("Abonne-toi", "prochaine ville : {next}"),
    ("Défends ta ville en commentaire", "la prochaine, c'est peut-être la tienne"),
]
CAPTION_OPENERS = [
    "Les électeurs de {nom}, vous défendez ça ? 👇",
    "Envoie ça à quelqu'un qui vote {nom} 😭",
    "Pire ville jusqu'ici : {ville} ou {autre} ? Défendez votre camp 👇",
    "{ville}, épisode {num}. On a reçu des menaces de rond-point.",
    "Dis-moi qui tu votes, je te dirai dans quelle ville tu habites 👇",
]
NEXT = {"bardellaville": "macronville", "macronville": "melenchonville", "melenchonville": "zemmourville",
        "zemmourville": "marineville", "marineville": "glucksmannville", "glucksmannville": "durifville",
        "durifville": "rinerville", "rinerville": "bardellaville"}


def _pick(seq, key: str, salt: str):
    h = int(hashlib.sha1((key + salt).encode()).hexdigest(), 16)
    return seq[h % len(seq)]


def apply(ep: dict) -> dict:
    """Ajoute accroche écrite, carte de fin et légende orientées réaction (rotation déterministe par épisode)."""
    city, key = ep["city_id"], ep["id"]
    nom, ville = NAMES.get(city, city), CITIES.get(city, city)
    autre = CITIES[NEXT.get(city, city)]
    # 1re image = sujet de la vidéo (titre + ville), lisible son coupé et dans l'aperçu du profil
    title = ep.get("title_cover") or _pick(HOOKS, key, "h").format(nom=nom)
    rival = RIVAL.get(city, NEXT.get(city, city))
    tag = _pick(HOOKS_CAMP, key, "t").format(fans=FANS.get(city, nom).upper(), rivaux=FANS.get(rival, "").upper())
    ep["hook_overlay"] = {"text": title, "tag": tag, "sub": ville.upper(), "until": 2.8}
    ep["endcard"] = {"title": f"Envoie ça à ton pote qui vote {nom}",
                     "sub": f"PROCHAINE VILLE : {CITIES.get(rival, rival).upper()}\\NLES {FANS.get(rival, '').upper()}, PRÉPAREZ-VOUS",
                     "at": 0.3}
    ep["premier_commentaire"] = (f"Bataille de commentaires 👇 Les {FANS.get(city, nom)} défendent {ville}, "
                                 f"les {FANS.get(rival, '')} préparent {CITIES.get(rival, rival)}. Qui a la ville la plus absurde ?")
    from . import seo                     # légende, hashtags et métadonnées YouTube optimisés pour la recherche
    meta = seo.build(ep)
    ep["caption"] = meta["caption"]
    ep["seo"] = {k: v for k, v in meta.items() if k != "caption"}
    return ep
