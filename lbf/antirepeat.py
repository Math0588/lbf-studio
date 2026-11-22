"""Contrôle anti-répétition : prémisse, mécanisme comique, formulation et chute comparés à toute la banque
(synopsis, scripts, épisodes produits, inspirations collectées). Un simple changement de nom ou de lieu
ne suffit pas à faire un épisode nouveau."""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from . import config

CITY_WORDS = r"bardellaville|m[ée]lenchonville|macronville|zemmourville|marineville|glucksmannville|ville"
STOP = set("le la les un une des de du d l à a au aux et ou en dans sur pour par avec ce cette ces qui que quoi "
           "il elle on ils elles se sa son ses leur leurs ne pas plus est sont été être fait faire tout tous "
           "même ici y n s c qu j t m".split())


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(CITY_WORDS, " ", s)
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def ngrams(s: str, n=4) -> Counter:
    s = norm(s).replace(" ", "_")
    return Counter(s[i:i + n] for i in range(max(0, len(s) - n + 1)))


def words(s: str) -> Counter:
    return Counter(w for w in norm(s).split() if w not in STOP and len(w) > 2)


def cos(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())))


def fields(item: dict) -> dict:
    """Extrait prémisse / chute / mécanisme d'un synopsis, d'un script ou d'un épisode."""
    if "narration_segments" in item:
        segs = [s["text"] for s in item["narration_segments"]]
        premise = item.get("premise") or (segs[0] if segs else "")
        ending = item.get("ending_variants", [segs[-2] if len(segs) > 1 else ""])[item.get("selected_ending", 0)] \
            if item.get("ending_variants") else (segs[-2] if len(segs) > 1 else "")
        full = " ".join(segs)
    else:
        premise = " ".join([item.get("daily_problem", ""), item.get("hook", "")])
        ending = item.get("visual_punchline", "")
        full = " ".join(str(item.get(k, "")) for k in ("hook", "development_1", "development_2", "visual_punchline"))
    return {"premise": premise, "ending": ending, "full": full,
            "mechanism": norm(item.get("comic_mechanism", "") or " ".join(item.get("novelty_tags", [])))}


def bank() -> list[dict]:
    out = []
    for p in sorted((config.CONTENT / "synopses").glob("*.json")):
        for s in json.loads(p.read_text(encoding="utf-8")):
            out.append({"id": s["id"], "kind": "synopsis", "city": s.get("city"), **fields(s)})
    for d in ("scripts", "episodes"):
        for p in sorted((config.CONTENT / d).glob("*.json")):
            s = json.loads(p.read_text(encoding="utf-8"))
            out.append({"id": s["id"], "kind": d[:-1], "city": s.get("city") or s.get("city_id"), **fields(s)})
    insp = config.DATA / "inspirations.json"
    if insp.exists():
        for s in json.loads(insp.read_text(encoding="utf-8")):
            if s.get("excerpt") or s.get("title"):
                txt = (s.get("title", "") + " " + s.get("excerpt", ""))
                out.append({"id": s["id"], "kind": "inspiration", "city": s.get("city"), "premise": txt,
                            "ending": txt, "full": txt, "mechanism": ""})
    return out


def compare(candidate: dict, exclude_ids=(), threshold=0.55) -> dict:
    c = fields(candidate)
    cg_full, cw_prem, cw_end = ngrams(c["full"]), words(c["premise"]), words(c["ending"])
    hits = []
    for b in bank():
        if b["id"] in exclude_ids or b["id"] == candidate.get("id"):
            continue
        s_full = cos(cg_full, ngrams(b["full"]))
        s_prem = cos(cw_prem, words(b["premise"]))
        s_end = cos(cw_end, words(b["ending"]))
        s_mech = 1.0 if c["mechanism"] and c["mechanism"] == b["mechanism"] else 0.0
        score = 0.4 * s_full + 0.25 * s_prem + 0.25 * s_end + 0.1 * s_mech
        if b["kind"] == "inspiration":
            score = s_full  # recopie d'un texte collecté : on regarde la formulation
        if score >= threshold * 0.8:
            hits.append({"id": b["id"], "kind": b["kind"], "score": round(score, 3), "full": round(s_full, 3),
                         "premise": round(s_prem, 3), "ending": round(s_end, 3)})
    hits.sort(key=lambda h: -h["score"])
    return {"too_similar": bool(hits and hits[0]["score"] >= threshold), "nearest": hits[:5]}


def audit_bank(threshold=0.55) -> list:
    """Paires trop proches dans toute la banque (hors inspirations)."""
    items = [b for b in bank() if b["kind"] != "inspiration"]
    grams = [(b, ngrams(b["full"]), words(b["premise"]), words(b["ending"])) for b in items]
    pairs = []
    for i in range(len(grams)):
        for j in range(i + 1, len(grams)):
            a, b = grams[i], grams[j]
            if a[0]["id"].split("-")[0] != b[0]["id"].split("-")[0] and a[0]["city"] == b[0]["city"]:
                pass
            sc = 0.5 * cos(a[1], b[1]) + 0.25 * cos(a[2], b[2]) + 0.25 * cos(a[3], b[3])
            if sc >= threshold:
                pairs.append((round(sc, 3), a[0]["id"], b[0]["id"]))
    return sorted(pairs, reverse=True)


if __name__ == "__main__":
    import sys
    pairs = audit_bank(float(sys.argv[1]) if len(sys.argv) > 1 else 0.55)
    print(f"{len(pairs)} paires au-dessus du seuil")
    for p in pairs[:40]:
        print(p)
