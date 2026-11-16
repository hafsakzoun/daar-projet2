from app.services.index_normalization import (
    count_index_words,
    normalize_index_query,
    normalize_index_term,
    tokenize_index_text,
)


def test_stopwords_removed():
    assert normalize_index_term("the") is None
    assert normalize_index_term("and") is None


def test_stemming_english():
    assert normalize_index_term("running") == "run"
    assert normalize_index_term("runs") == "run"


def test_frequencies_after_stemming():
    assert count_index_words("The whales and whale") == {
        "whale": 2
    }


def test_query_uses_same_normalization():
    assert normalize_index_query("Running runs the") == ["run"]


def test_empty_query():
    assert normalize_index_query("the and") == []


def test_unicode_tokenization():
    assert tokenize_index_text("Éléphants, Bücher!") == [
        "éléphants", "bücher"
    ]


def test_french_stemming():
    assert normalize_index_term(
        "maisons", "fr"
    ) == normalize_index_term("maison", "fr")


def test_old_english_without_stemming():
    assert normalize_index_term("whales", "ang") == "whales"


def test_language_specific_stopwords():
    assert normalize_index_term("les", "fr") is None
    assert normalize_index_term("und", "de") is None
