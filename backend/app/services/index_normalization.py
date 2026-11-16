"""Normalisation multilingue pour l'index inverse V2."""

import re
import unicodedata
from collections import Counter
from functools import lru_cache
from threading import local

import snowballstemmer


STEMMERS = {
    "en": "english",
    "fr": "french",
    "de": "german",
}

STOPWORDS = {
    "en": frozenset({
        "a", "an", "and", "are", "as", "at", "be", "been",
        "but", "by", "for", "from", "had", "has", "have",
        "he", "her", "his", "i", "in", "is", "it", "its",
        "of", "on", "or", "our", "she", "that", "the",
        "their", "them", "there", "these", "they",
        "this", "those", "to", "was", "were", "with",
        "you", "your",
    }),
    "fr": frozenset({
        "à", "au", "aux", "avec", "ce", "ces", "dans",
        "de", "des", "du", "elle", "en", "est", "et",
        "il", "ils", "la", "le", "les", "leur",
        "mais", "ne", "nous", "ou", "par", "pas",
        "pour", "que", "qui", "se", "son", "sur",
        "un", "une", "vous",
    }),
    "de": frozenset({
        "aber", "das", "dem", "den", "der", "des",
        "die", "ein", "eine", "einem", "einen",
        "einer", "er", "es", "ich", "im", "in",
        "ist", "mit", "nicht", "sie", "und",
        "von", "zu",
    }),
}

_thread_state = local()


def tokenize_index_text(text: str) -> list[str]:
    """Extrait les mots Unicode sans chiffres ni underscores."""
    text = unicodedata.normalize("NFC", text).casefold()
    return re.findall(r"[^\W\d_]+", text)


def get_stemmer(language: str):
    """Retourne un stemmer propre au thread courant."""
    stemmer_name = STEMMERS.get(language)

    if stemmer_name is None:
        return None

    if not hasattr(_thread_state, "stemmers"):
        _thread_state.stemmers = {}

    if language not in _thread_state.stemmers:
        _thread_state.stemmers[language] = (
            snowballstemmer.stemmer(stemmer_name)
        )

    return _thread_state.stemmers[language]


@lru_cache(maxsize=100_000)
def normalize_index_term(
    term: str,
    language: str = "en",
) -> str | None:
    """Filtre et normalise un terme selon sa langue."""
    term = unicodedata.normalize("NFC", term).casefold()

    if not 2 <= len(term) <= 25:
        return None

    if term in STOPWORDS.get(language, frozenset()):
        return None

    stemmer = get_stemmer(language)

    if stemmer is None:
        return term

    return stemmer.stemWord(term)


def count_index_words(
    text: str,
    language: str = "en",
) -> dict[str, int]:
    """Compte les racines conservees pour un livre."""
    counts = Counter()

    for word in tokenize_index_text(text):
        stem = normalize_index_term(word, language)
        if stem:
            counts[stem] += 1

    return dict(counts)


def normalize_index_query(
    query: str,
    language: str = "en",
) -> list[str]:
    """Normalise une requete comme les livres indexes."""
    stems = (
        normalize_index_term(word, language)
        for word in tokenize_index_text(query)
    )

    return list(dict.fromkeys(
        stem for stem in stems if stem
    ))
