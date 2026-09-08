from __future__ import annotations

from tekken_assistant.glossary import GLOSSARY, all_terms, lookup


def test_glossary_has_categories() -> None:
    assert len(GLOSSARY) >= 4
    for category, terms in GLOSSARY.items():
        assert terms, category
        for term, desc in terms:
            assert term and desc


def test_all_terms_flat() -> None:
    flat = all_terms()
    assert len(flat) >= 60
    assert all(len(item) == 3 for item in flat)


def test_lookup() -> None:
    assert lookup("ws") is not None
    assert lookup("CH") is not None
    assert lookup("несуществующий термин") is None
