#!/usr/bin/env bash
# Exécuté sur l'instance EC2 par le job GitLab deploy_aws.
# Remplace les images backend et frontend par celles du commit déployé,
# sans toucher aux volumes (base, corpus) ni au certificat HTTPS.
set -euo pipefail

: "${DEPLOY_DIR:?}" "${BACKEND_IMAGE:?}" "${FRONTEND_IMAGE:?}"
cd "$DEPLOY_DIR"

# Secrets Docker du serveur (créés une seule fois, jamais versionnés).
# Le mot de passe de la base reprend celui de l'ancien .env s'il existe.
if ! grep -q '^DB_PASSWORD_SECRET=' .env 2>/dev/null; then
  mkdir -p secrets && chmod 700 secrets
  current=$(sed -n 's/^POSTGRES_PASSWORD=//p' .env 2>/dev/null | tail -1)
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

COMPOSE=(sudo BACKEND_IMAGE="$BACKEND_IMAGE" FRONTEND_IMAGE="$FRONTEND_IMAGE"
  docker compose -p daar
  -f compose.yaml -f compose.aws.yaml -f compose.ec2.yaml -f compose.https.yaml)

"${COMPOSE[@]}" pull backend frontend
# Les services d'initialisation sont relancés mais passent leur tour
# si le corpus, l'index et le graphe sont déjà en place.
"${COMPOSE[@]}" up -d --no-build --wait backend frontend

# Vérification finale à travers nginx.
for attempt in $(seq 1 20); do
  if curl -fsk https://127.0.0.1/api/v1/health > /dev/null; then
    echo "Déploiement réussi : $BACKEND_IMAGE / $FRONTEND_IMAGE"
    sudo docker image prune -f > /dev/null
    exit 0
  fi
  sleep 3
done

echo "L'API ne répond pas après le déploiement." >&2
"${COMPOSE[@]}" ps -a >&2
exit 1
