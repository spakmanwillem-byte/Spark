"""v13_boekhouding_routes_001 — REST endpoints voor multi-book boekhouding.

Owner-only + admin (gradatie ≤ 2) mag alles zien. Anders alleen eigen books.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from modules.core.storage import load_json
from modules.boekhouder import books as book_svc
from modules.boekhouder import migration as book_migration
from modules.boekhouder import sepa as sepa_svc
from modules.boekhouder import notify as book_notify

router = APIRouter(prefix="/boekhouding", tags=["boekhouding"])

USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def _get_user(user_id: str) -> Optional[dict]:
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    for u in users:
        if u.get("id") == user_id:
            return u
    return None


def _is_admin(user_id: str) -> bool:
    u = _get_user(user_id) or {}
    return u.get("admin") is True or (u.get("gradatie") or 99) <= 2


def _can_access_book(viewer_id: str, book: dict) -> bool:
    if _is_admin(viewer_id):
        return True
    if book.get("owner_user_id") == viewer_id:
        return True
    # spark_core is voor iedereen leesbaar (het systeem-boek)
    if book.get("type") == "spark_core":
        return True
    return False


# ============================================================
# CRUD boeken
# ============================================================

class CreateBookIn(BaseModel):
    naam: str
    type: str  # spark_core | shop | entity | user_prive
    owner_user_id: str
    iban: Optional[str] = None
    bank_naam: Optional[str] = None
    linked_shop_id: Optional[str] = None
    kleur: Optional[str] = None
    icoon: Optional[str] = None


class UpdateBookIn(BaseModel):
    naam: Optional[str] = None
    iban: Optional[str] = None
    bank_naam: Optional[str] = None
    kleur: Optional[str] = None
    icoon: Optional[str] = None
    status: Optional[str] = None


class AddEntryIn(BaseModel):
    type: str = "other"
    amount_eur: float
    naam: str
    note: Optional[str] = ""
    tegenrekening_iban: Optional[str] = None
    tegenrekening_naam: Optional[str] = None
    tags: Optional[list] = None


@router.get("/books")
def list_books(viewer_id: str):
    if _is_admin(viewer_id):
        items = book_svc.list_books(owner_user_id=None)
    else:
        items = book_svc.list_books(owner_user_id=viewer_id, include_system=True)
    return {"success": True, "books": items, "count": len(items)}


@router.post("/books")
def create_book(payload: CreateBookIn, viewer_id: str):
    # Alleen admin of eigen books (voor user_prive)
    if not _is_admin(viewer_id) and payload.owner_user_id != viewer_id:
        raise HTTPException(403, "Geen rechten om book voor andere user aan te maken.")
    if payload.type == "spark_core" and not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin mag spark_core book aanmaken.")
    try:
        meta = book_svc.create_book(
            naam=payload.naam,
            type_=payload.type,
            owner_user_id=payload.owner_user_id,
            iban=payload.iban,
            bank_naam=payload.bank_naam,
            linked_shop_id=payload.linked_shop_id,
            kleur=payload.kleur,
            icoon=payload.icoon,
        )
        return {"success": True, "book": meta}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/books/{book_id}")
def get_book(book_id: str, viewer_id: str):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404, "Book niet gevonden")
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403, "Geen toegang tot dit book")
    return {"success": True, "book": b, "summary": book_svc.book_summary(book_id)}


@router.patch("/books/{book_id}")
def patch_book(book_id: str, payload: UpdateBookIn, viewer_id: str):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404, "Book niet gevonden")
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403, "Geen toegang")
    patch = payload.model_dump(exclude_none=True)
    updated = book_svc.update_book(book_id, patch)
    return {"success": True, "book": updated}


@router.delete("/books/{book_id}")
def delete_book(book_id: str, viewer_id: str):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404, "Book niet gevonden")
    if not (_is_admin(viewer_id) or b.get("owner_user_id") == viewer_id):
        raise HTTPException(403, "Geen toegang")
    ok = book_svc.delete_book(book_id, archive=True)
    if not ok:
        raise HTTPException(400, "Kon book niet archiveren (systeem-boek?)")
    return {"success": True}


@router.get("/books/{book_id}/entries")
def get_entries(book_id: str, viewer_id: str, limit: int = 200):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    return {"success": True, "entries": book_svc.list_entries(book_id, limit=limit)}


@router.post("/books/{book_id}/entries")
def add_entry(book_id: str, payload: AddEntryIn, viewer_id: str):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    e = book_svc.add_entry(book_id, payload.model_dump(exclude_none=True))
    return {"success": True, "entry": e}


# ============================================================
# Seed & migratie
# ============================================================

@router.post("/seed")
def seed_books(viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    return {"success": True, **book_svc.seed_initial_books()}


@router.get("/migrate/dry-run")
def migrate_dry(viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    return {"success": True, **book_migration.dry_run_migration()}


@router.post("/migrate/run")
def migrate_run(viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    return book_migration.run_migration()


# ============================================================
# SEPA import + export
# ============================================================

@router.post("/books/{book_id}/sepa/import-camt")
async def import_camt(book_id: str, viewer_id: str, file: UploadFile = File(...)):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    content = (await file.read()).decode("utf-8", errors="ignore")
    parsed = sepa_svc.parse_camt053(content)
    if "error" in parsed:
        raise HTTPException(400, parsed["error"])
    imported = 0
    for tx in parsed.get("transactions", []):
        # duplicate check op source_id
        existing = book_svc.list_entries(book_id, limit=100_000)
        src_id = f"{tx.get('iban_account','')}:{tx.get('ts','')}:{tx.get('amount_eur',0):.2f}:{tx.get('tegenrekening_iban','')}"
        if any(e.get("source_id") == src_id for e in existing):
            continue
        book_svc.add_entry(book_id, {**tx, "source": "camt053", "source_id": src_id})
        imported += 1
    return {"success": True, "imported": imported, "statements": parsed.get("statements", [])}


@router.post("/books/{book_id}/sepa/import-mt940")
async def import_mt940(book_id: str, viewer_id: str, file: UploadFile = File(...)):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    content = (await file.read()).decode("utf-8", errors="ignore")
    parsed = sepa_svc.parse_mt940(content)
    imported = 0
    for tx in parsed.get("transactions", []):
        existing = book_svc.list_entries(book_id, limit=100_000)
        src_id = f"{tx.get('iban_account','')}:{tx.get('ts','')}:{tx.get('amount_eur',0):.2f}"
        if any(e.get("source_id") == src_id for e in existing):
            continue
        book_svc.add_entry(book_id, {**tx, "source": "mt940", "source_id": src_id})
        imported += 1
    return {"success": True, "imported": imported, "iban": parsed.get("iban")}


class SepaBatchIn(BaseModel):
    payments: list  # [{amount_eur, creditor_naam, creditor_iban, remittance?}]
    initiator_naam: Optional[str] = None


@router.post("/books/{book_id}/sepa/export-pain001")
def export_pain001(book_id: str, payload: SepaBatchIn, viewer_id: str):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    if not b.get("iban"):
        raise HTTPException(400, "Book heeft geen IBAN — vul die eerst in bij book-instellingen.")
    xml_out = sepa_svc.generate_pain001(
        debtor_naam=b["naam"],
        debtor_iban=b["iban"],
        payments=payload.payments,
        initiator_naam=payload.initiator_naam or b["naam"],
    )
    total = sum(float(p["amount_eur"]) for p in payload.payments)
    # trigger notification
    book_notify.on_sepa_batch_ready(b, n_payments=len(payload.payments), total_eur=total)
    return {
        "success": True,
        "xml": xml_out,
        "n_payments": len(payload.payments),
        "total_eur": round(total, 2),
    }


# ============================================================
# Notify test-hook (voor UI-development)
# ============================================================

@router.post("/books/{book_id}/notify/test-invoice")
def notify_test_invoice(book_id: str, viewer_id: str, naam: str, amount_eur: float):
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    result = book_notify.on_new_invoice(b, invoice_naam=naam, amount_eur=amount_eur)
    return {"success": True, **result}
