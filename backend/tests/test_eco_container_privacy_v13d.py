"""Regressie: eco-container privacy per user voor agenda/dagboek/notes/tasks.

Willem sessie 55: "iedere user moet in zijn eigen eco-container". Bug: agenda,
dagboek en notes lieten iedereen elkanders data lezen via `GET /{user_id}`.

Fix: `require_access(viewer_id, target_user_id)` in `modules/core/privacy.py`.
"""
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import app  # noqa

client = TestClient(app)

WILLEM = "user-001"       # admin
GERBEN = "user-4d9b59aa"  # G2, familie, non-admin
MARIEKE = "user-c609d7d1"  # G3, kennis


class TestAgendaPrivacy:
    def test_gerben_cannot_view_willems_agenda(self):
        r = client.get(f"/api/agenda/events/{WILLEM}", params={"viewer_id": GERBEN})
        assert r.status_code == 403

    def test_willem_can_view_own_agenda(self):
        r = client.get(f"/api/agenda/events/{WILLEM}", params={"viewer_id": WILLEM})
        assert r.status_code == 200

    def test_admin_can_view_any_agenda(self):
        r = client.get(f"/api/agenda/events/{GERBEN}", params={"viewer_id": WILLEM})
        assert r.status_code == 200


class TestDagboekPrivacy:
    def test_gerben_cannot_view_willems_dagboek(self):
        r = client.get(f"/api/dagboek/entries/{WILLEM}", params={"viewer_id": GERBEN})
        assert r.status_code == 403

    def test_marieke_cannot_view_willems_dagboek(self):
        r = client.get(f"/api/dagboek/entries/{WILLEM}", params={"viewer_id": MARIEKE})
        assert r.status_code == 403

    def test_willem_can_view_own_dagboek(self):
        r = client.get(f"/api/dagboek/entries/{WILLEM}", params={"viewer_id": WILLEM})
        assert r.status_code == 200


class TestNotesPrivacy:
    def test_gerben_cannot_view_willems_notes(self):
        r = client.get("/api/notes/all", params={"user_id": WILLEM, "viewer_id": GERBEN})
        assert r.status_code == 403

    def test_gerben_cannot_view_willems_tasks(self):
        r = client.get("/api/notes/tasks", params={"user_id": WILLEM, "viewer_id": GERBEN})
        assert r.status_code == 403

    def test_own_notes_ok(self):
        r = client.get("/api/notes/all", params={"user_id": GERBEN, "viewer_id": GERBEN})
        assert r.status_code == 200


class TestBackwardsCompat:
    """Bestaande frontend-calls zonder viewer_id moeten blijven werken."""
    def test_agenda_no_viewer_id_falls_back(self):
        r = client.get(f"/api/agenda/events/{WILLEM}")
        assert r.status_code == 200

    def test_dagboek_no_viewer_id_falls_back(self):
        r = client.get(f"/api/dagboek/entries/{WILLEM}")
        assert r.status_code == 200

    def test_notes_no_viewer_id_falls_back(self):
        r = client.get("/api/notes/all", params={"user_id": WILLEM})
        assert r.status_code == 200
