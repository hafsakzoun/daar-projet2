import pytest

from app.services.automate_v2 import AutomateV2, RegexError


@pytest.mark.parametrize(
    "pattern,word,expected",
    [
        ("run", "run", True),
        ("run", "running", False),
        ("run.*", "running", True),
        ("run.*", "alice", False),
        ("alice|rabbit", "alice", True),
        ("alice|rabbit", "rabbit", True),
        ("alice|rabbit", "alicea", False),
        ("run(s|ning)?", "run", True),
        ("run(s|ning)?", "runs", True),
        ("run(s|ning)?", "running", True),
        ("ab*c", "ac", True),
        ("ab*c", "abbbc", True),
        ("ab*c", "ab", False),
        ("ALICE", "alice", True),
    ],
)
def test_automate_matches(pattern, word, expected):
    assert AutomateV2(pattern).fullmatch(word) is expected


@pytest.mark.parametrize(
    "pattern",
    ["*abc", "abc\\", "a(", "x)", ""],
)
def test_invalid_regex_rejected(pattern):
    with pytest.raises(RegexError):
        AutomateV2(pattern)
