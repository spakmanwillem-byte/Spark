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



# v13c_tag_sanitizer_apostrof — sessie 58 regressie voor de ghost-scan:
# unicode-apostrof-varianten mogen niet meer als aparte tag/begrip
# blijven bestaan (voorheen produceerde "foto’s" een ghost naast "foto's").
def test_unicode_apostrof_right_single_quote():
    """U+2019 (’) → rechte apostrof."""
    assert sanitize_tag("foto\u2019s") == "foto's"


def test_unicode_apostrof_left_single_quote():
    """U+2018 (‘) → rechte apostrof."""
    assert sanitize_tag("foto\u2018s") == "foto's"


def test_unicode_apostrof_modifier_letter():
    """U+02BC (ʼ) → rechte apostrof."""
    assert sanitize_tag("foto\u02BCs") == "foto's"


def test_unicode_apostrof_acute_accent():
    """U+00B4 (´) soms als apostrof gebruikt → rechte apostrof."""
    assert sanitize_tag("foto\u00B4s") == "foto's"


def test_apostrof_dedupe_in_lijst():
    """Beide varianten van foto's in één lijst moeten na sanitize dedupen."""
    tags = ["foto\u2019s", "foto's", "foto\u2018s"]
    out = sanitize_tag_list(tags)
    assert out == ["foto's"]


def test_merge_apostrof_variant():
    """Merge tussen unicode en ASCII apostrof mag geen dubbele opleveren."""
    existing = ["foto's"]
    new = ["foto\u2019s", "hobby\u2019s"]
    out = merge_tags(existing, new)
    assert out == ["foto's", "hobby's"]
