# DAAR 2 — Validation technique P1

Date : 9 novembre 2026

## 1. Environnement

- Backend : FastAPI
- Frontend : React et Vite
- Base : PostgreSQL 16
- Conteneurisation : Docker Compose
- Environnement de test : daar2_rendu_verif
- Corpus : 1 700 livres Project Gutenberg

L'installation a été réalisée sur des volumes Docker initialement vides.
L'indexation a été interrompue puis reprise avec succès.

Les services PostgreSQL, corpus-init, index-init, backend et frontend
ont atteint leurs états attendus.

FastAPI et React ont répondu avec le code HTTP 200.
Le catalogue React affichait les livres issus de PostgreSQL.

## 2. Vérification du corpus

Résultats SQL :

| Indicateur | Résultat |
|---|---:|
| Livres enregistrés | 1 700 |
| Livres indexés | 1 700 |
| Minimum de mots | 10 183 |
| Moyenne de mots | 142 068 |
| Maximum de mots | 4 542 910 |
| Livres sous 10 000 mots | 0 |
| Chemins distincts | 1 700 |
| Champs source_url ou text_path vides | 0 |

Volume Docker du corpus : environ 1,4 Go.

## 3. Cohérence du manifeste

Le manifeste est accessible dans le conteneur à
/app/data/books.csv.

Résultats du contrôle :

| Vérification | Résultat |
|---|---|
| Livres du manifeste | 1 700 |
| Livres PostgreSQL | 1 700 |
| Identifiants identiques | True |
| Nombres de mots identiques | True |
| Fichiers manquants | 0 |
| Fichiers vides | 0 |
| Empreintes SHA-256 incorrectes | 0 |
| Doublons exacts SHA-256 | 0 |

Les empreintes des fichiers ont été recalculées et comparées
à celles du manifeste.

Limites :
- Les mots n'ont pas été recomptés indépendamment des métadonnées.
- Les doublons presque identiques ne sont pas détectés par SHA-256.
- La méthode de nettoyage reste à documenter.

## 4. Recherche simple — DAAR-011

Requête : alice

Total : 296 livres.

| ID | Score API | Fréquence PostgreSQL |
|---|---:|---:|
| 12 | 468 | 468 |
| 28885 | 406 | 406 |
| 11 | 399 | 399 |

Les scores vérifiés correspondent aux fréquences de l'index.

Autres vérifications :

- limit=3 : trois résultats retournés.
- offset=0 et offset=3 : deux pages sans doublons.
- Les deux pages indiquent le même total de 296.
- Requête sans correspondance : HTTP 200, total=0, results=[].

## 5. Recherche regex — DAAR-012

Expression : alice|rabbit

Total : 617 livres.

| ID | alice | rabbit | Score API |
|---|---:|---:|---:|
| 26429 | 0 | 1468 | 1468 |
| 12 | 468 | 0 | 468 |
| 28885 | 406 | 53 | 459 |

Les scores correspondent aux sommes des fréquences SQL.

Expression invalide "[" :
HTTP 400, message "Expression régulière invalide."

## 6. Performances — DAAR-020

Mesures effectuées via HTTP en local.

Six appels par recherche, premier appel écarté.
Statistiques calculées sur cinq appels.

| Indicateur | Simple | Regex |
|---|---:|---:|
| Moyenne | 29,00 ms | 314,23 ms |
| Médiane | 25,48 ms | 312,19 ms |
| Minimum | 23,53 ms | 305,95 ms |
| Maximum | 43,70 ms | 324,27 ms |

La recherche regex est environ 10,8 fois plus lente
pour les requêtes testées.

Ces mesures comprennent le transport HTTP local et la lecture
des réponses JSON. Elles ne mesurent pas uniquement PostgreSQL.

Une campagne plus large sera nécessaire pour une évaluation
complète des performances.

## 7. Tests et intégration continue

- 37 tests Python réussis.
- Job backend_tests validé.
- Job frontend_build validé.
- Dernier commit de documentation vérifié : de75c51.
- Push GitHub et GitLab effectué.
- Pipeline GitLab associé : #3045984898, Passed.

