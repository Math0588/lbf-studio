"""Horloge autonome : fait tourner Le Bordel Français 24 h/24 sans Claude et sans PC.

Le cron de GitHub est trop peu fiable (un seul passage en 12 h, avec 3 h de retard). Cette horloge tourne
donc en continu dans GitHub Actions, sur ce dépôt public (minutes gratuites) :
- toutes les 5 min, elle regarde l'heure de Paris ; à chaque créneau de publication (state/control.json du
  diffuseur, + une relance 30 min après), elle déclenche publish.yml du diffuseur. Le diffuseur décide seul
  (créneaux, plafond du jour) : aucun risque de doublon ;
- toutes les 30 min, elle compte la réserve (vidéos prêtes non publiées) et lance des fabrications si elle
  passe sous RESERVE_MIN, sauf si des fabrications tournent déjà ;
- après ~5 h 40 (limite GitHub : 6 h par tâche), elle se relance elle-même (workflow_dispatch) et s'arrête.
  Un seul exemplaire à la fois (groupe de concurrence « horloge ») ; la fabrication la relance aussi si elle
  ne tourne plus (filet de sécurité), et le cron GitHub aussi, quand il veut bien partir.

Secret nécessaire dans ce dépôt : DIFFUSION_TOKEN (jeton GitHub limité au dépôt du diffuseur : Actions en
lecture/écriture, Contenu en lecture). Sans lui : fabrication seulement, et la publication dépend du cron.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Paris")
REPO = os.environ.get("GITHUB_REPOSITORY", "Math0588/lbf-studio")
DIFF = os.environ.get("DIFFUSION_REPO", "Math0588/lbf-diffusion")
DIFF_TOKEN = os.environ.get("DIFFUSION_TOKEN", "").strip()
LIFETIME_S = float(os.environ.get("HORLOGE_MINUTES", "340")) * 60
TICK_S = 300
RESERVE_MIN = int(os.environ.get("RESERVE_MIN", "10"))
DEFAULT_SLOTS = ["08:00", "12:00", "17:00", "20:00", "22:00"]
SUPERSEDED = {"mcv-s01e01", "glv-s01e01"}


def log(msg: str):
    print(f"[horloge {dt.datetime.now(TZ):%d/%m %H:%M}] {msg}", flush=True)


def gh(*args, token: str | None = None, check: bool = False) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if token:
        env["GH_TOKEN"] = token
    r = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300])
    return r


def diff_file(path: str):
    """Fichier d'état du diffuseur (dépôt privé), via DIFFUSION_TOKEN."""
    if not DIFF_TOKEN:
        return None
    r = gh("api", f"repos/{DIFF}/contents/{path}", "-H", "Accept: application/vnd.github.raw", token=DIFF_TOKEN)
    if r.returncode != 0:
        log(f"lecture {path} impossible : {r.stderr.strip()[:160]}")
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def slots_today() -> list[str]:
    c = diff_file("state/control.json") or {}
    if c.get("paused"):
        return []
    today = dt.datetime.now(TZ).date().isoformat()
    burst = next((b for b in c.get("bursts", []) if b.get("date") == today), None)
    if burst:
        return [burst["at"]]
    return c.get("slots") or DEFAULT_SLOTS


def dispatch_publish() -> bool:
    if not DIFF_TOKEN:
        log("DIFFUSION_TOKEN absent : publication laissée au cron du diffuseur")
        return False
    r = gh("workflow", "run", "publish.yml", "-R", DIFF, "--ref", "main", token=DIFF_TOKEN)
    log("publication déclenchée" if r.returncode == 0 else f"échec du déclenchement : {r.stderr.strip()[:200]}")
    return r.returncode == 0


def release_assets() -> list[dict]:
    r = gh("api", f"repos/{REPO}/releases/tags/reserve")
    try:
        return json.loads(r.stdout).get("assets", []) if r.returncode == 0 else []
    except json.JSONDecodeError:
        return []


def runs_active(workflow: str) -> int:
    n = 0
    for st in ("in_progress", "queued", "pending", "waiting", "requested"):
        r = gh("run", "list", "-R", REPO, "--workflow", workflow, "--status", st, "--json", "databaseId", "-L", "50")
        try:
            n += len(json.loads(r.stdout or "[]"))
        except json.JSONDecodeError:
            pass
    return n


def reserve_left(assets: list[dict]) -> int | None:
    """Vidéos prêtes non publiées (None si l'état du diffuseur est illisible)."""
    pubs = diff_file("state/publications.json")
    if pubs is None:
        return None
    done = {p["episode_id"] for p in pubs if p.get("status") in ("published", "publication_uncertain")}
    fails = {}
    for p in pubs:
        if p.get("status") == "failed":
            fails[p["episode_id"]] = fails.get(p["episode_id"], 0) + 1
    ready = {a["name"][:-4] for a in assets if a["name"].endswith(".mp4")}
    return len([i for i in ready if i not in done and i not in SUPERSEDED and fails.get(i, 0) < 2])


def maybe_produce():
    if runs_active("produce.yml"):
        return
    assets = release_assets()
    left = reserve_left(assets)
    if left is None:   # sans l'état du diffuseur : garder ~6 vidéos fabriquées par 24 h
        lim = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        recent = len([a for a in assets if a["name"].endswith(".mp4") and a.get("created_at", "") >= lim])
        missing = max(0, 6 - recent)
    else:
        missing = max(0, RESERVE_MIN - left)
    log(f"réserve : {left if left is not None else '?'} prête(s) non publiée(s) ; à fabriquer : {missing}")
    if not missing:
        return
    batch = "h" + dt.datetime.now(TZ).strftime("%m%d%H%M")
    for k in range(min(4, math.ceil(missing / 2))):
        r = gh("workflow", "run", "produce.yml", "-R", REPO, "--ref", "main",
               "-f", f"slot={k}", "-f", f"batch={batch}", "-f", "max_videos=2")
        log(f"fabrication {batch}-{k} " + ("lancée" if r.returncode == 0 else f"refusée : {r.stderr.strip()[:160]}"))


def relaunch():
    r = gh("workflow", "run", "horloge.yml", "-R", REPO, "--ref", "main")
    log("relève lancée" if r.returncode == 0 else f"relève impossible : {r.stderr.strip()[:200]}")


def main() -> int:
    t0 = time.time()
    fired = set()        # créneaux déjà déclenchés par ce passage
    last_prod = 0.0
    slots, slots_at = DEFAULT_SLOTS, 0.0
    log(f"démarrage (jeton diffuseur : {'oui' if DIFF_TOKEN else 'non'})")
    while time.time() - t0 < LIFETIME_S:
        now = dt.datetime.now(TZ)
        if time.time() - slots_at > 3600:
            slots, slots_at = slots_today(), time.time()
        for s in slots:
            h, m = map(int, s.split(":"))
            base = now.replace(hour=h, minute=m, second=0, microsecond=0)
            for k, delay in enumerate((0, 30)):      # créneau, puis relance 30 min après (échec, retard Meta…)
                at = base + dt.timedelta(minutes=delay)
                key = (now.date(), s, k)
                if at <= now < at + dt.timedelta(minutes=12) and key not in fired:
                    fired.add(key)
                    log(f"créneau {s}" + (" (relance)" if k else ""))
                    dispatch_publish()
        if time.time() - last_prod > 1800:
            last_prod = time.time()
            try:
                maybe_produce()
            except Exception as e:      # l'horloge ne doit jamais s'arrêter sur une erreur passagère
                log(f"contrôle de la réserve impossible : {type(e).__name__} {e}")
        time.sleep(TICK_S)
    relaunch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
