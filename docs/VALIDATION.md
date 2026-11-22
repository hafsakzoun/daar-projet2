# Tests et validation

## Lancer les tests

Tests unitaires (aucune base nécessaire) :

```bash
docker compose run --rm -T --no-deps backend python -m pytest tests/ -v
```

Tests d'intégration : ils tournent uniquement sur la base jetable `daar_test`,
dont les tables sont réinitialisées. Créer la base une fois, puis lancer :

```bash
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" daar_test'
```

```bash
docker compose run --rm -T --no-deps \
  -e DB_NAME=daar_test -e DAAR_TEST_DB=1 -e PRELOAD_VOCABULARY=0 \
  backend python -m pytest tests/ -q
```

Sans `DB_NAME=daar_test` et `DAAR_TEST_DB=1`, les tests d'intégration sont
ignorés : la base principale ne peut pas être effacée par erreur. Le pipeline
GitLab lance les deux suites à chaque commit ([CI_CD.md](CI_CD.md)).

## Installation neuve (17 novembre 2026, commit `3ae4534`)

- Copie du code commité, sans `.env`, dans un projet Docker séparé avec des
  volumes neufs.
- Corpus téléchargé et vérifié, index et graphe reconstruits : les trois tâches
  d'initialisation terminent avec le code 0 ; base, backend et frontend `healthy`.
- 98 tests backend réussis sur `daar_test`.
- 13 contrôles fonctionnels réussis, en local puis sur AWS en HTTPS : interface
  et relais nginx, santé de l'API, catalogue, recherche et pagination, PageRank,
  RegEx, rejet d'un motif invalide, recommandations, lecture, cohérence des
  données. La recherche `alice` renvoie 309 livres.

Validations de la première version : [VALIDATION_P1.md](VALIDATION_P1.md).
