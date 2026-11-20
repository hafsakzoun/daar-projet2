#!/usr/bin/env bash
# Exécuté sur l'instance EC2, soit par le job GitLab deploy_aws (images du
# registre), soit par scripts/update_aws.sh depuis un poste (BUILD=1).
#
# 1. prépare les secrets Docker du serveur (une seule fois) ;
# 2. renseigne la configuration e-mail dans .env si la CI la fournit ;
# 3. remplace les images backend et frontend par celles du commit ;
# 4. vérifie l'API à travers nginx, et revient à la version précédente
#    si elle ne répond pas.
#
# Les volumes (base, corpus) et le certificat HTTPS ne sont jamais touchés.
set -euo pipefail

: "${DEPLOY_DIR:?}" "${BACKEND_IMAGE:?}" "${FRONTEND_IMAGE:?}"
cd "$DEPLOY_DIR"
touch .env

# Le mot de passe de la base passe désormais par un secret Docker : une
# surcharge propre au serveur ne doit plus le fournir en variable
# (PostgreSQL refuse POSTGRES_PASSWORD et POSTGRES_PASSWORD_FILE ensemble).
if [ -f compose.ec2.yaml ] && grep -qE '^[[:space:]]*(POSTGRES_PASSWORD|DB_PASSWORD):' compose.ec2.yaml; then
  echo "compose.ec2.yaml définit encore un mot de passe en variable :" >&2
  grep -nE 'PASSWORD' compose.ec2.yaml >&2
  echo "Retire ces lignes (le secret Docker les remplace), puis relance." >&2
  exit 1
fi

# ── 1. Secret de la base ──────────────────────────────────────────────
# Reprend le mot de passe de l'ancien .env (base déjà initialisée avec).
if ! grep -q '^DB_PASSWORD_SECRET=' .env; then
  mkdir -p secrets && chmod 700 secrets
  current=$(sed -n 's/^POSTGRES_PASSWORD=//p' .env | tail -1)
  if [ -n "$current" ]; then
    printf '%s' "$current" > secrets/db_password.txt
  else
    head -c 24 /dev/urandom | base64 | tr -d '/+=' > secrets/db_password.txt
  fi
  # Lisible par l'utilisateur postgres du conteneur ; le dossier reste privé.
  chmod 644 secrets/db_password.txt
  sed -i '/^POSTGRES_PASSWORD=/d' .env
  printf '\nDB_PASSWORD_SECRET=./secrets/db_password.txt\n' >> .env
  echo "Secret de la base créé dans $DEPLOY_DIR/secrets/."
fi

# ── 2. Configuration e-mail (valeurs non secrètes, fournies par la CI) ─
set_env() {
  local name=$1 value=$2
  [ -n "$value" ] || return 0
  sed -i "/^${name}=/d" .env
  printf '%s=%s\n' "$name" "$value" >> .env
}
set_env APP_URL "${APP_URL:-}"
set_env SMTP_HOST "${SMTP_HOST:-}"
set_env SMTP_PORT "${SMTP_PORT:-}"
set_env SMTP_USER "${SMTP_USER:-}"
set_env MAIL_FROM "${MAIL_FROM:-}"
if [ -s secrets/smtp_password.txt ]; then
  set_env SMTP_PASSWORD_SECRET ./secrets/smtp_password.txt
fi

# ── 3. Nouvelles images ───────────────────────────────────────────────
compose() {
  sudo BACKEND_IMAGE="$1" FRONTEND_IMAGE="$2" docker compose -p daar \
    -f compose.yaml -f compose.aws.yaml -f compose.ec2.yaml -f compose.https.yaml \
    "${@:3}"
}

current_image() {
  local id
  id=$(compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" ps -q "$1" 2>/dev/null || true)
  [ -n "$id" ] && sudo docker inspect --format '{{.Config.Image}}' "$id" 2>/dev/null || true
}
previous_backend=$(current_image backend)
previous_frontend=$(current_image frontend)

if [ "${BUILD:-0}" = "1" ]; then
  # Mise à jour lancée depuis un poste (scripts/update_aws.sh) : images
  # construites sur le serveur à partir du code envoyé.
  compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" build backend frontend
else
  # Mise à jour par la CI : images déjà construites dans le registre GitLab.
  compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" pull backend frontend
  # Le jeton du registre ne doit pas rester sur le serveur.
  [ -n "${REGISTRY:-}" ] && sudo docker logout "$REGISTRY" > /dev/null 2>&1 || true
fi

# Les services d'initialisation sont relancés mais passent leur tour
# si le corpus, l'index et le graphe sont déjà en place.
compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" up -d --no-build backend frontend

# ── 4. Vérification, et retour arrière si besoin ──────────────────────
healthy() {
  for _ in $(seq 1 30); do
    if curl -fsk https://127.0.0.1/api/v1/health > /dev/null 2>&1; then
      return 0
    fi
    sleep 4
  done
  return 1
}

if healthy; then
  echo "Déploiement réussi : $BACKEND_IMAGE / $FRONTEND_IMAGE"
  sudo docker image prune -f > /dev/null
  exit 0
fi

echo "La nouvelle version ne répond pas." >&2
compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" ps -a >&2 || true
compose "$BACKEND_IMAGE" "$FRONTEND_IMAGE" logs --tail 40 backend >&2 || true

if [ -n "$previous_backend" ] && [ -n "$previous_frontend" ]; then
  echo "Retour à la version précédente : $previous_backend / $previous_frontend" >&2
  compose "$previous_backend" "$previous_frontend" up -d --no-build backend frontend
  healthy && echo "Version précédente rétablie." >&2
fi
exit 1
