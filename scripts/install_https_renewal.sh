#!/usr/bin/env bash
# A executer sur le serveur avec sudo, apres l'emission du certificat lisiere.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Executer avec sudo." >&2
  exit 1
fi

test -x /opt/daar-certbot/bin/certbot
test -f /etc/letsencrypt/renewal/lisiere.conf
docker exec daar-frontend-1 nginx -t

install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/daar-nginx <<'HOOK'
#!/bin/sh
set -eu
/usr/bin/docker exec daar-frontend-1 nginx -t
/usr/bin/docker exec daar-frontend-1 nginx -s reload
HOOK
chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/daar-nginx

cat > /etc/systemd/system/daar-certbot-renew.service <<'SERVICE'
[Unit]
Description=Renouvellement du certificat HTTPS Lisiere
Wants=network-online.target
After=network-online.target docker.service

[Service]
Type=oneshot
ExecStart=/opt/daar-certbot/bin/certbot renew --quiet --cert-name lisiere
TimeoutStartSec=300
SERVICE

cat > /etc/systemd/system/daar-certbot-renew.timer <<'TIMER'
[Unit]
Description=Verification du certificat Lisiere toutes les six heures

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
RandomizedDelaySec=1800
Persistent=true
Unit=daar-certbot-renew.service

[Install]
WantedBy=timers.target
TIMER

systemctl daemon-reload
systemctl enable --now daar-certbot-renew.timer
systemctl list-timers daar-certbot-renew.timer --no-pager
