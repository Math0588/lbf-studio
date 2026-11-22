"""Production complète d'un épisode : contrôle éditorial → voix → 3D → musique → mixage → sous-titres →
montage → couverture → QA → dossier de publication. Chaque étape est reprenable (fichiers déjà faits gardés)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import audio, captions_v2, config, cover, editorial, qa, subtitles

CITY_NAMES = {"bardellaville": "Bardellaville", "melenchonville": "Mélenchonville", "macronville": "Macronville",
              "zemmourville": "Zemmourville", "marineville": "Marineville", "glucksmannville": "Glucksmannville", "durifville": "Durifville", "rinerville": "Rinerville"}


def load_episode(path: Path) -> dict:
    ep = json.loads(Path(path).read_text(encoding="utf-8"))
    ep["city_name"] = CITY_NAMES.get(ep["city_id"], ep["city_id"])
    return ep


def build_job(ep: dict, timeline: dict, out: Path, profile: str) -> Path:
    city = json.loads((config.CONTENT / "sets" / f"{ep['city_id']}.json").read_text(encoding="utf-8"))
    dur = {s["id"]: s["dur"] for s in timeline["shots"]}
    shots = []
    for sc in ep["scenes"]:
        shots.append({k: sc[k] for k in ("id", "keys", "lens", "parent", "dof", "fstop", "interp") if k in sc}
                     | {"dur": dur[sc["id"]]})
    job = {"out_dir": str(out / f"render_{profile}"), "profile": profile, "mood": city.get("mood", {}),
           "set": city["set"] + ep.get("extra_set", []), "shots": shots, "events": ep.get("events", []),
           "stills": ep.get("stills", []) if profile != "preview" else []}
    if config.get("RENDER_QUALITY") and profile == "final":
        job["quality"] = config.get("RENDER_QUALITY")
    p = out / f"job_{profile}.json"
    p.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def render(job_path: Path, log: Path) -> dict:
    t0 = time.time()
    with open(log, "w", encoding="utf-8") as lf:
        r = subprocess.run([config.blender_path(), "-b", "--factory-startup", "-noaudio", "--python-exit-code", "3", "-P",
                            str(config.BLENDER_ENGINE), "--", str(job_path)], stdout=lf, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError(f"Blender a échoué (code {r.returncode}), voir {log}")
    job = json.loads(job_path.read_text(encoding="utf-8"))
    rp = Path(job["out_dir"]) / "render_report.json"
    if not rp.exists():
        raise RuntimeError(f"Rendu incomplet (aucun rapport), voir {log}")
    rep = json.loads(rp.read_text(encoding="utf-8"))
    rep["wall_s"] = round(time.time() - t0, 1)
    return rep


def cached_render(job_path: Path) -> dict | None:
    """Réutilise un rendu existant si le job (décor, plans, durées, événements) est identique et complet."""
    import hashlib
    job = json.loads(job_path.read_text(encoding="utf-8"))
    out_dir = Path(job["out_dir"])
    key = hashlib.sha1(json.dumps({k: job[k] for k in ("profile", "mood", "set", "shots", "events")},
                                  sort_keys=True).encode()).hexdigest()
    stamp, rep = out_dir / "job.key", out_dir / "render_report.json"
    frames = list((out_dir / "frames").glob("f_*.png"))
    if stamp.exists() and rep.exists() and stamp.read_text() == key:
        r = json.loads(rep.read_text(encoding="utf-8"))
        if len(frames) >= r["frames"]:
            r["cached"] = True
            r["wall_s"] = 0
            return r
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp.write_text(key)
    return None


def fill_frames(frames_dir: Path) -> None:
    """Rendu « une image sur deux » : recopie l'image précédente dans les trous (numérotation continue)."""
    nums = sorted(int(p.stem[2:]) for p in frames_dir.glob("f_*.png"))
    if not nums:
        return
    have = set(nums)
    for n in range(nums[0], nums[-1] + 2):
        if n not in have and (n - 1) in have or (n not in have and n - 1 >= nums[0]):
            src = frames_dir / f"f_{n - 1:04d}.png"
            dst = frames_dir / f"f_{n:04d}.png"
            if src.exists() and not dst.exists():
                shutil.copyfile(src, dst)
                have.add(n)


