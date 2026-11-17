# DAAR — Projet 2 : Lisière, moteur de recherche de livres

Projet de l'UE DAAR du Master Informatique de Sorbonne Université.

Lisière permet de rechercher dans un corpus de livres par mots-clés ou par
expressions régulières, de classer les résultats et de découvrir des livres
similaires à partir d'un graphe de Jaccard.

**Démonstration AWS : [http://13.61.8.67/](http://13.61.8.67/).**
Le déploiement actuel utilise HTTP ; HTTPS n'est pas configuré. Pour les essais
des comptes, utiliser des identifiants fictifs et un mot de passe réservé à la
démonstration : HTTP ne chiffre pas les échanges. L'adresse publique peut
changer après un arrêt et un redémarrage de l'instance EC2.

## Fonctionnalités

- Recherche par mots-clés avec normalisation linguistique et racinisation.
- Recherche par RegEx avec un automate de Thompson, déterminisé à la volée.
- Classement par fréquence normalisée ou par centralité PageRank.
- Pagination du catalogue et des résultats.
- Recommandations issues du graphe de similarité de Jaccard.
- Lecture du texte intégral, paginé en caractères.
- Comptes utilisateurs, favoris et historique conservés dans PostgreSQL.

## Technologies

- Python 3.12, FastAPI, SQLAlchemy et pytest.
- PostgreSQL 16.
- React et Vite ; nginx sert le frontend compilé et relaie les appels à l'API.
- Docker Compose pour l'installation et l'exécution.

## Démarrage local

Prérequis : Docker Desktop ou Docker Engine avec une version récente de Docker
Compose. Une connexion Internet est nécessaire pour télécharger les images,
les dépendances et le corpus lors de la première installation.

Depuis la racine du dépôt :

```bash
docker compose up -d --build
```

Cette commande fonctionne sans fichier `.env`, avec les valeurs locales par
défaut. Pour personnaliser les ports ou les paramètres du graphe :

```bash
cp .env.example .env
```

Ne pas publier le fichier `.env`. Pour un déploiement public, définir un mot de
passe PostgreSQL propre au serveur.

Au premier lancement, les étapes sont exécutées dans cet ordre :

1. PostgreSQL démarre et devient disponible.
2. `corpus-init` télécharge, vérifie et installe les livres.
3. `index-init` construit l'index inversé V2.
4. `graph-init` construit le graphe de Jaccard et calcule PageRank.
5. Le backend démarre, puis le frontend.

Le premier lancement peut prendre plusieurs dizaines de minutes. Le corpus
occupe environ 1,4 Go et la base validée environ 990 Mo ; prévoir également
l'espace nécessaire aux images Docker, aux caches et aux fichiers temporaires.

Suivre l'installation :

```bash
docker compose ps -a
docker compose logs -f corpus-init index-init graph-init
```

Les services `corpus-init`, `index-init` et `graph-init` doivent terminer avec
le code **0**. Les services `db`, `backend` et `frontend` doivent devenir
**healthy**.

| Accès local | Adresse |
|---|---|
| Interface | [http://localhost:5173](http://localhost:5173) |
| Préfixe API | `/api/v1` sur le port 8000 |
| Documentation FastAPI | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Santé de l'API | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) |

Par défaut, les ports ne sont accessibles que depuis la machine hôte. Pour
une démonstration sur plusieurs appareils du même réseau :

```bash
FRONTEND_BIND=0.0.0.0 docker compose up -d
```

Ouvrir ensuite `http://<IP-du-serveur>:5173` depuis les autres appareils.

Après une modification du code :

```bash
docker compose up -d --build backend frontend
```

## Corpus et index

Le corpus contient **1 700 livres de Project Gutenberg**, chacun avec au moins
10 000 mots. Le minimum vérifié est de **10 183 mots**.

L'archive externe est publiée ici :
[corpus-1700.tar.gz](https://github.com/ouumm/daar-corpus-public/releases/download/corpus-v1/corpus-1700.tar.gz).

L'installateur vérifie le SHA-256 de l'archive, puis les empreintes des fichiers
par rapport au manifeste `backend/data/books.csv`. Un téléchargement partiel
peut être repris par HTTP Range si le serveur le permet. Une installation
interrompue peut être relancée avec la même commande Docker.

Chaque livre indexé et ses associations livre-terme sont validés dans une même
transaction ; les livres déjà terminés sont conservés lors d'une reprise.

| Indicateur | Index V2 validé |
|---|---:|
| Livres indexés | 1 700 |
| Termes distincts | 973 252 |
| Associations livre-terme | 10 753 306 |
| Arêtes non orientées du graphe | 36 506 |
| Scores PageRank | 1 700 |

La V2 découpe les mots Unicode, les passe en minuscules, retire des mots vides
et applique la racinisation Snowball pour l'anglais, le français et l'allemand.
Par exemple, `whales` et `whale` partagent une racine.

Les titres sont nettoyés lors de l'installation et à chaque nouvelle exécution
de `corpus-init`, même lorsque le corpus est déjà présent. Les codes de
catalogue MARC sont retirés, par exemple
`Peter Pan : $b [Peter and Wendy]` devient `Peter Pan : [Peter and Wendy]`.

L'ancien index V1 a été retiré ; ses mesures restent dans les documents de
comparaison : 1 000 281 termes et 15 546 923 associations livre-terme.

## API de recherche et de lecture

```text
GET /api/v1/search?q=alice&sort=occurrences&limit=20&offset=0
GET /api/v1/search?q=alice&sort=pagerank&limit=20&offset=0
GET /api/v1/search/regex?q=alic%7Crabbit&limit=20&offset=0
GET /api/v1/books?limit=20&offset=0
GET /api/v1/books/11
GET /api/v1/books/11/text?offset=0&limit=40000
GET /api/v1/books/11/recommendations?limit=5
```

La recherche par mots-clés utilise une logique **OU** pour plusieurs mots.
Le score par défaut est la somme des occurrences des racines reconnues,
rapportée à un million de mots du livre. Le tri PageRank utilise la centralité
globale du livre dans le graphe, parmi les livres correspondant à la recherche.
Le tri et la pagination sont réalisés dans PostgreSQL.

Les RegEx s'appliquent à chaque **racine entière de l'index**, et non aux
phrases du texte original. Ainsi, `alice` est normalisé en `alic` en recherche
par mots-clés ; en mode RegEx, utiliser `alic` ou `alic.*`.

La syntaxe de l'automate comprend les caractères littéraux, `.`, `|`, les
groupes `(...)`, les répétitions `*`, `+`, `?` et l'échappement par antislash.
Les classes `[a-z]`, les ancres `^` et `$` et les raccourcis comme `\d` ne sont
pas implémentés comme dans les moteurs RegEx généralistes. Un motif est limité
à 100 caractères ; une expression reconnaissant plus de 20 000 termes est
refusée avec HTTP 422.

Le frontend utilise `/api/v1` sur la même origine. Avec Compose, nginx relaie
les appels à FastAPI ; avec `npm run dev`, Vite les relaie vers le backend local.

## Graphe et stockage

| Donnée | Stockage |
|---|---|
| Textes Gutenberg | fichiers `.txt`, volume Docker `corpus` |
| Métadonnées | PostgreSQL : `books` |
| Index inversé | PostgreSQL : `books_v2`, `terms_v2`, `postings_v2` |
| Similarités de Jaccard | PostgreSQL : `book_similarities` |
| Centralité PageRank | PostgreSQL : `book_scores` |
| Comptes et sessions | PostgreSQL : `users`, `auth_sessions` |
| Favoris et historique | PostgreSQL : `user_favorites`, `search_history` |

Le graphe compare le vocabulaire discriminant des livres : racines présentes
dans au moins deux livres et dans au plus 50 % du corpus. Le seuil Jaccard par
défaut est de 0,20 ; jusqu'à cinq voisins supplémentaires de similarité
positive sont retenus par livre. Des livres peuvent rester isolés lorsqu'ils
n'ont aucun vocabulaire retenu en commun avec les autres.

Lors d'un redémarrage, le corpus est vérifié et l'index et le graphe existants
sont réutilisés. Le contrôle du graphe repose sur le nombre de livres ayant
un score. **Après une modification des paramètres du graphe**, forcer son
recalcul :

```bash
docker compose run --rm graph-init python -m scripts.build_graph --force
```

## Tests et validation finale

Validation du **17 novembre 2026**, sur le code du commit `3ae4534` :

- **98 tests backend réussis**, aucun ignoré, avec la base isolée `daar_test`.
- Installation complète depuis une copie du code commité, sans `.env`, dans
  le projet Docker séparé `daar-fresh-verif`, avec des volumes neufs.
- Les 110 fichiers suivis par Git de cette copie ont été comparés au commit.
- Corpus téléchargé et vérifié, index et graphe reconstruits ; les trois
  tâches d'initialisation ont terminé avec le code 0.
- PostgreSQL, backend et frontend : `healthy`.
- **13 contrôles fonctionnels réussis** sur l'installation neuve, puis sur AWS :
  interface et proxy nginx, santé API, catalogue, recherche et pagination,
  PageRank, RegEx, rejet d'un motif invalide, recommandations, lecture et
  cohérence des données en base.
- Accès public AWS vérifié : interface HTTP 200, API opérationnelle et recherche
  `alice` renvoyant 309 livres.

### Relancer la suite backend

Utiliser uniquement la base **`daar_test`** : les fixtures réinitialisent ses
tables. Les tests d'intégration sont ignorés si `DB_NAME=daar_test` et
`DAAR_TEST_DB=1` ne sont pas tous deux définis.

Si cette base n'existe pas encore, la créer une seule fois :

```bash
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" daar_test'
```

Puis lancer les tests avec l'image locale, qui inclut par défaut les
dépendances de développement :

```bash
docker compose run --rm -T --no-deps \
  -e DB_NAME=daar_test -e DAAR_TEST_DB=1 -e PRELOAD_VOCABULARY=0 \
  backend python -m pytest tests/ -q
```

Ne pas exécuter cette suite sur la base principale `daar`. Les dépendances de
test sont déclarées dans `backend/requirements-dev.txt`. La CI GitLab contient
les jobs `backend_tests` et `frontend_build` ; les validations ci-dessus ne
constituent pas une confirmation d'un nouveau pipeline distant.

## Performances

Voir [PERFORMANCES_V2.md](docs/PERFORMANCES_V2.md) pour les mesures locales,
leur méthode, les données CSV et les graphiques. Ces chiffres ne sont pas des
mesures de charge de l'instance AWS.

- Recherche par mot-clé sur le corpus complet, sans filtre artificiel
  d'échantillonnage : environ 2 à 7 ms selon le mot.
- RegEx avec préfixe littéral : environ 25 à 32 ms ; sans préfixe, environ
  560 ms pour le motif mesuré.
- Recommandations : environ 10 ms.
- Charge locale : environ 270 requêtes/s, aucune erreur jusqu'à 16 clients
  dans la campagne mesurée.

Reproduire les mesures :

```bash
docker compose exec backend python -m scripts.benchmark_v2 --out /tmp/bench
docker cp "$(docker compose ps -q backend)":/tmp/bench/. docs/benchmarks_v2/
python3 scripts/plot_benchmark_v2.py docs/benchmarks_v2
```

Les validations antérieures restent dans
[VALIDATION_P1.md](docs/VALIDATION_P1.md), et les mesures V1 dans
[PERFORMANCES_P1.md](docs/PERFORMANCES_P1.md).

## Déploiement AWS

Pour installer depuis zéro sur un serveur disposant de Docker et de ressources
suffisantes pour l'indexation et le calcul du graphe :

```bash
cp .env.example .env
# Définir un mot de passe PostgreSQL propre au serveur dans .env.
docker compose -f compose.yaml -f compose.aws.yaml up -d --build
```

La surcharge AWS publie le frontend sur le port 80, retire l'exposition directe
du backend et exige `POSTGRES_PASSWORD`. Le groupe de sécurité EC2 doit
autoriser HTTP TCP 80 pour l'accès public ; PostgreSQL et le port 8000 du
backend n'ont pas besoin d'être ouverts sur Internet.

### Instance de démonstration validée

- Région : `eu-north-1` ; Debian 13, architecture x86-64.
- Instance `t3.micro`, environ 1 Go de RAM, disque de 8 Go et 1 Go de swap.
- Application : [http://13.61.8.67/](http://13.61.8.67/).
- Version applicative déployée : `3ae4534`.

Sur cette petite instance, les images ont été construites sur le serveur,
puis le corpus et la base issus de l'installation neuve validée ont été
transférés. L'index et le graphe ont été restaurés, sans recalcul sur EC2.
Ce déploiement valide le service sur cette instance, pas la capacité à y
reconstruire tout le corpus depuis zéro.

Le dossier du déploiement est `/home/admin/daar-release-3ae4534`, avec le projet
Compose `daar`. Un fichier propre au serveur, `compose.ec2.yaml`, limite les
journaux et ajuste PostgreSQL : `shared_buffers=64MB`, `max_connections=40`,
`max_wal_size=256MB` et `min_wal_size=80MB`. Ce fichier n'est pas livré dans le
dépôt ; il s'ajoute aux deux fichiers Compose du projet.

Pour consulter les services du déploiement existant, depuis une session SSH :

```bash
cd /home/admin/daar-release-3ae4534
sudo docker compose -p daar \
  -f compose.yaml -f compose.aws.yaml -f compose.ec2.yaml ps -a
```

HTTPS et un certificat TLS restent à configurer avant une utilisation avec
des identifiants réels. Le déploiement actuel sert uniquement en HTTP.

## Arrêt et conservation des données

En local, arrêter les conteneurs en conservant les volumes :

```bash
docker compose down
docker compose up -d
```

Les volumes `pgdata` et `corpus` conservent respectivement la base et les textes.
**Ne pas utiliser `docker compose down -v` pour conserver ces données.**
Sur AWS, conserver également le nom de projet `daar` et les trois fichiers
Compose dans les commandes de gestion du déploiement existant.

## Livraison

Le dépôt contient le code et les scripts nécessaires pour récupérer le corpus.
Les textes volumineux, les volumes PostgreSQL et le fichier `.env` ne doivent
pas être inclus dans l'archive de rendu.

Créer l'archive finale, avec le rapport et la vidéo :

```bash
scripts/make_archive.sh --noms NOM1-NOM2-NOM3 --rapport rapport.pdf --video video.mp4
```

Le script vérifie la limite de **30 Mo**. La validation de l'application ne
remplace pas la relecture du rapport, de la vidéo et de l'archive finale selon
les consignes du rendu.
