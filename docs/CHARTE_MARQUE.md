# Charte de marque — Le Bordel Français

Version du 2026-11-21. Complète `docs/BRIEF_AUTEURS.md` (ton, interdits, structure d'épisode) : en cas de conflit, le brief gagne.

## 1. Identité

| Élément | Valeur |
|---|---|
| Nom | Le Bordel Français |
| Série phare | « Si les politiques géraient ta ville » |
| Signature | **Liberté. Égalité. N'importe quoi.** |
| Pseudo Instagram | **`@lebordelfrancais`** — compte déjà détenu par le propriétaire (https://www.instagram.com/lebordelfrancais/). Les alternatives `@le.bordel.francais` / `@lebordelfrancais.fr` sont abandonnées. |
| Nom affiché | `Le Bordel Français` (18 caractères). Limite du champ « Nom » : **à vérifier** |

Réserver si possible le même pseudo `lebordelfrancais` sur les autres réseaux, même non utilisés (X reste désactivé côté publication).

## 2. Bio (≤ 150 caractères)

```
Si les politiques géraient ta ville.
Satire 3D · villes fictives
Fiction satirique
Liberté. Égalité. N'importe quoi.
```

Comptage : **143 caractères**, sauts de ligne compris (compté par script Python, `len()` en UTF-8 et UTF-16 identiques, 2026-11-21).
Limite de 150 caractères : largement rapportée (ex. https://bitly.com/blog/instagram-character-limit/), page officielle du Help Center non chargeable par script → **à vérifier** dans l'app.
Lien boutique / coulisses : dans le champ **Liens** du profil, pas dans la bio.

## 3. Palette

| Rôle | Couleur | Hex | Part visuelle |
|---|---|---|---|
| Fond, bandeaux, ciel, signalétique | Bleu | `#1649FF` | 60 % |
| Respiration, cartons, papiers, façades | Blanc cassé | `#FFFDF7` | 30 % |
| Accent unique (chute, mot clé, crête) | Rouge | `#EF233C` | 10 % |
| Texte | Noir d'encre | `#111827` | texte seulement |

Règles : un seul élément rouge par image fixe ; jamais de texte rouge sur bleu (contraste faible) ; texte sur bleu = blanc cassé ; texte sur blanc cassé = noir d'encre. Le tricolore n'est pas reproduit comme drapeau ni comme logo d'État (pas d'imitation du bloc-marque gouvernemental ni de Marianne officielle).

## 4. Typographies

| Fonte | Usage | Licence |
|---|---|---|
| **Archivo Black** | Titres de couverture, wordmark, slogans t-shirts | SIL Open Font License 1.1 — `assets/fonts/OFL-ArchivoBlack.txt` |
| **Anton** | Sous-titres vidéo, chiffres, étiquettes 3D | SIL Open Font License 1.1 — `assets/fonts/OFL-Anton.txt` |

OFL : usage commercial et incorporation dans images/vidéos/textiles permis ; ne pas vendre les fichiers de fonte seuls ; garder les fichiers OFL avec les fontes si elles sont redistribuées (ex. kit de formation).

## 5. Avatar et wordmark

- **Avatar** (fourni par le propriétaire) : coq blanc de profil sur fond bleu `#1649FF`, crête et barbillon rouges `#EF233C`, œil blasé. Centré dans le cercle, marge ≥ 10 % autour de la crête. Ne jamais ajouter de texte dans l'avatar.
- **Wordmark** : `LE BORDEL FRANÇAIS` en Archivo Black capitales, blanc cassé sur bleu ou noir d'encre sur blanc cassé. Variante courte : `LBF`. Le « Ç » peut porter la seule touche rouge (cédille rouge). Pas d'effets (ombre portée, dégradé, contour).

## 6. Couvertures Reels

- Titre **2 à 5 mots**, Archivo Black capitales, sur un **bandeau bleu** pleine largeur ; **un seul mot en rouge** (le mot absurde).
  Ex. : `MAIRIE EN` **`MAINTENANCE`** · `LE BUS` **`DÉMISSIONNE`**.
- Image : plan large de la ville miniature, sujet lisible en vignette.
- Garder titre et sujet dans la zone centrale : le recadrage de la grille de profil (format affiché **à vérifier**, a priori 3:4) ne doit rien couper.
- Nom de ville en petit (Anton, blanc cassé) sous le bandeau. Jamais de visage photoréaliste.

## 7. Sous-titres

- Anton, **blanc cassé `#FFFDF7` sur pavé sombre `#111827`** (opacité 80–90 %), 1–2 lignes, ≤ 32 caractères/ligne, mot-chute éventuellement en rouge.
- Synchronisés mot à mot ou par groupe de 2–4 mots, jamais en retard sur la voix.
- **Zones sûres Reels** : marges officielles **à vérifier**. Marges internes prudentes (choix maison, non officiel) : rien d'important dans les 15 % du haut, les 25 % du bas, ni dans la colonne droite (icônes j'aime/commentaires). Sous-titres vers 60–70 % de la hauteur.

## 8. Transitions

Coupe sèche par défaut. Trois effets autorisés : **balayage bleu** (changement de lieu), **flash blanc cassé 2 images** (révélation), **volet rouge** (réservé à la chute, 1 fois par vidéo max). Pas de transitions décoratives gratuites.

## 9. Voix et ton

- Narration **posée, sérieuse, administrative** face à l'absurde ; c'est l'image qui fait la blague.
- Phrases courtes. Vocabulaire de communiqué officiel détourné (« Dans un souci de proximité… »).
- Mordant, familier, grossier seulement si la chute y gagne.
- Voix de synthèse Piper : n'utiliser que les voix validées commercialement dans `lbf/config.py` (`fr_FR-siwis-medium`, `fr_FR-mls-medium`). `fr_FR-tom-medium` est marquée non commerciale (jeu de données AGPLv3 selon sa MODEL_CARD) : **ne pas publier**. Choix final de la voix : **à faire par le propriétaire** (tests dans `output/voice_tests/`).
- Attribution CC BY de la voix : à placer dans un lien « Crédits » (page coulisses) et la story à la une « Contact ».

## 10. Interdits (rappel)

Ceux du brief s'appliquent intégralement : aucune fausse citation/aveu/soutien/délit, aucune statistique inventée, aucune vanne sur une caractéristique protégée, aucun visage photoréaliste, aucun appel au vote ou au harcèlement, aucune info privée, pas d'imitation d'humoriste identifié. En plus côté marque : pas de logo de parti, pas de bloc-marque gouvernemental imité, pas de pub payante (cf. §13).

## 11. Mention obligatoire

Sur chaque publication (fin de légende) et dans la bio :
**`Fiction satirique`**
Cocher aussi l'étiquette IA d'Instagram si l'interface ou l'API la propose (champ `is_ai_generated` documenté pour les carrousels ; disponibilité pour Reels **à vérifier**).

## 12. Publications épinglées (3)

1. **Concept** — Reel de présentation (30 s) qui survole les 5 villes.
   Légende : « Cinq villes. Cinq maires imaginaires. Zéro bon sens. Ici on imagine ce que donnerait ta ville si on la confiait aux réflexes de com' de nos politiques. Aucun vrai propos, aucune vraie citation : que de la maquette. Abonne-toi pour la prochaine ville. Fiction satirique »
2. **Meilleur épisode** — choisi sur les statistiques réelles (taux de partage), remplacé si un épisode fait mieux.
   Légende : celle de l'épisode + « 📌 Si tu ne devais en voir qu'un. »
3. **Coulisses / boutique** — Reel « Comment on fabrique une ville en 3D » se terminant sur les t-shirts dans le décor.
   Légende : « Chaque ville est construite en vraie 3D, bloc par bloc. Les t-shirts que tu vois dans le décor existent : lien dans le profil. Liberté. Égalité. N'importe quoi. Fiction satirique »

## 13. Stories à la une (4)

| Titre | Contenu | Icône (bleu, pictogramme blanc cassé) |
|---|---|---|
| **Villes** | 1 story par ville : carte, maire fictif, règle absurde, lien vers le meilleur épisode | maquette de mairie |
| **Boutique** | Visuels des 6 t-shirts, prix réel affiché par la boutique, lien | t-shirt |
| **Coulisses** | Blender, maquettes, ratés de rendu, lien formation | caméra |
| **Contact** | Adresse partenariats (à créer), règles : pas de partenariat avec partis/candidats, crédits (voix, fontes) | enveloppe |

Croissance **organique uniquement** : Meta ne diffuse plus de publicités politiques, électorales ou sur des sujets de société dans l'UE depuis le 6 octobre 2025 (https://about.fb.com/news/2025/07/ending-political-electoral-and-social-issue-advertising-in-the-eu/, consulté le 2026-11-21).
