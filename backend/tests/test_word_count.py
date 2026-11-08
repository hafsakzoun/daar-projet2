from app.services.word_count import count_words


def test_repeated_word():
    result = count_words("The king is a king")

    assert result["king"] == 2
    assert result["the"] == 1
    assert result["is"] == 1
    assert result["a"] == 1


def test_empty_text():
    assert count_words("") == {}


def test_case_insensitive():
    assert count_words("KING King king") == {"king": 3}


def test_punctuation():
    assert count_words("Hello, hello! World.") == {
        "hello": 2,
        "world": 1,
    }


def test_different_words():
    assert count_words("apple banana apple orange") == {
        "apple": 2,
        "banana": 1,
        "orange": 1,
    }
