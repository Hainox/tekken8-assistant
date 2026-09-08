from tekken_assistant.detect.watcher import Watcher
from tekken_assistant.models import Detection


def make_watcher(sequence, stable_polls=2):
    iterator = iter(sequence)
    return Watcher(detect=lambda: next(iterator), poll_interval=1.0, stable_polls=stable_polls)


def test_requires_stable_polls_before_commit():
    d1 = Detection("Jin Kazama", None)
    watcher = make_watcher([d1, d1])
    watcher.poll()
    assert watcher.state.is_empty()
    watcher.poll()
    assert watcher.state == d1


def test_jitter_never_commits():
    d1 = Detection("Jin Kazama", None)
    d2 = Detection(None, "King")
    watcher = make_watcher([d1, d2, d1, d2, d1, d2], stable_polls=3)
    for _ in range(6):
        watcher.poll()
    assert watcher.state.is_empty()


def test_commits_only_on_change():
    d1 = Detection("Jin Kazama", "King")
    d2 = Detection("Jin Kazama", "Paul Phoenix")
    watcher = make_watcher([d1, d1, d2, d2, d2])
    watcher.poll()
    watcher.poll()
    assert watcher.state == d1
    watcher.poll()
    watcher.poll()
    assert watcher.state == d2
    watcher.poll()
    assert watcher.state == d2


def test_stable_polls_one_commits_immediately():
    d1 = Detection("King", "King")
    watcher = make_watcher([d1], stable_polls=1)
    watcher.poll()
    assert watcher.state == d1


def test_empty_detection_does_not_commit():
    d_empty = Detection()
    d1 = Detection("King", None)
    watcher = make_watcher([d1, d1, d_empty, d_empty])
    watcher.poll()
    watcher.poll()
    assert watcher.state == d1
    watcher.poll()
    watcher.poll()
    assert watcher.state == d1
