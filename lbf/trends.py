"""Détection des tendances politiques (gratuite) → épisodes d'actualité prioritaires.

Un sujet est « chaud » pour une ville quand le nombre de titres récents sur la personnalité explose par rapport à
la moyenne des 7 jours précédents. On prend le titre le plus représentatif (mots communs), hors sujets exclus
(vie privée, justice, santé). Le titre est une DONNÉE : il inspire une transposition absurde dans la ville
fictive, jamais une affirmation factuelle ; sa source est enregistrée."""
from __future__ import annotations

import datetime as dt
import email.utils
import json
import re
from collections import Counter

from . import config
from .antirepeat import words

STORE = config.DATA / "inspirations.json"
USED = config.DATA / "trends_used.json"


def _date(s: str):
    try:
        return email.utils.parsedate_to_datetime(s).astimezone().replace(tzinfo=None)
    except Exception:
        try:
            return dt.datetime.fromisoformat(s[:19])
        except Exception:
            return None


def hot_topics(now: dt.datetime | None = None, min_24h: int = 6, ratio: float = 2.0) -> list[dict]:
    if not STORE.exists():
        return []
    now = now or dt.datetime.now()
    items = [i for i in json.loads(STORE.read_text(encoding="utf-8")) if not i.get("excluded") and not i.get("flag")]
    used = set(json.loads(USED.read_text(encoding="utf-8"))) if USED.exists() else set()
    out = []
    for city in {i["city"] for i in items}:
        recent, before = [], []
        for i in items:
            if i["city"] != city:
                continue
            d = _date(i.get("published", ""))
            if not d:
                continue
            age = (now - d).total_seconds() / 3600
            if age <= 24:
                recent.append(i)
            elif age <= 24 * 8:
                before.append(i)
        base = max(1.0, len(before) / 7)
        if len(recent) < min_24h or len(recent) / base < ratio:
            continue
        common = Counter(w for i in recent for w in set(words(i.get("title", ""))))
        best = max(recent, key=lambda i: sum(common[w] for w in set(words(i.get("title", "")))))
        if best["id"] in used:
            continue
        out.append({"city": city, "item": best, "volume_24h": len(recent), "ratio": round(len(recent) / base, 1),
                    "keywords": [w for w, _ in common.most_common(6)]})
    return sorted(out, key=lambda x: -x["ratio"])


def mark_used(item_id: str) -> None:
    used = json.loads(USED.read_text(encoding="utf-8")) if USED.exists() else []
    used.append(item_id)
    USED.write_text(json.dumps(used[-500:]), encoding="utf-8")


if __name__ == "__main__":
    for t in hot_topics():
        print(t["city"], t["volume_24h"], t["ratio"], t["item"]["title"][:100])
