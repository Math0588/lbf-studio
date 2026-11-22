# Configuration Instagram — guide propriétaire

Version du 2026-11-21. Compte : **@lebordelfrancais** (déjà détenu). Sources consultées le 2026-11-21 :
- Publication : https://developers.facebook.com/docs/instagram-platform/content-publishing
- Instagram Login : https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login
- Rafraîchissement : https://developers.facebook.com/docs/instagram-platform/reference/refresh_access_token

`LIVE_PUBLISH=false` tant que les étapes 1–7 ne sont pas validées par un test.

## 1. Passer en compte professionnel

App Instagram → Paramètres → Type de compte et outils → **Passer à un compte professionnel** → « Créateur » ou « Entreprise » (la doc parle de « professional accounts » sans distinguer ; Entreprise recommandé si Unified Login). Catégorie : divertissement / humour. Activer la double authentification.

## 2. Créer l'app Meta

1. https://developers.facebook.com/ → se connecter → **Créer une app** (type Business / cas d'usage Instagram).
2. Ajouter le produit **Instagram** et choisir la voie (§3).
3. Ajouter `@lebordelfrancais` dans les rôles de l'app (testeur Instagram) puis accepter l'invitation dans l'app Instagram.
4. **Standard Access** suffit pour un compte que tu possèdes ; **Advanced Access** (et la vérification qui l'accompagne) n'est requis que pour servir des comptes que tu ne gères pas.

## 3. Choisir la voie d'authentification

| | **Instagram Login** (défaut projet, `IG_API=instagram_login`) | **Unified Login** (Facebook Login for Business) |
|---|---|---|
| Hôte | `graph.instagram.com` | `graph.facebook.com` |
| Permissions | `instagram_business_basic`, `instagram_business_content_publish` | `instagram_basic`, `instagram_content_publish`, `pages_read_engagement` (+ `ads_management`/`ads_read` si rôle Business Manager sur la Page) |
| Page Facebook | Non requise | Requise, liée au compte Instagram |
| Vidéo | Doit être sur une **URL publique** au moment de l'appel | **Upload reprenable** (`upload_type=resumable`, `rupload.facebook.com`) : pas d'hébergement public |
| Intérêt | Plus simple | Évite l'hébergement temporaire depuis un dépôt privé |

Recommandation : Instagram Login si un hébergement public temporaire gratuit est trouvé ; sinon Unified Login.

## 4. Obtenir le jeton long (Instagram Login)

1. Autorisation OAuth → code valable **1 h**, usage unique.
2. `POST https://api.instagram.com/oauth/access_token` (`grant_type=authorization_code`) → jeton court.
3. `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token` → **jeton long, 60 jours**.
4. Relever l'ID utilisateur Instagram (`/me?fields=user_id,username`).

(Unified Login : équivalent via le flux Facebook Login for Business ; durée des jetons de cette voie **à vérifier**.)

## 5. Stockage

Dépôt GitHub (privé recommandé) → Settings → Secrets and variables → Actions :
- secret `IG_ACCESS_TOKEN` = jeton long ;
- secret `IG_USER_ID` = ID Instagram ;
- variable `LIVE_PUBLISH` = `false` puis `true` après test.
Jamais dans le code, `.env` versionné, logs ou captures.

## 6. Rafraîchissement automatique

- `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token` ; conditions : jeton long **≥ 24 h**, **non expiré**, permission `instagram_business_basic`. Le jeton rafraîchi vaut **60 jours** à partir du rafraîchissement.
- Workflow planifié hebdomadaire. Si la valeur renvoyée change, la réécrire dans `IG_ACCESS_TOKEN` (`gh secret set`) avec un jeton GitHub à grain fin limité à ce dépôt (permission Secrets : écriture), stocké en secret `GH_SECRETS_PAT`.
- Alerte (échec du workflow = e-mail GitHub) si le rafraîchissement échoue.

## 7. Limites de publication

- **100 publications via API par 24 h glissantes** (un carrousel = 1) ; la section carrousel de la même page indique 50 → à vérifier. Le projet publie 1 Reel/jour.
- Reels : `media_type=REELS` + `video_url` (ou upload reprenable). Conteneur non publié sous 24 h → `EXPIRED`. Sonder le statut 1×/min, 5 min max.
- Spécifications vidéo Reels (durée, poids, codecs) : **à vérifier** sur la page « reel specifications » de Meta.
- Cron GitHub : UTC par défaut, retards possibles ; en dépôt public, désactivé après 60 jours sans activité.

## 8. Ce qui exige ta présence

- Créer/valider : compte pro, app Meta, rôles, consentement OAuth initial.
- Vérification d'identité ou d'entreprise si Meta la demande.
- **Reconnexion** si le jeton est révoqué (changement de mot de passe, retrait de l'app, alerte de sécurité) ou expiré (> 60 jours sans rafraîchissement).
- Basculer `LIVE_PUBLISH=true`, et `PAUSED=true` en cas de crise.
- Répondre aux commentaires/DM et aux partenariats.

## 9. Pas de publicité

Meta ne diffuse plus de publicités politiques, électorales ou sur des sujets de société dans l'UE depuis le **6 octobre 2025** (https://about.fb.com/news/2025/07/ending-political-electoral-and-social-issue-advertising-in-the-eu/ ; https://developers.facebook.com/blog/post/2025/10/06/prohibiting-ads-about-social-issues-elections-or-politics-from-running-in-the-eu-due-to-regulation/, consultés le 2026-11-21). Le contenu organique reste autorisé : croissance **organique uniquement**, pas de bouton « Booster ».
