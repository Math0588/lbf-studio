# Le Bordel Français tourne seul (sans Claude, PC éteint)

Tout est hébergé sur GitHub (gratuit) :

| Quoi | Où | Quand |
|---|---|---|
| **Horloge** (`horloge.yml`) | dépôt public lbf-studio | en continu ; se relance seule toutes les ~5 h 40 |
| **Fabrication** des vidéos (`produce.yml`) | lbf-studio | lancée par l'horloge quand la réserve passe sous 10 vidéos |
| **Publication** Instagram (`publish.yml`) | dépôt privé lbf-diffusion | lancée par l'horloge à chaque créneau (+ relance 30 min après) |

Créneaux : `state/control.json` du diffuseur (aujourd'hui 8h, 12h, 17h, 20h, 22h). L'horloge relit ce fichier
toutes les heures : il suffit de le modifier sur GitHub pour changer le rythme. `"paused": true` arrête tout.

Si l'horloge s'arrête : chaque fabrication la relance, et le cron GitHub aussi (quand il veut bien partir).
À la main : onglet **Actions** de lbf-studio → **Horloge** → **Run workflow**.

## À faire une seule fois (5 minutes)

### 1. Jeton pour que l'horloge puisse publier (obligatoire)

L'horloge est dans le dépôt public, la publication dans le dépôt privé : il lui faut une clé limitée à ce dépôt.

1. https://github.com/settings/personal-access-tokens/new
2. Nom : `lbf-horloge` ; expiration : la plus longue proposée (noter la date dans un agenda).
3. **Repository access** → *Only select repositories* → `lbf-diffusion`.
4. **Permissions** → *Repository permissions* :
   - **Actions** : *Read and write*
   - **Contents** : *Read-only*
5. **Generate token**, copier la clé.
6. https://github.com/Math0588/lbf-studio/settings/secrets/actions → **New repository secret**
   - Name : `DIFFUSION_TOKEN`
   - Secret : coller la clé → **Add secret**.

Sans ce jeton, les vidéos continuent d'être fabriquées mais la publication ne dépend plus que du cron GitHub
(très irrégulier).

### 2. Bonne voix (conseillé)

Sans clé, la voix de secours (Piper) est utilisée : correcte mais robotique.

**ElevenLabs** (la voix des meilleures vidéos) :
1. https://elevenlabs.io/app/settings/api-keys → **Create API key** (droit *Text to Speech* suffit).
2. https://github.com/Math0588/lbf-studio/settings/secrets/actions → secret `ELEVENLABS_API_KEY`.

Budget : une vidéo ≈ 560 caractères. Gratuit 10 000/mois ≈ 17 vidéos (3 jours à 5/jour), puis secours
automatique. Pour 5 vidéos/jour tout le mois (~85 000 caractères) : offre *Creator*. Si la voix « Hugo »
est refusée par l'API (certaines voix de la bibliothèque sont réservées aux offres payantes), choisir une voix
française dans *Voices* et mettre son identifiant dans la **variable** `ELEVENLABS_VOICE_ID`
(Settings → Secrets and variables → Actions → onglet *Variables*).

**Azure** (gratuit 500 000 caractères/mois, voix neuronale française) : secrets `AZURE_SPEECH_KEY` et
`AZURE_SPEECH_REGION`. Utilisé automatiquement quand ElevenLabs est absent ou épuisé.

Ordre automatique : ElevenLabs → Azure → Piper. Jamais deux voix dans la même vidéo.

## Ce qui ne se fait plus sans Claude

- Nouveaux scripts liés à l'actualité : la banque contient ~400 histoires validées (≈ 80 jours à 5/jour).
- Corrections de bugs : les journaux sont dans l'onglet **Actions** de chaque dépôt.
