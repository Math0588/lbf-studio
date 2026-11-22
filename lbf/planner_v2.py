"""Planificateur v2 — script → épisode au format des Reels viraux (personnages cubiques expressifs, coupes de
1,5–3 s, sous-titres mot à mot, étiquettes, bulles du maire, carte de fin).

Règles appliquées (docs/TENDANCES_VIRALES.md, docs/VIRALITE_SCIENCE.md) : un visage dès la 1re seconde, un plan
par phrase, alternance plan large / gros plan, texte écran du script → étiquette rouge inclinée, réplique entre
guillemets → bulle, fin sur « ABONNE-TOI » + teaser de la ville suivante. Le maire est un personnage cubique
générique (jamais un visage réaliste) ; ses bulles ne sont jamais présentées comme des citations réelles."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from . import config
from .planner import CATALOG, SHOP_SPOT, _wrap_lines

PASTEL = ["#F6E3C5", "#DDEBF7", "#F7D9D9", "#E3F2D9", "#FFF1B8", "#E8DDF5", "#FCE1C8"]

# Maires : silhouettes génériques par ville (couleurs, coiffure) — choix de fiction, pas des portraits.
MAYORS = {
    "bardellaville": {"suit": True, "sash": True, "shirt": "#1B2A4A", "pants": "#1B2A4A", "tie": "#1649FF",
                      "hair": "plaque", "hair_color": "#1C1C1C", "faces": ["sourire_pro", "parle_fier", "fier"]},
    "melenchonville": {"suit": True, "sash": True, "shirt": "#3A3A3A", "pants": "#2B2B2B", "tie": "#B01E2F",
                       "hair": "chauve_cotes", "hair_color": "#BDBDBD", "glasses": True,
                       "faces": ["colere", "parle", "fier"]},
    "macronville": {"suit": True, "sash": True, "shirt": "#1F3B73", "pants": "#1F3B73", "tie": "#0B1B3F",
                    "hair": "court", "hair_color": "#6B4A2F", "iris": "bleu", "faces": ["sourire_pro", "parle", "fier"]},
    "zemmourville": {"suit": True, "sash": True, "shirt": "#2B2B33", "pants": "#2B2B33", "tie": "#5A1E2C",
                     "hair": "chauve_cotes", "hair_color": "#3A3A3A", "glasses": True,
                     "faces": ["blase", "parle", "colere"]},
    "marineville": {"suit": True, "sash": True, "shirt": "#22306B", "pants": "#22306B", "tie": "#22306B",
                    "hair": "long", "hair_color": "#E2C27A", "iris": "bleu", "faces": ["sourire_pro", "parle", "fier"]},
    "glucksmannville": {"suit": True, "sash": True, "shirt": "#C8B79A", "pants": "#8A7B64", "tie": "#B9A68A",
                        "hair": "meche", "hair_color": "#4A3626", "iris": "bleu", "faces": ["neutre", "parle", "blase"]},
}
NEXT_CITY = {"bardellaville": "Macronville", "macronville": "Mélenchonville", "melenchonville": "Zemmourville",
             "zemmourville": "Marineville", "marineville": "Glucksmannville", "glucksmannville": "Bardellaville"}
SPOTS = [(0, -50), (0, 40), (-44, 0), (44, 0), (-40, -50), (0, -92)]
SHIRTS = ["#5B8DEF", "#F2B134", "#EF6F6C", "#7BC47F", "#B983FF", "#2EC4B6", "#F78FB3", "#FFFDF7"]
HAIRS = ["court", "meche", "herisse", "long", "chignon", "casquette", "beret"]
SKINS = ["#F1C9A5", "#E0AC7E", "#C68642", "#8D5524", "#F6D7B0"]


def mood_of(text: str) -> str:
    t = text.lower()
    if re.search(r"\?|quoi|comment|vraiment|pardon", t):
        return "choque"
    if re.search(r"fatigu|attend|toujours|encore|depuis|personne|rien|vide|dort|ennui", t):
        return "blase"
    if re.search(r"pire|marre|colère|scandale|non\b|interdit|refus", t):
        return "colere"
    if re.search(r"bravo|inaugur|fier|génial|parfait|offert|gagn|nouveau|record", t):
        return "fier"
    return "content"


def city_set_v2(city: str) -> dict:
    from .planner import STYLES
    st = STYLES[city]
    s = [{"type": "ground", "size": 320, "color": "#5DBB4A"},
         {"type": "roundabout", "id": "rp_central", "at": [0, 0], "radius": 12, "island": 6.5, "island_color": "#6ACB55"}]
    for a, b in (((0, 12), (0, 34)), ((0, -12), (0, -120)), ((12, 0), (120, 0)), ((-12, 0), (-120, 0))):
        s.append({"type": "road", "start": list(a), "end": list(b), "width": 8})
    s.append({"type": "car_orbit", "id": "orbit", "center": [0, 0], "radius": 9.3, "count": 6, "period": 20,
              "colors": ["#EF233C", "#FFFDF7", "#1649FF", "#F2B134", "#2E8B57", "#F78FB3"]})
    s.append({"type": "mairie", "id": "mairie", "at": [0, 54], "width": 20, "height": 11, "color": st["mairie"],
              "style": st["mairie_style"], "label": "MAIRIE", "struts": False})
    for i, y in enumerate(range(-24, -112, -13)):
        for side in (-1, 1):
            if abs(y + 50) < 7 or abs(y + 92) < 7:
                continue  # dégage les scènes de gag
            s.append({"type": "house", "at": [side * 14, y], "rot": 90 * side, "size": [8, 7, 4.6],
                      "color": PASTEL[(i * 2 + (side > 0)) % len(PASTEL)], "roof": "#D9483B"})
    for y in range(-20, -112, -18):
        for side in (-1, 1):
            s.append({"type": "flag", "at": [side * 6.2, y], "height": 5.5, "w": 1.8})
    bl = st["bld"]
    for i, (x, y, h) in enumerate([(-26, 24, 14), (26, 24, 12), (-66, 22, 11), (66, 22, 12), (-26, 66, 12),
                                   (26, 66, 13), (-66, -24, 14), (66, -26, 10)]):
        s.append({"type": "building", "at": [x, y], "size": [12, 10, h], "color": bl[i % len(bl)], "roof": "#7A6558"})
    s.append({"type": "shop", "id": "boutique", "at": [SHOP_SPOT[0], SHOP_SPOT[1] + 5], "size": [11, 7, 6.5],
              "name": "BOUTIQUE", "color": "#FFF3DC"})
    for (x, y) in [(-15, 15), (15, 15), (-15, -14), (15, -14), (-34, 8), (34, 8), (-10, 62), (10, 62)]:
        s.append({"type": "tree", "at": [x, y], "height": 4.8, "color": "#3FA34D"})
    sig = dict(st["signature"][0])
    sig.update(id="signature", at=[0, 0])
    s.append(sig)
    return {"city": city, "version": 2, "generated": True,
            "mood": {"view": "Standard", "sky": "#8CCBFF", "sky_strength": 0.9, "sun_energy": 3.4,
                     "sun_color": st.get("sun_color", "#FFF4E0"), "sun_rot": [45, 8, 38], "sun_soft": 6}, "set": s}


def ensure_set_v2(city: str) -> None:
    p = config.CONTENT / "sets" / f"{city}.json"
    if p.exists() and json.loads(p.read_text(encoding="utf-8")).get("version") == 2:
        return
    if p.exists():
        p.rename(p.with_name(f"{city}_v1.json"))
    p.write_text(json.dumps(city_set_v2(city), ensure_ascii=False, indent=1), encoding="utf-8")


def _char(cid, at, rot, rnd, faces, **kw):
    d = {"type": "char", "id": cid, "at": at, "rot": rot, "faces": faces, "shirt": rnd.choice(SHIRTS),
         "skin": rnd.choice(SKINS), "hair": rnd.choice(HAIRS), "iris": rnd.choice(["brun", "bleu", "vert"]),
         "hair_color": rnd.choice(["#2B1D14", "#6B4423", "#C9A15B", "#1C1C1C", "#8A8A8A", "#B5542C"])}
    d.update(kw)
    return d


TEE_LINES = ["LE PAYS BUGUE.", "MOI AUSSI."]


def product_for(script: dict) -> str:
    """T-shirt de l'épisode : celui du script s'il fait partie de la série « cauchemar », sinon celui qui vise
    le politicien de la ville (champ « cities » de content/products.json)."""
    pid = (script.get("cta_commercial") or {}).get("product_id") or ""
    try:
        prods = json.loads((config.CONTENT / "products.json").read_text(encoding="utf-8"))
    except Exception:
        return pid or "tee-pays-bugue"
    if any(p["id"] == pid and p.get("lines") for p in prods):
        return pid
    for p in prods:
        if script.get("city") in p.get("cities", []):
            return p["id"]
    return pid or "tee-pays-bugue"


def slogan_of(prod: str) -> list[str]:
    """Lignes du slogan d'un produit (porté par un personnage sur deux scènes : placement, pas matraquage)."""
    try:
        for p in json.loads((config.CONTENT / "products.json").read_text(encoding="utf-8")):
            if p["id"] == prod and p.get("lines"):
                return list(p["lines"])
            if p["id"] == prod:
                parts = [x.strip() for x in p["slogan"].replace(". ", ".|").split("|") if x.strip()]
                if len(parts) == 1:
                    w = parts[0].split()
                    parts = [" ".join(w[: (len(w) + 1) // 2]), " ".join(w[(len(w) + 1) // 2:])]
                return parts[:2]
    except Exception:
        pass
    return ["LE PAYS BUGUE.", "MOI AUSSI."]


def sticker_text(onscreen: str, segs: list[dict]) -> str:
    """Étiquette rouge cohérente avec ce qui est dit : le texte écran du script s'il partage au moins un mot fort
    avec la narration de la scène (ou contient un chiffre), sinon les mots d'accent de la scène."""
    from .antirepeat import words
    said = " ".join(s["text"] for s in segs)
    if onscreen and (set(words(onscreen)) & set(words(said)) or re.search(r"\d", onscreen)):
        return onscreen
    acc = [a for s in segs for a in s.get("accent_words", []) if a]
    return acc[-1].upper() if acc else ""


def _quote(text: str) -> str | None:
    m = re.search(r"«\s*([^»]{3,60})\s*»", text)
    return m.group(1).strip() if m else None


def plan(script: dict) -> dict:
    city = script["city"]
    ensure_set_v2(city)
    rnd = random.Random(script["id"])
    segs = {s["id"]: s for s in script["narration_segments"]}
    extra, events, stickers, bubbles, shots, warnings = [], [], [], [], [], []
    global TEE_LINES
    PRODUCT = product_for(script)
    TEE_LINES = slogan_of(PRODUCT)
    mayor_spot = None
    n_sc = len(script["scenes"])
    first_close_done = False
    for k, sc in enumerate(script["scenes"]):
        is_cta = k == n_sc - 1
        spot = SPOTS[k % len(SPOTS)]
        cx, cy = spot
        props = [p if isinstance(p, str) else p.get("type", "") for p in sc.get("set", [])]
        unknown = [p for p in props if p and p not in CATALOG]
        if unknown:
            warnings.append(f"{sc['id']} : accessoires hors catalogue ignorés {unknown}")
        text_all = " ".join(segs[n]["text"] for n in sc["narration_ids"] if n in segs)
        has_mayor = bool({"tribune", "lift_tribune", "mairie"} & set(props)) or re.search(r"\bmaire\b", text_all, re.I)
        # décor de la scène : 1 à 2 accessoires du catalogue derrière les personnages
        for i, pn in enumerate([p for p in props if p in CATALOG and p not in
                                {"ground", "road", "roundabout", "building", "mairie", "shop", "lamp", "tree",
                                 "car_orbit", "facade_row", "person", "mascot", "tshirt", "text3d", "sign",
                                 "tribune", "lift_tribune"}][:2]):
            d = {"type": pn, "id": f"{sc['id']}_{pn}", "at": [cx + (-4.5 if i == 0 else 4.5), cy + 3.5]}
            if pn in ("screen", "gps"):
                d.update(text=sc.get("onscreen_text") or " ", z=2.6)
            if pn in ("banner", "scroll", "bus") and sc.get("onscreen_text"):
                d["text"] = sc["onscreen_text"].upper()[:30]
            if pn == "car":
                d["rot"] = 90
            extra.append(d)
        hero = f"{sc['id']}_hero"
        mood = mood_of(text_all)
        if has_mayor:
            mayor_spot = spot
            extra.append({"type": "tribune", "id": f"{sc['id']}_pupitre", "at": [cx, cy + 0.9], "scale": 1.25,
                          "color": "#1649FF"})
            extra.append({"type": "char", "id": f"{sc['id']}_maire", "at": [cx, cy + 2.0], **MAYORS[city]})
            extra.append({"type": "crowd", "id": f"{sc['id']}_foule", "at": [cx, cy - 9], "count": 8, "cols": 4,
                          "dx": 1.9, "dy": 1.9, "rot": 180, "faces": [rnd.choice(["colere", "choque", "blase"])],
                          "hand_up_ratio": 0.5, "seed": k + 3})
            extra.append(_char(hero, [cx - 1.6, cy - 4.0], 182, rnd, [mood, "choque"], hand_up=True))
        else:
            extra.append(_char(hero, [cx, cy], 0, rnd, [mood, "choque" if mood != "choque" else "blase"],
                               hold=rnd.choice([None, None, "phone", "verre", "baguette"])))
            wear = {} if k % 2 else {"shirt": "#111827", "tee": {"lines": TEE_LINES, "ink": "#FFFDF7", "size": 0.13}}
            extra.append(_char(f"{sc['id']}_b", [cx - 2.4, cy + 1.6], 15, rnd, [rnd.choice(["blase", "content", "neutre"])],
                               **wear))
            extra.append(_char(f"{sc['id']}_c", [cx + 2.5, cy + 1.2], -20, rnd, [rnd.choice(["blase", "fier", "choque"])]))
        # un plan par phrase, alternance large / gros plan
        for j, nid in enumerate(sc["narration_ids"]):
            sid = f"{sc['id']}{'abcdefgh'[j]}"
            t = segs[nid]["text"] if nid in segs else ""
            wide = (j % 2 == 0 and (k == 0 or sc.get("camera") in ("descend", "orbit", "street_dolly"))) and not (k == 0 and j == 0 and first_close_done)
            if k == 0 and j == 0:
                wide = False  # un visage dès la première seconde
                first_close_done = True
            if has_mayor:
                if j % 2 == 0:
                    keys = [{"t": 0, "loc": [cx + 0.5, cy - 3.4, 3.3], "look": [cx, cy + 2.0, 2.85]},
                            {"t": 1, "loc": [cx + 0.4, cy - 2.8, 3.2], "look": [cx, cy + 2.0, 2.85]}]
                else:
                    keys = [{"t": 0, "loc": [cx - 1.2, cy - 1.2, 2.8], "look": [cx - 1.6, cy - 4.0, 2.6]},
                            {"t": 1, "loc": [cx - 1.3, cy - 1.6, 2.75], "look": [cx - 1.6, cy - 4.0, 2.6]}]
                q = _quote(t)
                if q and j % 2 == 0:
                    bubbles.append({"text": q, "shot": sid, "at": 0.05, "x": 560, "y": 430, "tail": [530, 560]})
                    events.append({"type": "talk", "target": f"{sc['id']}_maire", "rest": MAYORS[city]["faces"][0],
                                   "open": MAYORS[city]["faces"][1], "shot": sid, "at": 0.05, "until": 0.9})
            elif wide:
                keys = [{"t": 0, "loc": [cx + 7, cy - 16, 11], "look": [cx, cy, 1.5]},
                        {"t": 1, "loc": [cx + 4, cy - 11, 6], "look": [cx, cy, 2]}]
            else:
                keys = [{"t": 0, "loc": [cx + 0.6, cy - 3.6, 2.95], "look": [cx, cy, 2.65]},
                        {"t": 1, "loc": [cx + 0.4, cy - 2.9, 2.85], "look": [cx, cy, 2.65]}]
            shots.append({"id": sid, "narration_ids": [nid], "keys": keys, "lens": 26 if wide else 33,
                          "lead_in": 0.08 if shots else 0.05, "tail": 0.12, "dof": False,
                          "comic_action": sc.get("comic_action", "")})
            if j == len(sc["narration_ids"]) - 1 and not has_mayor:
                events.append({"type": "face", "target": hero, "expr": "choque" if mood != "choque" else "blase",
                               "shot": sid, "at": 0.7})
        label = sticker_text(sc.get("onscreen_text", ""), [segs[n] for n in sc["narration_ids"] if n in segs])
        if label:
            stickers.append({"text": label[:28], "shot": shots[-1]["id"] if len(sc["narration_ids"]) == 1
                             else f"{sc['id']}a", "at": 0.25, "x": rnd.choice([520, 560, 600]),
                             "y": rnd.choice([560, 600, 640]), "rot": rnd.choice([-9, -7, 6, 8])})
    # pas d'étiquette sur le 1er plan (accroche écrite) ni sur le dernier (carte de fin) : lisibilité
    if shots:
        first_id, last_id = shots[0]["id"], shots[-1]["id"]
        stickers = [st for st in stickers if st["shot"] not in (first_id, last_id)]
    # insert produit (muet) puis plan final aérien avec carte de fin
    slogan = TEE_LINES
    sx, sy = SHOP_SPOT
    extra += [{"type": "mascot", "id": "coq", "at": [sx - 2.5, sy, 0.95], "rot": 10, "scale": 0.82,
               "shirt": {"color": "#111827", "lines": slogan}},
              {"type": "tshirt", "id": "tee", "at": [sx + 3, sy, 2.6], "rot": -8, "scale": 1.15, "color": "#FFFFFF",
               "lines": slogan, "text_color": "#EF233C"}]
    last_nid = shots[-1]["narration_ids"]
    shots.insert(len(shots) - 1, {"id": "sprod", "narration_ids": [], "dur": 2.8, "lens": 34, "dof": False,
                                  # travelling avant sur le t-shirt (le produit remplit le cadre à la fin du plan)
                                  "keys": [{"t": 0, "loc": [sx + 1.6, sy - 10.0, 3.2], "look": [sx + 2.2, sy + 0.5, 2.5]},
                                           {"t": 1, "loc": [sx + 2.6, sy - 6.6, 2.8], "look": [sx + 2.9, sy + 0.5, 2.55]}]})
    stickers.append({"text": "CE T-SHIRT EXISTE VRAIMENT", "shot": "sprod", "at": 0.05, "x": 540, "y": 430, "rot": -6})
    stickers.append({"text": "LIEN EN BIO", "shot": "sprod", "at": 0.35, "x": 560, "y": 560, "rot": 5})
    shots[-1]["keys"] = [{"t": 0, "loc": [10, -40, 14], "look": [0, -10, 3]}, {"t": 1, "loc": [12, -62, 46], "look": [0, -5, 2]}]
    shots[-1]["lens"] = 24
    shots[-1]["tail"] = 1.6
    num = re.search(r"e(\d+)$", script["id"])
    ep = {
        "id": script["id"], "version": 2, "city_id": city, "season": 1,
        "episode_number": int(num.group(1)) if num else 0, "format": script.get("format", "A"),
        "length": "court", "caption_style": "words", "voice_length_scale": 0.92,
        "title_cover": script["title_cover"], "hook_variants": script.get("hook_variants", []),
        "selected_hook": script.get("selected_hook", 0), "ending_variants": script.get("ending_variants", []),
        "selected_ending": script.get("selected_ending", 0), "narration_segments": script["narration_segments"],
        "scenes": shots, "events": events, "extra_set": extra, "stickers": stickers, "bubbles": bubbles,
        "endcard": {"title": "Abonne-toi", "sub": f"prochaine ville : {NEXT_CITY[city]} · t-shirt en bio", "at": 0.35},
        "stills": [{"name": "still_cover", "shot": shots[0]["id"], "at": 0.6}], "cover_still": "still_cover",
        "cta_primary": script.get("cta_primary"), "cta_commercial": script.get("cta_commercial"),
        "sources": script.get("sources", []), "claims": script.get("claims", []), "product_ids": [PRODUCT],
        "disclosure": "", "editorial_status": "scripted", "render_profile": "final", "scheduled_at": None,
        "planner": "v2", "planner_warnings": warnings, "synopsis_id": script.get("synopsis_id"),
        "editorial_notes": script.get("editorial_notes", ""),
    }
    from . import provocation
    return provocation.apply(ep)


def plan_file(script_path: Path) -> Path:
    s = json.loads(Path(script_path).read_text(encoding="utf-8"))
    ep = plan(s)
    out = config.CONTENT / "episodes" / f"{ep['id']}.json"
    out.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys
    for a in sys.argv[1:]:
        o = plan_file(Path(a))
        e = json.loads(o.read_text(encoding="utf-8"))
        print(o.name, len(e["scenes"]), "plans ; avertissements :", e["planner_warnings"])
