"""Fabrication 24 h/24 dans GitHub Actions (PC éteint).

Un passage : prochain script non utilisé (état versionné dans state/studio.json) → planner_v2.plan →
produce.produce("final") → vidéo, couverture et métadonnées envoyées dans la release publique « reserve »
de ce dépôt → index.json (file d'attente lue par le diffuseur) mis à jour.

Ordre : pilotes réécrits prioritaires, puis la banque (villes alternées, worker.bank_scripts)."""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import config

STATE = config.ROOT / "state" / "studio.json"
RELEASE = "reserve"
PRIORITY = ["macronville_pilot_01.json", "glucksmannville_pilot_01.json"]
ALREADY_PUBLISHED = {"bdv-s01e01"}   # publié avant la fabrication cloud
MAX_ATTEMPTS = 2


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"produced": [], "attempts": {}, "skipped": []}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def candidates() -> list[Path]:
    from .worker import bank_scripts
    scripts = config.CONTENT / "scripts"
    first = [scripts / n for n in PRIORITY if (scripts / n).exists()]
    rest = [p for p in bank_scripts() if p not in first]
    return first + rest


def release_names() -> set:
    r = gh("release", "view", RELEASE, "--json", "assets", check=False)
    return {a["name"] for a in json.loads(r.stdout or "{}").get("assets", [])} if r.returncode == 0 else set()


def next_script(st: dict, offset: int = 0) -> Path | None:
    """offset-ième script non fabriqué : plusieurs passages en parallèle prennent chacun le leur."""
    names = release_names()
    done = {n[:-4] for n in names if n.endswith(".mp4")} | set(st["skipped"]) | ALREADY_PUBLISHED
    skip = offset
    from . import viral_lint
    cands = candidates()

    from . import voix_externe

    def rank(p):
        sc = json.loads(p.read_text(encoding="utf-8"))
        histoire = any(x.get("gags") or x.get("actions") for x in sc.get("scenes", []))
        if histoire and voix_externe.available(sc):
            return -1                      # voix enregistrée prête : on la fabrique en premier
        return 0 if histoire else (1 if viral_lint.check(sc, strict=True)["ok"] else 2)
    # histoires absurdes avec gags et gestes d'abord, puis « moquerie de la personne », puis le reste validé
    cands = sorted(cands, key=rank)
    for p in cands:
        sc = json.loads(p.read_text(encoding="utf-8"))
        sid = sc["id"]
        if sid in done or st["attempts"].get(sid, 0) >= MAX_ATTEMPTS:
            continue
        if not viral_lint.check(sc)["ok"]:   # ancien script « soft » ou incomplet : jamais fabriqué
            continue
        if sc.get("a_verifier"):              # fait pas assez sourcé : en attente de vérification
            continue
        if skip:
            skip -= 1
            continue
        return p
    return None


def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} : {r.stderr.strip()[:300]}")
    return r


def ensure_release():
    if gh("release", "view", RELEASE, check=False).returncode != 0:
        gh("release", "create", RELEASE, "--title", "Réserve de vidéos",
           "--notes", "Vidéos prêtes à publier (fabrication automatique).", "--latest=false")


def upload(files: list[Path]):
    gh("release", "upload", RELEASE, *map(str, files), "--clobber")


def produce_one(st: dict, script: Path) -> dict:
    from . import planner_v2, produce
    s = json.loads(script.read_text(encoding="utf-8"))
    sid = s["id"]
    t0 = time.time()
    ep_path = planner_v2.plan_file(script)
    rep = produce.produce(ep_path, "final")
    if rep.get("status") != "qa_passed":
        print(f"[studio] {sid} : {rep.get('status')} — QA : "
              + ", ".join(c["check"] for c in rep.get("qa", {}).get("checks", []) if not c["ok"]), flush=True)
        st["attempts"][sid] = st["attempts"].get(sid, 0) + 1   # seul un échec réel compte (pas une annulation)
        if rep.get("status") == "rejected":
            st["skipped"].append(sid)
        return {"id": sid, "ok": False, "status": rep.get("status")}
    pub = config.OUTPUT / "episodes" / sid / "publication"
    ep = json.loads(ep_path.read_text(encoding="utf-8"))
    manifest = json.loads((pub / "manifest.json").read_text(encoding="utf-8"))
    meta = {"episode_id": sid, "city": ep["city_id"], "title": ep["title_cover"],
            "caption": (pub / "caption.txt").read_text(encoding="utf-8"),
            "credits": (pub / "CREDITS.txt").read_text(encoding="utf-8"),
            "manifest": manifest, "seo": ep.get("seo", {}),
            "narration": [x["text"] for x in ep["narration_segments"]],
            "premier_commentaire": ep.get("premier_commentaire"),
            "produced_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "render": {k: rep.get("render", {}).get(k) for k in ("engine", "res", "samples", "frames", "wall_s")},
            "steps": rep.get("steps")}
    tmp = config.OUTPUT / "upload"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / f"{sid}.mp4").write_bytes((pub / "video.mp4").read_bytes())
    (tmp / f"{sid}.jpg").write_bytes((pub / "cover.jpg").read_bytes())
    (tmp / f"{sid}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    upload([tmp / f"{sid}.mp4", tmp / f"{sid}.jpg", tmp / f"{sid}.json"])
    st["produced"].append({"id": sid, "city": ep["city_id"], "title": ep["title_cover"],
                           "at": meta["produced_at"], "wall_s": round(time.time() - t0)})
    save_state(st)
    publish_index(st)
    print(f"[studio] {sid} prêt en {round(time.time() - t0)} s", flush=True)
    return {"id": sid, "ok": True}


def publish_index(st: dict):
    """index.json reconstruit depuis la release (sûr même avec des passages parallèles), ordre de fabrication."""
    names = release_names()
    items = []
    for p in candidates():
        s = json.loads(p.read_text(encoding="utf-8"))
        if f"{s['id']}.mp4" in names and f"{s['id']}.json" in names:
            items.append({"id": s["id"], "city": s.get("city"), "title": s.get("title_cover")})
    st = {"produced": items}
    idx = config.OUTPUT / "upload" / "index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(json.dumps({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                               "items": st["produced"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    upload([idx])


def main():
    max_n = int(os.environ.get("MAX_VIDEOS", "1") or 1)
    budget = float(os.environ.get("TIME_BUDGET_MIN", "270")) * 60
    t0 = time.time()
    st = load_state()
    ensure_release()
    made = 0
    offset = int(os.environ.get("SLOT", "0") or 0)
    while made < max_n and time.time() - t0 < budget:
        sc = next_script(st, offset)
        if not sc:
            print("[studio] banque épuisée", flush=True)
            break
        try:
            r = produce_one(st, sc)
        except Exception as e:
            print(f"[studio] échec {sc.name} : {type(e).__name__} {str(e)[:500]}", flush=True)
            sid = json.loads(sc.read_text(encoding="utf-8"))["id"]
            st["attempts"][sid] = st["attempts"].get(sid, 0) + 1
            r = {"ok": False}
        save_state(st)
        made += 1 if r.get("ok") else 0
        if not r.get("ok") and os.environ.get("STOP_ON_FAIL") == "true":
            break
    print(f"[studio] {made} vidéo(s) fabriquée(s) en {round((time.time() - t0) / 60)} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
