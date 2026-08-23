"""v13c_tag_sanitizer_001 — regressie voor LLM-lek-preventie.

Test dat sanitize_tag/sanitize_tag_list/merge_tags de bug-patronen
uit sessie 54 correct opvangt.
"""
from modules.kb_v2.tag_sanitizer import sanitize_tag, sanitize_tag_list, merge_tags


def test_llm_multiline_lek():
    """De originele bug: LLM output als tag."""
    corrupt = "neutraal\n\n🧠 weten\nbegrip"
    assert sanitize_tag(corrupt) == "neutraal"


def test_emoji_strippen():
    assert sanitize_tag("🧠 weten") == "weten"
    assert sanitize_tag("🌸 emotie 💭") == "emotie"


def test_dubbele_whitespace():
    assert sanitize_tag("  cloud    computing  ") == "cloud computing"


def test_length_cap():
    long = "a" * 100
    assert len(sanitize_tag(long)) == 60


def test_niet_string_input():
    assert sanitize_tag(None) == ""
    assert sanitize_tag(123) == ""
    assert sanitize_tag({"tag": "x"}) == ""
    assert sanitize_tag(["a", "b"]) == ""


def test_lege_string():
    assert sanitize_tag("") == ""
    assert sanitize_tag("   ") == ""
    assert sanitize_tag("\n\n🎭") == ""


def test_idempotent():
    """Herhaald aanroepen mag niks meer veranderen."""
    t = "cloud computing"
    assert sanitize_tag(sanitize_tag(t)) == t


def test_lijst_dedupe():
    tags = ["werk", "Werk", "WERK", "familie"]
    out = sanitize_tag_list(tags)
    assert out == ["werk", "familie"]


def test_lijst_met_llm_lek():
    tags = ["politiek", "neutraal\n\n🧠 weten\nbegrip", "🌸 voelen\nkaart"]
    out = sanitize_tag_list(tags)
    assert out == ["politiek", "neutraal", "voelen"]


def test_lijst_non_list_input():
    assert sanitize_tag_list(None) == []
    assert sanitize_tag_list("string") == []


def test_merge_behoudt_bestaande_volgorde():
    existing = ["knowledge-snap", "auto-generated", "werk"]
    new = ["🧠 weten", "auto-generated", "familie"]
    out = merge_tags(existing, new)
    assert out == ["knowledge-snap", "auto-generated", "werk", "weten", "familie"]


def test_merge_geen_duplicaten():
    existing = ["werk"]
    new = ["WERK", "werk\n\n🧠"]
    out = merge_tags(existing, new)
    assert out == ["werk"]
