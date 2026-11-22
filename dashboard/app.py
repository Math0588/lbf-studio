"""Tableau de bord local — Le Bordel Français.

Lancement : Demarrer.bat (ou `python -m dashboard.app`). Écoute 127.0.0.1:8765 par défaut.
Accès téléphone : uniquement via un accès authentifié (ex. Tailscale) ET un DASHBOARD_TOKEN ; jamais exposé
publiquement sans protection.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import subprocess
import sys
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, send_file

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lbf import config, db, worker  # noqa: E402

app = Flask(__name__)
E = html.escape

STATE_FR = {"idea": "idée", "scripted": "écrit", "checked": "vérifié", "render_queued": "en file de rendu",
            "rendering": "rendu en cours", "rendered": "rendu", "qa_passed": "prêt", "scheduled": "dans la réserve cloud",
            "publishing": "publication en cours", "published": "publié (preuve)", "needs_review": "à relire",
            "rejected": "rejeté", "retry_wait": "nouvel essai prévu", "failed": "échec",
            "publication_uncertain": "publication incertaine", "archived": "archivé"}
COLOR = {"published": "#1a7f37", "qa_passed": "#1649FF", "scheduled": "#1649FF", "failed": "#EF233C",
         "rejected": "#EF233C", "publication_uncertain": "#b26b00", "needs_review": "#b26b00"}

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#f6f5f0;color:#111827}
header{background:#1649FF;color:#FFFDF7;padding:12px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header b{font-weight:900;letter-spacing:.5px}header .r{border-bottom:4px solid #EF233C}
nav{display:flex;gap:6px;flex-wrap:wrap;padding:8px 12px;background:#fff;border-bottom:1px solid #ddd;position:sticky;top:0}
nav a{padding:6px 10px;border-radius:8px;text-decoration:none;color:#111827;font-size:14px}nav a.on{background:#1649FF;color:#fff}
main{padding:14px;max-width:1100px;margin:auto}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.card{background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 3px #0001}.big{font-size:28px;font-weight:800}
.pill{display:inline-block;padding:2px 8px;border-radius:99px;color:#fff;font-size:12px;background:#6b7280}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}td,th{padding:8px;border-bottom:1px solid #eee;text-align:left;font-size:14px;vertical-align:top}
button,.btn{background:#1649FF;color:#fff;border:0;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block;margin:2px}
.danger{background:#EF233C}.ghost{background:#e5e7eb;color:#111827}.warn{color:#b26b00}.ok{color:#1a7f37}.ko{color:#EF233C}
video{width:100%;max-width:340px;border-radius:12px;background:#000}input,textarea,select{width:100%;padding:8px;border:1px solid #ccc;border-radius:8px;font:inherit}
small{color:#6b7280}h2{margin:18px 0 8px}
"""

TABS = [("/", "Aujourd'hui"), ("/studio", "Studio"), ("/calendrier", "Calendrier"), ("/univers", "Univers"),
        ("/bibliotheque", "Bibliothèque"), ("/stats", "Statistiques"), ("/boutique", "Boutique & formation"),
        ("/contacts", "Contacts marques"), ("/reglages", "Réglages & diagnostic")]


@app.before_request
def guard():
    tok = config.get("DASHBOARD_TOKEN")
    local = request.remote_addr in ("127.0.0.1", "::1")
    if not local and (not tok or request.args.get("t") != tok and request.cookies.get("t") != tok):
        abort(403)


