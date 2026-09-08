from __future__ import annotations

import pytest

from tekken_assistant.notation import iter_segments, to_official

CASES = [
    ("d/f,2 ► f,f,3 ► d/f,1 ► f,1+2", "d/f+2 ► f,f+3 ► d/f+1 ► f+1+2"),
    ("d/f 2 ► 4 ► d/f 4", "d/f+2 ► 4 ► d/f+4"),
    ("WS 1 2", "WS 1,2"),
    ("WS 1, f,f,3", "WS 1,f,f+3"),
    ("d d/f f 2", "d,d/f,f+2"),
    ("u 1+2 1", "u+1+2,1"),
    ("Dash N 3 2 B", "Dash N+3,2 B"),
    ("Sway D/F 2 1", "Sway d/f+2,1"),
    ("qcf,1", "qcf,1"),
    ("CH f,2", "CH f+2"),
    ("f F 2", "f,F+2"),
    ("b,f,2,1", "b,f+2,1"),
    ("f,f,n,d,d/f,1", "f,f,n,d,d/f+1"),
    ("qcb,4 ► f,f+2,1", "qcb,4 ► f,f+2,1"),
    ("STB,d+2", "STB,d+2"),
    ("3 2 B 1+2", "3,2 B+1+2"),
    ("d 4 2 1", "d+4,2,1"),
    ("f F 2 1+2 W!", "f,F+2,1+2 W!"),
    ("( f 2 2 ) 1 *(max)", "( f+2,2 ) 1 *(max)"),
    ("Updraft : 3", "Updraft : 3"),
    ("Zantetsuken Lv.5 1+4", "Zantetsuken Lv.5 1+4"),
    ("d/f 3+4 Deep Dive 1", "d/f+3+4 Deep Dive 1"),
    ("f f F 2", "f,f,F+2"),
    ("Dash D/B N 3 2", "Dash d/b,N+3,2"),
    ("4 4 F", "4,4 F"),
    ("1 1 F", "1,1 F"),
    ("u/f 3 4", "u/f+3,4"),
    ("SSR b 1 2", "SSR b+1,2"),
    ("Sway d d/b b 1+2", "Sway d,d/b,b+1+2"),
    ("d 1+2 W!", "d+1+2 W!"),
]


@pytest.mark.parametrize(("raw", "expected"), CASES)
def test_to_official(raw: str, expected: str) -> None:
    assert to_official(raw) == expected


@pytest.mark.parametrize(("raw", "_expected"), CASES)
def test_to_official_idempotent(raw: str, _expected: str) -> None:
    once = to_official(raw)
    assert to_official(once) == once


def test_segments_direction_button() -> None:
    assert list(iter_segments("d/f+2")) == [("↘", "dir"), ("2", "btn2"), (" ", "space")]


def test_segments_dash() -> None:
    assert list(iter_segments("f,f+3")) == [("»", "dir"), ("3", "btn3"), (" ", "space")]


def test_segments_buttons() -> None:
    assert list(iter_segments("1,2")) == [
        ("1", "btn1"), (",", "comma"), ("2", "btn2"), (" ", "space"),
    ]
    assert list(iter_segments("1+2")) == [
        ("1", "btn1"), ("+", "plus"), ("2", "btn2"), (" ", "space"),
    ]


def test_segments_qcd_motion() -> None:
    assert list(iter_segments("d,d/f,f+2")) == [
        ("↓", "dir"), ("↘", "dir"), ("→", "dir"), ("2", "btn2"), (" ", "space"),
    ]


def test_segments_words_kept() -> None:
    kinds = [k for _v, k in iter_segments("WS 1,2 ► Dash ► Heat Burst")]
    assert "word" in kinds and "sep" in kinds and "btn1" in kinds
