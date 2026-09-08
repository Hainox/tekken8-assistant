from tekken_assistant.detect.ocr import find_names
from tekken_assistant.detect.matcher import NameMatcher
from tekken_assistant.models import Character, OcrWord


def make_matcher() -> NameMatcher:
    chars = [
        Character(name="Jin Kazama", aliases=["jin"]),
        Character(name="King", aliases=["king"]),
        Character(name="Devil Jin", aliases=["devil jin"]),
    ]
    return NameMatcher({c.name: c for c in chars})


def word(text, x, y, w=100, h=30, conf=90):
    return OcrWord(text=text, x=x, y=y, w=w, h=h, conf=conf)


def test_finds_single_word_name():
    words = [word("KING", 900, 500), word("MENU", 100, 100, h=14)]
    hits = find_names(words, make_matcher(), min_height=20)
    names = [h.name for h in hits]
    assert "King" in names
    assert all(h.name != "MENU" for h in hits)


def test_finds_multi_word_name():
    words = [word("Jin", 200, 500), word("Kazama", 320, 500)]
    hits = find_names(words, make_matcher(), min_height=20)
    assert len(hits) == 1
    assert hits[0].name == "Jin Kazama"


def test_min_height_filters_small_text():
    words = [word("KING", 900, 500, h=12)]
    assert find_names(words, make_matcher(), min_height=20) == []


def test_low_confidence_single_word_not_matched():
    matcher = make_matcher()
    words = [word("Jn", 900, 500, h=30)]
    assert find_names(words, matcher, min_height=20) == []


def test_names_on_different_lines():
    words = [word("KING", 900, 500), word("Devil", 200, 700), word("Jin", 340, 700)]
    hits = find_names(words, make_matcher(), min_height=20)
    names = {h.name for h in hits}
    assert names == {"King", "Devil Jin"}
