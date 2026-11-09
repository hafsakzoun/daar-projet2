# DAAR — Projet 2 : moteur de recherche de livres

Application web permettant de rechercher des livres par mot-clé ou expression régulière, de classer les résultats et de proposer des ouvrages similaires.

Projet réalisé dans le cadre de l’UE DAAR du Master Informatique de Sorbonne Université.

## État du projet

Le projet est en cours de développement. Le démarrage du serveur FastAPI a été vérifié localement. Le dossier frontend React est créé ; la connexion entre React et l’API reste à vérifier.

Les fonctionnalités de recherche, d’indexation, de classement et de recommandation décrites ci-dessous constituent les objectifs du projet ; leur présence dans ce README ne signifie pas qu’elles sont déjà implémentées.

## Objectifs fonctionnels

- Constituer une bibliothèque d’au moins **1 664 livres**, contenant chacun au moins **10 000 mots**.
- Rechercher les livres par mot-clé à partir d’un index inversé.
- Effectuer une recherche avancée par expression régulière dans le vocabulaire de l’index.
- Classer les résultats, notamment selon une mesure de centralité du graphe de Jaccard.
- Recommander des livres similaires à partir du voisinage des meilleurs résultats.
- Proposer une interface adaptée aux ordinateurs et aux téléphones.
- Évaluer l’exactitude, la pertinence et les performances du moteur.

Le choix prévu pour la centralité est PageRank. La définition de Jaccard et les conventions de construction du graphe devront être alignées sur le cours.

## Technologies

| Technologie | Rôle | État |
| --- | --- | --- |
| Python | Traitement des textes et algorithmes | Utilisé |
| FastAPI / Uvicorn | API et serveur de développement | Installés |
| React | Interface utilisateur | Projet créé |
| Vite | Développement et compilation du frontend | Configuré dans le frontend |
| SQLite | Stockage des métadonnées et données structurées | Prévu |
| Git | Suivi des modifications | Initialisé |

Les textes des livres seront conservés dans des fichiers. L’organisation du stockage de l’index et du graphe sera précisée pendant le développement.

## Organisation actuelle

| Chemin | Description |
| --- | --- |
| `backend/main.py` | Point d’entrée de l’application FastAPI |
| `backend/requirements.txt` | Dépendances Python |
| `backend/.venv/` | Environnement Python local, à exclure de Git |
| `frontend/src/` | Code de l’interface React |
| `frontend/public/` | Ressources statiques |
| `frontend/package.json` | Dépendances et commandes du frontend |
| `frontend/package-lock.json` | Versions des dépendances npm |
| `frontend/vite.config.js` | Configuration Vite |
| `README.md` | Documentation générale du projet |

## Démarrage avec Docker

Depuis la racine du dépôt, avec Docker Compose installé :

```bash
docker compose up --build
```

Ouvrir l’interface sur <http://localhost:5173>. La documentation FastAPI est disponible sur <http://127.0.0.1:8000/docs>. Le démarrage utilise des valeurs par défaut et fonctionne sans fichier `.env`. Pour personnaliser les origines CORS des appels directs à FastAPI, utiliser `.env.example` comme modèle.

## Prérequis pour le lancement sans Docker

Configuration utilisée lors de l’initialisation :

- Python **3.12.7** ;
- Node.js **22.13.0** ;
- npm **10.9.2** ;
- Git **2.47.1**.

Ces versions décrivent l’environnement initial, pas les versions minimales garanties.

Vérifier les outils :

```bash
python3 --version
node --version
npm --version
git --version
```

Le chemin du projet ne doit pas contenir de caractère `:` pour permettre la création de l’environnement virtuel Python sur macOS/Linux.

## Installation

Les commandes suivantes sont prévues pour macOS/Linux et s’exécutent depuis la racine du projet.

### Backend

Si un environnement Conda est actif, le quitter avant de créer l’environnement du projet :

```bash
conda deactivate
```

Créer un environnement Python, uniquement s’il n’existe pas encore :

```bash
cd backend
python3 -m venv .venv
```

L’activer et installer les dépendances :

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

L’environnement `.venv` se crée localement sur chaque machine ; il ne doit pas être partagé dans Git.

### Frontend

Depuis la racine du projet, dans un autre terminal :

```bash
cd frontend
npm ci
```

`npm ci` installe les dépendances à partir du fichier `package-lock.json` fourni. Le dossier `node_modules` ne doit pas être partagé dans Git.

## Lancement en développement

