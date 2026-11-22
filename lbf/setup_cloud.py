"""Prépare le dossier du dépôt de diffusion (publication cloud, PC éteint).

Usage : python -m lbf.setup_cloud C:\\chemin\\lbf-diffusion
Crée : cloud/publisher.py, .github/workflows/publish.yml, reserve/queue.json, state/control.json, .nojekyll.
Ne crée AUCUN compte et ne pousse rien : la création du dépôt GitHub et des secrets est faite par le propriétaire
(docs/DIFFUSION_CLOUD.md)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import config


def main(target: str) -> None:
    t = Path(target)
    (t / "cloud").mkdir(parents=True, exist_ok=True)
    (t / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (t / "reserve").mkdir(exist_ok=True)
    (t / "state").mkdir(exist_ok=True)
    shutil.copy(config.ROOT / "cloud" / "publisher.py", t / "cloud" / "publisher.py")
    shutil.copy(config.ROOT / "cloud" / "youtube.py", t / "cloud" / "youtube.py")
    shutil.copy(config.ROOT / "cloud" / "workflow_publish.yml", t / ".github" / "workflows" / "publish.yml")
    q = t / "reserve" / "queue.json"
    if not q.exists():
        q.write_text("[]", encoding="utf-8")
    c = t / "state" / "control.json"
    if not c.exists():
        c.write_text(json.dumps({"paused": False, "slot": config.get("PUBLISH_SLOT")}, indent=2), encoding="utf-8")
    (t / ".nojekyll").touch()
    # page de liens (lien en bio) servie à la racine de GitHub Pages
    links = config.ROOT / "brand" / "page_liens"
    if links.exists():
        for f in links.iterdir():
            shutil.copy(f, t / f.name)
    (t / "README.md").write_text("# Diffusion — Le Bordel Français\n\nRéserve de vidéos et état de publication. "
                                 "Publié automatiquement par GitHub Actions (voir .github/workflows/publish.yml).\n",
                                 encoding="utf-8")
    if not (t / ".git").exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=t, check=True)
    env = config.ROOT / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    lines = [l for l in lines if not l.startswith("CLOUD_REPO_DIR=")] + [f"CLOUD_REPO_DIR={t}"]
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Dossier prêt : {t}\nÉtape suivante : docs/DIFFUSION_CLOUD.md (création du dépôt GitHub public + secrets).")


if __name__ == "__main__":
    main(sys.argv[1])
