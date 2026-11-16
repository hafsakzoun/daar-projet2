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
