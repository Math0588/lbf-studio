"""Planificateur automatique : script (auteur ou modèle local) → épisode rendable (décor, plans caméra, textes).

Principe : chaque ville utilise le même kit et la même disposition de « scènes de gag » (spots), avec sa propre
ambiance. Chaque plan du script reçoit un spot ; ses accessoires y sont disposés selon une grille fixe et la
caméra suit un gabarit du type demandé (descend, street_dolly, closeup, orbit, window_pass, return).
Le planificateur ne peut utiliser que des accessoires du catalogue ; une demande d'asset inconnu est signalée
(`new_asset_requests`) et remplacée par un panneau-texte, jamais promise silencieusement.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from . import config

CATALOG = {"ground", "road", "roundabout", "building", "mairie", "facade_set", "ring_light", "studio_light",
           "tripod_camera", "sign", "car", "car_orbit", "bus", "tree", "lamp", "bench", "bin", "shop", "tshirt",
           "mascot", "gps", "screen", "text3d", "person", "tribune", "lift_tribune", "table", "form_stack",
           "traffic_light", "router_lectern", "scroll", "banner", "column", "arch", "fountain", "facade_row"}
LAYOUT_ONLY = {"ground", "road", "roundabout", "building", "mairie", "shop", "lamp", "tree", "car_orbit",
               "facade_set", "facade_row"}
TEXT_PROPS = {"sign", "screen", "gps", "text3d", "banner", "scroll", "bus"}

# Ambiances (choix de fiction, pas une classification des personnes)
STYLES = {
    "bardellaville": {"sky": "#9CC9F2", "ground": "#8FB477", "mairie": "#F3E7D3", "mairie_style": "mairie",
                      "bld": ["#E8D8BF", "#D9E2EA", "#EBD3C8", "#F0E3C8"], "sign_bg": "#FFFDF7",
                      "signature": [{"type": "ring_light", "radius": 4.5, "height": 4.0, "emit": 20}]},
    "melenchonville": {"sky": "#F2C9A0", "ground": "#9FA978", "mairie": "#E9D2C0", "mairie_style": "classic",
                       "bld": ["#D9B8A3", "#E6CDB5", "#C9A58C", "#EBD9C6"], "sign_bg": "#7A1E2C", "sun_color": "#FFD9B0",
                       "signature": [{"type": "tribune", "scale": 2.2, "color": "#7A1E2C"}]},
    "macronville": {"sky": "#BFE0FF", "ground": "#A3BF8E", "mairie": "#DDE8F2", "mairie_style": "modern",
                    "bld": ["#CFE0EE", "#E6EEF5", "#BCD3E6", "#F2F5F8"], "sign_bg": "#1649FF",
                    "signature": [{"type": "arch", "radius": 3.5, "color": "#1649FF", "text": "INAUGURATION"}]},
    "zemmourville": {"sky": "#E9D8B4", "ground": "#A79F72", "mairie": "#CFC6B4", "mairie_style": "castle",
                     "bld": ["#CDBFA3", "#BFAF8E", "#D8CCB2", "#B8A68A"], "sign_bg": "#3A2A1A", "sun_color": "#FFE3B0",
                     "signature": [{"type": "scroll", "length": 3.5, "text": "C'ÉTAIT MIEUX AVANT", "scale": 1.6}]},
    "marineville": {"sky": "#B4D4F0", "ground": "#93AD80", "mairie": "#EFE8DA", "mairie_style": "plain",
                    "bld": ["#E4DCCB", "#D3DCE6", "#EAD8D8", "#DDE4D2"], "sign_bg": "#1649FF",
                    "signature": [{"type": "sign", "w": 6, "h": 2.4, "z": 3,
                                   "lines": [{"text": "NOUVEAU NOM", "size": 0.55}]}]},
    "glucksmannville": {"sky": "#D9E4EA", "ground": "#B3BC9E", "mairie": "#EDE3D3", "mairie_style": "plain",
                        "bld": ["#E8DFD0", "#DCD6CB", "#E5E1D8", "#D8D2C2"], "sign_bg": "#B9A68A",
                        "signature": [{"type": "screen", "w": 5, "h": 3, "z": 3.5, "text": "IL FAUT UN CAP CLAIR"}]},
}

# Spots (centres des scènes de gag). La caméra arrive toujours par le sud (-Y) : couloirs dégagés.
SPOTS = [(0, -46), (0, 40), (-44, 0), (44, 0), (-44, -46), (0, -90)]
SHOP_SPOT = (44, -44)


def city_set(city: str) -> dict:
    """Décor de base d'une ville (persistant). Si content/sets/<ville>.json existe, il fait foi."""
    p = config.CONTENT / "sets" / f"{city}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    st = STYLES[city]
    s = [{"type": "ground", "size": 300, "color": st["ground"]},
         {"type": "roundabout", "id": "rp_central", "at": [0, 0], "radius": 12, "island": 6.5}]
    for a, b in (((0, 12), (0, 34)), ((0, -12), (0, -120)), ((12, 0), (120, 0)), ((-12, 0), (-120, 0))):
        s.append({"type": "road", "start": list(a), "end": list(b), "width": 7})
    s.append({"type": "car_orbit", "id": "orbit", "center": [0, 0], "radius": 9.3, "count": 6, "period": 20})
    s.append({"type": "mairie", "id": "mairie", "at": [0, 52], "width": 20, "height": 11, "color": st["mairie"],
              "style": st["mairie_style"], "label": "MAIRIE", "struts": False})
    bl = st["bld"]
    for i, (x, y, h) in enumerate([(-24, 22, 14), (24, 22, 12), (-24, -24, 16), (24, -24, 13), (-66, 22, 11),
                                   (66, 22, 12), (-66, -22, 14), (66, -26, 10), (-26, 64, 12), (26, 64, 13),
                                   (-24, -70, 12), (24, -72, 15)]):
        s.append({"type": "building", "at": [x, y], "size": [14, 12, h], "color": bl[i % len(bl)]})
    s.append({"type": "shop", "id": "boutique", "at": [SHOP_SPOT[0], SHOP_SPOT[1] + 5], "size": [11, 7, 6.5],
              "name": "BOUTIQUE"})
    for (x, y) in [(-15, 15), (15, 15), (-15, -15), (15, -15), (-34, 8), (34, 8), (-10, 60), (10, 60), (34, -34)]:
        s.append({"type": "tree", "at": [x, y], "height": 4.5})
    for (x, y) in [(-5, -18), (5, -32), (17, -5), (-17, 5), (-5, 20)]:
        s.append({"type": "lamp", "at": [x, y]})
    sig = dict(st["signature"][0])
    sig.update(id="signature", at=[0, 0])
    s.append(sig)
    return {"city": city, "generated": True,
            "mood": {"sky": st["sky"], "sky_strength": 1.15, "sun_energy": 4.4, "sun_color": st.get("sun_color", "#FFF0DA"),
                     "sun_rot": [50, 6, 30], "sun_soft": 5}, "set": s}


