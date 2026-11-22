# Ce qui fait circuler un Reel : science, règles officielles, observations

Version du 2026-11-21. Recherche web faite le 2026-11-21. Complète `docs/BRIEF_AUTEURS.md` et `docs/INSTAGRAM_SETUP.md`.

## 0. Comment lire ce document

Chaque affirmation porte une étiquette :

| Étiquette | Sens | Ce qu'on peut en tirer |
|---|---|---|
| **[E]** | Résultat d'étude publiée (revue par les pairs ou actes de conférence à comité) | Un mécanisme humain plausible. Rarement mesuré sur Instagram Reels. |
| **[P]** | Déclaration officielle de Meta / Instagram (blog, Help Center, system card, documentation API, propos d'Adam Mosseri) | Ce que la plateforme dit faire. Ce n'est pas une preuve d'effet sur notre compte. |
| **[O]** | Observation de cabinets d'analyse (Buffer, etc.) | Corrélation sur des comptes qui ne sont pas les nôtres. Jamais une cause. |
| **[H]** | Hypothèse créative à tester sur notre compte | À confirmer ou rejeter avec le plan de test (§7). |

Quand une source n'a pas pu être lue directement (pages Meta qui ne se chargent pas par script), c'est signalé « via » une source secondaire ou noté **à vérifier**.

**Ce qu'on ne trouvera pas ici** : « bouton dopamine », « score de viralité », pondérations chiffrées de l'algorithme (« un partage vaut 5 likes ») ni heure magique universelle. Aucune source officielle ne publie ces chiffres. Ceux qui circulent viennent de blogs tiers. Aucune vidéo n'a de vues garanties (voir §2.7).

---

## 1. Ce que dit Instagram : classement des Reels [P]

### 1.1 Signaux de classement

| Point | Ce qui est dit | Source, date |
|---|---|---|
| Les surfaces ont des classements différents | Il n'y a pas « un » algorithme. Feed, Stories, Explore et Reels ont chacun leur système. Dans Reels, la majorité du contenu vient de comptes non suivis. | A. Mosseri, *Instagram Ranking Explained*, 31/05/2023 — https://about.instagram.com/blog/announcements/instagram-ranking-explained |
| Prédictions clés pour Reels (2023) | Dans l'ordre : probabilité de **repartager**, de **regarder jusqu'au bout**, d'**aimer**, de **visiter la page audio** (indice d'envie de créer). Instagram sonde aussi les utilisateurs pour savoir si un Reel était divertissant ou drôle. | Même source, 31/05/2023 |
| Signaux (2023) | Activité de l'utilisateur, historique avec le compte, infos sur le Reel (audio, visuel, popularité), infos sur l'auteur. | Même source |
| Les 3 signaux principaux (2025) | « watch time, likes and sends ». À suivre dans les statistiques : temps de visionnage moyen, **likes par portée**, **envois par portée**. Les likes comptent un peu plus auprès des abonnés, les envois (partages en message) un peu plus auprès des non-abonnés. | Vidéo de Mosseri rapportée par Social Media Today, 22/01/2025 — https://www.socialmediatoday.com/news/instagram-shares-algorithm-insights-2025/738034/ |
| Vues + envois par portée | Mosseri a présenté les vues et les envois par portée comme « probablement » les métriques les plus importantes, au moment où les vues sont devenues la métrique principale. | Août 2024, via https://www.socialmediatoday.com/news/instagram-updates-metrics-to-focus-creators-on-views/723645/ |
| Temps de visionnage relatif et absolu | Instagram regarderait à la fois le % vu et les secondes vues. Une vidéo plus longue n'est donc pas pénalisée par principe. | Propos de Mosseri rapportés par Fanpage Karma (secondaire) — https://www.fanpagekarma.com/insights/instagram-reels-algorithm/ |
| System card « Instagram Reels Chaining » | Prédictions listées, entre autres : commenter, repartager, partager hors d'Instagram, s'abonner à l'auteur, utiliser l'audio, **regarder plus longtemps que 95 % des spectateurs de Reels de même durée**. | Meta Transparency Center — https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/ (page non lisible par script, contenu vu via extraits de recherche ; date de mise à jour **à vérifier**) |
| Diffusion par paliers | Un Reel recommandable est d'abord montré à un petit public, y compris des non-abonnés. S'il marche, il est montré à des publics de plus en plus larges. | Instagram for Creators, *Helping Creators Find New Audiences*, 30/04/2024 — https://creators.instagram.com/recommendations-and-originality |

### 1.2 Recommandabilité : ce qui sort un Reel des recommandations

| Point | Ce qui est dit | Source, date |
|---|---|---|
| Recommendation Guidelines | Ces règles sont plus strictes que les Standards de la communauté. Un contenu autorisé peut ne pas être recommandé. Exemples : contenu sensible ou choquant, **clickbait et « engagement bait »**, contenu faux ou trompeur, contenu de faible qualité. | 30/04/2024 — https://creators.instagram.com/recommendations-and-originality |
| Formats moins visibles | Reels en basse résolution, avec **filigrane**, **muets**, avec bordure, majoritairement texte, ou déjà publiés sur Instagram. | Mosseri, 31/05/2023 (URL §1.1) |
| Originalité (Reels, 2024) | Si deux contenus sont identiques, seul l'original est recommandé. Les comptes qui republient sans créer ni améliorer « substantiellement » sont exclus des recommandations. Le remplacement ne s'applique pas aux contenus transformés (mème, compilation satirique, re-narration, remix réaction). | 30/04/2024 — même URL ; et TechCrunch 30/04/2024 — https://techcrunch.com/2024/04/30/instagram-is-updating-its-ranking-systems-to-surface-more-content-from-smaller-original-creators |
| Originalité (tous formats, 2026) | Extension aux photos et carrousels. **Ajouter seulement un filigrane, une bordure, des sous-titres ou un crédit ne rend pas un contenu original.** L'évaluation porte sur le **compte entier**, en continu, sur une **fenêtre de 30 jours**. Statut visible dans **Statut du compte**, avec appel possible. | *Rewarding original creators on Instagram*, 30/04/2026 — https://creators.instagram.com/blog/rewarding-original-creators-on-instagram |
| Origine de la règle | Depuis 2022, Instagram privilégie le contenu original et dé-priorise les agrégateurs. | TechCrunch, 20/04/2022 — https://techcrunch.com/2022/04/20/instagram-ranking-system-recommend-original-content/ |

