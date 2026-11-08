from app.services.normalization import tokenize


def test_lowercase():
    assert tokenize("King KING king") == [
        "king", "king", "king"
    ]


def test_punctuation():
    assert tokenize("Hello, world!") == [
        "hello", "world"
    ]


def test_empty_text():
    assert tokenize("") == []


def test_numbers():
    assert tokenize("Book 123 chapter 4") == [
        "book", "chapter"
    ]


def test_repeated_words():
    assert tokenize("the king is a king") == [
        "the", "king", "is", "a", "king"
    ]
