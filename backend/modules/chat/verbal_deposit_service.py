"""
Verbal Deposit Intent (v6_verbal_deposit_001 — 28 mei 2026)
=============================================================
Spark herkent gesproken/getypte stortingen en vraagt voor welke user te crediten.

Triggers (NL):
  - "ik stortte 50 euro"
  - "ik heb 50€ gestort"
  - "er kwam 100 euro binnen"
  - "Marieke heeft 25 gestort"

Twee-staps flow:
  1. Detect amount + optional name → return type=deposit_ask, store pending state
  2. Volgende user-bericht antwoord = naam → crediteer en log in spark_kasboek
"""
import re
from datetime import datetime, timezone
from typing import Optional, Dict

from modules.core.storage import load_json, save_json
from pathlib import Path

DATA = Path(__file__).parent.parent.parent / "data"

# Patronen — match amount, optioneel "voor X" / "van X"
_DEPOSIT_PATTERNS = [
    # "ik stortte X euro" / "ik heb X gestort"
    r"\b(?:ik|er)\s+(?:heb\s+)?(?:stort(?:te|)|kwam\s+binnen)\s+(?:€\s*)?(\d+(?:[.,]\d+)?)\s*(?:euro|eur|€)?",
    r"\b(?:€\s*)?(\d+(?:[.,]\d+)?)\s*(?:euro|eur|€)\s+(?:gestort|binnen\s*gekomen|ontvangen)",
    # "Marieke heeft 25 gestort"
    r"\b([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\s+heeft\s+(?:€\s*)?(\d+(?:[.,]\d+)?)\s*(?:euro|eur|€)?\s+gestort",
]


def _parse_amount(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ".").replace(" ", ""))
    except Exception:
        return None


def detect_verbal_deposit(text: str, user_id: str = "") -> Optional[Dict]:
    """Returns dict {type, amount_eur, suggested_user?, message} of None."""
    if not text or len(text) < 8:
        return None
    t = text.strip()
    amount = None
    suggested_naam = None

    # Probeer "X heeft Y gestort" eerst (geeft naam + amount)
    m = re.search(_DEPOSIT_PATTERNS[2], t, re.IGNORECASE)
    if m:
        suggested_naam = m.group(1).strip()
        amount = _parse_amount(m.group(2))
    else:
        for pat in _DEPOSIT_PATTERNS[:2]:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                amount = _parse_amount(m.group(1))
                break

    if amount is None or amount <= 0 or amount > 100000:
        return None

    return {
        "type": "deposit_ask",
        "amount_eur": amount,
        "suggested_naam": suggested_naam,
        "needs_user_confirmation": True,
        "message": (
            f"Genoteerd: storting van €{amount:.2f}"
            + (f" van {suggested_naam}" if suggested_naam else "")
            + ". Voor welke user moet ik dit crediteren? (zeg de naam, of 'spark' voor Spark zelf, of 'annuleer')"
        ),
    }


def confirm_deposit(amount_eur: float, target_naam: str, actor_user_id: str) -> Dict:
    """Voer de storting uit: crediteer wallet + log kasboek-entry."""
    # Resolve target_naam
    USERS = DATA / "system" / "users.json"
    udata = load_json(USERS, default={"users": []})
    users = udata.get("users", []) if isinstance(udata, dict) else udata

    q = target_naam.strip().lower()
    if q in ("spark", "user-000", "zelf"):
        target = next((u for u in users if u.get("id") == "user-000"), None)
    elif q in ("annuleer", "stop", "cancel"):
        return {"type": "deposit_cancelled", "message": "Storting geannuleerd. Niets geboekt."}
    else:
        target = next((u for u in users if (u.get("naam") or "").lower() == q or q in (u.get("naam") or "").lower()), None)

    if not target:
        return {"type": "deposit_unresolved", "message": f"Ik ken geen '{target_naam}'. Geef de juiste naam, of 'annuleer'."}

    target_id = target.get("id")
    # Crediteer wallet
    WALLETS = DATA / "wallet" / "wallets.json"
    w = load_json(WALLETS, default={"wallets": {}})
    bucket = w.setdefault("wallets", {}).setdefault(target_id, {})
    old_eur = float(bucket.get("balance_eur", bucket.get("balance", 0)) or 0)
    bucket["balance_eur"] = round(old_eur + amount_eur, 2)
    bucket["balance"] = bucket["balance_eur"]
    bucket["last_deposit_at"] = datetime.now(timezone.utc).isoformat()
    save_json(WALLETS, w)

    # Log in spark_kasboek (als target = Spark zelf)
    kasboek_entry = None
    if target_id == "user-000":
        KB_FILE = DATA / "system" / "spark_kasboek.json"
        kb = load_json(KB_FILE, default={"entries": [], "totals": {}})
        kb.setdefault("entries", [])
        kb.setdefault("totals", {})
        kb["totals"].setdefault("storting_in", 0)
        kasboek_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "storting_in",
            "bedrag_eur": amount_eur,
            "bron_user": actor_user_id,
            "omschrijving": f"Verbaal aangemelde storting via Spark ({actor_user_id})",
        }
        kb["entries"].append(kasboek_entry)
        kb["totals"]["storting_in"] = round(kb["totals"]["storting_in"] + amount_eur, 2)
        save_json(KB_FILE, kb)

    return {
        "type": "deposit_confirmed",
        "target_id": target_id,
        "target_naam": target.get("naam"),
        "amount_eur": amount_eur,
        "new_balance_eur": bucket["balance_eur"],
        "kasboek_logged": kasboek_entry is not None,
        "message": (
            f"✅ €{amount_eur:.2f} bijgeschreven op {target.get('naam')}'s wallet. "
            f"Nieuw saldo: €{bucket['balance_eur']:.2f}."
            + (" Ook geboekt in Spark kasboek." if kasboek_entry else "")
        ),
    }
