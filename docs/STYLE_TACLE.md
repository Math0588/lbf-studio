# Style « tacle » — narrations Le Bordel Français (22/11/2026)

Demande du propriétaire : « ultra provocateur, drôle, blagues sourcées de X », « trop soft, faut tacler fort », « durcis à mort ».

## Forme
- Phrase 1, toujours : « Dans cette ville, tout le monde vote <Nom>. » + éventuellement 1 à 3 mots qui piquent (« Enfin, votait. », « Presque. »).
- Puis 4 à 6 piques **frontales**, une par phrase, une par plan : setup court → retournement sec. Pas de description molle, pas de « gentil absurde ».
- Chaque pique s'appuie sur un mème / une formule / un fait que tout le monde reconnaît (content/veille/memes_<ville>.json, ou mème de X/TikTok rapporté par la presse, avec URL + date).
- Avant-dernière phrase = la chute la plus violente (souvent une citation exacte retournée contre son auteur).
- Dernière phrase = partage ciblé : « Envoie ça au pote qui … » (jamais « commente OUI si »).
- 50 à 85 « mots » au total, en comptant comme `len(text.split())` (la ponctuation isolée compte : « ? », « : », « « »).

## Tacler fort, mais légalement
- On tape sur : le bilan, les promesses, les formules publiques, les contradictions, l'image médiatique, la com', les surnoms publics, les mèmes.
- Jamais : un fait inventé présenté comme vrai ; la vie privée, le couple, la famille, la santé, le physique ; l'origine, la religion, le sexe, l'orientation, le handicap, l'âge (y compris des électeurs) ; les affaires judiciaires ; un appel à voter / ne pas voter ; désigner quelqu'un à harceler ; déshumaniser des électeurs (on moque le politicien et la ville fictive, pas « les gens qui votent X »).
- Citations entre « » : uniquement exactes, `claim_type: citation_exacte`, URL dans `claims` et `sources`. Paraphrase d'un mème = sans guillemets.
- Fait chiffré : `fait_public` + source. Exagération évidente de la ville fictive : `fiction_satirique`.
- Jamais les mots « fiction satirique », « IA », « intelligence artificielle » dans la narration ou l'écran.
- Pas de « demain ».
- Validation : `python -c` avec `lbf.editorial.check(ep)` (ajouter `city_id`) → `decision` doit être `pass`, aucune note de nombre de mots.

## Exemple (macronville_pilot_01)
1. Dans cette ville, tout le monde vote Macron. Enfin, votait.
2. Pas de boulot ? Traverse la rue. Ça marche depuis 2018, paraît-il.
3. Les aides ? « Un pognon de dingue ». Les dividendes ? Raisonnables.
4. Ça ruisselle depuis 2017. Seul truc qui coule : la dette.
5. Le maire, c'est Jupiter : il descend juste crier « Hey ! Hey ! ».
6. Son bilan sur X : « parfois des erreurs ». Parfois. For sure.
7. Envoie ça au pote qui croit encore au ruissellement.

## Mise à jour 22/11/2026 : on se fout de la gueule de la PERSONNE (demande du propriétaire)
- Les gags de situation (« Ici, la mairie… ») demandent trop de contexte. On vise le politicien lui-même, sur des trucs
  que tout le monde connaît : phrases cultes, gaffes, tics de langage, surnoms publics, mèmes, défaites, retournements
  de veste, promesses non tenues, image médiatique, com' ratée.
- Forme : « Dans cette ville, tout le monde vote X. » puis chaque phrase = [truc connu sur X] + [retournement qui le
  ridiculise]. Une seule phrase de situation absurde au maximum.
- Contrôle : `python3 -m lbf.viral_lint --strict` (≥ 3 piques sur des faits/mèmes connus et sourcés, ≤ 1 gag de situation).
- Toujours interdit : physique, vie privée, couple, famille, santé, traits protégés, affaires judiciaires, fait inventé.
