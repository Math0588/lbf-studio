"""Moteur de scène paramétrique — Le Bordel Français.

Exécuté DANS Blender :  blender -b --factory-startup -P blender/engine.py -- <job.json>

Sécurité : ce script n'exécute jamais de code fourni par un modèle ou une page. Il lit un JSON validé
et ne peut appeler que les constructeurs listés dans PROPS / EVENTS. Les seuls fichiers lus sont les
fontes du dossier assets/fonts ; les seules écritures vont dans le dossier de sortie du job.
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
FPS = 30

# --------------------------------------------------------------------------- utilitaires

_MATS = {}
_FONTS = {}
OBJ = {}          # id -> objet racine
SUB = {}          # id.partie -> objet (lumières, textes changeants…)


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(hexstr):
    h = hexstr.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat(color="#cccccc", rough=0.55, emit=0.0, metal=0.0, alpha=1.0, emit_color=None):
    key = (color, round(rough, 2), round(emit, 2), metal, alpha, emit_color)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(f"m_{len(_MATS)}")
    try:
        m.use_nodes = True
    except Exception:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    c = rgb(color)
    bsdf.inputs["Base Color"].default_value = (*c, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0:
        ec = rgb(emit_color) if emit_color else c
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    m.diffuse_color = (*c, 1.0)
    _MATS[key] = m
    return m


def font(name="ArchivoBlack-Regular.ttf"):
    if name not in _FONTS:
        _FONTS[name] = bpy.data.fonts.load(os.path.join(FONT_DIR, name))
    return _FONTS[name]


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, loc=(0, 0, 0), rot_z=0.0, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.5
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z))
    return link(e, parent)


def _finish(name, bm, material, loc, rot, parent, smooth):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = tuple(math.radians(a) for a in rot)
    return link(o, parent)


def box(name, size, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    o = _finish(name, bm, material or mat(), loc, rot, parent, False)
    if bevel > 0:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "ANGLE"
    return o


def cyl(name, r, h, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), r2=None, seg=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=h)
    return _finish(name, bm, material or mat(), loc, rot, parent, True)


def sphere(name, r, loc=(0, 0, 0), material=None, parent=None, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    return _finish(name, bm, material or mat(), loc, rot, parent, True)


def torus(name, R, r, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0), seg=64, ring=16):
    bm = bmesh.new()
    rows = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[(i + 1) % seg][j], rows[(i + 1) % seg][(j + 1) % ring],
                          rows[i][(j + 1) % ring]))
    return _finish(name, bm, material or mat(), loc, rot, parent, True)


def prism(name, w, h, depth, loc=(0, 0, 0), material=None, parent=None, rot=(0, 0, 0)):
    """Fronton triangulaire (base w, hauteur h, profondeur depth selon Y)."""
    bm = bmesh.new()
    d = depth / 2
    pts = [(-w / 2, 0), (w / 2, 0), (0, h)]
    front = [bm.verts.new((x, -d, z)) for x, z in pts]
    back = [bm.verts.new((x, d, z)) for x, z in pts]
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(name, bm, material or mat(), loc, rot, parent, False)


def text(name, body, size=1.0, loc=(0, 0, 0), material=None, parent=None, rot=(90, 0, 0),
         align="CENTER", extrude=0.02, fontname="ArchivoBlack-Regular.ttf", max_width=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font(fontname)
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.space_line = 0.85
    if max_width > 0:
        cu.text_boxes[0].width = max_width
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(material or mat("#FFFDF7"))
    o.location = loc
    o.rotation_euler = tuple(math.radians(a) for a in rot)
    return link(o, parent)


def area_light(name, energy, size, loc, target, color="#ffffff", parent=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = rgb(color)
    o = bpy.data.objects.new(name, ld)
    link(o, parent)
    o.location = loc
    look_at(o, Vector(target))
    return o


def point_light(name, energy, loc, color="#ffffff", radius=0.5, parent=None, shadow=True):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    try:
        ld.use_shadow = shadow
    except Exception:
        pass
    ld.color = rgb(color)
    ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    return link(o, parent)


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def root(p, prefix):
    pid = p.get("id") or f"{prefix}_{len(OBJ)}"
    at = p.get("at", [0, 0, 0])
    if len(at) == 2:
        at = [at[0], at[1], 0]
    r = empty(pid, tuple(at), p.get("rot", 0))
    s = p.get("scale")
    if s:
        r.scale = (s, s, s)
    OBJ[pid] = r
    return pid, r


# --------------------------------------------------------------------------- palette ville

PAL = {
    "ground": "#9DB08A", "asphalt": "#3B3F46", "curb": "#D9D4C7", "marking": "#F4F1E8",
    "sidewalk": "#CFC8BA", "window": "#26313F", "trunk": "#6B4F3A", "leaf": "#5E8C4A",
    "blue": "#1649FF", "white": "#FFFDF7", "red": "#EF233C", "ink": "#111827", "wood": "#B98A5A",
}


# --------------------------------------------------------------------------- constructeurs (catalogue)

def p_ground(p):
    s = p.get("size", 200)
    box("ground", (s, s, 0.2), (0, 0, -0.1), mat(p.get("color", PAL["ground"]), 0.95))


def p_road(p):
    pid, r = root(p, "road")
    a, b = Vector(p["start"] + [0]), Vector(p["end"] + [0])
    w = p.get("width", 6)
    L = (b - a).length
    ang = math.degrees(math.atan2((b - a).y, (b - a).x))
    mid = (a + b) / 2
    body = box(pid + "_asph", (L, w, 0.1), (mid.x, mid.y, 0.02), mat(PAL["asphalt"], 0.9), rot=(0, 0, ang))
    for side in (-1, 1):
        box(pid + f"_walk{side}", (L, 2.2, 0.22), (0, side * (w / 2 + 1.1), 0.0), mat(PAL["sidewalk"], 0.9),
            parent=body)
    dash = box(pid + "_dash", (1.4, 0.18, 0.02), (-L / 2 + 1.5, 0, 0.06), mat(PAL["marking"], 0.6), parent=body)
    arr = dash.modifiers.new("arr", "ARRAY")
    arr.count = max(1, int(L / 3.2))
    arr.relative_offset_displace = (3.2 / 1.4, 0, 0)


def p_roundabout(p):
    pid, r = root(p, "roundabout")
    ro, ri = p.get("radius", 12), p.get("island", 6.5)
    cyl(pid + "_asph", ro, 0.1, (0, 0, 0.03), mat(PAL["asphalt"], 0.9), parent=r, seg=96)
    cyl(pid + "_island", ri, 0.35, (0, 0, 0.15), mat(p.get("island_color", "#7FA36A"), 0.95), parent=r, seg=96)
    torus(pid + "_curb", ri, 0.22, (0, 0, 0.3), mat(PAL["curb"], 0.7), parent=r, seg=96, ring=8)
    torus(pid + "_outer", ro, 0.2, (0, 0, 0.12), mat(PAL["curb"], 0.7), parent=r, seg=128, ring=8)


def p_ring_light(p):
    pid, r = root(p, "ringlight")
    R, h = p.get("radius", 4.0), p.get("height", 6.0)
    emit = p.get("emit", 18.0)
    ring = torus(pid + "_ring", R, 0.42, (0, 0, h + R), mat("#FFFDF7", 0.3, emit, emit_color="#FFF1DC"),
                 parent=r, rot=(90, 0, 0))
    torus(pid + "_housing", R, 0.5, (0, 0.12, h + R), mat("#1A1D24", 0.4), parent=r, rot=(90, 0, 0))
    cyl(pid + "_pole", 0.22, h + 0.4, (0, 0.2, (h + 0.4) / 2), mat("#22252C", 0.4, metal=0.6), parent=r)
    cyl(pid + "_hub", 0.5, 0.6, (0, 0.25, h + R), mat("#22252C", 0.4), parent=r, rot=(90, 0, 0))
    for a in (0, 120, 240):
        leg = box(pid + f"_leg{a}", (3.2, 0.18, 0.18), (0, 0, 0.6), mat("#22252C", 0.4, metal=0.6), parent=r,
                  rot=(0, 15, a))
        leg.location = (math.cos(math.radians(a)) * 1.4, math.sin(math.radians(a)) * 1.4 + 0.2, 0.55)
    # « cellphone » sur le support : le gag du studio
    box(pid + "_phone", (1.1, 0.12, 2.0), (0, -0.25, h + R), mat("#111827", 0.3), parent=r, bevel=0.08)
    box(pid + "_phone_scr", (0.95, 0.02, 1.8), (0, -0.32, h + R), mat("#1649FF", 0.3, 2.0), parent=r)
    SUB[pid + ".ring"] = ring
    lt = point_light(pid + "_lamp", p.get("light_power", 9000), (0, -1.5, h + R), "#FFF1DC", 2.5, parent=r)
    SUB[pid + ".lamp"] = lt


def _windows(prefix, parent, w, h, y, z0, color, cols, rows, win=(1.0, 1.4), side_x=None):
    """Grille de fenêtres via modificateurs Array (peu coûteux)."""
    gx = w / cols
    gz = (h - z0) / rows
    m = mat(color, 0.25, 0.0, 0.2)
    wobj = box(prefix + "_win", (win[0], 0.12, win[1]), (-w / 2 + gx / 2, y, z0 + gz / 2), m, parent=parent)
    a1 = wobj.modifiers.new("cols", "ARRAY")
    a1.count = cols
    a1.relative_offset_displace = (gx / win[0], 0, 0)
    a2 = wobj.modifiers.new("rows", "ARRAY")
    a2.count = rows
    a2.relative_offset_displace = (0, 0, gz / win[1])
    return wobj


def p_building(p):
    pid, r = root(p, "bld")
    w, d, h = p.get("size", [8, 8, 12])
    col = p.get("color", "#E8DCC6")
    box(pid + "_body", (w, d, h), (0, 0, h / 2), mat(col, 0.85), parent=r, bevel=0.06)
    box(pid + "_roof", (w + 0.4, d + 0.4, 0.5), (0, 0, h + 0.25), mat(p.get("roof", "#6E5B52"), 0.8), parent=r)
    cols = max(2, int(w / 2.4))
    rows = max(1, int(h / 3.2))
    _windows(pid, r, w, h - 0.6, -d / 2 - 0.02, 1.0, p.get("window", PAL["window"]), cols, rows)
    if p.get("sign"):
        s = p["sign"]
        box(pid + "_signbg", (min(w * 0.8, len(s) * 0.75 + 1), 0.2, 1.3), (0, -d / 2 - 0.15, 3.6),
            mat(p.get("sign_bg", PAL["blue"]), 0.5), parent=r)
        text(pid + "_sign", s, 0.8, (0, -d / 2 - 0.3, 3.6), mat(PAL["white"], 0.4, 1.5), parent=r)


def _facade(prefix, parent, w, h, color, style, loc_y=0.0):
    f = empty(prefix, (0, loc_y, 0), 0, parent)
    m = mat(color, 0.8)
    box(prefix + "_slab", (w, 0.5, h), (0, 0, h / 2), m, parent=f)
    trim = mat(PAL["white"] if style != "modern" else "#9FB6C8", 0.6)
    if style in ("classic", "mairie"):
        n = max(4, int(w / 3))
        for i in range(n):
            x = -w / 2 + 1.5 + i * (w - 3) / (n - 1)
            cyl(prefix + f"_col{i}", 0.42, h * 0.62, (x, -0.9, h * 0.31 + 0.6), trim, parent=f)
        box(prefix + "_steps", (w * 0.8, 2.4, 0.6), (0, -1.2, 0.3), mat("#D8D2C4", 0.8), parent=f)
        box(prefix + "_entab", (w + 0.6, 2.0, 1.0), (0, -0.7, h * 0.62 + 1.1), trim, parent=f)
        prism(prefix + "_ped", w + 0.6, 2.6, 1.6, (0, -0.6, h * 0.62 + 1.6), trim, parent=f)
        box(prefix + "_door", (2.6, 0.2, 4.2), (0, -0.3, 2.7), mat("#5A3D2B", 0.6), parent=f)
    elif style == "modern":
        box(prefix + "_glass", (w * 0.9, 0.2, h * 0.9), (0, -0.3, h * 0.48), mat("#7FB3D9", 0.08, metal=0.3),
            parent=f)
    elif style == "castle":
        for i in range(int(w / 1.6)):
            box(prefix + f"_cren{i}", (0.8, 0.5, 0.9), (-w / 2 + 0.4 + i * 1.6, 0, h + 0.45), m, parent=f)
        box(prefix + "_gate", (3.0, 0.2, 4.0), (0, -0.3, 2.0), mat("#2E2620", 0.8), parent=f)
    elif style == "beach":
        box(prefix + "_sky", (w * 0.96, 0.2, h * 0.55), (0, -0.3, h * 0.6), mat("#7EC8F2", 0.5, 0.4), parent=f)
        sphere(prefix + "_sun", 1.6, (w * 0.25, -0.45, h * 0.75), mat("#FFD45C", 0.4, 3.0), parent=f,
               scale=(1, 0.2, 1))
    elif style == "factory":
        for i in range(3):
            cyl(prefix + f"_chim{i}", 0.6, 4, (-w / 3 + i * w / 3, 0, h + 2), mat("#7B6E66", 0.8), parent=f)
    else:
        _windows(prefix, f, w, h - 0.6, -0.27, 1.0, PAL["window"], max(2, int(w / 2.6)), max(1, int(h / 3.4)))
    return f


def p_facade_set(p):
    """Façade de cinéma : plate, tenue par des étais à l'arrière (révélée en orbite)."""
    pid, r = root(p, "facade")
    w, h = p.get("width", 18), p.get("height", 11)
    _facade(pid + "_main", r, w, h, p.get("color", "#F1E6D2"), p.get("style", "mairie"))
    if p.get("label"):
        text(pid + "_label", p["label"], 1.15, (0, -1.75, h * 0.62 + 1.1), mat(PAL["ink"], 0.5), parent=r)
    if p.get("struts", True):
        wood = mat(PAL["wood"], 0.85)
        for i, x in enumerate([-w / 2 + 1, -w / 4, 0, w / 4, w / 2 - 1]):
            L = h * 0.95
            box(pid + f"_strut{i}", (0.3, 0.3, L), (x, 0.3 + L * 0.35, L * 0.45), wood, parent=r, rot=(-38, 0, 0))
            box(pid + f"_sand{i}", (0.9, 0.7, 0.45), (x, 0.3 + L * 0.7, 0.22), mat("#C8B27A", 0.95), parent=r)
        box(pid + "_back", (w, 0.12, h), (0, 0.32, h / 2), mat("#B9A68A", 0.95), parent=r)


