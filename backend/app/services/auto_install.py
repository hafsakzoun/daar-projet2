"""Installation du corpus avec téléchargement HTTP reprenable."""

import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

from sqlalchemy import func, select

from app.db.models import Base, Book
from app.db.session import SessionLocal, engine
from app.services.install_corpus import (
    CORPUS_DIR,
    file_sha256,
    load_manifest,
    sync_metadata,
)

ARCHIVE_SHA256 = (
    "6e78b4dbe208518ad972178b63e4a90b91d6d10281c98e115b551d616472d235"
)
ARCHIVE_PATH = CORPUS_DIR.parent / ".cache" / "corpus-1700.tar.gz.part"
CHUNK_SIZE = 1024 * 1024


def corpus_ready():
    Base.metadata.create_all(bind=engine)
    books, expected = load_manifest()

    with SessionLocal() as session:
        total = session.scalar(
            select(func.count()).select_from(Book)
        )

    if total != len(books):
        return False

    for book_id, sha256 in expected.items():
        path = CORPUS_DIR / f"{book_id}.txt"
        if not path.is_file() or file_sha256(path) != sha256:
            return False

    return True


def download_archive(url, destination=ARCHIVE_PATH):
    """Reprendre une archive partielle si le serveur le permet."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.is_file():
        if file_sha256(destination) == ARCHIVE_SHA256:
            print("Archive déjà vérifiée.", flush=True)
            return destination

    for _ in range(2):
        offset = destination.stat().st_size if destination.is_file() else 0
        headers = {"User-Agent": "DAAR-Corpus-Installer"}

        if offset:
            headers["Range"] = f"bytes={offset}-"

        request = urllib.request.Request(url, headers=headers)

        try:
            response = urllib.request.urlopen(request, timeout=60)
        except urllib.error.HTTPError as error:
            if error.code == 416 and offset:
                destination.unlink(missing_ok=True)
                continue
            raise

        with response:
            status = response.status

            if offset and status == 206:
                content_range = response.headers.get(
                    "Content-Range", ""
                )
                match = re.fullmatch(
                    r"bytes (\d+)-(\d+)/(\d+|\*)",
                    content_range,
                )

                if not match or int(match.group(1)) != offset:
                    raise RuntimeError(
                        "Réponse Content-Range incorrecte."
                    )

                mode = "ab"
                total = (
                    None if match.group(3) == "*"
                    else int(match.group(3))
                )

            elif status == 200:
                if offset:
                    print(
                        "Reprise non supportée : téléchargement complet.",
                        flush=True,
                    )
                mode = "wb"
                total = None

            else:
                raise RuntimeError(
                    f"Réponse HTTP inattendue : {status}"
                )

            expected_length = response.headers.get("Content-Length")
            downloaded = 0

            with destination.open(mode) as output:
                while chunk := response.read(CHUNK_SIZE):
                    output.write(chunk)
                    downloaded += len(chunk)

            if (
                expected_length is not None
                and downloaded != int(expected_length)
            ):
                raise RuntimeError(
                    "Téléchargement interrompu : fichier partiel conservé."
                )

            if (
                total is not None
                and destination.stat().st_size != total
            ):
                raise RuntimeError(
                    "Téléchargement incomplet : reprise possible."
                )

        if file_sha256(destination) != ARCHIVE_SHA256:
            destination.unlink(missing_ok=True)
            raise ValueError("SHA-256 de l'archive incorrect.")

        return destination

    raise RuntimeError(
        "Impossible de reprendre le téléchargement HTTP."
    )


def main():
    if corpus_ready():
        changed = sync_metadata()
        print(
            f"Corpus déjà installé et vérifié ({changed} titres mis à jour).",
            flush=True,
        )
        return

    url = os.environ.get("CORPUS_URL", "").strip()

    if not url:
        raise RuntimeError(
            "CORPUS_URL manquante : téléchargement impossible."
        )

    print("Téléchargement du corpus...", flush=True)
    archive_path = download_archive(url)

    print("Archive vérifiée. Installation...", flush=True)

    with archive_path.open("rb") as source:
        subprocess.run(
            [sys.executable, "-m", "app.services.install_corpus"],
            stdin=source,
            check=True,
        )

    if not corpus_ready():
        raise RuntimeError(
            "Corpus incomplet après installation."
        )

    archive_path.unlink(missing_ok=True)
    print("Initialisation du corpus réussie.", flush=True)


if __name__ == "__main__":
    main()
