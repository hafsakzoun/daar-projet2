from collections import Counter

from app.services.normalization import tokenize


def count_words(text: str) -> dict[str, int]:
    """Compte les occurrences des mots normalisés."""
    words = tokenize(text)
    return dict(Counter(words))
