import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from sqlalchemy import func, select

from app.db.models import Base, Book
from app.db.session import SessionLocal, engine
from app.services.install_corpus import (
    CORPUS_DIR,
    file_sha256,
    load_manifest,
)

ARCHIVE_SHA256 = (
    "6e78b4dbe208518ad972178b63e4a90b91d6d10281c98e115b551d616472d235"
)


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
        if not path.is_file():
            return False
        if file_sha256(path) != sha256:
            return False

    return True


def main():
    if corpus_ready():
        print("Corpus déjà installé et vérifié.", flush=True)
        return

    url = os.environ.get("CORPUS_URL", "").strip()
    if not url:
        raise RuntimeError(
            "CORPUS_URL manquante : téléchargement impossible."
        )

    print("Téléchargement du corpus...", flush=True)

    with tempfile.TemporaryDirectory() as directory:
        archive_path = Path(directory) / "corpus.tar.gz"
        sha = hashlib.sha256()

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "DAAR-Corpus-Installer"},
        )

        with urllib.request.urlopen(request, timeout=60) as response:
            with archive_path.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
                    sha.update(chunk)

        if sha.hexdigest() != ARCHIVE_SHA256:
            raise ValueError("SHA-256 de l'archive incorrect.")

        print("Archive vérifiée. Installation...", flush=True)

        with archive_path.open("rb") as source:
            subprocess.run(
                [sys.executable, "-m", "app.services.install_corpus"],
                stdin=source,
                check=True,
            )

    print("Initialisation du corpus réussie.", flush=True)


if __name__ == "__main__":
    main()
