from app.services.build_index import make_posting_rows


def test_posting_rows():
    counts = {"king": 2, "queen": 1}
    term_ids = {"king": 10, "queen": 20}

    result = make_posting_rows(5, counts, term_ids)

    assert result == [
        {"book_id": 5, "term_id": 10, "frequency": 2},
        {"book_id": 5, "term_id": 20, "frequency": 1},
    ]


def test_empty_postings():
    assert make_posting_rows(5, {}, {}) == []


def test_single_word():
    result = make_posting_rows(
        7,
        {"alice": 3},
        {"alice": 12},
    )

    assert result == [
        {"book_id": 7, "term_id": 12, "frequency": 3}
    ]
