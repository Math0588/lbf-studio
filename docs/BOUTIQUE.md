# Boutique — Le Bordel Français

Version du 2026-11-21. Données produits : `content/products.json`. Rien n'est en vente : statut `design_ready_not_listed` tant que le propriétaire n'a pas ouvert et configuré la boutique.

## 1. Collections

| Collection | Idée | Règle d'équilibre |
|---|---|---|
| **Tout le monde prend** | Le citoyen épuisé par tout le système | Aucun camp visé |
| **Gauche** | Autodérision de qui se dit de gauche | Chaque design a son **miroir exact** en Droite |
| **Droite** | Autodérision de qui se dit de droite | Même texte, même mise en page que le miroir Gauche |

Le compte ne prend pas parti : les collections Gauche/Droite vendent de l'autodérision symétrique, jamais une attaque contre l'autre camp.

## 2. Designs de lancement

Typo : Archivo Black capitales. Placement : **devant, centré, haut de poitrine**, largeur à ajuster à la zone d'impression du produit choisi (dimensions **à vérifier** dans l'outil du POD). Pas de logo au dos au lancement.
Encres : sur **écru** → noir d'encre `#111827` + rouge `#EF233C` ; sur **noir** → blanc cassé `#FFFDF7` + rouge `#EF233C`. Rouge = un seul segment de texte.

| id | Collection | Texte (ligne 1 / ligne 2) | Segment rouge |
|---|---|---|---|
| `tee-pays-bugue` | Tout le monde prend | LE PAYS BUGUE. / MOI AUSSI. | MOI AUSSI. |
| `tee-avis-mandat` | Tout le monde prend | J'AI UN AVIS. / PAS DE MANDAT. | PAS DE MANDAT. |
| `tee-gauche-canape` | Gauche | À GAUCHE / DU CANAPÉ. | CANAPÉ. |
| `tee-droite-canape` | Droite | À DROITE / DU CANAPÉ. | CANAPÉ. |
| `tee-gauche-fatigue` | Gauche | PLUTÔT GAUCHE. / TRÈS FATIGUÉ. | TRÈS FATIGUÉ. |
| `tee-droite-fatigue` | Droite | PLUTÔT DROITE. / TRÈS FATIGUÉ. | TRÈS FATIGUÉ. |

Fichiers à fournir au POD : PNG fond transparent, haute définition (résolution minimale exigée **à vérifier** chez le POD), un fichier par coloris d'encre.

## 3. Fiche produit (modèle honnête)

> **[SLOGAN]** — collection [Collection].
> T-shirt imprimé à la demande après ta commande, par [Spreadshop / Printful], qui fabrique, expédie et gère le service client.
> Matière, grammage, coupe, origine et entretien : ceux indiqués par le fabricant dans le tableau du produit de base ci-dessous. Nous n'avons **pas encore testé d'échantillon** de ce modèle ; cette fiche sera mise à jour après réception.
> Design original Le Bordel Français. Fiction satirique, aucun soutien à un parti.

Interdits sur la fiche : « premium », « haute qualité », « bio », « made in France » ou toute origine/qualité non justifiée par la fiche technique du fabricant. Exception : si le produit de base choisi est certifié (ex. coton biologique) et que la boutique l'affiche, on peut le reprendre en citant la mention du fabricant. Le CTA vidéo « Collection en bio » du brief désigne le **lien en bio Instagram**, pas du coton bio : ne jamais l'écrire sur une fiche produit.

## 4. Spreadshop vs Printful

Sources consultées le 2026-11-21 : https://www.spreadshop.fr/ · https://www.spreadshop.com/helpcenter/earning-money-with-spreadshop/your-margin/ · https://www.spreadshirt.ie/t-and-c-customers · https://www.printful.com/pricing · https://help.printful.com/hc/en-us/articles/360014006840

