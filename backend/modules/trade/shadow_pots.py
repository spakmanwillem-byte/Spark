"""
Shadow-potjes systeem (v6_shadow_pot_001 + v6_shadow_cascade_002) — Willem's idee.

Concept (Willem, 2026-05-31):
  Elk origineel potje krijgt 3 shadow-twins (slot 1/2/3).
  Bij een drop + stabilisatie (NIET puur %) → activeer eerstvolgende idle shadow:
    - Origineel BLIJFT OPEN (geen gerealiseerd verlies)
    - Shadow doet BUY op gestabiliseerde lage prijs (na de val)
    - Bij recovery → shadow trail-SELT op winst
  Bij 4e drop-cyclus (alle 3 shadows op): RECYCLE origineel als "shadow-0" en
  herstart de cyclus. Idee: origineel was tenslotte de "eerste shadow" van zichzelf.

Storage: data/trade/shadow_pots.json
  Elke shadow heeft naast id/owner ook `slot` (1/2/3) zodat we 3 lagen kunnen
  onderscheiden in UI ("Shadow 2/3 actief").

Activatie-trigger:
  Niet meer puur profit_pct ≤ -3%. Nu: bodemdetectie via candle-analyse
  (`is_stabilizing_after_drop`). Voorkomt freefall-buys.

v6_shadow_safety_001 (2026-06-01, sessie 19):
  SHADOW_ENABLED feature-flag (default False) — pauzeert shadow-BUYs zolang we
  recycle-bug + data-corruptie aan het opruimen zijn. Origineel-potje BUY/SELL
  blijft normaal werken. Zet True via /api/trade/shadow/flag/enable als alles
  weer gevalideerd is. Reden: recycle archiveerde ACTIVE shadows zonder SELL →
  coin verloren in admin. Plus market/entry-corruptie ontdekt in actieve
  shadows (BCH-shadow met SOL-entry €69 etc.).
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from ..core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SHADOW_FILE = DATA_ROOT / "trade" / "shadow_pots.json"
POTJES_FILE = DATA_ROOT / "financial" / "user_potjes.json"
FLAG_FILE = DATA_ROOT / "trade" / "shadow_flag.json"

# Configuratie
MAX_SHADOWS_PER_POT = 3       # 3-laags piramide (Willem's idee)
MIN_DROP_BEFORE_SHADOW = 0.015  # min -1.5% onder entry voordat bodemdetectie iets doet
STABILIZATION_RANGE_PCT = 0.012  # laatste 5 candles range < 1.2% = vlak/stabiel
STABILIZATION_LOOKBACK = 5        # candles om naar terug te kijken

# v6_shadow_safety_001 — DEFAULT UIT in productie
SHADOW_ENABLED_DEFAULT = False


def is_shadow_enabled() -> bool:
    """v6_shadow_safety_001 — master-flag voor shadow-cascade. Default False.
    Persist in shadow_flag.json zodat admin via API kan toggelen zonder code-deploy.
    """
    try:
        if FLAG_FILE.exists():
            data = load_json(FLAG_FILE, default={})
            return bool(data.get("enabled", SHADOW_ENABLED_DEFAULT))
    except Exception:
        pass
    return SHADOW_ENABLED_DEFAULT


def set_shadow_enabled(enabled: bool, by_user: str = "system") -> dict:
    """Toggle de master-flag. Schrijft persistent."""
    FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"enabled": bool(enabled), "updated_at": _now_iso(), "updated_by": by_user}
    save_json(FLAG_FILE, data)
    return data


def _load() -> dict:
    SHADOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    return load_json(SHADOW_FILE, default={"shadows": []})


def _save(data: dict) -> None:
    save_json(SHADOW_FILE, data)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Bodemdetectie — stabilisatie na drop (Willem's "lijn stabiel na duik")
# ---------------------------------------------------------------------------
def is_stabilizing_after_drop(
    candles: List[Dict],
    entry_price: float,
    current_price: float,
    min_drop: float = MIN_DROP_BEFORE_SHADOW,
    range_thresh: float = STABILIZATION_RANGE_PCT,
    lookback: int = STABILIZATION_LOOKBACK,
) -> dict:
    """
    Detecteer of de markt zich stabiliseert NA een drop t.o.v. entry_price.

    Vereisten (allemaal waar = stabilisatie):
      1. Huidige prijs is significant lager dan entry (drop ≥ min_drop)
      2. Laatste `lookback` candles: (max(high) - min(low)) / min(low) < range_thresh
      3. Geen verdere new low: laatste candle close ≥ vorige close × 0.998

    Returnt: {"stable": bool, "drop_pct": float, "range_pct": float, "reason": str}
    """
    if not candles or len(candles) < lookback:
        return {"stable": False, "drop_pct": 0.0, "range_pct": 0.0,
                "reason": f"insufficient candles ({len(candles) if candles else 0}/{lookback})"}

    drop_pct = (current_price - entry_price) / entry_price
    if drop_pct > -min_drop:
        return {"stable": False, "drop_pct": drop_pct, "range_pct": 0.0,
                "reason": f"drop {drop_pct*100:.2f}% niet groot genoeg (min -{min_drop*100:.1f}%)"}

    last_n = candles[-lookback:]
    highs = [float(c.get("high", c.get("close", 0))) for c in last_n]
    lows = [float(c.get("low", c.get("close", 0))) for c in last_n]
    closes = [float(c.get("close", 0)) for c in last_n]
    min_low = min(lows) if lows else 0.0
    if min_low <= 0:
        return {"stable": False, "drop_pct": drop_pct, "range_pct": 0.0, "reason": "invalid candle data"}

    range_pct = (max(highs) - min_low) / min_low
    if range_pct >= range_thresh:
        return {"stable": False, "drop_pct": drop_pct, "range_pct": range_pct,
                "reason": f"range {range_pct*100:.2f}% nog te volatiel (max {range_thresh*100:.1f}%)"}

    if len(closes) >= 2 and closes[-1] < closes[-2] * 0.998:
        return {"stable": False, "drop_pct": drop_pct, "range_pct": range_pct,
                "reason": "nog verder gezakt (new lower close)"}

    return {"stable": True, "drop_pct": drop_pct, "range_pct": range_pct,
            "reason": f"bodem-formatie: drop {drop_pct*100:.2f}%, range {range_pct*100:.2f}%"}


# ---------------------------------------------------------------------------
# Shadow lifecycle
# ---------------------------------------------------------------------------
def get_shadows_for_pot(pot_id: str, owner_user_id: Optional[str] = None) -> List[dict]:
    """Alle shadows voor een origineel potje (per-user scoped indien owner gegeven)."""
    data = _load()
    out = []
    for s in data.get("shadows", []):
        if s.get("original_pot_id") != pot_id:
            continue
        if owner_user_id and s.get("original_owner_id") != owner_user_id:
            continue
        out.append(s)
    # sort by slot ascending
    out.sort(key=lambda s: int(s.get("slot", 1)))
    return out


def get_active_shadows(pot_id: str, owner_user_id: Optional[str] = None) -> List[dict]:
    """Alle actieve (in-positie) shadows voor een potje."""
    return [s for s in get_shadows_for_pot(pot_id, owner_user_id) if s.get("status") == "active"]


def get_next_idle_shadow(pot_id: str, owner_user_id: str) -> Optional[dict]:
    """De eerstvolgende beschikbare idle shadow (laagste slot eerst)."""
    for s in get_shadows_for_pot(pot_id, owner_user_id):
        if s.get("status") == "idle":
            return s
    return None


def shadow_capacity(pot_id: str, owner_user_id: str) -> dict:
    """
    Toon hoeveel shadows een potje heeft + status per slot.
    Returnt: {"total": 3, "idle": int, "active": int, "closed": int, "slots": {1: status, 2: status, 3: status}}
    """
    shadows = get_shadows_for_pot(pot_id, owner_user_id)
    slots = {}
    counts = {"idle": 0, "active": 0, "closed": 0}
    for s in shadows:
        slot = int(s.get("slot", 1))
        slots[slot] = s.get("status", "idle")
        counts[s.get("status", "idle")] = counts.get(s.get("status", "idle"), 0) + 1
    return {
        "total": MAX_SHADOWS_PER_POT,
        "have": len(shadows),
        **counts,
        "slots": slots,
    }


def create_shadow_for_pot(
    pot_id: str,
    user_id: str,
    market: str,
    capital: float = 10.0,
    slot: Optional[int] = None,
) -> dict:
    """
    Maak een idle shadow voor een (pot_id, user_id). Idempotent per (pot, owner, slot).
    Als slot=None: pak laagste vrije slot (1, 2 of 3). Geeft error als alle slots vol.
    """
    data = _load()
    existing_for_pot = [s for s in data["shadows"]
                        if s.get("original_pot_id") == pot_id
                        and s.get("original_owner_id") == user_id]
    used_slots = {int(s.get("slot", 1)) for s in existing_for_pot
                  if s.get("status") in ("idle", "active")}

    if slot is None:
        for candidate in range(1, MAX_SHADOWS_PER_POT + 1):
            if candidate not in used_slots:
                slot = candidate
                break
        if slot is None:
            return {"success": True, "shadow": None, "created": False,
                    "reason": f"alle {MAX_SHADOWS_PER_POT} shadow-slots bezet voor {pot_id}"}
    else:
        if slot in used_slots:
            existing = next((s for s in existing_for_pot
                             if int(s.get("slot", 1)) == slot
                             and s.get("status") in ("idle", "active")), None)
            return {"success": True, "shadow": existing, "created": False}

    next_idx = len(data["shadows"]) + 1
    shadow = {
        "shadow_id": f"shadow-{next_idx:03d}",
        "slot": int(slot),
        "original_pot_id": pot_id,
        "owner_user_id": user_id,
        "original_owner_id": user_id,
        "market": market,
        "capital": float(capital),
        "status": "idle",
        "activated_at": None,
        "entry_price": None,
        "exit_price": None,
        "trigger_drop_pct": None,
        "trigger_reason": None,
        "profit": None,
        "borrowed_from": None,
        "cycle": _current_cycle(existing_for_pot),
        "created_at": _now_iso(),
        "closed_at": None,
    }
    data["shadows"].append(shadow)
    _save(data)
    return {"success": True, "shadow": shadow, "created": True}


def _current_cycle(existing_for_pot: List[dict]) -> int:
    """Bepaal welke recycle-cyclus we in zitten (start 1, +1 bij elke recycle)."""
    if not existing_for_pot:
        return 1
    return max(int(s.get("cycle", 1)) for s in existing_for_pot)


def activate_shadow(
    pot_id: str,
    entry_price: float,
    drop_pct: float,
    trade_id: Optional[str] = None,
    owner_user_id: Optional[str] = None,
    trigger_reason: Optional[str] = None,
) -> dict:
    """Activeer eerstvolgende idle shadow (laagste slot eerst)."""
    if not owner_user_id:
        return {"success": False, "error": "owner_user_id verplicht"}
    data = _load()
    candidates = [s for s in data["shadows"]
                  if s.get("original_pot_id") == pot_id
                  and s.get("original_owner_id") == owner_user_id
                  and s.get("status") == "idle"]
    if not candidates:
        return {"success": False, "error": f"geen idle shadow voor {pot_id} (owner {owner_user_id})"}
    candidates.sort(key=lambda s: int(s.get("slot", 1)))
    target = candidates[0]
    target["status"] = "active"
    target["activated_at"] = _now_iso()
    target["entry_price"] = float(entry_price)
    target["trigger_drop_pct"] = float(drop_pct)
    target["trade_id"] = trade_id
    if trigger_reason:
        target["trigger_reason"] = trigger_reason
    _save(data)
    return {"success": True, "shadow": target}


def close_shadow(shadow_id: str, exit_price: float, profit: float) -> dict:
    """Sluit een actieve shadow (= shadow doet SELL bij recovery)."""
    data = _load()
    sh = next((s for s in data["shadows"] if s.get("shadow_id") == shadow_id), None)
    if not sh:
        return {"success": False, "error": f"shadow {shadow_id} niet gevonden"}
    if sh.get("status") != "active":
        return {"success": False, "error": f"shadow {shadow_id} niet actief (status={sh.get('status')})"}
    sh["status"] = "closed"
    sh["exit_price"] = float(exit_price)
    sh["profit"] = float(profit)
    sh["closed_at"] = _now_iso()
    _save(data)
    return {"success": True, "shadow": sh}


def recycle_pot_as_shadow_zero(pot_id: str, owner_user_id: str, current_price: float) -> dict:
    """
    Willem's "4e drop wordt origineel".
    Alle 3 shadows zitten vol → bij volgende drop-stabilisatie behandel we het
    ORIGINELE potje als "shadow-0" van een nieuwe cyclus.

    v6_shadow_safety_001 (2026-06-01) — VEILIGHEIDSCHECK:
    Vereist nu dat alle shadows status `closed` zijn (= via SELL gesloten op
    Bitvavo). Voorheen archiveerde we ook `active` shadows → coin op Bitvavo
    raakte uit zicht ("verloren" in admin). Nu blokkeert recycle als er nog
    1 active shadow is → bot stopt met nieuwe BUYs tot SELL automatisch fired.
    """
    data = _load()
    relevant = [s for s in data["shadows"]
                if s.get("original_pot_id") == pot_id
                and s.get("original_owner_id") == owner_user_id
                and not str(s.get("status", "")).startswith("archived")]
    if not relevant:
        return {"success": False, "error": "geen shadows om te recyclen"}
    idle_count = sum(1 for s in relevant if s.get("status") == "idle")
    active_count = sum(1 for s in relevant if s.get("status") == "active")
    closed_count = sum(1 for s in relevant if s.get("status") == "closed")
    if idle_count > 0:
        return {"success": False, "error": f"recycle alleen als 0 idle shadows ({idle_count} gevonden)"}
    if active_count > 0:
        # v6_shadow_safety_001 — BLOKKADE: niet archiveren terwijl er nog
        # ongeslotene posities zijn. Wacht tot trail-SELL ze sluit.
        return {
            "success": False,
            "error": f"recycle geweigerd: {active_count} active shadow(s) nog niet gesloten (zou coin verliezen)",
            "active_count": active_count, "closed_count": closed_count,
        }

    cur_cycle = max(int(s.get("cycle", 1)) for s in relevant)
    for s in relevant:
        if s.get("status") == "closed":
            s["status"] = f"archived_cycle_{cur_cycle}"
            s["archived_at"] = _now_iso()
    _save(data)

    # Maak 3 nieuwe idle shadows in nieuwe cyclus
    market = relevant[0].get("market", "BCH-EUR")
    capital = float(relevant[0].get("capital", 10.0))
    created = []
    for slot in range(1, MAX_SHADOWS_PER_POT + 1):
        r = create_shadow_for_pot(pot_id, owner_user_id, market, capital, slot=slot)
        if r.get("created"):
            # Forceer juiste cycle
            data = _load()
            for s in data["shadows"]:
                if s.get("shadow_id") == r["shadow"]["shadow_id"]:
                    s["cycle"] = cur_cycle + 1
                    s["recycled_from_cycle"] = cur_cycle
            _save(data)
            created.append(r["shadow"]["shadow_id"])
    return {"success": True, "archived_cycle": cur_cycle, "new_cycle": cur_cycle + 1,
            "new_shadow_ids": created}


def auto_ensure_shadows_for_user(user_id: str) -> dict:
    """Zorg dat ELKE non-anchor pot van een user 3 idle shadow-slots heeft."""
    pots_data = load_json(POTJES_FILE, default={"users": {}})
    u = pots_data.get("users", {}).get(user_id, {})
    pots = u.get("potjes", []) or u.get("pots", [])
    created = []
    for p in pots:
        pot_id = p.get("id")
        if not pot_id or p.get("pot_locked"):
            continue
        for slot in range(1, MAX_SHADOWS_PER_POT + 1):
            r = create_shadow_for_pot(
                pot_id=pot_id,
                user_id=user_id,
                market=p.get("market", "BCH-EUR"),
                capital=float(p.get("capital", 10.0)),
                slot=slot,
            )
            if r.get("created"):
                created.append(r["shadow"]["shadow_id"])
    return {"success": True, "user_id": user_id, "created": created, "total_created": len(created)}


def list_shadows_for_user(user_id: str) -> List[dict]:
    """Alle shadows die deze user bezit."""
    data = _load()
    return [s for s in data.get("shadows", []) if s.get("owner_user_id") == user_id]


def stats() -> dict:
    """Aggregate stats voor admin dashboard."""
    data = _load()
    shadows = data.get("shadows", [])
    by_status = {"idle": 0, "active": 0, "closed": 0, "archived": 0}
    total_profit = 0.0
    for s in shadows:
        st = s.get("status", "idle")
        if st.startswith("archived"):
            st = "archived"
        by_status[st] = by_status.get(st, 0) + 1
        if s.get("profit"):
            total_profit += float(s.get("profit", 0))
    return {
        "total": len(shadows),
        "by_status": by_status,
        "total_profit_realized": round(total_profit, 4),
        "max_per_pot": MAX_SHADOWS_PER_POT,
    }


def cleanup_corrupt_active_shadows() -> dict:
    """v6_shadow_safety_001 — Markeer actieve shadows met data-corruptie als
    `archived_corrupt`. Detectie:
      - shadow.market != pot.market (mismatch)
      - shadow.entry_price niet binnen 0.5×..2× van pot.position.entry_price
    Idle slots worden NIET aangeraakt — eerst handmatig beoordelen via UI.
    """
    pots_data = load_json(POTJES_FILE, default={"users": {}})
    pot_lookup = {}
    for uid, u in pots_data.get("users", {}).items():
        for p in u.get("potjes", []) or u.get("pots", []):
            pot_lookup[(uid, p.get("id"))] = p

    now = _now_iso()
    data = _load()
    flagged = []
    for s in data.get("shadows", []):
        if s.get("status") != "active":
            continue
        owner = s.get("original_owner_id")
        pot_id = s.get("original_pot_id")
        pot = pot_lookup.get((owner, pot_id))
        if not pot:
            continue
        pot_market = pot.get("market")
        pot_entry = (pot.get("position") or {}).get("entry_price") or 0
        s_market = s.get("market")
        s_entry = float(s.get("entry_price") or 0)
        reasons = []
        if pot_market and s_market and pot_market != s_market:
            reasons.append(f"market_mismatch pot={pot_market} shadow={s_market}")
        if pot_entry and s_entry:
            ratio = s_entry / pot_entry
            if ratio < 0.5 or ratio > 2.0:
                reasons.append(f"entry_drift pot={pot_entry:.4f} shadow={s_entry:.4f} ratio={ratio:.2f}")
        if reasons:
            s["status"] = "archived_corrupt"
            s["archived_at"] = now
            s["corrupt_reasons"] = reasons
            flagged.append({"shadow_id": s.get("shadow_id"), "pot_id": pot_id,
                            "owner": owner, "reasons": reasons})
    _save(data)
    return {"success": True, "flagged_count": len(flagged), "flagged": flagged}
