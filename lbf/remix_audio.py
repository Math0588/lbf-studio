"""Remixe le son des vidéos déjà fabriquées (réserve non publiée) avec le sound design actuel, sans refaire la 3D.

Pour chaque vidéo : la narration est reconstruite à l'identique (même voix, même texte → même timeline), puis
musique / impacts / bruitages / mixage actuels, et la nouvelle piste remplace l'ancienne dans le MP4 (image
copiée telle quelle). Sécurité : si la durée reconstruite s'écarte de plus de 0,15 s de la vidéo (synchronisation
des sous-titres et des coupes), la vidéo est laissée intacte.

Usage (GitHub Actions, workflow « Remix son ») : python -m lbf.remix_audio [id ...]
Sans identifiant : toutes les vidéos de la réserve pas encore publiées (état public du diffuseur).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from . import audio, config

STUDIO = "Math0588/lbf-studio"
DIFF_STATE = "https://raw.githubusercontent.com/Math0588/lbf-diffusion/main/state/publications.json"


def gh(*a, check=True):
    r = subprocess.run(["gh", *a], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300])
    return r


def unpublished() -> list[str]:
    names = {a["name"] for a in json.loads(gh("release", "view", "reserve", "-R", STUDIO, "--json", "assets").stdout)["assets"]}
    pubs = json.loads(urllib.request.urlopen(DIFF_STATE, timeout=30).read())
    done = {p["episode_id"] for p in pubs if p.get("status") in ("published", "publication_uncertain")}
    return sorted(n[:-4] for n in names if n.endswith(".mp4") and n[:-4] not in done)


def duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def remix(ep_id: str) -> str:
    ep_path = config.CONTENT / "episodes" / f"{ep_id}.json"
    if not ep_path.exists():
        return "épisode introuvable"
    ep = json.loads(ep_path.read_text(encoding="utf-8"))
    out = config.OUTPUT / "remix" / ep_id
    out.mkdir(parents=True, exist_ok=True)
    mp4 = out / f"{ep_id}.mp4"
    gh("release", "download", "reserve", "-R", STUDIO, "-p", f"{ep_id}.mp4", "-D", str(out), "--clobber")
    tl = audio.build_narration(ep, out)
    vd = duration(mp4)
    if abs(tl["total"] - vd) > 0.15 and abs(tl["total"] + 1.0 - vd) > 0.3:   # (la vidéo peut finir sur une fin muette)
        return f"ignoré : timeline {tl['total']:.2f} s ≠ vidéo {vd:.2f} s"
    total = vd
    cuts = [s["start"] for s in tl["shots"][1:]]
    seed = int(hashlib.sha1(ep_id.encode()).hexdigest(), 16) % 10007
    segs = tl["segments"]
    punch = (segs[-2]["start"], segs[-2]["end"]) if len(segs) >= 3 else None
    style = audio.make_music(total, out / "music.wav", seed=seed, cuts=cuts, punch=punch)
    audio.make_whooshes(cuts, total, out / "whoosh.wav")
    audio.hook_hit(out / "whoosh.wav")
    if config.get("MEME_SFX") != "false":
        qc = [tuple(c) for c in tl.get("quote_cues", [])]
        audio.add_sfx(out / "whoosh.wav", [c for c in audio.meme_cues(ep, tl) if c[1] not in {q[1] for q in qc}] + qc)
    # narration à la longueur de la vidéo (fin muette éventuelle)
    nar = audio.read_wav(out / "narration.wav")
    need = int(total * audio.SR)
    if len(nar) < need:
        import numpy as np
        audio.write_wav(out / "narration.wav", np.pad(nar, (0, need - len(nar))))
    audio.mix(out, total)
    new = out / f"{ep_id}.new.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-i", str(out / "mix.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(new)], check=True)
    if abs(duration(new) - vd) > 0.2:
        return "ignoré : durée finale incohérente"
    final = out / "up" / f"{ep_id}.mp4"
    final.parent.mkdir(exist_ok=True)
    new.replace(final)
    gh("release", "upload", "reserve", str(final), "-R", STUDIO, "--clobber")
    return f"remixé ({style})"


def main() -> int:
    # sans identifiant : vidéos non publiées dont la voix est enregistrée (ElevenLabs), seule voix reconstruite
    # à l'identique ; la voix de secours varie d'une synthèse à l'autre (désynchronisation) : non remixée
    ids = sys.argv[1:] or [i for i in unpublished() if (config.ASSETS / "voix" / f"{i}.key").exists()]
    print(f"[remix] {len(ids)} vidéo(s) : {' '.join(ids)}", flush=True)
    for i in ids:
        try:
            print(f"[remix] {i} : {remix(i)}", flush=True)
        except Exception as e:      # une vidéo en échec ne bloque pas les autres (l'ancienne reste en place)
            print(f"[remix] {i} : échec {type(e).__name__} {str(e)[:200]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
