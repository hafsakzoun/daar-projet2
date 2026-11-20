# Intégration et déploiement continus (GitLab CI/CD)

Le pipeline est défini dans [`.gitlab-ci.yml`](../.gitlab-ci.yml).

```
test ──────────────────────────────┬─ build (main) ───────────┬─ deploy (main, manuel)
backend_tests      (pytest + PG)   │ build_backend_image      │ deploy_aws
frontend_lint_build (lint + build) │ build_frontend_image     │
compose_config     (Compose)       │                          │
```

| Job | Rôle | Quand |
|---|---|---|
| `backend_tests` | Tests unitaires **et** d'intégration sur un PostgreSQL jetable ; rapport JUnit visible dans la merge request | toujours |
| `frontend_lint_build` | `oxlint` puis `vite build` | toujours |
| `compose_config` | Vérifie que `compose.yaml` et la surcharge AWS sont valides | toujours |
| `build_*_image` | Construit les images et les publie dans le registre GitLab, étiquetées par commit (`:abc1234`) et `:latest` | branche `main` |
| `deploy_aws` | Met à jour l'instance EC2 avec les images du commit | `main`, déclenché à la main |

Les tests d'intégration ne tournent que sur une base nommée `daar_test` avec
`DAAR_TEST_DB=1` : la base de production ne peut jamais être réinitialisée.

## Mettre à jour AWS en une commande (depuis un poste)

```bash
scripts/update_aws.sh
```

La clé `.pem` est trouvée automatiquement (ou se passe en argument). Le script
envoie le code du dernier commit, sauvegarde l'ancien dossier du serveur,
prépare les secrets Docker (base, e-mail depuis `secrets/smtp_password.txt`),
reconstruit les images sur le serveur, vérifie l'API à travers nginx et remet
la version précédente en place si la nouvelle ne répond pas.

## Déploiement continu vers AWS

Le job `deploy_aws` :

1. copie sur le serveur les fichiers Compose du dépôt et la configuration nginx HTTPS ;
2. connecte le serveur au registre GitLab avec le jeton éphémère du job ;
3. exécute [`scripts/deploy_ec2.sh`](../scripts/deploy_ec2.sh) : téléchargement
   des nouvelles images, redémarrage du backend et du frontend, vérification
   de `/api/v1/health` à travers nginx.

Les volumes (base, corpus) et le certificat HTTPS ne sont pas modifiés. Le
fichier `compose.ec2.yaml`, propre au serveur, est conservé.

Le job se déclenche d'un clic sur ▶ dans le pipeline de `main`. Il n'apparaît
que si les variables ci-dessous sont définies, et le groupe de sécurité EC2
doit accepter SSH (port 22) depuis les machines de GitLab. Pour un déploiement
sans clic à chaque commit, remplacer `when: manual` par `when: on_success`.
Si la nouvelle version ne répond pas, la précédente est remise en place.

### Variables à définir

GitLab → *Settings → CI/CD → Variables* (cocher *Protect* et *Mask* quand c'est possible) :

| Variable | Type | Valeur |
|---|---|---|
| `EC2_HOST` | Variable | `13.61.8.67` |
| `EC2_SSH_KEY` | **File** | contenu de la clé privée `.pem` de l'instance |
| `EC2_KNOWN_HOSTS` | Variable | sortie de `ssh-keyscan 13.61.8.67` |

Facultatif : `EC2_USER` (défaut `admin`), `DEPLOY_DIR`
(défaut `/home/admin/daar-release-3ae4534`) et, pour les e-mails, `SMTP_PASSWORD`
(**masquée**), `SMTP_HOST`, `SMTP_USER`, `MAIL_FROM`, `APP_URL`.

Le registre de conteneurs doit être activé sur le projet
(*Settings → General → Visibility → Container registry*).

## Reproduire les jobs de test en local

```bash
docker compose run --rm -T --no-deps backend python -m pytest tests/ -v
```

Cette commande lance les tests unitaires ; les tests d'intégration sont
ignorés hors base de test. Pour les lancer aussi, voir la section Tests du
[README](../README.md).