def assemble(out: Path, frames_dir: Path, mp4_name: str, fps: int = 30) -> Path:
    fill_frames(frames_dir)
    fonts_rel = os.path.relpath(config.FONTS, out).replace("\\", "/")
    frames_rel = os.path.relpath(frames_dir, out).replace("\\", "/")
    vf = f"scale=1080:1920:flags=lanczos,ass=subs.ass:fontsdir={fonts_rel},format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{frames_rel}/f_%04d.png",
                    "-i", "mix.wav", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-profile:v", "high", "-level", "4.1", "-r", str(fps), "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", mp4_name], cwd=out, check=True)
    return out / mp4_name


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def produce(ep_path: Path, profile: str = "final", log=print) -> dict:
    ep = load_episode(ep_path)
    out = config.OUTPUT / "episodes" / ep["id"]
    out.mkdir(parents=True, exist_ok=True)
    report = {"episode": ep["id"], "profile": profile, "steps": {}}

    t = time.time()
    ed = editorial.check(ep)
    report["editorial"] = ed
    log(f"[éditorial] {ed['decision']} ({ed['word_count']} mots)")
    if ed["decision"] == "rejected":
        report["status"] = "rejected"
        return report

    t = time.time()
    tl = audio.build_narration(ep, out)
    report["steps"]["voix_s"] = round(time.time() - t, 1)
    log(f"[voix] {tl['total']:.2f} s de timeline, {len(tl['segments'])} segments")

    t = time.time()
    job = build_job(ep, tl, out, profile)
    rr = cached_render(job) or render(job, out / f"blender_{profile}.log")
    report["render"] = rr
    report["steps"]["rendu_s"] = round(time.time() - t, 1)
    log(f"[3D] {rr['frames']} images en {rr['wall_s']} s ({rr['engine']}, {rr['res']})")

    t = time.time()
    cuts = [s["start"] for s in tl["shots"][1:]]
    audio.make_music(tl["total"], out / "music.wav")
    audio.make_whooshes(cuts, tl["total"], out / "whoosh.wav")
    if config.get("MEME_SFX") != "false":
        qc = [tuple(c) for c in tl.get("quote_cues", [])]
        report["sfx"] = [c for c in audio.meme_cues(ep, tl) if c[1] not in {q[1] for q in qc}] + qc
        audio.add_sfx(out / "whoosh.wav", report["sfx"])
    report["loudnorm_pass1"] = audio.mix(out, tl["total"])
    if ep.get("caption_style", "words") == "words":
        subs = captions_v2.build(ep, tl, out / "subs.ass")
    else:
        subs = subtitles.build_ass(ep, tl, out / "subs.ass")
    frames = Path(json.loads(job.read_text(encoding="utf-8"))["out_dir"]) / "frames"
    name = f"{ep['id']}{'' if profile == 'final' else '_' + profile}.mp4"
    mp4 = assemble(out, frames, name)
    report["steps"]["montage_s"] = round(time.time() - t, 1)
    log(f"[montage] {mp4.name}")

    res = (1080, 1920) if profile != "preview" else (540, 960)
    q = qa.run(mp4, tl, subs, res)
    report["qa"] = q
    log(f"[QA] {'OK' if q['passed'] else 'ÉCHEC'} — " + ", ".join(c["check"] for c in q["checks"] if not c["ok"]))

    if profile == "final":
        rdir = Path(json.loads(job.read_text(encoding="utf-8"))["out_dir"])
        still = rdir / f"{ep.get('cover_still', 'still_cover')}.png"
        pub = out / "publication"
        pub.mkdir(exist_ok=True)
        cover.make_cover(still, ep["title_cover"], f"{ep['city_name']} · ép. {ep['episode_number']}",
                         pub / "cover.jpg")
        shutil.copy(mp4, pub / "video.mp4")
        cap = ep["caption"]
        if tl.get("voice", {}).get("engine") == "elevenlabs" and "elevenlabs" not in cap.lower():
            cap = cap.rstrip() + "\n\n" + tl["voice"]["attribution"]   # mention exigée par l'offre gratuite
        (pub / "caption.txt").write_text(cap, encoding="utf-8")
        if ep.get("seo"):
            (pub / "seo.json").write_text(json.dumps(ep["seo"], ensure_ascii=False, indent=2), encoding="utf-8")
        voice = tl["voice"]
        credits = ("Crédits et licences\n"
                   f"- {voice['attribution']}\n"
                   + ({"azure": "- Synthèse vocale : Azure AI Speech (voix neuronale standard).\n",
                       "elevenlabs": "- Synthèse vocale : ElevenLabs.\n"}.get(voice.get("engine"),
                                                                            "- Moteur de synthèse : Piper (piper1-gpl, GPL-3.0).\n")) +
                   "- Musique et effets : créations originales générées par le projet (lbf/audio.py).\n"
                   "- Fontes : Archivo Black et Anton, SIL Open Font License 1.1.\n"
                   "- Décors, personnages et mascotte : modélisés par le projet dans Blender (GPL pour le logiciel ; "
                   "les rendus appartiennent au créateur).\n")
        (pub / "CREDITS.txt").write_text(credits, encoding="utf-8")
        manifest = {"episode_id": ep["id"], "status": "qa_passed" if q["passed"] and ed["decision"] == "pass"
                    else ("needs_review" if q["passed"] else "failed"),
                    "published": False, "video_sha256": sha256(pub / "video.mp4"),
                    "duration_s": q["duration"], "size_mb": q["size_mb"], "cover": "cover.jpg",
                    "caption_file": "caption.txt", "disclosure": ep.get("disclosure", ""),
                    "platform_flags": {"ai_label": False, "paid_partnership": False},
                    "youtube_shorts_compatible": q["duration"] <= 60,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        (pub / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        report["status"] = manifest["status"]
    else:
        report["status"] = "preview_done"
    (out / f"report_{profile}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    prof = sys.argv[2] if len(sys.argv) > 2 else "final"
    r = produce(Path(sys.argv[1]), prof)
    print(json.dumps({k: r[k] for k in ("status", "steps")}, ensure_ascii=False))
