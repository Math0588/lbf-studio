"""Sous-titres v2 (codes des Reels qui marchent) : un mot à la fois, jaune à contour noir, sous le centre (y=1340) ;
étiquettes rouges inclinées, bulles de dialogue, carte de fin « ABONNE-TOI », teaser « Partie 2 »."""
from __future__ import annotations

from pathlib import Path

from .subtitles import FONT_NAME, H, W, _fmt, text_width

SHORT = {"le", "la", "les", "l'", "un", "une", "de", "du", "des", "d'", "à", "au", "aux", "et", "en", "ne", "n'",
         "se", "ce", "ça", "on", "il", "y", "a", "je", "tu", "j'", "qu'", "c'", "s'", "t'", "m'", "est", "pas", "sa",
         "son", "ses", "ton", "ta", "tes", "mon", "ma", "mes", "lui", "qui", "que", "ou", "où"}
YEL = "&H0000E6FF&"
RED = "&H003C23EF&"
WORD_Y = 1340  # centre vertical des mots (1920 px de haut ; boutons et légende Instagram sous ~1500)


def word_cards(text: str) -> list[str]:
    """Mots affichés un par un ; les petits mots sont collés au suivant pour éviter le clignotement."""
    raw = text.replace("«", "").replace("»", "").replace("“", "").replace("”", "").split()
    cards, buf = [], ""
    for w in raw:
        cur = (buf + " " + w).strip() if buf else w
        bare = w.lower().strip(",.:;!?…")
        if (bare in SHORT or len(bare) <= 2) and len(cur) < 14 and not w.endswith((".", "?", "!", ":", ",")):
            buf = cur
            continue
        cards.append(cur)
        buf = ""
    if buf:
        cards.append(buf)
    return cards


def _weight(card: str) -> float:
    w = len(card.replace(" ", "")) + 2
    if card.endswith((".", "?", "!", "…")):
        w += 5
    elif card.endswith((",", ":", ";")):
        w += 3
    return w


def _shot_time(timeline, shot, at):
    sh = next(x for x in timeline["shots"] if x["id"] == shot)
    return sh["start"] + at * sh["dur"]


