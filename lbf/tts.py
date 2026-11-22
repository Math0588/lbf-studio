"""Synthèse vocale locale (Piper). Aucune dépendance cloud, aucun crédit payant."""
from __future__ import annotations

import hashlib
import json
import re
import wave
from pathlib import Path

from . import config

_VOICE_CACHE: dict = {}

# Corrections de prononciation pour la voix (texte affiché inchangé).
PRONUNCIATION = {
    "ring light": "rinne laïte",
    "ring lights": "rinne laïtes",
    "GPS": "G.P.S.",
    "Wi-Fi": "oui-fi",
    "t-shirts": "tishirts",
    "t-shirt": "tishirt",
    "Bardellaville": "Bardéllaville",
    "Mélenchonville": "Mélanchonville",
    "Macronville": "Macronnville",
    "Zemmourville": "Zémourville",
    "copro": "copro",
}


def spoken_form(text: str) -> str:
    out = text
    for k in sorted(PRONUNCIATION, key=len, reverse=True):
        out = re.sub(re.escape(k), PRONUNCIATION[k], out, flags=re.IGNORECASE)
    # guillemets typographiques : petite pause
    out = out.replace("«", ",").replace("»", ",").replace("“", "").replace("”", "")
    out = re.sub(r",\s*,", ",", out)
    return out.strip()


def voice_dir(model: str) -> Path:
    return config.VOICES / model


def check_voice(model: str) -> dict:
    """Vérifie que la voix est autorisée commercialement et que le fichier correspond au hash validé."""
    d = voice_dir(model)
    onnx = d / f"{model}.onnx"
    info = {"model": model, "exists": onnx.exists(), "cleared": model in config.CLEARED_VOICES}
    if onnx.exists():
        h = hashlib.sha256(onnx.read_bytes()).hexdigest()
        info["sha256"] = h
        info["hash_ok"] = info["cleared"] and h == config.CLEARED_VOICES[model]["sha256"]
        card = d / "MODEL_CARD"
        info["model_card"] = card.read_text(encoding="utf-8") if card.exists() else None
        if model == "fr_FR-siwis-medium" and info["model_card"] and "lessac" in info["model_card"]:
            info["hash_ok"] = False
            info["warning"] = "Ancienne version siwis (base lessac) : non autorisée commercialement"
    return info


def _load(model: str):
    from piper import PiperVoice

    if model not in _VOICE_CACHE:
        d = voice_dir(model)
        _VOICE_CACHE[model] = PiperVoice.load(d / f"{model}.onnx", config_path=d / f"{model}.onnx.json")
    return _VOICE_CACHE[model]


def synthesize(text: str, out_wav: Path, model: str | None = None, speaker: int | None = None,
               length_scale: float | None = None, require_cleared: bool = True) -> float:
    """Synthétise `text` dans `out_wav`. Retourne la durée en secondes."""
    from piper import SynthesisConfig

    model = model or config.get("VOICE_MODEL")
    if require_cleared:
        chk = check_voice(model)
        if not chk.get("hash_ok"):
            raise PermissionError(f"Voix non validée pour un usage commercial : {model} ({chk})")
    if speaker is None and config.get("VOICE_SPEAKER"):
        speaker = int(config.get("VOICE_SPEAKER"))
    ls = length_scale if length_scale is not None else float(config.get("VOICE_LENGTH_SCALE") or 1.0)
    voice = _load(model)
    syn = SynthesisConfig(speaker_id=speaker, length_scale=ls, noise_scale=0.6, noise_w_scale=0.7)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        voice.synthesize_wav(spoken_form(text), wf, syn_config=syn)
    with wave.open(str(out_wav), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def voice_report(model: str) -> dict:
    chk = check_voice(model)
    meta = config.CLEARED_VOICES.get(model, {})
    return {**{k: v for k, v in chk.items() if k != "model_card"}, "license": meta.get("license"),
            "attribution": meta.get("attribution")}


if __name__ == "__main__":
    print(json.dumps(voice_report(config.get("VOICE_MODEL")), ensure_ascii=False, indent=2))