### 1.3 Contenu politique : état actuel et conséquences pour nous

| Date | Fait | Source |
|---|---|---|
| 09/02/2024 | Instagram et Threads cessent de recommander de façon proactive le contenu politique (« lois, élections, sujets sociaux ») venant de comptes **non suivis**. Surfaces concernées : Explore, Reels, recommandations dans le fil, comptes suggérés. Les abonnés continuent de voir ce contenu. Les comptes pro peuvent vérifier leur éligibilité dans **Statut du compte**. | https://about.instagram.com/blog/announcements/continuing-our-approach-to-political-content-on-instagram-and-threads |
| 07–08/01/2025 | Revirement. Meta annonce une approche « plus personnalisée » et réintroduit le contenu politique dans les recommandations. Mosseri : réglage à 3 niveaux (**Moins / Standard / Plus**), **Standard par défaut**, déploiement mondial dans les semaines suivantes. Selon lui, tracer une ligne entre politique et non politique s'est révélé « impraticable ». | Engadget, 08/01/2025 — https://www.engadget.com/social-media/threads-and-instagram-will-recommend-political-content-after-all-232343107.html ; TechCrunch, 07/01/2025 — https://techcrunch.com/2025/01/07/meta-to-phase-back-in-political-content-on-facebook-instagram-and-threads |
| 18/09/2025 (selon extrait de recherche) | La page Transparence de Meta dit traiter le contenu politique « plus comme les autres contenus ». Elle peut recommander du contenu politique de comptes non suivis, et chacun peut régler la quantité. | https://transparency.meta.com/features/approach-to-political-content/ (non lisible par script : **à vérifier dans un navigateur**) |
| 06/10/2025 | **Fin des publicités politiques, électorales et sur des sujets de société dans l'UE** (règlement TTPA). Les publications organiques restent autorisées. | https://about.fb.com/news/2025/07/ending-political-electoral-and-social-issue-advertising-in-the-eu/ ; https://developers.facebook.com/blog/post/2025/10/06/prohibiting-ads-about-social-issues-elections-or-politics-from-running-in-the-eu-due-to-regulation/ |

**Conséquences pour Le Bordel Français :**
1. Nos Reels seront très probablement classés « politiques ». La définition (« lois, élections, sujets sociaux ») est large.
2. Depuis janvier 2025, ils **peuvent** être recommandés à des non-abonnés au niveau « Standard ». Les spectateurs réglés sur « Moins » les verront moins. Aucun chiffre public ne mesure l'effet de « Standard » par rapport à « Plus ».
3. On **ne peut pas booster** ces Reels en publicité payante dans l'UE. Une pub pour la boutique doit utiliser un visuel non politique (t-shirt seul), ce qui reste **à vérifier** au cas par cas avec l'outil publicitaire.
4. Il faut contrôler **Statut du compte** chaque semaine : recommandabilité, originalité, contenu signalé.
5. Le ciblage des deux camps est aussi une protection : un compte perçu comme partisan s'expose aux signalements groupés d'un camp.

### 1.4 Format, outils, cadence [P]

