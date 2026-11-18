#!/usr/bin/env bash
# Exécuté sur l'instance EC2 par le job GitLab deploy_aws.
# Remplace les images backend et frontend par celles du commit déployé,
# sans toucher aux volumes (base, corpus) ni au certificat HTTPS.
set -euo pipefail

: "${DEPLOY_DIR:?}" "${BACKEND_IMAGE:?}" "${FRONTEND_IMAGE:?}"
cd "$DEPLOY_DIR"

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
