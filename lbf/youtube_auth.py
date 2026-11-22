"""Connexion YouTube, une seule fois, sur ton PC (le jeton ne passe jamais par la conversation).

1. Google Cloud Console : créer un projet, activer « YouTube Data API v3 », écran de consentement OAuth
   (type Externe, ajoute ton adresse comme testeur), puis Identifiants › ID client OAuth › « Application de bureau ».
   Télécharge le JSON du client dans data/youtube_client.json (dossier ignoré, jamais publié).
2. Lance :  python -m lbf.youtube_auth
   → le navigateur s'ouvre, tu choisis la chaîne YouTube, tu acceptes.
3. Le script écrit data/youtube_secrets.txt avec les 3 valeurs à copier dans les secrets GitHub du dépôt de
   diffusion : YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Supprime ensuite ce fichier.
"""
from __future__ import annotations

import http.server
import json
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser

from . import config

SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def main() -> None:
    cfg = json.loads((config.DATA / "youtube_client.json").read_text(encoding="utf-8"))
    c = cfg.get("installed") or cfg.get("web")
    state = secrets.token_urlsafe(16)
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                got["code"] = q["code"][0]
                msg = "Connexion YouTube reçue. Tu peux fermer cet onglet."
            else:
                msg = "Requête ignorée."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    t = threading.Thread(target=srv.handle_request)
    t.start()
    webbrowser.open(url)
    print("Navigateur ouvert : connecte la chaîne YouTube du compte, puis reviens ici.")
    t.join(timeout=600)
    if "code" not in got:
        raise SystemExit("Aucune autorisation reçue.")
    data = urllib.parse.urlencode({"code": got["code"], "client_id": c["client_id"], "client_secret": c["client_secret"],
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data)) as r:
        tok = json.loads(r.read().decode())
    out = config.DATA / "youtube_secrets.txt"
    out.write_text(f"YT_CLIENT_ID={c['client_id']}\nYT_CLIENT_SECRET={c['client_secret']}\n"
                   f"YT_REFRESH_TOKEN={tok['refresh_token']}\n", encoding="utf-8")
    print(f"Écrit : {out}\nCopie ces 3 valeurs dans les secrets GitHub du dépôt de diffusion, puis supprime le fichier.")


if __name__ == "__main__":
    main()
