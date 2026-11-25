"""Worker autonome (un seul au départ) : fabrique la réserve et l'envoie au diffuseur cloud.

Boucle : veille quotidienne → choix du prochain script (banque validée, puis génération locale) → planification
→ production (voix, 3D, montage, QA) → export vers le dépôt de diffusion (GitHub) → synchronisation des statuts
publiés (preuve : identifiant + lien) → continuité de la série mise à jour UNIQUEMENT après publication réussie.

Robustesse : verrou de processus, verrous par épisode avec expiration (reprise après redémarrage), tentatives
limitées, contrôle d'espace disque, pause générale, aucune action payante, journal d'audit.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

from . import config, db, editorial, gagmatrix, planner_v2 as planner, produce, trends, veille, writer

OWNER = f"{socket.gethostname()}:{os.getpid()}"
LOCK = config.DATA / "worker.lock"
CITY_ORDER = ["bardellaville", "macronville", "melenchonville", "zemmourville", "marineville", "glucksmannville",
              "durifville", "rinerville"]
MAX_ATTEMPTS = 2


def log(msg: str) -> None:
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    config.DATA.mkdir(exist_ok=True)
    with open(config.DATA / "worker.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ----------------------------------------------------------------------------- verrou de processus

def acquire_process_lock() -> bool:
    if LOCK.exists():
        try:
            info = json.loads(LOCK.read_text(encoding="utf-8"))
            beat = dt.datetime.fromisoformat(info["heartbeat"])
            if (dt.datetime.now() - beat).total_seconds() < 600:
                return False  # un autre worker est vivant
        except Exception:
            pass
    heartbeat()
    return True


def heartbeat(state: str = "actif") -> None:
    config.DATA.mkdir(exist_ok=True)
    LOCK.write_text(json.dumps({"owner": OWNER, "heartbeat": dt.datetime.now().isoformat(timespec="seconds"),
                                "state": state}), encoding="utf-8")


# ----------------------------------------------------------------------------- santé

def disk_free_gb() -> float:
    return shutil.disk_usage(config.ROOT).free / 1e9


def health(con) -> dict:
    free = disk_free_gb()
    return {"disk_free_gb": round(free, 1), "disk_ok": free >= float(config.get("MIN_FREE_DISK_GB") or 15),
            "paused": (db.get_conf(con, "PAUSED") or config.get("PAUSED")) == "true",
            "free_mode": config.flag("FREE_MODE"), "live_publish": config.flag("LIVE_PUBLISH")}


# ----------------------------------------------------------------------------- choix du prochain épisode

def bank_scripts() -> list[Path]:
    """Scripts validés : pilotes puis banque, villes alternées (rendez-vous variés, pas 5 fois la même ville)."""
    per_city = {c: [] for c in CITY_ORDER}
    for p in sorted((config.CONTENT / "scripts").glob("*_pilot_*.json")):
        c = p.name.split("_pilot_")[0]
        per_city.setdefault(c, []).append(p)
    for c in CITY_ORDER:
        # banque « ultra » (scénarios les plus provocants) en tête, puis la banque de série
        bank = sorted((config.CONTENT / "scripts" / "bank_auto" / c).glob("*.json")) + \
            sorted((config.CONTENT / "scripts" / "bank_ultra" / c).glob("*.json")) + \
            sorted((config.CONTENT / "scripts" / "bank" / c).glob("*.json"))
        memes = sorted((config.CONTENT / "scripts" / "bank_memes" / c).glob("*.json"))
        mixed = []  # alterne scripts de série et scripts ancrés sur un mème réel
        for i in range(max(len(bank), len(memes))):
            mixed += ([memes[i]] if i < len(memes) else []) + ([bank[i]] if i < len(bank) else [])
        per_city[c] += mixed
    order, i = [], 0
    while any(per_city.values()):
        c = CITY_ORDER[i % len(CITY_ORDER)]
        if per_city.get(c):
            order.append(per_city[c].pop(0))
        i += 1
    return order


def from_gag_factory(con) -> int:
    """Un épisode neuf tiré de l'usine à gags (mème réel × situation × ressort) ; 0 si échec des contrôles."""
    n_total = con.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    city = CITY_ORDER[n_total % len(CITY_ORDER)]
    cand = gagmatrix.next_candidate(city)
    if not cand:
        return 0
    syn = gagmatrix.to_synopsis(city, cand)
    num = con.execute("SELECT COALESCE(MAX(episode_number),0)+1 FROM episodes WHERE city_id=?", (city,)).fetchone()[0]
    ep_id = f"{city[:3]}-gm{num:03d}"
    gagmatrix.mark_used(city, cand)  # même en cas d'échec : on ne réessaie pas la même combinaison
    try:
        script = writer.write_episode(city, syn, ep_id)
    except Exception as e:
        db.audit(con, "gag_factory_failed", ep_id, {"error": str(e)[:200], "anchor": syn["anchor"][:120]})
        return 0
    gen = config.CONTENT / "scripts" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    sp = gen / f"{ep_id}.json"
    sp.write_text(json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")
    ep_path = planner.plan_file(sp)
    con.execute("INSERT INTO episodes(id,city_id,season,episode_number,title,state,path,synopsis_id,created,updated) "
                "VALUES(?,?,1,?,?,'scripted',?,?,?,?)", (ep_id, city, num, script["title_cover"], str(ep_path),
                                                         syn["id"], db.now(), db.now()))
    db.audit(con, "gag_factory", ep_id, {"anchor": syn["anchor"][:200], "situation": cand["situation"],
                                         "ressort": cand["ressort"]})
    return 1


def ensure_backlog(con, target: int) -> int:
    """S'assure qu'au moins `target` épisodes sont planifiés (scripted) ou en cours. Retourne le nombre ajouté.
    Une vidéo sur deux vient de l'usine à gags (mèmes récents), l'autre de la banque relue."""
    active = con.execute("SELECT COUNT(*) FROM episodes WHERE state IN ('scripted','checked','render_queued',"
                         "'rendering','rendered','retry_wait')").fetchone()[0]
    added = 0
    known = {r["id"] for r in con.execute("SELECT id FROM episodes")}
    for p in bank_scripts():
        if active + added >= target:
            break
        s = json.loads(p.read_text(encoding="utf-8"))
        if s["id"] in known:
            continue
        ep_path = planner.plan_file(p)
        e = json.loads(ep_path.read_text(encoding="utf-8"))
        con.execute("INSERT INTO episodes(id,city_id,season,episode_number,title,state,path,synopsis_id,created,"
                    "updated) VALUES(?,?,?,?,?,'scripted',?,?,?,?)",
                    (e["id"], e["city_id"], e.get("season", 1), e.get("episode_number"), e.get("title_cover"),
                     str(ep_path), e.get("synopsis_id"), db.now(), db.now()))
        db.audit(con, "planned_from_bank", e["id"], {"script": p.name, "warnings": e.get("planner_warnings")})
        added += 1
    # banque épuisée : usine à gags (mèmes réels, Qwen3-14B local), puis synopsis restants
    while active + added < target and from_gag_factory(con):
        added += 1
    if active + added < target:
        added += generate_locally(con, target - active - added)
    return added


def generate_locally(con, n: int) -> int:
    """Banque épuisée : écriture par le modèle local à partir des synopsis non utilisés."""
    used = {r["synopsis_id"] for r in con.execute("SELECT synopsis_id FROM episodes WHERE synopsis_id IS NOT NULL")}
    made = 0
    for city in CITY_ORDER:
        if made >= n:
            break
        syn = writer.next_synopsis(city, used)
        if not syn:
            continue
        num = con.execute("SELECT COALESCE(MAX(episode_number),0)+1 FROM episodes WHERE city_id=?", (city,)).fetchone()[0]
        ep_id = f"{syn['id'].split('-')[0]}-s01e{num:02d}"
        try:
            script = writer.write_episode(city, syn, ep_id)
        except Exception as e:
            db.audit(con, "local_generation_failed", ep_id, {"error": str(e)[:300]})
            used.add(syn["id"])
            continue
        gen_dir = config.CONTENT / "scripts" / "generated"
        gen_dir.mkdir(parents=True, exist_ok=True)
        sp = gen_dir / f"{ep_id}.json"
        sp.write_text(json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")
        ep_path = planner.plan_file(sp)
        con.execute("INSERT INTO episodes(id,city_id,season,episode_number,title,state,path,synopsis_id,created,"
                    "updated) VALUES(?,?,1,?,?,'scripted',?,?,?,?)",
                    (ep_id, city, num, script["title_cover"], str(ep_path), syn["id"], db.now(), db.now()))
        db.audit(con, "generated_locally", ep_id, script.get("generation_log"))
        used.add(syn["id"])
        made += 1
    return made


def react_to_trends(con) -> list:
    """Sujet politique chaud → épisode d'actualité en tête de file (priorité 10, péremption 48 h)."""
    made = []
    last = db.get_conf(con, "last_topical", "")
    if last and (dt.datetime.now() - dt.datetime.fromisoformat(last)).total_seconds() < 6 * 3600:
        return made  # au plus un épisode d'actualité toutes les 6 h
    for tr in trends.hot_topics()[:1]:
        city = tr["city"]
        if city not in CITY_ORDER:
            continue
        num = con.execute("SELECT COALESCE(MAX(episode_number),0)+1 FROM episodes WHERE city_id=?", (city,)).fetchone()[0]
        ep_id = f"{city[:3]}-act{dt.datetime.now():%m%d%H}"
        try:
            script = writer.write_topical(city, tr, ep_id)
        except Exception as e:
            db.audit(con, "topical_failed", ep_id, {"error": str(e)[:200], "trend": tr["item"].get("title")})
            trends.mark_used(tr["item"]["id"])
            continue
        gen = config.CONTENT / "scripts" / "generated"
        gen.mkdir(parents=True, exist_ok=True)
        sp = gen / f"{ep_id}.json"
        sp.write_text(json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")
        ep_path = planner.plan_file(sp)
        e = json.loads(ep_path.read_text(encoding="utf-8"))
        e["topical"] = True
        e["expires_at"] = (dt.datetime.now() + dt.timedelta(hours=48)).isoformat(timespec="seconds")
        e["sources"] = script["sources"]
        ep_path.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
        con.execute("INSERT INTO episodes(id,city_id,season,episode_number,title,state,path,priority,created,updated) "
                    "VALUES(?,?,1,?,?,'scripted',?,10,?,?)", (ep_id, city, num, script["title_cover"], str(ep_path),
                                                             db.now(), db.now()))
        db.audit(con, "topical_planned", ep_id, {"trend": tr["item"].get("title"), "ratio": tr["ratio"]})
        trends.mark_used(tr["item"]["id"])
        db.set_conf(con, "last_topical", db.now(), "worker")
        made.append(ep_id)
    if made:
        check_scripted(con)
    return made


# ----------------------------------------------------------------------------- étapes

def check_scripted(con) -> None:
    for r in con.execute("SELECT id, path FROM episodes WHERE state='scripted'").fetchall():
        e = json.loads(Path(r["path"]).read_text(encoding="utf-8"))
        ed = editorial.check(e)
        if ed["decision"] == "pass":
            db.set_state(con, r["id"], "render_queued")
        elif ed["decision"] == "needs_review":
            db.set_state(con, r["id"], "needs_review", "; ".join(ed["review"])[:500])
        else:
            db.set_state(con, r["id"], "rejected", "; ".join(ed["blocking"])[:500])


def produce_one(con) -> str | None:
    ep_id = db.claim_episode(con, OWNER, ("render_queued", "rendering", "retry_wait"))
    if not ep_id:
        return None
    row = con.execute("SELECT * FROM episodes WHERE id=?", (ep_id,)).fetchone()
    db.set_state(con, ep_id, "rendering")
    con.execute("UPDATE episodes SET attempts=attempts+1 WHERE id=?", (ep_id,))
    log(f"Production de {ep_id} (essai {row['attempts'] + 1})")
    try:
        rep = produce.produce(Path(row["path"]), "final", log=log)
        r = rep.get("render", {})
        con.execute("INSERT INTO renders(episode_id,profile,frames,render_s,wall_s,engine,blender,path,created) "
                    "VALUES(?,?,?,?,?,?,?,?,?)", (ep_id, "final", r.get("frames"), r.get("render_s"), r.get("wall_s"),
                                                  r.get("engine"), r.get("blender"), str(config.OUTPUT / "episodes" / ep_id),
                                                  db.now()))
        q = rep.get("qa", {})
        con.execute("INSERT INTO qa_results(episode_id,passed,report,created) VALUES(?,?,?,?)",
                    (ep_id, int(bool(q.get("passed"))), json.dumps(q, ensure_ascii=False), db.now()))
        cleanup_frames(ep_id)
        if rep.get("status") == "qa_passed":
            db.set_state(con, ep_id, "qa_passed")
        elif rep.get("status") == "needs_review":
            db.set_state(con, ep_id, "needs_review", "contrôle éditorial à relire")
        else:
            fails = [c["check"] for c in q.get("checks", []) if not c["ok"]]
            if row["attempts"] + 1 < MAX_ATTEMPTS:
                db.set_state(con, ep_id, "retry_wait", "QA : " + ", ".join(fails))
            else:
                db.set_state(con, ep_id, "failed", "QA : " + ", ".join(fails))
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        log(err + "\n" + traceback.format_exc()[-1500:])
        db.set_state(con, ep_id, "retry_wait" if row["attempts"] + 1 < MAX_ATTEMPTS else "failed", err[:500])
    finally:
        db.release(con, ep_id)
    return ep_id


def cleanup_frames(ep_id: str) -> None:
    """Les PNG intermédiaires (~2 Go/épisode) sont supprimés une fois la vidéo encodée ; le .blend est gardé."""
    for d in (config.OUTPUT / "episodes" / ep_id).glob("render_*/frames"):
        shutil.rmtree(d, ignore_errors=True)


# ----------------------------------------------------------------------------- diffusion

def cloud_repo() -> Path | None:
    p = config.get("CLOUD_REPO_DIR")
    return Path(p) if p and (Path(p) / ".git").exists() else None


def git(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")


def upload_reserve_video(video: Path, ep_id: str):
    """Envoie la vidéo dans la release privée « reserve » du dépôt de diffusion (créée au besoin)."""
    import tempfile
    repo_name = config.get("CLOUD_REPO") or "Math0588/lbf-diffusion"
    if subprocess.run(["gh", "release", "view", "reserve", "-R", repo_name], capture_output=True).returncode != 0:
        subprocess.run(["gh", "release", "create", "reserve", "-R", repo_name, "--title", "Réserve",
                        "--notes", "Vidéos en attente de publication (dépôt privé)."], capture_output=True)
    with tempfile.TemporaryDirectory() as tmp:
        named = Path(tmp) / f"{ep_id}.mp4"
        shutil.copy(video, named)
        return subprocess.run(["gh", "release", "upload", "reserve", str(named), "--clobber", "-R", repo_name],
                              capture_output=True, text=True)


def export_reserve(con) -> dict:
    """Copie les épisodes prêts dans le dépôt de diffusion (reserve/<id>/) et met à jour queue.json."""
    repo = cloud_repo()
    ready = con.execute("SELECT id FROM episodes WHERE state='qa_passed' ORDER BY updated").fetchall()
    if not repo:
        return {"status": "configuration_requise", "ready": len(ready),
                "detail": "CLOUD_REPO_DIR non configuré (voir docs/DIFFUSION_CLOUD.md)"}
    git(repo, "pull", "--rebase", "--autostash")
    res = repo / "reserve"
    res.mkdir(exist_ok=True)
    qpath = res / "queue.json"
    queue = json.loads(qpath.read_text(encoding="utf-8")) if qpath.exists() else []
    inq = {q["episode_id"] for q in queue}
    exported = []
    for r in ready:
        src = config.OUTPUT / "episodes" / r["id"] / "publication"
        if not (src / "video.mp4").exists():
            continue
        dst = res / r["id"]
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("video.mp4"))
        up = upload_reserve_video(src / "video.mp4", r["id"])
        if up.returncode != 0:
            shutil.rmtree(dst)
            log(f"Export {r['id']} : envoi de la vidéo dans la release privée impossible ({up.stderr[-200:]})")
            continue
        e = json.loads(Path(con.execute("SELECT path FROM episodes WHERE id=?", (r["id"],)).fetchone()["path"])
                       .read_text(encoding="utf-8"))
        if r["id"] not in inq:
            entry = {"episode_id": r["id"], "added": db.now()}
            if e.get("topical"):
                entry.update(urgent=True, expires=e.get("expires_at"))
            queue.append(entry)
        man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
        con.execute("INSERT INTO publish_jobs(episode_id,status,exported_at,video_sha256) VALUES(?,?,?,?) "
                    "ON CONFLICT(episode_id) DO UPDATE SET status='exported', exported_at=excluded.exported_at",
                    (r["id"], "exported", db.now(), man.get("video_sha256")))
        db.set_state(con, r["id"], "scheduled")
        exported.append(r["id"])
    qpath.write_text(json.dumps(queue, ensure_ascii=False, indent=1), encoding="utf-8")
    gi = repo / ".gitignore"
    if "reserve/*/video.mp4" not in (gi.read_text(encoding="utf-8") if gi.exists() else ""):
        with gi.open("a", encoding="utf-8") as f:
            f.write("reserve/*/video.mp4\n")
    if exported:
        git(repo, "add", "reserve", ".gitignore")
        git(repo, "commit", "-m", f"réserve : +{len(exported)} épisode(s)")
        p = git(repo, "push")
        if p.returncode != 0:
            return {"status": "echec_push", "detail": p.stderr[-300:], "exported": exported}
    return {"status": "ok", "exported": exported, "queue": len(queue)}


def sync_publications(con) -> dict:
    """Lit state/publications.json du diffuseur ; seul un statut « published » avec identifiant fait foi."""
    repo = cloud_repo()
    if not repo:
        return {"status": "configuration_requise"}
    git(repo, "pull", "--rebase", "--autostash")
    pubs_p = repo / "state" / "publications.json"
    pubs = json.loads(pubs_p.read_text(encoding="utf-8")) if pubs_p.exists() else []
    n = 0
    for p in pubs:
        ep = p["episode_id"]
        st = p.get("status")
        con.execute("INSERT INTO publications(episode_id,platform,media_id,permalink,published_at,status,raw) "
                    "VALUES(?,?,?,?,?,?,?) ON CONFLICT(episode_id) DO UPDATE SET media_id=excluded.media_id, "
                    "permalink=excluded.permalink, published_at=excluded.published_at, status=excluded.status, "
                    "raw=excluded.raw", (ep, "instagram", p.get("media_id"), p.get("permalink"), p.get("published_at"),
                                         st, json.dumps(p, ensure_ascii=False)))
        cur = con.execute("SELECT state FROM episodes WHERE id=?", (ep,)).fetchone()
        if not cur:
            continue
        if st == "published" and p.get("media_id") and cur["state"] != "published":
            db.set_state(con, ep, "published")
            mark_continuity_shown(con, ep)
            n += 1
        elif st == "publication_uncertain" and cur["state"] != "publication_uncertain":
            db.set_state(con, ep, "publication_uncertain", p.get("error"))
        elif st == "failed" and cur["state"] == "scheduled":
            db.set_state(con, ep, "failed", p.get("error"))
    mpath = repo / "state" / "metrics.json"
    if mpath.exists():
        for m in json.loads(mpath.read_text(encoding="utf-8")):
            con.execute("INSERT OR IGNORE INTO metric_snapshots(episode_id,media_id,window,taken_at,data) "
                        "VALUES(?,?,?,?,?)", (m["episode_id"], m["media_id"], m["window"], m["at"],
                                              json.dumps(m.get("values") or {"error": m.get("error")})))
    return {"status": "ok", "newly_published": n}


def mark_continuity_shown(con, ep_id: str) -> None:
    """La publication réussie valide l'évolution officielle de la série (jamais un épisode rejeté)."""
    row = con.execute("SELECT path, city_id FROM episodes WHERE id=?", (ep_id,)).fetchone()
    e = json.loads(Path(row["path"]).read_text(encoding="utf-8"))
    for i, desc in enumerate(e.get("continuity_after", [])):
        con.execute("INSERT OR REPLACE INTO continuity_events(id,city_id,description,status,episode_id,created) "
                    "VALUES(?,?,?,?,?,?)", (f"{ep_id}-c{i}", row["city_id"], desc, "shown", ep_id, db.now()))


IG_TOKEN_FILE = config.DATA / "ig_token.txt"   # local, jamais versionné (data/ est dans .gitignore)


def refresh_ig_token(con) -> dict:
    """Renouvelle le jeton Instagram longue durée (60 j) chaque semaine et met à jour le secret GitHub du
    dépôt de diffusion via le GitHub CLI déjà connecté. Le jeton n'apparaît jamais dans les journaux."""
    if "graph.instagram.com" not in (config.get("IG_API_HOST") or ""):
        return {"status": "jeton sans expiration (connexion unifiée)"}
    if not IG_TOKEN_FILE.exists():
        return {"status": "configuration_requise"}
    last = db.get_conf(con, "ig_token_refreshed", "")
    if last and (dt.datetime.now() - dt.datetime.fromisoformat(last)).days < 7:
        return {"status": "à jour"}
    import urllib.parse
    import urllib.request
    tok = IG_TOKEN_FILE.read_text(encoding="utf-8").strip()
    url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": tok})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            new = json.loads(r.read().decode())["access_token"]
    except Exception as e:
        log(f"ALERTE jeton Instagram : renouvellement impossible ({type(e).__name__}) — reconnexion peut-être nécessaire")
        return {"status": "échec"}
    repo = config.get("CLOUD_REPO") or "Math0588/lbf-diffusion"
    p = subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "-R", repo], input=new, text=True,
                       capture_output=True)
    if p.returncode != 0:
        log("ALERTE jeton Instagram : renouvelé mais secret GitHub non mis à jour")
        return {"status": "échec_secret"}
    IG_TOKEN_FILE.write_text(new, encoding="utf-8")
    db.set_conf(con, "ig_token_refreshed", db.now(), "worker")
    return {"status": "renouvelé"}


def reserve_days(con) -> int:
    """Jours de publication couverts par la réserve (nombre de vidéos ÷ créneaux quotidiens)."""
    n = con.execute("SELECT COUNT(*) FROM episodes WHERE state IN ('qa_passed','scheduled')").fetchone()[0]
    per_day = max(1, len([s for s in (config.get("PUBLISH_SLOTS") or "12:30,19:00").split(",") if s.strip()]))
    return n // per_day


# ----------------------------------------------------------------------------- boucle

def tick(con) -> dict:
    heartbeat()
    h = health(con)
    out = {"health": h}
    if h["paused"]:
        log("Pause générale : rien n'est produit ni exporté.")
        return out
    if not h["disk_ok"]:
        log(f"ALERTE espace disque : {h['disk_free_gb']} Go libres")
        return out
    last_v = db.get_conf(con, "last_veille", "")
    if last_v[:10] != dt.date.today().isoformat():
        try:
            out["veille"] = veille.run()
        except Exception as e:
            out["veille"] = {"error": str(e)[:200]}
        db.set_conf(con, "last_veille", db.now(), "worker")
    out["ig_token"] = refresh_ig_token(con)
    out["trends"] = react_to_trends(con)
    out["sync"] = sync_publications(con)
    target = int(config.get("RESERVE_TARGET_DAYS") or 10)
    urgent = con.execute("SELECT COUNT(*) FROM episodes WHERE priority<100 AND state IN "
                         "('render_queued','retry_wait')").fetchone()[0]
    if reserve_days(con) < target or urgent:
        out["planned"] = ensure_backlog(con, 2)
        check_scripted(con)
        out["produced"] = produce_one(con)
    out["export"] = export_reserve(con)
    out["reserve"] = reserve_days(con)
    if db.get_conf(con, "last_backup", "")[:10] != dt.date.today().isoformat():
        db.backup(con)
        db.set_conf(con, "last_backup", db.now(), "worker")
    return out


def main(loop: bool) -> int:
    if not acquire_process_lock():
        log("Un autre worker tourne déjà : arrêt.")
        return 1
    con = db.connect()
    db.sync_content(con)
    # reprise après redémarrage : les verrous expirés seront repris, un « rendering » orphelin est remis en file
    con.execute("UPDATE episodes SET state='render_queued', lock_owner=NULL, lock_until=NULL "
                "WHERE state='rendering' AND (lock_until IS NULL OR lock_until < ?)", (db.now(),))
    log("Worker démarré.")
    try:
        return _loop(con, loop)
    finally:
        release_process_lock()


def release_process_lock() -> None:
    try:
        if json.loads(LOCK.read_text(encoding="utf-8")).get("owner") == OWNER:
            LOCK.unlink()
    except Exception:
        pass


def _loop(con, loop: bool) -> int:
    while True:
        try:
            r = tick(con)
            log(f"Cycle : réserve={r.get('reserve')} produit={r.get('produced')} export={r.get('export', {}).get('status')}")
        except Exception as e:
            log(f"Erreur de cycle : {e}\n{traceback.format_exc()[-1200:]}")
        if not loop:
            break
        idle = 60 if reserve_days(con) < int(config.get("RESERVE_TARGET_DAYS") or 10) else 1800
        heartbeat("en attente")
        time.sleep(idle)
    return 0


if __name__ == "__main__":
    sys.exit(main("--loop" in sys.argv))
