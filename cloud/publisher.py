"""Diffuseur cloud — publie la réserve sur Instagram, même PC éteint.

Tourne dans GitHub Actions (cron horaire), bibliothèque standard Python uniquement.
API Instagram (graph.facebook.com, Page Facebook reliée ou connexion unifiée). Le dépôt est PRIVÉ : aucune
adresse publique. La vidéo est stockée comme fichier de la release privée « reserve » du dépôt, téléchargée
dans le runner, puis envoyée directement à Instagram (envoi « resumable » vers rupload.facebook.com).

Garanties :
- LIVE_PUBLISH != "true"  → simulation explicite, jamais de statut « published ».
- Créneaux Europe/Paris (state/control.json « slots »), pas de rafale après panne (2 h 30 minimum).
- Identifiant du conteneur persisté AVANT publication ; un timeout donne « publication_uncertain »
  puis une réconciliation (lecture des derniers médias) au lieu d'un nouvel essai aveugle.
- Le jeton n'est jamais écrit dans les journaux.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
RESERVE = ROOT / "reserve"
STATE = ROOT / "state"
TZ = ZoneInfo("Europe/Paris")
# Connexion unifiée (recommandée par Meta depuis 2026) : graph.facebook.com ; jeton « utilisateur système »
GRAPH = os.environ.get("IG_API_HOST", "").strip() or "https://graph.facebook.com"
VER = os.environ.get("IG_GRAPH_VERSION", "").strip() or "v27.0"


def env(k, d=""):
    return os.environ.get(k, d).strip()


def now():
    return dt.datetime.now(TZ)


def load(name, default):
    p = STATE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(name, data):
    STATE.mkdir(exist_ok=True)
    (STATE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log(msg):
    tok = env("IG_ACCESS_TOKEN")
    if tok:
        msg = msg.replace(tok, "***")
    print(f"[{now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status, self.body = status, body


def call(method, path, params=None, timeout=60):
    params = dict(params or {})
    params["access_token"] = env("IG_ACCESS_TOKEN")
    url = path if path.startswith("http") else f"{GRAPH}/{VER}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read().decode(errors="replace"))


def notify(kind, text):
    """Exception concrète → fichier d'alertes (visible dans le dépôt et le tableau de bord). Pas de demande
    d'approbation pour les opérations courantes."""
    alerts = load("alerts.json", [])
    alerts.append({"at": now().isoformat(), "kind": kind, "text": text})
    save("alerts.json", alerts[-200:])
    log(f"ALERTE {kind}: {text}")


# ----------------------------------------------------------------------------- jeton

def maybe_refresh_token():
    """Jeton long Instagram : 60 jours, rafraîchissable s'il a ≥ 24 h et n'a pas expiré.
    Le nouveau jeton est écrit dans le secret GitHub via `gh secret set` (PAT dédié, droit Secrets: write)."""
    if "graph.instagram.com" not in GRAPH:
        return  # connexion unifiée : jeton sans expiration (choisi dans la configuration Meta)
    meta = load("token.json", {})
    last = meta.get("refreshed_at")
    if last and (now() - dt.datetime.fromisoformat(last)).days < 7:
        return
    if env("LIVE_PUBLISH") != "true":
        return
    try:
        r = call("GET", f"{GRAPH}/refresh_access_token", {"grant_type": "ig_refresh_token"})
    except ApiError as e:
        notify("token", f"Rafraîchissement du jeton impossible ({e.status}). Reconnexion du propriétaire "
                        f"probablement nécessaire.")
        return
    new = r.get("access_token")
    if new and env("GH_SECRETS_TOKEN"):
        import subprocess
        p = subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", new],
                           env={**os.environ, "GH_TOKEN": env("GH_SECRETS_TOKEN")}, capture_output=True, text=True)
        if p.returncode != 0:
            notify("token", "Nouveau jeton obtenu mais non enregistré dans les secrets GitHub.")
            return
    elif new:
        notify("token", "Jeton rafraîchi côté Meta mais GH_SECRETS_TOKEN absent : l'ancien reste valable "
                        "jusqu'à son expiration, ajouter GH_SECRETS_TOKEN.")
    meta["refreshed_at"] = now().isoformat()
    meta["expires_in_s"] = r.get("expires_in")
    save("token.json", meta)


# ----------------------------------------------------------------------------- publication

