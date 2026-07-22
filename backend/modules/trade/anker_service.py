"""
Anker Service (v10_anker_skeleton_001) — Hybride gap-up guard voor Spark Trader.
=================================================================================
DOEL: Voorkomen dat de bot bovenaan een gap-up koopt.

RICHTING (Willem, sessie 47): hybride
  1. Bij eerste boot: 1x Bitvavo daily candles ophalen (lookback_days uit blueprint)
     en cachen in data/trade/anker/{market}.json.
  2. Elke ticker-tick: rolling average bijwerken (later — nu skeleton).
  3. Nachtelijke reconciliatie tegen Bitvavo (later).

HOOK: strategy_decision._simple_decision belt anker_service.check_gap_up(market, price)
      NA een BUY-signaal maar VOOR execute. Retourneert:
        {"allow": bool, "reason": str, "anker": float, "current": float, "delta_pct": float}

STATUS: SKELETON — feature flag `anker.enabled` in blueprint staat op FALSE.
        Als flag off is, retourneert check_gap_up altijd allow=True. Zero behavioral change.

VERANTWOORDING: Elke skip logt naar boekhouder papertrail (event_type=anker_skip)
                zodat we effect kunnen meten voordat we live gaan.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger("spark_anker")

MODULE_DIR = Path(__file__).parent
BLUEPRINT_FILE = MODULE_DIR / "blueprints" / "spark_trader.json"
BACKEND_DIR = MODULE_DIR.parent.parent  # /app/backend
DEFAULT_CACHE_DIR = BACKEND_DIR / "data" / "trade" / "anker"


# ============================================================
# Blueprint reader — leest anker-sectie, respecteert feature flag
# ============================================================

def _load_anker_config() -> Dict:
    """Lees anker-sectie uit blueprint. Retourneert dict met defaults als sectie ontbreekt."""
    try:
        bp = json.loads(BLUEPRINT_FILE.read_text())
    except Exception as e:
        logger.warning(f"anker: kan blueprint niet lezen: {e}")
        return {"enabled": False}

    cfg = bp.get("anker") or {}
    # Defaults (safe-off)
    return {
        "enabled": bool(cfg.get("enabled", False)),
        "lookback_days": int(cfg.get("lookback_days", 30)),
        "above_anker_threshold_pct": float(cfg.get("above_anker_threshold_pct", 8.0)),
        "reconciliation_hour_utc": int(cfg.get("reconciliation_hour_utc", 3)),
        "cache_dir": cfg.get("cache_dir", "data/trade/anker"),
        "action_on_above_anker": cfg.get("action_on_above_anker", "log_only"),
    }


def _cache_file(market: str, cache_dir: Optional[Path] = None) -> Path:
    cd = cache_dir or DEFAULT_CACHE_DIR
    cd.mkdir(parents=True, exist_ok=True)
    return cd / f"{market.replace('/', '_')}.json"


# ============================================================
# Anker read/write
# ============================================================

def get_anker(market: str) -> Optional[Dict]:
    """
    Lees anker-cache voor market. Retourneert:
        {"market": str, "anker_price_eur": float, "lookback_days": int,
         "computed_at": iso, "sample_count": int, "source": str}
    None als cache niet bestaat of niet parsebaar is.
    """
    fp = _cache_file(market)
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text())
    except Exception as e:
        logger.warning(f"anker: cache {fp} niet leesbaar: {e}")
        return None


def _save_anker(market: str, anker_price: float, sample_count: int, source: str,
                lookback_days: int) -> Dict:
    """Persist anker-record."""
    record = {
        "market": market,
        "anker_price_eur": round(float(anker_price), 8),
        "lookback_days": lookback_days,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": int(sample_count),
        "source": source,
        "_schema_version": "1.0",
        "_generated_by": "v10_anker_skeleton_001",
    }
    fp = _cache_file(market)
    fp.write_text(json.dumps(record, indent=2))
    return record


# ============================================================
# Hoofd-check — hier plugt strategy_decision in
# ============================================================

def check_gap_up(market: str, current_price: float) -> Dict:
    """
    Check of `current_price` te ver boven anker zit voor deze market.

    Retourneert:
        {
          "allow": bool,             # True = mag kopen, False = skip
          "reason": str,             # menselijke reden
          "anker": float | None,     # anker-prijs (None als cache leeg)
          "current": float,          # meegegeven prijs
          "delta_pct": float,        # (current - anker) / anker * 100
          "enabled": bool,           # feature flag stand
          "action": str,             # log_only / skip / lower_confidence
        }

    FEATURE-FLAG OFF (default) → altijd allow=True, reason="anker feature off".
    """
    cfg = _load_anker_config()

    if not cfg["enabled"]:
        return {
            "allow": True,
            "reason": "anker feature off",
            "anker": None,
            "current": current_price,
            "delta_pct": 0.0,
            "enabled": False,
            "action": "log_only",
        }

    anker_rec = get_anker(market)
    if not anker_rec or not anker_rec.get("anker_price_eur"):
        # Geen cache → laat door (fail-open zolang skeleton nog niet gebooteerd is).
        return {
            "allow": True,
            "reason": f"geen anker-cache voor {market}",
            "anker": None,
            "current": current_price,
            "delta_pct": 0.0,
            "enabled": True,
            "action": "log_only",
        }

    anker = float(anker_rec["anker_price_eur"])
    delta_pct = (current_price - anker) / anker * 100.0 if anker > 0 else 0.0
    threshold = cfg["above_anker_threshold_pct"]
    above = delta_pct > threshold
    action = cfg["action_on_above_anker"]

    # log_only = altijd allow, alleen loggen
    # skip = disallow als above
    # lower_confidence = allow maar caller mag confidence verlagen
    allow = not (above and action == "skip")
    reason = (
        f"prijs €{current_price:.4f} zit {delta_pct:+.2f}% boven anker €{anker:.4f} "
        f"(drempel {threshold}%) → {action}"
        if above else
        f"prijs €{current_price:.4f} zit {delta_pct:+.2f}% t.o.v. anker €{anker:.4f} (binnen drempel)"
    )
    return {
        "allow": allow,
        "reason": reason,
        "anker": anker,
        "current": current_price,
        "delta_pct": round(delta_pct, 4),
        "enabled": True,
        "action": action,
        "above_threshold": above,
    }


# ============================================================
# Boot: eerste-keer cache builden uit Bitvavo candles
# ============================================================

def bootstrap_anker_from_bitvavo(market: str, user_id: str = "user-001") -> Dict:
    """
    Bij eerste boot van feature: 30d daily candles fetchen van Bitvavo,
    simple-mean uitrekenen, cachen. Idempotent: overschrijft bestaande cache.

    Retourneert het opgeslagen record of {"error": ...} als het niet lukt.
    """
    cfg = _load_anker_config()
    lookback_days = cfg["lookback_days"]

    try:
        from .bitvavo_client import BitvavoClient
    except Exception as e:
        return {"error": f"bitvavo_client niet importeerbaar: {e}"}

    try:
        client = BitvavoClient.for_user(user_id)
        # Bitvavo API: /market/{market}/candles?interval=1d&limit={n}
        candles = client.get_candles(market=market, interval="1d", limit=lookback_days)
        if not candles or len(candles) < 3:
            return {"error": f"onvoldoende candles ({len(candles) if candles else 0}) voor {market}"}
        # candle = [timestamp_ms, open, high, low, close, volume]
        closes = [float(c[4]) for c in candles if len(c) >= 5]
        if not closes:
            return {"error": "geen close-prijzen in candles"}
        anker_price = sum(closes) / len(closes)
        record = _save_anker(
            market=market,
            anker_price=anker_price,
            sample_count=len(closes),
            source=f"bitvavo_daily_candles_{lookback_days}d",
            lookback_days=lookback_days,
        )
        logger.info(f"anker gebootstrapt voor {market}: €{anker_price:.4f} ({len(closes)} candles)")
        return record
    except Exception as e:
        return {"error": f"bootstrap failed: {e}"}


# ============================================================
# Papertrail-logging helper (voor hook in strategy_decision)
# ============================================================

def log_anker_event(market: str, decision: Dict, user_id: str = "system") -> None:
    """
    v10_anker_shadow_refactor_001 — log naar `data/trade/shadow_events/YYYY-MM-DD.jsonl`.

    Volgt bestaand shadow-patroon (chat/shadow_observer): dag-jsonl, ts + ts_epoch + event_type.
    Eigen sub-dir onder `trade/` omdat consumers van `data/shadow/events/` chat-schema
    verwachten (user_msg/spark_msg_preview). Trader-events blijven schoon gescheiden.
    """
    try:
        now = datetime.now(timezone.utc)
        day = now.strftime("%Y-%m-%d")
        log_dir = BACKEND_DIR / "data" / "trade" / "shadow_events"
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": now.isoformat(),
            "ts_epoch": now.timestamp(),
            "event_type": "anker_check",
            "market": market,
            "user_id": user_id,
            "allow": decision.get("allow"),
            "action": decision.get("action"),
            "above_threshold": decision.get("above_threshold", False),
            "anker": decision.get("anker"),
            "current": decision.get("current"),
            "delta_pct": decision.get("delta_pct"),
            "reason": decision.get("reason"),
            "enabled": decision.get("enabled"),
        }
        with open(log_dir / f"{day}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"anker: log_event failed: {e}")
