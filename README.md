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

Ancien index V1 (retiré du code, chiffres gardés pour comparaison) :
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

Le frontend est compilé par Vite puis servi par nginx, qui relaie
`/api` vers FastAPI sur le réseau Docker `app_net`.

Par défaut, l'application n'écoute que sur 127.0.0.1. Pour la
démonstration sur plusieurs appareils (même Wi-Fi), l'ouvrir au réseau :

```bash
FRONTEND_BIND=0.0.0.0 docker compose up -d
```

puis ouvrir `http://<IP-du-serveur>:5173` sur les autres machines.

Après une modification du code :

```bash
docker compose up -d --build backend frontend
```

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

React envoie ses requêtes à `/api/v1`. Avec Compose, nginx les transmet à FastAPI ; avec `npm run dev` (sans Docker), le serveur Vite les transmet à `http://127.0.0.1:8000`.

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

La CI utilise backend/requirements-dev.txt.
Le fichier .gitlab-ci.yml comporte les jobs backend_tests
et frontend_build.

Les 41 tests locaux ne constituent pas à eux seuls une nouvelle
validation de la CI après les derniers commits.

## Performances

Voir `docs/PERFORMANCES_V2.md` (mesures V2, graphiques SVG) :

- mot-clé : 2 ms (100 livres) à 19 ms (1 700 livres), croissance linéaire ;
- regex par automate : 25 à 32 ms avec préfixe littéral (1,1 s avant
  optimisation), ~560 ms sans préfixe ; mêmes résultats que PostgreSQL ;
- suggestions : 10 ms (1,3 s quand le graphe était un fichier JSON) ;
- test de charge : ~270 requêtes/s, aucune erreur jusqu'à 16 clients.

Relancer les mesures :

```bash
docker compose exec backend python -m scripts.benchmark_v2 --out /tmp/bench
docker cp "$(docker compose ps -q backend)":/tmp/bench/. docs/benchmarks_v2/
python3 scripts/plot_benchmark_v2.py docs/benchmarks_v2
```

Les mesures de la V1 restent dans `docs/PERFORMANCES_P1.md` pour comparaison.

## Architecture des données

| Donnée | Stockage |
|---|---|
| Texte des livres | fichiers `.txt`, volume Docker `corpus` |
| Index inversé | PostgreSQL : `terms_v2` (racines), `postings_v2` (livre, racine, fréquence) |
| Graphe de Jaccard | PostgreSQL : `book_similarities` (arêtes pondérées) |
| Centralité PageRank | PostgreSQL : `book_scores` |
| Comptes, favoris, historique | PostgreSQL : `users`, `user_favorites`, `search_history` |

Chaîne d'initialisation (une seule commande, `docker compose up`) :
`corpus-init` (télécharge et vérifie les 1 700 livres) → `index-init`
(index inversé) → `graph-init` (Jaccard + PageRank, ~3 min) → `backend` → `frontend`.
Chaque étape est sautée si son résultat existe déjà.

Choix d'indexation :

- découpage en mots Unicode, minuscules, mots vides retirés, racinisation
  Snowball (anglais, français, allemand) : `whales` et `whale` partagent une racine ;
- le graphe de Jaccard compare le vocabulaire discriminant de chaque livre
  (racines présentes dans 2 livres au moins et 50 % du corpus au plus), seuil 0,20,
  plus les 5 plus proches voisins de chaque livre ;
- la regex est exécutée par notre automate (Thompson + déterminisation à la
  volée) sur les racines de l'index, gardées triées en mémoire.

## Déploiement sur un serveur (AWS)

```bash
cp .env.example .env   # puis définir POSTGRES_PASSWORD
docker compose -f compose.yaml -f compose.aws.yaml up -d
```

L'application est alors servie sur le port 80. Le premier lancement indexe les
livres et calcule le graphe : une instance d'au moins 2 Go de mémoire est
conseillée (besoin non mesuré précisément).

## Fonctionnalités

- Recherche par mot-clé et par RegEx (automate sur les racines de l'index)
- Classement par fréquence normalisée ou par PageRank
- Suggestions : voisins Jaccard des deux meilleurs résultats
- Lecture du texte complet d'un livre
- Comptes utilisateurs ; favoris et historique stockés dans PostgreSQL
  (retrouvés sur n'importe quelle machine)

## Livraison

Le dépôt contient le code source et les scripts nécessaires
pour récupérer le corpus externe.

Le corpus volumineux et les volumes PostgreSQL ne sont pas
inclus dans l'archive de livraison.

Créer l'archive de rendu (≤ 30 Mo, sans `.env` ni données générées) :

```bash
scripts/make_archive.sh --noms NOM1-NOM2-NOM3 --rapport rapport.pdf --video video.mp4
```
