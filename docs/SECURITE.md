# Sécurité et gestion des secrets

Audit réalisé le 20 novembre 2026.

## Secrets

| Secret | Où il vit | Comment il arrive au conteneur |
|---|---|---|
| Mot de passe PostgreSQL | fichier hors Git (`secrets/db_password.txt`, ou `db_password.dev` en local) | **secret Docker** monté dans `/run/secrets/db_password` (PostgreSQL : `POSTGRES_PASSWORD_FILE`, backend : `DB_PASSWORD_FILE`) |
| Mot de passe d'application Gmail | fichier hors Git (`secrets/smtp_password.txt`) | **secret Docker** `/run/secrets/smtp_password`, monté **uniquement** dans le backend |
| Mots de passe des utilisateurs | base de données | jamais stockés : seule une empreinte **Argon2** est conservée |
| Jetons de session et liens e-mail | base de données | seule l'empreinte **SHA-256** est stockée |
| Clé SSH du serveur, accès registre | variables **masquées et protégées** GitLab CI/CD | jeton éphémère du job pour le registre |
| Certificat HTTPS | `/etc/letsencrypt` sur le serveur | monté en lecture seule, jamais dans le dépôt ni dans une image |
| Kubernetes | objets `Secret` (`lisiere-db`, `lisiere-smtp` facultatif) | variables injectées depuis le Secret |

Vérifications :

- `docker inspect` n'affiche plus aucun mot de passe : seulement les chemins
  `/run/secrets/...` ;
- aucun `.env`, aucune clé, aucun mot de passe réel dans **tout l'historique Git** ;
- `.gitignore` exclut `.env` et `secrets/*` (sauf les fichiers `*.dev` sans valeur réelle) ;
- l'archive de rendu (`scripts/make_archive.sh`) n'inclut ni `.env` ni secret ;
- le mot de passe SMTP est masqué dans les traces d'erreur (`repr=False`) ;
- `compose.aws.yaml` refuse de démarrer avec le mot de passe de développement :
  la CI vérifie ce refus à chaque commit.

Les fichiers `secrets/*.dev` permettent au correcteur de lancer le projet avec la
seule commande `docker compose up`, sans `.env`. Ils ne protègent rien de réel :
la base n'est joignable que depuis le réseau Docker interne `db_net`.

## Comptes utilisateurs

| Mesure | Détail |
|---|---|
| Hachage | Argon2 (`pwdlib`), mot de passe de 12 caractères minimum |
| Session | cookie `HttpOnly`, `SameSite=Strict`, `Secure` en HTTPS, limité au chemin `/api/v1/auth`, 24 h |
| CSRF | requêtes d'écriture acceptées seulement depuis le site lui-même (en-tête `Origin`) |
| Confirmation de l'adresse | lien valable 48 h, à usage unique ; connexion refusée avant confirmation (si un serveur SMTP est configuré) |
| Mot de passe oublié | lien valable 1 h, à usage unique ; ferme toutes les sessions ouvertes |
| Énumération des comptes | « mot de passe oublié » et « renvoyer l'e-mail » répondent pareil que l'adresse existe ou non ; l'e-mail est envoyé après la réponse (même durée) |
| Liens e-mail | construits avec `APP_URL`, jamais avec l'en-tête `Host` (empêche l'envoi d'un lien piégé) ; le jeton est après le `#`, donc jamais envoyé au serveur ni journalisé |
| Force brute | 8 tentatives de connexion / 10 min par adresse, 30 par IP ; 3 e-mails / 15 min par adresse |
| Mesure du temps | une connexion avec une adresse inconnue vérifie quand même un hachage factice |

## Application web

- En-têtes nginx : `Content-Security-Policy`, `X-Frame-Options: DENY`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `Strict-Transport-Security` en HTTPS ; version de nginx masquée.
- Réseaux Docker séparés : le frontend ne voit pas la base (`app_net` / `db_net`).
- Sur AWS, seul nginx est exposé (80/443) ; l'API et PostgreSQL ne sont pas publiés.
- RegEx : motif de 100 caractères maximum, automate limité à 512 états,
  20 000 termes reconnus au plus ; requête mot-clé limitée à 200 caractères.

## Limites connues

- Le compteur anti force brute est en mémoire : avec plusieurs répliques
  (Kubernetes), chaque pod compte séparément. Une version partagée demanderait Redis.
- L'inscription indique si une adresse est déjà utilisée (choix d'ergonomie).
- Une RegEx commençant par `.*` parcourt tout le vocabulaire (~7 s sur la petite
  instance AWS) : de nombreuses requêtes simultanées de ce type ralentiraient le service.
- L'historique Git contient un ancien dossier `backend/.venv` (bibliothèques
  Python, aucun secret) qui alourdit le dépôt.
