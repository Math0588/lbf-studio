"""Audio : timeline de narration, musique originale procédurale (aucune licence tierce), effets, mixage."""
from __future__ import annotations

import json
import re
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
    from . import tts_azure, voix_externe
    eng = tts_azure.engine()
    ext = voix_externe.available(ep)
    ext_files = voix_externe.split(ext, len(segs), audio_dir / "ext") if ext else None
    if ext_files:
        eng = "externe"
    voice_info = None
    last_id = ep["narration_segments"][-2]["id"] if len(ep["narration_segments"]) > 1 else None
    for sid, s in segs.items():
        ls = ep.get("voice_length_scale")
        vname = (tts_azure.config.get("AZURE_VOICE") or tts_azure.DEFAULT_VOICE) if eng == "azure" \
            else tts.config.get("VOICE_MODEL")
        key = hashlib.sha1((eng + "|" + vname + "|" + str(ls) + "|" + s["text"]).encode()).hexdigest()
        wav, stamp = audio_dir / f"{sid}.wav", audio_dir / f"{sid}.key"
        if eng == "externe":
            import shutil as _sh
            idx = list(segs).index(sid)
            _sh.copyfile(ext_files[idx], wav)
            with wave.open(str(wav), "rb") as wf:
                durs[sid] = wf.getnframes() / float(wf.getframerate())
            voice_info = {"engine": "elevenlabs", "attribution": voix_externe.ATTRIBUTION}
            continue
        if wav.exists() and stamp.exists() and stamp.read_text() == key:   # cache : même texte, même voix
            with wave.open(str(wav), "rb") as wf:
                durs[sid] = wf.getnframes() / float(wf.getframerate())
            continue
        if eng == "azure":
            try:
                durs[sid] = tts_azure.synthesize(s["text"], wav, s.get("accent_words"), last=(sid == last_id))
                voice_info = tts_azure.report()
                stamp.write_text(key)
                continue
            except Exception as e:  # quota, réseau… : secours Piper pour tout l'épisode
                print(f"[voix] Azure indisponible ({e}) : secours Piper")
                eng = "piper"
                key = hashlib.sha1(("piper|" + tts.config.get("VOICE_MODEL") + "|" + str(ls) + "|"
                                    + s["text"]).encode()).hexdigest()
        durs[sid] = tts.synthesize(s["text"], wav, length_scale=ls)
        stamp.write_text(key)
    quotes = quote_clips(ep)        # vraie réplique du politicien juste après la phrase qui la cite
    quote_cues = []
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
            if nid in quotes:
                f, qd = quotes[nid]
                quote_cues.append((round(t + 0.08, 3), "clip:" + f))
                t += qd + 0.18
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
    info = {"total": round(total, 3), "segments": timeline, "shots": shots, "quote_cues": quote_cues,
            "voice": voice_info if eng in ("azure", "externe") and voice_info else tts.voice_report(tts.config.get("VOICE_MODEL"))}
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


# ----------------------------------------------------------------- bruitages « mèmes » (synthétisés, libres de droits)

def _sfx(kind: str, rng) -> np.ndarray:
    def t_(d):
        return np.arange(int(d * SR)) / SR
    if kind == "boom":          # basse qui tombe, façon « vine boom »
        t = t_(1.1)
        f = 62 * np.exp(-t * 1.4) + 34
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
        x[: int(0.004 * SR)] += rng.standard_normal(int(0.004 * SR)) * 0.6
        return np.tanh(x * 2.2) * 0.95
    if kind == "explosion":     # souffle grave + grondement
        t = t_(1.6)
        n = rng.standard_normal(len(t))
        y, acc = np.zeros_like(n), 0.0
        for j in range(len(n)):
            acc += (0.02 + 0.25 * np.exp(-t[j] * 6)) * (n[j] - acc)
            y[j] = acc
        boom = _sfx("boom", rng)
        boom = np.pad(boom, (0, max(0, len(t) - len(boom))))[: len(t)]
        return np.tanh(y * 6 * np.exp(-t * 2.4) + boom * 0.7) * 0.95
    if kind == "scratch":       # scratch de vinyle
        t = t_(0.32)
        f = 900 + 700 * np.sin(2 * np.pi * 9 * t)
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25 + rng.standard_normal(len(t)) * 0.35
        return x * np.sin(np.linspace(0, np.pi, len(t))) * 0.8
    if kind == "airhorn":       # trois coups de corne
        out = []
        for d in (0.16, 0.16, 0.42):
            t = t_(d)
            x = sum(((2 * ((f * t) % 1) - 1)) for f in (466, 470, 587, 698)) / 4
            out += [np.tanh(x * 2.5) * np.minimum(1, t / 0.01) * 0.8, np.zeros(int(0.05 * SR))]
        return np.concatenate(out)
    if kind == "trombone":      # « wah wah wah waaah »
        out = []
        for f0, d in ((233, 0.38), (220, 0.38), (208, 0.38), (196, 1.0)):
            t = t_(d)
            f = f0 * (1 + (0.02 * np.sin(2 * np.pi * 6 * t) if d > 0.5 else 0))
            ph = 2 * np.pi * np.cumsum(f) / SR
            x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)) / 1.8
            out.append(x * np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.08) * 0.7)
        return np.concatenate(out)
    if kind == "ding":
        t = t_(0.9)
        return (np.sin(2 * np.pi * 1760 * t) + 0.4 * np.sin(2 * np.pi * 2640 * t)) * np.exp(-t * 5) * 0.5
    raise ValueError(kind)


