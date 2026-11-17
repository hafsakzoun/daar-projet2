# HTTPS sur l'instance EC2

Lisière est accessible sur **https://13.61.8.67/**. Le certificat gratuit
Let's Encrypt porte sur cette adresse IP ; aucun nom de domaine ni service
AWS supplémentaire n'a été ajouté.

## Configuration

- HTTP 80 reste ouvert pour le challenge ACME et redirige le site vers HTTPS.
- HTTPS est servi sur le port 443 par le conteneur nginx existant.
- `frontend/nginx.https.conf` configure TLS et conserve le proxy `/api/`.
- `compose.https.yaml` monte le certificat en lecture seule, expose le port
  443 et transmet `AUTH_COOKIE_SECURE=true` au backend.
- Les clés privées sont conservées sur le serveur dans `/etc/letsencrypt`.
  Elles ne doivent être ni copiées dans le dépôt ni incluses dans les images.
- Le certificat est nommé `lisiere` et utilise le profil `shortlived`.

Sur le serveur actuel, toutes les commandes de gestion utilisent :

```bash
cd /home/admin/daar-release-3ae4534
sudo docker compose -p daar \
  -f compose.yaml -f compose.aws.yaml -f compose.ec2.yaml -f compose.https.yaml \
  ps -a
```

Conserver ces quatre fichiers lors d'une mise à jour du frontend afin de ne
pas retirer les ports, les montages et la configuration HTTPS.

## Renouvellement

Les certificats IP Let's Encrypt durent six jours : le renouvellement est
obligatoirement automatisé pour conserver un site accessible.

Certbot est installé dans `/opt/daar-certbot`. Le timer systemd
`daar-certbot-renew.timer` vérifie le renouvellement toutes les six heures,
avec un décalage aléatoire de trente minutes au maximum. Après un
renouvellement, le hook `/etc/letsencrypt/renewal-hooks/deploy/daar-nginx`
vérifie puis recharge nginx pour utiliser le nouveau certificat.

Le script suivant installe le timer et le hook sur le serveur déjà configuré :

```bash
sudo bash scripts/install_https_renewal.sh
```

Contrôler le timer et simuler un renouvellement :

```bash
sudo systemctl list-timers daar-certbot-renew.timer
sudo journalctl -u daar-certbot-renew.service --no-pager -n 30
sudo /opt/daar-certbot/bin/certbot renew --cert-name lisiere --dry-run --run-deploy-hooks
```

## En cas de changement d'adresse IP

Le certificat ne couvre que l'adresse pour laquelle il a été émis. Après un
arrêt/redémarrage EC2, vérifier l'IP publique. Si elle change, demander un
certificat pour la nouvelle IP puis mettre à jour les liens de démonstration.
Le certificat initial n'est pas réutilisable pour une autre adresse.

Pour une nouvelle installation, préparer d'abord un webroot HTTP accessible
sur `/.well-known/acme-challenge/`, installer Certbot 5.4 ou plus récent et
obtenir le certificat `lisiere` avant d'activer `compose.https.yaml`. Cette
surcharge suppose que les répertoires de certificat existent déjà.

Documentation officielle :
[certificats IP et renouvellement avec Certbot](https://letsencrypt.org/2026/03/11/shorter-certs-certbot).
