"""Audio : timeline de narration, musique originale procédurale (aucune licence tierce), effets, mixage."""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

from . import tts

SR = 48000
GAP = 0.32  # silence entre deux segments d'un même plan


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
    if sr != SR:
        n = int(len(data) * SR / sr)
        data = np.interp(np.linspace(0, len(data) - 1, n), np.arange(len(data)), data).astype(np.float32)
    return data


def write_wav(path: Path, data: np.ndarray, stereo: bool = False) -> None:
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype(np.int16)
    if stereo and pcm.ndim == 1:
        pcm = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2 if stereo else 1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def build_narration(ep: dict, out: Path) -> dict:
    """Synthétise chaque segment, calcule la durée de chaque plan depuis l'audio réel, écrit narration.wav."""
    audio_dir = out / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    segs = {s["id"]: s for s in ep["narration_segments"]}
    durs = {}
    import hashlib
    for sid, s in segs.items():
        ls = ep.get("voice_length_scale")
        key = hashlib.sha1((tts.config.get("VOICE_MODEL") + "|" + str(ls) + "|" + s["text"]).encode()).hexdigest()
        wav, stamp = audio_dir / f"{sid}.wav", audio_dir / f"{sid}.key"
        if wav.exists() and stamp.exists() and stamp.read_text() == key:   # cache : même texte, même voix
            with wave.open(str(wav), "rb") as wf:
                durs[sid] = wf.getnframes() / float(wf.getframerate())
        else:
            durs[sid] = tts.synthesize(s["text"], wav, length_scale=ls)
            stamp.write_text(key)
    timeline = []   # (segment_id, start, end)
    shots = []
    t = 0.0
    for sc in ep["scenes"]:
        start = t
        t += sc.get("lead_in", 0.12)
        for i, nid in enumerate(sc["narration_ids"]):
            if i:
                t += GAP
            timeline.append({"id": nid, "start": round(t, 3), "end": round(t + durs[nid], 3)})
            t += durs[nid]
        t += sc.get("tail", 0.25)
        if not sc["narration_ids"]:
            t = start + sc.get("dur", 1.5)   # plan muet (insert visuel, carte de fin)
        shots.append({"id": sc["id"], "start": round(start, 3), "dur": round(t - start, 3)})
    total = t
    track = np.zeros(int(total * SR) + SR // 10, dtype=np.float32)
    for seg in timeline:
        d = read_wav(audio_dir / f"{seg['id']}.wav")
        i = int(seg["start"] * SR)
        track[i:i + len(d)] += d[: len(track) - i]
    write_wav(out / "narration.wav", track)
    info = {"total": round(total, 3), "segments": timeline, "shots": shots,
            "voice": tts.voice_report(tts.config.get("VOICE_MODEL"))}
    (out / "timeline.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


# ----------------------------------------------------------------- musique originale (générée, CC0 de fait)

def _env(n, a=0.005, r=0.25):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def _pluck(freq, dur, bright=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + bright * 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return (s * _env(n, 0.003, 0.18)).astype(np.float32)


def _kick(dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 110 * np.exp(-t * 18) + 45
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)


def _hat(dur=0.06, seed=0):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n).astype(np.float32)
    x = np.diff(x, prepend=0)  # passe-haut grossier
    return x * np.exp(-np.arange(n) / SR * 60) * 0.3


def make_music(total: float, path: Path, bpm: float = 104, seed: int = 1) -> None:
    """Petite boucle « pizzicato ironique » en do majeur, originale et générée localement."""
    beat = 60 / bpm
    n = int((total + 1) * SR)
    mix = np.zeros(n, dtype=np.float32)
    notes = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "B3": 246.94,
             "G3": 196.0, "C5": 523.25, "A3": 220.0, "F3": 174.61}
    motif = ["C4", "E4", "G4", "E4", "F4", "A4", "G4", None, "E4", "D4", "C4", "D4", "E4", None, "G3", None]
    bass = ["C3", "C3", "F3", "G3"]
    bfreq = {"C3": 130.81, "F3": 174.61, "G3": 196.0}
    step = beat / 2
    i = 0
    t = 0.0
    while t < total + 0.5:
        nt = motif[i % len(motif)]
        if nt:
            s = _pluck(notes[nt], step * 1.6, 0.6) * 0.22
            k = int(t * SR)
            mix[k:k + len(s)] += s[: n - k]
        if i % 2 == 0:
            h = _hat(seed=i) * 0.25
            k = int(t * SR)
            mix[k:k + len(h)] += h[: n - k]
        if i % 4 == 0:
            kk = _kick() * 0.5
            k = int(t * SR)
            mix[k:k + len(kk)] += kk[: n - k]
        if i % 8 == 0:
            b = _pluck(bfreq[bass[(i // 8) % 4]], beat * 3.5, 0.2) * 0.3
            k = int(t * SR)
            mix[k:k + len(b)] += b[: n - k]
        i += 1
        t += step
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= max(1e-6, np.abs(mix).max()) / 0.7
    write_wav(path, mix[: int(total * SR)])


def make_whooshes(times: list, total: float, path: Path) -> None:
    n = int(total * SR) + SR
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(7)
    for t in times:
        d = int(0.38 * SR)
        x = rng.standard_normal(d).astype(np.float32)
        # bruit filtré par moyenne glissante dont la largeur décroît : balayage montant
        y = np.zeros(d, dtype=np.float32)
        acc = 0.0
        for j in range(d):
            a = 0.02 + 0.5 * j / d
            acc += a * (x[j] - acc)
            y[j] = acc
        env = np.sin(np.linspace(0, np.pi, d)) ** 2
        k = max(0, int((t - 0.19) * SR))
        seg = (y * env * 0.5)[: n - k]
        out[k:k + len(seg)] += seg
    write_wav(path, out[: int(total * SR)])


def mix(out: Path, total: float) -> dict:
    """Voix au premier plan, musique atténuée sous la voix (sidechain), normalisation EBU R128 en 2 passes."""
    raw = out / "mix_raw.wav"
    fc = ("[1:a]volume=0.32[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[md];"
          "[0:a]highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120,volume=1.0[v];"
          "[2:a]volume=0.5[w];[v][md][w]amix=inputs=3:normalize=0:duration=first[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "narration.wav", "-i", "music.wav", "-i",
                    "whoosh.wav", "-filter_complex", fc, "-map", "[a]", "-ar", str(SR), "-ac", "2", raw.name],
                   cwd=out, check=True)
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw.name, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       cwd=out, capture_output=True, text=True, encoding="utf-8", errors="replace")
    js = p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw.name, "-af", af, "-ar", str(SR), "mix.wav"],
                   cwd=out, check=True)
    return m
