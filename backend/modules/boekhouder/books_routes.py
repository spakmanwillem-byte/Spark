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
from modules.sepa_hub import get_hub as get_sepa_hub
from modules.boekhouder import notify as book_notify
from modules.boekhouder import shop_hooks as shop_book_hooks
from modules.boekhouder import shop_announcer as shop_ann

router = APIRouter(prefix="/boekhouding", tags=["boekhouding"])

USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def _get_user(user_id: str) -> Optional[dict]:
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    for u in users:
        if u.get("id") == user_id:
            return u
    return None


def _is_admin(user_id: str) -> bool:
    """v13d_boekhouder_admin_leak_001 (sessie 55) — Willem meldde: 'Gerben (G2)
    zag mijn kasboek'. Root cause: `gradatie <= 2` behandelde G2 als admin.
    G2 is echter familie (niet admin). Fix: alleen echte admin-flags tellen."""
    u = _get_user(user_id) or {}
    return bool(u.get("admin")) or bool(u.get("admin_capable"))


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
    # v13d_boekhouder_auto_prive_001 (sessie 55) — Willem: "iedere gebruiker
    # moet in zijn omgeving zijn eigen boekhouding". Als user nog geen privé-book
    # heeft, autocreate 'm bij eerste GET. Zo krijgt elke user bij eerste
    # bezoek automatisch een lege privé-boekhouding zonder admin-actie.
    if viewer_id and viewer_id != "user-000":
        user = _get_user(viewer_id)
        if user:
            existing = book_svc.list_books(owner_user_id=viewer_id, include_system=False)
            has_prive = any(b.get("type") == "user_prive" for b in existing)
            if not has_prive:
                try:
                    book_svc.create_book(
                        naam=f"{user.get('naam', 'Gebruiker')} — Privé",
                        type_="user_prive",
                        owner_user_id=viewer_id,
                        iban=None, bank_naam=None, linked_shop_id=None,
                        kleur="#22c55e", icoon="👤",
                    )
                except Exception as ex:
                    print(f"[auto-prive-book] kon geen privé-book aanmaken voor {viewer_id}: {ex}")

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
    parsed = get_sepa_hub().parse_camt053(content)
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
    parsed = get_sepa_hub().parse_mt940(content)
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
    xml_out = get_sepa_hub().generate_pain001(
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


@router.post("/books/{book_id}/opening-balance")
def set_opening_balance(book_id: str, viewer_id: str, amount_eur: float, naam: str = "Openingsbalans"):
    """Zet een openingsbalans-entry (idempotent: vervangt bestaande opening als aanwezig)."""
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    # Verwijder bestaande opening
    from pathlib import Path
    from modules.core.storage import load_json, save_json
    kfp = Path(__file__).parent.parent.parent / "data" / "boekhouding" / "books" / book_id / "kasboek.json"
    data = load_json(kfp, default={"entries": []})
    data["entries"] = [e for e in data.get("entries", []) if e.get("type") != "opening_balance"]
    save_json(kfp, data)
    e = book_svc.add_entry(book_id, {
        "type": "opening_balance",
        "amount_eur": float(amount_eur),
        "naam": naam,
        "note": "Handmatig ingesteld startsaldo",
        "source": "manual_opening",
        "tags": ["opening"],
    })
    return {"success": True, "entry": e, "summary": book_svc.book_summary(book_id)}


@router.post("/books/{book_id}/reset")
def reset_book(book_id: str, viewer_id: str, keep_meta: bool = True):
    """Wipe alle entries van dit book — schoon nulpunt. Meta blijft (IBAN/naam/etc)."""
    b = book_svc.get_book(book_id)
    if not b:
        raise HTTPException(404)
    if not _can_access_book(viewer_id, b):
        raise HTTPException(403)
    from pathlib import Path
    from modules.core.storage import save_json
    bdir = Path(__file__).parent.parent.parent / "data" / "boekhouding" / "books" / book_id
    save_json(bdir / "kasboek.json", {"entries": []})
    save_json(bdir / "reserve.json", {"balance_eur": 0.0, "history": []})
    save_json(bdir / "closings.json", {"closings": []})
    save_json(bdir / "documents.json", {"documents": []})
    save_json(bdir / "sepa_batches.json", {"batches": []})
    save_json(bdir / "bank_imports.json", {"imports": []})
    return {"success": True, "book_id": book_id, "reset_at": datetime_now_iso()}


def datetime_now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


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


# ============================================================
# Shop verkoop/aankoop hooks
# ============================================================

class ShopSaleIn(BaseModel):
    shop_id: str
    netto_eur: float  # v13b: verkoper geeft netto op, systeem berekent bruto met BTW
    koper_naam: Optional[str] = ""
    remittance: Optional[str] = ""
    source_id: Optional[str] = None
    btw_pct_override: Optional[float] = None
    spark_pct_override: Optional[float] = None


@router.post("/hooks/shop-sale")
def hook_shop_sale(payload: ShopSaleIn, viewer_id: str):
    """Boek een shop-verkoop: NETTO in shop-book, BTW zichtbaar voor koper, Spark-fee openstaand."""
    from pathlib import Path as _P
    shops_meta = load_json(_P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json", default={"shops": []})
    shop = next((s for s in shops_meta.get("shops", []) if s.get("id") == payload.shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    if not (_is_admin(viewer_id) or shop.get("owner_user_id") == viewer_id):
        raise HTTPException(403, "Alleen shop-eigenaar of admin")
    return shop_book_hooks.record_shop_sale(
        shop_id=payload.shop_id,
        netto_eur=payload.netto_eur,
        koper_naam=payload.koper_naam or "",
        remittance=payload.remittance or "",
        source_id=payload.source_id,
        btw_pct_override=payload.btw_pct_override,
        spark_pct_override=payload.spark_pct_override,
    )


@router.get("/hooks/openstaand/{shop_id}")
def hook_openstaand(shop_id: str, viewer_id: str):
    from pathlib import Path as _P
    shops_meta = load_json(_P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json", default={"shops": []})
    shop = next((s for s in shops_meta.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404)
    if not (_is_admin(viewer_id) or shop.get("owner_user_id") == viewer_id):
        raise HTTPException(403)
    return shop_book_hooks.get_openstaand(shop_id)


class ShopFinanceConfigIn(BaseModel):
    btw_default_pct: Optional[float] = None
    spark_fee_pct: Optional[float] = None
    btw_kor_default: Optional[bool] = None
    commissie_default_pct: Optional[float] = None


@router.get("/shop-finance-config")
def get_shop_finance_config(viewer_id: str):
    from pathlib import Path as _P
    fp = _P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json"
    d = load_json(fp, default={})
    return {
        "success": True,
        "commissie_default_pct": d.get("commissie_default_pct", 1.0),
        "config": d.get("config", {"btw_default_pct": 21.0, "spark_fee_pct": 1.0, "btw_kor_default": False}),
    }


@router.patch("/shop-finance-config")
def patch_shop_finance_config(payload: ShopFinanceConfigIn, viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    from pathlib import Path as _P
    fp = _P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json"
    d = load_json(fp, default={})
    d.setdefault("config", {})
    for k in ("btw_default_pct", "spark_fee_pct", "btw_kor_default"):
        v = getattr(payload, k)
        if v is not None:
            d["config"][k] = v
    if payload.commissie_default_pct is not None:
        d["commissie_default_pct"] = payload.commissie_default_pct
    from modules.core.storage import save_json as _save
    _save(fp, d)
    return {"success": True, "commissie_default_pct": d.get("commissie_default_pct"), "config": d.get("config")}


@router.post("/hooks/inlossen/{shop_id}")
def hook_inlossen(shop_id: str, viewer_id: str):
    from pathlib import Path as _P
    shops_meta = load_json(_P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json", default={"shops": []})
    shop = next((s for s in shops_meta.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404)
    if not (_is_admin(viewer_id) or shop.get("owner_user_id") == viewer_id):
        raise HTTPException(403)
    return shop_book_hooks.inlossen_openstaand(shop_id, viewer_id)


class ShopPurchaseIn(BaseModel):
    shop_id: str
    amount_eur: float
    leverancier_naam: Optional[str] = ""
    remittance: Optional[str] = ""
    source_id: Optional[str] = None


@router.post("/hooks/shop-purchase")
def hook_shop_purchase(payload: ShopPurchaseIn, viewer_id: str):
    from pathlib import Path as _P
    shops_meta = load_json(_P(__file__).parent.parent.parent / "data" / "shops" / "_meta.json", default={"shops": []})
    shop = next((s for s in shops_meta.get("shops", []) if s.get("id") == payload.shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    if not (_is_admin(viewer_id) or shop.get("owner_user_id") == viewer_id):
        raise HTTPException(403, "Alleen shop-eigenaar of admin")
    return shop_book_hooks.record_shop_purchase(
        shop_id=payload.shop_id,
        amount_eur=payload.amount_eur,
        leverancier_naam=payload.leverancier_naam or "",
        remittance=payload.remittance or "",
        source_id=payload.source_id,
    )


@router.get("/winst-events")
def winst_events(viewer_id: str, limit: int = 50):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    from modules.boekhouder.agents.log_agent import LogAgent
    from pathlib import Path as _P
    import json as _json
    logs_dir = _P(__file__).parent.parent.parent / "data" / "boekhouder" / "logs" / "winst_events"
    events = []
    if logs_dir.exists():
        for fp in sorted(logs_dir.glob("*.jsonl"), reverse=True):
            with fp.open() as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(_json.loads(line))
            if len(events) >= limit:
                break
    return {
        "success": True,
        "events": events[-limit:],
        "total_spark_deel_eur": round(sum(e.get("data", {}).get("spark_deel_eur", 0) for e in events), 2),
    }



# ============================================================
# v13n_shop_announcer_001 — Per-user shop-report + boekhouder DM
# ============================================================

@router.get("/shop-report/{user_id}")
def shop_report_user(user_id: str, viewer_id: str, days: int = 7):
    """Rapport bouwen voor 1 user. Owner of admin mag zien."""
    if not (_is_admin(viewer_id) or user_id == viewer_id):
        raise HTTPException(403, "Alleen owner of admin")
    return {"success": True, "report": shop_ann.build_user_shop_report(user_id, days=days)}


@router.post("/shop-report/{user_id}/announce")
def announce_shop_report(user_id: str, viewer_id: str, days: int = 7, force: bool = False):
    """Verstuur DM van boekhouder-bot naar user met eigen shop-rapport."""
    if not (_is_admin(viewer_id) or user_id == viewer_id):
        raise HTTPException(403)
    return shop_ann.announce_to_user(user_id, days=days, force=force)


@router.post("/shop-report/announce-all")
def announce_all(viewer_id: str, days: int = 7, force: bool = False):
    """Admin-only: alle shop-eigenaren krijgen hun rapport."""
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    return shop_ann.announce_all_shop_owners(days=days, force=force)


@router.get("/shop-report-aggregate")
def shop_report_aggregate(viewer_id: str, days: int = 7):
    """Admin-only: aggregate view over alle shop-owners."""
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin")
    return shop_ann.admin_aggregate_report(days=days)
