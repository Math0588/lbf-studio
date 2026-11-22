"""SQLite : schéma, migrations simples (PRAGMA user_version), sauvegarde et restauration."""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sqlite3
from pathlib import Path

from . import config

DB_PATH = config.DATA / "lbf.db"
BACKUPS = config.DATA / "backups"

STATES = ["idea", "scripted", "checked", "render_queued", "rendering", "rendered", "qa_passed", "scheduled",
          "publishing", "published"]
BRANCHES = ["needs_review", "rejected", "retry_wait", "failed", "publication_uncertain", "archived"]

MIGRATIONS = [
    # v1 — schéma minimal du cahier des charges
    """
    CREATE TABLE sources(id INTEGER PRIMARY KEY, url TEXT UNIQUE, author TEXT, published TEXT, consulted TEXT,
        kind TEXT, license TEXT);
    CREATE TABLE inspirations(id TEXT PRIMARY KEY, source_id INTEGER, city TEXT, subject TEXT, context TEXT,
        status TEXT, license TEXT, original_angle TEXT, excluded TEXT, used_in TEXT, created TEXT);
    CREATE TABLE claims(id INTEGER PRIMARY KEY, episode_id TEXT, segment_id TEXT, text TEXT, claim_type TEXT,
        source_urls TEXT, verified INTEGER DEFAULT 0);
    CREATE TABLE cities(id TEXT PRIMARY KEY, name TEXT, bible_path TEXT, set_path TEXT);
    CREATE TABLE districts(id TEXT PRIMARY KEY, city_id TEXT, name TEXT, description TEXT);
    CREATE TABLE recurring_characters(id TEXT PRIMARY KEY, city_id TEXT, name TEXT, role TEXT, data TEXT);
    CREATE TABLE story_arcs(id TEXT PRIMARY KEY, city_id TEXT, title TEXT, data TEXT);
    CREATE TABLE continuity_events(id TEXT PRIMARY KEY, city_id TEXT, description TEXT,
        status TEXT CHECK(status IN ('established','unpublished_idea','shown')), episode_id TEXT, created TEXT);
    CREATE TABLE running_gags(id TEXT PRIMARY KEY, city_id TEXT, base TEXT, last_stage INTEGER DEFAULT 0, data TEXT);
    CREATE TABLE episodes(id TEXT PRIMARY KEY, city_id TEXT, season INTEGER, episode_number INTEGER,
        title TEXT, state TEXT NOT NULL DEFAULT 'idea', path TEXT, synopsis_id TEXT, content_hash TEXT,
        attempts INTEGER DEFAULT 0, last_error TEXT, lock_owner TEXT, lock_until TEXT, priority INTEGER DEFAULT 100,
        scheduled_at TEXT, created TEXT, updated TEXT);
    CREATE TABLE script_versions(id INTEGER PRIMARY KEY, episode_id TEXT, version INTEGER, author TEXT,
        body TEXT, created TEXT);
    CREATE TABLE scenes(id INTEGER PRIMARY KEY, episode_id TEXT, scene_id TEXT, data TEXT);
    CREATE TABLE assets(id TEXT PRIMARY KEY, kind TEXT, path TEXT, description TEXT, license_id INTEGER);
    CREATE TABLE asset_licenses(id INTEGER PRIMARY KEY, name TEXT, license TEXT, attribution TEXT,
        commercial_ok INTEGER, verified_on TEXT, evidence TEXT);
    CREATE TABLE renders(id INTEGER PRIMARY KEY, episode_id TEXT, profile TEXT, frames INTEGER, render_s REAL,
        wall_s REAL, engine TEXT, blender TEXT, path TEXT, created TEXT);
    CREATE TABLE qa_results(id INTEGER PRIMARY KEY, episode_id TEXT, passed INTEGER, report TEXT, created TEXT);
    CREATE TABLE publish_jobs(id INTEGER PRIMARY KEY, episode_id TEXT UNIQUE, status TEXT, exported_at TEXT,
        video_sha256 TEXT, attempts INTEGER DEFAULT 0, last_error TEXT);
    CREATE TABLE publications(id INTEGER PRIMARY KEY, episode_id TEXT UNIQUE, platform TEXT, media_id TEXT,
        permalink TEXT, published_at TEXT, status TEXT, raw TEXT);
    CREATE TABLE metric_snapshots(id INTEGER PRIMARY KEY, episode_id TEXT, media_id TEXT, window TEXT,
        taken_at TEXT, data TEXT, UNIQUE(media_id, window));
    CREATE TABLE experiments(id INTEGER PRIMARY KEY, name TEXT, hypothesis TEXT, arm TEXT, episode_id TEXT,
        notes TEXT);
    CREATE TABLE products(id TEXT PRIMARY KEY, collection TEXT, slogan TEXT, status TEXT, shop_url TEXT, data TEXT);
    CREATE TABLE sales_aggregates(id INTEGER PRIMARY KEY, period TEXT, platform TEXT, revenue REAL,
        creator_earnings REAL, variable_costs REAL, refunds REAL, orders INTEGER, sessions INTEGER, source TEXT);
    CREATE TABLE inbound_partnerships(id INTEGER PRIMARY KEY, company TEXT, contact TEXT, request TEXT,
        received TEXT, budget_stated TEXT, status TEXT DEFAULT 'nouveau', conversation_url TEXT, draft_reply TEXT);
    CREATE TABLE configuration(key TEXT PRIMARY KEY, value TEXT, updated TEXT);
    CREATE TABLE audit_events(id INTEGER PRIMARY KEY, at TEXT, actor TEXT, action TEXT, episode_id TEXT,
        detail TEXT);
    CREATE INDEX ix_ep_state ON episodes(state);
    """,
]


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=30, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    migrate(con)
    repair_paths(con)
    return con


