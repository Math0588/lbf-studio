"""Contrôle qualité technique du MP4 rendu (mesures réelles sur le fichier)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def probe(path: Path) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                       capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(p.stdout)


def loudness(path: Path) -> dict:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    s = p.stderr[p.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", s)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", s)
    return {"integrated_lufs": float(i.group(1)) if i else None, "true_peak_dbfs": float(tp.group(1)) if tp else None}


def black_segments(path: Path) -> list:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", "blackdetect=d=0.25:pix_th=0.08",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", p.stderr)


def run(mp4: Path, timeline: dict, subs: dict, expected_res=(1080, 1920)) -> dict:
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    pr = probe(mp4)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"])
    fps = eval(v["r_frame_rate"])  # format "30/1" issu de ffprobe
    add("résolution", (v["width"], v["height"]) == tuple(expected_res), f"{v['width']}x{v['height']}")
    add("codec vidéo H.264", v["codec_name"] == "h264", v["codec_name"])
    add("30 images/s", abs(fps - 30) < 0.01, str(fps))
    add("pixel format yuv420p", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"))
    add("piste audio AAC", a is not None and a["codec_name"] == "aac", a["codec_name"] if a else "absente")
    add("durée 12–90 s", 12 <= dur <= 90, f"{dur:.2f} s")
    checks.append({"check": "durée idéale Reels ≤ 35 s (avertissement)", "ok": True, "warning": dur > 35,
                   "detail": f"{dur:.2f} s"})
    add("durée = timeline", abs(dur - timeline["total"]) < 0.25, f"{dur:.2f} vs {timeline['total']:.2f}")
    last_end = max(s["end"] for s in timeline["segments"])
    add("la voix finit avant la fin", dur - last_end >= 0.5, f"marge {dur - last_end:.2f} s")
    ld = loudness(mp4)
    add("loudness −16…−12 LUFS", ld["integrated_lufs"] is not None and -16 <= ld["integrated_lufs"] <= -12,
        f"{ld['integrated_lufs']} LUFS")
    add("crête vraie ≤ −1 dBFS", ld["true_peak_dbfs"] is not None and ld["true_peak_dbfs"] <= -1.0,
        f"{ld['true_peak_dbfs']} dBFS")
    blacks = black_segments(mp4)
    add("pas d'image noire", not blacks, str(blacks))
    over = [c for c in subs["cards"] if c["max_px"] > subs["max_px_allowed"] or c["lines"] > 2]
    add("sous-titres sans débordement (≤2 lignes)", not over, str(over))
    fast = [c for c in subs["cards"] if c["dur"] < 0.16]
    add("chaque carton reste ≥ 0,16 s à l'écran", not fast, str([(c["text"], c["dur"]) for c in fast]))
    first = timeline["segments"][0]["start"]
    add("la voix démarre avant 1,5 s", first <= 1.5, f"{first:.2f} s")
    ok = all(c["ok"] for c in checks)
    return {"passed": ok, "duration": dur, "size_mb": round(mp4.stat().st_size / 1e6, 2), "loudness": ld,
            "checks": checks}
