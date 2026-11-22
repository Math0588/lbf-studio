# Frais et limites — Le Bordel Français

Sources consultées le **2026-11-21** sauf mention. « À vérifier » = non confirmé sur une page officielle ce jour. Aucun chiffre n'est estimé sans le dire.

## 1. Tableau

| Élément | Coût fixe | Coût par vente / usage | Abonnement obligatoire ? | Limites | Source + date |
|---|---|---|---|---|---|
| Blender | 0 € | 0 € | Non | Logiciel libre (GPL, non relu ce jour) | blender.org — à vérifier |
| FFmpeg | 0 € | 0 € | Non | LGPL/GPL selon compilation (non relu) | ffmpeg.org — à vérifier |
| Piper + voix | 0 € | 0 € | Non | Seules `fr_FR-siwis-medium` et `fr_FR-mls-medium` validées commerciales (CC BY 4.0 → attribution obligatoire) ; `fr_FR-tom-medium` exclue | `lbf/config.py` (vérifié sur piper1-gpl `COMMERCIAL_USE.md` + MODEL_CARD, 2026-11-21) |
| Ollama + Qwen3-4B | 0 € | 0 € (électricité) | Non | Qwen3-4B sous Apache 2.0 ; tourne en local | https://huggingface.co/Qwen/Qwen3-4B (2026-11-21) ; licence Ollama à vérifier |
| Python / SQLite | 0 € | 0 € | Non | — | à vérifier (licences PSF / domaine public) |
| Électricité du PC | 0 € | Voir méthode §3 | Non | Dépend du tarif et du temps de rendu | Facture du propriétaire |
| GitHub Actions | 0 € | Dépôt **public** : runners standard gratuits. Dépôt **privé** (GitHub Free) : 12 $ de calcul inclus/mois, Linux 2 cœurs 0,006 $/min au-delà | Non | 500 Mo d'artefacts ; cache 10 Go/dépôt ; cron ≥ 5 min, UTC par défaut, retards possibles en charge, branche par défaut seulement ; en dépôt public, cron désactivé après **60 jours** sans activité | https://docs.github.com/en/billing/concepts/product-billing/github-actions · https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-11-21) |
| Hébergement vidéo temporaire (API Instagram) | 0 € visé | 0 € visé | Non | Instagram Login : la vidéo doit être sur une **URL publique** au moment de la création du conteneur. Upload reprenable (sans hébergement) réservé à Facebook Login for Business. Offres gratuites de stockage : **à vérifier** | https://developers.facebook.com/docs/instagram-platform/content-publishing (2026-11-21) |
| API Instagram | 0 € | 0 € | Non | **100** publications via API / 24 h glissantes (la section carrousel du même document indique 50 → à vérifier) ; conteneur expiré après 24 h ; jeton long 60 j | Idem + https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login (2026-11-21) |
| X API | 0 € (désactivée) | Paiement à l'usage par crédits prépayés ; tarifs par requête dans la console (**à vérifier**) | Non (pas d'abonnement) | `X_ENABLED=false` ; garde-fou `MAX_API_SPEND=0` | https://docs.x.com/x-api/getting-started/pricing (2026-11-21) |
| Spreadshop | 0 € | Prix de base retenu par Spreadshop ; ta marge = prix de vente − prix de base ; part des promos sur ta marge | Non | Versement mensuel sous 15 jours ; marge en principe soumise à TVA et à déclarer | https://www.spreadshop.fr/ · https://www.spreadshop.com/helpcenter/earning-money-with-spreadshop/your-margin/ (2026-11-21) |
| Printful | 0 € (plan Free) | Produit + impression + livraison payés par toi à chaque commande + frais de ta boutique | Non (Growth 24,99 $/mois optionnel) | Pas de retour pour changement d'avis ; défauts signalés sous 30 j | https://www.printful.com/pricing · https://help.printful.com/hc/en-us/articles/360014006840 (2026-11-21) |
| Payhip | 0 € (Free Forever) | **5 %** par transaction + frais PayPal/Stripe | Non (Plus 29 $/mois, Pro 99 $/mois optionnels) | Livraison numérique automatique | https://payhip.com/pricing (2026-11-21) |
| Nom de domaine (optionnel) | Prix annuel du registrar (**à vérifier**) | 0 € | Oui si pris (renouvellement annuel) | Non nécessaire au lancement | — |
| Échantillons textiles | 0 € | Prix d'achat d'un produit + livraison (**à relever** dans l'espace partenaire) | Non | 1 écru + 1 noir minimum avant de décrire la qualité | — |

## 2. Synthèse par nature

- **Zéro abonnement** : tout le socle (Blender, FFmpeg, Piper, Ollama, Python/SQLite, GitHub Actions, API Instagram, Spreadshop, Printful Free, Payhip Free) fonctionne sans abonnement. X désactivé.
- **Coûts par vente** : prix de base Spreadshop (ou coûts Printful), 5 % Payhip + frais PayPal/Stripe, TVA et cotisations selon statut (**à vérifier** avec le statut choisi).
- **Matériel** : PC existant (RTX 5070 Ti), déjà acquis ; usure et disque non chiffrés.
- **Électricité** : seul coût récurrent de production, à mesurer (§3).
- **Travail initial** : configuration des comptes, boutique, app Meta, designs, échantillons — temps du propriétaire.
- **Coût de développement avec Claude** : coût de *construction* du pipeline selon l'offre Claude du propriétaire (**à vérifier** sur son abonnement/facturation). **Distinct** du coût d'exécution : une fois construit, le pipeline tourne sans appel payant à Claude (`MAX_API_SPEND=0`).

## 3. Méthode de calcul de l'électricité (aucun chiffre supposé)

1. Mesurer la puissance réelle à la prise (wattmètre) pendant un rendu : `P_rendu` (W) ; au repos : `P_repos`.
2. Noter la durée de production d'un épisode : `t_rendu` (h).
3. Lire le prix du kWh sur la facture : `tarif` (€/kWh).
4. `coût_épisode = P_rendu / 1000 × t_rendu × tarif`.
5. `coût_mensuel = coût_épisode × épisodes_par_mois (+ P_repos/1000 × heures_allumé_hors_rendu × tarif)`.

## 4. Minutes GitHub — estimation (à confirmer par l'usage réel)

Un job de publication = téléchargement de la vidéo + appels API + attente du traitement (sondage ≤ 5 min selon la doc Meta). Mesurer la durée réelle des premiers jobs dans l'onglet Actions ; en dépôt privé, vérifier que `durée × runs/mois × 0,006 $` reste sous les 12 $ inclus.