RELEASE = "reserve"
# Vidéos fabriquées dans GitHub Actions par le dépôt studio (release publique « reserve »)
STUDIO = os.environ.get("STUDIO_REPO", "").strip() or "Math0588/lbf-studio"
STUDIO_DL = f"https://github.com/{STUDIO}/releases/download/reserve"


def _get(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lbf-diffusion"}),
                                timeout=timeout) as r:
        return r.read()


def studio_index() -> list:
    """File d'attente du studio (ordre de fabrication). Vide si le studio n'est pas encore public."""
    try:
        return json.loads(_get(f"{STUDIO_DL}/index.json")).get("items", [])
    except Exception as e:
        log(f"Studio indisponible ({type(e).__name__}) : réserve locale seulement")
        return []


def studio_meta(ep_id) -> dict:
    return json.loads(_get(f"{STUDIO_DL}/{ep_id}.json"))


def public_url(name: str) -> str:
    """URL directe (fichier public de la release studio), redirection résolue pour Meta."""
    req = urllib.request.Request(f"{STUDIO_DL}/{name}", method="HEAD", headers={"User-Agent": "lbf-diffusion"})
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            return e.headers["Location"]
        raise
    return f"{STUDIO_DL}/{name}"


def gh(*args):
    import subprocess
    return subprocess.run(["gh", *args], capture_output=True, text=True,
                          env={**os.environ, "GH_TOKEN": env("GH_TOKEN") or env("GITHUB_TOKEN")})


def release_assets() -> set:
    """Noms des vidéos disponibles dans la release privée (vide si gh indisponible : on se fie au disque)."""
    try:
        p = gh("release", "view", RELEASE, "--json", "assets")
    except FileNotFoundError:
        return set()
    if p.returncode != 0:
        return set()
    return {a["name"] for a in json.loads(p.stdout or "{}").get("assets", [])}


def has_video(ep_id, assets) -> bool:
    return (RESERVE / ep_id / "video.mp4").exists() or f"{ep_id}.mp4" in assets


def ensure_local(ep_id) -> Path:
    """Télécharge la vidéo de la release privée dans reserve/<id>/video.mp4 (jamais versionnée)."""
    dst = RESERVE / ep_id / "video.mp4"
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    p = gh("release", "download", RELEASE, "-p", f"{ep_id}.mp4", "-D", str(dst.parent), "--clobber")
    if p.returncode != 0:
        raise RuntimeError(f"vidéo introuvable dans la release privée ({p.stderr.strip()[:150]})")
    (dst.parent / f"{ep_id}.mp4").rename(dst)
    return dst


def upload_video(uri: str, path: Path) -> dict:
    """Envoi direct du fichier à Instagram (protocole resumable, en une fois)."""
    data = path.read_bytes()
    req = urllib.request.Request(uri, data=data, method="POST", headers={
        "Authorization": f"OAuth {env('IG_ACCESS_TOKEN')}", "offset": "0", "file_size": str(len(data))})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read().decode(errors="replace"))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def signed_asset_url(name: str) -> str:
    """Lien de téléchargement signé (quelques minutes) d'un fichier de la release privée. Le lien ne contient ni
    le nom du dépôt ni celui du propriétaire ; seul Meta le voit, le temps de récupérer la vidéo."""
    repo = env("GITHUB_REPOSITORY")
    p = gh("api", f"repos/{repo}/releases/tags/{RELEASE}", "--jq",
           f'.assets[] | select(.name=="{name}") | .url')
    api_url = (p.stdout or "").strip()
    if not api_url:
        raise RuntimeError(f"{name} absent de la release privée")
    req = urllib.request.Request(api_url, headers={
        "Authorization": f"Bearer {env('GH_TOKEN') or env('GITHUB_TOKEN')}", "Accept": "application/octet-stream"})
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            return e.headers["Location"]
        raise
    raise RuntimeError("pas de lien signé renvoyé par GitHub")


def wait_container(cid: str, minutes: int = 15) -> dict:
    deadline = time.time() + minutes * 60
    s = {}
    while time.time() < deadline:
        s = call("GET", cid, {"fields": "status_code,status"})
        if s.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
            return s
        time.sleep(20)
    return s


