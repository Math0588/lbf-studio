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

## Mise à jour 22/11/2026 (2) : UN thème par vidéo, qui monte en puissance
Le propriétaire trouve que les piques sans lien « font le bordel, on comprend pas ». Désormais :
1. « Dans cette ville, tout le monde vote X. » (+ 1 à 3 mots qui annoncent le thème)
2. LE truc connu, posé clairement pour quelqu'un qui ne suit pas la politique (fait/citation sourcé).
3. Escalade 1, 4. Escalade 2, 5. Escalade 3 : le MÊME thème appliqué à des choses de plus en plus énormes
   (bilan, chiffres, autres gaffes connues qui vont dans le même sens). Chaque phrase découle de la précédente.
6. Chute : on retourne le thème contre lui (rappel de la phrase 2, mot de la fin).
7. « Envoie ça au pote qui… » (lié au thème).
Exemple (thème « for sure ») :
- Dans cette ville, tout le monde vote Macron. For sure.
- Depuis Davos, le président répond « for sure » à tout.
- La dette qui explose ? For sure.
- Sept Premiers ministres en un mandat et demi ? For sure.
- Le pays qui coule ? « For sure », en anglais, pour que personne ne comprenne.
- Son bilan sur X : « parfois des erreurs ». Lesquelles ? For sure.
- Envoie ça au pote qui dit « for sure » sans parler anglais.

## Mise à jour 22/11/2026 (3) : une HISTOIRE ABSURDE (format qui remplace la liste de piques)
Référence du propriétaire : « c'est what the fuck, mais il y a une vraie trame ». Toujours absurde, c'est le plus important.
1. « Dans cette ville, tout le monde vote X. » (+ un détail absurde : même le chien porte un t-shirt X)
2. Le point de départ = un truc connu de X (position, slogan, citation, mème), sourcé.
3–5. On le prend AU PIED DE LA LETTRE et ça dégénère, cause → conséquence → pire conséquence, dans la ville.
6. Chute qui retombe sur X lui-même.
7. « Envoie ça au pote qui… »
Exemples d'esprit :
- Mélenchon : « taxer les riches » → les riches partent en courant → plus personne à taxer → les habitants se taxent
  entre eux → baston générale pour savoir qui taxe qui → Mélenchon taxe… la tortue.
- Bardella : tout le monde a la brosse à dents Bardella, le chien en t-shirt Bardella, selfie obligatoire au réveil…
- Glucksmann : le matcha à 10,50 €, le lait d'avoine, la mairie au cap pas clair.
Gags visuels (champ « gags » de chaque scène) : affiches de propagande du politicien, chien en t-shirt, prix délirants,
objets à son effigie. Gestes et expressions (champ « actions ») qui jouent littéralement la phrase.
Contrôle : `python3 -m lbf.viral_lint --histoire` (≥ 1 point de départ sourcé, formule d'ouverture, partage ciblé).
