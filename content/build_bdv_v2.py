"""Construit le décor v2 de Bardellaville et l'épisode 1 v2 (réalisation plan par plan, codes des Reels viraux).
Relancer : python content/build_bdv_v2.py"""
import json
from pathlib import Path

C = Path(__file__).resolve().parent
PASTEL = ["#F6E3C5", "#DDEBF7", "#F7D9D9", "#E3F2D9", "#FFF1B8", "#E8DDF5", "#FCE1C8"]

s = [
    {"type": "ground", "size": 320, "color": "#5DBB4A"},
    {"type": "roundabout", "id": "rp_central", "at": [0, 0], "radius": 12, "island": 6.5, "island_color": "#6ACB55"},
    {"type": "road", "start": [0, 12], "end": [0, 24], "width": 7},
    {"type": "road", "start": [0, -12], "end": [0, -120], "width": 8},
    {"type": "road", "start": [12, 0], "end": [120, 0], "width": 7},
    {"type": "road", "start": [-12, 0], "end": [-120, 0], "width": 7},
    {"type": "ring_light", "id": "rl_central", "at": [0, 0], "radius": 5.2, "height": 4.0, "emit": 22, "light_power": 6000},
    {"type": "car_orbit", "id": "orbit", "center": [0, 0], "radius": 9.3, "count": 7, "period": 18, "hero_index": 0,
     "colors": ["#EF233C", "#FFFDF7", "#1649FF", "#F2B134", "#2E8B57", "#8E9AAF", "#F78FB3"],
     "hero_driver": {"faces": ["blase", "fatigue"], "shirt": "#F2B134", "hair": "casquette", "hair_color": "#1649FF",
                     "iris": "bleu"}},
    {"type": "mairie", "id": "mairie", "at": [0, 32], "width": 20, "height": 11, "color": "#FFF3DC", "style": "mairie",
     "label": "MAIRIE", "struts": True},
    {"type": "facade_row", "id": "fonds", "at": [0, 35.8, -20], "count": 11, "spacing": 2.5, "width": 20, "height": 11.5,
     "colors": ["#FFB3B3", "#B3D9FF", "#FFE08A", "#B8F2B0", "#E0C3FF", "#FFC9A3"],
     "styles": ["classic", "modern", "castle", "beach", "factory", "plain"]},
    {"type": "studio_light", "id": "spot_g", "at": [-1.3, 25.2], "height": 3.4, "target": [3.5, 27, 3], "power": 400},
    {"type": "studio_light", "id": "spot_d", "at": [8.3, 25.2], "height": 3.4, "target": [3.5, 27, 3], "power": 400},
    {"type": "tribune", "id": "pupitre", "at": [3.5, 26.2], "scale": 1.25, "color": "#1649FF"},
    {"type": "char", "id": "maire", "at": [3.5, 27.3], "suit": True, "sash": True, "shirt": "#1B2A4A", "pants": "#1B2A4A",
     "tie": "#1649FF", "hair": "plaque", "hair_color": "#1C1C1C", "skin": "#EBC3A0", "iris": "brun",
     "faces": ["sourire_pro", "parle_fier", "fier"]},
    {"type": "sign", "id": "sign_rep", "at": [12.5, 25.0], "w": 6.4, "h": 3.0, "z": 1.6, "bg": "#FFFDF7",
     "lines": [{"text": "RÉPONSES", "size": 0.55, "color": "#111827", "emit": 0.0},
               {"text": "CONCRÈTES", "size": 0.55, "color": "#111827", "emit": 0.0},
               {"variants": ["CHARGEMENT.", "CHARGEMENT..", "CHARGEMENT..."], "size": 0.45, "color": "#EF233C",
                "emit": 0.6}]},
    {"type": "crowd", "id": "foule_mairie", "at": [0, 16], "count": 10, "cols": 5, "dx": 1.9, "dy": 1.9, "rot": 180,
     "faces": ["colere"], "hand_up_ratio": 0.5, "seed": 7},
    {"type": "char", "id": "cit1", "at": [-1.8, 21.0], "rot": 185, "faces": ["colere", "choque"], "shirt": "#EF6F6C",
     "hair": "herisse", "hair_color": "#6B4423", "hand_up": True},
    {"type": "char", "id": "cit2", "at": [2.2, 21.4], "rot": 172, "faces": ["choque", "blase"], "shirt": "#111827", "tee": {"lines": ["EXCELLENTE", "QUESTION."], "ink": "#FFFDF7"},
     "hair": "long", "hair_color": "#C9A15B", "iris": "vert", "skin": "#C68642"},
    # avenue sud : foule qui marche, ring lights à la main
    {"type": "crowd", "id": "foule", "at": [0, -70], "count": 12, "cols": 4, "dx": 1.7, "dy": 1.8, "rot": 180,
     "faces": ["fier"], "hold": "ring_light", "hold_ratio": 0.85, "seed": 3},
    {"type": "char", "id": "heros", "at": [-0.6, -63.2], "rot": 180, "faces": ["fier", "content"], "hold": "ring_light",
     "shirt": "#111827", "tee": {"lines": ["LE PAYS BUGUE.", "MOI AUSSI."], "ink": "#FFFDF7", "size": 0.13}, "hair": "meche", "hair_color": "#C9A15B", "iris": "bleu"},
    # boulangerie (intérieur, zone isolée)
    {"type": "wall", "id": "boul_mur", "at": [80, 84], "w": 14, "h": 6, "color": "#FCE9D2", "sign": "BOULANGERIE",
     "sign_color": "#EF233C"},
    {"type": "counter", "id": "comptoir", "at": [80, 80.2], "w": 5, "price": "2 €"},
    {"type": "char", "id": "boulanger", "at": [80.2, 81.6], "faces": ["sourire_pro", "fier"], "shirt": "#FFFFFF",
     "pants": "#3B3F46", "hair": "beret", "hair_color": "#111827", "iris": "brun", "hold": "baguette"},
    {"type": "ring_light", "id": "rl_boul", "at": [76, 83], "radius": 1.6, "height": 1.2, "emit": 14, "light_power": 300},
    # boutique
    {"type": "shop", "id": "boutique", "at": [24, -20], "size": [11, 7, 6.5], "name": "BOUTIQUE", "color": "#FFF3DC"},
    {"type": "mascot", "id": "coq", "at": [21.5, -25.0, 0.95], "rot": 10, "scale": 0.82,
     "shirt": {"color": "#111827", "lines": ["EXCELLENTE", "QUESTION."]}},
    {"type": "tshirt", "id": "tee_vitrine", "at": [27.0, -25.0, 2.6], "rot": -8, "scale": 0.9, "color": "#F3EBDD",
     "lines": ["EXCELLENTE", "QUESTION."], "text_color": "#111827"},
]
for i, y in enumerate(range(-24, -112, -13)):
    for side in (-1, 1):
        s.append({"type": "house", "at": [side * 13.5, y], "rot": 90 * side, "size": [8, 7, 4.6],
                  "color": PASTEL[(i * 2 + (side > 0)) % len(PASTEL)], "roof": "#D9483B",
                  "poster": "MON\nMEILLEUR\nPROFIL" if (i + (side > 0)) % 2 == 0 else None})
