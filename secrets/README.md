# Secrets Docker

Les mots de passe ne passent pas par des variables d'environnement : Docker
Compose les monte en fichiers en lecture seule dans `/run/secrets/` des seuls
conteneurs qui en ont besoin (`docker inspect` ne les affiche pas).

| Secret | Utilisé par | Fichier par défaut |
|---|---|---|
| `db_password` | PostgreSQL, backend, services d'initialisation | `db_password.dev` |
| `smtp_password` | backend (envoi d'e-mails) | `smtp_password.dev` (vide : e-mails désactivés) |

Les fichiers `*.dev` permettent de lancer le projet en local avec la seule
commande `docker compose up`. Ils ne contiennent **aucun vrai secret** : la base
n'est joignable que depuis le réseau Docker interne `db_net`.

## En production (ou pour vos propres valeurs)

Créer des fichiers à part, **jamais commités** (`.gitignore` exclut tout ce
dossier sauf les `*.dev`), puis indiquer leur chemin dans `.env` :

```bash
chmod 700 secrets                      # dossier privé
openssl rand -base64 24 > secrets/db_password.txt
printf '%s' 'mot-de-passe-application-gmail' > secrets/smtp_password.txt
chmod 644 secrets/*.txt                # lisibles par l'utilisateur postgres du conteneur
```

Sous Linux, un fichier en `600` appartenant à votre utilisateur serait
illisible par PostgreSQL : c'est le dossier, en `700`, qui protège les fichiers.

```dotenv
DB_PASSWORD_SECRET=./secrets/db_password.txt
SMTP_PASSWORD_SECRET=./secrets/smtp_password.txt
```

Sur AWS, `compose.aws.yaml` refuse de démarrer sans `DB_PASSWORD_SECRET`.
