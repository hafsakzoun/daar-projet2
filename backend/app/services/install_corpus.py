
import csv
import hashlib
import re
import shutil
import sys
import tarfile
from pathlib import Path

from app.db.models import Base, Book
from app.db.session import SessionLocal, engine


CORPUS_DIR = Path("/data/books")
CSV_PATH = Path("/app/data/books.csv")
MIN_WORDS = 10000


def file_sha256(path):
    sha = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(chunk)

    return sha.hexdigest()


def load_manifest():
    # Charger les livres attendus depuis le CSV
    with CSV_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required = {
            "gutenberg_id",
            "title",
            "author",
            "language",
            "text_path",
            "word_count",
            "source_url",
            "sha256",
        }

        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Colonnes manquantes dans books.csv")

        books = list(reader)

    if not books:
        raise ValueError("Le manifeste books.csv est vide")

    expected = {}

    for row in books:
        book_id = int(row["gutenberg_id"])
        word_count = int(row["word_count"])
        sha256 = row["sha256"].lower()

        if book_id in expected:
            raise ValueError(f"Identifiant en double : {book_id}")

        if word_count < MIN_WORDS:
            raise ValueError(f"Livre trop court : {book_id}")

        if row["text_path"] != f"{book_id}.txt":
            raise ValueError(f"Chemin incorrect : {book_id}")

        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError(f"SHA-256 incorrect dans le CSV : {book_id}")

        expected[book_id] = sha256

    return books, expected


def install_corpus(archive_stream=None):
    books, expected_hashes = load_manifest()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    existing = 0
    seen_ids = set()

    # Lire l'archive .tar.gz fournie depuis le terminal
    stream = archive_stream if archive_stream is not None else sys.stdin.buffer

    with tarfile.open(fileobj=stream, mode="r|gz") as archive:
        for member in archive:
            if not member.isfile():
                continue

            match = re.fullmatch(r"books/([0-9]+)\.txt", member.name)

            if match is None:
                continue

            book_id = int(match.group(1))

            if book_id not in expected_hashes:
                raise ValueError(
                    f"Livre inattendu dans l'archive : {book_id}"
                )

            if book_id in seen_ids:
                raise ValueError(
                    f"Livre présent plusieurs fois dans l'archive : {book_id}"
                )

            seen_ids.add(book_id)

            expected_hash = expected_hashes[book_id]
            target = CORPUS_DIR / f"{book_id}.txt"

            # Conserver un fichier existant uniquement s'il est conforme
            if target.is_file() and file_sha256(target) == expected_hash:
                existing += 1
                continue

            source = archive.extractfile(member)

            if source is None:
                raise OSError(f"Impossible de lire {member.name}")

            temporary = CORPUS_DIR / f"{book_id}.partial"

            try:
                with source, temporary.open("wb") as output:
                    shutil.copyfileobj(source, output)

                if temporary.stat().st_size != member.size:
                    raise OSError(
                        f"Copie incomplète pour le livre {book_id}"
                    )

                if file_sha256(temporary) != expected_hash:
                    raise ValueError(
                        f"SHA-256 incorrect pour le livre {book_id}"
                    )

                temporary.replace(target)

            finally:
                temporary.unlink(missing_ok=True)

            copied += 1

            if copied % 200 == 0:
                print(f"{copied} livres copiés...", flush=True)

    # Vérification finale de tous les livres
    missing = []
    incorrect = []

    for book_id, expected_hash in expected_hashes.items():
        path = CORPUS_DIR / f"{book_id}.txt"

        if not path.is_file():
            missing.append(book_id)
        elif file_sha256(path) != expected_hash:
            incorrect.append(book_id)

    if missing or incorrect:
        raise ValueError(
            "Corpus incomplet ou incorrect : "
            f"{len(missing)} manquants, "
            f"{len(incorrect)} empreintes incorrectes. "
            f"Exemples : {missing[:5]} {incorrect[:5]}"
        )

    if len(seen_ids) != len(expected_hashes):
        raise ValueError(
            "Archive incomplète : "
            f"{len(seen_ids)} livres présents sur "
            f"{len(expected_hashes)} attendus"
        )

    # Créer les tables et importer les métadonnées
    Base.metadata.create_all(bind=engine)

    inserted = 0
    updated = 0

    with SessionLocal() as session:
        for row in books:
            book_id = int(row["gutenberg_id"])
            path = CORPUS_DIR / f"{book_id}.txt"

            book = session.get(Book, book_id)

            if book is None:
                book = Book(id=book_id)
                session.add(book)
                inserted += 1
            else:
                updated += 1

            book.title = row["title"]
            book.author = row["author"] or "Auteur inconnu"
            book.language = row["language"]
            book.word_count = int(row["word_count"])
            book.source_url = row["source_url"]
            book.text_path = str(path)

        session.commit()

    print("\n=== INSTALLATION TERMINÉE ===")
    print("Livres attendus :", len(expected_hashes))
    print("Fichiers copiés :", copied)
    print("Fichiers conservés :", existing)
    print("Livres ajoutés en base :", inserted)
    print("Livres actualisés en base :", updated)
    print("Fichiers manquants :", len(missing))
    print("Fichiers incorrects :", len(incorrect))


if __name__ == "__main__":
    install_corpus()