def p_facade_row(p):
    """Rangée de façades interchangeables derrière la première (« douze arrière-plans »)."""
    pid, r = root(p, "frow")
    styles = p.get("styles", ["classic", "modern", "castle", "beach", "factory", "plain"])
    colors = p.get("colors", ["#F4D6C6", "#D6E4F0", "#CFC6B4", "#FCE8B2", "#C9D9C1", "#E9C9D9"])
    n = p.get("count", 11)
    sp = p.get("spacing", 2.2)
    for i in range(n):
        f = _facade(pid + f"_{i}", r, p.get("width", 18) - (i % 3) * 0.6, p.get("height", 11) + (i % 4) * 0.8,
                    colors[i % len(colors)], styles[i % len(styles)], loc_y=i * sp)
        f.location.x = ((i % 2) * 2 - 1) * 0.35 * (i % 3)
        wood = mat(PAL["wood"], 0.85)
        for x in (-6, 6):
            box(pid + f"_{i}_st{x}", (0.25, 0.25, 7), (x, 1.6, 3.2), wood, parent=f, rot=(-34, 0, 0))


def p_studio_light(p):
    pid, r = root(p, "studio")
    h = p.get("height", 3.2)
    metal = mat("#22252C", 0.4, metal=0.6)
    for a in (0, 120, 240):
        leg = box(pid + f"_leg{a}", (0.08, 0.08, h * 0.75), (0, 0, h * 0.33), metal, parent=r, rot=(18, 0, a))
        leg.location = (math.sin(math.radians(a)) * 0.45, -math.cos(math.radians(a)) * 0.45, h * 0.33)
    cyl(pid + "_mast", 0.06, h, (0, 0, h / 2), metal, parent=r)
    head = empty(pid + "_head", (0, 0, h), 0, r)
    box(pid + "_box", (1.4, 0.9, 1.4), (0, 0, 0), mat("#15171C", 0.5), parent=head)
    box(pid + "_diff", (1.3, 0.05, 1.3), (0, -0.47, 0), mat("#FFFFFF", 0.3, 12.0), parent=head)
    if "target" in p:
        tgt = Vector(p["target"])
        wp = r.matrix_world @ Vector((0, 0, h)) if r.parent else Vector(r.location) + Vector((0, 0, h))
        d = tgt - wp
        head.rotation_euler = (0, 0, math.atan2(d.x, -d.y) - r.rotation_euler.z)
        area_light(pid + "_light", p.get("power", 600), 1.4, (wp.x, wp.y, wp.z), p["target"], "#FFF6EA")


def p_tripod_camera(p):
    pid, r = root(p, "tcam")
    metal = mat("#22252C", 0.4, metal=0.6)
    for a in (0, 120, 240):
        leg = box(pid + f"_leg{a}", (0.07, 0.07, 1.7), (0, 0, 0.75), metal, parent=r, rot=(15, 0, a))
        leg.location = (math.sin(math.radians(a)) * 0.3, -math.cos(math.radians(a)) * 0.3, 0.75)
    box(pid + "_body", (0.7, 1.0, 0.6), (0, 0, 1.75), mat("#1A1C22", 0.4), parent=r, bevel=0.05)
    cyl(pid + "_lens", 0.22, 0.6, (0, -0.75, 1.75), mat("#0D0F12", 0.2), parent=r, rot=(90, 0, 0))
    sphere(pid + "_rec", 0.07, (0.25, -0.5, 2.05), mat(PAL["red"], 0.3, 6.0), parent=r)