| Sujet | Ce qui est dit | Source, date |
|---|---|---|
| Durée max / recommandation | Enregistrement jusqu'à 20 min. Selon le Help Center, les **Reels de plus de 3 min ne sont pas recommandés à de nouveaux publics**. | Help Center https://help.instagram.com/2720958398006062 (non lisible par script ; texte rapporté par CreatorFlow, vérifié le 30/10/2026, et Buffer, 12/11/2026) |
| Durées conseillées | 3–15 s pour tendances et punchlines ; **15–60 s** pour la plupart des formats créatifs ; 60 s–3 min pour les récits longs. | Guide officiel *How to make Instagram Reels*, 28/09/2026 — https://about.instagram.com/blog/tips-and-tricks/how-to-make-instagram-reels (via https://www.socialmediatoday.com/news/instagram-shares-reels-creation-tips-in-new-guide/831551/) |
| Premières secondes | Les premières secondes « décident de tout ». Ouvrir sur une affirmation forte, un visuel surprenant ou une question, couper ce qui ralentit le début, puis vérifier avec le **taux de skip**. | *Creator video editing tips*, Instagram for Creators, via Social Media Today 05/08/2026 — https://socialmediatoday.com/news/instagram-shares-tips-on-video-creation/827172 |
| Taux de skip | Part des vues où le spectateur quitte dans les **3 premières secondes**. Dans Insights depuis 2025, exposé par l'API (`reels_skip_rate`, estimé, « en développement »). Instagram ne publie **aucun seuil de référence**. | API : https://developers.facebook.com/documentation/instagram-platform/reference/instagram-media/insights ; annonce API 03/12/2025 — https://developers.facebook.com/blog/post/2025/12/03/instragram-api-updates/ |
| Texte et sous-titres | Le texte incrusté sert d'accroche et souligne un moment. Les sous-titres rendent tout l'audio visible. Les deux sont complémentaires, et les sous-titres sont recommandés même avec du texte incrusté. Le texte aide le visionnage sans son. | Guide 28/09/2026 et tips 05/08/2026 (URL ci-dessus) |
| Audio | Un Reel **muet** est moins visible (2023). Couper sur le temps fort de la musique (beat markers d'Edits). Les sons tendance sont suggérés. La « visite de la page audio » est une prédiction de classement. | Mosseri 31/05/2023 ; tips 05/08/2026 |
| Trial Reels | Reel montré d'abord **à des non-abonnés seulement**, absent de la grille. Statistiques après 24 h, puis publication aux abonnés à la main, ou automatiquement s'il performe dans les 72 h. **Création possible via l'API de publication** (`trial_params`, d'après la doc et des outils tiers ; valeurs `MANUAL` / `SS_PERFORMANCE` **à vérifier**). Seuil d'éligibilité actuel **à vérifier** (1 000 abonnés selon une source secondaire). | Meta, 10/12/2024 — https://about.fb.com/news/2024/12/trial-reels-try-content-non-followers/ ; API 03/12/2025 (URL ci-dessus) |
| Hashtags | **5 hashtags maximum** par post / Reel depuis décembre 2025. Mosseri répète que les hashtags n'augmentent pas la portée et servent surtout à dire de quoi parle le post. | Social Media Today, déc. 2025 — https://www.socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309/ |
| Fréquence | Pas de fréquence unique : certains réussissent avec 1 post par mois, d'autres avec 5 Reels par jour. Publier plus donne plus de portée, mais il faut un rythme **soutenable**. | Reel de Mosseri rapporté par RouteNote, 06/12/2024 — https://routenote.com/blog/how-often-you-should-post-on-instagram/ |
| Horaires | **Aucune recommandation officielle** trouvée. Voir les observations §3. | — |
| IA | Depuis le 31/08/2026, la portée est limitée pour les **profils** qui présentent une personne générée par IA sans l'étiquette « AI-generated profile ». Ça ne concerne pas l'usage de l'IA comme simple outil. Le brief interdit déjà les visages photoréalistes. | https://techcrunch.com/2026/08/31/instagram-puts-new-limits-on-undisclosed-ai-profiles/ ; https://creators.instagram.com/blog/ai-generated-profile-label |

---

## 2. Ce que disent les études [E]

### 2.1 Émotions et partage

| Étude | Ce qu'elle établit | Limite | Transposable à nos Reels ? |
|---|---|---|---|
| Berger, J. & Milkman, K. L. (2012). What makes online content viral? *Journal of Marketing Research*, 49(2), 192–205. doi:10.1509/jmr.10.0353 | Sur ~7 000 articles du *New York Times* (liste des plus envoyés par e-mail, 3 mois en 2008–2009), le contenu positif circule plus que le négatif. Les émotions à **forte activation** (émerveillement, colère, anxiété) augmentent le partage, celles à faible activation (tristesse) le réduisent. Des expériences confirment le rôle de l'activation. | Articles de presse, partage par e-mail, lectorat du NYT, période ancienne. Effets moyens, beaucoup de variance non expliquée. | **Moyennement.** Le mécanisme (activation → envoi) est plausible pour les envois en DM. Le support est très différent. |
| Berger, J. (2011). Arousal increases social transmission of information. *Psychological Science*, 22(7), 891–893. doi:10.1177/0956797611413294 | En labo, l'activation physiologique (amusement, anxiété, ou même courir sur place) augmente l'intention de partager un contenu sans rapport. | Petits échantillons, intention déclarée et non comportement réel. | **Faiblement à moyennement.** Va dans le même sens : un rire franc, de la surprise. |
| Tellis, G. J., MacInnis, D. J., Tirunillai, S. & Zhang, Y. (2019). What drives virality (sharing) of online digital content? *Journal of Marketing*, 83(4), 1–20. doi:10.1177/0022242919841034 | Sur des pubs YouTube, les émotions positives (inspiration, chaleur, amusement, excitation) et les éléments **dramatiques ou surprenants** augmentent le partage. Le contenu informatif le réduit, sauf pour les achats risqués. Une **marque montrée tôt, longtemps ou souvent réduit le partage**, une apparition tardive moins. | Publicités, pas de satire. Données de 2010s. | **Moyennement.** Appui pour : pas de logo ni de boutique au début, le produit seulement à la fin. |

### 2.2 Humour et satire

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| McGraw, A. P. & Warren, C. (2010). Benign violations: Making immoral behavior funny. *Psychological Science*, 21(8), 1141–1149. doi:10.1177/0956797610376073 | Une situation fait rire quand elle est à la fois une **transgression** (quelque chose cloche) et **bénigne** (sans danger, jeu). Trop de transgression dégoûte, trop peu laisse indifférent. | Théorie testée surtout sur des scénarios écrits, avec des étudiants américains. | **Bien comme grille d'écriture** : la règle absurde est la transgression, la ville miniature fictive la rend bénigne. |
| McGraw, A. P., Warren, C., Williams, L. E. & Leonard, B. (2012). Too close for comfort, or too far to care? *Psychological Science*, 23(10), 1215–1223. doi:10.1177/0956797612443831 | La **distance psychologique** module l'humour. Une tragédie grave est plus drôle de loin (temps, distance), un petit malheur est plus drôle de près. | Labo. | **Oui pour le choix des sujets** : ne pas traiter une actualité tragique à chaud, préférer les tics et postures du quotidien. |
| LaMarre, H. L., Landreville, K. D. & Beam, M. A. (2009). The irony of satire. *International Journal of Press/Politics*, 14(2), 212–231. doi:10.1177/1940161208330904 | Les spectateurs interprètent la satire **selon leur camp**. Des conservateurs pensaient que Colbert se moquait vraiment de la gauche. | Une seule émission américaine, 2000s. | **Oui** : chaque camp verra ce qu'il veut voir. La symétrie entre cibles doit être réelle et visible sur la grille, pas seulement intentionnelle. |
| Poulsen, S., Bond, R. M. & Garrett, R. K. (2023). Comparing beliefs in falsehoods based on satiric and non-satiric news. *PLoS ONE*. doi:10.1371/journal.pone.0278639 | Des affirmations fausses venues d'articles **satiriques** sont crues par une partie notable des Américains. Le signalement « contenu satirique » aide. | Articles écrits « réalistes » (type Babylon Bee). Panel américain. | **Oui, pour l'éthique et le risque de signalement** : il faut un marquage « fiction satirique » visible. Notre 3D stylisée aide aussi à ne pas être pris au premier degré. |

