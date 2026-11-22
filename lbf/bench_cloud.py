"""Mesure rapide de la vitesse de rendu dans GitHub Actions : 20 images d'un épisode, qualité cloud."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from . import audio, config, planner_v2, produce

q = sys.argv[1] if len(sys.argv) > 1 else "cloud"
ep_path = planner_v2.plan_file(config.CONTENT / "scripts" / "macronville_pilot_01.json")
ep = produce.load_episode(ep_path)
out = config.OUTPUT / "bench"
out.mkdir(parents=True, exist_ok=True)
t = time.time()
tl = audio.build_narration(ep, out)
print(f"voix : {time.time() - t:.1f} s, durée {tl['total']:.1f} s", flush=True)
job = produce.build_job(ep, tl, out, "final")
j = json.loads(job.read_text())
j["quality"], j["frame_range"], j["stills"], j["out_dir"] = q, [1, 20], [], str(out / f"render_{q}")
job.write_text(json.dumps(j))
t = time.time()
r = subprocess.run([config.blender_path(), "-b", "--factory-startup", "-noaudio", "-P", str(config.BLENDER_ENGINE),
                    "--", str(job)], capture_output=True, text=True, timeout=1500)
print(r.stdout[-3000:], r.stderr[-2000:], flush=True)
el = time.time() - t
tot = round(tl["total"] * 30)
print(f"BENCH {q}: 20 images en {el:.0f} s (construction incluse) ; épisode = {tot} images", flush=True)