def p_sign(p):
    pid, r = root(p, "sign")
    w, h = p.get("w", 6), p.get("h", 3)
    z = p.get("z", 3.5)
    if p.get("posts", True):
        for x in (-w / 2 + 0.3, w / 2 - 0.3):
            cyl(pid + f"_post{x}", 0.1, z, (x, 0.05, z / 2), mat("#5B6068", 0.5, metal=0.5), parent=r)
    box(pid + "_panel", (w, 0.2, h), (0, 0, z + h / 2 - 0.4), mat(p.get("bg", PAL["blue"]), 0.5), parent=r)
    box(pid + "_frame", (w + 0.2, 0.15, h + 0.2), (0, 0.06, z + h / 2 - 0.4), mat(PAL["white"], 0.5), parent=r)
    lines = p.get("lines", [])
    n = len(lines)
    for i, ln in enumerate(lines):
        variants = ln.get("variants")
        zz = z + h / 2 - 0.4 + (n - 1) * 0.5 * ln.get("size", 0.6) * 1.4 - i * ln.get("size", 0.6) * 1.4
        m = mat(ln.get("color", PAL["white"]), 0.4, ln.get("emit", 1.2))
        if variants:
            for k, v in enumerate(variants):
                t = text(pid + f"_l{i}_v{k}", v, ln.get("size", 0.6), (0, -0.16, zz), m, parent=r,
                         align=ln.get("align", "CENTER"))
                if ln.get("align") == "LEFT":
                    t.location.x = -w / 2 + 0.4
                SUB[f"{pid}.l{i}.v{k}"] = t
                if k > 0:
                    t.hide_render = True
        else:
            t = text(pid + f"_l{i}", ln["text"], ln.get("size", 0.6), (0, -0.16, zz), m, parent=r)
            SUB[f"{pid}.l{i}"] = t


def p_car(p, parent=None):
    pid = p.get("id") or f"car_{len(OBJ)}"
    at = p.get("at", [0, 0, 0])
    r = empty(pid, (at[0], at[1], at[2] if len(at) > 2 else 0), p.get("rot", 0), parent)
    OBJ[pid] = r
    col = p.get("color", PAL["red"])
    box(pid + "_body", (3.8, 1.8, 0.9), (0, 0, 0.75), mat(col, 0.3, metal=0.2), parent=r, bevel=0.25)
    if p.get("open") or p.get("driver"):
        box(pid + "_wind", (0.1, 1.5, 0.32), (0.75, 0, 1.32), mat("#9ED0F5", 0.1, alpha=0.55), parent=r, rot=(0, -25, 0))
        box(pid + "_seat", (0.5, 1.2, 0.9), (-0.75, 0, 1.35), mat("#3B3F46", 0.7), parent=r)
        if p.get("driver"):
            d = dict(p["driver"])
            d.update(id=pid + "_drv", at=[-0.45, 0.35, 0.55], rot=90, seated=True, scale=d.get("scale", 0.62))
            p_char(d, parent=r)
    else:
        box(pid + "_cab", (2.0, 1.6, 0.8), (-0.2, 0, 1.45), mat(col, 0.3, metal=0.2), parent=r, bevel=0.25)
        box(pid + "_glass", (2.05, 1.62, 0.55), (-0.2, 0, 1.5), mat("#1D2733", 0.1, metal=0.4), parent=r, bevel=0.2)
    for x in (-1.25, 1.25):
        for y in (-0.9, 0.9):
            cyl(pid + f"_w{x}{y}", 0.42, 0.35, (x, y, 0.42), mat("#16181C", 0.8), parent=r, rot=(90, 0, 0))
    for y in (-0.55, 0.55):
        sphere(pid + f"_hl{y}", 0.15, (1.9, y, 0.85), mat("#FFF4D6", 0.3, 4.0), parent=r)
    if p.get("gps"):
        g = p["gps"]
        dev = empty(pid + "_gps", (0.4, 0, 2.05), 0, r)
        box(pid + "_gps_body", (0.14, 1.6, 1.0), (0, 0, 0.5), mat("#111827", 0.3), parent=dev, bevel=0.05)
        cyl(pid + "_gps_arm", 0.05, 0.4, (0.05, 0, -0.05), mat("#111827", 0.3), parent=dev)
        box(pid + "_gps_scr", (0.02, 1.45, 0.85), (-0.075, 0, 0.5), mat("#0E2A88", 0.3, 1.2), parent=dev)
        for k, v in enumerate(g.get("variants", [])):
            t = text(pid + f"_gps_t{k}", v, 0.2, (-0.09, 0, 0.5), mat(PAL["white"], 0.3, 2.5), parent=dev,
                     rot=(90, 0, -90), extrude=0.0, max_width=0.0)
            SUB[f"{pid}.gps.v{k}"] = t
            if k > 0:
                t.hide_render = True
        SUB[pid + ".gps"] = dev
    return r


def p_car_orbit(p):
    """Voitures qui tournent autour d'un centre (rond-point sans sortie)."""
    pid = p.get("id", "orbit")
    c = p.get("center", [0, 0])
    rad = p.get("radius", 9.5)
    n = p.get("count", 6)
    colors = p.get("colors", ["#EF233C", "#FFFDF7", "#1649FF", "#F2B134", "#2E8B57", "#8E9AAF"])
    period = p.get("period", 14.0)
    for i in range(n):
        pv = empty(f"{pid}_pv{i}", (c[0], c[1], 0.05), 360.0 * i / n)
        OBJ[f"{pid}_pv{i}"] = pv
        cp = {"id": f"{pid}_car{i}", "at": [rad, 0, 0], "rot": 90, "color": colors[i % len(colors)]}
        if i == p.get("hero_index", 0) and p.get("hero_gps"):
            cp["gps"] = p["hero_gps"]
        if i == p.get("hero_index", 0) and p.get("hero_driver"):
            cp["driver"] = p["hero_driver"]
        p_car(cp, parent=pv)
        pv["orbit_period"] = period
    OBJ[pid] = OBJ[f"{pid}_pv0"]


def p_tree(p):
    pid, r = root(p, "tree")
    h = p.get("height", 4)
    cyl(pid + "_trunk", 0.22, h * 0.45, (0, 0, h * 0.22), mat(PAL["trunk"], 0.9), parent=r)
    sphere(pid + "_crown", h * 0.32, (0, 0, h * 0.62), mat(p.get("color", PAL["leaf"]), 0.9), parent=r,
           scale=(1, 1, 1.15))


def p_lamp(p):
    pid, r = root(p, "lamp")
    cyl(pid + "_pole", 0.09, 4.5, (0, 0, 2.25), mat("#2B2F36", 0.5, metal=0.5), parent=r)
    sphere(pid + "_bulb", 0.3, (0, 0, 4.6), mat("#FFF1C9", 0.3, 5.0), parent=r)


def p_bench(p):
    pid, r = root(p, "bench")
    w = mat(PAL["wood"], 0.8)
    box(pid + "_seat", (2.2, 0.6, 0.12), (0, 0, 0.55), w, parent=r)
    box(pid + "_back", (2.2, 0.1, 0.5), (0, 0.28, 0.9), w, parent=r)
    for x in (-0.9, 0.9):
        box(pid + f"_leg{x}", (0.1, 0.5, 0.55), (x, 0, 0.27), mat("#2B2F36", 0.5), parent=r)


def p_bin(p):
    pid, r = root(p, "bin")
    cyl(pid + "_b", 0.35, 0.9, (0, 0, 0.45), mat(p.get("color", "#2E7D4F"), 0.6), parent=r)


def p_person(p):
    pid, r = root(p, "person")
    c = p.get("color", "#E0A458")
    cyl(pid + "_body", 0.33, 1.1, (0, 0, 0.75), mat(c, 0.7), parent=r, r2=0.26)
    sphere(pid + "_head", 0.3, (0, 0, 1.6), mat(p.get("skin", "#F1D3B3"), 0.7), parent=r)


def p_tshirt(p, parent=None):
    pid = p.get("id") or f"tee_{len(OBJ)}"
    at = p.get("at", [0, 0, 0])
    r = empty(pid, tuple(at if len(at) == 3 else at + [0]), p.get("rot", 0), parent)
    OBJ[pid] = r
    s = p.get("scale", 1.0)
    r.scale = (s, s, s)
    col = p.get("color", "#111827")
    m = mat(col, 0.9)
    box(pid + "_torso", (2.0, 0.25, 2.4), (0, 0, 0), m, parent=r, bevel=0.12)
    for side in (-1, 1):
        box(pid + f"_sl{side}", (0.9, 0.24, 0.8), (side * 1.25, 0, 0.75), m, parent=r, rot=(0, side * -28, 0),
            bevel=0.1)
    box(pid + "_collar", (0.7, 0.27, 0.12), (0, 0, 1.15), mat("#000000" if col != "#111827" else "#2A2F3A", 0.8),
        parent=r)
    lines = p.get("lines", ["LE PAYS BUGUE.", "MOI AUSSI."])
    tc = p.get("text_color", PAL["white"] if col in ("#111827", "#1649FF") else PAL["blue"])
    for i, ln in enumerate(lines):
        accent = (i == len(lines) - 1) and p.get("accent_last", True)
        text(pid + f"_t{i}", ln, 0.27, (0, -0.14, 0.45 - i * 0.38),
             mat(PAL["red"] if accent else tc, 0.6), parent=r, extrude=0.0, fontname="Anton-Regular.ttf")
    return r