### 2.3 Politique, indignation, « l'autre camp »

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Brady, W. J., Wills, J. A., Jost, J. T., Tucker, J. A. & Van Bavel, J. J. (2017). Emotion shapes the diffusion of moralized content in social networks. *PNAS*, 114(28), 7313–7318. doi:10.1073/pnas.1618923114 | Sur 563 312 tweets (armes, mariage homosexuel, climat), chaque mot **moral-émotionnel** augmente les retweets d'environ **20 %**. La diffusion se fait surtout **à l'intérieur** de chaque camp. | Twitter, texte, États-Unis, corrélationnel. | **Partiellement.** Le mécanisme existe, mais il pousse vers l'entre-soi partisan, l'inverse de notre positionnement. |
| Rathje, S., Van Bavel, J. J. & van der Linden, S. (2021). Out-group animosity drives engagement on social media. *PNAS*, 118(26), e2024292118. doi:10.1073/pnas.2024292118 | Sur 2,7 M de publications Facebook et Twitter (médias, élus américains), chaque mot désignant **l'autre camp** augmente en moyenne de **67 %** la probabilité de partage. C'est le prédicteur le plus fort, environ 4,8 fois plus que le langage négatif. Il est associé aux réactions « colère ». | Corrélationnel, comptes politiques et médias américains, texte, Facebook et Twitter. | **Le mécanisme est réel, et il est éthiquement piégé.** Voir la note éthique (§5). |
| Brady, W. J. et al. (2021). How social learning amplifies moral outrage expression in online social networks. *Science Advances*, 7(33), eabe5641. doi:10.1126/sciadv.abe5641 | Les utilisateurs **récompensés** (likes, retweets) pour une expression d'indignation en expriment davantage ensuite. Les métriques façonnent l'auteur. | Twitter. | **Oui, pour nous-mêmes** : si on optimise à l'aveugle sur l'engagement, on glissera vers l'indignation. D'où les garde-fous de la règle 4. |
| Milli, S. et al. (2025). Engagement, user satisfaction, and the amplification of divisive content on social media. *PNAS Nexus*, 4(3), pgaf062. | Expérience préenregistrée sur Twitter (2023) : l'algorithme fondé sur l'engagement amplifie l'animosité envers l'autre camp, et les utilisateurs **ne préféraient pas** ces tweets. | Twitter de 2023, pas Instagram. | **Oui comme alerte** : l'engagement de colère n'est pas de la satisfaction. Instagram dit sonder la satisfaction (« divertissant / drôle », §1.1). |
| Robertson, C. E. et al. (2023). Negativity drives online news consumption. *Nature Human Behaviour*, 7, 812–822. doi:10.1038/s41562-023-01538-4 | Sur 22 743 tests A/B de titres (Upworthy), les mots négatifs augmentent le taux de clic, environ +2,3 % par mot négatif pour un titre de longueur moyenne. L'effet le plus net vient de la tristesse. | Clics sur titres, pas visionnage ni partage. | **Faible** pour des Reels, mais utile pour le texte d'accroche. |
| McLoughlin, K. L. et al. (2024). Misinformation exploits outrage to spread online. *Science*, 386(6725), 991–996. doi:10.1126/science.adl2829 | Le contenu qui provoque l'indignation est partagé davantage **sans être lu**, indépendamment de son exactitude. | Facebook et Twitter, liens d'actualité. | **Oui pour l'éthique** : une satire mal marquée et indignante peut circuler comme une fausse information. |

