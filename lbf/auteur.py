"""Auteur automatique (format v4), dans GitHub Actions, avec Google Gemini (clé gratuite GEMINI_API_KEY).

Une petite salle d'écriture :
1. un fait RÉEL et SOURCÉ, jamais utilisé en v4, est tiré de la banque (plus de 600 faits déjà vérifiés) ;
2. Gemini écrit 3 versions d'une histoire en format v4 autour de ce fait (règles, principes viraux, scripts
   de référence en exemple) ;
3. un second appel joue le critique impitoyable et note chaque version ; on ne garde que la meilleure, et
   seulement si elle atteint la note minimale (sinon on recommence, au plus 3 fois) ;
4. contrôles automatiques : vocabulaire du moteur 3D, fait repris fidèlement (chiffres, citation), format v4,
   contrôle éditorial. Rien n'est inventé sur les faits : le fait cité vient de la banque, le reste est fiction.

Usage : python -m lbf.auteur [--n 3] [--stock 6] [--force]
  écrit jusqu'à n scripts si moins de « stock » scripts v4 restent à fabriquer (--force : écrit quand même).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import config, editorial, planner_v2, viral_lint

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELS = ["gemini-3.1-pro-preview", "gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-2.5-flash"]  # 2.5 Pro retiré par Google
SCRIPTS = config.CONTENT / "scripts"
AUTO = SCRIPTS / "bank_auto"
USED = config.ROOT / "state" / "faits_utilises.json"
LOG = config.ROOT / "state" / "auteur_log.json"
NOTE_MIN = float(config.get("AUTEUR_NOTE_MIN") or 8.0)

PREFIX = {"zemmourville": "zmv", "marineville": "mrv", "bardellaville": "bdv", "glucksmannville": "glv",
          "melenchonville": "mlv", "macronville": "mcv", "rinerville": "rnv", "durifville": "dfv"}
NAMES = {"bardellaville": "Bardella", "melenchonville": "Mélenchon", "macronville": "Macron", "zemmourville": "Zemmour",
         "marineville": "Marine Le Pen", "glucksmannville": "Glucksmann", "durifville": "Sylvain Durif",
         "rinerville": "Teddy Riner"}
RIVAL_CAMP = {"melenchonville": "le RN de Bardella", "bardellaville": "les Insoumis de Mélenchon",
              "glucksmannville": "les Insoumis", "macronville": "le RN et les gilets jaunes",
              "zemmourville": "le RN de Marine", "marineville": "les zemmouriens", "durifville": "les macronistes",
              "rinerville": "le RN de Bardella"}
PRODUCT = {"melenchonville": "absurde-melenchon", "bardellaville": "absurde-bardella",
           "glucksmannville": "absurde-glucksmann", "macronville": "absurde-macron", "zemmourville": "absurde-zemmour",
           "marineville": "absurde-marine"}
MAIN = ["macronville", "melenchonville", "bardellaville", "glucksmannville", "marineville", "zemmourville"]

CAMERAS = ["dolly_in", "closeup", "orbit", "street_dolly", "descend", "return"]
DECORS = ["person", "sign", "shop", "text3d", "ground", "mairie", "banner", "tribune", "tshirt", "table", "screen",
          "road", "building", "car", "ring_light", "tree", "lamp", "roundabout", "facade_row", "fountain", "bench",
          "bus", "mascot", "bin", "traffic_light"]
ANIMAUX = ["chat", "pigeon", "vache", "tortue", "mouton", "canard"]
PERSOS = ["alien", "robot", "bebe", "mamie"]
REFERENCES = ["glucksmannville/glv-u07", "zemmourville/zmv-u07", "marineville/mrv-u07", "macronville/mcv-u07"]

CONSIGNES = """Tu es le meilleur auteur satirique de France, au niveau des plus grands sketchs viraux. Tu écris pour
« Le Bordel Français » : des Reels Instagram de 25-30 s en animation 3D (personnages cubiques), voix off
sarcastique, qui se moquent des politiciens français. Objectif : que les gens regardent jusqu'au bout, rient
fort, et ENVOIENT la vidéo à un ami (le signal n°1 de l'algorithme Instagram), et que le camp adverse commente.

FORMAT V4 (obligatoire) :
- UNE seule SITUATION PRÉCISE et concrète (un lieu, un moment, un enjeu) : un repas de Noël, un mariage, un
  plateau télé, une dédicace, un aéroport, une soirée électorale… PAS une liste d'idées.
- Réplique 1 = ACCROCHE (≤ 12 mots) : on plonge directement dans la situation, avec le nom du politicien et
  l'image la plus absurde, sans l'expliquer (fossé de curiosité : on DOIT vouloir savoir pourquoi).
  Exemples : « 20 h, plateau télé : Glucksmann est en train de fondre. » / « Soirée électorale : Zemmour
  fixe la télé. Il attend le sursaut. »
- Le FAIT RÉEL fourni est repris fidèlement dans une réplique (ses chiffres, dates et citations exacts), sans
  rien y ajouter de faux. C'est lui qui déclenche ou explique l'absurde.
- Chaque réplique DÉCOULE de la précédente : lien « mais » (un obstacle, un retournement) ou « donc » (une
  conséquence), parfois « car ». Jamais « et puis ». Chaque tentative du personnage empire la situation :
  escalade absurde, de plus en plus énorme, mais toujours logique dans son monde.
- Avant-dernière réplique = CHUTE : un retournement qui vise la PERSONNE (son ego, sa contradiction, son bilan,
  son positionnement), drôle et cinglant. C'est la phrase qu'on cite en commentaire.
- Dernière réplique = « Envoie ça au pote qui… » : un pote PRÉCIS et reconnaissable (pas « qui vote X »).
- Provoque le camp adverse : {rival} doit en prendre pour son grade dans l'histoire, sans insulte.
- Ton : ultra provocateur, insolent, absurde, très drôle, références et mèmes français connus. Phrases
  courtes et orales (≤ 16 mots), 7 à 9 répliques au total, 75 à 92 mots au total.
- AUCUN élément gratuit : chaque animal, objet, personnage sert l'histoire et doit pouvoir se VOIR à l'écran.

INTERDITS : fausse citation, délit ou affaire inventés, vie privée, physique réel, origine, religion, sexualité,
handicap, appel à voter, le mot « suicide », toute accusation de vol ou de crime.

CE QUE LE MOTEUR 3D SAIT MONTRER (n'utilise RIEN d'autre) :
- caméras : {cameras}
- décors : {decors}
- le politicien (« maire ») et une foule ; gestes : {gestes} ; visages : {visages} ;
  objets tenus : {objets}
- gags : affiche avec texte court, panneau de prix (texte court), animal ({animaux}), personnage ({persos}),
  foule en gilets jaunes
- taille du politicien par plan (1.0 = normal, 0.3 = minuscule, 1.6 = géant) pour montrer une transformation
- un texte court à l'écran par plan (≤ 5 mots, en MAJUSCULES)
"""

FORMAT = """Réponds en JSON strict : {"versions": [ ...3 versions... ]}. Chaque version :
{"titre": "≤ 4 mots", "situation": "lieu, moment, enjeu en une phrase",
 "lignes": [{"texte": "…", "lien": "accroche|car|donc|mais|cta", "fait": true si c'est la réplique du fait réel,
   "ecran": "TEXTE ÉCRAN", "camera": "…", "decor": ["…"], "maire": {"geste": "…", "visage": "…", "objet": "…"} ou null,
   "foule": {"geste": "…", "visage": "…", "objet": "…"} ou null,
   "gags": [{"type": "affiche", "texte": "…"} | {"type": "prix", "texte": "…"} | {"type": "animal", "espece": "…"}
            | {"type": "perso", "qui": "…"} | {"type": "gilets_jaunes"}],
   "taille_maire": nombre ou null}]}"""

JUGE = """Tu es un directeur d'écriture impitoyable (humour viral, Instagram, France). Note chaque version de 0 à 10
sur : drole (fait-on vraiment rire ?), absurde (escalade folle mais logique), situation (une seule situation
précise et claire), enchainement (chaque réplique découle de la précédente), accroche (on veut savoir la suite
dès la 1re seconde), chute (cinglante, vise la personne), provocation (le camp adverse va commenter), visuel
(tout se voit à l'écran). Sois sévère : 8 = vraiment excellent, 5 = moyen. Donne aussi « global ».
Réponds en JSON strict : {"notes": [{"version": 0, "drole": n, "absurde": n, "situation": n, "enchainement": n,
"accroche": n, "chute": n, "provocation": n, "visuel": n, "global": n, "critique": "une phrase"}]}"""


def log(m):
    print(f"[auteur] {m}", flush=True)


def gemini(prompt: str, temperature: float = 1.0) -> dict:
    """Appel texte Gemini en JSON ; essaie Pro puis Flash (quota gratuit), avec attente si limite par minute."""
    models = [config.get("GEMINI_TEXT_MODEL")] if config.get("GEMINI_TEXT_MODEL") else MODELS
    last = None
    for model in models:
        for attempt in range(3):
            body = {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"}}
            req = urllib.request.Request(API.format(model=model), data=json.dumps(body).encode(), method="POST",
                                         headers={"x-goog-api-key": config.get("GEMINI_API_KEY").strip(),
                                                  "Content-Type": "application/json"})
            try:
                data = json.loads(urllib.request.urlopen(req, timeout=300).read())
                txt = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
                return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
            except urllib.error.HTTPError as e:
                last = f"{model} {e.code} {e.read()[:200].decode('utf-8', 'replace')}"
                if e.code in (429, 500, 503) and attempt < 2:   # limite par minute ou surcharge : on patiente
                    time.sleep(45 * (attempt + 1))
                    continue
                break                                  # modèle indisponible ou quota du jour : modèle suivant
            except (KeyError, IndexError, ValueError) as e:
                last = f"{model} réponse illisible ({e})"
                time.sleep(5)
        log(f"repli : {last}")
    raise RuntimeError(f"Gemini indisponible : {last}")


def all_scripts() -> list[dict]:
    out = []
    for f in glob.glob(str(SCRIPTS / "**" / "*.json"), recursive=True):
        try:
            s = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(s, dict) and "narration_segments" in s:
            s["_path"] = f
            out.append(s)
    return out


def fact_pool(scripts: list[dict]) -> dict:
    """ville → faits sourcés uniques (pas des scripts en attente de vérification)."""
    pool = {}
    for s in scripts:
        if s.get("a_verifier"):
            continue
        city = s.get("city") or s.get("city_id")
        for c in s.get("claims") or []:
            if isinstance(c, dict) and str(c.get("source", "")).startswith("http") \
                    and c.get("claim_type") in ("fait_public", "citation_exacte") and len(c.get("text", "")) > 15:
                pool.setdefault(city, {}).setdefault(c["text"].strip(), c)
    return pool


def produced() -> set:
    try:
        rel = json.loads(urllib.request.urlopen(
            "https://api.github.com/repos/Math0588/lbf-studio/releases/tags/reserve", timeout=30).read())
        return {a["name"][:-4] for a in rel.get("assets", []) if a["name"].endswith(".mp4")}
    except Exception:
        return set()


def stock(scripts: list[dict], done: set) -> dict:
    """Scripts v4 pas encore fabriqués, par ville."""
    st = {}
    for s in scripts:
        if s.get("format_v4") and s["id"] not in done:
            st.setdefault(s.get("city"), []).append(s["id"])
    return st


def _keys(text: str) -> list[str]:
    """Éléments du fait qui doivent apparaître tels quels : nombres, citation entre guillemets."""
    keys = re.findall(r"\d[\d  ,.]*\d|\d", text)
    keys += [q.strip() for q in re.findall(r"«\s*([^»]{4,})\s*»", text)]
    return [k.replace(" ", " ").strip(" .,") for k in keys if k.strip(" .,")]


def fact_ok(line: str, fact: str) -> bool:
    norm = lambda t: re.sub(r"\s+", " ", t.replace(" ", " ").replace("’", "'")).lower()
    l = norm(line)
    return all(norm(k) in l for k in _keys(fact))


def to_script(v: dict, city: str, sid: str, claim: dict) -> dict:
    segs, scenes = [], []
    lines = v.get("lignes", [])
    for i, ln in enumerate(lines):
        role = ln.get("lien", "")
        n = {"id": f"n{i}", "text": str(ln.get("texte", "")).strip(), "accent_words": [],
             "claim_type": ("citation_exacte" if "«" in claim["text"] else "fait_public") if ln.get("fait")
             else "fiction_satirique"}
        if i == 0:
            n["role"] = "accroche"
        elif role in ("car", "donc", "mais", "alors"):
            n["lien"] = role
        segs.append(n)
        acts = []
        for who in ("maire", "foule"):
            a = ln.get(who)
            if isinstance(a, dict) and a.get("geste") in planner_v2.GESTES:
                d = {"who": who, "geste": a["geste"],
                     "visage": a.get("visage") if a.get("visage") in planner_v2.VISAGES else "neutre",
                     "quand": 0.1 if who == "maire" else 0.4}
                if a.get("objet") in planner_v2.OBJETS:
                    d["objet"] = a["objet"]
                acts.append(d)
        gags = []
        for g in ln.get("gags") or []:
            t = g.get("type")
            if t in ("affiche", "prix") and g.get("texte"):
                gags.append({"type": t, "texte": str(g["texte"]).upper()[:28]})
            elif t == "animal" and g.get("espece") in ANIMAUX:
                gags.append({"type": "animal", "espece": g["espece"]})
            elif t == "perso" and g.get("qui") in PERSOS:
                gags.append({"type": "perso", "qui": g["qui"]})
            elif t == "gilets_jaunes":
                gags.append({"type": "gilets_jaunes"})
        sc = {"id": f"s{i}", "narration_ids": [f"n{i}"],
              "camera": ln.get("camera") if ln.get("camera") in CAMERAS else "closeup",
              "set": [d for d in (ln.get("decor") or []) if d in DECORS][:4] or ["person"],
              "onscreen_text": str(ln.get("ecran") or "").upper()[:30], "comic_action": n["text"],
              "expected_result": "", "actions": acts, "gags": gags[:2]}
        tm = ln.get("taille_maire")
        if isinstance(tm, (int, float)) and 0.2 <= tm <= 1.8:
            sc["mayor_look"] = {"scale": round(float(tm), 2)}
        if i == len(lines) - 1:
            sc.update(camera="return", set=["ground", "mairie", "tshirt"])
        scenes.append(sc)
    s = {"id": sid, "city": city, "synopsis_id": None, "format": "A", "length": "court", "format_v4": True,
         "auteur": "auto-gemini", "title_cover": str(v.get("titre", ""))[:40], "situation": v.get("situation", ""),
         "anchor": claim["text"], "hook_variants": [segs[0]["text"]] if segs else [], "selected_hook": 0,
         "ending_variants": [segs[-1]["text"]] if segs else [], "selected_ending": 0,
         "narration_segments": segs, "scenes": scenes, "cta_primary": segs[-1]["text"] if segs else "",
         "cta_commercial": {"type": "visual_product", "text": "Collection en bio",
                            "product_id": PRODUCT.get(city, "absurde-macron")},
         "claims": [claim], "sources": [claim["source"]],
         "disclosure": "Fiction satirique en animation 3D. Le fait cité est réel et sourcé ; le reste est inventé.",
         "editorial_notes": "Écrit automatiquement (format v4), sélectionné par un critique automatique."}
    s["word_count"] = sum(len(x["text"].split()) for x in segs)
    return s


def check(s: dict, claim: dict) -> list[str]:
    errs = list(viral_lint.check(s)["blocking"])
    fl = [n for n in s["narration_segments"] if n["claim_type"] != "fiction_satirique"]
    if len(fl) != 1:
        errs.append("une et une seule réplique doit porter le fait réel")
    elif not fact_ok(fl[0]["text"], claim["text"]):
        errs.append(f"fait déformé : la réplique doit reprendre exactement {_keys(claim['text'])}")
    if not 75 <= s["word_count"] <= 95:
        errs.append(f"{s['word_count']} mots (75 à 95)")
    try:
        ed = editorial.check(planner_v2.plan(s))
        if ed.get("decision") != "pass":
            errs.append(f"éditorial : {ed.get('decision')} {ed.get('review') or ed.get('blocking') or ''}")
    except Exception as e:
        errs.append(f"plan impossible : {type(e).__name__} {e}")
    return errs


def reference_text() -> str:
    out = []
    for r in REFERENCES:
        f = SCRIPTS / "bank_ultra" / f"{r}.json"
        if f.exists():
            s = json.loads(f.read_text(encoding="utf-8"))
            out.append(f"« {s['title_cover']} » — situation : {s.get('situation', '')}\n" + "\n".join(
                f"  [{n.get('lien') or n.get('role') or 'cta'}] {n['text']}" for n in s["narration_segments"]))
    return "\n\n".join(out)


def write_one(city: str, claim: dict, sid: str, avoid: list[str]) -> dict | None:
    base = CONSIGNES.format(rival=RIVAL_CAMP.get(city, "le camp adverse"), cameras=", ".join(CAMERAS),
                            decors=", ".join(DECORS), gestes=", ".join(sorted(planner_v2.GESTES)),
                            visages=", ".join(sorted(planner_v2.VISAGES)), objets=", ".join(sorted(planner_v2.OBJETS)),
                            animaux=", ".join(ANIMAUX), persos=", ".join(PERSOS))
    feedback = ""
    for tour in range(3):
        prompt = (base + "\n\nSCRIPTS DE RÉFÉRENCE (le niveau attendu, ne les copie pas) :\n" + reference_text()
                  + f"\n\nPOLITICIEN : {NAMES.get(city, city)}\nFAIT RÉEL À UTILISER (à reprendre fidèlement) :\n"
                  + f"« {claim['text']} » (source : {claim['source']})"
                  + ("\n\nSITUATIONS DÉJÀ UTILISÉES (trouve autre chose) : " + " ; ".join(avoid[-25:]) if avoid else "")
                  + feedback + "\n\nÉcris 3 versions TRÈS DIFFÉRENTES (3 situations différentes).\n" + FORMAT)
        versions = gemini(prompt, 1.0).get("versions", [])[:3]
        cands = []
        for k, v in enumerate(versions):
            s = to_script(v, city, sid, claim)
            errs = check(s, claim)
            if errs:
                log(f"version {k} refusée : {errs[:2]}")
            else:
                cands.append((k, s))
        if not cands:
            feedback = "\n\nTES VERSIONS PRÉCÉDENTES ONT ÉTÉ REFUSÉES (respecte TOUTES les règles, en particulier le fait exact, 75-92 mots, liens mais/donc)."
            continue
        txt = "\n\n".join(f"VERSION {k} — « {s['title_cover']} » ({s['situation']})\n" + "\n".join(
            f"  [{n.get('lien') or n.get('role') or 'cta'}] {n['text']}" for n in s["narration_segments"]) for k, s in cands)
        notes = {n["version"]: n for n in gemini(JUGE + "\n\n" + txt, 0.2).get("notes", [])}
        best = max(cands, key=lambda c: float(notes.get(c[0], {}).get("global", 0)))
        nb = notes.get(best[0], {})
        log(f"tour {tour + 1} : meilleure version {best[0]} « {best[1]['title_cover']} » note {nb.get('global')} — {nb.get('critique', '')}")
        if float(nb.get("global", 0)) >= NOTE_MIN and float(nb.get("drole", 0)) >= NOTE_MIN - 0.5:
            best[1]["notes_critique"] = {k: nb.get(k) for k in ("drole", "absurde", "situation", "enchainement",
                                                                   "accroche", "chute", "provocation", "visuel", "global")}
            return best[1]
        feedback = (f"\n\nLE CRITIQUE A JUGÉ TES VERSIONS PAS ASSEZ BONNES (meilleure : {nb.get('global')}/10, "
                    f"« {nb.get('critique', '')} »). Plus drôle, plus absurde, chute plus cinglante, situation plus précise.")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--stock", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if not config.get("GEMINI_API_KEY"):
        log("clé GEMINI_API_KEY absente")
        return 0
    scripts = all_scripts()
    st = stock(scripts, produced())
    total = sum(len(v) for v in st.values())
    log(f"stock v4 à fabriquer : {total} {dict((k, len(v)) for k, v in st.items())}")
    if total >= a.stock and not a.force:
        log("stock suffisant : rien à écrire")
        return 0
    used = set(json.loads(USED.read_text(encoding="utf-8"))) if USED.exists() else set()
    used |= {s["anchor"] for s in scripts if s.get("format_v4") and s.get("anchor")}
    pool = fact_pool(scripts)
    avoid = [s.get("situation", "") for s in scripts if s.get("format_v4") and s.get("situation")]
    journal = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    written = 0
    for _ in range(a.n * 2):
        if written >= a.n:
            break
        city = min(MAIN, key=lambda c: (len(st.get(c, [])), random.random()))   # la ville la moins fournie
        facts = [c for t, c in pool.get(city, {}).items() if t not in used]
        if not facts:
            log(f"{city} : plus de fait sourcé inutilisé")
            MAIN.remove(city)
            continue
        claim = random.choice(facts)
        nums = [int(re.sub(r"\D", "", Path(p).stem.split("-a")[-1]) or 0)
                for p in glob.glob(str(AUTO / city / f"{PREFIX[city]}-a*.json"))]
        sid = f"{PREFIX[city]}-a{max(nums, default=0) + 1:03d}"
        log(f"{sid} : {NAMES[city]} — fait : {claim['text'][:90]}")
        try:
            s = write_one(city, claim, sid, avoid)
        except RuntimeError as e:          # Gemini indisponible : on s'arrête, le fait reste disponible
            log(f"arrêt : {e}")
            break
        used.add(claim["text"].strip())    # fait consommé (script écrit, ou refusé par le critique 3 fois)
        journal.append({"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "id": sid,
                        "fait": claim["text"], "ok": bool(s), "titre": s and s["title_cover"],
                        "notes": s and s.get("notes_critique")})
        if s:
            (AUTO / city).mkdir(parents=True, exist_ok=True)
            (AUTO / city / f"{sid}.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
            st.setdefault(city, []).append(sid)
            avoid.append(s["situation"])
            written += 1
            log(f"{sid} écrit : « {s['title_cover']} »")
    USED.write_text(json.dumps(sorted(used), ensure_ascii=False, indent=1), encoding="utf-8")
    LOG.write_text(json.dumps(journal[-300:], ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{written} script(s) écrit(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