def p_mascot(p):
    """Mascotte récurrente : coq blasé stylisé (blanc, crête et barbillon rouges)."""
    pid, r = root(p, "mascot")
    white = mat("#FFFDF7", 0.6)
    red = mat(PAL["red"], 0.5)
    sphere(pid + "_body", 1.0, (0, 0, 1.6), white, parent=r, scale=(0.9, 0.8, 1.1))
    sphere(pid + "_head", 0.62, (0, -0.25, 3.0), white, parent=r)
    for i, (x, z, s) in enumerate([(-0.25, 3.62, 0.24), (0.0, 3.72, 0.28), (0.25, 3.6, 0.22)]):
        sphere(pid + f"_comb{i}", s, (x * 0.6, -0.15 + x, z), red, parent=r, scale=(0.6, 1, 1.2))
    cyl(pid + "_beak", 0.2, 0.45, (0, -0.95, 2.95), mat("#F2B134", 0.5), parent=r, rot=(90, 0, 0), r2=0.0)
    sphere(pid + "_wattle", 0.16, (0, -0.8, 2.62), red, parent=r, scale=(0.7, 0.7, 1.3))
    for x in (-0.33, 0.33):
        sphere(pid + f"_eye{x}", 0.13, (x, -0.72, 3.12), mat("#FFFFFF", 0.3), parent=r)
        sphere(pid + f"_pupil{x}", 0.065, (x, -0.83, 3.1), mat(PAL["blue"], 0.3), parent=r)
        box(pid + f"_lid{x}", (0.3, 0.12, 0.1), (x, -0.78, 3.2), white, parent=r)  # paupière blasée
    for x in (-0.35, 0.35):
        cyl(pid + f"_leg{x}", 0.08, 0.8, (x, 0, 0.4), mat("#F2B134", 0.5), parent=r)
    for i, a in enumerate((-30, 0, 30)):
        box(pid + f"_tail{i}", (0.25, 1.2, 0.25), (math.sin(math.radians(a)) * 0.4, 0.9, 2.2), mat(PAL["blue"], 0.5),
            parent=r, rot=(-35, a, 0))
    if p.get("shirt"):
        sh = dict(p["shirt"])
        sh["id"] = pid + "_shirt"
        sh["at"] = [0, -0.86, 1.55]
        sh["scale"] = 0.62
        p_tshirt(sh, parent=r)


def p_shop(p):
    pid, r = root(p, "shop")
    w, d, h = p.get("size", [10, 7, 6])
    box(pid + "_body", (w, d, h), (0, 0, h / 2), mat(p.get("color", "#F3EBDD"), 0.8), parent=r, bevel=0.05)
    box(pid + "_win", (w * 0.8, 0.1, h * 0.55), (0, -d / 2 - 0.01, h * 0.42), mat("#26313F", 0.2), parent=r)
    # vitrine extérieure (estrade devant la baie) : les produits y sont visibles de la rue
    box(pid + "_floor", (w * 0.85, 3.0, 0.9), (0, -d / 2 - 1.6, 0.45), mat("#E9E1D3", 0.6), parent=r, bevel=0.05)
    # store tricolore
    for i, c in enumerate([PAL["blue"], PAL["white"], PAL["red"]] * 3):
        box(pid + f"_aw{i}", (w / 9, 1.6, 0.12), (-w / 2 + w / 18 + i * w / 9, -d / 2 - 0.8, h * 0.78),
            mat(c, 0.7), parent=r, rot=(-18, 0, 0))
    box(pid + "_signbg", (w * 0.7, 0.2, 1.1), (0, -d / 2 - 0.12, h - 0.7), mat(PAL["blue"], 0.5), parent=r)
    text(pid + "_sign", p.get("name", "BOUTIQUE"), 0.75, (0, -d / 2 - 0.25, h - 0.7), mat(PAL["white"], 0.4, 1.5),
         parent=r)
    area_light(pid + "_inner", 900, 4, (r.location.x, r.location.y - d / 2 - 3, h * 0.9),
               (r.location.x, r.location.y - d / 2 + 0.5, 1.5), "#FFF3E0")


def p_text3d(p):
    pid, r = root(p, "txt")
    t = text(pid + "_t", p["text"], p.get("size", 1.0), (0, 0, 0), mat(p.get("color", PAL["white"]), 0.4,
             p.get("emit", 0.0)), parent=r, rot=tuple(p.get("trot", [90, 0, 0])), extrude=p.get("extrude", 0.05))
    SUB[pid + ".t"] = t


def p_tribune(p):
    pid, r = root(p, "tribune")
    box(pid + "_desk", (1.6, 1.0, 1.3), (0, 0, 0.65), mat(p.get("color", "#7A1E2C"), 0.6), parent=r, bevel=0.05)
    box(pid + "_top", (1.8, 1.1, 0.1), (0, 0, 1.35), mat(PAL["wood"], 0.6), parent=r)
    cyl(pid + "_mic", 0.03, 0.6, (0.62, -0.2, 1.65), mat("#22252C", 0.4), parent=r, rot=(20, 0, 0))


def p_traffic_light(p):
    pid, r = root(p, "feu")
    cyl(pid + "_pole", 0.1, 3.6, (0, 0, 1.8), mat("#2B2F36", 0.5), parent=r)
    box(pid + "_box", (0.6, 0.5, 1.7), (0, 0, 4.2), mat("#1A1C22", 0.5), parent=r)
    for i, c in enumerate(p.get("lamps", ["#EF233C", "#F2B134", "#2ECC71"])):
        sphere(pid + f"_l{i}", 0.2, (0, -0.26, 4.75 - i * 0.55), mat(c, 0.3, p.get("emits", [6, 0, 6])[i]), parent=r)


def p_form_stack(p):
    pid, r = root(p, "forms")
    n = p.get("count", 30)
    for i in range(n):
        box(pid + f"_f{i}", (0.9, 1.2, 0.04), (math.sin(i) * 0.05, 0, 0.02 + i * 0.05), mat("#FBFAF5", 0.9),
            parent=r, rot=(0, 0, (i * 7) % 11 - 5))


def p_column(p):
    pid, r = root(p, "col")
    cyl(pid + "_c", p.get("r", 0.5), p.get("h", 5), (0, 0, p.get("h", 5) / 2), mat(PAL["white"], 0.6), parent=r)


def p_fountain(p):
    pid, r = root(p, "fountain")
    cyl(pid + "_basin", 2.2, 0.6, (0, 0, 0.3), mat("#CFC8BA", 0.7), parent=r)
    cyl(pid + "_water", 2.0, 0.1, (0, 0, 0.58), mat("#7FB3D9", 0.05, 0.3), parent=r)


def _wrap(s, n=14):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines[:4])


def p_screen(p):
    """Écran géant sur poteau ; texte émissif (variants possibles)."""
    pid, r = root(p, "screen")
    w, h, z = p.get("w", 7), p.get("h", 4), p.get("z", 4)
    cyl(pid + "_post", 0.18, z, (0, 0.3, z / 2), mat("#2B2F36", 0.5, metal=0.5), parent=r)
    box(pid + "_frame", (w + 0.4, 0.4, h + 0.4), (0, 0.1, z + h / 2), mat("#111827", 0.4), parent=r, bevel=0.08)
    box(pid + "_scr", (w, 0.05, h), (0, -0.12, z + h / 2), mat(p.get("bg", "#0E2A88"), 0.3, 1.0), parent=r)
    variants = p.get("variants") or [p.get("text", "")]
    size = p.get("size", min(0.9, w / 9.5))
    for k, v in enumerate(variants):
        t = text(pid + f"_t{k}", _wrap(v, p.get("wrap", 16)), size, (0, -0.2, z + h / 2),
                 mat(p.get("color", PAL["white"]), 0.3, 2.5), parent=r, extrude=0.0)
        SUB[f"{pid}.v{k}"] = t
        if k > 0:
            t.hide_render = True


