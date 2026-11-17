import pytest

from app.services.install_corpus import clean_title


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Peter Pan : $b [Peter and Wendy]", "Peter Pan : [Peter and Wendy]"),
        ("Black Beauty : $b The autobiography of a horse", "Black Beauty : The autobiography of a horse"),
        ("Astounding Stories,  August, 1931", "Astounding Stories, August, 1931"),
        ("Moby-Dick; or, The Whale", "Moby-Dick; or, The Whale"),
        ("  Le Prix : 5 $  ", "Le Prix : 5 $"),
    ],
)
def test_clean_title(raw, expected):
    assert clean_title(raw) == expected