for y in range(-20, -112, -18):
    for side in (-1, 1):
        s.append({"type": "flag", "at": [side * 5.6, y], "height": 5.5, "w": 1.8})
        s.append({"type": "tree", "at": [side * 8.0, y - 7], "height": 4.6, "color": "#3FA34D"})
for (x, y, h, c) in [(36, 24, 15, "#BDE0FE"), (-36, 24, 13, "#FFD6A5"), (-30, -14, 17, "#CAFFBF"),
                     (34, 8, 12, "#FFC6FF"), (-46, 40, 20, "#A0C4FF"), (46, 42, 18, "#FDFFB6")]:
    s.append({"type": "building", "at": [x, y], "size": [12, 10, h], "color": c, "roof": "#7A6558"})
for (x, y) in [(-15, 15), (15, 15), (-15, -12), (12, -12), (-9, 40), (9, 40)]:
    s.append({"type": "tree", "at": [x, y], "height": 4.8, "color": "#3FA34D"})

city = {"city": "bardellaville", "version": 2,
        "note": "Décor persistant v2 (style Reels : couleurs franches, personnages cubiques).",
        "mood": {"view": "Standard", "sky": "#8CCBFF", "sky_strength": 0.9, "sun_energy": 3.4,
                 "sun_color": "#FFF4E0", "sun_rot": [45, 8, 38], "sun_soft": 6, "exposure": 0.0},
        "set": s}
(C / "sets" / "bardellaville.json").write_text(json.dumps(city, ensure_ascii=False, indent=1), encoding="utf-8")

