"""
Strategy Decision Engine v2 — Trend-following variant (v8_engine_switch_001)
=============================================================================
Experimenteel A/B alternatief voor strategy_decision.py (v1).

Filosofie: pure trend-following i.p.v. mean-reversion.
- BUY: 3 opeenvolgende stijgende candles (bullish momentum)
- SELL: 2 opeenvolgende dalende candles (trend broken)
- Geen Bollinger, geen loss-cut, geen event-pauze — puur momentum

WAARSCHUWING: Deze engine is een STUB voor A/B-testing framework. Backtest niet
uitgevoerd. Niet voor productie gebruik. Alleen actief als
blueprint.active_decision_engine == "v2".

Interface (bewust identiek aan v1):
    _simple_decision(candles, position=None, trade_amount=5.0) -> Dict
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, List

# Import shared constants uit v1 (blueprint fee)
from .strategy_decision import BITVAVO_TAKER_FEE

logger = logging.getLogger("spark_monitor")


def _simple_decision(candles: List[Dict], position: Optional[Dict] = None, trade_amount: float = 5.0) -> Dict:
    """v2 stub: 3-candle up = BUY, 2-candle down = SELL."""
    if len(candles) < 4:
        return {"action": "HOLD", "reason": "v2: te weinig candles (<4)", "confidence": 0}

    price = candles[-1]["close"]
    base = {"price": price, "engine": "v2"}

    # In positie? Check 2 dalende candles = SELL
    if position and position.get("is_open"):
        entry = position["entry_price"]
        profit_pct = (price - entry) / entry
        total_fees = trade_amount * BITVAVO_TAKER_FEE * 2
        netto_profit = trade_amount * profit_pct - total_fees

        c1_down = candles[-1]["close"] < candles[-2]["close"]
        c2_down = candles[-2]["close"] < candles[-3]["close"]
        if c1_down and c2_down and netto_profit > 0:
            return {
                **base, "action": "SELL",
                "reason": f"v2: 2 dalende candles + netto €{netto_profit:.4f} > 0",
                "confidence": 0.7,
                "netto_profit": round(netto_profit, 4),
                "position_update": {"close": True},
            }
        return {
            **base, "action": "HOLD",
            "reason": f"v2: in positie, profit {profit_pct*100:+.2f}%",
            "confidence": 0.4,
        }

    # Geen positie: check 3 stijgende candles = BUY
    if len(candles) >= 4:
        c1_up = candles[-1]["close"] > candles[-2]["close"]
        c2_up = candles[-2]["close"] > candles[-3]["close"]
        c3_up = candles[-3]["close"] > candles[-4]["close"]
        if c1_up and c2_up and c3_up:
            return {
                **base, "action": "BUY",
                "reason": "v2: 3 opeenvolgende stijgende candles (momentum)",
                "confidence": 0.6,
                "position_update": {"open": True, "entry_price": price},
            }

    return {**base, "action": "HOLD", "reason": "v2: geen momentum patroon", "confidence": 0.2}


# v1-compat re-exports (voor MonitorService die deze mogelijk gebruikt)
# Deze functies gebruiken we niet direct in v2 maar behouden interface-parity
def _gap_breakout_check(candles):
    return {"signal": "NONE", "reason": "v2 gebruikt geen gap-check"}


def _detect_daily_drop(candles, threshold_pct=5.0):
    # v2 heeft geen event-pauze mechanisme
    return {"is_event": False, "engine": "v2"}