def repair_paths(con) -> int:
    """Après un déplacement du projet, recolle les chemins d'épisodes sur le dossier courant."""
    n = 0
    for r in con.execute("SELECT id, path FROM episodes WHERE path IS NOT NULL").fetchall():
        p = Path(r["path"])
        if not p.exists() or config.ROOT.resolve() not in p.resolve().parents:
            cand = config.CONTENT / "episodes" / f"{r['id']}.json"
            if cand.exists():
                con.execute("UPDATE episodes SET path=? WHERE id=?", (str(cand), r["id"]))
                n += 1
    return n


def migrate(con: sqlite3.Connection) -> int:
    v = con.execute("PRAGMA user_version").fetchone()[0]
    for i, sql in enumerate(MIGRATIONS[v:], start=v + 1):
        con.executescript("BEGIN;" + sql + f"; PRAGMA user_version={i}; COMMIT;")
    return con.execute("PRAGMA user_version").fetchone()[0]


def audit(con, action: str, episode_id: str | None = None, detail=None, actor: str = "worker") -> None:
    con.execute("INSERT INTO audit_events(at, actor, action, episode_id, detail) VALUES(?,?,?,?,?)",
                (now(), actor, action, episode_id, json.dumps(detail, ensure_ascii=False) if detail else None))


def set_state(con, episode_id: str, state: str, error: str | None = None) -> None:
    assert state in STATES + BRANCHES, state
    con.execute("UPDATE episodes SET state=?, last_error=?, updated=? WHERE id=?", (state, error, now(), episode_id))
    audit(con, f"state:{state}", episode_id, {"error": error} if error else None)