| Critère | Spreadshop | Printful |
|---|---|---|
| Abonnement | Aucun (« entièrement gratuit », sans frais d'ouverture ni minimum) | Plan Free 0 $/mois ; Growth 24,99 $/mois optionnel |
| Vendeur / partie au contrat | **sprd.net AG (« Spreadshirt »)** selon ses CGV clients (version consultée : site IE ; version FR **à vérifier**) | **Toi** : Printful facture au marchand, la boutique (Shopify, Etsy, Quick Stores…) est la tienne |
| Qui encaisse | Spreadshop encaisse le client, garde le prix de base, te reverse la marge | Ta boutique encaisse ; tu paies Printful (produit + impression + livraison) quand le client commande |
| Avance de trésorerie | **Aucune** | **Oui possible** : Printful est payé via ton Wallet/carte à la commande, avant que les fonds de ta boutique soient disponibles |
| Automatisation bout en bout | Oui : paiement, impression, expédition, retours, SAV gérés par Spreadshop | Fabrication/expédition oui ; boutique, paiement, TVA, SAV client et retours à ta charge |
| Retours | Gérés par Spreadshop ; affiche « Easy returns within 30 days » (site IE, conditions FR **à vérifier**) | Printful refuse les retours pour changement d'avis/taille/couleur ; défauts à signaler **sous 30 jours** après livraison (réimpression ou remboursement) |
| Rétractation 14 jours (France) | Gérée par Spreadshirt, vendeur | **À ta charge** : produit retourné et remboursé par toi, Printful ne reprend pas |
| Versement | Solde mensuel, versé dans les 15 jours (SEPA ou PayPal) | Selon le processeur de ta boutique (**à vérifier**) |
| TVA | Spreadshop gère la TVA sur les ventes ; ta marge est « en principe soumise à TVA » et à déclarer | Entièrement à ta charge |

**Droit de rétractation et impression à la demande.** Délai de 14 jours (art. L221-18 Code de la consommation). L'exception de l'art. L221-28 vise les biens « confectionnés selon les spécifications du consommateur ou nettement personnalisés ». Un design standard du catalogue, choisi tel quel, n'est en principe **pas** dans l'exception, même s'il est imprimé à la demande : le client peut se rétracter. Textes non relus sur Légifrance ce jour (accès refusé au script) → **à vérifier**.

**Conclusion** : Spreadshop pour le lancement (zéro avance, zéro SAV, zéro abonnement). Printful seulement si besoin d'un catalogue/qualité différent, en acceptant d'être vendeur.

## 5. Configuration Spreadshop — à faire par le propriétaire

Rien de cela ne peut être fait par l'automatisation : compte, identité, fiscalité et paiement sont personnels.

1. **Compte** : créer un compte partenaire sur https://www.spreadshop.fr/ avec l'adresse e-mail du projet (cf. `PARTENARIATS.md`). Activer la double authentification si proposée.
2. **Nom/URL de boutique** : `lebordelfrancais` (disponibilité **à vérifier**).
3. **Identité et versements** : renseigner nom légal, adresse, IBAN ou PayPal dans l'espace partenaire.
4. **Fiscalité** : déclarer le statut (particulier / micro-entreprise / société) et le régime TVA demandés par Spreadshop. Les gains sont des revenus à déclarer ; faire valider le statut adapté (URSSAF/impôts ou comptable) — **à vérifier** avant la première vente.
5. **Upload des designs** : 1 PNG par design et par encre (§2), produit de base = t-shirt unisexe, coloris **écru** et **noir** uniquement (noms exacts des coloris **à vérifier** dans le catalogue).
6. **Prix** : fixer la marge (§6), vérifier le prix public affiché.
7. **Fiches** : coller le modèle §3, compléter avec la fiche technique réelle du produit de base.
8. **Pages légales** : vérifier les mentions générées par Spreadshop (CGV Spreadshirt, mentions légales du shop) ; ajouter les mentions légales du propriétaire si exigées.
9. **Commande d'échantillons** : 1 écru + 1 noir minimum, contrôle impression/lavage, puis mise à jour des fiches.
10. **Mise en ligne** : passer chaque produit en public, puis reporter `shop_url` et `status: "listed"` dans `content/products.json`.

## 6. Calcul de marge

**Spreadshop** :
`marge_brute = prix_de_vente − prix_de_base`
`gain_net = marge_brute − TVA_éventuelle_sur_marge − part_promo_supportée − cotisations_et_impôts(statut)`

**Printful** :
`gain_net = prix_de_vente − (produit + impression + livraison Printful) − frais_paiement_boutique − abonnement_boutique_éventuel − coût_des_retours − TVA − cotisations_et_impôts`

**Exemple** (chiffres publiés par Spreadshop sur sa page d'accueil FR, consultée le 2026-11-21 — ce ne sont **pas** nos prix) : prix de vente 45,99 €, prix de base 29,99 € → marge brute **16,00 €** par t-shirt, avant TVA éventuelle et cotisations. Nos prix de base réels : **à relever** dans l'espace partenaire.

Les promos réduisent ta marge (ta part) ; les promos livraison gratuite sont à la charge de Spreadshop (blog Spreadshop, date non vérifiée → **à vérifier**).

## 7. Vérifications juridiques avant vente

Ne rien déclarer « libre » ou « disponible » : une recherche sans résultat n'est pas une garantie.

- **Marques** : rechercher « Le Bordel Français », « Bordel Français », « Liberté. Égalité. N'importe quoi. » et chacun des 6 slogans, en classes 25 (vêtements), 41 (divertissement), 9/38 (contenus numériques) sur :
  - INPI : https://data.inpi.fr/
  - EUIPO / TMview : https://www.tmdn.org/tmview/
  - OMPI Global Brand Database : https://branddb.wipo.int/
- **Usages existants** : recherche web, Instagram, TikTok, Etsy, Redbubble, Spreadshirt sur les mêmes textes (risque de collision ou de reprise d'une punchline existante, interdite par le brief).
- **Symboles publics** : pas de Marianne officielle, de bloc-marque gouvernemental, de logo de parti ni de nom de personnalité réelle sur les textiles.
- **Règles du POD** : vérifier la politique de contenu de Spreadshop/Spreadshirt sur les designs politiques (**à vérifier**).
- **Dépôt de marque** : décision et coût à évaluer par le propriétaire (tarifs INPI **à vérifier**).