## 8. Éléments restant à finaliser

- DAAR-005 : reprise d'un téléchargement d'archive interrompu.
- DAAR-006 : documentation du nettoyage et du comptage.
- DAAR-011/012 : compléter les cas limites automatisés si nécessaire.
- DAAR-017 : intégration des scores PageRank de P2.
- DAAR-020 : mesures complémentaires.
- DAAR-022 : rédaction des sections du rapport.
- Intégration des contributions et démonstration finale.

Le corpus déjà installé est vérifié avant un nouveau téléchargement.
La reprise de l'indexation a été validée.
La reprise partielle du téléchargement HTTP n'est pas implémentée.

## 9. Validation indépendante du 16 novembre 2026

Contrôle effectué sur les fichiers réels du volume Docker `corpus`,
et non uniquement sur les métadonnées PostgreSQL.

Méthode :
- Lecture des 1 700 identifiants du manifeste `books.csv`.
- Vérification de l'existence de chaque fichier texte.
- Recalcul du SHA-256 à partir des octets du fichier.
- Recalcul du nombre de mots par découpage sur les espaces (`split()`).
- Comparaison avec le manifeste et contrôle du minimum de 10 000 mots.

| Vérification | Résultat |
|---|---:|
| Livres attendus | 1 700 |
| Fichiers vérifiés | 1 700 |
| Fichiers manquants | 0 |
| SHA-256 incorrects | 0 |
| Livres sous 10 000 mots | 0 |
| Écarts de comptage | 0 |

La limitation mentionnée dans la section 3 concernant le recomptage
indépendant des mots est donc levée pour ce corpus installé.

Contrôle complémentaire de l'index PostgreSQL :

| Indicateur | Résultat |
|---|---:|
| Livres en base | 1 700 |
| Livres ayant au moins un posting | 1 700 |
| Termes distincts | 1 000 281 |
| Associations livre-terme | 15 546 923 |

Tests backend exécutés avec la base isolée `daar_test` :
37 réussis sur 37, en 0,73 seconde.

Ces contrôles ne prouvent pas encore la reproductibilité complète
sur une machine neuve ni l'absence d'index partiellement corrompu.

## Validation Docker sur volumes vierges — 16 novembre 2026

Installation indépendante avec le projet Compose `daar-validation`.

Résultats :
- PostgreSQL initialisé sur un volume neuf.
- Archive Gutenberg téléchargée et vérifiée.
- 1700 livres copiés, aucun fichier manquant ou incorrect.
- 1700 livres ajoutés dans PostgreSQL.
- Index inversé entièrement reconstruit : index-init Exited (0).
- 1 000 281 termes distincts.
- 15 546 923 postings.
- 1700 livres présents dans les postings.
- Backend indépendant accessible sur le port 8001.
- GET /api/v1/health : HTTP 200.
- Recherche simple "alice" : 296 résultats.
- Recherche Regex "alice|rabbit" : 617 résultats.

Conclusion : installation et indexation reproductibles sur volumes vierges.
La démonstration depuis plusieurs appareils reste à confirmer.

## Validation Docker complete depuis zero — 16 novembre 2026

Une seconde installation Docker independante a ete creee
avec un clone Git et deux volumes neufs :
- daar-v2-fresh_pgdata
- daar-v2-fresh_corpus

Resultats observes :
- corpus-init : termine avec code 0
- index-init : termine avec code 0
- PostgreSQL : healthy
- Backend FastAPI : healthy
- Frontend React : HTTP 200
- Livres installes : 1700
- Livres indexes V2 : 1700
- Postings V2 : 10753306
- Postings V1 : 0
- GET /api/v1/search?q=alice : HTTP 200, 309 livres
- GET /api/v1/search/regex?q=alice%7Crabbit :
  HTTP 200, 593 livres

Conclusion :
L'installation Docker complete depuis des volumes vierges
fonctionne. Le corpus est installe, la V2 est construite
sans index V1 et les recherches API fonctionnent.