def _wrap_lines(text: str, n: int = 14) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:3]


def _prop_name(x) -> str:
    return x if isinstance(x, str) else x.get("type", "")


def _camera(kind: str, c, first_keys=None):
    cx, cy = c
    if kind == "return" and first_keys:
        return first_keys
    if kind == "descend":
        return [{"t": 0, "loc": [cx + 10, cy - 24, 20], "look": [cx, cy, 3]},
                {"t": 1, "loc": [cx + 3, cy - 13, 6], "look": [cx, cy, 3]}]
    if kind in ("street_dolly", "window_pass"):
        z = 2.2 if kind == "window_pass" else 3
        return [{"t": 0, "loc": [cx - 4, cy - 22, z], "look": [cx, cy, 2.5]},
                {"t": 1, "loc": [cx - 1.2, cy - 11, z], "look": [cx, cy + 1, 2.5]}]
    if kind == "closeup":
        return [{"t": 0, "loc": [cx + 1.6, cy - 8.5, 3.2], "look": [cx, cy + 1, 2.4]},
                {"t": 1, "loc": [cx + 0.8, cy - 6.8, 2.9], "look": [cx, cy + 1, 2.4]}]
    if kind == "orbit":
        keys = []
        for t, a in ((0, -130), (0.5, -95), (1, -60)):
            r = math.radians(a)
            keys.append({"t": t, "loc": [cx + 11 * math.cos(r), cy + 11 * math.sin(r), 5.5], "look": [cx, cy, 2.5]})
        return keys
    return [{"t": 0, "loc": [cx, cy - 14, 4], "look": [cx, cy, 2.5]},
            {"t": 1, "loc": [cx, cy - 11, 3.6], "look": [cx, cy, 2.5]}]


