# Boutique : message à coller dans Claude sur ton PC (Claude Desktop + Claude dans Chrome)

Prérequis : Chrome avec l'extension Claude, et ton compte Spreadshirt déjà connecté dans Chrome.
Ouvre une conversation Claude sur ton ordinateur et colle tout le bloc ci-dessous.

---

Pilote Chrome pour mettre en place, de bout en bout, la boutique Spreadshirt « Le Bordel Français »
(compte déjà connecté). Travaille dans un nouvel onglet.

1. Télécharge le kit : https://github.com/Math0588/lbf-studio/releases/download/boutique/kit_boutique.zip
   et décompresse-le dans Téléchargements/kit_boutique. Il contient :
   - `designs/` : 36 PNG transparents. `-fonce.png` = pour t-shirt NOIR, `-clair.png` = pour t-shirt BLANC ;
   - `fiche_produits.csv` (séparateur « ; ») : 18 produits avec titre, description, mots-clés et fichiers ;
   - `galerie/banniere_2400x600.jpg` et `galerie/avatar.png` ; deux planches d'aperçu.
2. Espace partenaire Spreadshirt (https://partner.spreadshirt.fr) → Designs → importer les 36 PNG.
   S'il y a une limite d'imports par jour : importe d'abord les 6 `absurde-*-fonce.png`, puis le reste dans
   l'ordre de la fiche, et dis-moi où tu t'es arrêté.
3. Pour chaque ligne de la fiche, dans l'ordre : créer le produit sur un t-shirt unisexe, design `-fonce` sur
   noir et `-clair` sur blanc, devant, centré, haut de poitrine ; reprendre exactement le titre, la description
   et les mots-clés de la fiche ; garder la marge par défaut ; publier sur la marketplace.
4. Rendre la galerie propre : bannière `banniere_2400x600.jpg`, photo `avatar.png`, nom « Le Bordel Français »,
   présentation : « Humour politique absurde. Les t-shirts des Reels @lebordelfrancais. Aucun soutien à un parti. »
   Retirer ou masquer les anciens produits de test s'il y en a.
5. Vérifier en navigation privée : https://www.spreadshirt.fr/shop/user/lebordelfrancais affiche les produits,
   et https://is.gd/lebordelfrancais mène bien à cette galerie.

Règles :
- Si Spreadshirt refuse un design ou un titre (modération, nom d'une personnalité…), ne le contourne pas :
  passe au suivant et note-le.
- N'invente aucune mention (bio, premium, made in France…). N'achète rien. Ne saisis aucune donnée de paiement.
- Si une étape demande mes données personnelles (identité, adresse, coordonnées bancaires, fiscalité),
  arrête-toi et demande-moi : je les remplis moi-même.

À la fin : la liste des produits en ligne (titre + lien), ceux refusés et pourquoi, et ce qui reste à faire.
