# État du projet — 21/11/2026 (soir)

## Testé et fonctionnel
- Matériel : Core Ultra 9 275HX, 31 Go, RTX 5070 Ti 12 Go, 428 Go libres. Blender 5.3, FFmpeg 9.1, Piper, Ollama (qwen3:4b).
- Chaîne complète voix → 3D → musique → mixage → sous-titres → montage → couverture → QA → dossier de publication.
- Rendu final mesuré : 0,56 s/image en 1080×1920 (EEVEE, 32 éch.), ≈ 9–15 min par épisode selon la longueur.
- Style v2 (codes « Dans cette ville… ») : personnages cubiques à visages interchangeables, marche, parole,
  plans de 1,5–3 s, sous-titres mot à mot jaunes, étiquettes rouges, bulles, carte « ABONNE-TOI ».
- Planificateur v2 : n'importe quel script de la banque → épisode rendable sans intervention.
- Contenu : 6 villes, 207 synopsis, 11 pilotes + 195 scripts en banque (≈ 6 mois à 1/jour), veille sourcée.
- Worker autonome (verrous, reprise, tentatives, disque, pause, sauvegarde quotidienne), base SQLite v1.
- Diffuseur cloud (GitHub Actions) : simulation, pause, timeout → réconciliation, jeton expiré : testés (mocks).
- Tableau de bord : 10 écrans OK, accès distant refusé sans jeton.
- Marque : avatar (clair/sombre/32 px/rond), 12 fichiers d'impression t-shirts, maquettes, stories à la une, page de liens.
- 15 tests automatiques : OK.

## Non testé / exige le propriétaire
- Publication réelle sur Instagram (compte pro, app Meta, jeton) → docs/DIFFUSION_CLOUD.md, étapes 1–7.
- Dépôt GitHub public + Pages + secrets (création de compte/dépôt : action du propriétaire).
- Boutique Spreadshop (compte, identité, fiscalité, upload des 12 fichiers de `brand/boutique/designs`).
- Écoute humaine de la voix et des premiers épisodes (calibrage) ; qualité textile (aucun échantillon).
- Formation : plan rédigé ; mise en vente Payhip seulement quand le système aura des résultats.

## Décisions du propriétaire
- Aucune mention « IA » ni « Fiction satirique » dans les vidéos/légendes (bio : « Fictions satiriques »).
- Ton ultra provocateur, mèmes réels sourcés ; Glucksmann = 6e ville.

## Mise à jour (fin de soirée)
- Banque : **386 scripts** validés (11 pilotes + 195 scripts de série réécrits « ultra provocateurs » + 180 scénarios
  ancrés sur un mème réel sourcé, 30 par ville). 386/386 passent le contrôle éditorial et la planification 3D ;
  aucun doublon détecté. À 2 vidéos/jour : ≈ 6 mois de contenu, puis l'usine à gags (mèmes × situations × ressorts)
  et la réaction aux tendances prennent le relais.
- Provocation : accroche choc écrite à 0 s, fin « Envoie ça à ton pote qui vote X », légendes « guerre des camps »,
  5 hashtags max. Règles et lignes rouges dans docs/BRIEF_AUTEURS.md.
- Épisode 1 v2 rendu en 12 min (ombres des petites lumières désactivées : ≈ 3× plus rapide).
- Qwen3-14B (modèle local plus fort pour l'usine à gags) : téléchargement en cours, non testé.