SLOTS = [(0, 0), (-3.6, 1.2), (3.6, 1.2), (-2, -1.8), (2, -1.8), (0, 3)]


def _place(props: list, spot, text: str, sid: str, st: dict, warnings: list, events: list, dur_hint: str):
    out = []
    used_text = False
    cx, cy = spot
    names = []
    for x in props:
        n = _prop_name(x)
        if n not in CATALOG:
            warnings.append(f"{sid} : accessoire hors catalogue « {n} » → remplacé par un panneau")
            n = "sign"
        if n in LAYOUT_ONLY or n in names:
            continue
        names.append(n)
    if text and not any(n in TEXT_PROPS for n in names):
        names.insert(1 if names else 0, "sign")
    # un accessoire à texte sans texte disponible n'apporte rien : on l'écarte
    keep, has_text = [], bool(text)
    for n in names:
        if n in ("text3d", "screen", "gps", "scroll", "sign") and not has_text:
            continue
        if n in ("text3d", "screen", "gps", "scroll", "sign") and any(k in TEXT_PROPS - {"banner", "bus"} for k in keep):
            continue
        keep.append(n)
    names = keep
    for i, n in enumerate(names[:6]):
        dx, dy = SLOTS[i]
        pid = f"{sid}_{n}_{i}"
        p = {"type": n, "id": pid, "at": [cx + dx, cy + dy]}
        if n in TEXT_PROPS and text and not used_text:
            used_text = True
            if n == "sign":
                p.update(w=6.4, h=2.8, z=1.4, bg=st["sign_bg"],
                         lines=[{"text": l, "size": 0.6, "color": "#111827" if st["sign_bg"] in ("#FFFDF7",) else "#FFFDF7",
                                 "emit": 0.0 if st["sign_bg"] == "#FFFDF7" else 1.0} for l in _wrap_lines(text.upper())])
                p["at"] = [cx + (dx if i else 0), cy + 3.2]
            elif n in ("screen", "gps"):
                p.update(text=text, z=2.0 if n == "screen" else 1.2)
                p["at"] = [cx + (dx if i else 0), cy + 3.2]
            elif n == "text3d":
                p.update(text="\n".join(_wrap_lines(text.upper(), 16)), size=0.8, color="#FFFDF7", emit=1.5,
                         at=[cx, cy + 3, 4.5])
            else:
                p["text"] = text.upper()[:40]
        if n == "person":
            p["color"] = ["#1649FF", "#E0A458", "#2E8B57", "#EF233C"][i % 4]
        if n == "mascot":
            p["shirt"] = {"color": "#111827", "lines": ["LE PAYS BUGUE.", "MOI AUSSI."]}
        if n == "tshirt":
            p.update(at=[cx + dx, cy + dy, 2.2], color="#F3EBDD")
        if n == "car":
            p["rot"] = 90
        if n == "lift_tribune":
            events.append({"type": "move", "target": pid + "_plat", "to": [0, 0, 5], "shot": sid, "at": 0.2,
                           "dur": 2.5})
        out.append(p)
    return out