def p_banner(p):
    """Ruban/banderole tendu entre deux poteaux, tricolore par défaut, texte optionnel."""
    pid, r = root(p, "banner")
    w, z = p.get("w", 6), p.get("z", 0.9)
    for x in (-w / 2, w / 2):
        cyl(pid + f"_p{x}", 0.07, z + 0.3, (x, 0, (z + 0.3) / 2), mat("#C9A227", 0.3, metal=0.8), parent=r)
    cols = p.get("colors", [PAL["blue"], PAL["white"], PAL["red"]])
    hh = p.get("h", 0.3)
    for i, c in enumerate(cols):
        box(pid + f"_s{i}", (w, 0.04, hh / len(cols)), (0, 0, z + hh / 2 - (i + 0.5) * hh / len(cols)),
            mat(c, 0.7), parent=r)
    if p.get("text"):
        text(pid + "_t", p["text"], hh * 0.6, (0, -0.06, z), mat(PAL["ink"], 0.5), parent=r, extrude=0.0)


def p_lift_tribune(p):
    """Cabine d'ascenseur devenue tribune : plateforme qui monte (événement « move » sur <id>_plat)."""
    pid, r = root(p, "lift")
    for x in (-1.6, 1.6):
        box(pid + f"_rail{x}", (0.25, 0.25, 9), (x, 0.8, 4.5), mat("#8E9AAF", 0.4, metal=0.6), parent=r)
    plat = empty(pid + "_plat", (0, 0, 0), 0, r)
    OBJ[pid + "_plat"] = plat
    box(pid + "_floor", (3.0, 2.4, 0.3), (0, 0, 0.15), mat("#3B3F46", 0.6), parent=plat)
    for x in (-1.45, 1.45):
        box(pid + f"_wall{x}", (0.1, 2.4, 2.6), (x, 0, 1.6), mat("#C9CED6", 0.3, metal=0.5), parent=plat)
    box(pid + "_desk", (1.6, 0.8, 1.2), (0, -0.6, 0.9), mat(p.get("color", "#7A1E2C"), 0.6), parent=plat)
    cyl(pid + "_mic", 0.03, 0.6, (0, -0.8, 1.75), mat("#22252C", 0.4), parent=plat, rot=(20, 0, 0))
    box(pid + "_drape", (3.0, 0.1, 1.0), (0, -1.25, 0.6), mat(PAL["red"], 0.8), parent=plat)


def p_bus(p):
    pid, r = root(p, "bus")
    col = p.get("color", PAL["blue"])
    box(pid + "_body", (10, 2.6, 2.8), (0, 0, 1.9), mat(col, 0.35, metal=0.1), parent=r, bevel=0.3)
    box(pid + "_glass", (9.4, 2.62, 1.0), (0, 0, 2.4), mat("#1D2733", 0.1, metal=0.4), parent=r, bevel=0.2)
    for x in (-3.3, 3.3):
        for y in (-1.3, 1.3):
            cyl(pid + f"_w{x}{y}", 0.55, 0.4, (x, y, 0.55), mat("#16181C", 0.8), parent=r, rot=(90, 0, 0))
    if p.get("text"):
        box(pid + "_dbg", (0.1, 2.0, 0.5), (5.02, 0, 3.0), mat("#111827", 0.4), parent=r)
        text(pid + "_dest", p["text"], 0.3, (5.1, 0, 3.0), mat("#F2B134", 0.3, 3.0), parent=r, rot=(90, 0, 90),
             extrude=0.0)


def p_router_lectern(p):
    pid, r = root(p, "router")
    w = mat("#6B4F3A", 0.7)
    box(pid + "_foot", (0.9, 0.9, 0.12), (0, 0, 0.06), w, parent=r)
    cyl(pid + "_col", 0.12, 1.1, (0, 0, 0.65), w, parent=r)
    box(pid + "_top", (1.3, 0.9, 0.1), (0, 0, 1.25), w, parent=r, rot=(-20, 0, 0))
    box(pid + "_router", (0.8, 0.5, 0.18), (0, 0.05, 1.42), mat("#F4F1E8", 0.4), parent=r, rot=(-20, 0, 0))
    for x in (-0.3, 0.3):
        cyl(pid + f"_ant{x}", 0.03, 0.6, (x, 0.2, 1.8), mat("#22252C", 0.4), parent=r)
    sphere(pid + "_led", 0.04, (0.25, -0.2, 1.5), mat("#2ECC71", 0.3, 6), parent=r)


def p_gps(p):
    """GPS géant sur pied (texte variable)."""
    pp = dict(p)
    pp.setdefault("w", 3.2)
    pp.setdefault("h", 2.0)
    pp.setdefault("z", 1.6)
    pp.setdefault("bg", "#0E2A88")
    p_screen(pp)


def p_table(p):
    pid, r = root(p, "table")
    w, d = p.get("w", 4), p.get("d", 1.6)
    box(pid + "_top", (w, d, 0.12), (0, 0, 0.9), mat(p.get("color", PAL["wood"]), 0.6), parent=r)
    for x in (-w / 2 + 0.2, w / 2 - 0.2):
        for y in (-d / 2 + 0.2, d / 2 - 0.2):
            box(pid + f"_l{x}{y}", (0.1, 0.1, 0.9), (x, y, 0.45), mat("#2B2F36", 0.5), parent=r)


def p_scroll(p):
    pid, r = root(p, "scroll")
    L = p.get("length", 3)
    box(pid + "_paper", (1.4, 0.03, L), (0, 0, L / 2 + 0.3), mat("#EAD9B0", 0.9), parent=r)
    for z in (0.3, L + 0.3):
        cyl(pid + f"_rod{z}", 0.09, 1.7, (0, 0, z), mat("#6B4F3A", 0.6), parent=r, rot=(0, 90, 0))
    if p.get("text"):
        text(pid + "_t", _wrap(p["text"], 12), 0.16, (0, -0.03, L / 2 + 0.3), mat("#3A2A1A", 0.8), parent=r,
             extrude=0.0, fontname="Anton-Regular.ttf")


def p_arch(p):
    """Arche gonflable d'inauguration."""
    pid, r = root(p, "arch")
    R = p.get("radius", 4)
    # moitié basse enterrée sous le sol : seule l'arche est visible
    torus(pid + "_a", R, 0.5, (0, 0, 0), mat(p.get("color", PAL["blue"]), 0.5), parent=r, rot=(90, 0, 0))
    if p.get("text"):
        text(pid + "_t", p["text"], 0.55, (0, -0.6, R + 0.2), mat(PAL["white"], 0.4, 1.0), parent=r)


# --------------------------------------------------------------------------- personnages cubiques (v2)

FACE_DIR = os.path.join(ROOT, "assets", "faces")
_FACE_MATS = {}


def face_mat(expr, iris="brun"):
    key = (expr, iris)
    if key in _FACE_MATS:
        return _FACE_MATS[key]
    path = os.path.join(FACE_DIR, f"{expr}_{iris}.png")
    if not os.path.exists(path):
        raise ValueError(f"Visage inconnu : {expr}")
    m = bpy.data.materials.new(f"face_{expr}_{iris}")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.8
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    _FACE_MATS[key] = m
    return m


def quad(name, w, h, loc, material, parent, rot=(90, 0, 0)):
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")  # sans couche UV, la texture du visage n'est pas plaquée
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= h
    return _finish(name, bm, material, loc, rot, parent, False)


HAIR = {
    "court": [((1.0, 1.0, 0.28), (0, 0.02, 0.62))],
    "plaque": [((1.04, 1.04, 0.22), (0, 0.04, 0.6)), ((1.04, 0.12, 0.42), (0, 0.5, 0.36))],
    "meche": [((1.0, 1.0, 0.26), (0, 0.02, 0.62)), ((0.55, 0.3, 0.2), (-0.18, -0.42, 0.62))],
    "herisse": [((1.0, 1.0, 0.2), (0, 0.02, 0.6))] + [((0.24, 0.24, 0.34), (x, y, 0.82))
                                                       for x in (-0.3, 0.05, 0.32) for y in (-0.25, 0.2)],
    "long": [((1.06, 1.06, 0.26), (0, 0.03, 0.6)), ((1.06, 0.3, 1.05), (0, 0.42, 0.1)),
             ((0.16, 0.9, 0.9), (-0.52, 0.05, 0.16)), ((0.16, 0.9, 0.9), (0.52, 0.05, 0.16))],
    "chignon": [((1.0, 1.0, 0.24), (0, 0.03, 0.6))],
    "chauve_cotes": [((0.12, 0.7, 0.4), (-0.52, 0.1, 0.1)), ((0.12, 0.7, 0.4), (0.52, 0.1, 0.1))],
    "casquette": [((1.04, 1.04, 0.3), (0, 0.02, 0.64)), ((0.9, 0.5, 0.08), (0, -0.7, 0.52))],
    "beret": [((1.15, 1.15, 0.2), (0.08, 0.02, 0.66))],
}
HELD = {}


