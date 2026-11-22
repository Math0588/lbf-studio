"""Voix ElevenLabs appelée directement par l'API, depuis GitHub Actions (aucun passage par Claude).

Activée si le secret ELEVENLABS_API_KEY existe (TTS_ENGINE=auto ou elevenlabs). Une requête par phrase :
pas de découpage à faire. Si une phrase échoue (quota épuisé, voix refusée, réseau), tout l'épisode
repasse sur le moteur suivant (Azure si sa clé existe, sinon Piper) : jamais deux voix dans une vidéo.

Réglages (variables du dépôt, facultatives) :
  ELEVENLABS_VOICE_ID  voix (défaut : « Hugo – Punchy French Creator », celle des premières vidéos)
  ELEVENLABS_MODEL     modèle (défaut eleven_v3, qui comprend les balises de ton comme [sarcastic])
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.error
import urllib.request
import wave
from pathlib import Path

from . import config

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
DEFAULT_VOICE = "3Tp5mYhT9wrfnry9pzvV"
DEFAULT_MODEL = "eleven_v3"
TAGGED_MODELS = ("eleven_v3", "eleven_v4")
ATTRIBUTION = "Voix : ElevenLabs (elevenlabs.io)"


def available() -> bool:
    return bool(config.get("ELEVENLABS_API_KEY").strip())


def wanted() -> bool:
    e = (config.get("TTS_ENGINE") or "auto").lower()
    return available() and e in ("auto", "elevenlabs")


def clean(text: str) -> str:
    t = text.replace("«", "").replace("»", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.])", r"\1", t)
    return re.sub(r"([!?])\.", r"\1", t)


def synthesize(text: str, wav: Path) -> float:
    """Une phrase → wav mono 48 kHz (silences de bord retirés, débit ×1,07 comme les voix validées)."""
    model = config.get("ELEVENLABS_MODEL").strip() or DEFAULT_MODEL
    voice = config.get("ELEVENLABS_VOICE_ID").strip() or DEFAULT_VOICE
    body = {"text": ("[sarcastic] " if model in TAGGED_MODELS else "") + clean(text), "model_id": model}
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": config.get("ELEVENLABS_API_KEY").strip(),
                                          "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        audio = urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode("utf-8", "replace")
        raise RuntimeError(f"ElevenLabs {e.code} : {detail}") from None
    if len(audio) < 2000:
        raise RuntimeError("ElevenLabs : fichier audio vide")
    mp3 = wav.with_suffix(".el.mp3")
    mp3.write_bytes(audio)
    trim = "silenceremove=start_periods=1:start_threshold=-45dB"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-af",
                    f"{trim},areverse,{trim},areverse,atempo=1.07", "-ar", "48000", "-ac", "1", str(wav)],
                   check=True)
    with wave.open(str(wav), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def report() -> dict:
    return {"engine": "elevenlabs", "voice": config.get("ELEVENLABS_VOICE_ID").strip() or DEFAULT_VOICE,
            "attribution": ATTRIBUTION}