### 2.4 Attention, rétention, montage

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Teixeira, T., Wedel, M. & Pieters, R. (2012). Emotion-induced engagement in internet video advertisements. *Journal of Marketing Research*, 49(2), 144–159. doi:10.1509/jmr.10.0207 | Avec eye-tracking et analyse faciale, la **surprise** et la **joie** retiennent l'attention et réduisent l'abandon des vidéos publicitaires. | Publicités, labo, avant les vidéos verticales. | **Moyennement** : vise à créer la surprise très tôt. |
| Teixeira, T., Wedel, M. & Pieters, R. (2010). Moment-to-moment optimal branding in TV commercials. *Marketing Science*, 29(5), 783–804. doi:10.1287/mksc.1100.0567 | Une **marque très présente au début** augmente le zapping. Des apparitions brèves et dosées le limitent. | TV, publicités. | **Oui** : pas de générique, de logo ni de « Bienvenue sur Le Bordel Français » au début. |
| Lang, A., Zhou, S., Schwartz, N., Bolls, P. D. & Potter, R. F. (2000). The effects of edits on arousal, attention, and memory for television messages. *Journal of Broadcasting & Electronic Media*, 44(1), 94–109. doi:10.1207/s15506878jobem4401_7 | Plus de **changements de plan dans une même scène** augmentent l'activation, l'attention et la mémorisation sans surcharge notable. Les coupes vers des scènes **sans rapport** relèvent d'un autre mécanisme et alourdissent la charge cognitive (cadre LC4MP de Lang). | TV des années 1990, messages courts, labo. | **Moyennement** : il faut du rythme, mais lisible (même ville, même gag). |
| Salminen, J., Wahid, R., Yang, X. & Jansen, B. J. (2024). Engagement patterns in TikTok: An analysis of short video ads. *ACM Hypertext '24*, 323–329. doi:10.1145/3648188.3677048 | Sur des pubs TikTok d'environ 57 s, **85,2 %** des abandons ont lieu dans le premier quart de la vidéo. L'abandon le plus fort est au tout début. | Une seule marque, publicités, pas de contenu organique. | **Oui** pour la forme de la courbe : tout se joue au début. |
| Ling, C., Blackburn, J., De Cristofaro, E. & Stringhini, G. (2022). Slapping cats, bopping heads, and Oreo shakes: Understanding indicators of virality in TikTok short videos. *ACM WebSci '22* (arXiv:2111.02452) | Sur 400 TikToks annotés, les vidéos virales ont plus souvent un **plan rapproché ou moyen** face caméra et du **texte à l'écran**. Le nombre d'abonnés du créateur est le facteur le plus fort. Empiler les hashtags ne sert à rien. | Petit échantillon, viralité définie par les likes, TikTok. | **Faiblement** : indice cohérent avec les règles 6 et 9. |

### 2.5 Visages et personnages

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Bakhshi, S., Shamma, D. A. & Gilbert, E. (2014). Faces engage us: Photos with faces attract more likes and comments on Instagram. *CHI '14*. doi:10.1145/2556288.2557403 | Sur ~1,1 M de photos Instagram, une photo avec visage a **38 %** plus de chances d'avoir des likes et **32 %** plus de chances d'avoir des commentaires, à audience contrôlée. Publier plus souvent est associé à moins de likes par photo. | Photos, Instagram de 2013, visages humains réels, corrélationnel. | **Partiellement** : nos visages sont des personnages 3D stylisés. Que l'effet tienne pour eux reste une **[H]**. |
| Cerf, M., Harel, J., Einhäuser, W. & Koch, C. (2008). Predicting human gaze using low-level saliency combined with face detection. *NIPS 20*. | Les visages attirent le regard plus fortement et plus vite que les autres éléments d'une image. | Labo, images fixes. | **Moyennement** : un visage expressif dans la première image aide à capter le regard. |

### 2.6 Sous-titres

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Gernsbacher, M. A. (2015). Video captions benefit everyone. *Policy Insights from the Behavioral and Brain Sciences*, 2(1), 195–202. doi:10.1177/2372732215602130 | Revue de plus de 100 études : les sous-titres améliorent la compréhension, l'attention et la mémorisation, surtout chez les non-natifs, les apprentis lecteurs et les personnes sourdes. | Contexte éducatif. Une critique (Watson) juge « everyone » trop fort et rappelle le risque de redondance si la charge est déjà élevée. | **Oui**, surtout pour le visionnage sans son. Des sous-titres courts, synchronisés et lisibles, pas un mur de texte. |

### 2.7 La viralité est en grande partie imprévisible

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Salganik, M. J., Dodds, P. S. & Watts, D. J. (2006). Experimental study of inequality and unpredictability in an artificial cultural market. *Science*, 311(5762), 854–856. doi:10.1126/science.1121066 | 14 341 participants, 48 chansons, plusieurs « mondes » parallèles. L'influence sociale (voir les téléchargements des autres) **augmente l'inégalité et l'imprévisibilité** du succès. Les meilleures chansons font rarement très mal et les pires rarement très bien, mais tout le reste est possible. | Marché artificiel. | **Oui, fondamental** : la qualité aide, mais un même Reel peut faire 2 000 ou 200 000 vues selon les premiers spectateurs. Il faut juger une série de vidéos, pas une seule. |
| Cheng, J., Adamic, L., Dow, P. A., Kleinberg, J. & Leskovec, J. (2014). Can cascades be predicted? *WWW '14*, 925–936. doi:10.1145/2566486.2567997 | Sur des partages de photos Facebook, on prédit assez bien si une cascade **déjà lancée** va doubler, surtout grâce à la **vitesse des premiers partages**. Le contenu seul prédit beaucoup moins bien. | Facebook 2013. | **Oui** : les premières heures informent, mais on ne prédit pas un tube avant publication. |
| Martin, T., Hofman, J. M., Sharma, A., Anderson, A. & Watts, D. J. (2016). Exploring limits to prediction in complex social systems. *WWW '16* (arXiv:1602.01013) | Même avec beaucoup de données sur les utilisateurs, le contenu et l'historique, les meilleurs modèles expliquent **moins de la moitié** de la variance de la taille des cascades Twitter. La limite théorique est du même ordre. | Twitter. | **Oui** : toute promesse de « score de viralité » est infondée. |
| Bakshy, E., Hofman, J. M., Mason, W. A. & Watts, D. J. (2011). Everyone's an influencer. *WSDM '11*. doi:10.1145/1935826.1935845 | Les grosses cascades sont rares et peu prévisibles individuellement. Multiplier les « petits paris » est plus fiable que miser sur un seul gros coup. | Twitter 2009–2010. | **Oui** : régularité et volume raisonnable plutôt qu'un épisode « parfait ». |
| Goel, S., Anderson, A., Hofman, J. & Watts, D. J. (2016). The structural virality of online diffusion. *Management Science*, 62(1), 180–196. doi:10.1287/mnsc.2015.2158 | La plupart des diffusions sont très peu profondes (un compte vers ses abonnés). Les diffusions virales « de proche en proche » sont rares et de formes variées. | Twitter. | **Oui** : le partage en DM, de proche en proche, est le levier rare qui fait sortir de la base d'abonnés. |