def held_prop(kind, pid, r):
    """Objets tenus, placés dans le repère du personnage (face vers -Y), bras droit tendu vers l'avant."""
    if kind == "ring_light":
        torus(pid + "_rl", 0.34, 0.06, (1.05, -1.35, 2.95), mat("#FFFDF7", 0.3, 16.0, emit_color="#FFF1DC"), r,
              rot=(90, 0, 0), seg=40, ring=8)
        box(pid + "_rlphone", (0.18, 0.04, 0.32), (1.05, -1.35, 2.95), mat("#111827", 0.3), r)
        cyl(pid + "_rlstick", 0.03, 0.85, (0.85, -1.15, 2.45), mat("#22252C", 0.4), r, rot=(-25, 20, 0))
        point_light(pid + "_rlp", 45, (0.8, -1.1, 2.85), "#FFF1DC", 0.3, parent=r, shadow=False)
    elif kind == "phone":
        box(pid + "_ph", (0.32, 0.06, 0.58), (0.55, -1.15, 2.2), mat("#111827", 0.3), r, rot=(15, 0, 0))
        box(pid + "_phs", (0.28, 0.02, 0.52), (0.55, -1.12, 2.2), mat("#3B82F6", 0.3, 2.0), r, rot=(15, 0, 0))
    elif kind == "baguette":
        cyl(pid + "_bg", 0.1, 1.5, (0.55, -1.0, 1.95), mat("#D9A55B", 0.8), r, rot=(0, 90, 20))
    elif kind == "verre":
        cyl(pid + "_gl", 0.16, 0.42, (0.62, -1.0, 2.05), mat("#BFE3B4", 0.1, alpha=0.7), r)
    elif kind == "micro":
        cyl(pid + "_mic", 0.05, 0.45, (0.55, -0.95, 2.15), mat("#22252C", 0.4), r, rot=(-30, 0, 0))
        sphere(pid + "_mich", 0.11, (0.55, -1.08, 2.37), mat("#5B6068", 0.5), r)
    elif kind == "pancarte":
        cyl(pid + "_pst", 0.05, 1.6, (0.7, -0.2, 3.2), mat(PAL["wood"], 0.8), r)
        box(pid + "_pbd", (1.4, 0.06, 0.8), (0.7, -0.2, 4.1), mat(PAL["white"], 0.7), r)


def p_char(p, parent=None):
    """Personnage cubique original. Visages interchangeables (événements face/talk), marche (événement walk)."""
    pid = p.get("id") or f"char_{len(OBJ)}"
    at = p.get("at", [0, 0, 0])
    par = OBJ.get(p["parent"]) if p.get("parent") else parent
    r = empty(pid, (at[0], at[1], at[2] if len(at) > 2 else 0), p.get("rot", 0), par)
    OBJ[pid] = r
    s = p.get("scale", 1.0)
    r.scale = (s, s, s)
    skin = mat(p.get("skin", "#E8B98F"), 0.7)
    shirt = mat(p.get("shirt", "#5B8DEF"), 0.75)
    pants = mat(p.get("pants", "#2F3A4F"), 0.8)
    shoes = mat("#1F1F24", 0.6)
    seated = p.get("seated", False)
    legs = []
    for side in (-1, 1):
        hip = empty(f"{pid}_hip{side}", (side * 0.25, 0, 1.0), 0, r)
        box(f"{pid}_leg{side}", (0.42, 0.45, 1.0), (0, 0, -0.5), pants, hip)
        box(f"{pid}_shoe{side}", (0.44, 0.6, 0.18), (0, -0.07, -0.95), shoes, hip)
        if seated:
            hip.rotation_euler.x = math.radians(-80)
        legs.append(hip)
    box(f"{pid}_torso", (1.05, 0.55, 1.15), (0, 0, 1.58), shirt, r)
    if p.get("tee"):  # t-shirt de la boutique porté par le personnage (placement produit)
        lines = p["tee"].get("lines", [])
        ink = p["tee"].get("ink", "#FFFDF7")
        for i, ln in enumerate(lines):
            text(f"{pid}_tee{i}", ln, p["tee"].get("size", 0.15), (0, -0.285, 1.86 - i * 0.2),
                 mat(PAL["red"] if i == len(lines) - 1 else ink, 0.6), r, extrude=0.0, fontname="Anton-Regular.ttf")
    arms = []
    for side in (-1, 1):
        sh = empty(f"{pid}_sh{side}", (side * 0.7, 0, 2.08), 0, r)
        box(f"{pid}_arm{side}", (0.34, 0.4, 0.95), (0, 0, -0.45), shirt, sh)
        hand = empty(f"{pid}_hand{side}", (0, 0, -0.95), 0, sh)
        box(f"{pid}_handb{side}", (0.3, 0.32, 0.22), (0, 0, 0), skin, hand)
        arms.append((sh, hand))
    if p.get("suit"):
        box(f"{pid}_shirtv", (0.36, 0.02, 0.6), (0, -0.285, 1.86), mat("#FFFFFF", 0.6), r)
        box(f"{pid}_tie", (0.14, 0.03, 0.55), (0, -0.3, 1.78), mat(p.get("tie", "#B01E2F"), 0.5), r)
    if p.get("sash"):
        for i, c in enumerate([PAL["blue"], PAL["white"], PAL["red"]]):
            b = box(f"{pid}_sash{i}", (0.14, 0.04, 1.45), (0.0, -0.3, 1.6), mat(c, 0.6), r, rot=(0, 38, 0))
            b.location.x = -0.12 + i * 0.13
            b.location.z = 1.6 - i * 0.1
    head = empty(f"{pid}_head", (0, 0, 2.62), 0, r)
    box(f"{pid}_headb", (0.98, 0.98, 0.98), (0, 0, 0), skin, head)
    exprs = p.get("faces") or [p.get("face", "neutre")]
    iris = p.get("iris", "brun")
    for k, e in enumerate(exprs):
        fq = quad(f"{pid}_face{k}", 0.96, 0.96, (0, -0.495, 0), face_mat(e, iris), head)
        SUB[f"{pid}.face.v{k}"] = fq
        if k > 0:
            fq.hide_render = True
    r["face_names"] = ",".join(exprs)
    hc = mat(p.get("hair_color", "#3A2A1F"), 0.85)
    for i, (sz, loc) in enumerate(HAIR.get(p.get("hair", "court"), [])):
        box(f"{pid}_hair{i}", sz, loc, hc, head)
    if p.get("hair") == "chignon":
        sphere(f"{pid}_bun", 0.24, (0, 0.38, 0.6), hc, head)
    if p.get("glasses"):
        for x in (-0.2, 0.2):
            torus(f"{pid}_gl{x}", 0.13, 0.025, (x, -0.51, 0.06), mat("#111827", 0.3), head, rot=(90, 0, 0), seg=24, ring=6)
    if p.get("hold"):
        sh, hand = arms[1]
        sh.rotation_euler.x = math.radians(-80 if p["hold"] != "pancarte" else 170)
        held_prop(p["hold"], pid, r)
    if p.get("hand_up"):
        arms[1][0].rotation_euler.x = math.radians(170)
    if p.get("arms_crossed"):
        for sh, _ in arms:
            sh.rotation_euler.x = math.radians(-70)
    SUB[pid + ".legs"] = legs
    SUB[pid + ".arms"] = [a[0] for a in arms]
    SUB[pid + ".head"] = head
    return r


