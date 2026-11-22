"""Voix Azure Speech (offre gratuite F0 : 500 000 caractères/mois, usage commercial autorisé).

La clé n'est jamais dans le code ni dans le dépôt : variables d'environnement AZURE_SPEECH_KEY et
AZURE_SPEECH_REGION (secrets GitHub Actions ou .env local). Sans clé, ou en cas d'erreur, on retombe sur Piper.

Rythme comédie : débit un peu rapide, micro-pause avant la chute (après « ? », « : », « . » internes),
mots d'accent appuyés, pause plus longue avant la dernière pique."""
from __future__ import annotations

import html
import re
import urllib.request
import wave
from pathlib import Path

from . import config

DEFAULT_VOICE = "fr-FR-RemyMultilingualNeural"
VOICES = ["fr-FR-RemyMultilingualNeural", "fr-FR-HenriNeural", "fr-FR-VivienneMultilingualNeural"]
PRONUNCIATION = {"X": "X", "France Travail": "France Travail", "for sure": "for shure", "For sure": "For shure",
                 "GPS": "G.P.S.", "QG": "Q.G.", "TikTok": "Tik Tok", "Glucksmann": "Glouksmann"}


def available() -> bool:
    return bool(config.get("AZURE_SPEECH_KEY") and config.get("AZURE_SPEECH_REGION"))


def _spoken(text: str) -> str:
    out = text
    for k in sorted(PRONUNCIATION, key=len, reverse=True):
        out = re.sub(r"\b" + re.escape(k) + r"\b", PRONUNCIATION[k], out)
    out = re.sub(r"«\s*", "", out)
    out = re.sub(r"\s*»", "", out)
    return out.replace("«", "").replace("»", "").replace("“", "").replace("”", "")


def ssml(text: str, accents: list | None = None, voice: str | None = None, rate: str | None = None,
         last: bool = False) -> str:
    voice = voice or config.get("AZURE_VOICE") or DEFAULT_VOICE
    rate = rate or config.get("AZURE_RATE") or "+8%"
    body = html.escape(_spoken(text), quote=False)
    for w in sorted(accents or [], key=len, reverse=True):
        w_s = html.escape(_spoken(w), quote=False)
        if w_s and w_s in body:
            body = body.replace(w_s, f'<prosody pitch="+10%" volume="+20%" rate="-6%">{w_s}</prosody>', 1)
    # micro-pauses comiques : avant la chute
    body = re.sub(r"\?\s+", '? <break time="260ms"/>', body)
    body = re.sub(r"\s+:\s+", ' : <break time="180ms"/>', body)
    body = re.sub(r"\.\s+(?=\S)", '. <break time="220ms"/>', body)
    body = body.replace("…", '… <break time="300ms"/>')
    lead = '<break time="250ms"/>' if last else ""
    return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="fr-FR">'
            f'<voice name="{voice}"><prosody rate="{rate}" pitch="+2%">{lead}{body}</prosody></voice></speak>')


def synthesize(text: str, out_wav: Path, accents: list | None = None, voice: str | None = None,
               last: bool = False) -> float:
    region, key = config.get("AZURE_SPEECH_REGION"), config.get("AZURE_SPEECH_KEY")
    if not (region and key):
        raise RuntimeError("Azure Speech non configuré (AZURE_SPEECH_KEY / AZURE_SPEECH_REGION)")
    req = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml(text, accents, voice, last=last).encode("utf-8"),
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm", "User-Agent": "lbf-studio"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    out_wav.write_bytes(data)
    with wave.open(str(out_wav), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def engine() -> str:
    """Moteur choisi : TTS_ENGINE=azure|piper|auto (défaut auto : Azure si la clé existe)."""
    e = (config.get("TTS_ENGINE") or "auto").lower()
    if e == "auto":
        return "azure" if available() else "piper"
    return e


def report() -> dict:
    v = config.get("AZURE_VOICE") or DEFAULT_VOICE
    return {"engine": "azure", "voice": v, "attribution": f"Voix : Azure AI Speech ({v})",
            "license": "Azure AI Speech, voix neuronales standard : usage commercial autorisé (conditions Microsoft)"}
