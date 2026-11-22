"""Tests du cahier des charges (§18). Lancer : python -m unittest discover -s tests -v"""
import datetime as dt
import importlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONUTF8"] = "1"

from lbf import captions_v2, config, db, editorial, tts  # noqa: E402


def base_episode(**kw):
    ep = {"id": "t-s01e01", "city_id": "bardellaville", "episode_number": 1, "caption": "x",
          "disclosure": "", "cta_primary": {"type": "comment", "text": "?"}, "cta_commercial": {"text": "bio"},
          "sources": [], "narration_segments": [
              {"id": f"n{i}", "text": "Dans cette ville le rond point a un ring light géant et brillant.",
               "claim_type": "fiction_satirique"} for i in range(6)]}
    ep.update(kw)
    return ep


class ModeGratuit(unittest.TestCase):
    def test_aucune_depense_en_mode_gratuit(self):
        with mock.patch.dict(os.environ, {"FREE_MODE": "true", "MAX_API_SPEND": "0"}):
            with self.assertRaises(PermissionError):
                config.assert_free_mode_spend(0.01, "appel payant")

    def test_x_desactive(self):
        from lbf import veille
        with mock.patch.dict(os.environ, {"X_ENABLED": "false"}):
            self.assertEqual(veille.fetch_x(), [])
        with mock.patch.dict(os.environ, {"X_ENABLED": "true", "FREE_MODE": "true"}):
            self.assertEqual(veille.fetch_x(), [])


class Editorial(unittest.TestCase):
    def test_citation_sans_source_bloquee(self):
        ep = base_episode()
        ep["narration_segments"][0]["claim_type"] = "citation_exacte"
        self.assertEqual(editorial.check(ep)["decision"], "rejected")

    def test_citation_sourcee_passe(self):
        ep = base_episode(sources=[{"url": "https://exemple.fr", "date": "2026-11-21"}])
        ep["narration_segments"][0]["claim_type"] = "citation_exacte"
        self.assertEqual(editorial.check(ep)["decision"], "pass")

    def test_motif_sensible_en_relecture(self):
        ep = base_episode()
        ep["narration_segments"][1]["text"] = "Le maire a été condamné hier."
        self.assertEqual(editorial.check(ep)["decision"], "needs_review")


class Licences(unittest.TestCase):
    def test_voix_non_autorisee_bloquee(self):
        with self.assertRaises(PermissionError):
            tts.synthesize("test", Path(tempfile.gettempdir()) / "x.wav", model="fr_FR-tom-medium")

    def test_voix_retenue_valide(self):
        self.assertTrue(tts.check_voice("fr_FR-siwis-medium")["hash_ok"])


class SousTitres(unittest.TestCase):
    def test_pas_de_debordement(self):
        ep = base_episode()
        ep["narration_segments"] = [{"id": "n1", "text": "Anticonstitutionnellement, l'arrière-boutique-studio.",
                                     "claim_type": "fiction_satirique"}]
        tl = {"segments": [{"id": "n1", "start": 0, "end": 3}], "shots": [{"id": "s1", "start": 0, "dur": 3}],
              "total": 3}
        r = captions_v2.build(ep, tl, Path(tempfile.gettempdir()) / "t.ass")
        self.assertTrue(all(c["max_px"] <= 960 for c in r["cards"]), r["cards"])


