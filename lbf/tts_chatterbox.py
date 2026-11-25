"""Voix open source Chatterbox Multilingual (Resemble AI, licence MIT, usage commercial autorisé), sur CPU.

Le modèle tourne dans son propre environnement (CBX_PYTHON, installé par le workflow de fabrication) via
tools/cbx_worker.py. Toutes les phrases de l'épisode en un seul appel (modèle chargé une fois), graine fixe par
phrase. Si quoi que ce soit échoue, l'épisode passe au moteur suivant ; jamais deux voix dans une vidéo.
Réglages (variables du dépôt) : CBX_EXAGGERATION (défaut 0.7, plus expressif), CBX_CFG (défaut 0.3),
CBX_REF (extrait de voix de référence, facultatif)."""
from __future__ import annotations

import json
import os
import subprocess
import wave
from pathlib import Path

from . import config

PY = os.environ.get("CBX_PYTHON", "/opt/cbx/bin/python")
WORKER = config.ROOT / "tools" / "cbx_worker.py"
ATTRIBUTION = "Voix : Chatterbox (Resemble AI, licence MIT)"


def available() -> bool:
    return Path(PY).exists() and WORKER.exists()


def wanted() -> bool:
    e = (config.get("TTS_ENGINE") or "auto").lower()
    return available() and e in ("auto", "chatterbox")


def synthesize_all(texts: list[str], out_dir: Path, seed: int = 7) -> list[float]:
    """Toutes les phrases → wav mono 48 kHz (silences de bord retirés, débit ×1,05). Renvoie les durées."""
    from .tts_elevenlabs import clean
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = [out_dir / f"cbx_{i}.wav" for i in range(len(texts))]
    job = {"items": [{"text": clean(t), "out": str(r)} for t, r in zip(texts, raw)],
           "ref": config.get("CBX_REF") or None,
           "exaggeration": float(config.get("CBX_EXAGGERATION") or 0.7),
           "cfg": float(config.get("CBX_CFG") or 0.3), "seed": seed}
    jf = out_dir / "cbx_job.json"
    jf.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    subprocess.run([PY, str(WORKER), str(jf)], check=True, timeout=3600)
    durs = []
    trim = "silenceremove=start_periods=1:start_threshold=-45dB"
    for i, r in enumerate(raw):
        w = out_dir / f"seg_{i}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(r), "-af",
                        f"{trim},areverse,{trim},areverse,atempo=1.05", "-ar", "48000", "-ac", "1", str(w)], check=True)
        with wave.open(str(w), "rb") as wf:
            durs.append(wf.getnframes() / float(wf.getframerate()))
    return durs


def report() -> dict:
    return {"engine": "chatterbox", "voice": "Chatterbox Multilingual (fr)", "attribution": ATTRIBUTION,
            "license": "MIT (Resemble AI)"}
