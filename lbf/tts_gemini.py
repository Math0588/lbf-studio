"""Voix Google Gemini TTS (clé gratuite AI Studio, secret GEMINI_API_KEY), sans Claude.

Une seule requête par vidéo : toute la narration, avec une consigne de ton en langage naturel (sarcastique,
moqueur, punchy, français de France), puis découpage phrase par phrase sur les silences (même outil que pour
les narrations ElevenLabs). Si le découpage ne tombe pas juste : une requête par phrase. Si tout échoue, le
moteur suivant prend l'épisode entier (jamais deux voix dans une vidéo).

Réglages (variables du dépôt, facultatives) :
  GEMINI_TTS_MODEL  (défaut gemini-2.5-flash-preview-tts)
  GEMINI_VOICE      (défaut Charon, choisie par le propriétaire ; autres : Puck, Fenrir, Orus…)
  GEMINI_STYLE      consigne de ton (défaut ci-dessous)
"""
from __future__ import annotations

import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

from . import config

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Charon"   # choisie par le propriétaire le 25/11 (posée, pince-sans-rire)
DEFAULT_STYLE = ("Lis ce texte en français de France, sans aucun accent étranger, comme un humoriste qui se moque : "
                 "ton sarcastique, pince-sans-rire et punchy, débit rapide d'une vidéo TikTok, énergie haute. "
                 "Marque un silence net d'une demi-seconde entre chaque ligne. Ne lis que le texte, pas cette consigne :")
ATTRIBUTION = "Voix : Google Gemini (synthèse vocale)"


def available() -> bool:
    return bool(config.get("GEMINI_API_KEY").strip())


def wanted() -> bool:
    e = (config.get("TTS_ENGINE") or "auto").lower()
    return available() and e in ("auto", "gemini")


def _request(text: str, out_wav: Path) -> float:
    model = config.get("GEMINI_TTS_MODEL").strip() or DEFAULT_MODEL
    voice = config.get("GEMINI_VOICE").strip() or DEFAULT_VOICE
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    last = None
    for attempt in range(3):
        req = urllib.request.Request(API.format(model=model), data=json.dumps(body).encode(), method="POST",
                                     headers={"x-goog-api-key": config.get("GEMINI_API_KEY").strip(),
                                              "Content-Type": "application/json"})
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=180).read())
            part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
            pcm = base64.b64decode(part["data"])
            rate = 24000
            mime = part.get("mimeType", "")
            if "rate=" in mime:
                rate = int(mime.split("rate=")[1].split(";")[0])
            with wave.open(str(out_wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(pcm)
            return len(pcm) / 2 / rate
        except urllib.error.HTTPError as e:
            last = RuntimeError(f"Gemini {e.code} : {e.read()[:300].decode('utf-8', 'replace')}")
            if e.code not in (429, 500, 503):
                break
            time.sleep(20 * (attempt + 1))      # quota par minute de l'offre gratuite
        except (KeyError, IndexError, ValueError) as e:
            last = RuntimeError(f"Gemini : réponse sans audio ({e})")
            break
    raise last


def _finish(src: Path, dst: Path) -> float:
    trim = "silenceremove=start_periods=1:start_threshold=-45dB"
    tempo = float(config.get("GEMINI_TEMPO") or 1.0)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af",
                    f"{trim},areverse,{trim},areverse,atempo={tempo}", "-ar", "48000", "-ac", "1", str(dst)], check=True)
    with wave.open(str(dst), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def synthesize_all(texts: list[str], out_dir: Path) -> list[float]:
    """Toutes les phrases d'un épisode → seg_i.wav (48 kHz mono). Renvoie les durées."""
    from . import voix_externe
    from .tts_elevenlabs import clean
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [clean(t) for t in texts]
    style = config.get("GEMINI_STYLE").strip() or DEFAULT_STYLE
    parts = None
    for attempt in range(2):            # une requête par essai : le quota gratuit est compté en requêtes
        whole = out_dir / f"gemini_full_{attempt}.wav"
        _request(style + "\n\n" + "\n".join(lines), whole)
        parts = voix_externe.split(whole, len(lines), out_dir / f"split_{attempt}", [len(t.split()) for t in lines])
        if parts:
            break
        print("[voix] Gemini : découpage incertain, nouvelle prise", flush=True)
        time.sleep(30)
    if not parts and config.get("GEMINI_PER_LINE") == "true":   # coûteux en quota : seulement sur demande
        parts = []
        for i, t in enumerate(lines):
            pth = out_dir / f"line_{i}.wav"
            _request(style + "\n\n" + t, pth)
            parts.append(pth)
            time.sleep(25)
    if not parts:
        raise RuntimeError("Gemini : découpage impossible après 2 prises")
    return [_finish(Path(p), out_dir / f"seg_{i}.wav") for i, p in enumerate(parts)]


def report() -> dict:
    v = config.get("GEMINI_VOICE").strip() or DEFAULT_VOICE
    return {"engine": "gemini", "voice": f"Gemini {v}", "attribution": ATTRIBUTION}
