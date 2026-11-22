"""Configuration centrale. Valeurs par défaut sûres : mode gratuit, aucune dépense, aucune publication réelle."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
DATA = ROOT / "data"
BLENDER_ENGINE = ROOT / "blender" / "engine.py"
FONTS = ASSETS / "fonts"
VOICES = ASSETS / "voices"

DEFAULTS = {
    "FREE_MODE": "true",
    "MAX_API_SPEND": "0",
    "X_ENABLED": "false",
    "PAID_VIDEO_GENERATION": "false",
    "PAID_TTS": "false",
    "LIVE_PUBLISH": "false",
    "PAUSED": "false",
    "TIMEZONE": "Europe/Paris",
    "PUBLISH_SLOT": "18:30", "PUBLISH_SLOTS": "12:30,19:00",
    "RESERVE_TARGET_DAYS": "10",
    "VOICE_MODEL": "fr_FR-siwis-medium",
    "VOICE_SPEAKER": "",
    "VOICE_LENGTH_SCALE": "1.0",
    "RENDER_PROFILE": "final",
    "BLENDER_PATH": "",
    "OLLAMA_MODEL": "qwen3:14b",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "DASHBOARD_HOST": "127.0.0.1",
    "DASHBOARD_PORT": "8765",
    "DASHBOARD_TOKEN": "",
    "MIN_FREE_DISK_GB": "15",
    "IG_API": "instagram_login",
    "IG_GRAPH_VERSION": "v27.0", "IG_API_HOST": "https://graph.facebook.com",
}

# Voix dont la chaîne de licence complète autorise l'usage commercial (vérifié sur
# piper1-gpl/docs/COMMERCIAL_USE.md le 2026-11-21, MODEL_CARD contrôlée).
CLEARED_VOICES = {
    "fr_FR-siwis-medium": {
        "license": "CC BY 4.0 (SIWIS) + CC BY 4.0 (Hi-Fi TTS reader 92, base)",
        "attribution": "Voix : Piper fr_FR-siwis-medium — SIWIS French Speech Synthesis Database (CC BY 4.0) ; "
                       "base Hi-Fi TTS reader 92 (CC BY 4.0).",
        "sha256": "b1d946fd68d0347155fa59bce0a018924abbef3c1561181db45ca463d83963ef",
    },
    "fr_FR-mls-medium": {
        "license": "CC BY 4.0 (Multilingual LibriSpeech, OpenSLR 94), entraînée de zéro",
        "attribution": "Voix : Piper fr_FR-mls-medium — Multilingual LibriSpeech (OpenSLR 94, CC BY 4.0).",
        "sha256": "0ed223f78466917f2bae05ee90096ce69ab1fdeb251f55590d0e7422d234e162",
    },
}


def _load_env_file() -> dict:
    env = {}
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get(key: str) -> str:
    if key in os.environ:
        return os.environ[key]
    file_env = _load_env_file()
    if key in file_env:
        return file_env[key]
    return DEFAULTS.get(key, "")


def flag(key: str) -> bool:
    return get(key).lower() in ("1", "true", "yes", "oui")


def blender_path() -> str:
    p = get("BLENDER_PATH")
    if p and Path(p).exists():
        return p
    found = shutil.which("blender")
    if found:
        return found
    base = Path(r"C:\Program Files\Blender Foundation")
    if base.exists():
        cands = sorted(base.glob("Blender */blender.exe"), reverse=True)
        if cands:
            return str(cands[0])
    raise FileNotFoundError("Blender introuvable : renseigner BLENDER_PATH dans .env")


def assert_free_mode_spend(cost_eur: float, what: str) -> None:
    """Garde-fou : en mode gratuit, toute opération payante est refusée."""
    if cost_eur > 0 and (flag("FREE_MODE") or float(get("MAX_API_SPEND") or 0) < cost_eur):
        raise PermissionError(f"Dépense refusée en mode gratuit : {what} ({cost_eur} €)")
