"""Regressie: boekhouder privacy + auto-privé-book (v13d_boekhouder_admin_leak_001).

Willem's productie-bug sessie 55: 'Gerben (G2) zag mijn kasboek'.
Root cause: `_is_admin` behandelde iedereen met gradatie<=2 als admin.
G2 is familie, geen admin — mag alleen eigen books zien + Spark Core.
"""
from pathlib import Path
import json
import shutil
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import app  # noqa

client = TestClient(app)
BOOKS_ROOT = Path(__file__).parent.parent / "data" / "boekhouding" / "books"


def _cleanup_prive_book(user_id: str):
    """Verwijder auto-gegenereerd privé-book na test."""
    for d in BOOKS_ROOT.glob("book-*"):
        meta_fp = d / "_meta.json"
        if not meta_fp.exists():
            continue
        m = json.loads(meta_fp.read_text())
        if m.get("owner_user_id") == user_id and m.get("type") == "user_prive":
            shutil.rmtree(d, ignore_errors=True)


class TestBoekhouderPrivacy:
    def test_g2_family_is_not_admin(self):
        """Gerben (G2) mag NIET admin zijn en niet alle books zien."""
        # Gerben: user-4d9b59aa, gradatie=2, admin=None
        r = client.get("/api/boekhouding/books", params={"viewer_id": "user-4d9b59aa"})
        assert r.status_code == 200
        books = r.json()["books"]
        owners = {b["owner_user_id"] for b in books}
        # Mag alleen Gerben zelf + system (user-000) zien
        assert owners.issubset({"user-4d9b59aa", "user-000"}), (
            f"Gerben ziet illegal books van: {owners - {'user-4d9b59aa', 'user-000'}}"
        )
        # Mag GEEN willem-books zien
        assert "user-001" not in owners
        _cleanup_prive_book("user-4d9b59aa")

    def test_g3_kennis_ziet_geen_admin_books(self):
        """Marieke (G3) idem."""
        r = client.get("/api/boekhouding/books", params={"viewer_id": "user-c609d7d1"})
        books = r.json()["books"]
        owners = {b["owner_user_id"] for b in books}
        assert "user-001" not in owners
        _cleanup_prive_book("user-c609d7d1")

    def test_admin_ziet_alles(self):
        """Willem (admin=True) ziet ALLE books."""
        r = client.get("/api/boekhouding/books", params={"viewer_id": "user-001"})
        books = r.json()["books"]
        owners = {b["owner_user_id"] for b in books}
        assert "user-001" in owners  # eigen books
        assert "user-000" in owners  # system

    def test_auto_prive_book_created_on_first_visit(self):
        """Bij eerste GET voor user zonder privé-book → automatisch aangemaakt."""
        _cleanup_prive_book("user-4d9b59aa")  # ensure clean
        r = client.get("/api/boekhouding/books", params={"viewer_id": "user-4d9b59aa"})
        books = r.json()["books"]
        prive = [b for b in books if b["type"] == "user_prive" and b["owner_user_id"] == "user-4d9b59aa"]
        assert len(prive) == 1
        assert "Gerben" in prive[0]["naam"]
        _cleanup_prive_book("user-4d9b59aa")

    def test_second_visit_does_not_duplicate(self):
        """Twee keer GET mag geen dubbel privé-book maken."""
        _cleanup_prive_book("user-4d9b59aa")
        client.get("/api/boekhouding/books", params={"viewer_id": "user-4d9b59aa"})
        r2 = client.get("/api/boekhouding/books", params={"viewer_id": "user-4d9b59aa"})
        books = r2.json()["books"]
        prive = [b for b in books if b["type"] == "user_prive" and b["owner_user_id"] == "user-4d9b59aa"]
        assert len(prive) == 1, f"Duplicated: {[b['id'] for b in prive]}"
        _cleanup_prive_book("user-4d9b59aa")
