import re


def tokenize(text: str) -> list[str]:
    """Transforme un texte en liste de mots normalisés."""
    text = text.lower()
    return re.findall(r"[a-z]+", text)
