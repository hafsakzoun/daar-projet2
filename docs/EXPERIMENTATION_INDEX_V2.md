# Experimentation : index inverse V1 / V2

Date : 16 novembre 2026

## Objectif

Comparer l'indexation initiale avec une nouvelle normalisation
integrant les stopwords, le stemming multilingue et Unicode.

## Methode

- Echantillon regulier de 200 livres sur 1700.
- 195 livres anglais et 5 livres francais.
- Memes textes analyses pour les deux versions.
- Comptage des termes et des couples (livre, terme) en memoire.
- Aucune modification de la base PostgreSQL principale.

## Resultats

| Metrique | V1 | V2 |
|---|---:|---:|
| Termes distincts | 241739 | 203758 |
| Postings | 1870565 | 1283434 |
| Temps de traitement Python | 12.69 s | 34.36 s |

Reduction des postings : 31.39 %.
Reduction des termes distincts : environ 15.7 %.

## Interpretation

La V2 produit un index potentiellement plus compact.

En contrepartie, la preparation des termes en Python
est environ 2.7 fois plus lente sur cet echantillon.

Ces mesures n'incluent pas les insertions SQL, la taille
reelle des tables PostgreSQL ni le temps des recherches.

Le comportement des recherches simple et Regex, ainsi
que la compatibilite avec Jaccard, restent a valider.

Le stemming de l'allemand et du vieil anglais n'a pas
ete evalue dans cet echantillon.

## Conclusion

La V2 est prometteuse. Une validation fonctionnelle et
une migration controlee sont necessaires avant son adoption.

## Validation sur les 1700 livres

La V2 a ete construite integralement dans PostgreSQL.

| Metrique | V1 | V2 |
|---|---:|---:|
| Livres | 1700 | 1700 |
| Termes | 1000281 | 973252 |
| Postings | 15546923 | 10753306 |
| Taille postings (avec index SQL) | 1216 Mo | 873 Mo |
| Taille termes (avec index SQL) | 98 Mo | 103 Mo |
| Taille totale de ces tables | 1314 Mo | 976 Mo |

Reduction des postings : 30,83 %.
Reduction du stockage de ces tables : 25,72 %.

La V2 utilise une tokenisation Unicode, des stopwords
multilingues et le stemming Snowball.

Le score de recherche est normalise par la longueur du
document : occurrences pour un million de mots.

Les recherches simples et Regex fonctionnent sur les
1700 livres. La recherche Regex porte sur les racines,
et non directement sur les formes originales des mots.

Les 50 tests Python passent. La recherche HTTP a ete
validee sur la V2.

La V1 reste disponible pour les comparaisons et pour
les composants qui n'ont pas encore migre vers V2.
