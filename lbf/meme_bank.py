"""Téléchargement de la banque de sons mèmes (exécuté dans GitHub Actions : accès réseau ouvert).
Pour chaque entrée de assets/memes/queries.json : recherche myinstants, 1er résultat, coupe à 3 s, normalisation."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from . import config

DIR = config.ASSETS / "memes"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def fetch(key: str, q: str) -> dict:
    html = get("https://www.myinstants.com/fr/search/?name=" + urllib.parse.quote(q)).decode("utf-8", "replace")
    m = re.search(r"play\('(/media/sounds/[^']+\.mp3)'", html)
    t = re.search(r'class="instant-link[^"]*"\s+href="([^"]+)"[^>]*>([^<]+)<', html)
    if not m:
        return {"key": key, "q": q, "ok": False, "error": "aucun résultat"}
    src = "https://www.myinstants.com" + m.group(1)
    raw = DIR / f"_{key}.mp3"
    raw.write_bytes(get(src))
    out = DIR / f"{key}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-t", "3", "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,loudnorm=I=-16:TP=-2,afade=t=out:st=2.7:d=0.3",
                    "-ar", "48000", "-ac", "1", str(out)], check=True)
    raw.unlink()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout.strip() or 0)
    return {"key": key, "q": q, "ok": True, "file": out.name, "duration": round(dur, 2), "source_mp3": src,
            "page": ("https://www.myinstants.com" + t.group(1)) if t else None,
            "title": t.group(2).strip() if t else None}


def main():
    qs = json.loads((DIR / "queries.json").read_text(encoding="utf-8"))
    old = {m["key"]: m for m in json.loads((DIR / "manifest.json").read_text(encoding="utf-8"))} \
        if (DIR / "manifest.json").exists() else {}
    man = []
    for k, v in qs.items():
        if k.startswith("_"):
            continue
        try:
            r = fetch(k, v["q"])
        except Exception as e:
            r = {"key": k, "q": v["q"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:150]}"}
        r.update(role=v.get("role", []), cities=v.get("cities"))
        # validation à l'écoute par le propriétaire (approved=true) : un son non écouté n'entre jamais au montage
        r["approved"] = bool(old.get(k, {}).get("approved")) and old.get(k, {}).get("source_mp3") == r.get("source_mp3")
        print(r, flush=True)
        man.append(r)
    (DIR / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