def page(title: str, body: str, path: str = "/") -> Response:
    nav = "".join(f'<a class="{"on" if p == path else ""}" href="{p}">{E(n)}</a>' for p, n in TABS)
    return Response(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · Le Bordel Français</title>
<style>{CSS}</style></head><body><header><b>LE BORDEL <span class="r">FRANÇAIS</span></b>
<small style="color:#dbe3ff">studio · tableau de bord</small></header><nav>{nav}</nav><main>{body}</main></body></html>""",
                    mimetype="text/html")


def con():
    return db.connect()


def pill(state: str) -> str:
    return f'<span class="pill" style="background:{COLOR.get(state, "#6b7280")}">{E(STATE_FR.get(state, state))}</span>'


def worker_status() -> dict:
    try:
        info = json.loads((config.DATA / "worker.lock").read_text(encoding="utf-8"))
        age = (dt.datetime.now() - dt.datetime.fromisoformat(info["heartbeat"])).total_seconds()
        info["alive"] = age < 2400
        info["age_min"] = round(age / 60)
        return info
    except Exception:
        return {"alive": False}


# ----------------------------------------------------------------------------- écrans

@app.route("/")
def today():
    c = con()
    h = worker.health(c)
    ws = worker_status()
    counts = {r["state"]: r["n"] for r in c.execute("SELECT state, COUNT(*) n FROM episodes GROUP BY state")}
    reserve = counts.get("qa_passed", 0) + counts.get("scheduled", 0)
    nxt = c.execute("SELECT id,title,state FROM episodes WHERE state IN ('scheduled','qa_passed') ORDER BY updated LIMIT 1").fetchone()
    last = c.execute("SELECT * FROM publications WHERE status='published' ORDER BY published_at DESC LIMIT 1").fetchone()
    alerts = []
    repo = worker.cloud_repo()
    if repo and (repo / "state" / "alerts.json").exists():
        alerts = json.loads((repo / "state" / "alerts.json").read_text(encoding="utf-8"))[-5:]
    paused = h["paused"]
    body = f"""
<div class="cards">
 <div class="card"><small>Prochaine vidéo</small><div class="big">{E(nxt['title']) if nxt else '—'}</div>
   {pill(nxt['state']) if nxt else '<span class="warn">réserve vide</span>'}</div>
 <div class="card"><small>Réserve (jours de publication prêts)</small><div class="big">{reserve}</div>
   <small>objectif {E(config.get('RESERVE_TARGET_DAYS'))} jours</small></div>
 <div class="card"><small>Dernière publication</small><div class="big">{E((last['published_at'] or '')[:10]) if last else '—'}</div>
   {f'<a href="{E(last["permalink"])}">voir sur Instagram</a>' if last and last['permalink'] else '<small>aucune preuve de publication pour l’instant</small>'}</div>
 <div class="card"><small>Santé</small><div>
   Worker : {'<b class="ok">actif</b>' if ws.get('alive') else '<b class="ko">arrêté</b>'} <small>({ws.get('state', '')})</small><br>
   Disque : <b class="{'ok' if h['disk_ok'] else 'ko'}">{h['disk_free_gb']} Go libres</b><br>
   Publication : <b>{'réelle' if h['live_publish'] else 'simulation (LIVE_PUBLISH=false)'}</b><br>
   Diffuseur cloud : <b class="{'ok' if repo else 'warn'}">{'configuré' if repo else 'configuration requise'}</b></div></div>
 <div class="card"><small>Coût d'exécution</small><div class="big">0 €</div>
   <small>mode gratuit : {'oui' if h['free_mode'] else 'NON'} · plafond API {E(config.get('MAX_API_SPEND'))} €</small></div>
</div>
<h2>Pause générale</h2>
<form method="post" action="/pause"><button class="{'ghost' if paused else 'danger'}">{'▶ Reprendre' if paused else '⏸ Tout mettre en pause'}</button>
<small>La pause arrête production, export et — via le diffuseur — publication.</small></form>
<h2>File</h2><table><tr><th>État</th><th>Nombre</th></tr>
{''.join(f'<tr><td>{pill(s)}</td><td>{n}</td></tr>' for s, n in sorted(counts.items()))}</table>
<h2>Exceptions à traiter</h2>
{''.join(f'<div class="card warn">{E(a["at"][:16])} · {E(a["kind"])} — {E(a["text"])}</div>' for a in alerts) or '<small>Aucune exception signalée.</small>'}
"""
    return page("Aujourd'hui", body, "/")


@app.post("/pause")
def toggle_pause():
    c = con()
    paused = (db.get_conf(c, "PAUSED") or "false") == "true"
    db.set_conf(c, "PAUSED", "false" if paused else "true")
    repo = worker.cloud_repo()
    if repo:  # propage au diffuseur cloud (state/control.json)
        cp = repo / "state" / "control.json"
        ctl = json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {"slot": config.get("PUBLISH_SLOT")}
        ctl["paused"] = not paused
        cp.parent.mkdir(exist_ok=True)
        cp.write_text(json.dumps(ctl, indent=2), encoding="utf-8")
        worker.git(repo, "add", "state/control.json")
        worker.git(repo, "commit", "-m", "pause" if not paused else "reprise")
        worker.git(repo, "push")
    return redirect("/")


@app.route("/studio")
@app.route("/studio/<eid>")
def studio(eid=None):
    c = con()
    if not eid:
        rows = c.execute("SELECT * FROM episodes ORDER BY updated DESC").fetchall()
        body = "<h2>Épisodes</h2><table><tr><th>Épisode</th><th>Titre</th><th>État</th><th>Essais</th></tr>" + "".join(
            f'<tr><td><a href="/studio/{E(r["id"])}">{E(r["id"])}</a></td><td>{E(r["title"] or "")}</td>'
            f'<td>{pill(r["state"])}<br><small>{E((r["last_error"] or "")[:120])}</small></td><td>{r["attempts"]}</td></tr>'
            for r in rows) + "</table>"
        return page("Studio", body, "/studio")
    r = c.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()
    if not r:
        abort(404)
    ep = json.loads(Path(r["path"]).read_text(encoding="utf-8"))
    out = config.OUTPUT / "episodes" / eid
    qa = c.execute("SELECT report FROM qa_results WHERE episode_id=? ORDER BY id DESC LIMIT 1", (eid,)).fetchone()
    qa = json.loads(qa["report"]) if qa else None
    vid = out / "publication" / "video.mp4"
    segs = "".join(f"<li>{E(s['text'])} <small>({E(s.get('claim_type', ''))})</small></li>" for s in ep["narration_segments"])
    checks = "".join(f'<li class="{"ok" if x["ok"] else "ko"}">{E(x["check"])} — {E(str(x["detail"]))[:120]}</li>'
                     for x in (qa or {}).get("checks", []))
    srcs = "".join(f'<li><a href="{E(s if isinstance(s, str) else s.get("url", ""))}">'
                   f'{E(s if isinstance(s, str) else s.get("url", ""))}</a></li>' for s in ep.get("sources", []))
    body = f"""<h2>{E(eid)} — {E(ep.get('title_cover', ''))} {pill(r['state'])}</h2>
<div class="cards"><div class="card">{f'<video controls src="/media/{E(eid)}/video.mp4"></video>' if vid.exists() else '<small>Pas encore de vidéo.</small>'}
<p><a href="/media/{E(eid)}/cover.jpg">couverture</a> · <a href="/media/{E(eid)}/caption.txt">légende</a></p></div>
<div class="card"><b>Script</b><ol>{segs}</ol><b>Accroches candidates</b><ul>{''.join(f'<li>{E(h)}</li>' for h in ep.get('hook_variants', []))}</ul>
<b>Chutes candidates</b><ul>{''.join(f'<li>{E(h)}</li>' for h in ep.get('ending_variants', []))}</ul>
<b>Sources</b><ul>{srcs or '<li><small>aucune (fiction pure)</small></li>'}</ul></div>
<div class="card"><b>Contrôles techniques</b><ul>{checks or '<li><small>non encore contrôlé</small></li>'}</ul>
<b>Avertissements du planificateur</b><ul>{''.join(f'<li class="warn">{E(w)}</li>' for w in ep.get('planner_warnings', [])) or '<li><small>aucun</small></li>'}</ul></div></div>
<form method="post" action="/studio/{E(eid)}/requeue"><button class="ghost">↻ Régénérer (remettre en file de rendu)</button></form>
<form method="post" action="/studio/{E(eid)}/archive"><button class="danger">Archiver (ne sera pas publié)</button></form>
{'<form method="post" action="/studio/' + E(eid) + '/approve"><button>Valider malgré l’alerte de relecture</button></form>' if r['state'] == 'needs_review' else ''}
<p><small>Aucune validation n'est requise pour les épisodes normaux : ces boutons servent aux exceptions.</small></p>"""
    return page(eid, body, "/studio")


@app.post("/studio/<eid>/<action>")
def studio_action(eid, action):
    c = con()
    if action == "requeue":
        c.execute("UPDATE episodes SET attempts=0 WHERE id=?", (eid,))
        db.set_state(c, eid, "render_queued")
    elif action == "archive":
        db.set_state(c, eid, "archived")
    elif action == "approve":
        db.audit(c, "approved_by_owner", eid, None, "propriétaire")
        db.set_state(c, eid, "render_queued")
    return redirect(f"/studio/{eid}")


@app.route("/media/<eid>/<name>")
def media(eid, name):
    if name not in ("video.mp4", "cover.jpg", "cover_grille.jpg", "caption.txt", "CREDITS.txt"):
        abort(404)
    p = (config.OUTPUT / "episodes" / eid / "publication" / name).resolve()
    if config.OUTPUT.resolve() not in p.parents or not p.exists():
        abort(404)
    return send_file(p)


@app.route("/calendrier")
def calendar():
    c = con()
    rows = c.execute("SELECT e.id,e.title,e.state,p.published_at,p.permalink FROM episodes e LEFT JOIN publications p "
                     "ON p.episode_id=e.id WHERE e.state IN ('qa_passed','scheduled','published','publication_uncertain') "
                     "ORDER BY COALESCE(p.published_at,'9999'), e.updated").fetchall()
    slot = config.get("PUBLISH_SLOT")
    day = dt.date.today()
    body = f"<p>Une vidéo par jour à <b>{E(slot)}</b> (Europe/Paris). Pas de rattrapage après une panne.</p><table>"
    body += "<tr><th>Jour</th><th>Épisode</th><th>État</th></tr>"
    for r in rows:
        if r["published_at"]:
            d = r["published_at"][:10]
        else:
            d = day.isoformat() + " (prévu)"
            day += dt.timedelta(days=1)
        link = f' · <a href="{E(r["permalink"])}">lien</a>' if r["permalink"] else ""
        body += f'<tr><td>{E(d)}</td><td><a href="/studio/{E(r["id"])}">{E(r["title"] or r["id"])}</a>{link}</td><td>{pill(r["state"])}</td></tr>'
    return page("Calendrier", body + "</table>", "/calendrier")


@app.route("/univers")
def universe():
    c = con()
    body = ""
    for city in c.execute("SELECT * FROM cities ORDER BY name"):
        b = json.loads(Path(city["bible_path"]).read_text(encoding="utf-8"))
        n_syn = len(json.loads((config.CONTENT / "synopses" / f"{city['id']}.json").read_text(encoding="utf-8")))
        n_bank = len(list((config.CONTENT / "scripts" / "bank" / city["id"]).glob("*.json")))
        eps = c.execute("SELECT state, COUNT(*) n FROM episodes WHERE city_id=? GROUP BY state", (city["id"],)).fetchall()
        shown = c.execute("SELECT description FROM continuity_events WHERE city_id=? AND status='shown'", (city["id"],)).fetchall()
        body += f"""<div class="card" style="margin-bottom:12px"><h2>{E(b['name'])}</h2><p><b>Règle :</b> {E(b.get('central_rule', ''))}</p>
<p><small>{n_syn} synopsis · {n_bank} scripts en banque · épisodes : {', '.join(f"{STATE_FR.get(e['state'], e['state'])} {e['n']}" for e in eps) or 'aucun'}</small></p>
<p><b>Habitants :</b> {', '.join(E(ch.get('name', '') + ' (' + ch.get('role', '') + ')') for ch in b.get('recurring_characters', []))}</p>
<p><b>Gags récurrents :</b> {'; '.join(E(g.get('base', '')) for g in b.get('running_gags', []))}</p>
<p><b>Continuité montrée à l'écran :</b> {'; '.join(E(s['description']) for s in shown) or '<small>rien encore publié</small>'}</p></div>"""
    return page("Univers", body, "/univers")


@app.route("/bibliotheque")
def library():
    voices = "".join(f"<li><b>{E(k)}</b> — {E(v['license'])}</li>" for k, v in config.CLEARED_VOICES.items())
    fonts = "".join(f"<li>{E(p.name)}</li>" for p in sorted(config.FONTS.glob("*")))
    from lbf.planner import CATALOG
    body = f"""<h2>Décors et accessoires 3D (catalogue du moteur)</h2><p>{', '.join(sorted(CATALOG))}</p>
<h2>Voix autorisées (chaîne de licence vérifiée)</h2><ul>{voices}</ul><h2>Fontes (SIL OFL)</h2><ul>{fonts}</ul>
<h2>Musique et effets</h2><p>Créations originales générées localement (lbf/audio.py) : aucune licence tierce.</p>
<h2>Ajouter une inspiration (blague, mème, lien)</h2>
<form method="post" action="/inbox"><input name="url" placeholder="URL de la source (ou « propriétaire »)">
<select name="city">{''.join(f'<option>{c}</option>' for c in worker.CITY_ORDER + ['transversal'])}</select>
<textarea name="text" rows="3" placeholder="Texte, mème ou idée"></textarea>
<input name="rights" placeholder="Droits de réutilisation (ex. : idée seulement, citation interdite)">
<button>Ajouter à la veille</button></form><small>Les inspirations sont des données : le générateur change toujours situation, construction et chute.</small>"""
    return page("Bibliothèque", body, "/bibliotheque")


@app.post("/inbox")
def inbox_add():
    d = ROOT / "inbox"
    d.mkdir(exist_ok=True)
    name = f"{request.form.get('city', 'transversal')}-{dt.datetime.now():%Y%m%d%H%M%S}.txt"
    (d / name).write_text(f"{request.form.get('url', '')}\n{request.form.get('text', '')}\ndroits: "
                          f"{request.form.get('rights', 'inconnu')}\n", encoding="utf-8")
    return redirect("/bibliotheque")


@app.route("/stats")
def stats():
    c = con()
    rows = c.execute("SELECT * FROM metric_snapshots ORDER BY taken_at DESC LIMIT 200").fetchall()
    if not rows:
        body = ("<p>Aucune mesure réelle pour l'instant. Les statistiques apparaissent 24 h, 72 h et 7 jours après "
                "chaque publication, uniquement avec les données exposées par l'API (aucune donnée inventée, une "
                "valeur absente reste absente).</p>")
    else:
        body = "<table><tr><th>Épisode</th><th>Fenêtre</th><th>Données</th></tr>" + "".join(
            f"<tr><td>{E(r['episode_id'])}</td><td>{E(r['window'])}</td><td><small>{E(r['data'])}</small></td></tr>"
            for r in rows) + "</table>"
        body += ("<p><small>Formules : partages / comptes touchés ; temps moyen / durée (≠ taux de complétion). "
                 "Comparer des médianes de vidéos comparables, jamais une réussite isolée.</small></p>")
    return page("Statistiques", body, "/stats")


@app.route("/boutique")
def shop():
    c = con()
    rows = c.execute("SELECT * FROM products").fetchall()
    body = "<h2>Produits</h2><table><tr><th>Produit</th><th>Collection</th><th>Slogan</th><th>État</th></tr>" + "".join(
        f"<tr><td>{E(r['id'])}</td><td>{E(r['collection'] or '')}</td><td>{E(r['slogan'] or '')}</td>"
        f"<td>{E(r['status'] or '')}{' · <a href=' + E(r['shop_url']) + '>boutique</a>' if r['shop_url'] else ''}</td></tr>"
        for r in rows) + "</table>"
    body += ("<p>La boutique (Spreadshop) encaisse, fabrique, expédie et gère le SAV elle-même : elle fonctionne même "
             "PC éteint. Voir docs/BOUTIQUE.md. Formation : docs/FORMATION.md.</p>")
    sales = c.execute("SELECT * FROM sales_aggregates ORDER BY period DESC LIMIT 12").fetchall()
    body += "<h2>Ventes (saisies depuis les relevés de la plateforme)</h2>" + ("<small>Aucune vente enregistrée.</small>" if not sales else "")
    return page("Boutique & formation", body, "/boutique")


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    c = con()
    if request.method == "POST":
        f = request.form
        c.execute("INSERT INTO inbound_partnerships(company,contact,request,received,budget_stated,status,conversation_url) "
                  "VALUES(?,?,?,?,?,?,?)", (f.get("company"), f.get("contact"), f.get("request"), db.now(),
                                            f.get("budget"), "nouveau", f.get("url")))
        return redirect("/contacts")
    rows = c.execute("SELECT * FROM inbound_partnerships ORDER BY received DESC").fetchall()
    body = "<table><tr><th>Entreprise</th><th>Demande</th><th>Budget annoncé</th><th>Statut</th></tr>" + "".join(
        f"<tr><td>{E(r['company'] or '')}<br><small>{E(r['contact'] or '')}</small></td><td>{E(r['request'] or '')}</td>"
        f"<td>{E(r['budget_stated'] or '—')}</td><td>{E(r['status'])}</td></tr>" for r in rows) + "</table>"
    body += """<h2>Nouvelle demande</h2><form method="post"><input name="company" placeholder="Entreprise">
<input name="contact" placeholder="Personne de contact"><textarea name="request" placeholder="Demande"></textarea>
<input name="budget" placeholder="Budget communiqué"><input name="url" placeholder="Lien vers la conversation">
<button>Enregistrer</button></form><small>Aucune prospection automatique. Partenariat payé = mention « Collaboration
commerciale » + outil « partenariat rémunéré » d'Instagram (docs/PARTENARIATS.md).</small>"""
    return page("Contacts marques", body, "/contacts")


@app.route("/reglages")
def settings():
    c = con()
    keys = ["FREE_MODE", "MAX_API_SPEND", "X_ENABLED", "PAID_VIDEO_GENERATION", "PAID_TTS", "LIVE_PUBLISH",
            "PUBLISH_SLOT", "RESERVE_TARGET_DAYS", "VOICE_MODEL", "OLLAMA_MODEL", "CLOUD_REPO_DIR"]
    rows = "".join(f"<tr><td>{k}</td><td>{E(config.get(k) or '—')}</td></tr>" for k in keys)
    try:
        bv = subprocess.run([config.blender_path(), "--version"], capture_output=True, text=True, timeout=30).stdout.split("\n")[0]
    except Exception as e:
        bv = f"introuvable ({e})"
    fv = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]
    rend = c.execute("SELECT AVG(render_s) a, COUNT(*) n FROM renders WHERE profile='final' AND render_s>0").fetchone()
    body = f"""<h2>Configuration (.env)</h2><table>{rows}</table>
<p><small>Les secrets (jetons Instagram, GitHub) ne sont jamais affichés ni stockés ici : ils vivent dans les secrets GitHub du dépôt de diffusion.</small></p>
<h2>Diagnostic</h2><table><tr><td>Blender</td><td>{E(bv)}</td></tr><tr><td>FFmpeg</td><td>{E(fv[:80])}</td></tr>
<tr><td>Rendu final moyen (mesuré)</td><td>{f"{rend['a'] / 60:.1f} min sur {rend['n']} épisode(s)" if rend['n'] else '—'}</td></tr></table>
<h2>Sauvegarde</h2><form method="post" action="/backup"><button>Sauvegarder la base maintenant</button></form>
<p><small>Sauvegarde automatique quotidienne (30 conservées) dans data/backups. Restauration : <code>python -m lbf.cli restaurer &lt;fichier&gt;</code>.</small></p>"""
    return page("Réglages", body, "/reglages")


@app.post("/backup")
def do_backup():
    db.backup(con())
    return redirect("/reglages")


if __name__ == "__main__":
    app.run(host=config.get("DASHBOARD_HOST"), port=int(config.get("DASHBOARD_PORT")), debug=False)
