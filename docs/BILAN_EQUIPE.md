# Bilan des ressources : répartition du travail

Établi à partir de l'historique Git (toutes branches, hors commits de fusion),
du 2 au 18 novembre 2026. L'énoncé demande, dans la partie introductive de la
présentation, un « tableau résumant le nombre de jour-hommes par tâche
principale du projet » : la dernière colonne est à compléter par l'équipe.

| | Oum | Hafsa |
|---|---:|---:|
| Commits | 47 | 17 |
| Jours avec au moins un commit | 5 | 5 |
| Période | 3 → 17 nov. | 2 → 16 nov. |

## Par tâche

« Commits » = nombre de commits ayant modifié au moins un fichier de la tâche.

| Tâche | Oum | Hafsa | Contenu principal | Jours-homme |
|---|---:|---:|---|---:|
| Initialisation du projet (FastAPI, React, Docker) | 0 | ✔ | squelette du dépôt, première API, premier frontend (Hafsa) | |
| Corpus Gutenberg (1 700 livres, téléchargement, vérification SHA-256) | 5 | 0 | `install_corpus`, `auto_install`, archive publiée (Oum) | |
| Index inversé (normalisation, racines, mots vides) | 9 | 0 | index V1 puis V2 sur PostgreSQL (Oum) | |
| Recherche par mot-clé et API | 12 | 4 | structure de l'API (Hafsa) ; recherche V2, pagination, lecture du texte (Oum) | |
| RegEx (automate, recherche) | 8 | 2 | automate Thompson + DFA, filtre par préfixe (Oum) | |
| Graphe de Jaccard et PageRank | 5 | 2 | algorithmes `jaccard.py` et `pagerank.py` (Hafsa) ; vocabulaire discriminant, stockage en base, tri SQL (Oum) | |
| Comptes, favoris, historique | 4 | 4 | authentification, première version favoris / historique (Hafsa) ; stockage en base, routes `/auth/me` (Oum) | |
| Interface React | 7 | 10 | première interface, recherche, fenêtre des recommandations (Hafsa) ; refonte visuelle, pages, lecture (Oum) | |
| Docker, Compose, AWS, HTTPS, CI/CD | 20 | 4 | Docker initial (Hafsa) ; chaîne d'initialisation, nginx, déploiement AWS + HTTPS, pipeline GitLab (Oum) | |
| Tests automatisés | 15 | 3 | tests du graphe (Hafsa) ; tests unitaires et d'intégration (Oum) | |
| Benchmarks, pertinence, documentation | 20 | 3 | `PERFORMANCES.md`, `PERTINENCE.md`, README (Oum) | |
| Rapport | | | | |
| Vidéo de présentation | | | | |

Limites : un nombre de commits ne mesure pas le temps passé, et une partie du
code initial a été réécrite depuis. Le tableau sert de base de discussion pour
remplir la colonne des jours-homme.
