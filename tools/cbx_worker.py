"""Synthèse Chatterbox Multilingual (Resemble AI, licence MIT) : tourne dans son propre environnement Python.
Entrée : un JSON {"items": [{"text": ..., "out": ...}], "ref": chemin ou null, "exaggeration": 0.7, "cfg": 0.3,
"seed": 0}. Graine fixée par phrase : même texte → même audio (resynchronisation possible)."""
import json
import sys
import time

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

job = json.load(open(sys.argv[1], encoding="utf-8"))
t0 = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
print(f"[cbx] modèle chargé en {time.time() - t0:.0f} s", flush=True)
for i, it in enumerate(job["items"]):
    t = time.time()
    torch.manual_seed(int(job.get("seed", 0)) + i)
    kw = {"language_id": "fr", "exaggeration": float(job.get("exaggeration", 0.7)),
          "cfg_weight": float(job.get("cfg", 0.3))}
    if job.get("ref"):
        kw["audio_prompt_path"] = job["ref"]
    wav = model.generate(it["text"], **kw)
    ta.save(it["out"], wav, model.sr)
    print(f"[cbx] {it['out']} : {wav.shape[-1] / model.sr:.1f} s d'audio en {time.time() - t:.0f} s", flush=True)
