"""Format « edit » (recette des vidéos à plus d'un million de vues sur la politique) : le VRAI visage du
politicien dès la 1re image, coupes toutes les 1 à 2 s, zooms « punch », secousses, flashs, sous-titres mot à mot,
mèmes sonores, voix sarcastique. Photos sous licence libre (lbf.photos), créditées. Aucun extrait télé.

Réutilise le reste de la chaîne : script v4, voix (Gemini ou narration fournie), sound design v2, sous-titres.
Usage : python -m lbf.edit_v5 <script.json> <dossier_sortie> [--voix fichier.mp3]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import wave
from pathlib import Path

from . import audio, captions_v2, config, photos

FPS = 30
LEAD, GAP = 0.08, 0.14          # rythme d'edit : presque pas de blanc entre les phrases


def _dur(p: Path) -> float:
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _voice(script: dict, out: Path, voix: Path | None) -> list[Path]:
    from . import tts_gemini, voix_externe
    segs = script["narration_segments"]
    if voix:
        parts = voix_externe.split(voix, len(segs), out / "split", [len(s["text"].split()) for s in segs])
        if not parts:
            raise RuntimeError("découpage de la narration fournie impossible")
        return [Path(p) for p in parts]
    tts_gemini.synthesize_all([s["text"] for s in segs], out / "gemini")
    return [out / "gemini" / f"seg_{i}.wav" for i in range(len(segs))]


def _shot(photo: Path, dur: float, kind: str, seed: int, out: Path) -> Path:
    """Un plan : photo floutée en fond + photo nette au centre, mouvement selon le rôle de la phrase."""
    n = max(1, round(dur * FPS))
    rnd = random.Random(seed)
    oy = rnd.choice([0.30, 0.35, 0.40])             # cadrage vers le haut (le visage)
    if kind == "punch":                               # coup de zoom sec puis lente poussée
        z = f"if(lt(on,5),1.0+0.04*on,1.20+0.0015*(on-5))"
    elif kind == "chute":                             # gros zoom sur le visage
        z = f"if(lt(on,4),1.0+0.12*on,1.48+0.002*(on-4))"
    elif kind == "push":
        z = "1.0+0.0035*on"
    else:                                             # léger dézoom
        z = "max(1.25-0.004*on,1.0)"
    shake = {"punch": (12, 0.35), "chute": (24, 0.7)}.get(kind, (0, 0))
    a, d = shake
    fc = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:4,"
          f"eq=brightness=-0.28:saturation=1.3[bg];"
          f"[0:v]scale=2160:2700:force_original_aspect_ratio=increase,crop=2160:2700,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*{oy}':d=1:s=1080x1350:fps={FPS}[fg];"
          f"[bg][fg]overlay=x='if(lt(t,{d}),{a}*sin(t*70),0)':y='240+if(lt(t,{d}),{a}*cos(t*63),0)':shortest=1,"
          f"fade=t=in:st=0:d=0.09:color=white,format=yuv420p[v]")
    f = out / f"plan_{seed:03d}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{n / FPS:.3f}", "-i", str(photo),
                    "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "19", str(f)], check=True)
    return f


def render(script_path: Path, out: Path, voix: Path | None = None) -> Path:
    s = json.loads(script_path.read_text(encoding="utf-8"))
    city = s["city"]
    out.mkdir(parents=True, exist_ok=True)
    pics = sorted((photos.DIR / city).glob("*.jpg"))
    if len(pics) < 3:
        raise RuntimeError(f"pas assez de photos libres pour {city} (lancer lbf.photos)")
    segs = s["narration_segments"]
    parts = _voice(s, out, voix)
    # narration serrée
    t, timeline, shots = LEAD, [], []
    for sg, p in zip(segs, parts):
        d = _dur(p)
        timeline.append({"id": sg["id"], "start": round(t, 3), "end": round(t + d, 3)})
        t += d + GAP
    total = round(t + 0.25, 3)
    import numpy as np
    track = np.zeros(int(total * audio.SR) + audio.SR // 10, dtype=np.float32)
    for sg, p in zip(timeline, parts):
        x = audio.read_wav(p)
        k = int(sg["start"] * audio.SR)
        track[k:k + len(x)] += x[: len(track) - k]
    audio.write_wav(out / "narration.wav", track)
    for i, sg in enumerate(timeline):
        a = 0.0 if i == 0 else sg["start"] - GAP / 2
        b = timeline[i + 1]["start"] - GAP / 2 if i + 1 < len(timeline) else total
        shots.append({"id": f"e{i}", "start": round(a, 3), "dur": round(b - a, 3)})
    tl = {"total": total, "segments": timeline, "shots": shots}
    ep = {"id": s["id"], "city_id": city, "city": city, "narration_segments": segs, "stickers": [], "bubbles": [],
          "endcard": None, "hook_overlay": {"text": s.get("title_cover", ""), "until": 1.8}}
    # son : sound design v2 complet
    seed = int(hashlib.sha1(s["id"].encode()).hexdigest(), 16) % 10007
    cuts = [x["start"] for x in shots[1:]]
    punch = (timeline[-2]["start"], timeline[-2]["end"]) if len(timeline) >= 3 else None
    audio.make_music(total, out / "music.wav", seed=seed, cuts=cuts, punch=punch)
    audio.make_whooshes(cuts, total, out / "whoosh.wav")
    audio.hook_hit(out / "whoosh.wav")
    audio.add_sfx(out / "whoosh.wav", audio.meme_cues(ep, tl))
    audio.mix(out, total)
    captions_v2.build(ep, tl, out / "subs.ass")
    # image : un plan par phrase, photos différentes, mouvement selon le rôle
    rnd = random.Random(seed)
    order = pics[:]
    rnd.shuffle(order)
    plans = []
    for i, sh in enumerate(shots):
        kind = "punch" if i == 0 else "chute" if i == len(shots) - 2 else ("push" if i % 2 else "out")
        plans.append(_shot(order[i % len(order)], sh["dur"], kind, i, out))
    lst = out / "plans.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in plans))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst.name, "-c", "copy",
                    "image.mp4"], cwd=out, check=True)
    import os
    fonts = os.path.relpath(config.FONTS, out).replace("\\", "/")
    final = out / f"{s['id']}_edit.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "image.mp4", "-i", "mix.wav",
                    "-vf", f"ass=subs.ass:fontsdir={fonts},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                    final.name], cwd=out, check=True)
    (out / "credits.txt").write_text(photos.credits(city), encoding="utf-8")
    print(f"[edit] {final} ({total:.1f} s, {len(plans)} plans)", flush=True)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("sortie")
    ap.add_argument("--voix")
    a = ap.parse_args()
    render(Path(a.script), Path(a.sortie), Path(a.voix) if a.voix else None)
