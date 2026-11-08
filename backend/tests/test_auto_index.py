import pytest

from app.services.auto_index import needs_index


def test_index_complete():
    assert needs_index(1700, 1700) is False


def test_index_incomplete():
    assert needs_index(1700, 20) is True


def test_empty_database():
    with pytest.raises(RuntimeError):
        needs_index(0, 0)
