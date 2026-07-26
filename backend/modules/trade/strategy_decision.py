"""
Strategy Decision Engine (v8_refactor_001)
==========================================
Pure decision-logica voor Spark Trader — Bollinger, gap-breakout, drop-detection.

Geëxtraheerd uit monitor.py om die file van 1831→~1500 regels te brengen zonder
gedragswijziging. Alle functies zijn stateless behalve `_BLUEPRINT_CACHE` (mtime-cache).

Externe modules blijven `from .monitor import _simple_decision` doen (facade in monitor.py).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger("spark_monitor")

# ============================================================
# Constanten (blueprint-gerelateerd)
# ============================================================

BLUEPRINT_FILE = Path(__file__).parent / "blueprints" / "spark_trader.json"
BITVAVO_TAKER_FEE = 0.0025  # 0.25%

_BLUEPRINT_CACHE: Dict = {"data": None, "mtime": 0}


def _load_trader_blueprint() -> Dict:
    """v8_blueprint_config_001 — laad spark_trader.json met simpele cache op mtime."""
    try:
        stat = BLUEPRINT_FILE.stat()
        if _BLUEPRINT_CACHE["mtime"] != stat.st_mtime:
            _BLUEPRINT_CACHE["data"] = json.loads(BLUEPRINT_FILE.read_text())
            _BLUEPRINT_CACHE["mtime"] = stat.st_mtime
        return _BLUEPRINT_CACHE["data"] or {}
    except Exception:
        return {}


# ============================================================
# Beslissing per candle-batch
# ============================================================

def _simple_decision(candles: List[Dict], position: Optional[Dict] = None, trade_amount: float = 5.0) -> Dict:
    """
    Decision engine with trailing stop + fee-aware profit guard.
    - Enters LONG bij prijs onder lower Bollinger band (2σ)
    - Activeert trailing stop bij +1% winst
    - Verkoopt bij -0.4% drop vanaf hoogste punt, MITS netto winst na fees > €0.01
    - NOOIT verkopen met verlies (Willem's regel) — behalve bij 48u loss-cut (v8)

    Args:
        candles: Laatste N candles (min 5)
        position: Huidige positie state (None = geen positie)
        trade_amount: EUR bedrag per trade
    """
    if len(candles) < 5:
        return {"action": "HOLD", "reason": "Te weinig data", "confidence": 0}

    closes = [c["close"] for c in candles[-20:]]
    mean = sum(closes) / len(closes)
    variance = sum((x - mean) ** 2 for x in closes) / len(closes)
    std = variance ** 0.5 if variance > 0 else 0.001
    price = candles[-1]["close"]
    lower = mean - 2 * std
    upper = mean + 2 * std

    base = {
        "price": price,
        "mean": round(mean, 2),
        "lower": round(lower, 2),
        "upper": round(upper, 2),
    }

    # ========== HEBBEN WE EEN POSITIE? ==========
    if position and position.get("is_open"):
        entry = position["entry_price"]
        highest = max(position.get("highest_price", entry), price)
        profit_pct = (price - entry) / entry
        bruto_profit = trade_amount * profit_pct
        # Fees: 0.25% buy + 0.25% sell = 0.5% van trade amount
        total_fees = trade_amount * BITVAVO_TAKER_FEE * 2
        netto_profit = bruto_profit - total_fees

        # v4_sell_trigger_002: cent-niveau triggers ipv vaste percentages
        trail_threshold = round(total_fees * 2, 6)
        exit_min_netto = round(total_fees * 1, 6)
        netto_rounded = round(netto_profit, 6)
        trailing_active = position.get("trailing_active", False) or netto_rounded >= trail_threshold
        drop_from_high = (highest - price) / highest if highest else 0

        # v8_time_losscut_001 — 48u loss-cut bij ≥3% verlies (Willems H2, backtest v4)
        try:
            _bp = _load_trader_blueprint()
            _loss_cut_hours = float(_bp.get("parameters", {}).get("loss_cut_hours", 48))
            _loss_cut_pct = float(_bp.get("parameters", {}).get("loss_cut_pct", -0.03))
            _loss_cut_enabled = bool(_bp.get("parameters", {}).get("loss_cut_enabled", True))
        except Exception:
            _loss_cut_hours, _loss_cut_pct, _loss_cut_enabled = 48, -0.03, True

        if _loss_cut_enabled:
            _entry_ts_str = position.get("entry_ts")
            if _entry_ts_str:
                try:
                    _entry_ts = datetime.fromisoformat(_entry_ts_str.replace("Z", "+00:00"))
                    _held_hours = (datetime.now(timezone.utc) - _entry_ts).total_seconds() / 3600
                    if _held_hours >= _loss_cut_hours and profit_pct <= _loss_cut_pct:
                        return {
                            **base,
                            "action": "SELL",
                            "reason": (
                                f"48u loss-cut @ €{price:.4f}. Ingekocht €{entry:.4f} "
                                f"({profit_pct*100:+.2f}%). Netto €{netto_profit:+.4f}. "
                                f"Verlies realiseren > geld bevriezen (Willems H2)."
                            ),
                            "confidence": 0.85,
                            "netto_profit": round(netto_profit, 4),
                            "loss_cut": True,
                            "held_hours": round(_held_hours, 1),
                            "position_update": {"close": True, "loss_cut": True},
                        }
                except Exception as _e:
                    logger.warning(f"loss-cut parse error: {_e}")

        # v11_rebound_h1_exit_001 — Rebound-posities krijgen een scherpe target-exit i.p.v. trailing.
        # Verkoopt zodra netto ≥ target_pct van position. Werkt naast de bestaande trailing (die
        # blijft actief voor grotere winsten na target).
        # v11_extreme_oversold_exit_001 — Zelfde target-exit voor extreme_oversold posities.
        if position.get("strategy_variant") in ("rebound_h1", "extreme_oversold"):
            _target_pct = float(position.get("target_pct", 2.0)) / 100.0
            _netto_pct = netto_profit / trade_amount if trade_amount > 0 else 0
            if _netto_pct >= _target_pct:
                _var = position.get("strategy_variant")
                return {
                    **base,
                    "action": "SELL",
                    "reason": (
                        f"{_var} target bereikt @ €{price:.4f}. Ingekocht €{entry:.4f} "
                        f"({profit_pct*100:+.2f}%). Netto +€{netto_profit:.4f} ({_netto_pct*100:.2f}% ≥ {_target_pct*100:.1f}%)."
                    ),
                    "confidence": 0.9,
                    "netto_profit": round(netto_profit, 4),
                    "strategy_variant": _var,
                    "target_hit": True,
                    "position_update": {"close": True, "target_hit": True},
                }

        if trailing_active and price < highest:
            if netto_rounded >= exit_min_netto:
                return {
                    **base,
                    "action": "SELL",
                    "reason": f"Trail exit @ €{price:.4f} (piek €{highest:.4f}, drop -{drop_from_high*100:.3f}%). Netto +€{netto_profit:.4f}",
                    "confidence": 0.95,
                    "netto_profit": round(netto_profit, 4),
                    "bruto_profit": round(bruto_profit, 4),
                    "fees": round(total_fees, 4),
                    "position_update": {"close": True, "highest_price": highest, "trailing_active": trailing_active},
                }
            else:
                return {
                    **base,
                    "action": "HOLD",
                    "reason": f"Drop maar netto €{netto_profit:.4f} < €{exit_min_netto:.4f}. Wacht op nieuwe piek.",
                    "confidence": 0.3,
                    "netto_profit": round(netto_profit, 4),
                    "position_update": {"highest_price": highest, "trailing_active": trailing_active},
                }

        return {
            **base,
            "action": "HOLD",
            "reason": f"In positie @ €{entry:.4f}. Nu €{price:.4f} ({profit_pct*100:+.3f}%). Netto €{netto_profit:+.4f}. Trail: {'AAN' if trailing_active else f'wacht op +€{trail_threshold:.4f}'}",
            "confidence": 0.5,
            "netto_profit": round(netto_profit, 3),
            "position_update": {"highest_price": highest, "trailing_active": trailing_active},
        }

    # ========== GEEN POSITIE: ZOEK BUY SIGNAAL ==========
    # v11_rebound_h1_001 — Willems H1 rebound (backtest v4: 62.5% van 5%-drops
    # rebounds binnen 24u, mediaan +1.96%). Trigger BUY bij grote drop in 24u
    # ONAFHANKELIJK van Bollinger. Blueprint-controlled (enabled + threshold).
    try:
        _bp = _load_trader_blueprint()
        _rebound_enabled = bool(_bp.get("parameters", {}).get("rebound_enabled", False))
        _rebound_drop = float(_bp.get("parameters", {}).get("rebound_drop_threshold_pct", 3.0))
        _rebound_target = float(_bp.get("parameters", {}).get("rebound_target_pct", 2.0))
    except Exception:
        _rebound_enabled = False
        _rebound_drop, _rebound_target = 3.0, 2.0

    if _rebound_enabled and len(candles) >= 96:  # 96 x 15m = 24u
        _24h_highs = [c.get("high", c.get("close", price)) for c in candles[-96:]]
        _24h_high = max(_24h_highs) if _24h_highs else price
        _drop_24h_pct = (_24h_high - price) / _24h_high * 100 if _24h_high > 0 else 0
        if _drop_24h_pct >= _rebound_drop:
            return {
                **base,
                "action": "BUY",
                "reason": (
                    f"Rebound-trigger (H1): -{_drop_24h_pct:.2f}% drop in 24u (24h-high €{_24h_high:.4f} → nu €{price:.4f}). "
                    f"Threshold ≥{_rebound_drop:.1f}%. Target +{_rebound_target:.1f}% netto."
                ),
                "confidence": 0.75,
                "strategy_variant": "rebound_h1",
                "target_pct": _rebound_target,
                "drop_24h_pct": round(_drop_24h_pct, 3),
                "high_24h": round(_24h_high, 4),
                "position_update": {"open": True, "entry_price": price, "strategy_variant": "rebound_h1", "target_pct": _rebound_target},
            }

    # v11_extreme_oversold_001 — Neef's N-red-then-green patroon (backtest v3: €+3.19 / 21 trades / 180d).
    # Koopt na N rode candles gevolgd door 1 groene met body ≥ ratio × laatste rode body.
    # Optioneel minimum drop-diepte over de N rode candles.
    try:
        _eo_enabled = bool(_bp.get("parameters", {}).get("extreme_oversold_enabled", False))
        _eo_n = int(_bp.get("parameters", {}).get("extreme_oversold_n_red", 3))
        _eo_min_drop = float(_bp.get("parameters", {}).get("extreme_oversold_min_drop_pct", 0.0))
        _eo_body_ratio = float(_bp.get("parameters", {}).get("extreme_oversold_body_ratio", 0.5))
        _eo_target = float(_bp.get("parameters", {}).get("extreme_oversold_target_pct", 2.0))
    except Exception:
        _eo_enabled, _eo_n, _eo_min_drop, _eo_body_ratio, _eo_target = False, 3, 0.0, 0.5, 2.0

    if _eo_enabled and len(candles) >= _eo_n + 1:
        last = candles[-(_eo_n + 1):]  # laatste N+1 candles
        reds = last[:_eo_n]
        green = last[-1]
        # Check: alle N candles rood (close < open)
        all_red = all(c["close"] < c["open"] for c in reds)
        # Check: laatste candle groen (close > open)
        is_green = green["close"] > green["open"]
        # Check: groene body ≥ ratio × laatste rode body
        last_red_body = abs(reds[-1]["open"] - reds[-1]["close"])
        green_body = abs(green["close"] - green["open"])
        body_ok = last_red_body > 0 and green_body >= _eo_body_ratio * last_red_body
        # Check: totale drop over N rode candles ≥ min_drop
        drop_start = reds[0]["open"]
        drop_bottom = min(c["low"] for c in reds)
        total_drop_pct = (drop_start - drop_bottom) / drop_start * 100 if drop_start > 0 else 0
        drop_ok = total_drop_pct >= _eo_min_drop

        if all_red and is_green and body_ok and drop_ok:
            return {
                **base,
                "action": "BUY",
                "reason": (
                    f"Extreme oversold (Neef): {_eo_n} rode candles + groene bevestiging "
                    f"(body {green_body:.4f} ≥ {_eo_body_ratio:.0%}×{last_red_body:.4f}). "
                    f"Totale drop {total_drop_pct:.2f}%. Target +{_eo_target:.1f}% netto."
                ),
                "confidence": 0.8,
                "strategy_variant": "extreme_oversold",
                "target_pct": _eo_target,
                "n_red": _eo_n,
                "total_drop_pct": round(total_drop_pct, 3),
                "position_update": {"open": True, "entry_price": price, "strategy_variant": "extreme_oversold", "target_pct": _eo_target},
            }

    if price <= lower:
        distance_from_upper = (upper - price) / upper if upper > 0 else 1
        if distance_from_upper < 0.015:
            return {
                **base,
                "action": "HOLD",
                "reason": f"Lower band geraakt maar te dicht bij upper ({distance_from_upper*100:.1f}% ruimte) — geen winstpotentieel",
                "confidence": 0.2,
            }

        # v7_dip_confirmation_001 — 1.5% dip guard
        recent_highs = [c.get("high", c.get("close", price)) for c in candles[-20:]]
        window_high = max(recent_highs) if recent_highs else price
        drop_from_window_high = (window_high - price) / window_high if window_high > 0 else 0
        MIN_DIP_PCT = 0.015
        if drop_from_window_high < MIN_DIP_PCT:
            return {
                **base,
                "action": "HOLD",
                "reason": (
                    f"Lower band geraakt maar geen echte dip: prijs €{price:.4f} is slechts "
                    f"{drop_from_window_high*100:.2f}% onder recente piek €{window_high:.4f}. "
                    f"Wacht op ≥{MIN_DIP_PCT*100:.1f}% terugval voor BUY."
                ),
                "confidence": 0.25,
                "window_high": round(window_high, 4),
                "drop_from_high_pct": round(drop_from_window_high * 100, 3),
            }

        return {
            **base,
            "action": "BUY",
            "reason": (
                f"Prijs €{price:.4f} onder lower band €{lower:.4f} én {drop_from_window_high*100:.2f}% "
                f"onder recente piek €{window_high:.4f}. Ruimte tot upper: {distance_from_upper*100:.1f}%"
            ),
            "confidence": min(0.9, (lower - price) / std + 0.5),
            "window_high": round(window_high, 4),
            "drop_from_high_pct": round(drop_from_window_high * 100, 3),
            "position_update": {"open": True, "entry_price": price},
            "_bollinger_action": "BUY",
        }


    band_pos = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    return {
        **base,
        "action": "HOLD",
        "reason": f"Prijs €{price:.2f} in band ({band_pos:.0%}). Wacht op lower band.",
        "confidence": 0.3,
        "band_position": round(band_pos, 2),
    }


# ============================================================
# Gap-breakout confirmation-filter
# ============================================================

def _gap_breakout_check(candles: List[Dict]) -> Dict:
    """
    v7_gap_breakout_001 — Structuur-omslag detector.
    Signaleert BUY als rood→groen candle-flip met body-ratio ≥ 50%.
    Winnaar backtest v2+v3.
    """
    if len(candles) < 2:
        return {"signal": "NONE", "reason": "te weinig candles"}
    prev = candles[-2]
    curr = candles[-1]
    prev_bearish = prev["close"] < prev["open"]
    prev_bullish = prev["close"] > prev["open"]
    curr_bullish = curr["close"] > curr["open"]
    curr_bearish = curr["close"] < curr["open"]

    if prev_bearish and curr_bullish:
        prev_body = abs(prev["open"] - prev["close"])
        curr_body = abs(curr["close"] - curr["open"])
        if curr_body >= prev_body * 0.5 and curr_body > 0:
            return {"signal": "BUY", "reason": f"gap-body: groen body {curr_body:.4f} ≥ 50% van rood body {prev_body:.4f}",
                    "curr_body": round(curr_body, 4), "prev_body": round(prev_body, 4)}
    if prev_bullish and curr_bearish:
        prev_body = abs(prev["close"] - prev["open"])
        curr_body = abs(curr["open"] - curr["close"])
        if curr_body >= prev_body * 0.5 and curr_body > 0:
            return {"signal": "SELL", "reason": f"gap-body inverse: rood body ≥ 50% van groen body"}
    return {"signal": "NONE", "reason": "geen kleuromslag of te kleine body"}


# ============================================================
# Event-detectie (shock-event / daily drop)
# ============================================================

def _detect_daily_drop(candles: List[Dict], threshold_pct: float = 5.0) -> Dict:
    """
    v8_event_protection_001 — Detecteer 'shock-event' in de laatste 24u (96 candles × 15m).
    Return {'is_event': True, 'drop_pct': X, 'peak_price': Y, 'trough_price': Z} als drop >= threshold.
    """
    if len(candles) < 96:
        return {"is_event": False}
    last_24h = candles[-96:]
    peak_high = max(c["high"] for c in last_24h)
    trough_low = min(c["low"] for c in last_24h[-24:])
    if peak_high <= 0:
        return {"is_event": False}
    drop_pct = (peak_high - trough_low) / peak_high * 100
    if drop_pct >= threshold_pct:
        return {"is_event": True, "drop_pct": round(drop_pct, 2),
                "peak_price": round(peak_high, 4), "trough_price": round(trough_low, 4)}
    return {"is_event": False, "drop_pct": round(drop_pct, 2)}
