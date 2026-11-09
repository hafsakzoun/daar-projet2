# DAAR — Projet 2 : moteur de recherche de livres

Projet réalisé dans le cadre de l'UE DAAR du Master Informatique de Sorbonne Université.

L'objectif est de développer un moteur de recherche de livres avec index inversé, recherche par mots-clés, expressions régulières et recommandations.

## Technologies

- Backend : Python 3.12, FastAPI, SQLAlchemy
- Base de données : PostgreSQL 16
- Frontend : React et Vite
- Conteneurisation : Docker Compose
- Tests : pytest

## Corpus

Le corpus contient 1 700 livres issus de Project Gutenberg, chacun contenant au moins 10 000 mots.

Les fichiers texte sont conservés dans un volume Docker dédié.

Le corpus est téléchargé automatiquement depuis :

https://github.com/ouumm/daar-corpus-public/releases/download/corpus-v1/corpus-1700.tar.gz

Les métadonnées et l'index inversé sont enregistrés dans PostgreSQL.

L'index comprend environ :
- 1 000 281 termes distincts ;
- 15,5 millions de postings ;
- 1 700 livres indexés.

## Installation avec Docker

### Prérequis

- Docker Desktop ou Docker Engine avec Compose
- Git
- Connexion Internet pour télécharger le corpus

Cloner le dépôt, puis se placer à sa racine.

Démarrer l'application :

docker compose up --build

Aucun fichier .env n'est obligatoire pour un lancement local : Docker Compose utilise des valeurs par défaut.

Pour personnaliser la configuration, utiliser le fichier .env.example comme référence avant la première initialisation de PostgreSQL.

### Services

- Frontend : http://localhost:5173
- Backend : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- Santé de l'API : http://localhost:8000/api/v1/health

Au premier lancement, Docker Compose :
1. démarre PostgreSQL ;
2. télécharge et installe le corpus ;
3. construit l'index inversé ;
4. démarre le backend FastAPI ;
5. démarre le frontend React.

Les volumes Docker permettent de conserver les données entre les redémarrages.

Une installation Docker sur des volumes initialement vides a été validée : 1 700 livres importés et indexés, reprise de l'indexation après interruption, backend FastAPI et frontend React accessibles en HTTP 200.

## Recherche

### Recherche simple

GET /api/v1/search?q=alice

La recherche utilise l'index inversé et classe les résultats selon la somme des fréquences des mots recherchés.

Les recherches avec plusieurs mots utilisent une logique OU.

### Recherche par expressions régulières

GET /api/v1/search/regex?q=alice

La regex est appliquée au vocabulaire de l'index inversé et non directement aux phrases complètes des livres.

Les résultats sont classés selon la fréquence cumulée des termes correspondants.

### Catalogue

GET /api/v1/books

GET /api/v1/books/11

Les routes de recherche et de catalogue prennent en charge la pagination.

## Tests et intégration continue

Le projet utilise pytest pour les tests unitaires et d'intégration.

La suite comporte 37 tests validés dans GitLab CI.

Les tests d'intégration utilisent une base PostgreSQL dédiée `daar_test`.
Certaines fixtures réinitialisent les tables : ne pas exécuter la suite
complète directement sur la base principale `daar`.

Les dépendances de test sont définies dans
`backend/requirements-test.txt`.

Le fichier `.gitlab-ci.yml` comporte deux jobs :
- `backend_tests` : tests Python avec PostgreSQL isolé ;
- `frontend_build` : compilation du frontend React.

Les deux jobs ont été validés.

## Organisation du stockage

Deux volumes Docker principaux :

- pgdata : base PostgreSQL, métadonnées et index inversé ;
- corpus : fichiers texte des livres.

Les deux volumes persistent entre les redémarrages ordinaires.

Attention : ne pas utiliser docker compose down -v pour arrêter le projet si les données doivent être conservées.

## Fonctionnalités en développement

- Calcul des similarités entre livres avec Jaccard ;
- Construction du graphe de similarité ;
- PageRank ;
- Recommandations ;
- Intégration complète du frontend React.

## Livraison

Le dépôt contient le code source et les scripts permettant de récupérer automatiquement le corpus externe.

Le corpus volumineux et les fichiers PostgreSQL générés ne sont pas inclus directement dans l'archive du code source.

La reproductibilité Docker et la CI ont été vérifiées. L'intégration des fonctionnalités restantes, les accès Git du professeur et la livraison finale restent à vérifier.


## Résultats de validation

Les vérifications du corpus, de l'index inversé, des recherches,
des empreintes SHA-256 et des performances sont documentées dans
[docs/VALIDATION_P1.md](docs/VALIDATION_P1.md).
