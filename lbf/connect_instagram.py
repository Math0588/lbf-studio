"""Connexion Instagram en une commande :  python -m lbf.connect_instagram

Deux chemins acceptés (le script détecte lequel) :

A. Connexion Facebook (Page « LBF Productions » reliée à @lebordelfrancais) — chemin utilisé depuis le 22/11 :
   jeton utilisateur généré dans l'Explorateur de l'API Graph (app LBF Diffusion) avec instagram_basic,
   instagram_content_publish, pages_show_list, pages_read_engagement, business_management.
   Le script l'échange contre un jeton longue durée (clé secrète de l'app demandée une fois, saisie masquée),
   puis en tire le jeton de la Page, qui n'expire pas.

B. Connexion unifiée : jeton généré dans Cas d'utilisation › Instagram › API setup with Unified login.

Dans les deux cas (saisie masquée, jeton jamais affiché ni journalisé) le script vérifie le compte, le quota de
publication, enregistre IG_ACCESS_TOKEN et IG_USER_ID dans les secrets GitHub du dépôt de diffusion et règle les
variables IG_API_HOST / IG_GRAPH_VERSION."""
from __future__ import annotations

import getpass
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from . import config

APP_ID = "2280938602485007"
HOST = "https://graph.facebook.com"


def _get(path, **params):
    ver = config.get("IG_GRAPH_VERSION") or "v27.0"
    with urllib.request.urlopen(f"{HOST}/{ver}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
        return json.loads(r.read().decode())


def api(path, token, **params):
    return _get(path, access_token=token, **params)


def gh(*args, value=None):
    return subprocess.run(["gh", *args], input=value, text=True, capture_output=True)


_SECRETS: list[str] = []


def _err(e: urllib.error.HTTPError) -> str:
    """Message d'erreur Meta, sans jamais réafficher un jeton ou une clé."""
    try:
        msg = json.loads(e.read().decode()).get("error", {}).get("message", "")
    except Exception:
        return ""
    for s in _SECRETS:
        if s:
            msg = msg.replace(s, "***")
    return re.sub(r"EAA[A-Za-z0-9]{20,}", "***", msg)[:200]


def _clipboard() -> str:
    p = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                       capture_output=True, text=True)
    return p.stdout or ""


def _clear_clipboard() -> None:
    subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ' '"], capture_output=True)


def _clean(raw: str) -> str:
    raw = re.sub(r"\x1b\[20[01]~", "", raw or "")          # marqueurs de « collage encadré » du terminal
    return re.sub(r"[^A-Za-z0-9]", "", raw)


def ask_secret(what: str, pattern: str, tries: int = 5) -> str:
    """Lit un secret dans le presse-papier, ou ce qui a été collé (saisie masquée : rien ne s'affiche),
    le vérifie, puis vide le presse-papier. Plusieurs essais. Le secret n'est jamais affiché."""
    for i in range(tries):
        typed = getpass.getpass(f"Copie {what}, puis appuie sur Entrée ici (rien ne s'affiche, c'est normal) : ")
        for val in (_clean(typed), _clean(_clipboard())):
            if re.fullmatch(pattern, val):
                _clear_clipboard()
                _SECRETS.append(val)
                print(f"OK : {what} lu ({len(val)} caractères), presse-papier vidé.")
                return val
        left = tries - i - 1
        print(f"Pas trouvé {what} dans le presse-papier. Copie-le{' et réessaie' if left else ''}"
              f"{f' ({left} essai(s) restant(s))' if left else '.'}")
    return ""


def via_unified(token):
    """Chemin B. Renvoie (jeton, id, pseudo) ou None."""
    try:
        accounts = api("me/assigned_instagram_accounts", token, fields="id,username").get("data", [])
    except urllib.error.HTTPError:
        return None
    if not accounts:
        return None
    acc = next((a for a in accounts if a.get("username", "").lower() == "lebordelfrancais"), accounts[0])
    return token, str(acc["id"]), acc.get("username")


def _pages(token):
    return api("me/accounts", token, fields="name,access_token,instagram_business_account{id,username}").get("data", [])


def _expires(page_token, user_token) -> int:
    try:
        return int(api("debug_token", user_token, input_token=page_token)["data"].get("expires_at", 1))
    except Exception:
        return 1


def via_page(token):
    """Chemin A. Renvoie (jeton de Page sans expiration, id Instagram, pseudo) ou None."""
    try:
        pages = [p for p in _pages(token) if p.get("instagram_business_account")]
    except urllib.error.HTTPError as e:
        print(f"Jeton refusé (HTTP {e.code}) : {_err(e)}")
        return None
    if not pages:
        print("Aucune Page Facebook reliée à un compte Instagram pro n'est visible avec ce jeton.\n"
              "Refais « Generate Access Token » en cochant la Page LBF Productions et @lebordelfrancais.")
        return None
    page = next((p for p in pages if p["instagram_business_account"].get("username", "").lower() == "lebordelfrancais"),
                pages[0])
    if _expires(page["access_token"], token) != 0:
        print("Jeton court (1 h). Pour obtenir un jeton qui n'expire pas, il faut la clé secrète de l'app une fois :\n"
              "  developers.facebook.com › LBF Diffusion › Paramètres de l'app › Général › Clé secrète › Afficher")
        secret = ask_secret("la clé secrète de l'app", r"[0-9a-f]{32}")
        if not secret:
            print("Pas de clé : arrêt (un jeton d'une heure ne suffit pas pour publier tout seul).")
            return None
        try:
            long_user = _get("oauth/access_token", grant_type="fb_exchange_token", client_id=APP_ID,
                             client_secret=secret, fb_exchange_token=token)["access_token"]
        except urllib.error.HTTPError as e:
            print(f"Échange refusé (HTTP {e.code}) : {_err(e)}")
            return None
        page = next(p for p in _pages(long_user) if p.get("id") == page["id"])
        if _expires(page["access_token"], long_user) != 0:
            print("Attention : le jeton de Page a encore une date d'expiration.")
    ig = page["instagram_business_account"]
    print(f"Page : {page.get('name')} — jeton de Page sans expiration.")
    return page["access_token"], str(ig["id"]), ig.get("username")


def main() -> int:
    repo = config.get("CLOUD_REPO") or "Math0588/lbf-diffusion"
    print("Étape 1 : dans l'Explorateur de l'API Graph, clique sur l'icône de copie à droite du jeton.")
    token = ask_secret("le jeton", r"EAA[A-Za-z0-9]{80,}")
    if not token:
        return 1
    got = via_unified(token) or via_page(token)
    if not got:
        return 1
    tok, ig_id, username = got
    print(f"Compte connecté : @{username} (ID {ig_id})")
    try:
        lim = api(f"{ig_id}/content_publishing_limit", tok, fields="quota_usage,config")
        print("Quota de publication :", lim.get("data", lim))
    except urllib.error.HTTPError as e:
        print(f"Attention : publication peut-être non autorisée (HTTP {e.code}) : {_err(e)}")
    for name, value in (("IG_ACCESS_TOKEN", tok), ("IG_USER_ID", ig_id)):
        p = gh("secret", "set", name, "-R", repo, value=value)
        print(f"Secret {name} : {'enregistré' if p.returncode == 0 else 'ÉCHEC ' + p.stderr[:120]}")
    for name, value in (("IG_API_HOST", HOST), ("IG_GRAPH_VERSION", config.get("IG_GRAPH_VERSION") or "v27.0")):
        gh("variable", "set", name, "--body", value, "-R", repo)
    print("\nTerminé. Dis « c'est fait » à Claude pour lancer la publication de contrôle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
