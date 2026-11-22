"""Narrations enregistrées à l'avance (ElevenLabs, offre de démarrage) : un fichier par épisode,
assets/voix/<id>.mp3, téléchargé par le workflow « Voix » depuis assets/voix/urls.json.

Le fichier contient toute la narration, phrases séparées par des pauses. On le découpe sur les N-1 plus longs
silences ; si le découpage ne tombe pas juste (texte modifié, pauses ambiguës), on revient à la voix locale."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import config

DIR = config.ASSETS / "voix"
ATTRIBUTION = "Voix : ElevenLabs (elevenlabs.io)"


def text_key(segs: list) -> str:
    return hashlib.sha1("\n".join(s["text"] for s in segs).encode()).hexdigest()[:12]


def prompt_for(segs: list) -> str:
    """Texte envoyé à ElevenLabs : une phrase par ligne, pause marquée entre les phrases."""
    out = []
    for s in segs:
        t = s["text"].replace("«", "").replace("»", "")
        t = re.sub(r"\s+", " ", t).strip()
        t = re.sub(r"\s+([,.])", r"\1", t)
        out.append(re.sub(r"([!?])\.", r"\1", t))
    # ton moqueur sur toute la narration ; longue pause entre les phrases (découpage sans ambiguïté)
    return "[sarcastic] " + "\n[long pause]\n".join(out)


def available(ep: dict) -> Path | None:
    meta = DIR / "urls.json"
    if not meta.exists():
        return None
    m = json.loads(meta.read_text(encoding="utf-8")).get(ep["id"])
    f = DIR / f"{ep['id']}.mp3"
    k = DIR / f"{ep['id']}.key"
    key = text_key(ep["narration_segments"])
    if not m or not f.exists() or m.get("key") != key or not k.exists() or k.read_text().strip() != key:
        return None
    return f


def split(mp3: Path, n: int, out_dir: Path, weights: list | None = None) -> list[Path] | None:
    """Découpe en n morceaux. Les coupures sont choisies parmi les silences, au plus près des frontières attendues
    (durée proportionnelle au nombre de mots de chaque phrase), en préférant les silences longs.
    None si le résultat n'est pas cohérent (on revient alors à la voix locale)."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af",
                        "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(mp3)], capture_output=True, text=True).stdout.strip() or 0)
    sil = [((a + b) / 2, b - a) for a, b in zip(starts, ends) if a > 0.3 and b < dur - 0.3]
    longs = [x for x in sil if x[1] >= 0.55]
    if len(longs) == n - 1:   # enregistrement avec [long pause] : les coupures sont les longues pauses
        sil = longs
    if len(sil) < n - 1:
        return None
    w = weights or [1] * n
    tot = float(sum(w))
    exp = [dur * sum(w[:k + 1]) / tot for k in range(n - 1)]
    m = len(sil)
    INF = float("inf")
    # programmation dynamique : coût = écart à la frontière attendue - bonus de longueur du silence
    cost = [[INF] * m for _ in range(n - 1)]
    back = [[-1] * m for _ in range(n - 1)]
    for j in range(m):
        cost[0][j] = abs(sil[j][0] - exp[0]) - 1.2 * sil[j][1]
    for k in range(1, n - 1):
        for j in range(m):
            c = abs(sil[j][0] - exp[k]) - 1.2 * sil[j][1]
            best, bi = INF, -1
            for i in range(j):
                if cost[k - 1][i] < best:
                    best, bi = cost[k - 1][i], i
            if bi >= 0:
                cost[k][j], back[k][j] = best + c, bi
    j = min(range(m), key=lambda x: cost[n - 2][x])
    if cost[n - 2][j] == INF:
        return None
    picks = [j]
    for k in range(n - 2, 0, -1):
        j = back[k][j]
        picks.append(j)
    cuts = [sil[i][0] for i in reversed(picks)]
    bounds = [0.0] + cuts + [dur]
    # contrôle : chaque morceau doit ressembler à sa phrase (durée par mot plausible)
    for k in range(n):
        got, want = bounds[k + 1] - bounds[k], dur * w[k] / tot
        if not 0.5 * want <= got <= 1.9 * want:
            return None
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(n):
        f = out_dir / f"ext_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{bounds[i]:.3f}", "-to", f"{bounds[i + 1]:.3f}",
                        "-i", str(mp3), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo=1.07",
                        "-ar", "48000", "-ac", "1", str(f)], check=True)
        files.append(f)
    return files