### 2.8 Partager à une personne vs à tout le monde

| Étude | Ce qu'elle établit | Limite | Transposable ? |
|---|---|---|---|
| Barasch, A. & Berger, J. (2014). Broadcasting and narrowcasting: How audience size affects what people share. *Journal of Marketing Research*, 51(3), 286–299. doi:10.1509/jmr.13.0238 | Quand on partage à **une seule personne**, l'attention se porte sur le destinataire : on partage ce qui lui est **utile ou pertinent**, et moins ce qui flatte sa propre image. En diffusion large, on évite ce qui nous fait mal paraître. | Expériences en ligne, partage déclaré. | **Oui, directement** pour les « envois » Instagram (DM = narrowcasting). Un Reel envoyé est un Reel qui « parle de » quelqu'un que le spectateur connaît. |

---

## 3. Observations de plateformes d'analyse [O] (non causales)

| Observation | Données | Limite | Source, date |
|---|---|---|---|
| Durée et portée | 2,73 M de Reels (janv.–août 2026), chaque compte comparé à lui-même : 90–179 s = +7,4 % de portée (≈ +4 % pour un compte typique), 30–59 s = +2,7 %, < 15 s = −1,5 %, **> 180 s = −49 % de portée**. Sous 90 s, les écarts (≤ 3 %) sont négligeables. | Clients Buffer, corrélation. L'auteur précise qu'allonger une vidéo n'ajoutera pas 7 %. | Buffer, 12/11/2026 — https://buffer.com/resources/instagram-reels-length |
| Horaires | Sur 9,6 M de posts, meilleurs créneaux : jeudi 9 h, mercredi 12 h, mercredi 18 h. Le soir (18–23 h) est solide, 1–5 h est le pire. D'autres études (Later, Sprout) donnent des créneaux **contradictoires**. | Fuseaux et publics majoritairement anglophones, formats mélangés. | Buffer 2026 — https://buffer.com/resources/when-is-the-best-time-to-post-on-instagram |
| Fréquence | Sur plus de 2 M de posts, 3 à 5 posts par semaine est associé à plus de portée par post qu'un rythme plus faible. | Corrélation, clients Buffer. | Buffer — https://buffer.com/resources/how-often-to-post-on-instagram/ |
| Visionnage muet | Sondage Verizon Media / Publicis Media (avril 2019, 5 616 adultes américains) : **69 %** regardent des vidéos sans le son dans les lieux publics, 25 % même en privé. Le chiffre « 80 % plus susceptibles de finir une vidéo sous-titrée » est rapporté de façon **variable** selon les sources. | Déclaratif, États-Unis, 2019, avant Reels. | Via 3Play Media — https://www.3playmedia.com/blog/verizon-media-and-publicis-media-find-viewers-want-captions/ |
| Hashtags | Au-delà de 5 hashtags, portée en baisse (Fanpage Karma). Moins de hashtags, portée légèrement meilleure (test Hootsuite). | Données vendeurs. | https://www.fanpagekarma.com/insights/how-many-hashtags-should-you-use-on-instagram/ |

---

## 4. Ce qui n'est pas établi

| Affirmation courante | Statut |
|---|---|
| « Un envoi vaut 3 à 5 likes » | Aucune source officielle. Meta ne publie pas de poids. |
| « Il faut X % de rétention pour être poussé » | Aucun seuil officiel. Le taux de skip n'a pas de valeur de référence publiée. |
| « La 1re heure décide de tout » | Cheng et al. montrent que la vitesse initiale **prédit** la croissance. Ce n'est pas une règle d'Instagram, et la diffusion par paliers (§1.1) peut redémarrer plus tard. |
| « Le son tendance booste la portée » | Instagram suggère les sons tendance. La visite de la page audio est une prédiction (2023). Aucun effet chiffré. Pour un compte de narration, la voix prime. **[H]** |
| « Heure idéale universelle » | Les études contredisent entre elles. À tester sur notre audience française. |

---

## 5. Note éthique : l'animosité marche, on ne s'en sert pas

Rathje et al. (2021) le montrent honnêtement : parler de « l'autre camp » avec hostilité est le prédicteur d'engagement le plus fort qu'ils aient mesuré. Brady et al. (2021) montrent que ces récompenses entraînent les auteurs à en faire davantage. Milli et al. (2025) montrent que ce contenu n'est pas préféré par les utilisateurs. McLoughlin et al. (2024) montrent que l'indignation se partage sans lecture.

Notre ligne :
- **On vise les postures publiques** des personnalités (communication, tics, promesses, mise en scène), **jamais un groupe** (électeurs, origine, religion, etc.). C'est déjà l'interdit absolu du brief.
- **Rotation des cibles** sur les cinq villes, suivie dans un tableau. Aucun camp ne doit dépasser l'autre sur 10 vidéos glissantes.
- **Le ressort comique est l'absurde (activation positive : surprise, amusement)**, pas la colère. Les deux ont une forte activation (Berger & Milkman), mais seul le premier est compatible avec un public des deux camps et avec la satisfaction que mesure Instagram.
- **Marquage « fiction satirique »** dans la bio (déjà fait) et un carton bref dans la vidéo (Poulsen et al. 2023).
- Les CTA ne doivent pas être de l'« engagement bait » (« partage si tu es d'accord », « tague un ami de gauche ») : les Recommendation Guidelines le dé-recommandent, et cela vise un groupe.

---

## 6. Règles de production

