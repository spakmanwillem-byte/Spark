"""v13_boekhouding_migration_001 — Splits centraal spark_kasboek + audit_log
naar de 4 initiële books met heuristics.

Heuristic-regels (best-effort):
  1. tx heeft `shop_id` → book-{linked shop_id} of book-roadkillshop
  2. tx `type` = mint/gift/omzet/trade  → book-spark-core
  3. tx user_id=user-001 + geen shop_id + type=personal/withdraw → book-willem-prive
  4. tx over "zorgboerderij" in naam/note → book-zorgboerderij
  5. fallback → book-spark-core

Migratie is ADDITIEF: entries krijgen bron-tag `migrated_from_spark_kasboek`
en `original_source_id`. Origineel spark_kasboek.json blijft ongewijzigd
(alleen gelezen). Zo blijft rollback mogelijk.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from modules.core.storage import load_json
from modules.boekhouder import books as book_svc

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SPARK_KASBOEK_FP = DATA_ROOT / "boekhouder" / "spark_kasboek.json"
AUDIT_LOG_FP = DATA_ROOT / "system" / "audit_log.json"


def _classify(tx: Dict) -> str:
    """Kies book-id voor een transactie via heuristics."""
    text_blob = " ".join(
        str(v).lower() for v in [
            tx.get("naam", ""), tx.get("note", ""), tx.get("bron", ""),
            tx.get("source", ""), tx.get("type", "")
        ]
    )
    shop_id = tx.get("shop_id") or tx.get("shop") or ""

    # 1. Shop-koppeling
    if shop_id:
        # zoek book met linked_shop_id
        for meta in book_svc.list_books(owner_user_id=None):
            if meta.get("linked_shop_id") == shop_id:
                return meta["id"]
        if "roadkill" in str(shop_id).lower() or "roadkill" in text_blob:
            return "book-roadkillshop"

    # 4. Zorgboerderij
    if "zorgboerderij" in text_blob or "zorg-boerderij" in text_blob:
        return "book-zorgboerderij"

    # 2. Spark-systeem transacties
    tx_type = (tx.get("type") or "").lower()
    if any(k in tx_type for k in ("mint", "gift_in", "omzet_in", "gift_out", "trade_buy", "trade_sell", "anchor")):
        return "book-spark-core"

    # 3. Willem-privé (user-001 zonder shop, persoonlijke acties)
    uid = tx.get("user_id") or tx.get("uid") or ""
    if uid == "user-001" and any(k in tx_type for k in ("withdraw", "personal", "topup", "sepa_deposit")):
        return "book-willem-prive"

    # 4b. Roadkill in blob → shop
    if "roadkill" in text_blob:
        return "book-roadkillshop"

    # fallback
    return "book-spark-core"


def _extract_amount(tx: Dict) -> float:
    """Probeer een bedrag te vinden, teken op basis van type."""
    for key in ("amount_eur", "bedrag", "amount", "netto", "totaal"):
        if key in tx and tx[key] is not None:
            try:
                v = float(tx[key])
                # Uitgaven negatief maken
                tx_type = (tx.get("type") or "").lower()
                if any(k in tx_type for k in ("out", "expense", "withdraw", "sell_back", "cost")):
                    return -abs(v)
                return v
            except (ValueError, TypeError):
                continue
    return 0.0


def dry_run_migration() -> Dict:
    """Simuleer migratie zonder te schrijven. Handig voor Willem om te reviewen."""
    kasboek = load_json(SPARK_KASBOEK_FP, default={})
    audit = load_json(AUDIT_LOG_FP, default={"entries": []})

    all_tx = []
    # spark_kasboek kan verschillende structuren hebben — pak alles wat op tx lijkt
    if isinstance(kasboek, dict):
        for key, val in kasboek.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        item.setdefault("source", f"spark_kasboek.{key}")
                        all_tx.append(item)
    # audit_log entries
    for e in audit.get("entries", []):
        if not isinstance(e, dict):
            continue
        e = {**e, "source": "audit_log"}
        all_tx.append(e)

    per_book: Dict[str, int] = {}
    per_book_eur: Dict[str, float] = {}
    for tx in all_tx:
        bid = _classify(tx)
        per_book[bid] = per_book.get(bid, 0) + 1
        per_book_eur[bid] = per_book_eur.get(bid, 0.0) + _extract_amount(tx)

    return {
        "total_tx": len(all_tx),
        "per_book_count": per_book,
        "per_book_eur": {k: round(v, 2) for k, v in per_book_eur.items()},
        "kasboek_keys": list(kasboek.keys()) if isinstance(kasboek, dict) else [],
        "audit_entries": len(audit.get("entries", [])),
    }


def run_migration(mode: str = "add") -> Dict:
    """Voer migratie uit. `mode='add'` = additief (default, veilig).
    Elke geïmporteerde entry krijgt `source_id` = original id + `tag=migrated`.
    """
    kasboek = load_json(SPARK_KASBOEK_FP, default={})
    audit = load_json(AUDIT_LOG_FP, default={"entries": []})

    # Zorg dat books bestaan
    book_svc.seed_initial_books()

    all_tx: List[Tuple[Dict, str]] = []  # (tx, source_label)
    if isinstance(kasboek, dict):
        for key, val in kasboek.items():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        all_tx.append((item, f"spark_kasboek.{key}"))
    for e in audit.get("entries", []):
        if isinstance(e, dict):
            all_tx.append((e, "audit_log"))

    imported_per_book: Dict[str, int] = {}
    skipped = 0
    for tx, src_label in all_tx:
        # Duplicaat-check op source_id
        src_id = tx.get("id") or tx.get("tx_id") or f"{src_label}:{tx.get('ts', '?')}"
        bid = _classify(tx)
        # Skip als al eerder gemigreerd (op src_id in kasboek)
        existing = book_svc.list_entries(bid, limit=100_000)
        if any(e.get("source_id") == src_id for e in existing):
            skipped += 1
            continue
        entry = {
            "ts": tx.get("ts") or tx.get("timestamp") or tx.get("created_at"),
            "type": tx.get("type", "migrated"),
            "amount_eur": _extract_amount(tx),
            "naam": tx.get("naam") or tx.get("bron") or src_label,
            "note": tx.get("note") or tx.get("description") or "",
            "source": "migration",
            "source_id": src_id,
            "tags": ["migrated_from_" + src_label.split(".")[0]],
        }
        book_svc.add_entry(bid, entry)
        imported_per_book[bid] = imported_per_book.get(bid, 0) + 1

    return {
        "success": True,
        "mode": mode,
        "total_seen": len(all_tx),
        "imported_per_book": imported_per_book,
        "skipped_duplicates": skipped,
        "migration_ts": datetime.now(timezone.utc).isoformat(),
    }