Les deux serveurs doivent fonctionner simultanément dans deux terminaux distincts.

### Terminal 1 — FastAPI

Depuis la racine du projet :

```bash
cd backend
source .venv/bin/activate
python -m uvicorn main:app --reload
```

- API : <http://127.0.0.1:8000>
- Documentation interactive : <http://127.0.0.1:8000/docs>

L’absence de route `/` peut produire une réponse 404 sur la racine de l’API ; utiliser `/docs` pour vérifier le démarrage.

### Terminal 2 — React

Depuis la racine du projet :

```bash
cd frontend
npm run dev -- --port 5173 --strictPort
```

- Interface : <http://localhost:5173>

Laisser les deux terminaux ouverts. `Ctrl + C` arrête le serveur du terminal concerné.

### Communication entre React et FastAPI

React envoie ses requêtes à `/api/v1`. Vite les transmet à FastAPI via le réseau Docker quand Compose est utilisé, et vers `http://127.0.0.1:8000` lors d’un lancement local sans Docker.

Les ports Compose sont accessibles depuis la machine qui exécute Docker. Pour une démonstration depuis un autre appareil, il faudra rendre le port du frontend accessible sur le réseau local.

## Corpus et traitement prévus

Source envisagée : [Project Gutenberg](https://www.gutenberg.org/).

Le pipeline de préparation devra :

1. Enregistrer les identifiants, métadonnées et sources des livres.
2. Récupérer les textes selon les modalités autorisées par la source.
3. Nettoyer les en-têtes et pieds de page.
4. Vérifier le seuil de 10 000 mots après nettoyage.
5. Détecter les doublons et conserver au moins 1 664 livres conformes.
6. Construire l’index inversé et les données du graphe.
7. Pré-calculer les scores de centralité.

Les règles de normalisation et de comptage seront documentées pour rendre les résultats reproductibles. Le corpus n’est pas encore fourni par ce dépôt ; les scripts et instructions de récupération seront ajoutés pendant le développement.

## Algorithmes prévus

- **Index inversé** : associer chaque terme aux livres correspondants et aux fréquences d’occurrence.
- **Recherche simple** : consulter les entrées de l’index correspondant au terme recherché.
- **Recherche regex** : sélectionner les termes de l’index correspondant à l’expression, puis agréger les documents associés.
- **Jaccard** : mesurer la proximité entre les représentations des livres et construire le graphe.
- **PageRank** : calculer un score de centralité utilisé pour ordonner les résultats.
- **Recommandation** : sélectionner des voisins similaires en évitant les doublons dans les résultats affichés.

Les calculs de préparation du corpus seront séparés du traitement des requêtes pour ne pas reconstruire l’index et le graphe à chaque recherche.

## Validation prévue

Aucune campagne complète de tests n’a encore été documentée.

Les vérifications porteront sur :

- la concordance entre recherche indexée et lecture directe des textes ;
- les expressions régulières valides, invalides et sans résultat ;
- les calculs de Jaccard et PageRank sur de petits exemples vérifiables ;
- les temps de préparation et de réponse sur plusieurs tailles de corpus ;
- les mesures répétées et la consommation mémoire ;
- la pertinence des résultats sur un ensemble de requêtes défini ;
- l’accès à l’application depuis plusieurs appareils.

Les commandes de tests et les résultats seront ajoutés lorsqu’ils seront disponibles.

## Problèmes fréquents

| Problème | Vérification |
| --- | --- |
| `ERR_CONNECTION_REFUSED` sur le port 8000 | Vérifier qu’Uvicorn fonctionne toujours et qu’aucune erreur n’est affichée dans son terminal |
| `No module named uvicorn` | Activer `.venv` et installer `requirements.txt` |
| Erreur lors de l’import de `main` | Exécuter la commande depuis `backend` et vérifier que `main.py` définit `app` |
| Port déjà utilisé | Arrêter l’ancien serveur ou adapter le port et la configuration frontend |
| Erreur CORS dans le navigateur | Vérifier l’origine exacte autorisée côté FastAPI |
| Refus de créer `.venv` avec un séparateur `:` | Déplacer le projet dans un chemin sans `:` |

## Livraison

Le rendu devra inclure le code source commenté, les instructions reproductibles, un rapport et les éléments de démonstration requis par le sujet.

Le corpus et les fichiers générés devront être gérés en tenant compte de la limite d’environ 30 Mo pour l’archive finale. Les modalités de mise à disposition des données au correcteur restent à préciser.