| # | Règle | Source(s) | Niveau de preuve |
|---|---|---|---|
| 1 | **Image déjà surprenante à 0 s.** Pas de logo, de générique, de « salut » ni de fondu au noir. Le premier plan montre la ville en train de dérailler, avec un visage expressif. | Guide Instagram 05/08/2026 et 28/09/2026 ; Teixeira 2010, 2012 ; Salminen 2024 | [P] + [E] moyen |
| 2 | **Écrire chaque épisode pour être envoyé en DM.** Le gag doit évoquer une personne précise (« mon maire », « mon beau-frère », « ma boîte »). Tester un CTA parlé de partage ciblé non manipulatoire (« envoie-le à celui qui… »), pas de « partage si d'accord ». | Mosseri 22/01/2025 (envois/portée, non-abonnés) ; Barasch & Berger 2014 ; Recommendation Guidelines 30/04/2024 | [P] + [E] + [H] pour le CTA |
| 3 | **Viser le rire de surprise (forte activation positive)**, pas la tristesse ni l'ironie molle. Une escalade de 2–3 révélations, puis la chute. | Berger & Milkman 2012 ; Berger 2011 ; Tellis 2019 ; McGraw & Warren 2010 | [E] moyen |
| 4 | **Satire des postures, jamais d'un groupe.** Rotation des 5 villes, équilibre gauche/droite sur 10 vidéos glissantes, pas d'actualité tragique à chaud. | Rathje 2021 ; Brady 2021 ; Milli 2025 ; McGraw 2012 ; LaMarre 2009 ; brief | [E] + éthique |
| 5 | **Durée 30–55 s, jamais plus de 3 min.** La durée sert le gag, pas l'inverse. Couper toute seconde sans information ni rire, pour garder le temps de visionnage relatif. | Help Center (> 3 min non recommandé) ; guide 28/09/2026 (15–60 s) ; Mosseri (temps relatif et absolu) ; Buffer 12/11/2026 | [P] + [O] |
| 6 | **Sous-titres incrustés synchronisés** (Anton, blanc cassé sur bandeau), dans la zone centrale, à l'écart des boutons et de la légende. Plus un **texte d'accroche** de 3–6 mots sur la première image. | Guide 28/09/2026 ; tips 05/08/2026 ; Gernsbacher 2015 ; Ling 2022 ; Verizon/Publicis 2019 | [P] + [E] + [O] |
| 7 | **Jamais de Reel muet.** Voix off et ambiance sonore toujours présentes. Audio original nommé (« Le Bordel Français – [épisode] ») pour pouvoir être réutilisé. Musique sous licence seulement si le type de compte y donne accès (**à vérifier**). | Mosseri 31/05/2023 (muet moins visible ; page audio) ; tips 05/08/2026 | [P] |
| 8 | **100 % original, export propre** : 1080×1920, 9:16, pas de filigrane (CapCut, TikTok, banque d'images), pas de bordure, pas de republication d'extraits TV ou de discours bruts. Un recyclage d'un de nos Reels doit être réellement retravaillé. | Ranking explained 2023 ; Originalité 30/04/2024 et 30/04/2026 | [P] |
| 9 | **Visage de personnage en plan rapproché ou moyen** dans les 2 premières secondes et à la chute. | Bakhshi 2014 ; Cerf 2008 ; Ling 2022 | [E] faible à moyen + [H] pour la 3D |
| 10 | **Rythme lisible** : un changement de plan ou une révélation toutes les 2–4 s **dans la même ville**, en laissant respirer la chute (~1 s de silence). | Lang 2000 ; brief | [E] moyen + [H] pour la cadence chiffrée |
| 11 | **Marquage satirique** : « Fiction satirique » en bio (fait) et petit carton ou mention en légende. Jamais de visuel photoréaliste ni de fausse citation. | Poulsen 2023 ; McLoughlin 2024 ; politique IA Meta 31/08/2026 ; brief | [E] + [P] |
| 12 | **5 hashtags maximum**, descriptifs (#satire #humour #politiquefrançaise…). Ne rien en attendre pour la portée. | Limite déc. 2025 ; Mosseri | [P] |
| 13 | **Cadence soutenable avant tout.** Le projet vise 1 Reel par jour : ne garder ce rythme que si la qualité (règles 1–4) tient. Sinon, 4–5 par semaine. Une vidéo ratée publiée dégrade les ratios moyens. | Mosseri 06/12/2024 ; Bakhshi 2014 (plus de posts, moins de likes par post) ; Buffer [O] ; Bakshy 2011 | [P] + [E] + [O] |
| 14 | **Contrôle hebdomadaire de « Statut du compte »** (recommandabilité, contenu politique, originalité) et **aucune pub payante sur un Reel politique dans l'UE**. | Instagram 09/02/2024 et 30/04/2026 ; Meta TTPA 06/10/2025 | [P] |
| 15 | **Juger sur des séries, jamais sur une vidéo.** Aucune vidéo n'est « ratée » ou « géniale » seule. On décide sur des médianes de 5 à 10 vidéos (§7). Aucune promesse de vues. | Salganik 2006 ; Martin 2016 ; Cheng 2014 | [E] fort |

---

## 7. Plan de test : les 20 premières vidéos

### 7.1 Ce que l'API expose vraiment (Reels)

Endpoint `GET /{ig-media-id}/insights?metric=…`, doc consultée le 21/11/2026 (v27.0) : https://developers.facebook.com/documentation/instagram-platform/reference/instagram-media/insights

| Métrique API | Définition (doc Meta) | Remarque |
|---|---|---|
| `views` | Lectures sur Instagram | « En développement » |
| `reach` | Comptes uniques ayant vu le Reel | Estimée |
| `likes`, `comments`, `saved`, `shares` | Comptages | `shares` = ce qu'Instagram appelle « envois/partages » |
| `reposts` | Republications (moins celles supprimées) | Depuis déc. 2025 |
| `total_interactions` | Likes + sauvegardes + commentaires + partages, nets | « En développement » |
| `ig_reels_avg_watch_time` | Temps de lecture moyen | Unité (ms ?) **à vérifier** au premier appel |
| `ig_reels_video_view_total_time` | Temps total, revisionnages inclus | « En développement » |
| `reels_skip_rate` | % de vues abandonnées dans les 3 premières secondes | Estimée, « en développement » |
| `crossposted_views`, `facebook_views` | Vues Facebook si crossposté | Seulement si partagé sur Facebook |

**Pas disponible par Reel via l'API** : abonnements générés (`follows`, `profile_visits` réservés aux posts et Stories), répartition abonnés / non-abonnés, courbe de rétention seconde par seconde. Ces données sont à **relever à la main dans l'app** (Insights du Reel) au même moment que l'appel API. Le nombre d'abonnés du compte se suit chaque jour au niveau compte (métrique compte, nom exact **à vérifier**).

### 7.2 Ratios calculés (par vidéo)

| Ratio | Formule | Pourquoi |
|---|---|---|
| **Taux d'envoi** | `shares / reach` | Signal n°1 cité par Mosseri pour les non-abonnés |
| Taux de like | `likes / reach` | Signal cité pour les abonnés |
| Taux de sauvegarde | `saved / reach` | Intérêt durable (indicateur secondaire) |
| Taux de commentaire | `comments / reach` | Prédiction listée dans la system card |
| **Visionnage relatif** | `ig_reels_avg_watch_time / durée de la vidéo` | Approche du « regarder jusqu'au bout » |
| **Taux de skip** | `reels_skip_rate` | Qualité de l'accroche (règle 1) |
| Revisionnage | `views / reach` | Une valeur > 1 indique des revisionnages ou des boucles |
| Part non-abonnés (app) | relevé manuel | Mesure si le Reel sort de la base |
| Abonnés gagnés (app) | relevé manuel / `reach` | Conversion |

Relevés à **J+1 (24 h), J+3 et J+7**, à heure fixe, dans un CSV `data/` (une ligne par vidéo et par relevé). On note aussi : date et heure de publication, durée, ville ciblée, camp, type d'accroche, type de CTA, Trial ou non, présence d'un visage à 0 s.

### 7.3 Protocole

**Principe** : avec 20 vidéos et une diffusion à queue lourde (§2.7), aucun test n'aura de puissance statistique. On fait de l'**exploration structurée** : hypothèses écrites **avant** publication (dans `docs/JOURNAL_DECISIONS.md`), une variable par bloc, comparaison par **médianes et rangs**, jamais par moyennes ni sur une vidéo isolée.

| Bloc | Vidéos | Variable testée (le reste est fixe) | Hypothèse [H] | Métrique de décision |
|---|---|---|---|---|
| A | 1–8 | **Accroche** : (a) image absurde + texte 3–6 mots, ou (b) question parlée face caméra du personnage. Alternance a/b/a/b, chaque ville vue avec a et b. | (a) donne un taux de skip plus bas | `reels_skip_rate`, visionnage relatif |
| B | 9–14 | **CTA final** : (a) aucun CTA parlé, ou (b) partage ciblé non manipulatoire (« envoie-le à quelqu'un qui… »). Alternance. | (b) augmente `shares/reach` sans baisser le visionnage relatif | `shares/reach` |
| C | 15–20 | **Créneau** (heure de Paris) : (a) 12 h 30, ou (b) 19 h 00. Alternance, mêmes jours de semaine répartis. | Pas d'hypothèse forte (les études se contredisent) | `reach` J+1, part non-abonnés |
| Tout le long | 1–20 | Rotation des 5 villes, durée 30–55 s, règles 5–12 fixes | — | Équilibre gauche/droite vérifié |

**Trial Reels (si le compte y est éligible)** : utiliser l'option Trial (API `trial_params`, **à vérifier**) pour tester une **accroche alternative d'un même épisode** auprès de non-abonnés avant la publication principale. Le risque d'être traité comme un doublon par la règle d'originalité est **à vérifier** : ne pas faire passer aux abonnés deux variantes quasi identiques.

**Règle de décision** : une variante est retenue si sa médiane est meilleure **dans les deux moitiés du bloc**, et si le taux de skip et le visionnage relatif ne se dégradent pas. Sinon, c'est « non concluant » : on garde la version la plus simple et on re-teste sur les vidéos 21–40. La valeur de référence est toujours **la médiane du compte** sur les vidéos précédentes, jamais un benchmark externe. Instagram n'en publie pas, et ceux des cabinets ne portent pas sur notre niche.

**Garde-fous** :
- Si une vidéo dépasse 5 fois la médiane de portée, on l'analyse **qualitativement** (sujet, accroche, cible) mais on **ne la compte pas** comme preuve d'une règle (Salganik 2006).
- Si `shares/reach` monte sur les vidéos les plus agressives envers un camp, on **ne suit pas** ce signal (§5) et on le note au journal.
- Chaque semaine, on contrôle Statut du compte et l'équilibre des cibles.

### 7.4 Sorties attendues après 20 vidéos

1. Un tableau des 20 vidéos avec les ratios à J+1 et J+7.
2. Pour chaque bloc : retenu / rejeté / non concluant, avec les médianes.
3. Une mise à jour des règles 1, 2 et 13 si les données le justifient. Toute autre règle ne change que sur une nouvelle source officielle ou scientifique.
