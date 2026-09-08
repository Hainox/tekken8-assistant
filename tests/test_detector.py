from tekken_assistant.capture.screen import ScreenCapture
from tekken_assistant.detect.detector import ScreenDetector
from tekken_assistant.detect.matcher import NameMatcher
from tekken_assistant.models import Character, OcrWord


def make_detector(swap_sides=False) -> ScreenDetector:
    chars = [
        Character(name="Jin Kazama", aliases=["jin"]),
        Character(name="King", aliases=["king"]),
    ]
    matcher = NameMatcher({c.name: c for c in chars})
    return ScreenDetector(
        capture=ScreenCapture(),
        ocr=None,
        matcher=matcher,
        min_name_height_ratio=0.02,
        swap_sides=swap_sides,
    )


def word(text, x, y, w=120, h=30, conf=90):
    return OcrWord(text=text, x=x, y=y, w=w, h=h, conf=conf)


WORDS_TWO_NAMES = [
    word("Jin", 200, 600),
    word("Kazama", 330, 600),
    word("KING", 1500, 600),
    word("SETTINGS", 100, 50, h=14),
]


def test_two_names_assign_left_player_right_opponent():
    detector = make_detector()
    detection = detector.detect_from_words(WORDS_TWO_NAMES, screen_height=1080)
    assert detection.player == "Jin Kazama"
    assert detection.opponent == "King"


def test_single_left_name_is_player():
    detector = make_detector()
    detection = detector.detect_from_words([word("Jin", 200, 600), word("Kazama", 330, 600)], screen_height=1080)
    assert detection.player == "Jin Kazama"
    assert detection.opponent is None


def test_swap_sides_flips_assignment():
    detector = make_detector(swap_sides=True)
    detection = detector.detect_from_words(WORDS_TWO_NAMES, screen_height=1080)
    assert detection.player == "King"
    assert detection.opponent == "Jin Kazama"


def test_no_names_empty_detection():
    detector = make_detector()
    detection = detector.detect_from_words([word("SETTINGS", 100, 50, h=14)], screen_height=1080)
    assert detection.is_empty()


def test_duplicate_names_pick_most_prominent():
    words = [
        word("KING", 1500, 600, h=40),
        word("KING", 300, 900, h=60),
    ]
    detector = make_detector()
    detection = detector.detect_from_words(words, screen_height=1080)
    assert detection.player == "King"
