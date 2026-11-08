from app.services.search import normalize_query, search_books


def test_query_lowercase():
    assert normalize_query("ALICE") == ["alice"]


def test_query_punctuation():
    assert normalize_query("Alice, Rabbit!") == [
        "alice", "rabbit"
    ]


def test_query_duplicates():
    assert normalize_query("alice ALICE rabbit") == [
        "alice", "rabbit"
    ]


def test_query_empty():
    assert normalize_query("   !!!   ") == []


def test_empty_search():
    result = search_books(None, "!!!")

    assert result["total"] == 0
    assert result["results"] == []
