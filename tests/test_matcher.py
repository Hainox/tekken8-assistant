from tekken_assistant.detect.matcher import NameMatcher, squash
from tekken_assistant.models import Character


def make_chars() -> dict[str, Character]:
    chars = [
        Character(name="Jin Kazama", aliases=["jin"]),
        Character(name="Jun Kazama", aliases=["jun"]),
        Character(name="Kazuya Mishima", aliases=["kazuya", "kaz"]),
        Character(name="Marshall Law", aliases=["law"]),
        Character(name="Lee Chaolan", aliases=["lee"]),
        Character(name="Leo Kliesen", aliases=["leo"]),
        Character(name="Devil Jin", aliases=["devil jin", "dj"]),
        Character(name="Jack-8", aliases=["jack", "jack 8"]),
        Character(name="King", aliases=["king"]),
        Character(name="Armor King", aliases=["armor king", "ak"]),
    ]
    return {c.name: c for c in chars}


def test_squash_removes_non_alnum():
    assert squash("Devil Jin!") == "deviljin"
    assert squash("Jack-8") == "jack8"


def test_exact_match():
    matcher = NameMatcher(make_chars())
    assert matcher.match("Jin Kazama") == ("Jin Kazama", 1.0)


def test_alias_match():
    matcher = NameMatcher(make_chars())
    assert matcher.match("law")[0] == "Marshall Law"
    assert matcher.match("Kaz")[0] == "Kazuya Mishima"
    assert matcher.match("deviljin")[0] == "Devil Jin"


def test_short_names_require_high_ratio():
    matcher = NameMatcher(make_chars())
    assert matcher.match("Jun") == ("Jun Kazama", 1.0)
    assert matcher.match("Jin") == ("Jin Kazama", 1.0)
    assert matcher.match("Les") is None
    assert matcher.match("Keng") is None


def test_jin_vs_jun_disambiguation():
    matcher = NameMatcher(make_chars())
    assert matcher.match("Jin Kazama")[0] == "Jin Kazama"
    assert matcher.match("Jun Kazama")[0] == "Jun Kazama"


def test_typo_match():
    matcher = NameMatcher(make_chars())
    assert matcher.match("Kazuy Mishima")[0] == "Kazuya Mishima"
    assert matcher.match("Armor Kign")[0] == "Armor King"


def test_garbage_returns_none():
    matcher = NameMatcher(make_chars())
    assert matcher.match("abcdefgh") is None
    assert matcher.match("") is None
    assert matcher.match("  ") is None


def test_substring_lookalikes_rejected():
    matcher = NameMatcher(make_chars())
    assert matcher.match("Tekken King") is None
    assert matcher.match("tekkinking") is None
    assert matcher.match("steel") is None


def test_case_and_punctuation_insensitive():
    matcher = NameMatcher(make_chars())
    assert matcher.match("JACK-8!")[0] == "Jack-8"
