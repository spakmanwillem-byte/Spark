"""v13_privacy_guard_001 — regressie voor Attente Spark privacy-matrix.

Testet dat KB-kaarten, identity_facts en persoonsnamen correct gestript worden
voor lage-gradatie requesters (5-7 = kennis/onbekend/vreemde).

Run: cd /app && pytest backend/tests/test_privacy_guard_v13.py -v
"""
from __future__ import annotations

import pytest
from modules.chat import privacy_guard


@pytest.fixture(autouse=True)
def _reset_cache():
    privacy_guard.reset_cache()
    yield
    privacy_guard.reset_cache()


def _fake_cards():
    return [
        {"id": "c1", "begrip": "koffie", "tags": ["voedsel"], "lade": "doen",
         "lagen": {"laag1": "warme drank"}},
        {"id": "c2", "begrip": "moeder", "tags": ["familie", "persoonlijk"], "lade": "voelen",
         "lagen": {"laag1": "Heidi is de moeder van Willem"}},
        {"id": "c3", "begrip": "boekhouding", "tags": ["financieel"], "lade": "weten",
         "lagen": {"laag1": "geld administratie"}},
        {"id": "c4", "begrip": "arts-bezoek", "tags": ["gezondheid"], "lade": "doen",
         "lagen": {"laag1": "check-up"}},
        {"id": "c5", "begrip": "regen", "tags": ["natuur"], "lade": "weten",
         "lagen": {"laag1": "water uit lucht"}},
    ]


def test_grad_1_ziet_alles():
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=1)
    assert len(out) == 5


def test_grad_2_ziet_alles():
    # gradatie 2 = familie, geen blokkeer_tags in defaults
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=2)
    assert len(out) == 5


def test_grad_3_blokkeert_financieel_gezondheid():
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=3)
    ids = {c["id"] for c in out}
    assert "c3" not in ids  # financieel
    assert "c4" not in ids  # gezondheid
    assert "c1" in ids
    assert "c2" in ids  # familie mag nog (gradatie 3)
    assert "c5" in ids


def test_grad_5_blokkeert_ook_familie_en_persoonlijk():
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=5)
    ids = {c["id"] for c in out}
    assert "c2" not in ids  # familie tag
    assert "c3" not in ids  # financieel
    assert "c4" not in ids  # gezondheid
    assert "c1" in ids
    assert "c5" in ids


def test_grad_7_maximum_strict():
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=7)
    ids = {c["id"] for c in out}
    assert "c2" not in ids
    assert "c3" not in ids
    assert "c4" not in ids
    # neutrale kaarten blijven
    assert "c1" in ids
    assert "c5" in ids


def test_grad_none_wordt_strengste():
    """Onbekende gradatie → gedraagt zich als gradatie 7."""
    cards = _fake_cards()
    out = privacy_guard.filter_kb_cards(cards, gradatie=None)
    ids = {c["id"] for c in out}
    assert "c2" not in ids
    assert "c3" not in ids


def test_grad_5_strip_person_names():
    text = "Willem's dochter Lotus heeft vandaag Heidi gebeld."
    stripped = privacy_guard.strip_person_names(text, gradatie=5)
    # Lotus en Heidi staan in blokkeer_ook_person_names
    assert "Lotus" not in stripped
    assert "Heidi" not in stripped
    assert "iemand" in stripped


def test_grad_2_names_blijven():
    text = "Willem's dochter Lotus heeft vandaag Heidi gebeld."
    out = privacy_guard.strip_person_names(text, gradatie=2)
    assert "Lotus" in out
    assert "Heidi" in out


def test_identity_facts_strip_grad_5():
    facts = {
        "about_user": [{"trigger": "adres", "value": "Molenweg 12"}],
        "about_relationship": [{"trigger": "familie", "value": "moeder Heidi"}],
        "about_spark": [{"trigger": "naam", "value": "je bent Spark"}],
    }
    out = privacy_guard.filter_identity_facts(facts, gradatie=5)
    assert out["about_user"] == []
    assert out["about_relationship"] == []
    assert len(out["about_spark"]) == 1  # spark-facts blijven


def test_identity_facts_admin_blijft():
    facts = {
        "about_user": [{"trigger": "adres", "value": "Molenweg 12"}],
        "about_relationship": [{"trigger": "familie", "value": "moeder Heidi"}],
        "about_spark": [],
    }
    out = privacy_guard.filter_identity_facts(facts, gradatie=1)
    assert len(out["about_user"]) == 1
    assert len(out["about_relationship"]) == 1


def test_should_include_relations():
    assert privacy_guard.should_include_relations(1) is True
    assert privacy_guard.should_include_relations(4) is True
    assert privacy_guard.should_include_relations(5) is False
    assert privacy_guard.should_include_relations(7) is False
    assert privacy_guard.should_include_relations(None) is False


def test_lade_prive_filter_grad_5():
    cards = [
        {"id": "priv1", "begrip": "geheim", "tags": [], "lade": "privé",
         "lagen": {"laag1": "iets"}},
        {"id": "pub1", "begrip": "normaal", "tags": [], "lade": "weten",
         "lagen": {"laag1": "iets"}},
    ]
    out = privacy_guard.filter_kb_cards(cards, gradatie=5)
    ids = {c["id"] for c in out}
    assert "priv1" not in ids
    assert "pub1" in ids


def test_name_in_laag1_filter_grad_5():
    """Cards zonder tags maar met familie-naam in laag1 → gefilterd voor grad 5+."""
    cards = [
        {"id": "leak", "begrip": "vandaag", "tags": [],
         "lade": "weten", "lagen": {"laag1": "Ik ging vandaag met Lotus naar het strand"}},
        {"id": "safe", "begrip": "vandaag", "tags": [],
         "lade": "weten", "lagen": {"laag1": "Vandaag was zonnig"}},
    ]
    out = privacy_guard.filter_kb_cards(cards, gradatie=5)
    ids = {c["id"] for c in out}
    assert "leak" not in ids
    assert "safe" in ids
