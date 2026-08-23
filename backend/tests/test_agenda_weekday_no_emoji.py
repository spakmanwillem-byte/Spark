"""
v13c_agenda_weekdays_001 + no-emoji-no-fake-tool regression tests
Test session 54 — Willem's production bug fixes.
"""
import os
import re
import time
import pytest
import requests
from pathlib import Path

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL"):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = _load_backend_url()
USER_ID = "user-001"

# Regex om fake tool-syntax te detecteren
FAKE_TOOL_RX = re.compile(r"(\[[a-z_]+\s*[—-]\s)|(⚙️)|(agenda_lezen)", re.IGNORECASE)

# Emoji-detectie (Unicode ranges voor emoji)
EMOJI_RX = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"  # miscellaneous symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F004-\U0001F0CF"
    "]+",
    flags=re.UNICODE,
)


def _post_chat(session_id: str, message: str, extra: dict | None = None) -> dict:
    payload = {"user_id": USER_ID, "session_id": session_id, "message": message}
    if extra:
        payload.update(extra)
    r = requests.post(f"{BASE_URL}/api/chat/message", json=payload, timeout=90)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:400]}"
    return r.json()


def _assert_no_fake_tool(msg: str):
    m = FAKE_TOOL_RX.search(msg or "")
    assert not m, f"Fake tool-syntax gevonden: {m.group(0)!r} in message: {msg!r}"


# ============== BUG 1 — Agenda weekday intent ==============

class TestAgendaWeekdayIntent:
    def test_dinsdag_returns_agenda(self):
        data = _post_chat("test-agenda-weekday-1", "wat staat er voor dinsdag")
        msg = data.get("message", "")
        rtype = data.get("type", "")
        print(f"[dinsdag] type={rtype} msg={msg[:300]}")
        assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type: {rtype}"
        _assert_no_fake_tool(msg)

    def test_aanstaande_dinsdag_afspraak(self):
        data = _post_chat(
            "test-agenda-weekday-2",
            "zou jij mijn afspraak van aanstaande dinsdag uit de agenda willen halen",
        )
        msg = data.get("message", "")
        rtype = data.get("type", "")
        print(f"[aanstaande dinsdag] type={rtype} msg={msg[:300]}")
        assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type: {rtype}"
        _assert_no_fake_tool(msg)

    def test_vrijdag_fallback(self):
        data = _post_chat("test-agenda-weekday-3", "wat staat er voor vrijdag")
        msg = data.get("message", "")
        rtype = data.get("type", "")
        print(f"[vrijdag] type={rtype} msg={msg[:300]}")
        assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type: {rtype}"
        _assert_no_fake_tool(msg)


# ============== BUG 2 — Geen fake tool-syntax in vrije chat ==============

class TestNoFakeToolSyntax:
    def test_volgende_week_no_fake_tool(self):
        data = _post_chat(
            "test-no-fake-tool-1", "kun je even in mijn agenda kijken naar volgende week"
        )
        msg = data.get("message", "")
        rtype = data.get("type", "")
        print(f"[volgende week] type={rtype} msg={msg[:400]}")
        _assert_no_fake_tool(msg)


# ============== BUG 2b — Geen emoji in LLM antwoord ==============

class TestNoEmojiInLLM:
    def test_hoi_spark_no_emoji(self):
        # 'diep' modus toggle — probeer verschillende parameter-namen
        data = _post_chat(
            "test-no-emoji-1",
            "hoi Spark, hoe gaat het",
            extra={"mode": "diep", "deep_mode": True},
        )
        msg = data.get("message", "")
        rtype = data.get("type", "")
        print(f"[hoi spark] type={rtype} msg={msg!r}")

        # Alleen checken als het echt LLM-output is (niet capability/agenda fastpath)
        if rtype in ("agenda_overview", "capability_response"):
            pytest.skip(f"Fastpath type={rtype}, emoji check niet relevant")
            return

        emojis = EMOJI_RX.findall(msg or "")
        assert not emojis, f"Emoji gevonden in LLM antwoord: {emojis} — hele message: {msg!r}"


# ============== REGRESSIE — vandaag/morgen blijft werken ==============

class TestRegressionTodayTomorrow:
    def test_vandaag_still_agenda(self):
        data = _post_chat("test-regr-vandaag", "wat staat er vandaag")
        rtype = data.get("type", "")
        msg = data.get("message", "")
        print(f"[vandaag] type={rtype}")
        assert rtype == "agenda_overview", f"Regressie: vandaag geeft type={rtype}"
        _assert_no_fake_tool(msg)

    def test_morgen_still_agenda(self):
        data = _post_chat("test-regr-morgen", "wat staat er morgen")
        rtype = data.get("type", "")
        msg = data.get("message", "")
        print(f"[morgen] type={rtype}")
        assert rtype == "agenda_overview", f"Regressie: morgen geeft type={rtype}"
        _assert_no_fake_tool(msg)