N = [
    ("n1", "Dans cette ville, tout le monde vote Bardella.", ["Bardella"]),
    ("n2", "Et franchement, ça se voit.", ["ça se voit"]),
    ("n3", "Ici, personne ne sort sans son ring light.", ["ring light"]),
    ("n4", "Le rond-point ? Un studio photo.", ["studio photo"]),
    ("n5", "Les voitures tournent depuis mardi. Personne ne veut sortir du cadre.", ["cadre"]),
    ("n6", "À la boulangerie, la baguette est à deux euros.", ["deux euros"]),
    ("n7", "Le filtre beauté, lui, est offert.", ["offert"]),
    ("n8", "À la mairie, le maire répond à toutes les questions.", ["toutes"]),
    ("n9", "Le chômage ?", ["chômage"]),
    ("n10", "Les loyers ?", ["loyers"]),
    ("n11", "Et le panneau des réponses concrètes ? Toujours en chargement.", ["chargement"]),
    ("n12", "Mais derrière la mairie, il n'y a rien. Juste douze arrière-plans.", ["douze arrière-plans"]),
    ("n13", "La prochaine fois, on visite la ville d'à côté.", ["ville d'à côté"]),
]
segs = [{"id": i, "text": t, "accent_words": a, "claim_type": "fiction_satirique"} for i, t, a in N]


def sc(i, nids, keys, lens=30, **kw):
    d = {"id": i, "narration_ids": nids, "keys": keys, "lens": lens, "lead_in": 0.05, "tail": 0.12}
    d.update(kw)
    return d


