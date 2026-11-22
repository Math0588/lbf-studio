"""Veille des sujets et des mèmes, avec traçabilité de chaque inspiration.

Sources gratuites automatiques : flux RSS publics (Google Actualités par personnalité, recherche Reddit r/france).
Source manuelle : dossier `inbox/` (liens ou textes déposés par le propriétaire, ou depuis le tableau de bord).
Source X : connecteur officiel facturé à l'usage, DÉSACTIVÉ en mode gratuit (X_ENABLED=false). Aucun scraping
ni contournement de connexion.

Tout contenu importé est une DONNÉE non fiable : il n'est jamais exécuté ni suivi comme une instruction, et ne
peut ni modifier la configuration ni déclencher une dépense. Les blagues collectées servent à repérer une
conversation : le générateur doit changer situation, construction et chute (contrôlé par antirepeat).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import config

PEOPLE = {
    "bardellaville": "Jordan Bardella",
    "melenchonville": "Jean-Luc Mélenchon",
    "macronville": "Emmanuel Macron",
    "zemmourville": "Éric Zemmour",
    "marineville": "Marine Le Pen",
    "glucksmannville": "Raphaël Glucksmann",
}
UA = "LeBordelFrancais-veille/1.0 (lecteur RSS)"
INBOX = config.ROOT / "inbox"
STORE = config.DATA / "inspirations.json"

# Sujets exclus de la génération : vie privée, famille, accusations et procédures judiciaires.
EXCLUDED_TOPICS = re.compile(r"compagne|compagnon|relation (amoureuse|avec)|mariage|enfant|fille de|fils de|"
                             r"accus|procès|condamn|mis en examen|enquête|plainte|justice|tribunal|santé|hôpital",
                             re.IGNORECASE)
INJECTION = re.compile(r"(ignore|oublie).{0,30}(instruction|consigne)|system prompt|api[_ ]?key|token|mot de passe",
                       re.IGNORECASE)


def _get(url: str, timeout=20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _clean(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:600]


def _rss(url: str, city: str, origin: str, status: str) -> list[dict]:
    out = []
    root = ET.fromstring(_get(url))
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for it in items[:25]:
        def f(tag):
            e = it.find(tag)
            if e is None:
                e = it.find("{http://www.w3.org/2005/Atom}" + tag)
            if e is None:
                return ""
            return e.get("href") if tag == "link" and e.get("href") else (e.text or "")
        title, link = _clean(f("title")), f("link").strip()
        desc = _clean(f("description") or f("content") or f("summary"))
        pub = f("pubDate") or f("updated") or f("published")
        out.append({"city": city, "origin": origin, "url": link, "source": origin, "title": title,
                    "excerpt": desc, "published": pub, "status": status})
    return out


def fetch_auto() -> list[dict]:
    found = []
    for city, person in PEOPLE.items():
        q = urllib.parse.quote(f'"{person}"')
        feeds = [
            (f"https://news.google.com/rss/search?q={q}+when:7d&hl=fr&gl=FR&ceid=FR:fr", "google_news", "fait_ou_opinion"),
            (f"https://www.reddit.com/r/france/search.rss?q={q}&restrict_sr=1&sort=top&t=week", "reddit_r_france",
             "opinion_ou_blague"),
        ]
        for url, origin, status in feeds:
            if origin.startswith("reddit"):
                import time
                time.sleep(6)  # Reddit limite le débit des lecteurs RSS anonymes
            try:
                found += _rss(url, city, origin, status)
            except Exception as e:  # une source en panne ne bloque jamais la série
                found.append({"city": city, "origin": origin, "error": str(e)[:200]})
    return found


def fetch_inbox() -> list[dict]:
    """Fichiers .txt/.md du dossier inbox : 1re ligne = URL (ou « propriétaire »), reste = texte/blague.
    Une ligne `droits: ...` indique l'autorisation de réutilisation."""
    out = []
    INBOX.mkdir(exist_ok=True)
    for p in sorted(INBOX.glob("*.*")):
        if p.suffix.lower() not in (".txt", ".md"):
            continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            continue
        url = lines[0].strip()
        rights = next((l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("droits:")), "inconnu")
        city = next((c for c in PEOPLE if c in p.stem.lower()), "transversal")
        body = "\n".join(l for l in lines[1:] if not l.lower().startswith("droits:"))
        out.append({"city": city, "origin": "inbox", "url": url, "source": url, "title": p.stem,
                    "excerpt": _clean(body), "published": "", "status": "blague_fournie" if "propri" in url
                    else "référence", "rights": rights})
    return out


def fetch_x() -> list[dict]:
    if not config.flag("X_ENABLED") or config.flag("FREE_MODE"):
        return []
    config.assert_free_mode_spend(0.01, "X API (lecture de posts)")  # lève en mode gratuit
    raise NotImplementedError("Connecteur X officiel à activer avec un budget plafonné (voir docs/FRAIS_LIMITES.md)")


def run() -> dict:
    store = json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else []
    known = {s["id"] for s in store}
    new = 0
    errors = []
    for item in fetch_auto() + fetch_inbox() + fetch_x():
        if "error" in item:
            errors.append(item)
            print("source indisponible :", item["city"], item["origin"], item["error"][:90])
            continue
        if INJECTION.search(item.get("excerpt", "") + item.get("title", "")):
            item["flag"] = "contenu suspect (texte adressé à une IA) : ignoré pour la génération"
        if EXCLUDED_TOPICS.search(item.get("title", "") + " " + item.get("excerpt", "")):
            item["excluded"] = "vie privée ou judiciaire : non utilisable comme base de gag"
        iid = hashlib.sha1((item.get("url") or item["title"]).encode()).hexdigest()[:16]
        if iid in known:
            continue
        item.update(id=iid, consulted=dt.datetime.now().isoformat(timespec="seconds"),
                    license="citation courte / référence uniquement" if item["origin"] != "inbox"
                    else item.get("rights", "inconnu"),
                    original_angle=None, used_in=[])
        store.append(item)
        known.add(iid)
        new += 1
    config.DATA.mkdir(exist_ok=True)
    STORE.write_text(json.dumps(store[-3000:], ensure_ascii=False, indent=1), encoding="utf-8")
    return {"new": new, "total": len(store), "errors": len(errors)}


if __name__ == "__main__":
    print(run())
