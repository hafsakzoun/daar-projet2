# Déploiement sur AWS

Démonstration : [https://13.61.8.67/](https://13.61.8.67/). HTTP redirige vers
HTTPS (code 308). Configuration du certificat : [HTTPS.md](HTTPS.md).

## Installer depuis zéro

Sur un serveur avec Docker et assez de ressources pour l'indexation et le graphe :

```bash
cp .env.example .env
chmod 700 secrets
openssl rand -base64 24 > secrets/db_password.txt && chmod 644 secrets/db_password.txt
echo "DB_PASSWORD_SECRET=./secrets/db_password.txt" >> .env
docker compose -f compose.yaml -f compose.aws.yaml up -d --build
```

La surcharge AWS publie nginx sur le port 80, retire l'exposition directe de
l'API et refuse de démarrer sans secret propre au serveur. Le groupe de
sécurité EC2 doit ouvrir les ports 80 et 443 ; PostgreSQL et le port 8000 restent
fermés.

## Mettre à jour

Depuis un poste, en une commande (voir [CI_CD.md](CI_CD.md)) :

```bash
scripts/update_aws.sh
```

ou d'un clic sur le job `deploy_aws` du pipeline GitLab. Dans les deux cas,
l'API est vérifiée après le redémarrage et la version précédente est remise en
place si la nouvelle ne répond pas.

## Instance de démonstration

- Région `eu-north-1` (Stockholm), Debian 13, x86-64.
- `t3.micro` : environ 1 Go de RAM, disque de 8 Go, 1 Go de swap.
- Dossier `/home/admin/daar-release-3ae4534`, projet Compose `daar`.
- `compose.ec2.yaml`, propre au serveur et non livré, limite les journaux et
  ajuste PostgreSQL (`shared_buffers=64MB`, `max_connections=40`,
  `max_wal_size=256MB`, `min_wal_size=80MB`).

Sur cette petite instance, le corpus et la base issus d'une installation neuve
validée ont été transférés, sans recalcul de l'index ni du graphe sur EC2.

Consulter les services depuis une session SSH :

```bash
cd /home/admin/daar-release-3ae4534
sudo docker compose -p daar \
  -f compose.yaml -f compose.aws.yaml -f compose.ec2.yaml -f compose.https.yaml ps -a
```

Garder le nom de projet `daar` et les quatre fichiers Compose pour gérer ce
déploiement. Après un arrêt de l'instance, l'adresse publique peut changer : il
faut alors réémettre le certificat.
