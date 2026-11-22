# Schémas de contenu — Le Bordel Français

Tous les fichiers sont en UTF-8, JSON valide, français correct (accents, espaces insécables non requis).
Tout le contenu est de la **fiction satirique** : aucune citation réelle inventée, aucun délit ou
événement réel inventé, aucune blague reposant sur l'origine, la religion, le handicap, le sexe,
l'orientation ou toute caractéristique protégée. On vise les postures publiques, la communication,
l'ego, les contradictions et les tics de langage publics.

## 1. Bible de ville — `content/cities/<slug>.json`

```json
{
  "slug": "bardellaville",
  "name": "Bardellaville",
  "inspired_by_public_codes_of": "Jordan Bardella (codes publics de communication uniquement)",
  "disclaimer": "Ville fictive. Aucune politique réellement mise en œuvre.",
  "central_rule": "Tout fonctionne pour la photo, rien pour l'usage.",
  "secondary_traits": ["...", "...", "..."],
  "mood": {"architecture": "...", "materials": "...", "signage": "...", "light": "...", "sound": "..."},
  "map": {
    "mairie": "...", "centre_ville": "...",
    "quartiers": [{"id": "q-studio", "name": "...", "description": "..."}],
    "transports": ["..."], "commerces": ["..."], "loisirs": ["..."]
  },
  "recurring_characters": [
    {"id": "bdv-char-01", "name": "...", "role": "employé municipal", "look": "forme simple 3D, couleur...", "running_trait": "..."}
  ],
  "running_gags": [
    {"id": "bdv-gag-01", "base": "...", "evolution": ["étape 1", "étape 2", "étape 3"]}
  ],
  "continuity_events": [
    {"id": "bdv-evt-000", "status": "established", "description": "Le rond-point central a un ring light géant.", "since_episode": null}
  ],
  "arcs": [
    {"id": "bdv-arc-01", "title": "...", "episodes": ["bdv-syn-01", "bdv-syn-02", "..."]}
  ],
  "blender_props_needed": ["ring_light", "studio_light", "sign", "..."]
}
```

`continuity_events.status` : `established` (fait de l'univers), `unpublished_idea`, `shown` (montré dans un épisode publié).

## 2. Synopsis — `content/synopses/<slug>.json`

Liste d'au moins 30 objets. **Un titre seul ne compte pas.**

```json
{
  "id": "bdv-syn-01",
  "city": "bardellaville",
  "format": "A",
  "domain": "circulation",
  "title": "Le rond-point studio",
  "daily_problem": "Sortir d'un rond-point aux heures de pointe.",
  "hook": "Dans cette ville, même les ronds-points ont un ring light.",
  "development_1": "...",
  "development_2": "...",
  "visual_punchline": "...",
  "set_needed": ["roundabout", "ring_light", "car"],
  "cta_idea": "Le pire : le GPS ou la mairie ?",
  "comic_mechanism": "image > fond",
  "arc_id": "bdv-arc-01",
  "continuity_uses": ["bdv-evt-000"],
  "continuity_adds": ["..."],
  "bite_level": "mordante"
}
```

- `format` : `A` (Si X gérait ta ville), `B` (copro), `C` (Mise à jour de la France), `D` (Simulateur de président).
- `domain` : un des domaines du réservoir (mairie, démarches administratives, métro, bus, circulation, permis
  de conduire, logement, copropriété, école, cantine, université, recrutement, bureau, boulangerie, supermarché,
  restaurant, salle de sport, stade, parc, collecte des déchets, travaux, panne d'électricité, tourisme,
  fête municipale, conseil de quartier, livraison, nouvelles technologies, marché, vacances, visite d'une ville voisine).
  30 synopsis par ville doivent couvrir au moins 20 domaines différents.
- `comic_mechanism` : courte étiquette du ressort comique, utilisée par l'anti-répétition. Varier.
- `bite_level` : `piquante`, `mordante`, `très mordante`.

## 3. Script complet — `content/scripts/<slug>_pilot_NN.json`

```json
{
  "id": "bdv-s01e02",
  "city": "bardellaville",
  "synopsis_id": "bdv-syn-02",
  "format": "A",
  "title_cover": "2 à 5 mots",
  "hook_variants": ["5 accroches"],
  "selected_hook": 0,
  "ending_variants": ["3 chutes"],
  "selected_ending": 0,
  "narration_segments": [
    {"id": "n1", "text": "Phrase dite par la voix.", "accent_words": ["ring light"], "claim_type": "fiction_satirique"}
  ],
  "scenes": [
    {"id": "s1", "narration_ids": ["n1"], "camera": "descend|street_dolly|window_pass|orbit|closeup|return",
     "set": ["props du catalogue"], "onscreen_text": "texte écran court ou vide",
     "comic_action": "ce qui se passe à l'image", "expected_result": "ce que le spectateur doit comprendre"}
  ],
  "cta_primary": {"type": "comment|share|follow", "text": "..."},
  "cta_commercial": {"type": "visual_product|bio_mention", "text": "Collection en bio", "product_id": "tee-pays-bugue"},
  "word_count": 70,
  "claims": [],
  "sources": [],
  "disclosure": "Fiction satirique",
  "editorial_notes": "pourquoi c'est drôle, risques vérifiés"
}
```

Règles : 55 à 80 mots de narration au total ; une prémisse, trois développements maximum, une chute ;
0–1,5 s = image déjà surprenante (pas de logo) ; un seul CTA parlé ; CTA commercial visuel court.
`claim_type` ∈ `fiction_satirique`, `fait_public`, `citation_exacte`, `incertain`. Les pilotes n'utilisent que
`fiction_satirique` sauf fait public sourcé (URL + date dans `sources`).

## Catalogue de props Blender disponibles (moteur `blender/engine.py`)

`ground, road, roundabout, building, mairie, facade_set, ring_light, studio_light, tripod_camera, sign,
car, car_orbit, bus, tree, lamp, bench, bin, shop, tshirt, mascot, gps, screen, text3d, person, tribune,
lift_tribune, table, form_stack, traffic_light, router_lectern, scroll, banner, column, arch, fountain`

Un script ne peut promettre que des visuels construits avec ces props (combinables, animables :
apparition, disparition, montée/descente, rotation, couleur de lumière, texte changeant).
Sinon, indiquer `"new_asset_request": "description"` dans la scène.
