# Journal des décisions — Le Bordel Français

Format : date · décision · raison · statut. Nouvelles entrées en bas.

| Date | Décision | Raison | Statut |
|---|---|---|---|
| 2026-11-21 | **Stack** : Blender (3D), FFmpeg (montage), Piper (voix), Ollama + Qwen3-4B (brouillons de scripts, local), Python + SQLite | Tout gratuit, local, sans abonnement | Acté |
| 2026-11-21 | **Réserve locale + publication cloud** : le PC fabrique une réserve d'épisodes (`RESERVE_TARGET_DAYS=10`) ; GitHub Actions planifié publie via l'API Instagram officielle (créneau `18:30` Europe/Paris) | Publier PC éteint, sans action quotidienne | Acté |
| 2026-11-21 | **Mode gratuit par défaut** : `FREE_MODE=true`, `MAX_API_SPEND=0`, `X_ENABLED=false`, `LIVE_PUBLISH=false` | Aucune dépense ni publication réelle sans décision explicite | Acté |
| 2026-11-21 | **Compte Instagram** : `@lebordelfrancais`, déjà détenu par le propriétaire (https://www.instagram.com/lebordelfrancais/) ; pseudos alternatifs abandonnés | Pseudo acquis | Acté |
| 2026-11-21 | **Voie API** : Instagram Login par défaut (`IG_API=instagram_login`) ; bascule vers Unified Login si pas d'hébergement public gratuit | Upload reprenable réservé à Facebook Login for Business | À confirmer |
| 2026-11-21 | **Boutique** : Spreadshop (Printful en alternative) | Pas d'abonnement, pas d'avance, paiement/fabrication/expédition/SAV gérés par Spreadshop | Choisi, non ouvert |
| 2026-11-21 | **Collections** : Gauche / Droite / Tout le monde prend ; 6 designs (`content/products.json`), écru et noir | Autodérision symétrique, pas de camp | Designs prêts, non listés |
| 2026-11-21 | **Formation** : Payhip, plan Free Forever (5 % + frais PayPal/Stripe) | Livraison automatique, sans abonnement | Choisi, non ouvert |
| 2026-11-21 | **Palette** : bleu `#1649FF` 60 %, blanc cassé `#FFFDF7` 30 %, rouge `#EF233C` 10 %, texte `#111827` | Identité lisible, accent unique | Acté |
| 2026-11-21 | **Fontes** : Archivo Black + Anton, SIL OFL 1.1 (licences dans `assets/fonts/`) | Usage commercial permis | Acté |
| 2026-11-21 | **Voix Piper** : seules `fr_FR-siwis-medium` (défaut) et `fr_FR-mls-medium` validées commerciales ; `fr_FR-tom-medium` exclue (AGPLv3) | Chaîne de licence vérifiée dans `lbf/config.py` | Choix final **à vérifier** par écoute |
| 2026-11-21 | **X désactivé** | API payante à l'usage ; incompatible avec `MAX_API_SPEND=0` | Acté |
| 2026-11-21 | **Pas de publicité payante** ; croissance organique | Meta n'accepte plus les pubs politiques/sociétales dans l'UE depuis le 6/10/2025 | Acté |
| 2026-11-21 | **Mention** « Fiction satirique » sur chaque publication et en bio | Transparence | Acté |

## Actions qui exigent le propriétaire

### Instagram / Meta
- [ ] Passer `@lebordelfrancais` en compte professionnel ; activer la double authentification
- [ ] Mettre nom affiché, bio (143 caractères) et avatar coq (`CHARTE_MARQUE.md`)
- [ ] Créer l'app Meta, ajouter le compte en testeur, choisir Instagram Login ou Unified Login
- [ ] Faire le consentement OAuth et obtenir le jeton long (60 j)
- [ ] Vérification d'identité/entreprise si Meta la demande
- [ ] Choisir et valider la solution d'hébergement vidéo (ou Unified Login)

### GitHub
- [ ] Créer le dépôt (privé recommandé) ; secrets `IG_ACCESS_TOKEN`, `IG_USER_ID`, `GH_SECRETS_PAT` ; variable `LIVE_PUBLISH=false`
- [ ] Après une publication test réussie : `LIVE_PUBLISH=true`

### Boutique
- [ ] Créer le compte Spreadshop ; identité, IBAN/PayPal, statut fiscal et TVA
- [ ] Faire les recherches INPI / EUIPO / OMPI et d'usages existants (nom, signature, 6 slogans)
- [ ] Uploader les 6 designs, fixer les prix, coller les fiches honnêtes
- [ ] Commander les échantillons (écru + noir), mettre à jour les fiches
- [ ] Lister les produits, reporter `shop_url` et statut dans `content/products.json`

### Formation / partenariats
- [ ] Créer le compte Payhip, connecter PayPal ou Stripe, fixer le prix
- [ ] Chronométrer une installation complète avant d'annoncer un temps de configuration
- [ ] Créer l'adresse de contact dédiée (3 propositions dans `PARTENARIATS.md`)
- [ ] Valider et envoyer soi-même chaque réponse aux partenaires

### Production
- [ ] Choisir la voix finale (siwis ou mls) ; ajouter l'attribution CC BY dans les crédits
- [ ] Mesurer la consommation électrique d'un rendu (méthode dans `FRAIS_LIMITES.md`)
- [ ] Choisir le statut juridique et fiscal avant la première vente

## 2026-11-21 — Mention « création assistée par IA » retirée (décision du propriétaire)
- À l'écran et dans les légendes, seule la mention « Fiction satirique » est conservée (protection : situations et répliques inventées).
- Label « Informations sur l'IA » de Meta : désactivé par défaut (`ai_label: false`). Il vise les contenus photoréalistes ou les audios réalistes trompeurs ; nos villes 3D stylisées, sans visage ni voix imitant une personne réelle, n'entrent pas dans ce cas. À réactiver si un épisode montrait un jour une image photoréaliste ou une voix ressemblant à une personne réelle (interdit par la charte de toute façon).
- Le propriétaire a demandé un ton beaucoup plus provocateur, alimenté par les mèmes qui circulent (X compris). Les limites restent : aucune fausse citation, aucun délit inventé, rien sur les caractéristiques protégées, aucune vie privée.
- « Guseman » résolu : il s'agit de Raphaël Glucksmann → 6e ville, Glucksmannville.
- 2026-11-21 (suite) : le propriétaire retire aussi « Fiction satirique » des vidéos et des légendes. La nature satirique reste affichée au niveau du compte (bio : « Fictions satiriques »). Conséquence assumée : la fiction doit être évidente par le contenu (villes inventées, absurde visible), et les interdits (fausses citations, délits inventés, vie privée, caractéristiques protégées) restent bloquants dans le contrôle éditorial.
- 2026-11-22 : **T-shirts « j'ai fait un cauchemar : »** : police **Fredoka** (SIL OFL, ronde, très grasse), mise en page maison (accroche / chute en rouge / petite phrase), texte seul, sans nom de compte. Pourquoi : rond = lu comme amical, donc la provoc passe pour de l'humour ; très gras + grand œil = lisible en un coup d'œil ; rouge = vu en premier ; une cible par camp = chacun achète celui qui pique l'autre.
- 2026-11-22 : **Série retenue par le propriétaire** (choix 2, 5, 8, 11, 14, 17 de la planche `brand/boutique_v3/_choix_chutes.jpg`) : Glucksmann avait un cap clair / Mélenchon était calme / Bardella était au Parlement / le ruissellement est arrivé jusqu'à moi / Sandrine Rousseau a vu mon barbecue / Zemmour était optimiste. Les 15 autres chutes restent dans `lbf/merch_text.py` (CHOIX_S). Fichiers : `brand/boutique_v3/upload/` ; produits : `content/products.json` (champ `cities`).
- 2026-11-22 : **Vidéos** : chaque ville porte le t-shirt qui vise son politicien (Marineville → Bardella ; Rousseau n'a pas de ville, vendu seul). `lbf/planner_v2.product_for`.
- 2026-11-22 : **Bloqués jusqu'au 23/11** : import Spreadshop (limite d'imports par jour atteinte) ; portefeuille business Meta (« LBF Productions » accepté, mais compte Facebook jugé trop récent).
- 2026-11-22 : **Vente via la marketplace Spreadshirt (galerie « lebordelfrancais »), pas via la boutique Spreadshop.** Pourquoi : Spreadshop exige des mentions légales publiques (prénom, nom, adresse) et le propriétaire ne veut pas être identifiable ; il n'a pas de société. La galerie marketplace n'en demande pas (Spreadshirt est le vendeur). Nom public « lebordelfrancais » (l'e-mail s'affichait par défaut, corrigé), logo coq, bannière, description, lien Instagram, modification des designs par IA interdite. Adresse : https://www.spreadshirt.fr/shop/user/lebordelfrancais (404 tant qu'aucun design n'est publié). Spreadshirt refuse le mot « Zemmour » dans les textes (à éviter dans titres et mots-clés ; le design Zemmour peut être refusé à la relecture). Boutique Spreadshop configurée (logo, couleurs) mais laissée désactivée.
