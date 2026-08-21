"""v13_boekhouding_books_001 — Multi-container boekhouding.

Elke boekhouding is een eigen container met unique ID, eigen kasboek,
reserve, closings, documenten en SEPA-koppeling. Owner-only toegang.

Structuur:
  /backend/data/boekhouding/books/book-{id}/
    _meta.json          — id, naam, type, owner_user_id, iban, ...
    kasboek.json        — {"entries": [...]}
    reserve.json        — {"balance_eur": 0.0, "history": [...]}
    closings.json       — {"closings": [...]}
    documents.json      — refs → user archive
    sepa_batches.json   — uitgaande SEPA-XML batches
    bank_imports.json   — importeerde CAMT/MT940 afschriften

Types:
  spark_core    — Spark's eigen kasboek (systeem-owned)
  shop          — Winkelstraat-shop boekhouding
  entity        — Eigen entiteit (bv Zorgboerderij)
  user_prive    — Persoonlijke boekhouding van user
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
BOOKS_ROOT = DATA_ROOT / "boekhouding" / "books"
BOOKS_ROOT.mkdir(parents=True, exist_ok=True)

VALID_TYPES = {"spark_core", "shop", "entity", "user_prive"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return "book-" + secrets.token_hex(5)


def _validate_iban(iban: Optional[str]) -> Optional[str]:
    """Lichtgewicht IBAN-check (formaat, checksum optioneel). Geeft schoongepoetste string terug of None."""
    if not iban:
        return None
    s = re.sub(r"\s+", "", iban).upper()
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$", s):
        return None
    return s


def _book_dir(book_id: str) -> Path:
    return BOOKS_ROOT / book_id


def _meta_fp(book_id: str) -> Path:
    return _book_dir(book_id) / "_meta.json"


# ============================================================
# CRUD
# ============================================================

def create_book(
    naam: str,
    type_: str,
    owner_user_id: str,
    iban: Optional[str] = None,
    bank_naam: Optional[str] = None,
    linked_shop_id: Optional[str] = None,
    kleur: Optional[str] = None,
    icoon: Optional[str] = None,
    book_id: Optional[str] = None,
) -> Dict:
    if type_ not in VALID_TYPES:
        raise ValueError(f"Ongeldig type: {type_}. Kies uit {VALID_TYPES}.")
    bid = book_id or _new_id()
    bdir = _book_dir(bid)
    if bdir.exists() and _meta_fp(bid).exists():
        # idempotent: bestaat al, geef terug
        return load_json(_meta_fp(bid), default={})
    bdir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": bid,
        "naam": naam,
        "type": type_,
        "owner_user_id": owner_user_id,
        "iban": _validate_iban(iban),
        "bank_naam": bank_naam or None,
        "linked_shop_id": linked_shop_id,
        "kleur": kleur or _default_kleur(type_),
        "icoon": icoon or _default_icoon(type_),
        "created_at": _now(),
        "last_touched": _now(),
        "status": "active",
    }
    save_json(_meta_fp(bid), meta)
    # Bootstrap child-files
    save_json(bdir / "kasboek.json", {"entries": []})
    save_json(bdir / "reserve.json", {"balance_eur": 0.0, "history": []})
    save_json(bdir / "closings.json", {"closings": []})
    save_json(bdir / "documents.json", {"documents": []})
    save_json(bdir / "sepa_batches.json", {"batches": []})
    save_json(bdir / "bank_imports.json", {"imports": []})
    return meta


def _default_kleur(type_: str) -> str:
    return {
        "spark_core": "#f59e0b",
        "shop": "#06b6d4",
        "entity": "#10b981",
        "user_prive": "#a855f7",
    }.get(type_, "#94a3b8")


def _default_icoon(type_: str) -> str:
    return {
        "spark_core": "sparkles",
        "shop": "shopping-bag",
        "entity": "building",
        "user_prive": "user",
    }.get(type_, "book")


def get_book(book_id: str) -> Optional[Dict]:
    fp = _meta_fp(book_id)
    if not fp.exists():
        return None
    return load_json(fp, default=None)


def list_books(owner_user_id: Optional[str] = None, include_system: bool = True) -> List[Dict]:
    """Lijst alle boeken. Filter op owner (owner-only view).
    include_system=True voegt spark_core toe voor iedereen die admin is (dat check je in de route).
    """
    out: List[Dict] = []
    for d in sorted(BOOKS_ROOT.glob("book-*")):
        if not d.is_dir():
            continue
        meta = load_json(d / "_meta.json", default=None)
        if not meta:
            continue
        if owner_user_id is None:
            out.append(meta)
            continue
        if meta.get("owner_user_id") == owner_user_id:
            out.append(meta)
        elif include_system and meta.get("type") == "spark_core":
            out.append(meta)
    return out


def update_book(book_id: str, patch: Dict) -> Optional[Dict]:
    meta = get_book(book_id)
    if not meta:
        return None
    editable = {"naam", "iban", "bank_naam", "kleur", "icoon", "status"}
    for k, v in patch.items():
        if k not in editable:
            continue
        if k == "iban":
            v = _validate_iban(v) if v else None
        meta[k] = v
    meta["last_touched"] = _now()
    save_json(_meta_fp(book_id), meta)
    return meta


def delete_book(book_id: str, archive: bool = True) -> bool:
    meta = get_book(book_id)
    if not meta:
        return False
    if meta.get("type") == "spark_core":
        # spark-core mag NIET verwijderd (systeem-boek)
        return False
    if archive:
        meta["status"] = "archived"
        meta["archived_at"] = _now()
        save_json(_meta_fp(book_id), meta)
    return True


# ============================================================
# Kasboek entries — CRUD per book
# ============================================================

def add_entry(book_id: str, entry: Dict) -> Optional[Dict]:
    """Voeg entry toe aan book kasboek + hash-chain (papertrail).
    entry-velden: type (income/expense/mint/gift/trade), amount_eur, naam,
    ts (auto), tegenrekening_iban, note, source, source_id, tags.

    v13_boekhouding_papertrail_001: elke entry wordt gelogd in de LogAgent
    papertrail met prev_hash chain. Zo is manipulatie achteraf detecteerbaar.
    """
    meta = get_book(book_id)
    if not meta:
        return None
    kasboek_fp = _book_dir(book_id) / "kasboek.json"
    data = load_json(kasboek_fp, default={"entries": []})
    eid = "entry-" + secrets.token_hex(4)
    e = {
        "id": eid,
        "ts": entry.get("ts") or _now(),
        "type": entry.get("type", "other"),
        "amount_eur": float(entry.get("amount_eur", 0.0)),
        "naam": entry.get("naam", ""),
        "note": entry.get("note", ""),
        "tegenrekening_iban": entry.get("tegenrekening_iban"),
        "tegenrekening_naam": entry.get("tegenrekening_naam"),
        "source": entry.get("source", "manual"),
        "source_id": entry.get("source_id"),
        "tags": entry.get("tags", []),
    }
    # Papertrail — hash-chain via LogAgent
    try:
        from modules.boekhouder.agents.log_agent import LogAgent
        agent = LogAgent()
        rec = agent.record(
            topic=f"book_{book_id}",
            event_type=e["type"],
            actor=meta.get("owner_user_id", "system"),
            data={
                "entry_id": eid,
                "amount_eur": e["amount_eur"],
                "naam": e["naam"][:80],
                "source": e["source"],
                "source_id": e.get("source_id"),
                "ts": e["ts"],
            },
        )
        e["papertrail_hash"] = rec.get("event_hash")
    except Exception as _pt_err:
        e["papertrail_error"] = str(_pt_err)[:120]

    data["entries"].append(e)
    save_json(kasboek_fp, data)
    meta["last_touched"] = _now()
    save_json(_meta_fp(book_id), meta)

    # v13o_auto_announce_001 — Automatische boekingen worden gemeld
    # aan owner via boekhouder-bot DM. Alleen skippen bij expliciet manueel.
    if e["source"] not in ("manual", "manual_opening"):
        try:
            _auto_announce_entry(meta, e)
        except Exception:
            pass  # DM-fail mag boeking niet blokkeren

    return e


def _auto_announce_entry(meta: Dict, entry: Dict):
    """Verstuur DM naar boek-owner over automatische boeking."""
    owner = meta.get("owner_user_id")
    if not owner or owner in ("user-000", "system"):
        return  # Spark zelf krijgt geen DM
    from modules.boekhouder.service import _send_dm
    src = entry.get("source", "auto")
    amt = entry["amount_eur"]
    arrow = "📈" if amt >= 0 else "📉"
    src_label = {
        "shop_hook": "verkoop",
        "camt053": "SEPA bank-import",
        "mt940": "MT940 bank-import",
        "migration": "migratie",
        "spark_fee_inlossen": "Spark-fee inlossing",
    }.get(src, f"auto-boeking ({src})")
    text = (
        f"{arrow} **Auto-boeking in {meta['naam']}**\n"
        f"Type: {src_label}\n"
        f"Bedrag: €{amt:+.2f}\n"
        f"Omschrijving: {entry.get('naam', '?')}\n"
        + (f"Hash: `{entry.get('papertrail_hash', '-')[:12]}`" if entry.get('papertrail_hash') else "")
    )
    _send_dm(
        text,
        kind="boekhouder_auto_entry",
        extra={"book_id": meta["id"], "entry_id": entry["id"], "source": src},
        recipient_id=owner,
    )


def list_entries(book_id: str, limit: int = 200) -> List[Dict]:
    kasboek_fp = _book_dir(book_id) / "kasboek.json"
    data = load_json(kasboek_fp, default={"entries": []})
    entries = data.get("entries", [])
    return sorted(entries, key=lambda x: x.get("ts", ""), reverse=True)[:limit]


def book_summary(book_id: str) -> Dict:
    """Snel overzicht: totaal inkomsten/uitgaven, balans, aantal entries."""
    entries = list_entries(book_id, limit=100_000)
    income = sum(e["amount_eur"] for e in entries if e["amount_eur"] > 0)
    expense = sum(abs(e["amount_eur"]) for e in entries if e["amount_eur"] < 0)
    return {
        "book_id": book_id,
        "n_entries": len(entries),
        "income_eur": round(income, 2),
        "expense_eur": round(expense, 2),
        "balance_eur": round(income - expense, 2),
    }


# ============================================================
# Seed — de 4 initiële boeken
# ============================================================

SEED_BOOKS = [
    {
        "id": "book-spark-core",
        "naam": "Spark Core",
        "type": "spark_core",
        "owner_user_id": "user-000",  # Spark
        "kleur": "#f59e0b",
        "icoon": "sparkles",
    },
    {
        "id": "book-roadkillshop",
        "naam": "Roadkillshop",
        "type": "shop",
        "owner_user_id": "user-001",
        "linked_shop_id": "shop-roadkill",
        "kleur": "#dc2626",
        "icoon": "shopping-bag",
    },
    {
        "id": "book-zorgboerderij",
        "naam": "Spark Zorgboerderij",
        "type": "entity",
        "owner_user_id": "user-001",
        "kleur": "#16a34a",
        "icoon": "building",
    },
    {
        "id": "book-willem-prive",
        "naam": "Willem — Privé",
        "type": "user_prive",
        "owner_user_id": "user-001",
        "kleur": "#a855f7",
        "icoon": "user",
    },
]


def seed_initial_books() -> Dict:
    """Idempotent seed van de 4 initiële boeken."""
    created = []
    skipped = []
    for spec in SEED_BOOKS:
        if _meta_fp(spec["id"]).exists():
            skipped.append(spec["id"])
            continue
        create_book(
            naam=spec["naam"],
            type_=spec["type"],
            owner_user_id=spec["owner_user_id"],
            linked_shop_id=spec.get("linked_shop_id"),
            kleur=spec.get("kleur"),
            icoon=spec.get("icoon"),
            book_id=spec["id"],
        )
        created.append(spec["id"])
    return {"created": created, "skipped": skipped, "total": len(list_books(owner_user_id=None))}


def ensure_shop_book(shop_id: str, owner_user_id: str, shop_naam: str) -> Dict:
    """Auto-hook: bij shop-create zorgt dit dat er ook een book bestaat."""
    # zoek bestaand book met linked_shop_id
    for meta in list_books(owner_user_id=None):
        if meta.get("linked_shop_id") == shop_id:
            return meta
    bid = f"book-shop-{shop_id[-8:]}"
    return create_book(
        naam=shop_naam or f"Shop {shop_id}",
        type_="shop",
        owner_user_id=owner_user_id,
        linked_shop_id=shop_id,
        book_id=bid,
    )
