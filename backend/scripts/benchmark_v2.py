"""Benchmarks V2 du moteur de recherche.

Quatre experiences, chacune ecrite dans un CSV :

1. volume.csv      recherche par mot-cle selon la taille du corpus
                   (100 -> 1700 livres, echantillon regulier)
2. automate.csv    parcours de l'automate RegEx selon la taille
                   du vocabulaire (50 000 -> tous les termes)
3. comparaison.csv automate Python vs regex PostgreSQL, tri
                   occurrences vs PageRank
4. charge.csv      test de charge HTTP : 1 -> 16 clients simultanes

Usage (dans le conteneur backend, l'API doit tourner) :
    python -m scripts.benchmark_v2 --out /tmp/bench
"""

import argparse
import csv
import random
import statistics
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from time import perf_counter

from sqlalchemy import func, select

from app.db.models import Book
from app.db.session import SessionLocal
from app.db.v2_models import TermV2
from app.services.automate_v2 import AutomateV2
from app.services.regex_automate_search_v2 import search_regex_automate_v2
from app.services.search_optimized import search_books_v2, search_regex_v2

KEYWORDS = ["alice", "love", "king"]
PATTERNS = ["alic.*", "(love|heart)", "k.ng", ".*land"]
VOLUMES = [100, 250, 500, 1000, 1700]
VOCABULARY = [50_000, 100_000, 250_000, 500_000, None]
CLIENTS = [1, 2, 4, 8, 16]
API = "http://127.0.0.1:8000/api/v1/search"


def measure(function, repetitions, warmup=1):
    for _ in range(warmup):
        function()
    samples = []
    for _ in range(repetitions):
        start = perf_counter()
        function()
        samples.append((perf_counter() - start) * 1000)
    return samples


def stats(samples):
    return {
        "moyenne_ms": round(statistics.mean(samples), 2),
        "ecart_type_ms": round(statistics.stdev(samples), 2) if len(samples) > 1 else 0.0,
        "mediane_ms": round(statistics.median(samples), 2),
        "min_ms": round(min(samples), 2),
        "max_ms": round(max(samples), 2),
    }


def write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"-> {path} ({len(rows)} lignes)")


def experiment_volume(db, repetitions):
    ids = list(db.scalars(select(Book.id).order_by(Book.id)))
    rows = []
    for volume in VOLUMES:
        # Echantillon regulier sur tout le corpus (pas seulement les premiers id).
        subset = [ids[i * len(ids) // volume] for i in range(volume)]
        for word in KEYWORDS:
            total = search_books_v2(db, word, book_ids=subset)["total"]
            samples = measure(
                lambda: search_books_v2(db, word, book_ids=subset), repetitions
            )
            rows.append({"livres": volume, "requete": word, "resultats": total, **stats(samples)})
            print("volume", volume, word, rows[-1]["moyenne_ms"], "ms")
    return rows


def experiment_automaton(db, repetitions):
    rows = []
    all_terms = db.execute(select(TermV2.value).order_by(TermV2.id)).scalars().all()
    for size in VOCABULARY:
        terms = all_terms if size is None else all_terms[:size]
        for pattern in PATTERNS:
            automate = AutomateV2(pattern)

            def scan():
                return sum(1 for word in terms if automate.fullmatch_normalized(word))

            matches = scan()
            samples = measure(scan, repetitions, warmup=0)
            rows.append({
                "termes": len(terms), "motif": pattern,
                "termes_reconnus": matches, **stats(samples),
            })
            print("automate", len(terms), pattern, rows[-1]["moyenne_ms"], "ms")
    return rows


def experiment_comparison(db, repetitions):
    rows = []
    for pattern in PATTERNS:
        for method, function in (
            ("automate", lambda: search_regex_automate_v2(db, pattern)),
            ("postgresql", lambda: search_regex_v2(db, pattern)),
        ):
            total = function()["total"]
            samples = measure(function, repetitions)
            db.rollback()  # leve le SET LOCAL statement_timeout
            rows.append({"experience": "regex", "variante": method, "requete": pattern,
                         "resultats": total, **stats(samples)})
            print("regex", method, pattern, rows[-1]["moyenne_ms"], "ms")

    for word in KEYWORDS:
        for sort in ("occurrences", "pagerank"):
            function = lambda: search_books_v2(db, word, sort=sort)  # noqa: E731
            total = function()["total"]
            samples = measure(function, repetitions)
            rows.append({"experience": "tri", "variante": sort, "requete": word,
                         "resultats": total, **stats(samples)})
            print("tri", sort, word, rows[-1]["moyenne_ms"], "ms")

    return rows


def experiment_load(requests_per_client):
    words = ["alice", "love", "king", "whale", "history", "war", "sea", "god"]
    rows = []
    # Echauffement : premieres requetes (cache PostgreSQL froid) exclues.
    for word in words:
        with urllib.request.urlopen(f"{API}?q={word}", timeout=30) as response:
            response.read()

    for clients in CLIENTS:
        latencies, errors = [], []
        lock = threading.Lock()

        def client(seed):
            rng = random.Random(seed)
            for _ in range(requests_per_client):
                url = f"{API}?{urllib.parse.urlencode({'q': rng.choice(words)})}"
                start = perf_counter()
                try:
                    with urllib.request.urlopen(url, timeout=30) as response:
                        response.read()
                    elapsed = (perf_counter() - start) * 1000
                    with lock:
                        latencies.append(elapsed)
                except OSError as exc:
                    with lock:
                        errors.append(str(exc))

        threads = [threading.Thread(target=client, args=(i,)) for i in range(clients)]
        start = perf_counter()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        duration = perf_counter() - start

        rows.append({
            "clients": clients,
            "requetes": len(latencies),
            "erreurs": len(errors),
            "debit_req_s": round(len(latencies) / duration, 2),
            "p95_ms": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 2),
            **stats(latencies),
        })
        print("charge", clients, rows[-1]["moyenne_ms"], "ms", rows[-1]["debit_req_s"], "req/s")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=15)
    parser.add_argument("--only", choices=["charge"], help="ne lancer qu'une experience")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if args.only == "charge":
        write(args.out / "charge.csv", experiment_load(requests_per_client=20))
        return

    with SessionLocal() as db:
        books = db.scalar(select(func.count()).select_from(Book))
        terms = db.scalar(select(func.count()).select_from(TermV2))
        print(f"Corpus : {books} livres, {terms} termes")

        write(args.out / "volume.csv", experiment_volume(db, args.repetitions))
        write(args.out / "automate.csv", experiment_automaton(db, max(3, args.repetitions // 3)))
        write(args.out / "comparaison.csv", experiment_comparison(db, max(5, args.repetitions // 2)))

    write(args.out / "charge.csv", experiment_load(requests_per_client=20))


if __name__ == "__main__":
    main()
