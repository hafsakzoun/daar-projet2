import json
import re
import tempfile
import time
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Book
from app.db.session import SessionLocal

TARGET_BOOKS = 1664
MIN_WORDS = 10000
CATALOG_URL = (
    "https://gutendex.com/books/"
    "?languages=en&mime_type=text%2Fplain"
)
CORPUS_DIR = Path("/data/books")


def download(url):
    """Retenter uniquement les erreurs reseau ou HTTP temporaires."""
    request = Request(url, headers={"User-Agent": "DAAR-Projet2/1.0"})

    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError, IncompleteRead) as error:
            if isinstance(error, HTTPError):
                if error.code not in (408, 429, 500, 502, 503, 504):
                    raise
            if attempt == 3:
                raise
            print(f"Tentative {attempt}/3 echouee : {error}", flush=True)
            time.sleep(2 * attempt)


def clean_text(text):
    start = re.search(
        r"\*\*\* START OF .*?PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text, re.IGNORECASE,
    )
    end = re.search(
        r"\*\*\* END OF .*?PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text, re.IGNORECASE,
    )
    if start is None or end is None or end.start() <= start.end():
        raise ValueError("Balises Gutenberg introuvables")
    return text[start.end():end.start()].strip()


def read_valid_local_text(path, expected_count=None):
    """Verifier qu'un fichier local est lisible et semble complet."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"[{path.stem}] Fichier local illisible : {error}", flush=True)
        return None

    count = len(text.split())
    if count < MIN_WORDS or (expected_count is not None and count != expected_count):
        print(f"[{path.stem}] Fichier local incomplet ou incoherent", flush=True)
        return None
    return text


def write_text_atomic(path, text):
    """Creer le fichier definitif seulement apres une ecriture complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            suffix=".tmp", delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(text)
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def import_book(metadata):
    book_id = metadata["id"]
    text_path = CORPUS_DIR / f"{book_id}.txt"
    text_url = (
        "https://gutenberg.pglaf.org/cache/epub/"
        f"{book_id}/pg{book_id}.txt"
    )

    with SessionLocal() as session:
        current = session.get(Book, book_id)
        already_in_db = current is not None
        expected_count = current.word_count if current is not None else None
        expected_path = current.text_path if current is not None else None

    text = read_valid_local_text(text_path, expected_count)
    if text is not None and already_in_db and expected_path == str(text_path):
        return "existing"

    downloaded = text is None
    if downloaded:
        try:
            raw_text = download(text_url).decode("utf-8-sig", errors="replace")
            text = clean_text(raw_text)
        except (HTTPError, URLError, TimeoutError, OSError, IncompleteRead, ValueError) as error:
            print(f"[{book_id}] Telechargement echoue : {error}", flush=True)
            return "failed"

    word_count = len(text.split())
    if word_count < MIN_WORDS:
        print(f"[{book_id}] Ignore : {word_count} mots", flush=True)
        return "ignored"

    title = metadata["title"]
    author = ", ".join(
        person["name"] for person in metadata.get("authors", [])
    ) or "Auteur inconnu"
    languages = metadata.get("languages", [])
    language = "en" if "en" in languages else (
        languages[0] if languages else "inconnue"
    )

    if downloaded:
        try:
            write_text_atomic(text_path, text)
        except OSError as error:
            print(f"[{book_id}] Ecriture echouee : {error}", flush=True)
            return "failed"
    else:
        print(f"[{book_id}] Fichier local reutilise", flush=True)

    # Si PostgreSQL echoue, le fichier reste utilisable pour une reprise.
    try:
        with SessionLocal() as session:
            book = session.get(Book, book_id)
            if book is None:
                book = Book(id=book_id)
                session.add(book)
            book.title = title
            book.author = author
            book.language = language
            book.word_count = word_count
            book.source_url = text_url
            book.text_path = str(text_path)
            session.commit()
    except SQLAlchemyError as error:
        print(f"[{book_id}] Erreur PostgreSQL : {error}", flush=True)
        return "failed"

    result = "repaired" if already_in_db else "imported"
    print(f"[{book_id}] {result} : {title} ({word_count} mots)", flush=True)
    return result


def count_books():
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(Book)) or 0


def main():
    total = count_books()
    url = CATALOG_URL
    page_number = 0
    results = {
        "imported": 0, "existing": 0, "repaired": 0,
        "ignored": 0, "failed": 0,
    }

    print(f"Livres deja presents : {total}")
    print(f"Objectif : {TARGET_BOOKS} livres\n")

    # Si 1664 livres sont deja en base, aucun telechargement n'est lance.
    while url is not None and total < TARGET_BOOKS:
        try:
            catalog = json.loads(download(url))
        except (HTTPError, URLError, TimeoutError, OSError, IncompleteRead, ValueError) as error:
            print(f"Erreur du catalogue : {error}", flush=True)
            break

        page_number += 1
        print(f"\n--- Page {page_number} du catalogue ---", flush=True)

        for metadata in catalog["results"]:
            if total >= TARGET_BOOKS:
                break
            result = import_book(metadata)
            results[result] += 1

            # Une reparation ne cree pas une nouvelle ligne en base.
            if result == "imported":
                total += 1
                if total % 25 == 0:
                    print(f"\nPROGRESSION : {total}/{TARGET_BOOKS}\n", flush=True)
            if result != "existing":
                time.sleep(2)

        url = catalog.get("next")
        if url is not None and total < TARGET_BOOKS:
            time.sleep(1)

    print("\n=== BILAN ===")
    print(f"Total en base : {count_books()}/{TARGET_BOOKS}")
    print(f"Nouveaux livres : {results['imported']}")
    print(f"Livres deja presents : {results['existing']}")
    print(f"Livres repares : {results['repaired']}")
    print(f"Livres trop courts : {results['ignored']}")
    print(f"Echecs : {results['failed']}")


if __name__ == "__main__":
    main()