def get_conf(con, key: str, default=None):
    r = con.execute("SELECT value FROM configuration WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_conf(con, key: str, value: str, actor="tableau_de_bord") -> None:
    con.execute("INSERT INTO configuration(key,value,updated) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET "
                "value=excluded.value, updated=excluded.updated", (key, value, now()))
    audit(con, f"config:{key}", None, {"value": value}, actor)


def claim_episode(con, owner: str, states=("render_queued",), minutes=90):
    """Verrouille atomiquement un épisode (un seul worker, reprise après redémarrage quand le verrou expire)."""
    until = (dt.datetime.now() + dt.timedelta(minutes=minutes)).isoformat(timespec="seconds")
    q = ",".join("?" * len(states))
    con.execute("BEGIN IMMEDIATE")
    try:
        r = con.execute(f"SELECT id FROM episodes WHERE state IN ({q}) AND (lock_until IS NULL OR lock_until < ?) "
                        f"ORDER BY priority, created LIMIT 1", (*states, now())).fetchone()
        if r:
            con.execute("UPDATE episodes SET lock_owner=?, lock_until=? WHERE id=?", (owner, until, r["id"]))
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return r["id"] if r else None


def release(con, episode_id: str) -> None:
    con.execute("UPDATE episodes SET lock_owner=NULL, lock_until=NULL WHERE id=?", (episode_id,))


def backup(con=None) -> Path:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    dst = BACKUPS / f"lbf-{dt.datetime.now():%Y%m%d-%H%M%S}.db"
    src = con or connect()
    with sqlite3.connect(dst) as b:
        src.backup(b)
    # on garde les 30 dernières
    for old in sorted(BACKUPS.glob("lbf-*.db"))[:-30]:
        old.unlink()
    return dst


def restore(backup_path: Path) -> None:
    """Restaure une sauvegarde (la base courante est elle-même sauvegardée avant)."""
    if DB_PATH.exists():
        shutil.copy(DB_PATH, DB_PATH.with_suffix(f".avant-restauration-{dt.datetime.now():%Y%m%d%H%M%S}.db"))
    for ext in ("-wal", "-shm"):
        w = Path(str(DB_PATH) + ext)
        if w.exists():
            w.unlink()
    shutil.copy(backup_path, DB_PATH)


def sync_content(con) -> dict:
    """Importe villes, produits et épisodes présents dans content/ (idempotent)."""
    n = {"cities": 0, "episodes": 0, "products": 0}
    for p in (config.CONTENT / "cities").glob("*.json"):
        c = json.loads(p.read_text(encoding="utf-8"))
        con.execute("INSERT OR IGNORE INTO cities(id,name,bible_path,set_path) VALUES(?,?,?,?)",
                    (c["slug"], c["name"], str(p), str(config.CONTENT / "sets" / f"{c['slug']}.json")))
        for ev in c.get("continuity_events", []):
            con.execute("INSERT OR IGNORE INTO continuity_events(id,city_id,description,status,episode_id,created) "
                        "VALUES(?,?,?,?,?,?)", (ev["id"], c["slug"], ev["description"], ev.get("status", "established"),
                                                ev.get("since_episode"), now()))
        for ch in c.get("recurring_characters", []):
            con.execute("INSERT OR IGNORE INTO recurring_characters VALUES(?,?,?,?,?)",
                        (ch["id"], c["slug"], ch.get("name"), ch.get("role"), json.dumps(ch, ensure_ascii=False)))
        n["cities"] += 1
    pp = config.CONTENT / "products.json"
    if pp.exists():
        for pr in json.loads(pp.read_text(encoding="utf-8")):
            con.execute("INSERT OR IGNORE INTO products VALUES(?,?,?,?,?,?)",
                        (pr["id"], pr.get("collection"), pr.get("slogan"), pr.get("status"), pr.get("shop_url"),
                         json.dumps(pr, ensure_ascii=False)))
            n["products"] += 1
    for p in (config.CONTENT / "episodes").glob("*.json"):
        e = json.loads(p.read_text(encoding="utf-8"))
        cur = con.execute("SELECT id FROM episodes WHERE id=?", (e["id"],)).fetchone()
        if not cur:
            con.execute("INSERT INTO episodes(id,city_id,season,episode_number,title,state,path,synopsis_id,created,"
                        "updated) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (e["id"], e["city_id"], e.get("season", 1), e.get("episode_number"), e.get("title_cover"),
                         "scripted", str(p), e.get("synopsis_id"), now(), now()))
            n["episodes"] += 1
    return n


if __name__ == "__main__":
    c = connect()
    print("schéma v", c.execute("PRAGMA user_version").fetchone()[0], sync_content(c))
    print("sauvegarde :", backup(c))
