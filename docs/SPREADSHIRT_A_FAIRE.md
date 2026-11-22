# Boutique Spreadshirt : marche à suivre (session Claude sur le PC du propriétaire, avec Claude dans Chrome)

Contexte : la vente passe par la galerie marketplace « lebordelfrancais » sur Spreadshirt
(https://www.spreadshirt.fr/shop/user/lebordelfrancais, lien court https://is.gd/lebordelfrancais).
Spreadshop (boutique perso) exige des mentions légales publiques : pas pour l'instant.
Le 22/11 au matin, l'import de designs était bloqué par la limite quotidienne d'imports.

## 1. Importer les designs (dans l'ordre de priorité)
Dossier du dépôt lbf-studio, fichiers PNG transparents (≈ 4000 px de large) :
1. `brand/boutique_v4/upload/` — collection « Les histoires absurdes » (montrée dans les Reels) :
   absurde-melenchon, absurde-macron, absurde-bardella, absurde-glucksmann, absurde-marine, absurde-zemmour
   - `-clair.png` → t-shirts clairs (blanc, écru) ; `-fonce.png` → t-shirts foncés (noir, marine).
2. `brand/boutique_v3/upload/` — deux gammes (24 fichiers) : « J'ai fait un rêve » (`reve-*`, ce qui n'arrivera jamais)
   et « J'ai fait un cauchemar » (`cauchemar-*`, ce qui fait vraiment peur). Aperçu : `brand/boutique_v3/planche_reve_cauchemar.jpg`.
Le mot « Zemmour » est refusé par Spreadshirt : aucun design de la v4 ne contient de nom de politicien.
Si la limite d'imports bloque encore, importer d'abord les 6 `-fonce.png` de la v4 (t-shirt noir), le reste demain.

## 2. Créer les produits
- Produit de base : t-shirt unisexe ; coloris : noir (design `-fonce`) et blanc (design `-clair`).
- Placement : devant, centré, haut de poitrine.
- Titre = le slogan (ex. « ICI, ON A TAXÉ LA TORTUE. »), description courte :
  « Le t-shirt du Reel. Design original Le Bordel Français. Humour politique, aucun soutien à un parti.
  Imprimé à la demande par Spreadshirt, qui expédie et gère les retours. »
- Mots-clés : humour politique, parodie, politique française, mème, + le thème (tortue, rond-point, matcha, selfie…).
- Marge : celle des autres produits de la galerie (ne pas inventer de mention « bio », « premium », « made in France »).

## 3. Après mise en ligne
- Copier l'URL de chaque produit dans `content/products.json` (`shop_url`) et passer `status` à `listed`.
- Vérifier le lien en bio Instagram (page de liens `brand/page_liens`) vers la galerie.
