"""Sous-titres ASS : blanc sur fond sombre, 2 lignes max, zones sûres Reels, mots accentués (jamais seule info)."""
from __future__ import annotations

import re
from pathlib import Path

from PIL import ImageFont

from . import config

W, H = 1080, 1920
FONT_FILE = "ArchivoBlack-Regular.ttf"
FONT_NAME = "Archivo Black"
SIZE = 60
MARGIN_L, MARGIN_R = 110, 170      # à droite : boutons d'interface Instagram
MARGIN_V = 600                     # bas : légende + barre d'interface
MAX_W = W - MARGIN_L - MARGIN_R - 60
RED = "&H3C23EF&"                  # ASS = BGR
BLUE_LIGHT = "&HFF9A6B&"


def _font():
    return ImageFont.truetype(str(config.FONTS / FONT_FILE), SIZE)


def text_width(s: str) -> int:
    return int(_font().getlength(s))


def _wrap_lines(words: list[str]) -> list[str]:
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if text_width(cand) <= MAX_W:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def chunk_segment(text: str) -> list[str]:
    """Découpe un segment en cartons d'au plus 2 lignes, en coupant de préférence sur la ponctuation."""
    clean = text.replace("« ", "« ").replace(" »", " »")
    phrases = [p.strip() for p in re.split(r"(?<=[.:?!])\s+", clean) if p.strip()]
    cards = []
    for ph in phrases:
        words = ph.split(" ")
        lines = _wrap_lines(words)
        while lines:
            cards.append(lines[:2])
            lines = lines[2:]
    return cards


def _fmt(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{(cs // 6000) % 60:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}"


def _accent(line: str, accents: list[str]) -> str:
    out = line.replace(" ", " ")
    for a in sorted(accents, key=len, reverse=True):
        out = re.sub(re.escape(a), lambda m: "{\\c" + RED + "}" + m.group(0) + "{\\c&HF7FDFF&}", out,
                     flags=re.IGNORECASE)
    return out


def build_ass(ep: dict, timeline: dict, out_path: Path, shot_starts: dict | None = None) -> dict:
    segs = {s["id"]: s for s in ep["narration_segments"]}
    events = []
    stats = []
    for seg in timeline["segments"]:
        s = segs[seg["id"]]
        cards = chunk_segment(s["text"])
        total_chars = sum(len(" ".join(c)) for c in cards) or 1
        t = seg["start"]
        dur = seg["end"] - seg["start"]
        for c in cards:
            n = len(" ".join(c))
            d = dur * n / total_chars
            body = "\\N".join(_accent(l, s.get("accent_words", [])) for l in c)
            events.append(("Sub", t, t + d - 0.02, body))
            stats.append({"text": " / ".join(c), "lines": len(c), "max_px": max(text_width(l) for l in c),
                          "cps": round(n / max(d, 0.01), 1), "dur": round(d, 2)})
            t += d
    total = timeline["total"]
    # mention de fiction (lisible, en haut, hors barre d'interface) + repère d'épisode discret
    disclosure = ep.get("disclosure", "")
    if disclosure:  # mention optionnelle (désactivée par décision du propriétaire)
        events.append(("Disc", 0, total, disclosure))
    city = ep.get("city_name") or ep["city_id"].capitalize()
    events.append(("Tag", 0, total, f"{city} · ép. {ep['episode_number']}"))
    # bandeau de marque + CTA commercial sur le dernier plan
    last = timeline["shots"][-1]
    t0 = last["start"]
    band = "m 0 0 l 1080 0 1080 26 0 26"
    events.append(("Band", max(0, t0 - 0.18), t0 + 0.22,
                   "{\\an7\\p1\\c&HFF4916&\\move(-1100,880,1100,880)}" + band))
    events.append(("Band", max(0, t0 - 0.12), t0 + 0.28,
                   "{\\an7\\p1\\c&H3C23EF&\\move(-1100,912,1100,912)}m 0 0 l 1080 0 1080 14 0 14"))
    cta = ep.get("cta_commercial", {}).get("text")
    if cta:
        events.append(("Cta", t0 + 0.3, total, "{\\fad(200,0)\\move(540,450,540,420,0,250)}" + cta.upper()))
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
        "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Sub,{FONT_NAME},{SIZE},&H00F7FDFF,&H00F7FDFF,&H28111827,&H28111827,0,0,0,0,100,100,0,0,3,14,0,2,"
        f"{MARGIN_L},{MARGIN_R},{MARGIN_V},1",
        f"Style: Disc,{FONT_NAME},30,&H00F7FDFF,&H00F7FDFF,&H64111827,&H64111827,0,0,0,0,100,100,0,0,3,8,0,8,"
        f"60,60,250,1",
        f"Style: Tag,{FONT_NAME},28,&H00F7FDFF,&H00F7FDFF,&H00FF4916,&H00FF4916,0,0,0,0,100,100,0,0,3,8,0,7,"
        f"60,60,318,1",
        f"Style: Band,{FONT_NAME},20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: Cta,{FONT_NAME},54,&H00F7FDFF,&H00F7FDFF,&H00FF4916,&H00FF4916,0,0,0,0,100,100,0,0,3,22,0,5,"
        f"60,60,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for style, a, b, txt in events:
        lines.append(f"Dialogue: {1 if style == 'Band' else 0},{_fmt(a)},{_fmt(b)},{style},,0,0,0,,{txt}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return {"cards": stats, "max_px_allowed": MAX_W}