def build(ep: dict, timeline: dict, out_path: Path) -> dict:
    segs = {s["id"]: s for s in ep["narration_segments"]}
    ev, stats = [], []
    for seg in timeline["segments"]:
        s = segs[seg["id"]]
        cards = word_cards(s["text"])
        tot = sum(_weight(c) for c in cards) or 1
        t, dur = seg["start"], seg["end"] - seg["start"]
        acc = [a.lower() for a in s.get("accent_words", []) if a]
        for c in cards:
            d = dur * _weight(c) / tot
            txt = c.upper().rstrip(",;")
            col = "{\\c" + RED + "}" if any(a in c.lower() for a in acc) else ""
            k = min(100, int(100 * 940 / max(1, text_width(txt) * 92 / 60)))  # rétrécit un mot trop large
            # plus bas que le centre (le gag reste visible), au-dessus de la zone des boutons Instagram
            pop = "{\\an5\\pos(540,%d)\\fscx%d\\fscy%d\\t(0,90,\\fscx%d\\fscy%d)}" % (
                WORD_Y, k * 118 // 100, k * 118 // 100, k, k)
            ev.append((0, "Word", t, t + d, pop + col + txt))
            stats.append({"text": txt, "lines": 1, "max_px": int(text_width(txt) * 92 / 60 * k / 100),
                          "cps": round(len(txt) / max(d, .01), 1), "dur": round(d, 2)})
            t += d
    for st in ep.get("stickers", []):
        a = _shot_time(timeline, st["shot"], st.get("at", 0.2))
        b = _shot_time(timeline, st.get("until_shot", st["shot"]), st.get("until", 1.0))
        x, y, r = st.get("x", 540), st.get("y", 640), st.get("rot", -8)
        pos = (f"\\an5\\pos({x},{y})\\frz{r}\\fscx40\\fscy40\\t(0,120,\\fscx112\\fscy112)"
               f"\\t(120,200,\\fscx100\\fscy100)")
        ev.append((2, "StampOut", a, b, "{" + pos + "}" + st["text"].upper()))
        ev.append((3, "StampIn", a, b, "{" + pos + "}" + st["text"].upper()))
    for bu in ep.get("bubbles", []):
        a = _shot_time(timeline, bu["shot"], bu.get("at", 0.1))
        b = _shot_time(timeline, bu.get("until_shot", bu["shot"]), bu.get("until", 1.0))
        x, y = bu.get("x", 540), bu.get("y", 520)
        tx, ty = bu.get("tail", [x - 40, y + 95])
        ev.append((4, "Draw", a, b, "{\\an7\\pos(0,0)\\p1\\c&HFFFFFF&\\fad(80,0)}m %d %d l %d %d %d %d" %
                   (tx - 26, y + 30, tx + 30, y + 30, tx - 12, ty)))
        ev.append((5, "Bubble", a, b, "{\\an5\\pos(%d,%d)\\fad(80,0)}%s" % (x, y, bu["text"].upper())))
    ec = ep.get("endcard")
    if ec:
        last = timeline["shots"][-1]
        a = last["start"] + ec.get("at", 0.25) * last["dur"]
        e = timeline["total"]
        title = ec["title"].upper()
        lines = [title]
        if len(title) > 13 and " " in title:  # deux lignes équilibrées
            ws = title.split()
            cut = min(range(1, len(ws)), key=lambda i: abs(len(" ".join(ws[:i])) - len(" ".join(ws[i:]))))
            lines = [" ".join(ws[:cut]), " ".join(ws[cut:])]
        widest = max(text_width(l) for l in lines) * 104 / 60
        k = min(100, int(100 * 900 / max(widest, 1)))
        y_sub = 720 + (60 if len(lines) == 2 else 0) + 92
        ev.append((6, "EndTitle", a, e, "{\\an5\\pos(540,720)\\fscx%d\\fscy%d\\t(0,140,\\fscx%d\\fscy%d)"
                   "\\t(140,220,\\fscx%d\\fscy%d)}" % (k * 60 // 100, k * 60 // 100, k * 106 // 100, k * 106 // 100,
                                                      k, k) + "\\N".join(lines)))
        if ec.get("sub"):
            ev.append((6, "EndSub", a + 0.1, e, "{\\an5\\pos(540,%d)\\fad(120,0)}" % y_sub + ec["sub"]))
    ho = ep.get("hook_overlay")
    if ho:  # accroche choc écrite, visible dès la 1re image (le son est souvent coupé au départ)
        txt = ho["text"].upper()
        if len(txt) > 22 and " " in txt:
            ws = txt.split()
            cut = max(range(1, len(ws)), key=lambda i: -abs(len(" ".join(ws[:i])) - len(" ".join(ws[i:]))))
            txt = " ".join(ws[:cut]) + "\\N" + " ".join(ws[cut:])
        ev.append((7, "Hook", 0, ho.get("until", 2.4),
                   "{\\an5\\pos(540,360)\\fscx70\\fscy70\\t(0,120,\\fscx104\\fscy104)\\t(120,200,\\fscx100\\fscy100)}" + txt))
        if ho.get("sub"):
            y = 360 - (150 if "\\N" in txt else 100)
            ev.append((7, "PartSub", 0, ho.get("until", 2.4), "{\\an5\\pos(540,%d)}" % y + ho["sub"].upper()))
    pt = ep.get("part_teaser")
    if pt:
        a = _shot_time(timeline, pt["shot"], pt.get("at", 0.0))
        b = _shot_time(timeline, pt["shot"], pt.get("until", 1.0))
        ev.append((6, "Part", a, b, "{\\an5\\pos(540,430)}" + pt["title"].upper()))
        if pt.get("sub"):
            ev.append((6, "PartSub", a, b, "{\\an5\\pos(540,520)}" + pt["sub"].upper()))
    head = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
        "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Word,{FONT_NAME},92,{YEL},{YEL},&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,9,4,5,60,60,0,1",
        f"Style: StampOut,{FONT_NAME},58,{RED},{RED},{RED},&H00000000,0,0,0,0,100,100,1,0,3,20,0,5,0,0,0,1",
        f"Style: StampIn,{FONT_NAME},58,{RED},{RED},&H00F7FDFF,&H00000000,0,0,0,0,100,100,1,0,3,13,0,5,0,0,0,1",
        f"Style: Hook,{FONT_NAME},64,&H00FFFFFF,&H00FFFFFF,{RED},&H00000000,0,0,0,0,100,100,1,0,3,22,0,5,40,40,0,1",
        f"Style: Bubble,{FONT_NAME},66,&H00111111,&H00111111,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,3,26,0,5,0,0,0,1",
        f"Style: Draw,{FONT_NAME},20,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: EndTitle,{FONT_NAME},104,&H00FFFFFF,&H00FFFFFF,{RED},&H00000000,0,0,0,0,100,100,2,0,3,34,0,5,0,0,0,1",
        f"Style: EndSub,{FONT_NAME},40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5,2,5,0,0,0,1",
        f"Style: Part,{FONT_NAME},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,8,3,5,0,0,0,1",
        f"Style: PartSub,{FONT_NAME},54,{YEL},{YEL},&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,6,2,5,0,0,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for layer, style, a, b, txt in ev:
        head.append(f"Dialogue: {layer},{_fmt(a)},{_fmt(b)},{style},,0,0,0,,{txt}")
    out_path.write_text("\n".join(head) + "\n", encoding="utf-8-sig")
    return {"cards": stats, "max_px_allowed": 960}
