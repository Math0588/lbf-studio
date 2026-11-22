"""Module optionnel : publication YouTube Shorts (API YouTube Data v3 officielle, gratuite dans le quota).

Activé seulement si YT_ENABLED=true et les secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN existent
(obtenus une fois par le propriétaire via l'écran de consentement OAuth Google). Un échec YouTube ne bloque
jamais Instagram. Envoi reprenable (resumable upload) ; l'identifiant vidéo est persisté avant tout nouvel essai.
Quota : un envoi coûte 1 600 unités sur 10 000/jour par défaut (à vérifier dans la console Google Cloud).
Note : une vidéo envoyée par l'API depuis un projet Google Cloud non audité peut être limitée en « privée »
tant que le projet n'est pas vérifié — à confirmer lors du premier essai (statut renvoyé).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def env(k, d=""):
    return os.environ.get(k, d).strip()


def enabled() -> bool:
    """Actif par défaut dès que les 3 secrets Google existent (désactivable avec YT_ENABLED=false)."""
    return env("YT_ENABLED", "true") != "false" and \
        all(env(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def access_token() -> str:
    data = urllib.parse.urlencode({"client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"),
                                   "refresh_token": env("YT_REFRESH_TOKEN"), "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def upload(video: Path, title: str, description: str, tags: list[str]) -> dict:
    tok = access_token()
    meta = {"snippet": {"title": title[:95] + " #shorts", "description": description[:4500], "tags": tags[:15],
                        "categoryId": "23", "defaultLanguage": "fr"},
            "status": {"privacyStatus": env("YT_PRIVACY", "public"), "selfDeclaredMadeForKids": False}}
    body = json.dumps(meta).encode()
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(video.stat().st_size)})
    with urllib.request.urlopen(init, timeout=60) as r:
        loc = r.headers["Location"]
    put = urllib.request.Request(loc, data=video.read_bytes(), method="PUT",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
    with urllib.request.urlopen(put, timeout=600) as r:
        res = json.loads(r.read().decode())
    return {"video_id": res.get("id"), "url": f"https://youtube.com/shorts/{res.get('id')}",
            "privacy": res.get("status", {}).get("privacyStatus"), "upload_status": res.get("status", {}).get("uploadStatus")}
