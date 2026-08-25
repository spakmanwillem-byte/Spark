"""
v13d_agenda_uren_registratie_001 (sessie 56b) — Test dat agenda events
scope (prive/zakelijk) + uren-registratie velden correct opslaan en
totaal_uren automatisch berekenen.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

TEST_USER = "user-agenda-test"


def _cleanup():
    p = Path("/app/backend/data/agenda") / f"{TEST_USER}.json"
    if p.exists():
        p.unlink()


def setup_module(m):
    _cleanup()


def teardown_module(m):
    _cleanup()


def test_create_prive_backwards_compat():
    """Bestaande frontends zonder scope → default prive, geen uren-velden."""
    res = client.post(f"/api/agenda/events/{TEST_USER}", json={
        "titel": "Verjaardag Marieke",
        "date": "2026-03-01T14:00:00",
    })
    assert res.status_code == 200
    ev = res.json()["event"]
    assert ev["scope"] == "prive"
    assert ev["totaal_uren"] is None
    assert ev["opdrachtgever"] is None
    assert ev["pauze_minuten"] is None


def test_create_zakelijk_met_uren_registratie():
    """Zakelijk event met start/eind/pauze → totaal_uren = 7.5."""
    res = client.post(f"/api/agenda/events/{TEST_USER}", json={
        "titel": "Klus bij De Zorgboerderij",
        "date": "2026-03-02T09:00:00",
        "end_date": "2026-03-02T17:00:00",
        "pauze_minuten": 30,
        "scope": "zakelijk",
        "opdrachtgever": "De Zorgboerderij",
        "onderwerp": "Tuinonderhoud",
    })
    assert res.status_code == 200
    ev = res.json()["event"]
    assert ev["scope"] == "zakelijk"
    assert ev["opdrachtgever"] == "De Zorgboerderij"
    assert ev["onderwerp"] == "Tuinonderhoud"
    assert ev["pauze_minuten"] == 30
    # 8 uur - 30 min = 7.5 uur
    assert ev["totaal_uren"] == 7.5


def test_zakelijk_zonder_end_date_geeft_geen_uren():
    """Zonder end_date kan totaal_uren niet berekend worden."""
    res = client.post(f"/api/agenda/events/{TEST_USER}", json={
        "titel": "Bel Kees",
        "date": "2026-03-03T10:00:00",
        "scope": "zakelijk",
        "opdrachtgever": "Kees",
    })
    assert res.status_code == 200
    ev = res.json()["event"]
    assert ev["scope"] == "zakelijk"
    assert ev["totaal_uren"] is None


def test_prive_negeert_zakelijk_velden():
    """Zakelijk-velden meesturen bij scope=prive worden genegeerd."""
    res = client.post(f"/api/agenda/events/{TEST_USER}", json={
        "titel": "Tandarts",
        "date": "2026-03-04T11:00:00",
        "scope": "prive",
        "opdrachtgever": "Moet weg",
        "pauze_minuten": 60,
    })
    assert res.status_code == 200
    ev = res.json()["event"]
    assert ev["scope"] == "prive"
    assert ev["opdrachtgever"] is None
    assert ev["pauze_minuten"] is None


def test_update_zakelijk_herberekent_totaal_uren():
    """PUT die pauze wijzigt moet totaal_uren opnieuw berekenen."""
    # Aanmaken
    res = client.post(f"/api/agenda/events/{TEST_USER}", json={
        "titel": "Werk",
        "date": "2026-03-05T09:00:00",
        "end_date": "2026-03-05T13:00:00",
        "pauze_minuten": 0,
        "scope": "zakelijk",
    })
    ev = res.json()["event"]
    assert ev["totaal_uren"] == 4.0

    # Pauze naar 60 min
    res2 = client.put(f"/api/agenda/events/{TEST_USER}/{ev['id']}", json={
        "pauze_minuten": 60,
    })
    assert res2.status_code == 200
    ev2 = res2.json()["event"]
    assert ev2["totaal_uren"] == 3.0


def test_chat_intent_zakelijk_detectie():
    """Chat-parser herkent 'zakelijk' + 'voor <Naam>' → scope=zakelijk."""
    from modules.chat.agenda_intent_service import _extract_zakelijk_fields
    scope, opd, pauze, onderwerp = _extract_zakelijk_fields(
        "Ik heb morgen zakelijk gewerkt voor De Zorgboerderij van 9 tot 17 met een uur pauze"
    )
    assert scope == "zakelijk"
    assert opd == "De Zorgboerderij"
    assert pauze == 60


def test_chat_intent_prive_default():
    """Chat zonder trigger-woorden → scope=prive."""
    from modules.chat.agenda_intent_service import _extract_zakelijk_fields
    scope, opd, pauze, onderwerp = _extract_zakelijk_fields(
        "Morgen tandarts om 10 uur"
    )
    assert scope == "prive"
    assert opd is None
    assert pauze is None
