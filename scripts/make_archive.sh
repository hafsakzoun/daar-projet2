#!/usr/bin/env bash
# Construit l'archive de rendu : daar-projet2-NOM1-NOM2-NOM3.zip
#
# Usage :
#   scripts/make_archive.sh --noms NOM1-NOM2-NOM3 --rapport rapport.pdf --video video.mp4
#
# - Code : uniquement les fichiers suivis par Git ou non ignores
#   (.gitignore exclut deja .env, data/generated, node_modules, .venv).
# - Ajoute le rapport et la video a la racine de l'archive.
# - Refuse une archive de plus de 30 Mo.
set -euo pipefail

NOMS=""
RAPPORT=""
VIDEO=""
LIMITE_MO=30

while [ $# -gt 0 ]; do
  case "$1" in
    --noms) NOMS="$2"; shift 2 ;;
    --rapport) RAPPORT="$2"; shift 2 ;;
    --video) VIDEO="$2"; shift 2 ;;
    *) echo "Option inconnue : $1" >&2; exit 2 ;;
  esac
done

if [ -z "$NOMS" ]; then
  echo "Usage : $0 --noms NOM1-NOM2-NOM3 [--rapport rapport.pdf] [--video video.mp4]" >&2
  exit 2
fi

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
NOM="daar-projet2-${NOMS}"
TRAVAIL="$(mktemp -d)"
trap 'rm -rf "$TRAVAIL"' EXIT
DEST="$TRAVAIL/$NOM"
mkdir -p "$DEST/code"

cd "$RACINE"

# Fichiers a ne jamais livrer, meme s'ils ne sont pas ignores par Git.
EXCLUS='^(TACHES_PROJET\.md|\.env|.*\.DS_Store|.*/\.env)$'

git ls-files -co --exclude-standard \
  | grep -Ev "$EXCLUS" \
  | while IFS= read -r fichier; do
      [ -f "$fichier" ] || continue
      mkdir -p "$DEST/code/$(dirname "$fichier")"
      cp "$fichier" "$DEST/code/$fichier"
    done

# Garde-fous : aucun secret ni donnee generee dans l'archive.
if find "$DEST" -name ".env" -o -name "node_modules" -o -name ".venv" | grep -q .; then
  echo "Erreur : .env, node_modules ou .venv present dans l'archive." >&2
  exit 1
fi

[ -n "$RAPPORT" ] && cp "$RAPPORT" "$DEST/rapport.pdf"
[ -n "$VIDEO" ] && cp "$VIDEO" "$DEST/video-pitch.${VIDEO##*.}"

SORTIE="$RACINE/$NOM.zip"
rm -f "$SORTIE"
(cd "$TRAVAIL" && zip -qr -9 "$SORTIE" "$NOM")

TAILLE=$(stat -f %z "$SORTIE" 2>/dev/null || stat -c %s "$SORTIE")
TAILLE_MO=$(awk "BEGIN { printf \"%.1f\", $TAILLE / 1048576 }")

echo "Archive : $SORTIE ($TAILLE_MO Mo)"
[ -z "$RAPPORT" ] && echo "Attention : pas de rapport ajoute (--rapport)."
[ -z "$VIDEO" ] && echo "Attention : pas de video ajoutee (--video)."

if [ "$TAILLE" -gt $((LIMITE_MO * 1048576)) ]; then
  echo "Erreur : l'archive depasse $LIMITE_MO Mo. Recompresse la video." >&2
  exit 1
fi
