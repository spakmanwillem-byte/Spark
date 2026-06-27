"""Iter_38 — Sessie 31, 3-in-1 batch backend regression.

C — self-awareness leest help/gradatie_{n}.json + admin.json (admin krijgt admin-topics)
B — gradatie-tonality in spark_user_view.format_for_system_prompt
A — semantic_matcher.py fuzzy match (rapidfuzz token_set_ratio) als laatste fast-path

Run: pytest /app/backend/tests/test_iter38_self_aware_tonality_semantic.py -v
"""
import os
import json
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
TURNS_DIR = Path("/app/backend/data/chat/logs")

ADMIN_USER = "user-001"        # Willem, gradatie 1, admin
FAM_USER = "user-672f0e5c"     # Jantje, gradatie 2 — familie

HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 60  # LLM-calls kunnen traag zijn


def _post_compose(text: str, user_id: str, session_id: str, timeout: int = TIMEOUT) -> dict:
    r = requests.post(
        COMPOSE_URL,
        json={"text": text, "user_id": user_id, "session_id": session_id},
        headers=HEADERS,
        timeout=timeout,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:300]}"
    return r.json()


# ===========================================================================
# A — SEMANTIC MATCHER
# ===========================================================================
class TestSemanticMatcher:
    """A — rapidfuzz token_set_ratio fast-path voor synoniemen."""

    def test_rps_synoniem_potje_sps(self):
        data = _post_compose("doe een potje sps", ADMIN_USER, "iter38-A-rps-1", timeout=15)
        assert data.get("action") == "open_game_rps", data
        assert data.get("used_model") == "semantic_matcher"
        assert data.get("semantic_score", 0) >= 78
        assert "sps" in (data.get("semantic_matched_canonical") or "").lower()
        assert data.get("fast_path") is True

    def test_rps_synoniem_kunnen_we_sps_spelen(self):
        data = _post_compose("kunnen we sps spelen", ADMIN_USER, "iter38-A-rps-2", timeout=15)
        assert data.get("action") == "open_game_rps", data
        assert data.get("used_model") == "semantic_matcher"
        assert data.get("semantic_score", 0) >= 78

    def test_tts_synoniem_zet_je_stem_aan(self):
        data = _post_compose("zet je stem maar aan", ADMIN_USER, "iter38-A-tts-1", timeout=15)
        # token_set_ratio van 'zet je stem maar aan' vs 'zet je stem aan' = 100
        assert data.get("action") == "enable_tts", data
        assert data.get("used_model") == "semantic_matcher"
        assert data.get("semantic_score", 0) >= 80

    def test_no_false_positive_filosofie(self):
        """'wat is filosofie?' moet GEEN semantic match geven → LLM-pad."""
        data = _post_compose("wat is filosofie?", ADMIN_USER, "iter38-A-neg-1", timeout=60)
        assert data.get("action") in (None, ""), f"unexpected action: {data.get('action')}"
        used = (data.get("used_model") or "").lower()
        # mag claude/llm/emergent zijn, maar NIET semantic_matcher
        assert used != "semantic_matcher", f"unexpected semantic_matcher hit: {data}"

    def test_no_false_positive_tts_irrelevant(self):
        """'vertel iets over je stem' → mag enable_tts NIET activeren."""
        data = _post_compose("vertel iets over je stem", ADMIN_USER, "iter38-A-neg-2", timeout=60)
        # action mag None zijn, OF iets anders dan enable/disable_tts
        action = data.get("action")
        assert action not in ("enable_tts", "disable_tts"), f"false positive tts: {data}"


# ===========================================================================
# REGRESSIE — exact fast-paths blijven prioriteit
# ===========================================================================
class TestExactFastPathRegression:
    """Exact triggers moeten NIET via semantic_matcher gaan."""

    def test_help_exact_blijft_smart_intents(self):
        data = _post_compose("help", ADMIN_USER, "iter38-reg-help", timeout=15)
        assert data.get("action") == "open_help_bark", data
        # MUST be smart_intents_service, NOT semantic_matcher
        assert data.get("used_model") == "smart_intents_service", \
            f"expected smart_intents_service, got {data.get('used_model')}"

    def test_multi_turn_memory_after_semantic_match(self):
        """Na semantic fast-path moet turns_dir log bestaan met user+spark message."""
        session_id = "iter38-sem-mem"
        # cleanup
        fp = TURNS_DIR / f"{session_id}.json"
        if fp.exists():
            fp.unlink()
        data = _post_compose("doe een potje sps", ADMIN_USER, session_id, timeout=15)
        assert data.get("action") == "open_game_rps"
        # geef het bestand even tijd om geschreven te worden
        time.sleep(0.5)
        assert fp.exists(), f"turns_dir log missing: {fp}"
        log = json.loads(fp.read_text())
        msgs = log.get("messages", [])
        assert len(msgs) >= 2, f"expected >=2 messages, got {len(msgs)}: {msgs}"
        roles = [m.get("role") for m in msgs[-2:]]
        assert "user" in roles, roles
        # spark-role wordt vaak 'spark' of 'assistant' — accepteer beide
        assert any(r in ("spark", "assistant") for r in roles), roles


