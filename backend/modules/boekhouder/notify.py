"""v13_boekhouding_notify_001 — Hooks naar user notes/tasks + urgent glow.

Bij events zoals nieuwe factuur, deadline, SEPA-import verschijnt automatisch:
  - Notitie of taak in user's `notes/tasks` (met tag book_{book_id})
  - Urgent-item in `/data/urgent/` zodat de sidebar-tab glow krijgt
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
USERS_ROOT = DATA_ROOT / "users"
URGENT_ROOT = DATA_ROOT / "urgent"
URGENT_ROOT.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_task_for_book(
    owner_user_id: str,
    book_id: str,
    book_naam: str,
    titel: str,
    inhoud: str = "",
    deadline_iso: Optional[str] = None,
) -> Dict:
    """Voeg een taak toe aan de tasks van de owner."""
    tasks_fp = USERS_ROOT / owner_user_id / "tasks.json"
    tasks_fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(tasks_fp, default={"tasks": []})
    task = {
        "id": "task-" + secrets.token_hex(4),
        "titel": titel,
        "inhoud": inhoud,
        "status": "open",
        "created_at": _now(),
        "deadline": deadline_iso,
        "tags": [f"book_{book_id}", "boekhouding", book_naam.lower().replace(" ", "-")],
        "source": "boekhouding_hook",
        "book_id": book_id,
    }
    data.setdefault("tasks", []).append(task)
    save_json(tasks_fp, data)
    return task


def create_note_for_book(
    owner_user_id: str,
    book_id: str,
    book_naam: str,
    titel: str,
    inhoud: str = "",
) -> Dict:
    notes_fp = USERS_ROOT / owner_user_id / "notes.json"
    notes_fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(notes_fp, default={"notes": []})
    note = {
        "id": "note-" + secrets.token_hex(4),
        "titel": titel,
        "inhoud": inhoud,
        "created_at": _now(),
        "tags": [f"book_{book_id}", "boekhouding"],
        "source": "boekhouding_hook",
        "book_id": book_id,
    }
    data.setdefault("notes", []).append(note)
    save_json(notes_fp, data)
    return note


def push_urgent(owner_user_id: str, book_id: str, book_naam: str, titel: str, severity: str = "amber") -> Dict:
    """Voeg een urgent-item toe voor de sidebar-glow.
    severity: 'amber' (aandacht) / 'red' (nu)
    """
    fp = URGENT_ROOT / f"{owner_user_id}.json"
    data = load_json(fp, default={"items": []})
    item = {
        "id": "urg-" + secrets.token_hex(4),
        "producer": "boekhouding",
        "nav_id": "boekhouding",
        "severity": severity,
        "titel": titel,
        "book_id": book_id,
        "book_naam": book_naam,
        "created_at": _now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
    }
    data.setdefault("items", []).append(item)
    save_json(fp, data)
    return item


def on_new_invoice(book: Dict, invoice_naam: str, amount_eur: float, deadline_iso: Optional[str] = None) -> Dict:
    """Handige combi-hook voor 'nieuwe factuur binnen'."""
    task = create_task_for_book(
        owner_user_id=book["owner_user_id"],
        book_id=book["id"],
        book_naam=book["naam"],
        titel=f"Factuur controleren — {invoice_naam}",
        inhoud=f"€{amount_eur:.2f} in {book['naam']}. Deadline: {deadline_iso or 'geen'}.",
        deadline_iso=deadline_iso,
    )
    urgent = push_urgent(
        owner_user_id=book["owner_user_id"],
        book_id=book["id"],
        book_naam=book["naam"],
        titel=f"Nieuwe factuur — {invoice_naam}",
        severity="amber",
    )
    return {"task": task, "urgent": urgent}


def on_sepa_batch_ready(book: Dict, n_payments: int, total_eur: float) -> Dict:
    return {
        "task": create_task_for_book(
            owner_user_id=book["owner_user_id"],
            book_id=book["id"],
            book_naam=book["naam"],
            titel=f"SEPA batch downloaden — {book['naam']} ({n_payments} betalingen, €{total_eur:.2f})",
        ),
        "urgent": push_urgent(
            owner_user_id=book["owner_user_id"],
            book_id=book["id"],
            book_naam=book["naam"],
            titel="SEPA batch klaar",
            severity="red",
        ),
    }
