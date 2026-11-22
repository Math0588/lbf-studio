"""Mesure / test visuel dans GitHub Actions : quelques images d'un épisode (qualité donnée), planche publiée dans la
release « bench » pour vérification (gestes des personnages, cadrage)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from . import audio, config, planner_v2, produce

q = sys.argv[1] if len(sys.argv) > 1 else "cloud"
script = json.loads((config.CONTENT / "scripts" / "macronville_pilot_01.json").read_text(encoding="utf-8"))
# gestes de test
script["scenes"][1]["actions"] = [{"who": "perso", "geste": "shrug", "visage": "blase"},
                                  {"who": "maire", "geste": "point", "visage": "fier", "quand": 0.1}]
script["scenes"][2]["actions"] = [{"who": "foule", "geste": "manif"}, {"who": "maire", "geste": "cough", "visage": "blase"}]
script["scenes"][4]["actions"] = [{"who": "maire", "geste": "arms_up", "visage": "colere", "quand": 0.05},
                                  {"who": "foule", "geste": "jump", "quand": 0.05}]
sp = config.OUTPUT / "bench_script.json"
sp.parent.mkdir(parents=True, exist_ok=True)
sp.write_text(json.dumps(script, ensure_ascii=False))
ep_path = planner_v2.plan_file(sp)
ep = produce.load_episode(ep_path)
out = config.OUTPUT / "bench"
out.mkdir(parents=True, exist_ok=True)
tl = audio.build_narration(ep, out)
job = produce.build_job(ep, tl, out, "final")
j = json.loads(job.read_text())
starts, fr = {}, 1
for s in tl["shots"]:
    starts[s["id"]] = (fr, round(s["dur"] * 30))
    fr += round(s["dur"] * 30)
picks = []
for sid in ("s2a", "s3a", "s5a"):
    a, n = starts[sid]
    picks += [a + int(n * x) for x in (0.1, 0.45, 0.8)]
j["quality"], j["stills"], j["out_dir"] = q, [], str(out / f"render_{q}")
j["frame_range"] = [min(picks), max(picks)]
job.write_text(json.dumps(j))
t = time.time()
# rendu image par image des seules images choisies (rapide)
frames = []
for f in picks:
    jj = dict(j, frame_range=[f, f])
    job.write_text(json.dumps(jj))
    r = subprocess.run([config.blender_path(), "-b", "--factory-startup", "-noaudio", "-P", str(config.BLENDER_ENGINE),
                        "--", str(job)], capture_output=True, text=True, timeout=900)
    print(r.stdout[-800:], r.stderr[-800:], flush=True)
    frames.append(Path(j["out_dir"]) / "frames" / f"f_{f:04d}.png")
print(f"BENCH {q}: {len(picks)} images en {time.time() - t:.0f} s", flush=True)
from PIL import Image
ims = [Image.open(p).resize((270, 480)) for p in frames if p.exists()]
sheet = Image.new("RGB", (280 * len(ims), 480), "white")
for i, im in enumerate(ims):
    sheet.paste(im, (i * 280, 0))
sheet.save(out / "planche_gestes.png")
subprocess.run(["gh", "release", "create", "bench", "--title", "Tests", "--notes", "tests visuels", "--latest=false"],
               capture_output=True)
subprocess.run(["gh", "release", "upload", "bench", str(out / "planche_gestes.png"), "--clobber"], check=True)