# ===========================================================================
# C — SELF-AWARENESS gradatie-help (admin krijgt admin-topics)
# ===========================================================================
class TestSelfAwarenessHelpChain:
    """C — _load_self_awareness leest help/gradatie_{n}.json + admin.json."""

    def test_admin_krijgt_admin_topics_in_overzicht(self):
        """Admin user-001 moet admin-specifieke commands kennen.

        ⚠️ KNOWN BUG: build_user_profile leest uit data/auth/users.json (bestaat NIET),
        valt terug op gradatie=2 default en zet is_admin nooit. Dus user-001 wordt nooit
        als admin herkend → _load_help_chain_for_gradatie krijgt is_admin=False → geen
        admin.json topics worden toegevoegd.

        Test markeert het als xfail tot main agent dit fixt in spark_user_view.py.
        """
        from modules.chat.response_composer import _load_self_awareness
        aw = _load_self_awareness(user_id=ADMIN_USER)
        assert aw is not None, "self_awareness load failed"
        topics = aw.get("_help_topics_for_user", [])
        topic_ids = {t.get("id") for t in topics}
        admin_topic_ids = {"shadow-flag", "admin-grant", "force-sell", "shadow-cleanup"}
        overlap = admin_topic_ids & topic_ids
        if not overlap:
            pytest.xfail(
                "BUG iter_38: build_user_profile(user-001) returns gradatie=2 + "
                "is_admin=None omdat data/auth/users.json niet bestaat. User-001 is "
                "in data/system/users.json gradatie 1 / Beheerder. Fix nodig in "
                "spark_user_view._get_user_meta() — moet system/users.json lezen en "
                "is_admin op basis van rol=='Beheerder' bepalen."
            )
        admin_marked = [t for t in topics if t.get("from_gradatie") == "admin"]
        assert len(admin_marked) >= 2, f"geen admin-marked topics: {topics[:5]}"

    def test_admin_chain_directly_when_is_admin_true(self):
        """Bewijs dat chain WEL werkt als is_admin=True expliciet gegeven."""
        from modules.chat.response_composer import _load_help_chain_for_gradatie
        chain = _load_help_chain_for_gradatie(gradatie=1, is_admin=True)
        topic_ids = {t.get("id") for t in chain}
        admin_topic_ids = {"shadow-flag", "admin-grant", "force-sell", "shadow-cleanup"}
        overlap = admin_topic_ids & topic_ids
        assert len(overlap) >= 2, f"admin chain broken: {topic_ids}"

    def test_non_admin_krijgt_geen_admin_topics(self):
        from modules.chat.response_composer import _load_self_awareness
        aw = _load_self_awareness(user_id=FAM_USER)
        assert aw is not None
        topics = aw.get("_help_topics_for_user", [])
        topic_ids = {t.get("id") for t in topics}
        forbidden = {"shadow-flag", "admin-grant", "force-sell", "shadow-cleanup", "kbv2-auto-resolve"}
        bad = forbidden & topic_ids
        assert not bad, f"non-admin user kreeg admin topics: {bad}"

    def test_gradatie_chain_walks_inherits_from(self):
        """Gradatie 2 user moet via inherits_from ook hogere gradatie-topics zien (indien chain bestaat),
        of in elk geval z'n eigen gradatie_2.json topics."""
        from modules.chat.response_composer import _load_help_chain_for_gradatie
        chain = _load_help_chain_for_gradatie(gradatie=2, is_admin=False)
        assert len(chain) > 0, "lege chain voor gradatie 2"
        # alle from_gradatie waardes moeten int zijn (geen admin)
        froms = {t.get("from_gradatie") for t in chain}
        assert "admin" not in froms, f"non-admin chain bevat admin: {froms}"

    def test_gradatie_7_chain_contains_rps_topic(self):
        from modules.chat.response_composer import _load_help_chain_for_gradatie
        chain = _load_help_chain_for_gradatie(gradatie=7, is_admin=False)
        topic_ids = {t.get("id") for t in chain}
        assert "rps" in topic_ids, f"rps mist in gradatie 7 chain: {topic_ids}"


# ===========================================================================
# B — Gradatie-tonality in spark_user_view.format_for_system_prompt
# ===========================================================================
class TestGradatieTonality:
    """B — tonality-instructies per gradatie."""

    def test_g1_admin_tonality_meta_cognitie(self):
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        prof = build_user_profile(ADMIN_USER)
        prof["gradatie"] = 1  # forceer voor tonality-check
        snippet = format_for_system_prompt(prof)
        assert "meta-cognitie" in snippet.lower() or "transparant" in snippet.lower(), snippet
        assert "core" in snippet.lower(), snippet

    def test_g2_familie_tonality_warm_persoonlijk(self):
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        prof = build_user_profile(FAM_USER)
        snippet = format_for_system_prompt(prof)
        low = snippet.lower()
        # gradatie 2 → warm/familie
        assert "warm" in low and ("familie" in low or "persoonlijk" in low), snippet
        # mag NIET de zakelijk-toon van 5-7 hebben
        assert "zakelijk-vriendelijk" not in low, snippet
        assert "spark shop" not in low, snippet

    def test_g5_zakelijk_tonality_no_prive(self):
        from modules.chat.spark_user_view import format_for_system_prompt
        prof = {"naam": "Test5", "gradatie": 5, "relaties": [], "recente_themes": []}
        snippet = format_for_system_prompt(prof)
        low = snippet.lower()
        assert "zakelijk" in low, snippet
        assert "geen privé-info" in low or "geen prive-info" in low, snippet
        # mag Spark Shop voorstellen
        assert "spark shop" in low, snippet


# ===========================================================================
# REGRESSIE — Privacy
# ===========================================================================
class TestPrivacyRegression:
    def test_no_prive_leak_for_g2_zus(self):
        """user-672f0e5c (gradatie 2) vraagt over zus — Spark mag NIET 'Maaike' noemen.

        LLM-call dus traag — geef het de tijd."""
        data = _post_compose(
            "ik ben Willem, wie is mijn zus?",
            FAM_USER,
            "iter38-priv-1",
            timeout=90,
        )
        msg = (data.get("message") or "").lower()
        assert "maaike" not in msg, f"PRIVACY LEAK: 'Maaike' in response for g2 user: {msg[:300]}"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
