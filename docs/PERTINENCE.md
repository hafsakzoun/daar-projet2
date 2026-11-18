# Test de pertinence du classement

Mesuré le 18 novembre 2026 sur l'index complet (1 700 livres). Données :
[`pertinence/pertinence.csv`](pertinence/pertinence.csv) et les trois premiers
résultats de chaque classement dans [`pertinence/exemples.csv`](pertinence/exemples.csv).

Reproduire :

```bash
docker compose exec backend python -m scripts.relevance_eval --out /tmp/pertinence
```

## Protocole

L'énoncé définit la pertinence comme un critère subjectif établi par des tests
utilisateur. Pour obtenir une mesure **reproductible**, chaque requête reçoit un
critère objectif fixé à l'avance : un livre est jugé pertinent si son titre ou
son auteur y correspond.

| Requête | Livre pertinent si titre ou auteur contient |
|---|---|
| whale | whal, moby |
| sherlock holmes | sherlock, holmes, doyle |
| vampire | vampir / vampyr, dracula, carmilla |
| pirate | pira, pyrat, treasure island, buccaneer |
| alice | alice |
| napoleon | napol, bonaparte |
| egypt | egypt |
| ghost | ghost |
| garden | garden |
| witch | witch |
| recipe | cook, recipe |

Ce jugement **sous-estime** la pertinence réelle : un roman maritime peut parler
de baleines sans le dire dans son titre. Mais il est identique pour tous les
classements comparés, ce qui suffit pour les départager.

Mesures sur les 10 premiers résultats :

- **P@5** : part de livres pertinents parmi les 5 premiers ;
- **MRR** : 1 / rang du premier livre pertinent (1 = en tête) ;
- **nDCG@10** : qualité de l'ordre, 1 = classement idéal.

Classements comparés :

| Classement | Définition |
|---|---|
| Fréquence | occurrences de la requête par million de mots du livre (défaut de l'application) |
| PageRank | centralité du livre dans le graphe de Jaccard |
| Produit | fréquence × PageRank |
| Fusion | fusion des rangs réciproques (RRF, k = 60) de la fréquence et du PageRank |

## Résultats moyens (11 requêtes)

| Classement | P@5 | MRR | nDCG@10 |
|---|---:|---:|---:|
| **Fréquence** | **0,53** | **0,88** | **0,65** |
| Produit | 0,47 | 0,82 | 0,58 |
| Fusion | 0,25 | 0,50 | 0,36 |
| PageRank | 0,02 | 0,05 | 0,02 |

## Par requête

| Requête | Résultats | Pertinents trouvés | P@5 fréquence | P@5 PageRank | P@5 produit | nDCG@10 fréquence | nDCG@10 PageRank | nDCG@10 produit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| whale | 467 | 3 | 0,6 | 0,0 | 0,6 | 1,0 | 0,0 | 1,0 |
| sherlock holmes | 353 | 15 | 1,0 | 0,0 | 1,0 | 1,0 | 0,0 | 0,922 |
| vampire | 167 | 4 | 0,2 | 0,2 | 0,2 | 0,66 | 0,246 | 0,76 |
| pirate | 598 | 4 | 0,2 | 0,0 | 0,2 | 0,151 | 0,0 | 0,39 |
| alice | 309 | 7 | 0,8 | 0,0 | 0,8 | 0,637 | 0,0 | 0,784 |
| napoleon | 559 | 5 | 0,6 | 0,0 | 0,6 | 0,836 | 0,0 | 0,684 |
| egypt | 733 | 6 | 0,2 | 0,0 | 0,2 | 0,398 | 0,0 | 0,191 |
| ghost | 1094 | 11 | 0,6 | 0,0 | 0,2 | 0,684 | 0,0 | 0,356 |
| garden | 1409 | 7 | 0,6 | 0,0 | 0,4 | 0,478 | 0,0 | 0,311 |
| witch | 648 | 4 | 0,2 | 0,0 | 0,2 | 0,521 | 0,0 | 0,359 |
| recipe | 248 | 8 | 0,8 | 0,0 | 0,8 | 0,811 | 0,0 | 0,657 |

Exemple, « whale » :

| Classement | 3 premiers résultats |
|---|---|
| Fréquence | ✓ Moby-Dick ; ✓ Moby Dick ; ✓ Moby Dick |
| PageRank | ✗ The Old Curiosity Shop ; ✗ Varney the vampyre ; ✗ Dombey and Son |

## Analyse

1. **La fréquence normalisée est le meilleur critère de pertinence** : un livre
   pertinent arrive en tête dans 9 requêtes sur 11 (MRR 0,88). C'est le tri par
   défaut de l'application.
2. **Le PageRank seul ne mesure pas la pertinence** (nDCG 0,02). C'est attendu :
   il ne dépend pas de la requête. Il classe toujours en tête les mêmes livres,
   centraux dans le corpus (romans longs au vocabulaire riche : Dickens, *Varney
   the vampyre*, *The Wandering Jew*), quel que soit le mot cherché. Il répond à
   une autre question : « quels livres sont les plus représentatifs du corpus ? ».
3. **Le produit fréquence × PageRank** reste proche de la fréquence (P@5 0,47) et
   l'améliore sur 3 requêtes (vampire, pirate, alice), mais la dégrade sur les
   termes très répandus (ghost, garden, egypt), où il favorise des livres longs
   et centraux qui citent le mot en passant.
4. **La fusion de rangs** est pénalisée par le PageRank, trop indépendant de la requête.

**Choix retenu** : tri par fréquence normalisée par défaut ; tri par PageRank
proposé en option pour découvrir les ouvrages centraux parmi les résultats,
comme le demande l'énoncé (indice de centralité obligatoire).

**Piste** : utiliser la centralité seulement pour départager des livres de
fréquence voisine, ou un PageRank personnalisé (*personalized PageRank*)
calculé à partir des livres les plus fréquents pour la requête, qui deviendrait
dépendant de la requête.
