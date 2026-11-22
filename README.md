# Le Bordel Français — studio de satire 3D automatisé

Compte : [@lebordelfrancais](https://www.instagram.com/lebordelfrancais/) · « Liberté. Égalité. N'importe quoi. »

Des villes 3D fictives (Bardellaville, Macronville, Mélenchonville, Zemmourville, Marineville, Glucksmannville)
inspirées des codes publics des responsables politiques. Format : Reels « Dans cette ville… » avec personnages
cubiques expressifs, coupes rapides, sous-titres mot à mot, étiquettes, bulles et carte « ABONNE-TOI ».

## Démarrer (au quotidien : rien à faire)
Double-cliquer **`Demarrer.bat`** → le worker fabrique la réserve et le tableau de bord s'ouvre
(http://127.0.0.1:8765). Démarrage automatique à l'ouverture de session : `scripts\installer_demarrage_auto.ps1`.
La publication tourne dans le cloud, même PC éteint : **`docs/DIFFUSION_CLOUD.md`** (configuration unique).

## Ce qui tourne tout seul
| Étape | Où | Outil (gratuit) |
|---|---|---|
| Veille actualité (Google Actualités, Reddit, boîte `inbox/`) | PC | `lbf/veille.py` (X désactivé : payant) |
| Script : banque de ~200 scripts validés, puis Qwen3-4B local en secours | PC | `lbf/worker.py`, `lbf/writer.py` |
| Contrôle éditorial + anti-répétition | PC | `lbf/editorial.py`, `lbf/antirepeat.py` |
| Mise en scène automatique (plans, personnages, bulles, étiquettes) | PC | `lbf/planner_v2.py` |
| Voix française locale (Piper, siwis, CC BY 4.0) | PC | `lbf/tts.py` |
| Rendu 3D Blender 5.3 EEVEE (≈ 0,56 s/image en 1080×1920) | PC | `blender/engine.py` |
| Musique originale, mixage −14 LUFS, sous-titres, montage H.264/AAC | PC | `lbf/audio.py`, `lbf/captions_v2.py`, `lbf/produce.py` |
| Contrôle qualité mesuré sur le MP4 | PC | `lbf/qa.py` |
| Export de la réserve → dépôt GitHub | PC | `lbf/worker.py` |
| Publication Instagram quotidienne, jeton renouvelé, métriques 24 h/72 h/7 j | **Cloud** | `cloud/publisher.py` + GitHub Actions |
| Boutique : paiement, fabrication, expédition, SAV | **Spreadshop** | `docs/BOUTIQUE.md`, `brand/boutique/` |

## Commandes ponctuelles
```powershell
python -m lbf.cli diagnostic
python -m lbf.cli episode content\episodes\bdv-s01e01.json preview
python -m lbf.cli sauvegarder
python -m unittest discover -s tests -v
```

## Arborescence
- `content/` : bibles des villes, 200+ synopsis, scripts (pilotes + `scripts/bank/`), épisodes, décors, produits, veille.
- `blender/engine.py` : moteur 3D (JSON → constructeurs autorisés uniquement, jamais de code externe).
- `assets/` : voix (MODEL_CARD + hash), fontes OFL, visages générés.
- `brand/` : avatar (clair/sombre/32 px), designs t-shirts 4500×5400, maquettes, stories à la une, page de liens.
- `output/episodes/<id>/publication/` : vidéo, couverture, légende, crédits, manifeste (prêt ≠ publié).
- `docs/` : charte, boutique, formation, partenariats, frais & limites, Instagram, diffusion cloud, tendances,
  science de la viralité, journal des décisions, état du projet.

## Garde-fous
`FREE_MODE=true`, `MAX_API_SPEND=0`, `X_ENABLED=false`, `LIVE_PUBLISH=false` tant que la publication de contrôle
n'est pas faite. Secrets uniquement dans les secrets GitHub. Aucune fausse citation, aucun délit inventé, rien sur
les caractéristiques protégées, aucune vie privée (contrôles bloquants).
