"""Commandes ponctuelles (le fonctionnement quotidien n'en demande aucune)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import db, planner, produce, tts, veille, worker


def main(argv):
    if not argv:
        print("Commandes : diagnostic | episode <fichier.json> [preview|final] | planifier <script.json> | "
              "veille | sauvegarder | restaurer <fichier.db> | cycle")
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "diagnostic":
        from . import config
        print(json.dumps({"blender": config.blender_path(), "voix": tts.voice_report(config.get("VOICE_MODEL")),
                          "disque_libre_go": worker.disk_free_gb(), "mode_gratuit": config.flag("FREE_MODE"),
                          "publication_reelle": config.flag("LIVE_PUBLISH")}, ensure_ascii=False, indent=2))
    elif cmd == "episode":
        r = produce.produce(Path(args[0]), args[1] if len(args) > 1 else "final")
        print(r.get("status"))
    elif cmd == "planifier":
        print(planner.plan_file(Path(args[0])))
    elif cmd == "veille":
        print(veille.run())
    elif cmd == "sauvegarder":
        print(db.backup())
    elif cmd == "restaurer":
        db.restore(Path(args[0]))
        print("restauré ; vérification :", db.connect().execute("SELECT COUNT(*) FROM episodes").fetchone()[0], "épisodes")
    elif cmd == "cycle":
        return worker.main(loop=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