def create_container(ep_id: str, params: dict, studio: bool = False) -> tuple[str, str]:
    """Crée le conteneur Reels et y met la vidéo. Méthode « url » (lien signé, défaut) ou « resumable »
    (envoi direct). Renvoie (id du conteneur, méthode utilisée)."""
    user_id = env("IG_USER_ID")
    method = env("IG_UPLOAD_METHOD") or "url"
    if studio:
        c = call("POST", f"{user_id}/media", {**params, "media_type": "REELS", "video_url": public_url(f"{ep_id}.mp4")})
        return c["id"], "url_studio"
    if method == "resumable":
        video = ensure_local(ep_id)
        c = call("POST", f"{user_id}/media", {**params, "media_type": "REELS", "upload_type": "resumable"})
        uri = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{VER}/{c['id']}"
        try:
            upload_video(uri, video)
            return c["id"], "resumable"
        except ApiError as e:
            log(f"Envoi direct refusé ({e.status}) : bascule sur le lien signé")
    c = call("POST", f"{user_id}/media", {**params, "media_type": "REELS", "video_url": signed_asset_url(f"{ep_id}.mp4")})
    return c["id"], "url"


def next_episode(queue, pubs, assets=frozenset(), studio=None):
    done = {p["episode_id"] for p in pubs if p["status"] in ("published", "publication_uncertain", "failed")
            and not p.get("retry")}
    # 1) vidéos du studio cloud, dans l'ordre de fabrication (elles remplacent les anciennes versions locales)
    for it in studio or []:
        if it["id"] not in done:
            return {"episode_id": it["id"], "source": "studio", "title": it.get("title")}
    studio_ids = {it["id"] for it in studio or []}
    queue = [q for q in queue if q["episode_id"] not in studio_ids and q["episode_id"] not in SUPERSEDED]
    fresh = []
    for item in queue:
        exp = item.get("expires")
        if exp and dt.datetime.fromisoformat(exp).replace(tzinfo=TZ) < now():
            continue  # actualité périmée : jamais publiée en retard
        fresh.append(item)
    queue = sorted(fresh, key=lambda i: 0 if i.get("urgent") else 1)
    for item in queue:
        if item["episode_id"] not in done and has_video(item["episode_id"], assets):
            return item
    return None


SUPERSEDED = {"mcv-s01e01", "glv-s01e01"}   # anciennes histoires : remplacées par les versions réécrites du studio


def reconcile(pub, user_id):
    """Après un timeout : chercher le média dans les derniers posts avant tout nouvel essai."""
    marker = pub["caption_head"]
    r = call("GET", f"{user_id}/media", {"fields": "id,caption,permalink,timestamp", "limit": 10})
    for m in r.get("data", []):
        if (m.get("caption") or "").startswith(marker):
            pub.update(status="published", media_id=m["id"], permalink=m.get("permalink"),
                       published_at=m.get("timestamp"), reconciled=True)
            return True
    return False


def publish_one(item, pubs):
    user_id = env("IG_USER_ID")
    ep_id = item["episode_id"]
    folder = RESERVE / ep_id
    from_studio = item.get("source") == "studio"
    if from_studio:
        meta = studio_meta(ep_id)
        caption, manifest = meta["caption"], meta.get("manifest", {})
    else:
        caption = (folder / "caption.txt").read_text(encoding="utf-8")
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    thumb = int(manifest.get("thumb_offset_ms", 300))
    pub = {"episode_id": ep_id, "status": "publishing", "attempt_at": now().isoformat(),
           "video_sha256": manifest.get("video_sha256"), "caption_head": caption[:60]}

    if env("LIVE_PUBLISH") != "true":
        pub.update(status="simulated", note="LIVE_PUBLISH=false : aucune requête envoyée à Instagram",
                   source="studio" if from_studio else "local",
                   would_post={"upload": "resumable", "video": f"release {RELEASE}/{ep_id}.mp4",
                               "thumb_offset_ms": thumb, "caption_chars": len(caption)})
        pubs.append(pub)
        log(f"SIMULATION {ep_id} → envoi direct (release privée {RELEASE}/{ep_id}.mp4)")
        return pub

    lim = call("GET", f"{user_id}/content_publishing_limit", {"fields": "quota_usage,config"})
    log(f"Quota : {lim}")
    pubs.append(pub)
    save("publications.json", pubs)
    params = {"caption": caption, "thumb_offset": thumb, "share_to_feed": "true"}
    if from_studio:  # couverture avec le titre de la vidéo (grille du profil et fil)
        try:
            params["cover_url"] = public_url(f"{ep_id}.jpg")
        except Exception as e:
            log(f"Couverture indisponible ({e}) : image extraite de la vidéo")
    cid, how = create_container(ep_id, params, studio=from_studio)
    c = {"id": cid}
    pub.update(container_id=cid, upload=how)
    save("publications.json", pubs)
    deadline = time.time() + 15 * 60
    status = ""
    while time.time() < deadline:
        s = call("GET", c["id"], {"fields": "status_code,status"})
        status = s.get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            pub.update(status="failed", error=s.get("status"))
            notify("publication", f"{ep_id} : conteneur {status} ({s.get('status')})")
            return pub
        time.sleep(20)
    if status != "FINISHED":
        pub.update(status="failed", error="traitement Meta trop long (15 min)")
        notify("publication", f"{ep_id} : traitement non terminé, réessai au prochain créneau")
        pub["retry"] = True
        return pub
    try:
        r = call("POST", f"{user_id}/media_publish", {"creation_id": c["id"]}, timeout=90)
        pub.update(status="published", media_id=r["id"], published_at=now().isoformat())
        try:
            m = call("GET", r["id"], {"fields": "permalink"})
            pub["permalink"] = m.get("permalink")
        except ApiError:
            pass
    except (urllib.error.URLError, TimeoutError, ApiError) as e:
        pub.update(status="publication_uncertain", error=str(e)[:300])
        save("publications.json", pubs)
        time.sleep(30)
        if not reconcile(pub, user_id):
            notify("publication", f"{ep_id} : publication incertaine, aucune republication automatique.")
    return pub


