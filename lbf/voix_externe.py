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
        out.append(re.sub(r"\s+([,.])", r"\1", t))
    return "\n\n".join(out)


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


def split(mp3: Path, n: int, out_dir: Path) -> list[Path] | None:
    """Découpe en n morceaux sur les n-1 plus longs silences. None si impossible."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af",
                        "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(mp3)], capture_output=True, text=True).stdout.strip() or 0)
    sil = [(a, b) for a, b in zip(starts, ends) if a > 0.3 and b < dur - 0.3]
    if len(sil) < n - 1:
        return None
    cuts = sorted(sorted(sil, key=lambda x: x[1] - x[0], reverse=True)[: n - 1])
    bounds = [0.0] + [(a + b) / 2 for a, b in cuts] + [dur]
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