scenes = [
    sc("s1", ["n1"], [{"t": 0, "loc": [9, -46, 24], "look": [0, -66, 1]}, {"t": 1, "loc": [6, -52, 15], "look": [0, -65, 2]}],
       lens=26, lead_in=0.1, comic_action="Plongée : une foule de personnages marche, chacun avec son ring light."),
    sc("s2", ["n2"], [{"t": 0, "loc": [0.6, -55.5, 2.9], "look": [0, -63, 2.5]}, {"t": 1, "loc": [0.4, -56.5, 2.8], "look": [0, -62, 2.5]}],
       lens=32, comic_action="Face caméra : visages satisfaits, éclairés comme en studio."),
    sc("s3", ["n3"], [{"t": 0, "loc": [0.9, -3.6, 2.95], "look": [0.55, 0, 2.75]}, {"t": 1, "loc": [0.8, -3.0, 2.9], "look": [0.55, 0, 2.75]}],
       lens=35, parent="heros", dof=False, comic_action="Gros plan : il marche, ring light allumé devant le visage."),
    sc("s4", ["n4"], [{"t": 0, "loc": [14, -26, 18], "look": [0, 0, 7]}, {"t": 1, "loc": [6, -18, 9], "look": [0, 0, 8]}],
       lens=24, comic_action="Le rond-point avec un ring light géant, les voitures tournent."),
    sc("s5", ["n5"], [{"t": 0, "loc": [9.45, 3.4, 2.95], "look": [8.95, -0.45, 2.2]}, {"t": 1, "loc": [9.3, 2.8, 2.8], "look": [8.95, -0.45, 2.2]}],
       lens=32, parent="orbit_pv0", dof=False, comic_action="Gros plan conducteur épuisé, il tourne en rond."),
    sc("s6", ["n6", "n7"], [{"t": 0, "loc": [80.6, 75.8, 2.9], "look": [80.1, 81.5, 2.5]}, {"t": 1, "loc": [80.4, 77.0, 2.75], "look": [80.1, 81.5, 2.55]}],
       lens=30, comic_action="Boulanger, baguette en main, ring light de comptoir."),
    sc("s7", ["n8"], [{"t": 0, "loc": [9, 8, 7], "look": [2.5, 25, 3]}, {"t": 1, "loc": [6.5, 11, 5.5], "look": [2.5, 25, 3]}],
       lens=28, comic_action="Plan large : le maire au pupitre, foule qui lève la main."),
    sc("s8", ["n9"], [{"t": 0, "loc": [-1.4, 24.0, 2.8], "look": [-1.8, 21.0, 2.6]}, {"t": 1, "loc": [-1.5, 23.5, 2.75], "look": [-1.8, 21.0, 2.6]}],
       lens=32, dof=False, lead_in=0.1, tail=0.15, comic_action="Gros plan habitant en colère."),
    sc("s9", [], [{"t": 0, "loc": [4.0, 21.9, 3.3], "look": [3.5, 27.3, 2.8]}, {"t": 1, "loc": [3.9, 22.5, 3.2], "look": [3.5, 27.3, 2.8]}],
       lens=34, dur=1.5, dof=False, comic_action="Le maire, sourire pro : bulle « Excellente question. »"),
    sc("s10", ["n10"], [{"t": 0, "loc": [2.6, 24.4, 2.85], "look": [2.2, 21.4, 2.6]}, {"t": 1, "loc": [2.5, 23.9, 2.8], "look": [2.2, 21.4, 2.6]}],
       lens=32, dof=False, lead_in=0.1, tail=0.15, comic_action="Gros plan habitante choquée."),
    sc("s11", [], [{"t": 0, "loc": [3.1, 22.6, 3.25], "look": [3.5, 27.3, 2.85]}, {"t": 1, "loc": [3.2, 23.1, 3.2], "look": [3.5, 27.3, 2.85]}],
       lens=36, dur=1.4, dof=False, comic_action="Même sourire, même bulle : « Excellente question. »"),
    sc("s12", ["n11"], [{"t": 0, "loc": [11.7, 17.0, 3.4], "look": [12.5, 25.0, 3.5]}, {"t": 1, "loc": [12.1, 19.0, 3.3], "look": [12.5, 25.0, 3.4]}],
       lens=32, comic_action="Panneau « Réponses concrètes : chargement… »."),
    sc("s13", ["n12"], [{"t": 0, "loc": [-12, 13, 8], "look": [0, 31, 7]}, {"t": 0.5, "loc": [-21, 22, 12], "look": [0, 37, 7.5]},
                        {"t": 1, "loc": [-26, 30, 15], "look": [0, 43, 8]}],
       lens=26, tail=0.4, comic_action="Orbite : la mairie est un décor sur étais ; onze façades de rechange surgissent."),
    sc("s14", [], [{"t": 0, "loc": [24.5, -37.5, 3.5], "look": [24.2, -24.5, 2.4]}, {"t": 1, "loc": [24.4, -34.5, 3.0], "look": [24.2, -24.5, 2.3]}],
       lens=34, dur=1.6, comic_action="Vitrine : la mascotte coq en t-shirt."),
    sc("s15", ["n13"], [{"t": 0, "loc": [10, -40, 14], "look": [0, -10, 3]}, {"t": 1, "loc": [12, -62, 46], "look": [0, -5, 2]}],
       lens=24, tail=1.6, comic_action="Plan aérien qui s'élève : carte « ABONNE-TOI »."),
]
events = [
    {"type": "walk", "target": "foule", "by": [0, 11], "shot": "s1", "at": 0.0, "dur": 9.5},
    {"type": "walk", "target": "heros", "by": [0, 11], "shot": "s1", "at": 0.0, "dur": 9.5},
    {"type": "face", "target": "heros", "expr": "content", "shot": "s3", "at": 0.55},
    {"type": "face", "target": "orbit_car0_drv", "expr": "fatigue", "shot": "s5", "at": 0.5},
    {"type": "talk", "target": "boulanger", "rest": "sourire_pro", "open": "sourire_pro", "shot": "s6", "at": 0.0, "until": 0.1},
    {"type": "face", "target": "boulanger", "expr": "fier", "shot": "s6", "at": 0.62},
    {"type": "talk", "target": "maire", "rest": "sourire_pro", "open": "parle_fier", "shot": "s9", "at": 0.05, "until": 0.7},
    {"type": "talk", "target": "maire", "rest": "sourire_pro", "open": "parle_fier", "shot": "s11", "at": 0.05, "until": 0.7},
    {"type": "face", "target": "cit2", "expr": "blase", "shot": "s11", "at": 0.0},
    {"type": "swap_text", "target": "sign_rep.l2", "count": 3, "show": 1, "shot": "s12", "at": 0.25},
    {"type": "swap_text", "target": "sign_rep.l2", "count": 3, "show": 2, "shot": "s12", "at": 0.5},
    {"type": "swap_text", "target": "sign_rep.l2", "count": 3, "show": 0, "shot": "s12", "at": 0.75},
    {"type": "move", "target": "fonds", "to": [0, 35.8, 0], "shot": "s13", "at": 0.42, "dur": 1.3},
]
ep = {
    "id": "bdv-s01e01", "version": 2, "city_id": "bardellaville", "season": 1, "episode_number": 1,
    "arc_id": "bdv-arc-01", "format": "A", "length": "long", "caption_style": "words", "voice_length_scale": 0.92,
    "title_cover": "Tout le monde vote Bardella",
    "fictional_subject": "Ville fictive inspirée des codes publics de communication de Jordan Bardella",
    "premise": "Une ville où tout est éclairé pour la photo et où rien ne mène nulle part.",
    "hook_variants": ["Dans cette ville, tout le monde vote Bardella.", "Ici, même les ronds-points ont un ring light.",
                      "Bienvenue dans la ville la mieux éclairée de France.", "Cette ville a tout misé sur l'éclairage.",
                      "Dans cette ville, personne ne sort sans son ring light."],
    "selected_hook": 0,
    "ending_variants": ["Mais derrière la mairie, il n'y a rien. Juste douze arrière-plans.",
                        "La mairie n'a pas de programme. Elle a une profondeur de champ.",
                        "Derrière la façade, il y a une autre façade."],
    "selected_ending": 0,
    "narration_segments": segs, "scenes": scenes, "events": events,
    "stickers": [
        {"text": "ÉCLAIRAGE : 10/10", "shot": "s3", "at": 0.25, "x": 560, "y": 560, "rot": -8},
        {"text": "TOUR N°847", "shot": "s5", "at": 0.15, "x": 600, "y": 600, "rot": 7},
        {"text": "FILTRE OFFERT", "shot": "s6", "at": 0.6, "x": 560, "y": 600, "rot": -9},
        {"text": "99 %", "shot": "s12", "at": 0.45, "x": 620, "y": 560, "rot": 8},
        {"text": "LE T-SHIRT EST EN BIO", "shot": "s14", "at": 0.1, "x": 540, "y": 520, "rot": -6},
    ],
    "bubbles": [
        {"text": "Excellente question.", "shot": "s9", "at": 0.05, "x": 560, "y": 430, "tail": [520, 560]},
        {"text": "Excellente question.", "shot": "s11", "at": 0.05, "x": 540, "y": 430, "tail": [560, 560]},
    ],
    "endcard": {"title": "Abonne-toi", "sub": "le t-shirt « Excellente question » est en bio", "at": 0.35},
    "stills": [{"name": "still_cover", "shot": "s3", "at": 0.7}],
    "cover_still": "still_cover",
    "ending": "n12",
    "cta_primary": {"type": "follow", "text": "La prochaine fois, on visite la ville d'à côté. Abonne-toi."},
    "cta_commercial": {"type": "visual_product", "text": "Le t-shirt est en bio", "product_id": "tee-excellente-question"},
    "continuity_after": ["Le rond-point central a un ring light géant.",
                         "La façade de la mairie est un décor plat ; onze façades de rechange attendent derrière.",
                         "Le maire répond « Excellente question. » à toutes les questions."],
    "sources": [], "claims": [], "product_ids": ["tee-excellente-question", "tee-pays-bugue"], "disclosure": "",
    "editorial_status": "scripted", "render_profile": "final", "scheduled_at": None,
    "caption": ("Dans cette ville, tout le monde vote Bardella… et personne ne sort du cadre 💡📸\n\n"
                "Le pire : le rond-point ou la mairie ? 👇\n\nPartie 2 : la ville d'à côté.\n\n"
                "👕 Le t-shirt « Excellente question. » est en bio.\n\n"
                "#danscetteville #humour #politique #bardella #satire #animation #3d #lebordelfrancais"),
    "editorial_notes": "Codes des Reels viraux (personnages expressifs, coupes 1,5–3 s, mots un par un, étiquettes, "
                       "bulle, carte de fin). Le maire est un personnage cubique générique ; aucune citation réelle.",
}
import sys
sys.path.insert(0, str(C.parent))
from lbf import provocation  # noqa: E402
ep = provocation.apply(ep)
ep["hook_overlay"] = {"text": "Les électeurs de Bardella vont me détester", "until": 2.4}
ep["endcard"] = {"title": "Envoie ça à ton pote qui vote Bardella", "sub": "le t-shirt « Excellente question » est en bio",
                 "at": 0.3}
(C / "episodes" / "bdv-s01e01.json").write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
print("décor :", len(s), "objets ; épisode :", len(scenes), "plans,", sum(len(t.split()) for _, t, _ in N), "mots")