def publish_youtube(item):
    """Module optionnel YouTube Shorts : jamais bloquant pour Instagram, jamais deux fois le même épisode."""
    sys.path.insert(0, str(Path(__file__).parent))
    import youtube
    if not youtube.enabled() or item.get("source") == "studio":
        return
    yts = load("youtube.json", [])
    if any(y["episode_id"] == item["episode_id"] and y.get("video_id") for y in yts):
        return
    folder = RESERVE / item["episode_id"]
    caption = (folder / "caption.txt").read_text(encoding="utf-8")
    seo = json.loads((folder / "seo.json").read_text(encoding="utf-8")) if (folder / "seo.json").exists() else {}
    title = seo.get("yt_title") or caption.splitlines()[0][:90]
    desc = seo.get("yt_description") or caption
    tags = seo.get("yt_tags") or ["humour politique", "politique française", "parodie"]
    try:
        r = youtube.upload(ensure_local(item["episode_id"]), title, desc, tags)
        yts.append({"episode_id": item["episode_id"], "at": now().isoformat(), **r})
        log(f"YouTube : {r.get('url')} ({r.get('privacy')})")
    except Exception as e:
        yts.append({"episode_id": item["episode_id"], "at": now().isoformat(), "error": str(e)[:300]})
        notify("youtube", f"{item['episode_id']} : envoi YouTube échoué ({str(e)[:120]})")
    save("youtube.json", yts)


def collect_metrics(pubs):
    """Mesures à 24 h, 72 h, 7 j — uniquement ce que l'API expose ; une donnée absente reste absente."""
    if env("LIVE_PUBLISH") != "true":
        return
    snaps = load("metrics.json", [])
    have = {(s["media_id"], s["window"]) for s in snaps}
    metrics = "reach,views,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time"
    for p in pubs:
        if p.get("status") != "published" or not p.get("published_at"):
            continue
        age_h = (now() - dt.datetime.fromisoformat(p["published_at"].replace("Z", "+00:00"))).total_seconds() / 3600
        for win, h in (("24h", 24), ("72h", 72), ("7j", 168)):
            if age_h >= h and (p["media_id"], win) not in have:
                try:
                    r = call("GET", f"{p['media_id']}/insights", {"metric": metrics})
                    vals = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in r.get("data", [])}
                    snaps.append({"media_id": p["media_id"], "episode_id": p["episode_id"], "window": win,
                                  "at": now().isoformat(), "values": vals})
                except ApiError as e:
                    snaps.append({"media_id": p["media_id"], "episode_id": p["episode_id"], "window": win,
                                  "at": now().isoformat(), "error": e.body[:200]})
    save("metrics.json", snaps)


def cleanup(pubs, assets=frozenset()):
    """Supprime de la réserve (dossier + vidéo de la release privée) les épisodes publiés depuis > 3 jours."""
    import shutil
    for p in pubs:
        if p.get("status") == "published" and p.get("published_at"):
            age = now() - dt.datetime.fromisoformat(p["published_at"].replace("Z", "+00:00"))
            if age.days < 3:
                continue
            d = RESERVE / p["episode_id"]
            if d.exists():
                shutil.rmtree(d)
                log(f"Réserve nettoyée : {p['episode_id']}")
            if f"{p['episode_id']}.mp4" in assets:
                gh("release", "delete-asset", RELEASE, f"{p['episode_id']}.mp4", "-y")