def p_crowd(p):
    """Foule de personnages variés (couleurs, coiffures, visages) disposée en grille irrégulière."""
    import random
    rnd = random.Random(p.get("seed", 1))
    cx, cy = p.get("at", [0, 0])[:2]
    n = p.get("count", 12)
    shirts = p.get("shirts", ["#5B8DEF", "#F2B134", "#EF6F6C", "#7BC47F", "#B983FF", "#FFFDF7", "#2EC4B6", "#F78FB3"])
    hairs = list(HAIR.keys())
    skins = ["#F1C9A5", "#E0AC7E", "#C68642", "#8D5524", "#F6D7B0"]
    cols = p.get("cols", 4)
    for i in range(n):
        x = cx + (i % cols - (cols - 1) / 2) * p.get("dx", 1.7) + rnd.uniform(-0.3, 0.3)
        y = cy + (i // cols) * p.get("dy", 1.8) + rnd.uniform(-0.3, 0.3)
        cp = {"id": f"{p.get('id', 'crowd')}_{i}", "at": [x, y], "rot": p.get("rot", 0) + rnd.uniform(-12, 12),
              "shirt": rnd.choice(shirts), "skin": rnd.choice(skins), "hair": rnd.choice(hairs),
              "hair_color": rnd.choice(["#2B1D14", "#6B4423", "#C9A15B", "#1C1C1C", "#8A8A8A", "#B5542C"]),
              "faces": p.get("faces", ["neutre"]), "iris": rnd.choice(["brun", "bleu", "vert"]),
              "hold": p.get("hold") if rnd.random() < p.get("hold_ratio", 1.0) else None,
              "hand_up": rnd.random() < p.get("hand_up_ratio", 0.0), "scale": rnd.uniform(0.92, 1.06)}
        p_char(cp)
    OBJ[p.get("id", "crowd")] = OBJ[f"{p.get('id', 'crowd')}_0"]


def p_house(p):
    pid, r = root(p, "house")
    w, d, h = p.get("size", [7, 6, 4.5])
    box(pid + "_b", (w, d, h), (0, 0, h / 2), mat(p.get("color", "#F3E9DC"), 0.85), r)
    roof = prism(pid + "_roof", d + 0.8, p.get("roof_h", 2.4), w + 0.6, (0, 0, h), mat(p.get("roof", "#D9483B"), 0.7),
                 r, rot=(0, 0, 90))
    box(pid + "_door", (1.1, 0.1, 2.0), (w * 0.2, -d / 2 - 0.03, 1.0), mat("#6B4423", 0.6), r)
    for x in (-w * 0.25, w * 0.42):
        box(pid + f"_w{x}", (1.0, 0.1, 1.0), (x if x < 0 else -w * 0.05, -d / 2 - 0.03, h * 0.6),
            mat("#9ED0F5", 0.15, 0.3), r)
    if p.get("poster"):
        box(pid + "_post", (1.4, 0.06, 1.9), (-w * 0.32, -d / 2 - 0.07, 1.6), mat(PAL["red"], 0.6), r)
        text(pid + "_postt", p["poster"], 0.22, (-w * 0.32, -d / 2 - 0.12, 1.6), mat(PAL["white"], 0.5, 0.5), r,
             extrude=0.0, max_width=0)


def p_flag(p):
    pid, r = root(p, "flag")
    h = p.get("height", 6)
    cyl(pid + "_pole", 0.07, h, (0, 0, h / 2), mat("#D8D8D8", 0.3, metal=0.7), r)
    cols = p.get("colors", [PAL["blue"], "#FFFFFF", PAL["red"]])
    w = p.get("w", 2.4)
    for i, c in enumerate(cols):
        box(pid + f"_s{i}", (w / 3, 0.04, w * 0.66), (0.1 + w / 6 + i * w / 3, 0, h - w * 0.33), mat(c, 0.7), r)


def p_poster(p):
    pid, r = root(p, "poster")
    w, h, z = p.get("w", 2.4), p.get("h", 3.2), p.get("z", 1.0)
    box(pid + "_bg", (w, 0.08, h), (0, 0, z + h / 2), mat(p.get("bg", PAL["blue"]), 0.6), r)
    lines = p.get("lines", ["MON", "MEILLEUR", "PROFIL"])
    for i, ln in enumerate(lines):
        text(pid + f"_t{i}", ln, p.get("size", 0.38), (0, -0.06, z + h * 0.72 - i * 0.5), mat(PAL["white"], 0.5, 0.6),
             r, extrude=0.0)
    if p.get("face"):
        box(pid + "_head", (1.0, 0.06, 1.0), (0, -0.03, z + h * 0.25), mat(p.get("skin", "#E8B98F"), 0.7), r)
        quad(pid + "_face", 0.98, 0.98, (0, -0.07, z + h * 0.25), face_mat(p["face"], "brun"), r)


def p_counter(p):
    """Comptoir de commerce (boulangerie, café)."""
    pid, r = root(p, "counter")
    w = p.get("w", 4)
    box(pid + "_c", (w, 1.2, 1.3), (0, 0, 0.65), mat(p.get("color", "#C98A52"), 0.6), r, bevel=0.05)
    box(pid + "_top", (w + 0.2, 1.4, 0.12), (0, 0, 1.36), mat("#F4EDE1", 0.4), r)
    for i in range(p.get("items", 5)):
        cyl(pid + f"_bg{i}", 0.1, 0.9, (-w / 2 + 0.5 + i * 0.6, -0.2, 1.52), mat("#D9A55B", 0.8), r, rot=(0, 90, 15))
    if p.get("price"):
        box(pid + "_pb", (1.2, 0.05, 0.6), (w / 2 - 0.8, -0.72, 1.0), mat("#111827", 0.6), r)
        text(pid + "_pt", p["price"], 0.3, (w / 2 - 0.8, -0.76, 1.0), mat(PAL["white"], 0.5, 1.0), r, extrude=0.0)


def p_wall(p):
    """Mur de fond simple (intérieurs : boulangerie, mairie)."""
    pid, r = root(p, "wall")
    w, h = p.get("w", 14), p.get("h", 6)
    box(pid + "_w", (w, 0.3, h), (0, 0, h / 2), mat(p.get("color", "#F2E6D8"), 0.9), r)
    box(pid + "_floor", (w, 10, 0.1), (0, -5, 0.05), mat(p.get("floor", "#B98A5A"), 0.7), r)
    if p.get("sign"):
        text(pid + "_sign", p["sign"], 0.6, (0, -0.2, h * 0.8), mat(p.get("sign_color", PAL["blue"]), 0.5), r)


PROPS = {
    "ground": p_ground, "road": p_road, "roundabout": p_roundabout, "ring_light": p_ring_light,
    "building": p_building, "mairie": p_facade_set, "facade_set": p_facade_set, "facade_row": p_facade_row,
    "studio_light": p_studio_light, "tripod_camera": p_tripod_camera, "sign": p_sign, "car": p_car,
    "car_orbit": p_car_orbit, "tree": p_tree, "lamp": p_lamp, "bench": p_bench, "bin": p_bin,
    "person": p_person, "tshirt": p_tshirt, "mascot": p_mascot, "shop": p_shop, "text3d": p_text3d,
    "tribune": p_tribune, "traffic_light": p_traffic_light, "form_stack": p_form_stack, "column": p_column,
    "fountain": p_fountain, "screen": p_screen, "banner": p_banner, "lift_tribune": p_lift_tribune,
    "bus": p_bus, "router_lectern": p_router_lectern, "gps": p_gps, "table": p_table, "scroll": p_scroll,
    "arch": p_arch, "char": p_char, "crowd": p_crowd, "house": p_house, "flag": p_flag, "poster": p_poster,
    "counter": p_counter, "wall": p_wall,
}

# --------------------------------------------------------------------------- scène, caméras, événements


def set_interp(kind):
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = kind
    except Exception:
        pass


def setup_world(mood, profile):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x, sc.render.resolution_y = profile["res"]
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    try:
        sc.eevee.taa_render_samples = profile["samples"]
    except Exception:
        pass
    for attr, val in (("use_raytracing", profile.get("raytracing", True)), ("use_shadows", True),
                      ("use_gtao", True)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
    try:
        sc.view_settings.view_transform = mood.get("view", "AgX")
        if mood.get("view") == "Standard":
            raise StopIteration
        for look in ("AgX - Punchy", "Punchy", "AgX - Medium High Contrast", "Medium High Contrast"):
            try:
                sc.view_settings.look = look
                break
            except Exception:
                continue
        sc.view_settings.exposure = mood.get("exposure", 0.0)
    except StopIteration:
        sc.view_settings.look = "None"
        sc.view_settings.exposure = mood.get("exposure", 0.0)
    except Exception:
        pass
    w = bpy.data.worlds.new("world")
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*rgb(mood.get("sky", "#BFD9F2")), 1)
    bg.inputs[1].default_value = mood.get("sky_strength", 1.0)
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = mood.get("sun_energy", 4.0)
    sd.color = rgb(mood.get("sun_color", "#FFF1DE"))
    sd.angle = math.radians(mood.get("sun_soft", 6))
    sun = bpy.data.objects.new("sun", sd)
    link(sun)
    sun.rotation_euler = tuple(math.radians(a) for a in mood.get("sun_rot", [48, 8, 35]))


def build_cameras(shots, profile):
    sc = bpy.context.scene
    frame = 1
    starts = {}
    for s in shots:
        n = max(1, int(round(s["dur"] * FPS)))
        starts[s["id"]] = (frame, n)
        parent = OBJ.get(s["parent"]) if s.get("parent") else None
        cd = bpy.data.cameras.new("cam_" + s["id"])
        cd.lens = s.get("lens", 28)
        cd.sensor_width = 36
        cd.clip_end = 1000
        cam = link(bpy.data.objects.new("cam_" + s["id"], cd), parent)
        tgt = empty("tgt_" + s["id"], (0, 0, 0), 0, parent)
        con = cam.constraints.new("TRACK_TO")
        con.target = tgt
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
        if profile.get("dof", True) and s.get("dof", True):
            cd.dof.use_dof = True
            cd.dof.focus_object = tgt
            cd.dof.aperture_fstop = s.get("fstop", 5.6)
        set_interp(s.get("interp", "BEZIER"))
        for k in s["keys"]:
            f = frame + int(round(k["t"] * (n - 1)))
            cam.location = k["loc"]
            cam.keyframe_insert("location", frame=f)
            tgt.location = k["look"]
            tgt.keyframe_insert("location", frame=f)
            if "lens" in k:
                cd.lens = k["lens"]
                cd.keyframe_insert("lens", frame=f)
        m = sc.timeline_markers.new(s["id"], frame=frame)
        m.camera = cam
        if frame == 1:
            sc.camera = cam
        frame += n
    sc.frame_start = 1
    sc.frame_end = frame - 1
    return starts


def shot_frame(starts, ev):
    f0, n = starts[ev["shot"]]
    return f0 + int(round(ev.get("at", 0.0) * (n - 1)))


def apply_orbits(total_frames):
    set_interp("LINEAR")
    for oid, o in list(OBJ.items()):
        if "orbit_period" in o.keys():
            period = float(o["orbit_period"])
            z0 = o.rotation_euler.z
            o.keyframe_insert("rotation_euler", index=2, frame=1)
            o.rotation_euler.z = z0 + 2 * math.pi * (total_frames / FPS) / period
            o.keyframe_insert("rotation_euler", index=2, frame=total_frames)


def apply_events(events, starts):
    shown = {}
    for ev in sorted(events, key=lambda e: shot_frame(starts, e)):
        f = shot_frame(starts, ev)
        t = ev["type"]
        if t == "swap_text":
            base, k, count = ev["target"], ev["show"], ev["count"]
            prev = shown.get(base, 0)
            for j in range(count):
                o = SUB[f"{base}.v{j}"]
                o.hide_render = j != prev
                o.keyframe_insert("hide_render", frame=max(1, f - 1))
                o.hide_render = j != k
                o.keyframe_insert("hide_render", frame=f)
            shown[base] = k
        elif t == "face":
            names = OBJ[ev["target"]]["face_names"].split(",")
            k = names.index(ev["expr"])
            base = f"{ev['target']}.face"
            prev = shown.get(base, 0)
            for j in range(len(names)):
                o = SUB[f"{base}.v{j}"]
                o.hide_render = j != prev
                o.keyframe_insert("hide_render", frame=max(1, f - 1))
                o.hide_render = j != k
                o.keyframe_insert("hide_render", frame=f)
            shown[base] = k
        elif t == "talk":
            names = OBJ[ev["target"]]["face_names"].split(",")
            a, b = names.index(ev.get("rest", names[0])), names.index(ev.get("open", "parle"))
            base = f"{ev['target']}.face"
            end = shot_frame(starts, {"shot": ev["shot"], "at": ev.get("until", 1.0)})
            cur = shown.get(base, 0)
            fr = f
            toggle = True
            while fr < end:
                k = b if toggle else a
                for j in range(len(names)):
                    o = SUB[f"{base}.v{j}"]
                    o.hide_render = j != cur
                    o.keyframe_insert("hide_render", frame=max(1, fr - 1))
                    o.hide_render = j != k
                    o.keyframe_insert("hide_render", frame=fr)
                cur = k
                toggle = not toggle
                fr += ev.get("step", 4)
            for j in range(len(names)):
                o = SUB[f"{base}.v{j}"]
                o.hide_render = j != cur
                o.keyframe_insert("hide_render", frame=max(1, fr - 1))
                o.hide_render = j != a
                o.keyframe_insert("hide_render", frame=fr)
            shown[base] = a
        elif t == "walk":
            import re as _re
            tgt = ev["target"]
            ids = [k for k in OBJ if k == tgt or _re.fullmatch(_re.escape(tgt) + r"_\d+", k)]
            n = int(ev.get("dur", 3.0) * FPS)
            dx, dy = ev.get("by", [0, 3])
            for oid in ids:
                o = OBJ[oid]
                if f"{oid}.legs" not in SUB:
                    continue
                set_interp("LINEAR")
                x0, y0 = o.location.x, o.location.y
                o.keyframe_insert("location", frame=f)
                o.location.x, o.location.y = x0 + dx, y0 + dy
                o.keyframe_insert("location", frame=f + n)
                o.location.x, o.location.y = x0, y0
                set_interp("BEZIER")
                ph = (hash(oid) % 7) * 0.6
                for fr in range(f, f + n + 1, 3):
                    a = math.sin((fr - f) / FPS * 2 * math.pi * 1.6 + ph) * math.radians(ev.get("swing", 28))
                    for i, hip in enumerate(SUB[f"{oid}.legs"]):
                        hip.rotation_euler.x = a * (1 if i == 0 else -1)
                        hip.keyframe_insert("rotation_euler", index=0, frame=fr)
                    for i, sh in enumerate(SUB[f"{oid}.arms"]):
                        if i == 1 and abs(sh.rotation_euler.x) > math.radians(40):
                            continue  # bras qui tient un objet
                        sh.rotation_euler.x = -a * (1 if i == 0 else -1)
                        sh.keyframe_insert("rotation_euler", index=0, frame=fr)
                    head = SUB[f"{oid}.head"]
                    head.location.z = 2.62 + abs(a) * 0.06
                    head.keyframe_insert("location", index=2, frame=fr)
        elif t == "nod":
            head = SUB[f"{ev['target']}.head"]
            n = int(ev.get("dur", 1.0) * FPS)
            for fr in range(f, f + n + 1, 4):
                head.rotation_euler.x = math.sin((fr - f) / 4 * math.pi / 2) * math.radians(ev.get("deg", 8))
                head.keyframe_insert("rotation_euler", index=0, frame=fr)
        elif t in ("hide", "show"):
            o = OBJ.get(ev["target"]) or SUB.get(ev["target"])
            objs = [o] + list(o.children_recursive)
            for x in objs:
                x.hide_render = t == "show"
                x.keyframe_insert("hide_render", frame=max(1, f - 1))
                x.hide_render = t == "hide"
                x.keyframe_insert("hide_render", frame=f)
        elif t == "light":
            o = SUB[ev["target"]]
            set_interp("CONSTANT")
            if o.type == "LIGHT":
                o.data.energy = ev.get("from", o.data.energy)
                o.data.keyframe_insert("energy", frame=max(1, f - 1))
                o.data.energy = ev["energy"]
                o.data.keyframe_insert("energy", frame=f)
        elif t == "move":
            o = OBJ[ev["target"]]
            set_interp("BEZIER")
            o.keyframe_insert("location", frame=f)
            o.location = ev["to"]
            o.keyframe_insert("location", frame=f + int(ev.get("dur", 1.0) * FPS))


def fix_swap_initial(events):
    """Avant tout événement, seule la variante 0 de chaque texte changeant est visible."""
    seen = set()
    for ev in events:
        if ev["type"] == "swap_text" and ev["target"] not in seen:
            seen.add(ev["target"])
            for j in range(ev["count"]):
                o = SUB[f"{ev['target']}.v{j}"]
                o.hide_render = j != 0
                o.keyframe_insert("hide_render", frame=1)


PROFILES = {
    "preview": {"res": (540, 960), "samples": 8, "dof": False, "raytracing": False},
    "final": {"res": (1080, 1920), "samples": 32, "dof": True, "raytracing": True},
    "bench": {"res": (1080, 1920), "samples": 32, "dof": True, "raytracing": True},
    # GitHub Actions (CPU, Mesa llvmpipe) : même cadre 1080×1920, moins d'échantillons
    "cloud": {"res": (1080, 1920), "samples": 10, "dof": False, "raytracing": False},
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    job = json.load(open(argv[0], encoding="utf-8"))
    out = job["out_dir"]
    os.makedirs(out, exist_ok=True)
    profile = dict(PROFILES[job.get("profile", "final")])
    if job.get("quality") in PROFILES:
        profile = dict(PROFILES[job["quality"]])
    t0 = time.time()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_world(job.get("mood", {}), profile)
    for p in job["set"]:
        fn = PROPS.get(p["type"])
        if fn is None:
            raise ValueError(f"Prop inconnu (refusé) : {p['type']}")
        fn(p)
    starts = build_cameras(job["shots"], profile)
    total = bpy.context.scene.frame_end
    apply_orbits(total)
    fix_swap_initial(job.get("events", []))
    apply_events(job.get("events", []), starts)

    sc = bpy.context.scene
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.use_overwrite = False     # rendu reprenable : les images déjà faites sont gardées
    sc.render.use_placeholder = True
    frames_dir = os.path.join(out, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    sc.render.filepath = os.path.join(frames_dir, "f_")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "scene.blend"))
    build_time = time.time() - t0

    stills = job.get("stills", [])
    for st in stills:
        f = shot_frame(starts, st)
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, st["name"])
        bpy.ops.render.render(write_still=True)
    sc.render.filepath = os.path.join(frames_dir, "f_")

    fr = job.get("frame_range")
    if fr:
        sc.frame_start, sc.frame_end = fr
    t1 = time.time()
    if not job.get("stills_only"):
        bpy.ops.render.render(animation=True)
    render_time = time.time() - t1
    report = {"frames": sc.frame_end - sc.frame_start + 1, "fps": FPS, "build_s": round(build_time, 2),
              "render_s": round(render_time, 2), "engine": sc.render.engine, "blender": bpy.app.version_string,
              "res": list(profile["res"]), "samples": profile["samples"],
              "shot_starts": {k: v[0] for k, v in starts.items()}}
    json.dump(report, open(os.path.join(out, "render_report.json"), "w", encoding="utf-8"), indent=2)
    print("LBF_RENDER_DONE", json.dumps(report))


if __name__ == "__main__":
    main()