def meme_cues(ep: dict, timeline: dict) -> list:
    """Bruitages avec parcimonie (1 à 3 par vidéo), choix déterministe par épisode.
    Chute (avant-dernière phrase) : boom / explosion / trombone ; retournement de la phrase 2 : scratch ;
    parfois une corne sur une citation exacte."""
    import hashlib
    h = int(hashlib.sha1(ep["id"].encode()).hexdigest(), 16)
    segs = timeline["segments"]
    kinds = {s["id"]: s.get("claim_type") for s in ep["narration_segments"]}
    cues = []
    if len(segs) < 3:
        return cues
    bank = meme_bank()
    city = ep.get("city_id") or ep.get("city")

    def pick(role, salt):
        c = [m for m in bank if role in m.get("role", []) and (not m.get("cities") or city in m["cities"])]
        own = [m for m in c if m.get("cities")]          # son propre à la ville en priorité (ex. Macron explosion)
        c = own or c
        return ("clip:" + c[(h >> salt) % len(c)]["file"]) if c else None

    punch = segs[-2]
    cues.append((punch["end"] + 0.05, pick("chute", 1) or ["boom", "explosion", "trombone", "boom"][h % 4]))
    if (h >> 3) % 2 == 0:
        cues.append((segs[1]["end"] + 0.02, pick("retournement", 4) or "scratch"))
    mids = [s for s in segs[2:-2] if kinds.get(s["id"]) in ("citation_exacte", "fait_public")]
    if mids and (h >> 5) % 3 == 0 and len(cues) < 2:
        cues.append((mids[0]["end"] + 0.02, pick("scandale", 6) or "airhorn"))
    return cues


def _n(x: str) -> str:
    import unicodedata
    x = unicodedata.normalize("NFKD", x.lower())
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in x if not unicodedata.combining(c))).split())


def quote_clips(ep: dict, limit: int = 2) -> dict:
    """{segment_id: (fichier, durée)} pour les phrases qui citent une réplique dont on a le vrai son validé."""
    city = ep.get("city_id") or ep.get("city")
    bank = [m for m in meme_bank() if m.get("quote_match") and (not m.get("cities") or city in m["cities"])]
    out = {}
    for seg in ep["narration_segments"]:
        if len(out) >= limit:
            break
        words = f" {_n(seg['text'])} "
        for m in bank:
            if f" {_n(m['quote_match'])} " in words and m["file"] not in [v[0] for v in out.values()]:
                out[seg["id"]] = (m["file"], float(m.get("duration") or 2.0))
                break
    return out


def meme_bank() -> list:
    """Sons mèmes réels téléchargés (assets/memes/manifest.json), vide sinon."""
    from . import config
    p = config.ASSETS / "memes" / "manifest.json"
    if not p.exists():
        return []
    return [m for m in json.loads(p.read_text(encoding="utf-8"))
            if m.get("ok") and m.get("approved") and (config.ASSETS / "memes" / m["file"]).exists()]


def add_sfx(path: Path, cues: list) -> None:
    """Ajoute les bruitages à la piste d'effets existante (whoosh.wav)."""
    base = read_wav(path)
    rng = np.random.default_rng(11)
    from . import config
    for t, kind in cues:
        if kind.startswith("clip:"):
            x = read_wav(config.ASSETS / "memes" / kind[5:]) * 0.9
        else:
            x = _sfx(kind, rng).astype(np.float32)
        k = int(t * SR)
        if k >= len(base):
            continue
        seg = x[: len(base) - k]
        base[k:k + len(seg)] += seg
    write_wav(path, base)
