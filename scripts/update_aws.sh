#!/usr/bin/env bash
# Met à jour l'application sur AWS en une commande, depuis ce poste :
#
#   scripts/update_aws.sh [chemin/vers/cle.pem]
#
# Envoie le code du dernier commit, prépare les secrets Docker du serveur
# (base et e-mail), reconstruit les images sur le serveur et vérifie l'API.
# Si la nouvelle version ne répond pas, la précédente est remise en place.
# La base, les livres et le certificat HTTPS ne sont pas touchés.
set -euo pipefail

HOST=${AWS_HOST:-13.61.8.67}
USER_NAME=${AWS_USER:-admin}
DEPLOY_DIR=${AWS_DEPLOY_DIR:-/home/admin/daar-release-3ae4534}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Clé SSH : argument, variable AWS_KEY, ou unique fichier .pem trouvé.
# (compatible avec le bash 3.2 de macOS : ni mapfile ni tableau vide)
KEY=${1:-${AWS_KEY:-}}
if [ -z "$KEY" ]; then
  found=$(find "$HOME/.ssh" "$HOME/Downloads" "$HOME/Desktop" "$HOME/Documents" \
    -maxdepth 2 -name '*.pem' -type f 2>/dev/null || true)
  if [ -n "$found" ] && [ "$(printf '%s\n' "$found" | wc -l | tr -d ' ')" = "1" ]; then
    KEY=$found
    echo "Clé utilisée : $KEY"
  else
    echo "Indique la clé AWS : scripts/update_aws.sh chemin/vers/cle.pem" >&2
    [ -n "$found" ] && printf 'Clés trouvées :\n%s\n' "$found" >&2
    exit 2
  fi
fi
chmod 600 "$KEY"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER_NAME@$HOST")
SCP=(scp -q -i "$KEY" -o StrictHostKeyChecking=accept-new)

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "Attention : des modifications ne sont pas commitées, elles ne seront pas envoyées." >&2
fi
SHA=$(git rev-parse --short HEAD)
echo "Mise à jour d'AWS ($HOST) avec le commit $SHA"

# 1. Code du commit
ARCHIVE=$(mktemp -t lisiere).tar.gz
trap 'rm -f "$ARCHIVE"' EXIT
git archive --format=tar.gz -o "$ARCHIVE" HEAD
"${SCP[@]}" "$ARCHIVE" "$USER_NAME@$HOST:/tmp/lisiere-$SHA.tar.gz"
# Sauvegarde du dossier (fichiers seulement, pas les données) avant d'écraser.
"${SSH[@]}" "set -e; mkdir -p '$DEPLOY_DIR';
  cp -a '$DEPLOY_DIR' '$DEPLOY_DIR.avant-$SHA';
  cd '$DEPLOY_DIR';
  tar -xzf /tmp/lisiere-$SHA.tar.gz; rm -f /tmp/lisiere-$SHA.tar.gz;
  mkdir -p secrets; chmod 700 secrets"
echo "Sauvegarde de l'ancien dossier : $DEPLOY_DIR.avant-$SHA"

# 2. Secret e-mail : le fichier local secrets/smtp_password.txt, s'il existe
if [ -s secrets/smtp_password.txt ]; then
  "${SSH[@]}" "umask 077; cat > '$DEPLOY_DIR/secrets/smtp_password.txt' && chmod 644 '$DEPLOY_DIR/secrets/smtp_password.txt'" \
    < secrets/smtp_password.txt
fi
# Configuration e-mail non secrète, reprise du .env local.
env_value() { sed -n "s/^$1=//p" .env 2>/dev/null | tail -1; }

# 3. Construction, redémarrage, vérification (et retour arrière si besoin)
"${SSH[@]}" "DEPLOY_DIR='$DEPLOY_DIR' BUILD=1
  BACKEND_IMAGE='lisiere-backend:$SHA' FRONTEND_IMAGE='lisiere-frontend:$SHA'
  APP_URL='https://$HOST' SMTP_HOST='$(env_value SMTP_HOST)' SMTP_PORT='$(env_value SMTP_PORT)'
  SMTP_USER='$(env_value SMTP_USER)' MAIL_FROM='$(env_value MAIL_FROM)'
  bash -s" < scripts/deploy_ec2.sh

echo "Terminé : https://$HOST/"
