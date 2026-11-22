# Formation — « Fabrique ton compte de satire 3D automatisé »

Version du 2026-11-21. Rien n'est en vente. Prix : **à fixer par le propriétaire**.

## 1. Promesse (honnête)

Tu apprends à reproduire une chaîne de production : idée → script → décor 3D Blender → voix et sous-titres → publication planifiée sur Instagram via l'API officielle, sans abonnement logiciel.
**Aucune promesse de vues, d'abonnés ni de revenus.** Les résultats dépendent de tes idées, de ta régularité et de l'algorithme. Nos propres statistiques ne sont montrées que si elles sont réelles, datées et vérifiables.

## 2. Page coulisses (gratuite)

Page publique (produit gratuit Payhip à 0 € ou page simple) liée depuis le profil :
- comment une ville est construite (captures Blender, avant/après) ;
- l'outillage utilisé et ses licences (Blender, Piper + voix CC BY, fontes OFL, Ollama + Qwen3-4B Apache 2.0) ;
- crédits obligatoires (attribution de la voix CC BY) ;
- lien vers la boutique et vers la formation.

## 3. Kit de démarrage (gratuit)

- Checklist de configuration (comptes, outils, secrets GitHub).
- Gabarits : charte vierge (palette, fontes OFL avec leurs fichiers de licence), structure d'épisode 30 s.
- Fichier `.env` d'exemple en mode gratuit (`FREE_MODE=true`, `MAX_API_SPEND=0`, `X_ENABLED=false`, `LIVE_PUBLISH=false`).
- Pas de voix non commerciales, pas de contenu du compte Le Bordel Français à republier.

## 4. Plan du cours (7 modules)

| # | Module | Livrable de l'élève |
|---|---|---|
| 1 | **Concept et identité** : niche, règle comique visuelle, palette 60/30/10, fontes libres, avatar, bio ≤ 150 caractères | Sa propre charte d'une page |
| 2 | **Scripts** : structure 30 s / 55–80 mots, mécanismes comiques, interdits (fausses citations, stats inventées, caractéristiques protégées), LLM local en assistant de brouillon | 5 scripts relus à la main |
| 3 | **Décors Blender** : maquette miniature par blocs, catalogue de props, éclairage, caméra, rendu en lot (GPU) | 1 décor + rendu 9:16 |
| 4 | **Voix, montage, sous-titres** : Piper, vérification de licence des voix, FFmpeg, sous-titres lisibles, zones sûres | 1 Reel complet |
| 5 | **Publication API** : compte pro, app Meta, jetons, GitHub Actions planifié, réserve d'épisodes, mode test `LIVE_PUBLISH=false` | Publication planifiée qui tourne PC éteint |
| 6 | **Mesure** : statistiques Instagram, lecture honnête (rétention, partages), une variable testée à la fois | Tableau de suivi |
| 7 | **Droits, limites, coûts** : licences, satire vs diffamation, mention IA, partenariats rémunérés (« Publicité »/« Collaboration commerciale »), pubs politiques interdites sur Meta dans l'UE, coûts réels (électricité, frais de vente) | Sa grille de frais et checklist juridique |

## 5. Prérequis

- PC Windows 10/11 avec GPU NVIDIA récent recommandé (rendu) ; ≥ 15 Go libres en permanence (seuil `MIN_FREE_DISK_GB` du projet), davantage pour la réserve de vidéos.
- Aisance de base avec les fichiers et un terminal ; aucune expérience Blender requise mais du temps de pratique.
- Comptes à créer soi-même : Instagram professionnel, Meta for Developers, GitHub.
- Accepter de publier sous sa propre responsabilité éditoriale.

## 6. Limites (à afficher sur la page de vente)

- Pas de garantie d'audience ou de revenu.
- Les API et conditions (Meta, GitHub, POD) changent : chaque module date ses sources ; mises à jour non garanties à vie (durée de mise à jour **à fixer**).
- Pas d'accompagnement individuel inclus (sauf offre séparée).
- Ne couvre pas : publicité payante (interdite pour ce type de contenu dans l'UE chez Meta), conseil juridique ou fiscal personnalisé.

## 7. Temps de configuration

**À mesurer** : chronométrer une installation complète sur un PC propre avant la mise en vente et afficher le temps réellement mesuré. Ne rien annoncer avant.
Étapes à chronométrer : installation des outils · création des comptes · app Meta et jeton · dépôt GitHub et secrets · premier rendu · première publication test.

## 8. Ce qui est inclus

Vidéos/textes des 7 modules · kit de démarrage · gabarits · scripts d'exemple du pipeline (licence de réutilisation **à définir**) · checklists juridique et frais. Non inclus : les assets et épisodes du compte Le Bordel Français, les voix non commerciales, les comptes tiers.

## 9. Vente via Payhip

Sources consultées le 2026-11-21 : https://payhip.com/pricing · https://help.payhip.com/article/132-how-payhip-works (via résultat de recherche, à relire).

| Point | Constat |
|---|---|
| Plan | **Free Forever : 0 $/mois + 5 % de frais de transaction** (Plus : 29 $/mois + 2 % ; Pro : 99 $/mois + 0 %) |
| Frais de paiement | PayPal et Stripe prélèvent **en plus** leurs frais standard (taux **à vérifier** sur leurs pages) |
| Livraison | Automatique : après paiement, l'acheteur arrive sur sa page de téléchargement/d'accès et reçoit un e-mail avec le lien |
| Versement | Fonds versés sur le compte PayPal/Stripe connecté du vendeur à la transaction |
| TVA | Payhip indique gérer collecte et reversement de la TVA UE/UK |

**Rétractation sur contenu numérique** : en France, l'exclusion du délai de 14 jours pour un contenu numérique fourni immédiatement suppose l'accord préalable exprès du consommateur et sa renonciation (art. L221-28 Code de la consommation, texte non relu ce jour → **à vérifier**). Vérifier si Payhip propose cette case à cocher ; sinon, prévoir une politique de remboursement claire.

Formule : `net_par_vente = prix − 5 % × prix − frais_PayPal_ou_Stripe − cotisations_et_impôts(statut)`.