class FileEtReprise(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.con = db.connect(self.tmp / "t.db")
        for i in range(2):
            self.con.execute("INSERT INTO episodes(id,state,created,updated) VALUES(?,?,?,?)",
                             (f"e{i}", "render_queued", db.now(), db.now()))

    def test_verrou_pas_de_doublon(self):
        a = db.claim_episode(self.con, "w1")
        b = db.claim_episode(self.con, "w2")
        self.assertNotEqual(a, b)
        self.assertIsNone(db.claim_episode(self.con, "w3"))

    def test_reprise_apres_expiration(self):
        a = db.claim_episode(self.con, "w1")
        past = (dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds")
        self.con.execute("UPDATE episodes SET lock_until=? WHERE id=?", (past, a))
        self.assertIsNotNone(db.claim_episode(self.con, "w2"))

    def test_sauvegarde_restauration(self):
        with mock.patch.object(db, "BACKUPS", self.tmp / "bk"), mock.patch.object(db, "DB_PATH", self.tmp / "t.db"):
            b = db.backup(self.con)
            self.con.execute("DELETE FROM episodes")
            self.con.close()
            db.restore(b)
            n = sqlite3.connect(self.tmp / "t.db").execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            self.assertEqual(n, 2)


class Diffuseur(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        sys.path.insert(0, str(ROOT / "cloud"))
        import publisher
        self.p = importlib.reload(publisher)
        self.p.ROOT, self.p.RESERVE, self.p.STATE = self.tmp, self.tmp / "reserve", self.tmp / "state"
        d = self.tmp / "reserve" / "e1"
        d.mkdir(parents=True)
        (d / "video.mp4").write_bytes(b"0")
        (d / "caption.txt").write_text("Légende unique e1", encoding="utf-8")
        (d / "manifest.json").write_text('{"video_sha256": "x"}', encoding="utf-8")
        (self.tmp / "reserve" / "queue.json").write_text('[{"episode_id": "e1"}]', encoding="utf-8")
        self.env = {"LIVE_PUBLISH": "true", "IG_ACCESS_TOKEN": "tok", "IG_USER_ID": "1"}
        # aucun appel réseau réel dans les tests : ni GitHub (release privée) ni envoi de vidéo
        from types import SimpleNamespace
        self.p.gh = lambda *a: SimpleNamespace(returncode=1, stdout="", stderr="test")
        self.uploads = []
        self.p.upload_video = lambda uri, path: self.uploads.append((uri, path.name)) or {"success": True}
        self.p.signed_asset_url = lambda name: f"https://signed.invalid/{name}?sig=x"

    def pubs(self):
        return json.loads((self.tmp / "state" / "publications.json").read_text(encoding="utf-8"))

    def test_simulation_jamais_publie(self):
        with mock.patch.dict(os.environ, {"LIVE_PUBLISH": "false"}):
            self.p.main.__globals__["sys"].argv = ["x", "--force"]
            self.p.main()
        self.assertEqual(self.pubs()[0]["status"], "simulated")

    def test_pause_empeche_publication(self):
        (self.tmp / "state").mkdir(exist_ok=True)
        (self.tmp / "state" / "control.json").write_text('{"paused": true}', encoding="utf-8")
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.p, "call") as c:
            self.p.main()
            c.assert_not_called()

    def test_timeout_reconciliation_sans_doublon(self):
        calls = []

        posted = []

        def fake(method, path, params=None, timeout=60):
            calls.append(path)
            if path.endswith("/media") and method == "POST":
                posted.append(params or {})
            if path.endswith("content_publishing_limit"):
                return {}
            if path.endswith("/media") and method == "POST":
                return {"id": "c1"}
            if path == "c1":
                return {"status_code": "FINISHED"}
            if path.endswith("media_publish"):
                raise TimeoutError("timeout")
            if path.endswith("/media") and method == "GET":
                return {"data": [{"id": "m9", "caption": "Légende unique e1", "permalink": "https://ig/p/m9"}]}
            return {}
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.p, "call", side_effect=fake), \
                mock.patch.object(self.p.time, "sleep"), mock.patch.object(sys, "argv", ["x", "--force"]):
            self.p.main()
        pub = self.pubs()[0]
        self.assertEqual(pub["status"], "published")
        self.assertTrue(pub.get("reconciled"))
        self.assertEqual(sum(1 for c in calls if c.endswith("media_publish")), 1)
        # vidéo fournie par lien signé temporaire vers la release privée (aucune adresse publique permanente)
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["video_url"], "https://signed.invalid/e1.mp4?sig=x")
        self.assertEqual(self.uploads, [])

    def test_envoi_direct_si_demande(self):
        def fake(method, path, params=None, timeout=60):
            if path.endswith("/media") and method == "POST":
                return {"id": "c2"}
            if path == "c2":
                return {"status_code": "FINISHED"}
            if path.endswith("media_publish"):
                return {"id": "m2"}
            return {}
        env = {**self.env, "IG_UPLOAD_METHOD": "resumable"}
        with mock.patch.dict(os.environ, env), mock.patch.object(self.p, "call", side_effect=fake),                 mock.patch.object(self.p.time, "sleep"), mock.patch.object(sys, "argv", ["x", "--force"]):
            self.p.main()
        self.assertEqual(self.pubs()[0]["status"], "published")
        self.assertEqual(len(self.uploads), 1)
        self.assertTrue(self.uploads[0][0].endswith("/c2"))

    def test_jeton_expire_pas_de_faux_publie(self):
        def fake(method, path, params=None, timeout=60):
            raise self.p.ApiError(401, "token expired")
        with mock.patch.dict(os.environ, self.env), mock.patch.object(self.p, "call", side_effect=fake), \
                mock.patch.object(sys, "argv", ["x", "--force"]):
            with self.assertRaises(self.p.ApiError):
                self.p.main()
        p = self.tmp / "state" / "publications.json"
        statuses = [x["status"] for x in json.loads(p.read_text(encoding="utf-8"))] if p.exists() else []
        self.assertNotIn("published", statuses)


if __name__ == "__main__":
    unittest.main()


class UsineAGags(unittest.TestCase):
    def test_jamais_deux_fois_la_meme_combinaison(self):
        from lbf import gagmatrix
        tmp = Path(tempfile.mkdtemp()) / "used.json"
        with mock.patch.object(gagmatrix, "USED", tmp):
            keys, memes_week = set(), []
            for i in range(25):
                c = gagmatrix.next_candidate("bardellaville", seed=i)
                self.assertIsNotNone(c)
                self.assertNotIn(c["key"], keys)
                keys.add(c["key"])
                memes_week.append(c["meme_key"])
                gagmatrix.mark_used("bardellaville", c)
            # un même mème au plus une fois par semaine tant qu'il reste des mèmes frais
            n = len(gagmatrix.memes("bardellaville"))
            self.assertEqual(len(set(memes_week[:min(n, 25)])), min(n, 25))
