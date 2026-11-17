import pytest

from app.services.automate_v2 import AutomateV2, literal_prefixes
from app.services.regex_automate_search_v2 import candidate_ranges


@pytest.mark.parametrize(
    "pattern, prefixes, exact",
    [
        ("alic.*", ["alic"], False),
        ("(love|heart)", ["love", "heart"], True),
        ("k.ng", ["k"], False),
        (".*ing", [""], False),
        ("ab(c|d)e*", ["abc", "abd"], False),
        ("a+b", ["a"], False),
        ("x?yz", [""], False),
        ("(a|)b", ["ab", "b"], True),
    ],
)
def test_literal_prefixes(pattern, prefixes, exact):
    assert literal_prefixes(AutomateV2(pattern).tree) == (prefixes, exact)


def test_every_match_starts_with_a_prefix():
    words = ["alice", "alicia", "king", "kong", "ring", "love", "lover", "heart"]
    for pattern in ["alic.*", "k.ng", "(love|heart)", ".*ing", "lov(e|er)"]:
        automate = AutomateV2(pattern)
        prefixes, _ = literal_prefixes(automate.tree)
        for word in words:
            if automate.fullmatch(word):
                assert any(word.startswith(prefix) for prefix in prefixes)


def test_candidate_ranges_narrow_and_merge():
    values = sorted(["alic", "alice", "bob", "king", "kong", "love", "lover", "zed"])

    assert candidate_ranges(values, [""]) == [(0, len(values))]
    assert [values[a:b] for a, b in candidate_ranges(values, ["k"])] == [["king", "kong"]]
    # "lo" contient deja "love" : les intervalles sont fusionnes.
    assert [values[a:b] for a, b in candidate_ranges(values, ["love", "lo"])] == [["love", "lover"]]
    assert [values[a:b] for a, b in candidate_ranges(values, ["x"])] == [[]]
