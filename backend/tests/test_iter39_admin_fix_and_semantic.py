"""Iter_39 — Re-test van iter_38 met fixes:
   (1) HIGH: spark_user_view._get_user_meta leest nu data/system/users.json primary.
   (2) MINOR: semantic_matcher canonical 'wat kan jij allemaal' verwijderd; min_score 85.

Run: pytest /app/backend/tests/test_iter39_admin_fix_and_semantic.py -v
"""
import os
import json
import time
import sys
from pathlib import Path

import pytest
import requests

# Zorg dat backend modules importeerbaar zijn
sys.path.insert(0, "/app/backend")

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://question-hub-160.preview.emergentagent.com").rstrip("/")
COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
TURNS_DIR = Path("/app/backend/data/chat/logs")

ADMIN_USER = "user-001"        # Willem, gradatie 1, admin (Beheerder)
GUEST_USER = "user-672f0e5c"   # Jantje, gradatie 7 (Onbekende/gast)

HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 90  # LLM-calls kunnen traag zijn


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
# FIX HIGH — build_user_profile admin detectie
# ===========================================================================
class TestUserMetaAdminFix:
    """Direct Python import tests voor build_user_profile."""

    def test_admin_user001_gradatie_1_is_admin(self):
        from modules.chat.spark_user_view import build_user_profile
        prof = build_user_profile(ADMIN_USER)
        assert prof["gradatie"] == 1, prof
        assert prof["is_admin"] is True, prof
        assert (prof.get("rol") or "").lower() == "beheerder", prof
        assert prof["naam"] == "De Willem", prof

    def test_non_admin_user672_is_not_admin(self):
        from modules.chat.spark_user_view import build_user_profile
        prof = build_user_profile(GUEST_USER)
        assert prof["is_admin"] is False, prof
        # in system/users.json staat gradatie 7
        assert prof["gradatie"] == 7, prof


# ===========================================================================
# FIX C — admin krijgt admin-topics, non-admin NIET
# ===========================================================================
class TestSelfAwarenessAdminTopics:
    def test_admin_help_chain_contains_admin_topics(self):
        from modules.chat.response_composer import _load_self_awareness
        aw = _load_self_awareness(user_id=ADMIN_USER)
        assert aw is not None
        topics = aw.get("_help_topics_for_user", [])
        topic_ids = {t.get("id") for t in topics}
        admin_topic_ids = {"shadow-flag", "admin-grant", "force-sell", "shadow-cleanup"}
        overlap = admin_topic_ids & topic_ids
        assert len(overlap) >= 2, f"admin krijgt niet ≥2 admin-topics: ids={topic_ids}"

    def test_non_admin_help_chain_no_admin_topics(self):
        from modules.chat.response_composer import _load_self_awareness
        aw = _load_self_awareness(user_id=GUEST_USER)
        assert aw is not None
        topics = aw.get("_help_topics_for_user", [])
        topic_ids = {t.get("id") for t in topics}
        forbidden = {"shadow-flag", "admin-grant", "force-sell", "shadow-cleanup", "kbv2-auto-resolve"}
        bad = forbidden & topic_ids
        assert not bad, f"non-admin user kreeg admin topics: {bad}"

    def test_admin_compose_message_contains_admin_words(self):
        """Live compose voor admin moet ≥2 admin-gerelateerde woorden bevatten."""
        data = _post_compose(
            "wat zijn mijn admin-rechten?", ADMIN_USER, "iter39-admin-c", timeout=90
        )
        msg = (data.get("message") or "").lower()
        admin_words = [
            "shadow", "admin-grant", "force-sell", "deploy",
            "tag-curatie", "kasboek", "beheer", "gradatie 1",
        ]
        hits = [w for w in admin_words if w in msg]
        assert len(hits) >= 2, f"admin response mist admin-context (hits={hits}): {msg[:500]}"

    def test_non_admin_compose_no_admin_keywords(self):
        """Non-admin compose mag GEEN technische admin keywords bevatten."""
        data = _post_compose(
            "wat zijn jouw admin-rechten?", GUEST_USER, "iter39-nonadmin-c", timeout=90
        )
        msg = (data.get("message") or "").lower()
        forbidden = ["shadow-flag", "admin-grant", "force-sell"]
        leaks = [w for w in forbidden if w in msg]
        assert not leaks, f"non-admin response bevat admin-keywords {leaks}: {msg[:500]}"


