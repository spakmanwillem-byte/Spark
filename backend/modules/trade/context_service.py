"""
Trading Context Service - Leermodule
Analyseert historische candles voor context insights (S/R, market state, patronen).

Principe (Willem's rule): "Context mag nooit trades triggeren, alleen confidence wegen"

Features:
- Dynamische support/resistance met strength + recency
- Market state detection (bull/bear/sideways)
- Weekday pattern analysis (bv zondag-dinsdag dip)
- Volatility tracking
- Per-coin cache (24h fresh)
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import statistics
import logging

from modules.core.storage import load_json, save_json

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "trade" / "context_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Coins waarvoor context wordt gegenereerd
LEARNING_COINS = ["BCH-EUR", "BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR"]
CACHE_FRESH_HOURS = 24


def _cache_file(market: str) -> Path:
    return CACHE_DIR / f"{market.replace('-', '_')}.json"


def _find_support_levels(candles: List[Dict], lows: List[float], window: int = 20, threshold: float = 0.02) -> List[Dict]:
    """Vind dynamische support levels (bounces) met strength + recency decay."""
    if len(lows) < window * 2:
        return []
    supports = []
    for i in range(window, len(lows) - window):
        if all(lows[j] > lows[i] or j == i for j in range(i - window, i + window)):
            supports.append({"price": lows[i], "timestamp": candles[i].get("timestamp", 0)})
    # Cluster binnen 2%
    clustered, used = [], set()
    for i, s1 in enumerate(supports):
        if i in used:
            continue
        cluster = [s1]
        for j, s2 in enumerate(supports[i+1:], start=i+1):
            if abs(s2["price"] - s1["price"]) / s1["price"] < threshold:
                cluster.append(s2)
                used.add(j)
        avg_price = statistics.mean([c["price"] for c in cluster])
        bounces = len(cluster)
        last_ts = max(c["timestamp"] for c in cluster)
        days_ago = (datetime.now(timezone.utc).timestamp() - last_ts / 1000) / 86400
        recency = max(0.5, 1 - (days_ago / 365))
        strength = min(1.0, (bounces / 10) * recency)
        clustered.append({
            "price": round(avg_price, 2),
            "strength": round(strength, 3),
            "bounces": bounces,
            "days_ago": round(days_ago, 1),
        })
    clustered.sort(key=lambda x: x["strength"], reverse=True)
    return clustered[:5]


def _find_resistance_levels(candles: List[Dict], highs: List[float], window: int = 20, threshold: float = 0.02) -> List[Dict]:
    """Zelfde logica als support, op highs."""
    if len(highs) < window * 2:
        return []
    resistances = []
    for i in range(window, len(highs) - window):
        if all(highs[j] < highs[i] or j == i for j in range(i - window, i + window)):
            resistances.append({"price": highs[i], "timestamp": candles[i].get("timestamp", 0)})
    clustered, used = [], set()
    for i, r1 in enumerate(resistances):
        if i in used:
            continue
        cluster = [r1]
        for j, r2 in enumerate(resistances[i+1:], start=i+1):
            if abs(r2["price"] - r1["price"]) / r1["price"] < threshold:
                cluster.append(r2)
                used.add(j)
        avg_price = statistics.mean([c["price"] for c in cluster])
        tests = len(cluster)
        last_ts = max(c["timestamp"] for c in cluster)
        days_ago = (datetime.now(timezone.utc).timestamp() - last_ts / 1000) / 86400
        recency = max(0.5, 1 - (days_ago / 365))
        strength = min(1.0, (tests / 10) * recency)
        clustered.append({
            "price": round(avg_price, 2),
            "strength": round(strength, 3),
            "tests": tests,
            "days_ago": round(days_ago, 1),
        })
    clustered.sort(key=lambda x: x["strength"], reverse=True)
    return clustered[:5]


def _detect_market_state(candles: List[Dict], closes: List[float]) -> Dict:
    """Bull/bear/sideways met MA cross + HH/LL + momentum."""
    if len(closes) < 50:
        return {"trend": "unknown", "confidence": 0.0}
    ma_20 = statistics.mean(closes[-20:])
    ma_50 = statistics.mean(closes[-50:])
    price = closes[-1]
    ma_cross = "bullish" if ma_20 > ma_50 else "bearish"
    recent_highs = [c["high"] for c in candles[-20:]]
    recent_lows = [c["low"] for c in candles[-20:]]
    higher_highs = recent_highs[-1] > max(recent_highs[:-1])
    lower_lows = recent_lows[-1] < min(recent_lows[:-1])
    momentum_pct = ((price - ma_50) / ma_50) * 100
    bull, bear = 0, 0
    if ma_cross == "bullish":
        bull += 1
    else:
        bear += 1
    if higher_highs:
        bull += 1
    if lower_lows:
        bear += 1
    if momentum_pct > 0.5:
        bull += 1
    elif momentum_pct < -0.5:
        bear += 1
    if bull > bear:
        trend = "bull"
        conf = bull / 3
    elif bear > bull:
        trend = "bear"
        conf = bear / 3
    else:
        trend = "sideways"
        conf = 0.5
    return {
        "trend": trend,
        "confidence": round(conf, 3),
        "momentum_pct": round(momentum_pct, 2),
        "ma_20": round(ma_20, 2),
        "ma_50": round(ma_50, 2),
        "indicators": {
            "ma_cross": ma_cross,
            "higher_highs": higher_highs,
            "lower_lows": lower_lows,
        },
    }


def _analyze_patterns(candles: List[Dict], closes: List[float]) -> Dict:
    """Weekday patronen + volatility."""
    if len(candles) < 100:
        return {}
    weekday_data = {i: [] for i in range(7)}
    names = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
    for i in range(1, len(candles)):
        ts = candles[i].get("timestamp", 0) / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        change = ((candles[i]["close"] - candles[i-1]["close"]) / candles[i-1]["close"]) * 100
        weekday_data[dt.weekday()].append(change)
    patterns = {}
    for day, changes in weekday_data.items():
        if len(changes) < 10:
            continue
        avg = statistics.mean(changes)
        patterns[names[day]] = {
            "avg_change_pct": round(avg, 3),
            "samples": len(changes),
            "bias": "bullish" if avg > 0.2 else ("bearish" if avg < -0.2 else "neutral"),
        }
    # Volatility
    volatility = {}
    if len(closes) >= 20:
        recent_vol = statistics.stdev(closes[-20:])
        avg_vol = statistics.stdev(closes)
        ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
        volatility = {
            "state": "high" if ratio > 1.2 else ("low" if ratio < 0.8 else "normal"),
            "ratio": round(ratio, 3),
        }
    return {"weekday_patterns": patterns, "volatility": volatility}


def analyze(candles: List[Dict], market: str = "BCH-EUR") -> Dict:
    """Volledige analyse. Minstens 100 candles vereist."""
    if len(candles) < 100:
        return {
            "market": market,
            "support_levels": [],
            "resistance_levels": [],
            "market_state": {"trend": "unknown", "confidence": 0},
            "patterns": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": f"Te weinig candles ({len(candles)} < 100)",
        }
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    context = {
        "market": market,
        "candles_analyzed": len(candles),
        "support_levels": _find_support_levels(candles, lows),
        "resistance_levels": _find_resistance_levels(candles, highs),
        "market_state": _detect_market_state(candles, closes),
        "patterns": _analyze_patterns(candles, closes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return context


def get_cached(market: str, max_age_hours: int = CACHE_FRESH_HOURS) -> Optional[Dict]:
    """Haal cached context op als fresh."""
    data = load_json(_cache_file(market), default=None)
    if not data or "generated_at" not in data:
        return None
    generated = datetime.fromisoformat(data["generated_at"])
    age_hours = (datetime.now(timezone.utc) - generated).total_seconds() / 3600
    if age_hours < max_age_hours:
        data["cache_age_hours"] = round(age_hours, 2)
        return data
    return None


def save_cache(market: str, context: Dict):
    save_json(_cache_file(market), context)


def apply_context_to_decision(decision: Dict, context: Dict, current_price: float) -> Dict:
    """
    Wegen van context op een decision (NOOIT triggering, alleen confidence bijstellen).
    Returns decision met extra velden: context_boost, near_support, near_resistance, trend_bias.
    """
    if not context or context.get("error"):
        return decision
    confidence = decision.get("confidence", 0.5)
    action = decision.get("action", "HOLD")
    notes = []

    # 1. Support/resistance proximity
    near_support = None
    for s in context.get("support_levels", []):
        if abs(current_price - s["price"]) / current_price < 0.01:  # <1% van support
            near_support = s
            break
    near_resistance = None
    for r in context.get("resistance_levels", []):
        if abs(current_price - r["price"]) / current_price < 0.01:
            near_resistance = r
            break

    if action == "BUY" and near_support:
        boost = near_support["strength"] * 0.2
        confidence = min(0.99, confidence + boost)
        notes.append(f"+{boost:.2f} near support €{near_support['price']} (strength {near_support['strength']})")
    if action == "BUY" and near_resistance:
        confidence = max(0.1, confidence - 0.15)
        notes.append(f"-0.15 too close to resistance €{near_resistance['price']}")

    # 2. Market state
    trend = context.get("market_state", {}).get("trend")
    if action == "BUY" and trend == "bear":
        confidence = max(0.1, confidence - 0.1)
        notes.append("-0.10 bear trend")
    if action == "BUY" and trend == "bull":
        confidence = min(0.99, confidence + 0.05)
        notes.append("+0.05 bull trend")

    # 3. Weekday bias
    today = datetime.now(timezone.utc).strftime("%A").lower()
    dutch_days = {"monday": "maandag", "tuesday": "dinsdag", "wednesday": "woensdag", "thursday": "donderdag", "friday": "vrijdag", "saturday": "zaterdag", "sunday": "zondag"}
    day_key = dutch_days.get(today)
    patterns = context.get("patterns", {}).get("weekday_patterns", {})
    if day_key and day_key in patterns:
        bias = patterns[day_key]["bias"]
        if action == "BUY" and bias == "bearish":
            confidence = max(0.1, confidence - 0.05)
            notes.append(f"-0.05 {day_key} bearish pattern")
        elif action == "BUY" and bias == "bullish":
            confidence = min(0.99, confidence + 0.05)
            notes.append(f"+0.05 {day_key} bullish pattern")

    decision["context_applied"] = True
    decision["context_notes"] = notes
    decision["confidence"] = round(confidence, 3)
    decision["near_support"] = near_support
    decision["near_resistance"] = near_resistance
    decision["trend_bias"] = trend
    return decision
