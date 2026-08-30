"""Batch-1 registry-uitbreiding: agenda + notes + bugs + help + triggers + kb_v2 admin.

Voegt 37 entries toe aan command_registry.json met correcte intent_tags,
gradatie_min en admin_only. Idempotent — bestaande cmd_id's worden overgeslagen.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402

REGISTRY = Path(__file__).parent.parent / "data" / "system" / "command_registry.json"

ENTRIES = [
    # -------- AGENDA (9) --------
    {"id": "cap_agenda_events_list", "path": "/api/agenda/events/{user_id}", "method": "GET",
     "intent_tags": ["agenda", "afspraken", "kalender", "overzicht", "planning", "bekijken"],
     "required_params": ["user_id"], "gradatie_min": 2, "behavior_class_hint": "informatief-functioneel",
     "source": "agenda.routes.get_events"},
    {"id": "cap_agenda_event_create", "path": "/api/agenda/events/{user_id}", "method": "POST",
     "intent_tags": ["agenda", "afspraak", "plannen", "toevoegen", "aanmaken", "inplannen"],
     "required_params": ["user_id"], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "agenda.routes.create_event"},
    {"id": "cap_agenda_event_update", "path": "/api/agenda/events/{user_id}/{event_id}", "method": "PUT",
     "intent_tags": ["agenda", "afspraak", "wijzigen", "aanpassen", "bewerken"],
     "required_params": ["user_id", "event_id"], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "agenda.routes.update_event"},
    {"id": "cap_agenda_event_delete", "path": "/api/agenda/events/{user_id}/{event_id}", "method": "DELETE",
     "intent_tags": ["agenda", "afspraak", "verwijderen", "annuleren", "weghalen"],
     "required_params": ["user_id", "event_id"], "gradatie_min": 3, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "agenda.routes.delete_event"},
    {"id": "cap_agenda_archive_list", "path": "/api/agenda/archive/{user_id}", "method": "GET",
     "intent_tags": ["agenda", "archief", "verleden", "historie", "bekijken"],
     "required_params": ["user_id"], "gradatie_min": 3, "behavior_class_hint": "informatief-functioneel",
     "source": "agenda.routes.get_archive"},
    {"id": "cap_agenda_archive_month", "path": "/api/agenda/archive/{user_id}/{month}", "method": "GET",
     "intent_tags": ["agenda", "archief", "maand", "verleden", "bekijken"],
     "required_params": ["user_id", "month"], "gradatie_min": 3, "behavior_class_hint": "informatief-functioneel",
     "source": "agenda.routes.get_archive_month"},
    {"id": "cap_agenda_archive_now_all", "path": "/api/agenda/archive-now", "method": "POST",
     "intent_tags": ["agenda", "archiveren", "afsluiten", "onderhoud", "opruimen"],
     "required_params": [], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "agenda.routes.archive_now_all"},
    {"id": "cap_agenda_archive_now_user", "path": "/api/agenda/archive-now/{user_id}", "method": "POST",
     "intent_tags": ["agenda", "archiveren", "afsluiten", "onderhoud"],
     "required_params": ["user_id"], "gradatie_min": 4, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "agenda.routes.archive_now_user"},
    {"id": "cap_agenda_uren_rapport", "path": "/api/agenda/uren-rapport/{user_id}", "method": "GET",
     "intent_tags": ["agenda", "uren", "rapport", "totaal", "overzicht", "bekijken"],
     "required_params": ["user_id"], "gradatie_min": 3, "behavior_class_hint": "informatief-functioneel",
     "source": "agenda.routes.uren_rapport"},

    # -------- NOTES (7 missen — /tasks bestaat al als cap_taken_lijst) --------
    {"id": "cap_notes_list_all", "path": "/api/notes/all", "method": "GET",
     "intent_tags": ["notities", "aantekeningen", "notes", "lijst", "bekijken", "overzicht"],
     "required_params": [], "gradatie_min": 2, "behavior_class_hint": "informatief-functioneel",
     "source": "notes.routes.list_all"},
    {"id": "cap_notes_create", "path": "/api/notes/create", "method": "POST",
     "intent_tags": ["notitie", "aantekening", "opschrijven", "onthouden", "toevoegen", "aanmaken"],
     "required_params": [], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "notes.routes.create_note"},
    {"id": "cap_notes_update", "path": "/api/notes/update/{note_id}", "method": "PUT",
     "intent_tags": ["notitie", "aanpassen", "wijzigen", "bewerken"],
     "required_params": ["note_id"], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "notes.routes.update_note"},
    {"id": "cap_notes_delete", "path": "/api/notes/delete/{note_id}", "method": "DELETE",
     "intent_tags": ["notitie", "verwijderen", "weghalen"],
     "required_params": ["note_id"], "gradatie_min": 3, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "notes.routes.delete_note"},
    {"id": "cap_notes_task_create", "path": "/api/notes/tasks/create", "method": "POST",
     "intent_tags": ["taak", "todo", "opdracht", "toevoegen", "aanmaken", "inplannen"],
     "required_params": [], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "notes.routes.create_task"},
    {"id": "cap_notes_task_update", "path": "/api/notes/tasks/update/{task_id}", "method": "PUT",
     "intent_tags": ["taak", "todo", "aanpassen", "wijzigen", "afvinken"],
     "required_params": ["task_id"], "gradatie_min": 2, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "notes.routes.update_task"},
    {"id": "cap_notes_task_delete", "path": "/api/notes/tasks/delete/{task_id}", "method": "DELETE",
     "intent_tags": ["taak", "todo", "verwijderen", "weghalen"],
     "required_params": ["task_id"], "gradatie_min": 3, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "notes.routes.delete_task"},

    # -------- BUGS (5) --------
    {"id": "cap_bug_report", "path": "/api/bugs/create", "method": "POST",
     "intent_tags": ["bug", "fout", "melden", "rapporteren", "probleem", "aanmaken"],
     "required_params": [], "gradatie_min": 1, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "bugs.routes.create_bug"},
    {"id": "cap_bug_list_all", "path": "/api/bugs/list", "method": "GET",
     "intent_tags": ["bugs", "meldingen", "lijst", "overzicht", "bekijken"],
     "required_params": [], "gradatie_min": 4, "admin_only": True, "behavior_class_hint": "informatief-functioneel",
     "source": "bugs.routes.list_all"},
    {"id": "cap_bug_mine", "path": "/api/bugs/mine", "method": "GET",
     "intent_tags": ["bugs", "mijn", "eigen", "meldingen", "bekijken"],
     "required_params": [], "gradatie_min": 2, "behavior_class_hint": "informatief-functioneel",
     "source": "bugs.routes.mine"},
    {"id": "cap_bug_status_update", "path": "/api/bugs/{bug_id}/status", "method": "PATCH",
     "intent_tags": ["bug", "status", "wijzigen", "aanpassen"],
     "required_params": ["bug_id"], "gradatie_min": 4, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "bugs.routes.update_status"},
    {"id": "cap_bug_delete", "path": "/api/bugs/{bug_id}", "method": "DELETE",
     "intent_tags": ["bug", "verwijderen", "weghalen"],
     "required_params": ["bug_id"], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "bugs.routes.delete_bug"},

    # -------- HELP (3) --------
    {"id": "cap_help_for_viewer", "path": "/api/help/for-viewer", "method": "GET",
     "intent_tags": ["help", "uitleg", "hulp", "handleiding", "bekijken"],
     "required_params": [], "gradatie_min": 1, "behavior_class_hint": "informatief-functioneel",
     "source": "help.routes.for_viewer"},
    {"id": "cap_help_find", "path": "/api/help/find", "method": "POST",
     "intent_tags": ["help", "zoeken", "vinden", "hulp", "vraag"],
     "required_params": [], "gradatie_min": 1, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "help.routes.find_topic"},
    {"id": "cap_help_topic", "path": "/api/help/topic/{topic_id}", "method": "GET",
     "intent_tags": ["help", "onderwerp", "uitleg", "detail", "bekijken"],
     "required_params": ["topic_id"], "gradatie_min": 1, "behavior_class_hint": "informatief-functioneel",
     "source": "help.routes.get_topic"},

    # -------- TRIGGERS (8) --------
    {"id": "cap_triggers_all", "path": "/api/triggers/all", "method": "GET",
     "intent_tags": ["triggers", "lijst", "overzicht", "bekijken", "systeem"],
     "required_params": [], "gradatie_min": 4, "admin_only": True, "behavior_class_hint": "informatief-functioneel",
     "source": "triggers.routes.all_triggers"},
    {"id": "cap_triggers_intent_patterns", "path": "/api/triggers/intent-patterns", "method": "GET",
     "intent_tags": ["triggers", "intent", "patronen", "bekijken"],
     "required_params": [], "gradatie_min": 4, "admin_only": True, "behavior_class_hint": "informatief-functioneel",
     "source": "triggers.routes.intent_patterns"},
    {"id": "cap_triggers_intent_add", "path": "/api/triggers/edit/intent/{intent_key}/add", "method": "POST",
     "intent_tags": ["triggers", "intent", "toevoegen", "patroon", "leren"],
     "required_params": ["intent_key"], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "triggers.routes.intent_pattern_add"},
    {"id": "cap_triggers_intent_remove", "path": "/api/triggers/edit/intent/{intent_key}/pattern", "method": "DELETE",
     "intent_tags": ["triggers", "intent", "verwijderen", "patroon"],
     "required_params": ["intent_key"], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "triggers.routes.intent_pattern_remove"},
    {"id": "cap_triggers_intent_test", "path": "/api/triggers/intent-patterns/test", "method": "POST",
     "intent_tags": ["triggers", "intent", "testen", "controleren", "matchen"],
     "required_params": [], "gradatie_min": 4, "behavior_class_hint": "informatief-functioneel",
     "source": "triggers.routes.intent_test"},
    {"id": "cap_triggers_by_type", "path": "/api/triggers/by-type/{trigger_type}", "method": "GET",
     "intent_tags": ["triggers", "type", "filteren", "bekijken"],
     "required_params": ["trigger_type"], "gradatie_min": 4, "admin_only": True, "behavior_class_hint": "informatief-functioneel",
     "source": "triggers.routes.by_type"},
    {"id": "cap_triggers_edit_add", "path": "/api/triggers/edit/{kind}/{key}/add", "method": "POST",
     "intent_tags": ["triggers", "toevoegen", "woord", "patroon", "leren"],
     "required_params": ["kind", "key"], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "exploreren-uitbreiden",
     "source": "triggers.routes.edit_add_word"},
    {"id": "cap_triggers_edit_remove", "path": "/api/triggers/edit/{kind}/{key}/{field}/{word}", "method": "DELETE",
     "intent_tags": ["triggers", "verwijderen", "woord"],
     "required_params": ["kind", "key", "field", "word"], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "triggers.routes.edit_remove_word"},

    # -------- KB v2 admin (5 die al bestaan als route) --------
    {"id": "cap_kb_dedupe_inbox", "path": "/api/kb/v2/admin/dedupe-inbox", "method": "POST",
     "intent_tags": ["kb", "inbox", "dedupe", "opschonen", "onderhoud", "duplicaten"],
     "required_params": [], "optional_params": ["dry_run"], "gradatie_min": 5, "admin_only": True,
     "behavior_class_hint": "vertragen-ondersteunen", "source": "kb_v2.routes.admin_dedupe_inbox"},
    {"id": "cap_kb_rebuild_index", "path": "/api/kb/v2/admin/rebuild-index", "method": "POST",
     "intent_tags": ["kb", "index", "rebuild", "herbouwen", "onderhoud", "opnieuw"],
     "required_params": [], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "kb_v2.routes.admin_rebuild_index"},
    {"id": "cap_kb_verbanden_rebuild", "path": "/api/kb/v2/admin/verbanden/rebuild-all", "method": "POST",
     "intent_tags": ["kb", "verbanden", "connecties", "rebuild", "herberekenen", "onderhoud"],
     "required_params": [], "gradatie_min": 5, "admin_only": True, "behavior_class_hint": "vertragen-ondersteunen",
     "source": "kb_v2.routes.admin_verbanden_rebuild_all"},
    {"id": "cap_kb_sync_v1_drift", "path": "/api/kb/v2/admin/sync-v1-drift", "method": "POST",
     "intent_tags": ["kb", "sync", "drift", "v1", "migreren", "onderhoud"],
     "required_params": [], "optional_params": ["dry_run"], "gradatie_min": 5, "admin_only": True,
     "behavior_class_hint": "vertragen-ondersteunen", "source": "kb_v2.routes.admin_sync_v1_drift"},
    {"id": "cap_kb_orphan_tag_scan", "path": "/api/kb/v2/inbox/orphan-tag-scan", "method": "POST",
     "intent_tags": ["kb", "orphan", "tags", "scannen", "opschonen", "onderhoud"],
     "required_params": [], "optional_params": ["dry_run"], "gradatie_min": 5, "admin_only": True,
     "behavior_class_hint": "vertragen-ondersteunen", "source": "kb_v2.routes.orphan_tag_scan"},

    # -------- COMMANDS/LIST (nieuwe route, zie routes) --------
    {"id": "cap_commands_list", "path": "/api/commands/list", "method": "GET",
     "intent_tags": ["commando", "commandos", "commando's", "lijst", "capaciteiten", "wat", "ken", "je", "kunnen", "acties"],
     "required_params": [], "optional_params": ["module", "admin_only", "gradatie_max", "q"],
     "gradatie_min": 1, "behavior_class_hint": "informatief-functioneel",
     "source": "system.commands_list_routes.list_commands"},
]


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = REGISTRY.with_suffix(REGISTRY.suffix + f".bak_batch1_{ts}")
    shutil.copy2(REGISTRY, bak)
    print(f"backup: {bak.name}")

    data = load_json(REGISTRY, default={"commands": []})
    existing = {c.get("id") for c in data.get("commands", [])}
    added = skipped = 0
    for entry in ENTRIES:
        if entry["id"] in existing:
            skipped += 1
            continue
        data["commands"].append(entry)
        added += 1
    data["last_updated"] = now
    save_json(REGISTRY, data)
    print(f"toegevoegd: {added}, overgeslagen (al aanwezig): {skipped}")
    print(f"totaal commands nu: {len(data['commands'])}")


if __name__ == "__main__":
    main()
