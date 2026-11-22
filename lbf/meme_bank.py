"""Téléchargement de la banque de sons mèmes (exécuté dans GitHub Actions : accès réseau ouvert).
Pour chaque entrée de assets/memes/queries.json : recherche myinstants (pages FR puis EN), on garde le résultat
dont le titre correspond le mieux (mots obligatoires « must »), coupe à 4 s, normalisation. Les candidats sont
gardés dans le manifeste pour vérification ; approved=true seulement après écoute par le propriétaire."""
from __future__ import annotations

import html as H
import json
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request

from . import config

DIR = config.ASSETS / "memes"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def results(q: str) -> list[dict]:
    out = []
    for lang in ("fr", "en"):
        try:
            page = get(f"https://www.myinstants.com/{lang}/search/?name=" + urllib.parse.quote(q)).decode("utf-8", "replace")
        except Exception:
            continue
        for block in page.split('class="instant"')[1:]:
            mp3 = re.search(r"play\('(/media/sounds/[^']+?\.mp3)'", block)
            a = re.search(r'<a[^>]*href="(/[a-z]{2}/instant/[^"]+)"[^>]*>([^<]+)</a>', block)
            if mp3:
                out.append({"mp3": "https://www.myinstants.com" + mp3.group(1),
                            "page": ("https://www.myinstants.com" + a.group(1)) if a else None,
                            "title": H.unescape(a.group(2)).strip() if a else ""})
        if out:
            break
    return out


def score(q: str, must: list, r: dict) -> float:
    t = norm(r["title"] + " " + r["mp3"].rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
    if any(f" {norm(m)} " not in f" {t} " for m in must):   # mots entiers (« cap » ≠ « handicapés »)
        return -1
    qw = set(norm(q).split())
    return len(qw & set(t.split())) / max(1, len(qw)) - 0.01 * len(t.split())


def fetch(key: str, spec: dict) -> dict:
    q, must = spec["q"], spec.get("must", [])
    res, ranked = [], []
    for qq in [q] + spec.get("alt", []):          # recherches alternatives si rien de conforme
        res = results(qq)
        ranked = sorted(res, key=lambda r: score(q, must, r), reverse=True)
        if ranked and score(q, must, ranked[0]) >= 0:
            break
    if spec.get("pick") is not None and spec["pick"] < len(ranked):
        best = ranked[spec["pick"]]
    else:
        best = ranked[0] if ranked and score(q, must, ranked[0]) >= 0 else None
    if not best:
        return {"key": key, "q": q, "ok": False, "error": "aucun résultat conforme",
                "candidates": [r["title"] for r in res[:5]]}
    raw = DIR / f"_{key}.mp3"
    raw.write_bytes(get(best["mp3"]))
    out = DIR / f"{key}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,atrim=0:4,"
                    "loudnorm=I=-16:TP=-2,areverse,afade=t=in:d=0.15,areverse",
                    "-ar", "48000", "-ac", "1", str(out)], check=True)
    raw.unlink()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout.strip() or 0)
    ok = dur >= 0.25
    return {"key": key, "q": q, "ok": ok, "file": out.name, "duration": round(dur, 2), "source_mp3": best["mp3"],
            "page": best["page"], "title": best["title"], "candidates": [r["title"] for r in ranked[:4]],
            **({} if ok else {"error": "son vide après découpe"})}


def main():
    qs = json.loads((DIR / "queries.json").read_text(encoding="utf-8"))
    old = {m["key"]: m for m in json.loads((DIR / "manifest.json").read_text(encoding="utf-8"))} \
        if (DIR / "manifest.json").exists() else {}
    man = []
    for k, v in qs.items():
        if k.startswith("_"):
            continue
        try:
            r = fetch(k, v)
        except Exception as e:
            r = {"key": k, "q": v["q"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:150]}"}
        for f in ("role", "cities", "quote_match"):
            if v.get(f):
                r[f] = v[f]
        o = old.get(k, {})
        # une validation reste valable tant que le fichier source n'a pas changé
        r["approved"] = bool(o.get("approved")) and o.get("source_mp3") == r.get("source_mp3")
        print(json.dumps({x: r.get(x) for x in ("key", "ok", "title", "duration", "approved", "error")},
                         ensure_ascii=False), flush=True)
        man.append(r)
    (DIR / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