def check_upload():
    """Vérification sans publication : pour chaque méthode d'envoi, conteneur + vidéo + traitement Meta, puis arrêt
    AVANT media_publish. Les conteneurs non publiés expirent seuls sous 24 h ; rien n'apparaît sur le compte."""
    queue = json.loads((RESERVE / "queue.json").read_text(encoding="utf-8")) if (RESERVE / "queue.json").exists() else []
    item = next_episode(queue, load("publications.json", []), release_assets(), studio_index())
    if not item:
        log("CHECK : aucune vidéo dans la réserve")
        return 1
    ep_id, ok = item["episode_id"], []
    for method in ("url", "resumable"):
        os.environ["IG_UPLOAD_METHOD"] = method
        try:
            cid, how = create_container(ep_id, {"caption": "vérification technique", "share_to_feed": "false"},
                                        studio=item.get("source") == "studio")
            st = wait_container(cid, 12)
            log(f"CHECK {method} : méthode effective {how}, statut {st.get('status_code')} ({st.get('status')})")
            if st.get("status_code") == "FINISHED" and how == method:
                ok.append(method)
        except Exception as e:
            log(f"CHECK {method} : échec {type(e).__name__} {str(e)[:200]}")
    log(f"CHECK : méthodes qui fonctionnent : {ok or 'aucune'} — rien n'a été publié")
    return 0 if ok else 1


def main():
    if "--check" in sys.argv:
        return check_upload()
    control = load("control.json", {"paused": False, "slot": "18:30"})
    pubs = load("publications.json", [])
    queue = json.loads((RESERVE / "queue.json").read_text(encoding="utf-8")) if (RESERVE / "queue.json").exists() else []
    missing = [k for k in ("IG_ACCESS_TOKEN", "IG_USER_ID") if not env(k)]
    if env("LIVE_PUBLISH") == "true" and missing:
        notify("configuration", f"Configuration requise : secrets manquants {missing}")
        return 0
    if control.get("paused"):
        log("Pause générale active : aucune requête, aucune publication.")
        return 0
    maybe_refresh_token()
    collect_metrics(pubs)
    assets = release_assets()
    cleanup(pubs, assets)
    today = now().date().isoformat()
    slots = control.get("slots") or [x.strip() for x in env("PUBLISH_SLOTS", "08:30,12:30,19:00,22:00").split(",") if x.strip()]
    counted = ("published", "publishing", "publication_uncertain") + \
        (() if env("LIVE_PUBLISH") == "true" else ("simulated",))   # un essai à blanc n'occupe pas un vrai créneau
    done_today = [p for p in pubs if p.get("attempt_at", "")[:10] == today and p["status"] in counted]
    passed = [s for s in slots if (now().hour, now().minute) >= tuple(map(int, s.split(":")))]
    if "--force" not in sys.argv:
        if len(done_today) >= len(passed):
            log(f"Rien à publier maintenant (créneaux {', '.join(slots)} Europe/Paris ; {len(done_today)} fait(s)).")
            return 0
        if done_today:
            last = max(dt.datetime.fromisoformat(p["attempt_at"]) for p in done_today)
            if (now() - last).total_seconds() < 2.5 * 3600:
                log("Moins de 3 h depuis la dernière publication : pas de rafale après une panne.")
                return 0
    studio = studio_index()
    item = next_episode(queue, pubs, assets, studio)
    if not item:
        notify("reserve", "Réserve vide : aucune vidéo prête (la fabrication cloud tourne 5 fois par jour).")
        save("publications.json", pubs)
        return 0
    done_ids = {p["episode_id"] for p in pubs if p["status"] == "published"}
    remaining = len([i for i in studio if i["id"] not in done_ids]) - 1 if studio else \
        len([q for q in queue if has_video(q["episode_id"], assets)]) - 1
    if remaining < 3:
        notify("reserve", f"Réserve basse : {remaining} vidéo(s) après celle-ci.")
    pub = publish_one(item, pubs)
    save("publications.json", pubs)
    publish_youtube(item)
    log(f"Résultat {pub['episode_id']} : {pub['status']} {pub.get('permalink', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
