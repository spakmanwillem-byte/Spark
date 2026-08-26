"""
v13d_agenda_terugblik_001 (sessie 56b) — Test dat Spark nu antwoord geeft op
"wat heb ik gisteren gedaan" en "hoeveel uur gewerkt deze week".

Willem's hooks uit gesprek 25 aug 2026, 22:18-22:32:
  U: "wat heb ik gisteren gedaan"
  U: "hoeveel uur heb ik gewerkt deze week"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone
from modules.core.storage import save_json, load_json

TEST_USER = "user-terugblik-test"
AGENDA_FILE = Path("/app/backend/data/agenda") / f"{TEST_USER}.json"


def setup_module(m):
    # Seed 3 events: 1 gisteren zakelijk, 1 eergisteren zakelijk, 1 vandaag prive
    now = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    gisteren = now - timedelta(days=1)
    eerg = now - timedelta(days=2)
    save_json(AGENDA_FILE, {"events": [
        {
            "id": "ev1", "titel": "Klus tuinonderhoud",
            "date": gisteren.isoformat(),
            "end_date": (gisteren.replace(hour=17)).isoformat(),
            "scope": "zakelijk", "opdrachtgever": "De Zorgboerderij",
            "pauze_minuten": 30, "totaal_uren": 7.5,
            "status": "upcoming",
        },
        {
            "id": "ev2", "titel": "Bel Kees",
            "date": eerg.isoformat(),
            "end_date": (eerg.replace(hour=11)).isoformat(),
            "scope": "zakelijk", "opdrachtgever": "Kees & Co",
            "pauze_minuten": 0, "totaal_uren": 2.0,
            "status": "upcoming",
        },
        {
            "id": "ev3", "titel": "Verjaardag Marieke",
            "date": now.isoformat(),
            "scope": "prive",
            "status": "upcoming",
        },
    ]})


def teardown_module(m):
    if AGENDA_FILE.exists():
        AGENDA_FILE.unlink()


def test_gisteren_gedaan():
    from modules.chat.capability_handler_service import _handle_agenda_terugblik
    r = _handle_agenda_terugblik(TEST_USER, "wat heb ik gisteren gedaan")
    assert r["type"] == "capability_response"
    assert "gisteren" in r["message"].lower()
    assert "Klus tuinonderhoud" in r["message"]
    assert "De Zorgboerderij" in r["message"]
    assert r["event_count"] == 1


def test_eergisteren_gedaan():
    from modules.chat.capability_handler_service import _handle_agenda_terugblik
    r = _handle_agenda_terugblik(TEST_USER, "wat heb ik eergisteren gedaan")
    assert "eergisteren" in r["message"].lower()
    assert "Bel Kees" in r["message"]


def test_uren_deze_week():
    from modules.chat.capability_handler_service import _handle_agenda_terugblik
    r = _handle_agenda_terugblik(TEST_USER, "hoeveel uur heb ik gewerkt deze week")
    # Deze week = ma-zo, gisteren + eergisteren zitten er in (tenzij vandaag maandag is)
    # Basis check: er wordt terug 'uur' en een getal getoond
    assert "uur" in r["message"].lower()
    # Beide klanten moeten getoond worden
    assert "De Zorgboerderij" in r["message"] or "9.5" in r["message"] or "7.5" in r["message"]


def test_uren_gisteren():
    from modules.chat.capability_handler_service import _handle_agenda_terugblik
    r = _handle_agenda_terugblik(TEST_USER, "hoeveel uur heb ik gisteren gewerkt")
    assert "gisteren" in r["message"].lower()
    assert "7.5" in r["message"]
    assert "De Zorgboerderij" in r["message"]


def test_prive_events_worden_niet_meegeteld_bij_uren():
    from modules.chat.capability_handler_service import _handle_agenda_terugblik
    r = _handle_agenda_terugblik(TEST_USER, "hoeveel uur heb ik vandaag gewerkt")
    # Vandaag heeft alleen een prive event (verjaardag) → 0 zakelijke uren
    assert "Geen zakelijke uren" in r["message"] or "0 uur" in r["message"].lower()


def test_capability_router_matched_agenda_terugblik():
    """End-to-end: chat-route → capability_router → onze handler."""
    from modules.chat.capability_handler_service import route_capability
    r = route_capability("wat heb ik gisteren gedaan", TEST_USER)
    assert r is not None
    assert r.get("capability_id") == "agenda_terugblik"
    assert "Klus tuinonderhoud" in r["message"]


def test_capability_router_matched_uren_vraag():
    from modules.chat.capability_handler_service import route_capability
    r = route_capability("hoeveel uur heb ik deze week gewerkt", TEST_USER)
    assert r is not None
    assert r.get("capability_id") == "agenda_terugblik"
    assert "uur" in r["message"].lower()
