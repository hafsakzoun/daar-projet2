# DAAR — Projet 2 : moteur de recherche de livres

Projet de l'UE DAAR du Master Informatique de Sorbonne Université.

Objectif : développer un moteur de recherche de livres avec
index inversé, recherche par mots-clés, expressions régulières,
classement et recommandations.

## Technologies

- Python 3.12, FastAPI, SQLAlchemy
- PostgreSQL 16
- React et Vite
- Docker Compose
- pytest

## Corpus Gutenberg

Le corpus contient 1 700 livres de Project Gutenberg.
Chaque livre contient au moins 10 000 mots.

Validation réalisée :
- 1 700 fichiers présents ;
- 1 700 empreintes SHA-256 conformes ;
- 1 700 livres au-dessus de 10 000 mots ;
- 1 700 livres indexés.

Ancien index V1 (conserve pour comparaison) :
- 1 000 281 termes distincts ;
- 15 546 923 associations livre-terme.

Index V2 optimise :
- 973 252 termes distincts ;
- 10 753 306 associations livre-terme ;
- recherche avec normalisation linguistique et stemming.

## Démarrage avec Docker

Depuis la racine du dépôt, avec Docker Compose installé :

```bash
docker compose up --build
```

Ouvrir l’interface sur <http://localhost:5173>. La documentation FastAPI est disponible sur <http://127.0.0.1:8000/docs>. Le démarrage utilise des valeurs par défaut et fonctionne sans fichier `.env`. Pour personnaliser les origines CORS des appels directs à FastAPI, utiliser `.env.example` comme modèle.

## Prérequis pour le lancement sans Docker

L'archive externe du corpus est disponible à l'adresse :

https://github.com/ouumm/daar-corpus-public/releases/download/corpus-v1/corpus-1700.tar.gz

Le téléchargement est reprenable par requêtes HTTP Range lorsque
le serveur le permet. L'archive est contrôlée par SHA-256.

## Installation Docker

Prérequis : Docker Desktop ou Docker Engine avec Docker Compose.

Cloner le dépôt et se placer à sa racine.

Pour une nouvelle installation, préparer les variables
d'environnement :

    cp .env.example .env

Modifier POSTGRES_PASSWORD dans le fichier .env avant de lancer
PostgreSQL. Ne pas publier ce fichier dans Git.

Démarrer les services :

    docker compose up -d --build

Vérifier leur état :

    docker compose ps -a

Les services db, backend et frontend disposent de healthchecks.
Les services corpus-init et index-init sont des tâches
d'initialisation : leur état normal après succès est Exited (0).

Au premier lancement :
1. PostgreSQL démarre.
2. Le corpus est téléchargé et vérifié.
3. L'index inversé est construit.
4. Le backend démarre.
5. Le frontend démarre.

Le premier téléchargement et la première indexation peuvent être
longs et nécessitent suffisamment d'espace disque.

## Accès local

- Frontend : http://localhost:5173
- API : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- Santé API : http://localhost:8000/api/v1/health

Par défaut, les ports applicatifs sont publiés uniquement sur
127.0.0.1. La démonstration sur plusieurs machines nécessitera
une configuration réseau supplémentaire.

Le frontend actuel utilise le serveur de développement Vite.
Un déploiement de production du frontend reste à préparer.

## Arrêt et conservation des données

Arrêter les conteneurs sans supprimer les volumes :

    docker compose down

Redémarrer les services :

    docker compose up -d

Deux volumes principaux conservent les données :
- pgdata : PostgreSQL et index inversé ;
- corpus : fichiers texte Gutenberg.

ATTENTION : ne pas utiliser docker compose down -v si les données
doivent être conservées.

## Recherche explicite

Recherche par mots-clés :

    GET /api/v1/search?q=alice

Le classement repose sur les fréquences cumulées des termes.
Les requêtes comportant plusieurs mots utilisent une logique OU.

Recherche par expression régulière :

    GET /api/v1/search/regex?q=alice%7Crabbit

Les expressions régulières s'appliquent aux termes de l'index
inversé, pas directement aux phrases complètes des livres.

Catalogue :

React envoie ses requêtes à `/api/v1`. Vite les transmet à FastAPI via le réseau Docker quand Compose est utilisé, et vers `http://127.0.0.1:8000` lors d’un lancement local sans Docker.

Les ports Compose sont accessibles depuis la machine qui exécute Docker. Pour une démonstration depuis un autre appareil, il faudra rendre le port du frontend accessible sur le réseau local.

    GET /api/v1/books
    GET /api/v1/books/11

Les routes de recherche et de catalogue prennent en charge
la pagination.

## Tests

41 tests backend ont réussi localement.

Utiliser uniquement la base de test daar_test pour la suite
d'intégration : certaines fixtures réinitialisent les tables.

Lorsque la base daar_test existe :

    docker compose run --rm -T --no-deps -e DB_NAME=daar_test -e DAAR_TEST_DB=1 backend python -m pytest -q

Ne jamais lancer cette suite sur la base principale daar.

Les dépendances de développement sont déclarées dans
backend/requirements-dev.txt.

La CI utilise backend/requirements-test.txt.
Le fichier .gitlab-ci.yml comporte les jobs backend_tests
et frontend_build.

Les 41 tests locaux ne constituent pas à eux seuls une nouvelle
validation de la CI après les derniers commits.

## Performances

Les recherches ont été mesurées sur 1 700 livres,
avec 20 répétitions pour chacune des six requêtes.

Recherche simple : 3,67 à 11,23 ms en moyenne.
Recherche Regex : 313,02 à 328,34 ms en moyenne.

Ces mesures concernent les requêtes SQL, sans temps HTTP
ni rendu React.

Fichiers de résultats :
- docs/benchmark_p1_full.csv
- docs/benchmark_p1_simple.svg
- docs/benchmark_p1_regex.svg
- docs/PERFORMANCES_P1.md

Les comparaisons sur plusieurs tailles réelles de bases
restent à compléter.

## Documentation et validation

Voir :
- docs/VALIDATION_P1.md
- docs/PERFORMANCES_P1.md

## Fonctionnalités restant à intégrer

- Calcul de similarité Jaccard
- Graphe de similarité entre livres
- PageRank et classement implicite
- Recommandations de livres
- Intégration complète du frontend
- Démonstration sur plusieurs machines

## Livraison

Le dépôt contient le code source et les scripts nécessaires
pour récupérer le corpus externe.

Le corpus volumineux et les volumes PostgreSQL ne sont pas
inclus dans l'archive de livraison.

Une installation sur volumes vierges avait été validée avant
les derniers changements. Une nouvelle vérification complète
de reproductibilité reste à effectuer.
