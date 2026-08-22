"""
Regression test voor v13_roles_array_001 — Zorgboerderij foundation.

Zorgt dat een persoon meerdere rollen tegelijk kan hebben (bv. vriend + cliënt)
zonder dat oude entries breken (backwards-compat via `relation_type`).
"""
from pathlib import Path
import json
import shutil
import tempfile
import pytest


@pytest.fixture
def temp_persons_dir(monkeypatch):
    """Isoleer tests van productie-data door PERSONS_DIR te patchen."""
    tmpdir = Path(tempfile.mkdtemp(prefix="test_roles_"))
    from modules.chat import relation_extraction_service as res
    monkeypatch.setattr(res, "PERSONS_DIR", tmpdir)
    monkeypatch.setattr(res, "DATA_DIR", tmpdir.parent)
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_new_person_gets_roles_array(temp_persons_dir):
    from modules.chat.relation_extraction_service import detect_and_save, get_roles

    detect_and_save("user-test", "Roeline is mijn vriendin")
    roles = get_roles("user-test", "Roeline")

    assert roles == ["vriend"], f"Expected ['vriend'], got {roles}"


def test_second_role_appends_not_duplicates(temp_persons_dir):
    from modules.chat.relation_extraction_service import detect_and_save, get_roles

    detect_and_save("user-test", "Roeline is mijn vriendin")
    detect_and_save("user-test", "Roeline is ook mijn cliënt")

    roles = get_roles("user-test", "Roeline")
    assert "vriend" in roles
    assert "professioneel/cliënt" in roles
    assert len(roles) == 2


def test_idempotent_duplicate_role(temp_persons_dir):
    from modules.chat.relation_extraction_service import detect_and_save, get_roles

    detect_and_save("user-test", "Roeline is mijn vriendin")
    detect_and_save("user-test", "Roeline is mijn vriendin")  # dubbel

    roles = get_roles("user-test", "Roeline")
    assert roles == ["vriend"]


def test_has_role_matches_short_and_full(temp_persons_dir):
    from modules.chat.relation_extraction_service import detect_and_save, has_role

    detect_and_save("user-test", "Roeline is ook mijn cliënt")

    # Beide match-vormen moeten werken
    assert has_role("user-test", "Roeline", "cliënt") is True
    assert has_role("user-test", "Roeline", "professioneel/cliënt") is True
    assert has_role("user-test", "Roeline", "medewerker") is False


def test_add_role_helper(temp_persons_dir):
    from modules.chat.relation_extraction_service import detect_and_save, add_role, get_roles

    detect_and_save("user-test", "Roeline is mijn vriendin")

    assert add_role("user-test", "Roeline", "medewerker") is True
    roles = get_roles("user-test", "Roeline")
    assert "professioneel/medewerker" in roles

    # Dubbele add = False
    assert add_role("user-test", "Roeline", "medewerker") is False


def test_migration_preserves_existing_data(temp_persons_dir):
    """Oude entry zonder roles-array moet backwards-compat werken."""
    from modules.chat.relation_extraction_service import (
        migrate_all_to_roles_array,
        get_roles,
    )

    # Schrijf oude-stijl entry (geen roles array)
    fp = temp_persons_dir / "user-test_relationships.json"
    fp.write_text(json.dumps({
        "user_id": "user-test",
        "relationships": [
            {
                "person_name": "Willie",
                "relation_type": "familie/vader",
                "knows_about_me": True,
                "notes": "Vader",
            }
        ]
    }), encoding="utf-8")

    stats = migrate_all_to_roles_array()
    assert stats["entries_migrated"] == 1

    roles = get_roles("user-test", "Willie")
    assert roles == ["familie/vader"]


def test_migration_is_idempotent(temp_persons_dir):
    from modules.chat.relation_extraction_service import (
        detect_and_save,
        migrate_all_to_roles_array,
    )

    detect_and_save("user-test", "Roeline is mijn vriendin")

    stats1 = migrate_all_to_roles_array()
    stats2 = migrate_all_to_roles_array()

    # Tweede run mag niks meer migreren
    assert stats2["entries_migrated"] == 0
    assert stats2["entries_ok"] >= 1
