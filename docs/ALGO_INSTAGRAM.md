# Codes de l'algorithme Instagram (Reels) — ce qui est sourcé, et ce qu'on en fait

Consulté le 22/11/2026. Instagram ne publie pas de poids chiffrés : seules les familles de signaux sont confirmées.

## Ce qui est confirmé (Adam Mosseri, vidéo de janvier 2025, reprise dans plusieurs synthèses 2026)
- **Temps de visionnage** (durée regardée rapportée à la longueur du Reel).
- **J'aime par compte touché** (likes / reach).
- **Envois en message par compte touché** (sends / reach) : signal le plus utile pour toucher des non-abonnés.
  Les « ×3 à ×5 » qui circulent ne sont PAS sourcés chez Instagram.
- Sources : https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers ·
  https://keywordseverywhere.com/news/instagram-algorithm-updates/how-the-instagram-algorithm-works/ ·
  https://creatorlanehq.com/blog/instagram-algorithm-2026-what-changed · https://www.reelxo.tech/blog/instagram-reels-algorithm
- Non confirmé par Instagram : une métrique « 3 premières secondes ». On garde quand même une accroche immédiate,
  parce qu'elle fait monter le temps de visionnage, qui lui est confirmé.

## Ce que le pipeline applique automatiquement (lbf/viral_lint.py bloque sinon)
| Signal | Application |
|---|---|
| Temps de visionnage | 1re image = titre choc + étiquette rouge provocante + ville (lisible son coupé) ; phrase 1 = « Dans cette ville, tout le monde vote X. » ; une pique par plan (coupes 1,5–3 s) ; 20–35 s au total ; sous-titres mot à mot sous le centre. |
| Envois par compte touché | Dernière phrase et carte de fin = « Envoie ça au pote qui… » / « Envoie ça à ton pote qui vote X » (jamais « commente OUI si… », rétrogradé comme engagement bait). |
| J'aime / reach | Piques sur des mèmes que tout le monde reconnaît (≥ 2 faits/citations sourcés par vidéo) : effet « c'est tellement vrai ». |
| Pas de rétrogradation | Contenu original (3D maison, voix, musique) ; pas de filigrane ; aucun fait inventé, rien sur la vie privée ni les traits protégés (évite les signalements massifs). |
| Vente | Plan produit muet de 2,8 s avant la fin (« CE T-SHIRT EXISTE VRAIMENT » / « LIEN EN BIO ») + rappel sur la carte de fin. |
| Régularité | 4 Reels par jour (08:00, 12:30, 19:00, 22:00, Paris) ; rafale ponctuelle possible (state/control.json « bursts »). |
