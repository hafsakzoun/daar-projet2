import pytest

from app.services.regex_search import validate_regex


def test_simple_regex():
    assert validate_regex("king") == "king"


def test_alternative():
    assert validate_regex("king|queen") == "king|queen"


def test_repetition():
    assert validate_regex("walk.*") == "walk.*"


def test_optional_character():
    assert validate_regex("colou?r") == "colou?r"


def test_uppercase():
    assert validate_regex("KING") == "KING"


def test_empty_regex():
    with pytest.raises(ValueError):
        validate_regex("")


def test_invalid_regex():
    with pytest.raises(ValueError):
        validate_regex("[abc")


def test_regex_too_long():
    with pytest.raises(ValueError):
        validate_regex("a" * 101)


def test_preserve_regex_escape():
    assert validate_regex(r"\D+") == r"\D+"