# ===========================================================================
# FIX B — gradatie-tonality (via format_for_system_prompt direct)
# ===========================================================================
class TestGradatieTonality:
    def test_g1_admin_tonality(self):
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        prof = build_user_profile(ADMIN_USER)
        snippet = format_for_system_prompt(prof).lower()
        # gradatie 1 tonality
        assert ("transparant" in snippet) or ("meta-cognitie" in snippet) or ("core" in snippet), snippet

    def test_g7_zakelijk_tonality_no_warm_familie(self):
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        prof = build_user_profile(GUEST_USER)
        snippet = format_for_system_prompt(prof).lower()
        # gradatie 7 valt onder 5-7 branch → zakelijk
        assert "zakelijk" in snippet, snippet
        # mag GEEN familie/persoonlijk-toon hebben (die staat alleen in 2-4 branch)
        # de 2-4 branch bevat "familie-gevoel"
        assert "familie-gevoel" not in snippet, snippet


# ===========================================================================
# FIX MINOR — semantic_matcher 'wat kan ik?' kort niet meer naar help-popup
# ===========================================================================
class TestSemanticHelpOverlapFix:
    def test_wat_kan_ik_not_short_circuit_to_help(self):
        """'wat kan ik?' mag NIET via semantic_matcher → open_help_bark gaan.
        Mag exact help-trigger zijn (smart_intents) of LLM-pad."""
        data = _post_compose("wat kan ik?", ADMIN_USER, "iter39-help-minor", timeout=90)
        used = (data.get("used_model") or "").lower()
        action = data.get("action")
        # Specifiek: semantic_matcher mag dit NIET als open_help_bark hebben opgepikt
        if action == "open_help_bark":
            assert used != "semantic_matcher", (
                f"REGRESSIE: 'wat kan ik?' wordt nog steeds door semantic_matcher "
                f"gecaptured als open_help_bark (used_model={used})"
            )


# ===========================================================================
# REGRESSIE A — semantic_matcher synoniemen blijven werken
# ===========================================================================
class TestSemanticMatcherRegression:
    def test_rps_synoniem_potje_sps(self):
        data = _post_compose("doe een potje sps", ADMIN_USER, "iter39-A-rps-1", timeout=20)
        assert data.get("action") == "open_game_rps", data
        assert data.get("used_model") == "semantic_matcher", data

    def test_tts_synoniem(self):
        data = _post_compose("zet je stem maar aan", ADMIN_USER, "iter39-A-tts-1", timeout=20)
        assert data.get("action") == "enable_tts", data
        assert data.get("used_model") == "semantic_matcher", data

    def test_no_false_positive_filosofie(self):
        data = _post_compose("wat is filosofie?", ADMIN_USER, "iter39-A-neg-1", timeout=90)
        action = data.get("action")
        assert action in (None, ""), f"unexpected action: {action}"
        used = (data.get("used_model") or "").lower()
        assert used != "semantic_matcher", data


# ===========================================================================
# REGRESSIE — exact help-trigger + multi-turn memory + privacy
# ===========================================================================
class TestCriticalRegressions:
    def test_help_exact_blijft_smart_intents(self):
        data = _post_compose("help", ADMIN_USER, "iter39-reg-help", timeout=20)
        assert data.get("action") == "open_help_bark", data
        assert data.get("used_model") == "smart_intents_service", \
            f"expected smart_intents_service, got {data.get('used_model')}"

    def test_multi_turn_memory_persistence(self):
        session_id = "iter39-mem"
        fp = TURNS_DIR / f"{session_id}.json"
        if fp.exists():
            fp.unlink()
        data = _post_compose("doe een potje sps", ADMIN_USER, session_id, timeout=20)
        assert data.get("action") == "open_game_rps"
        time.sleep(0.5)
        assert fp.exists(), f"turns_dir log missing: {fp}"
        log = json.loads(fp.read_text())
        msgs = log.get("messages", [])
        assert len(msgs) >= 2, f"expected >=2 messages, got {len(msgs)}: {msgs}"
        roles = [m.get("role") for m in msgs[-2:]]
        assert "user" in roles, roles
        assert any(r in ("spark", "assistant") for r in roles), roles

    def test_no_prive_leak_zus_for_guest_user(self):
        """user-672f0e5c (gradatie 7) — vragen over 'mijn zus' mag NIET Maaike noemen."""
        data = _post_compose(
            "wie is mijn zus?",
            GUEST_USER,
            "iter39-priv-1",
            timeout=90,
        )
        msg = (data.get("message") or "").lower()
        assert "maaike" not in msg, f"PRIVACY LEAK 'Maaike' in response: {msg[:300]}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
