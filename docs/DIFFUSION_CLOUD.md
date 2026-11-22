# Publier tous les jours, même PC éteint

## Principe
```
 PC (quand il est allumé)                         GitHub (gratuit, toujours allumé)
 ┌──────────────────────────┐   git push    ┌─────────────────────────────────────────┐
 │ worker : écrit → voix →  │ ────────────▶ │ reserve/<épisode>/video.mp4 + légende    │
 │ 3D → montage → QA        │               │ GitHub Pages sert la vidéo (URL publique)│
 │ = RÉSERVE de N jours     │ ◀──────────── │ Actions (cron horaire) → API Instagram   │
 └──────────────────────────┘   git pull    │ state/ : publications, preuves, métriques│
                                            └─────────────────────────────────────────┘
```
- Le PC fabrique d'avance (objectif : `RESERVE_TARGET_DAYS=10` jours). Un épisode ≈ 10–15 min de rendu sur ta RTX 5070 Ti.
- Le cloud publie **1 vidéo par jour** au créneau (`18:30` Europe/Paris par défaut), même PC éteint, et rafraîchit le jeton Instagram.
- Si le PC reste éteint plus longtemps que la réserve : publication suspendue proprement + alerte « réserve vide ». Rien n'est inventé pour combler.

## Ce que TU dois faire une seule fois (≈ 30–45 min)
Ces étapes demandent ta présence (comptes, identité) : le logiciel ne peut pas les faire à ta place.

1. **Instagram** : passer @lebordelfrancais en compte professionnel (Créateur ou Entreprise) — Paramètres › Type de compte.
2. **Meta for Developers** : créer une app, ajouter le produit *Instagram* › *API avec connexion Instagram* ; ajouter ton compte comme testeur ; générer un **jeton longue durée** avec `instagram_business_basic` + `instagram_business_content_publish` ; noter l'**ID utilisateur Instagram**. (Détail : `docs/INSTAGRAM_SETUP.md`.)
3. **GitHub** (gratuit) : créer un dépôt **public** vide, ex. `lbf-diffusion` (public = minutes Actions illimitées + Pages gratuit ; contrepartie : les vidéos de la réserve sont visibles quelques jours avant publication).
4. Sur ton PC :
   ```powershell
   python -m lbf.setup_cloud C:\Users\mathe\lbf-diffusion
   cd C:\Users\mathe\lbf-diffusion
   git remote add origin https://github.com/<ton-compte>/lbf-diffusion.git
   git add . ; git commit -m "diffuseur" ; git push -u origin main
   ```
5. Dans le dépôt GitHub › *Settings* :
   - *Pages* : Source = « Deploy from a branch », branche `main`, dossier `/ (root)`. Noter l'URL (`https://<ton-compte>.github.io/lbf-diffusion`).
   - *Secrets and variables › Actions › Secrets* : `IG_ACCESS_TOKEN`, `IG_USER_ID`, et `GH_SECRETS_TOKEN` (jeton GitHub « fine-grained » limité à ce dépôt, permission *Secrets: Read and write*, pour que le jeton Instagram se renouvelle seul).
   - *Variables* : `PAGES_BASE_URL` = l'URL Pages ; `LIVE_PUBLISH` = `false` pour commencer.
6. **Test** : onglet *Actions* › *Publication quotidienne* › *Run workflow* (cocher « force ») → en simulation, `state/publications.json` montre ce qui serait publié, sans rien envoyer.
7. **Publication de contrôle** : passer `LIVE_PUBLISH` = `true`, relancer avec « force » → vérifier le Reel sur le compte et le lien enregistré dans `state/publications.json`. Ensuite, plus rien à faire au quotidien.
8. (Optionnel) Démarrage automatique du studio à l'ouverture de session :
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\installer_demarrage_auto.ps1
   ```

## Ce qui peut encore te demander une action (exceptions, pas de routine)
- Meta révoque le jeton, change les permissions ou restreint le compte → reconnexion (alerte dans `state/alerts.json` et le tableau de bord).
- Réserve vide parce que le PC est resté éteint trop longtemps.
- GitHub désactive un cron après 60 jours sans activité sur un dépôt public : le diffuseur commite son état à chaque passage, ce qui maintient l'activité.

## Limites connues (honnêtes)
- La file Instagram « Instagram Login » exige une URL vidéo publique : Pages la fournit. L'import par URL depuis Pages doit être confirmé par la publication de contrôle (étape 7).
- Limite Meta : 100 publications API / 24 h (largement au-dessus de notre besoin).
- Les créneaux GitHub Actions peuvent avoir quelques minutes de retard.

## YouTube Shorts (activé par défaut, gratuit)
Les mêmes vidéos partent aussi sur YouTube Shorts dès que les 3 secrets Google existent (TikTok : abandonné).
1. Google Cloud Console : projet + « YouTube Data API v3 » + écran de consentement (Externe, toi en testeur) +
   ID client OAuth « Application de bureau » → télécharger le JSON dans `data/youtube_client.json`.
2. `python -m lbf.youtube_auth` → choisir la chaîne, accepter.
3. Copier les 3 lignes de `data/youtube_secrets.txt` dans les secrets GitHub (`YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
   `YT_REFRESH_TOKEN`), puis supprimer le fichier. Pour couper YouTube : variable `YT_ENABLED` = `false`.
Limite à vérifier au premier envoi : un projet Google non audité peut voir ses vidéos API forcées en « privé » ;
dans ce cas, demander l'audit du projet (gratuit) dans la console Google.

## Mise à jour du 22/11 : dépôt privé, aucune adresse publique

- Le dépôt `lbf-diffusion` est **privé** (plus de GitHub Pages, plus d'adresse `math0588.github.io`) : rien ne relie publiquement LBF au compte GitHub du propriétaire. `btc-autotrader` est aussi passé en privé.
- Les vidéos ne sont plus versionnées : le PC les envoie dans la **release privée « reserve »** (`gh release upload`), le dépôt ne garde que `caption.txt`, `manifest.json` et la file `queue.json`.
- Dans GitHub Actions, le diffuseur télécharge la vidéo de la release, puis l'**envoie directement à Instagram** (conteneur `upload_type=resumable`, puis envoi vers `rupload.facebook.com`). La vignette est l'image à `thumb_offset_ms` (300 ms par défaut).
- Après 3 jours, la vidéo publiée est supprimée de la release.
- Lien en bio : directement la boutique (liens natifs Instagram), plus de page de liens hébergée.
- Connexion Instagram : Page Facebook « LBF Productions » reliée à @lebordelfrancais ; `python -m lbf.connect_instagram` accepte le jeton de l'Explorateur de l'API Graph et en tire un jeton de Page sans expiration.
- Coût : 0 €. Minutes Actions d'un dépôt privé : environ 1 000 par mois utilisées sur les 2 000 gratuites.