def plan(script: dict) -> dict:
    """Retourne un épisode (contrat episode.json) prêt pour lbf.produce."""
    city = script["city"]
    st = STYLES[city]
    warnings, events, extra = [], [], []
    scenes = []
    first_keys = None
    spot_i = 0
    n = len(script["scenes"])
    for k, sc in enumerate(script["scenes"]):
        kind = sc.get("camera", "street_dolly")
        is_cta = k == n - 1 and script.get("cta_commercial")
        if is_cta:
            spot = SHOP_SPOT
            keys = [{"t": 0, "loc": [spot[0] + 0.5, spot[1] - 14, 4.4], "look": [spot[0], spot[1] + 1, 3.0]},
                    {"t": 1, "loc": [spot[0] + 0.4, spot[1] - 10, 3.6], "look": [spot[0], spot[1] + 1, 2.8]}]
            prod = (script.get("cta_commercial") or {}).get("product_id", "tee-pays-bugue")
            slogan = {"tee-pays-bugue": ["LE PAYS BUGUE.", "MOI AUSSI."],
                      "tee-avis-mandat": ["J'AI UN AVIS.", "PAS DE MANDAT."],
                      "tee-gauche-canape": ["À GAUCHE", "DU CANAPÉ."], "tee-droite-canape": ["À DROITE", "DU CANAPÉ."],
                      "tee-gauche-fatigue": ["PLUTÔT GAUCHE.", "TRÈS FATIGUÉ."],
                      "tee-droite-fatigue": ["PLUTÔT DROITE.", "TRÈS FATIGUÉ."]}.get(prod, ["LE PAYS BUGUE.", "MOI AUSSI."])
            extra += [{"type": "mascot", "id": f"{sc['id']}_coq", "at": [spot[0] - 2.5, spot[1], 0.95], "rot": 10,
                       "scale": 0.82, "shirt": {"color": "#111827", "lines": slogan}},
                      {"type": "tshirt", "id": f"{sc['id']}_tee", "at": [spot[0] + 3, spot[1], 2.6], "rot": -8,
                       "scale": 0.9, "color": "#F3EBDD", "lines": slogan, "text_color": "#1649FF"}]
        else:
            if kind == "return" and first_keys:
                spot = SPOTS[0]
            else:
                spot = SPOTS[spot_i % len(SPOTS)]
                spot_i += 1
            keys = _camera(kind, spot, first_keys)
            extra += _place(sc.get("set", []), spot, sc.get("onscreen_text", ""), sc["id"], st, warnings, events,
                            kind)
        if sc.get("new_asset_request"):
            warnings.append(f"{sc['id']} : nouvel asset demandé — {sc['new_asset_request']}")
        if first_keys is None:
            first_keys = keys
        scenes.append({**sc, "keys": keys, "lens": {"descend": 22, "closeup": 32, "orbit": 26}.get(kind, 28),
                       "lead_in": 0.3 if k == 0 else 0.12, "tail": 0.9 if k == n - 1 else 0.3})
    ep = {
        "id": script["id"], "version": 1, "city_id": city, "season": 1,
        "episode_number": int(re.search(r"e(\d+)$", script["id"]).group(1)) if re.search(r"e(\d+)$", script["id"]) else 0,
        "format": script.get("format", "A"), "title_cover": script["title_cover"],
        "hook_variants": script.get("hook_variants", []), "selected_hook": script.get("selected_hook", 0),
        "ending_variants": script.get("ending_variants", []), "selected_ending": script.get("selected_ending", 0),
        "narration_segments": script["narration_segments"], "scenes": scenes, "events": events,
        "extra_set": extra, "stills": [{"name": "still_cover", "shot": scenes[min(len(scenes) - 2, 2)]["id"], "at": 0.6}],
        "cta_primary": script.get("cta_primary"), "cta_commercial": script.get("cta_commercial"),
        "sources": script.get("sources", []), "claims": script.get("claims", []),
        "product_ids": [(script.get("cta_commercial") or {}).get("product_id")],
        "disclosure": script.get("disclosure", ""),
        "editorial_status": "scripted", "render_profile": "final", "scheduled_at": None,
        "planner_warnings": warnings, "synopsis_id": script.get("synopsis_id"),
        "editorial_notes": script.get("editorial_notes", ""),
    }
    ep["caption"] = caption(ep)
    return ep


def caption(ep: dict) -> str:
    from .produce import CITY_NAMES
    city = CITY_NAMES.get(ep["city_id"], ep["city_id"])
    cta = (ep.get("cta_primary") or {}).get("text", "")
    tags = "#satire #humour #politique #france #3D #blender #lebordelfrancais"
    return (f"{city}, épisode {ep['episode_number']} : {ep['title_cover'].lower()}.\n\n{cta}\n\n"
            f"👕 La collection du compte est en bio.\n\n"
            f"{tags}")


def ensure_city_set(city: str) -> Path:
    p = config.CONTENT / "sets" / f"{city}.json"
    if not p.exists():
        p.write_text(json.dumps(city_set(city), ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def plan_file(script_path: Path) -> Path:
    s = json.loads(Path(script_path).read_text(encoding="utf-8"))
    ensure_city_set(s["city"])
    ep = plan(s)
    out = config.CONTENT / "episodes" / f"{ep['id']}.json"
    out.write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys
    for a in sys.argv[1:]:
        o = plan_file(Path(a))
        e = json.loads(o.read_text(encoding="utf-8"))
        print(o.name, "avertissements :", e["planner_warnings"])
