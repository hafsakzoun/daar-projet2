# Lisière : moteur de recherche de livres

Projet 2 de l'UE DAAR (Master Informatique, Sorbonne Université).

Lisière cherche dans 1 700 livres du Projet Gutenberg par mot-clé ou par
expression régulière, classe les résultats par fréquence ou par PageRank, et
suggère des livres similaires grâce à un graphe de Jaccard.

**Démonstration : [https://13.61.8.67/](https://13.61.8.67/)**

## Lancer le projet

Prérequis : Docker avec Docker Compose, et une connexion Internet au premier
lancement.

```bash
docker compose up -d --build
```

Aucun `.env` n'est nécessaire. Le premier lancement télécharge et vérifie le
corpus, construit l'index puis le graphe (environ 30 minutes, 2,5 Go). Les
lancements suivants réutilisent tout et prennent quelques secondes.

| | Adresse |
|---|---|
| Interface | [http://localhost:5173](http://localhost:5173) |
| Documentation de l'API | [http://localhost:8000/docs](http://localhost:8000/docs) |

Suivre l'installation : `docker compose ps -a` (les trois tâches `*-init`
terminent avec le code 0, les autres services passent `healthy`).

Démonstration sur plusieurs appareils du même réseau :
`FRONTEND_BIND=0.0.0.0 docker compose up -d`, puis `http://<IP>:5173`.

Tests unitaires :

```bash
docker compose run --rm -T --no-deps backend python -m pytest tests/ -v
```

## Fonctionnalités

- Recherche par mot-clé (racines, mots vides retirés) et par RegEx (automate
  de Thompson déterminisé à la volée, sur les racines de l'index).
- Classement par fréquence normalisée ou par centralité PageRank.
- Livres similaires : voisins dans le graphe de Jaccard.
- Lecture du texte intégral.
- Comptes avec confirmation par e-mail, mot de passe oublié, favoris et historique.

## Architecture

React servi par nginx, API FastAPI (Python 3.12), PostgreSQL 16, le tout lancé
par Docker Compose. Les mots de passe passent par des secrets Docker
([secrets/README.md](secrets/README.md)).

| Donnée | Stockage |
|---|---|
| Textes des livres | volume Docker `corpus` |
| Index inversé | PostgreSQL : `terms_v2`, `postings_v2` |
| Graphe et PageRank | PostgreSQL : `book_similarities`, `book_scores` |
| Comptes, favoris, historique | PostgreSQL : `users`, `user_favorites`, `search_history` |

## Documentation

| Sujet | Fichier |
|---|---|
| Tests et validation | [docs/VALIDATION.md](docs/VALIDATION.md) |
| Performances | [docs/PERFORMANCES_V2.md](docs/PERFORMANCES_V2.md) |
| Pertinence du classement | [docs/PERTINENCE.md](docs/PERTINENCE.md) |
| Sécurité | [docs/SECURITE.md](docs/SECURITE.md) |
| CI/CD GitLab | [docs/CI_CD.md](docs/CI_CD.md) |
| Kubernetes | [docs/KUBERNETES.md](docs/KUBERNETES.md) |
| Déploiement AWS et HTTPS | [docs/AWS.md](docs/AWS.md), [docs/HTTPS.md](docs/HTTPS.md) |
| Répartition du travail | [docs/BILAN_EQUIPE.md](docs/BILAN_EQUIPE.md) |

## Archive de rendu

```bash
scripts/make_archive.sh --noms NOM1-NOM2 --rapport rapport.pdf --video video.mp4
```

L'archive exclut `.env`, les secrets et les données générées, et refuse de
dépasser 30 Mo.
