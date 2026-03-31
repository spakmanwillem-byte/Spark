"""
Trading Context Service
========================
Analyseert historische data voor context insights (GEEN directe trades!)

Principe: "Live = leidend, Context = weging"

Features:
- Dynamische support/resistance met strength + timestamp
- Market state detection (bull/bear/sideways)
- Pattern analysis (weekdag trends, volatiliteit)
- Context verhoogt/verlaagt alleen CONFIDENCE, triggert NOOIT direct

Willem's rule: Context mag nooit trades triggeren, alleen wegen.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import statistics

logger = logging.getLogger(__name__)


class TradingContextService:
    """
    Service voor historische context insights
    
    Output is compact en snel - geen ruwe data, alleen samenvattingen
    """
    
    def __init__(self):
        self.cache_file = Path("/app/backend/data/system/trading_context_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info("📊 Trading Context Service initialized")
    
    @staticmethod
    def analyze_historical_data(candles: List[Dict], market: str = "BCH-EUR") -> Dict:
        """
        Analyseer historische candles voor context insights
        
        Args:
            candles: Lijst met historische candles (sorted oldest → newest)
            market: Trading pair
        
        Returns:
            {
                "support_levels": [...],  # Dynamisch met strength
                "resistance_levels": [...],  # Dynamisch met strength
                "market_state": {...},  # Trend + confidence
                "patterns": {...},  # Weekdag, volatiliteit
                "generated_at": timestamp
            }
        """
        if len(candles) < 100:
            logger.warning(f"⚠️ Insufficient data for context analysis ({len(candles)} candles)")
            return TradingContextService._empty_context()
        
        logger.info(f"🔍 Analyzing {len(candles)} candles for context...")
        
        try:
            # Extract prices
            closes = [float(c['close']) for c in candles]
            highs = [float(c['high']) for c in candles]
            lows = [float(c['low']) for c in candles]
            
            # 1. Support/Resistance (dynamisch)
            support_levels = TradingContextService._find_support_levels(candles, lows)
            resistance_levels = TradingContextService._find_resistance_levels(candles, highs)
            
            # 2. Market State (trend detection)
            market_state = TradingContextService._detect_market_state(candles, closes)
            
            # 3. Patterns (weekdag, volatiliteit)
            patterns = TradingContextService._analyze_patterns(candles, closes)
            
            context = {
                "support_levels": support_levels,
                "resistance_levels": resistance_levels,
                "market_state": market_state,
                "patterns": patterns,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "market": market,
                "candles_analyzed": len(candles)
            }
            
            logger.info(f"✅ Context generated: {len(support_levels)} supports, {len(resistance_levels)} resistances, trend={market_state['trend']}")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error analyzing context: {e}")
            return TradingContextService._empty_context()
    
    @staticmethod
    def _find_support_levels(candles: List[Dict], lows: List[float], window: int = 20, threshold: float = 0.02) -> List[Dict]:
        """
        Vind dynamische support levels met strength
        
        Logic:
        - Zoek lokale minima (bounce points)
        - Cluster nearby bounces (binnen 2%)
        - Bereken strength (aantal bounces, recency)
        """
        if len(lows) < window * 2:
            return []
        
        supports = []
        
        # Find local minima
        for i in range(window, len(lows) - window):
            is_min = True
            for j in range(i - window, i + window):
                if j != i and lows[j] <= lows[i]:
                    is_min = False
                    break
            
            if is_min:
                supports.append({
                    "price": lows[i],
                    "index": i,
                    "timestamp": candles[i]['timestamp']
                })
        
        # Cluster nearby supports (within 2%)
        clustered = []
        used = set()
        
        for i, s1 in enumerate(supports):
            if i in used:
                continue
            
            cluster = [s1]
            for j, s2 in enumerate(supports[i+1:], start=i+1):
                if abs(s2['price'] - s1['price']) / s1['price'] < threshold:
                    cluster.append(s2)
                    used.add(j)
            
            # Calculate cluster stats
            avg_price = statistics.mean([s['price'] for s in cluster])
            bounces = len(cluster)
            last_tested = max([s['timestamp'] for s in cluster])
            
            # Strength: more bounces = stronger, recent test = stronger
            days_ago = (datetime.now(timezone.utc).timestamp() - last_tested / 1000) / 86400
            recency_factor = max(0.5, 1 - (days_ago / 365))  # Decay over 1 year
            strength = min(1.0, (bounces / 10) * recency_factor)  # Max 10 bounces = 1.0
            
            clustered.append({
                "price": round(avg_price, 2),
                "strength": round(strength, 3),
                "bounces": bounces,
                "last_tested": datetime.fromtimestamp(last_tested / 1000, tz=timezone.utc).isoformat(),
                "days_ago": round(days_ago, 1)
            })
        
        # Sort by strength
        clustered.sort(key=lambda x: x['strength'], reverse=True)
        
        # Return top 5
        return clustered[:5]
    
    @staticmethod
    def _find_resistance_levels(candles: List[Dict], highs: List[float], window: int = 20, threshold: float = 0.02) -> List[Dict]:
        """
        Vind dynamische resistance levels met strength
        
        Same logic as support, but for highs
        """
        if len(highs) < window * 2:
            return []
        
        resistances = []
        
        # Find local maxima
        for i in range(window, len(highs) - window):
            is_max = True
            for j in range(i - window, i + window):
                if j != i and highs[j] >= highs[i]:
                    is_max = False
                    break
            
            if is_max:
                resistances.append({
                    "price": highs[i],
                    "index": i,
                    "timestamp": candles[i]['timestamp']
                })
        
        # Cluster nearby resistances
        clustered = []
        used = set()
        
        for i, r1 in enumerate(resistances):
            if i in used:
                continue
            
            cluster = [r1]
            for j, r2 in enumerate(resistances[i+1:], start=i+1):
                if abs(r2['price'] - r1['price']) / r1['price'] < threshold:
                    cluster.append(r2)
                    used.add(j)
            
            avg_price = statistics.mean([r['price'] for r in cluster])
            tests = len(cluster)
            last_tested = max([r['timestamp'] for r in cluster])
            
            days_ago = (datetime.now(timezone.utc).timestamp() - last_tested / 1000) / 86400
            recency_factor = max(0.5, 1 - (days_ago / 365))
            strength = min(1.0, (tests / 10) * recency_factor)
            
            clustered.append({
                "price": round(avg_price, 2),
                "strength": round(strength, 3),
                "tests": tests,
                "last_tested": datetime.fromtimestamp(last_tested / 1000, tz=timezone.utc).isoformat(),
                "days_ago": round(days_ago, 1)
            })
        
        clustered.sort(key=lambda x: x['strength'], reverse=True)
        return clustered[:5]
    
    @staticmethod
    def _detect_market_state(candles: List[Dict], closes: List[float]) -> Dict:
        """
        Detecteer market state: bull/bear/sideways met confidence
        
        Indicators:
        - MA cross (20/50)
        - Higher highs / lower lows
        - Momentum
        - Volatility
        """
        if len(closes) < 50:
            return {"trend": "unknown", "confidence": 0.0}
        
        # Calculate MAs
        ma_20 = statistics.mean(closes[-20:])
        ma_50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else ma_20
        
        current_price = closes[-1]
        
        # Trend indicators
        ma_cross = "bullish" if ma_20 > ma_50 else "bearish"
        
        # Higher highs / lower lows (last 20 candles)
        recent_highs = [float(c['high']) for c in candles[-20:]]
        recent_lows = [float(c['low']) for c in candles[-20:]]
        
        higher_highs = recent_highs[-1] > max(recent_highs[:-1]) if len(recent_highs) > 1 else False
        lower_lows = recent_lows[-1] < min(recent_lows[:-1]) if len(recent_lows) > 1 else False
        
        # Momentum (price vs MA50)
        momentum_pct = ((current_price - ma_50) / ma_50) * 100
        
        if momentum_pct > 2:
            momentum = "strong_positive"
        elif momentum_pct > 0.5:
            momentum = "positive"
        elif momentum_pct < -2:
            momentum = "strong_negative"
        elif momentum_pct < -0.5:
            momentum = "negative"
        else:
            momentum = "neutral"
        
        # Determine trend
        bull_score = 0
        bear_score = 0
        
        if ma_cross == "bullish":
            bull_score += 1
        else:
            bear_score += 1
        
        if higher_highs:
            bull_score += 1
        if lower_lows:
            bear_score += 1
        
        if "positive" in momentum:
            bull_score += 1
        elif "negative" in momentum:
            bear_score += 1
        
        # Calculate trend and confidence
        total_indicators = 3
        
        if bull_score > bear_score:
            trend = "bull"
            confidence = bull_score / total_indicators
        elif bear_score > bull_score:
            trend = "bear"
            confidence = bear_score / total_indicators
        else:
            trend = "sideways"
            confidence = 0.5
        
        # Duration (simplified: how long has current MA cross persisted)
        duration_days = 0
        for i in range(len(closes) - 50, len(closes)):
            if i < 50:
                continue
            ma20_i = statistics.mean(closes[max(0, i-20):i])
            ma50_i = statistics.mean(closes[max(0, i-50):i])
            
            if (ma_cross == "bullish" and ma20_i > ma50_i) or (ma_cross == "bearish" and ma20_i < ma50_i):
                duration_days += 1
            else:
                duration_days = 0
        
        return {
            "trend": trend,
            "confidence": round(confidence, 3),
            "duration_days": duration_days,
            "indicators": {
                "ma_20_50_cross": ma_cross,
                "higher_highs": higher_highs,
                "lower_lows": lower_lows,
                "momentum": momentum,
                "momentum_pct": round(momentum_pct, 2)
            }
        }
    
    @staticmethod
    def _analyze_patterns(candles: List[Dict], closes: List[float]) -> Dict:
        """
        Analyseer patterns: weekdag trends, volatiliteit
        """
        if len(candles) < 100:
            return {}
        
        # Weekday analysis
        weekday_data = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
        
        for i in range(1, len(candles)):
            timestamp = candles[i]['timestamp'] / 1000
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            weekday = dt.weekday()
            
            prev_close = float(candles[i-1]['close'])
            curr_close = float(candles[i]['close'])
            change_pct = ((curr_close - prev_close) / prev_close) * 100
            
            weekday_data[weekday].append(change_pct)
        
        # Aggregate weekday stats
        weekday_patterns = {}
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day, changes in weekday_data.items():
            if len(changes) < 10:
                continue
            
            avg_change = statistics.mean(changes)
            weekday_patterns[weekday_names[day]] = {
                "avg_change_pct": round(avg_change, 3),
                "samples": len(changes),
                "bias": "bullish" if avg_change > 0.2 else ("bearish" if avg_change < -0.2 else "neutral")
            }
        
        # Volatility
        if len(closes) >= 20:
            recent_volatility = statistics.stdev(closes[-20:])
            avg_volatility = statistics.stdev(closes)
            volatility_ratio = recent_volatility / avg_volatility if avg_volatility > 0 else 1.0
            
            volatility_state = "high" if volatility_ratio > 1.2 else ("low" if volatility_ratio < 0.8 else "normal")
        else:
            volatility_state = "unknown"
            volatility_ratio = 1.0
        
        return {
            "weekday_patterns": weekday_patterns,
            "volatility": {
                "state": volatility_state,
                "ratio": round(volatility_ratio, 3)
            }
        }
    
    @staticmethod
    def _empty_context() -> Dict:
        """Return empty context when analysis fails"""
        return {
            "support_levels": [],
            "resistance_levels": [],
            "market_state": {"trend": "unknown", "confidence": 0.0},
            "patterns": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": "Insufficient data"
        }
    
    def save_context(self, context: Dict):
        """Save context to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(context, f, indent=2)
            logger.info(f"💾 Context saved to cache")
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def load_context(self) -> Optional[Dict]:
        """Load context from cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    context = json.load(f)
                    logger.info(f"📂 Context loaded from cache")
                    return context
        except Exception as e:
            logger.error(f"Error loading context: {e}")
        
        return None


# Helper function for monitor service
def get_trading_context(candles: List[Dict], use_cache: bool = True) -> Dict:
    """
    Get trading context (with caching)
    
    Args:
        candles: Historical candles for analysis
        use_cache: Use cached context if available (< 24h old)
    
    Returns:
        Context dict with support/resistance/market_state/patterns
    """
    service = TradingContextService()
    
    # Try cache first
    if use_cache:
        cached = service.load_context()
        if cached:
            # Check if cache is fresh (< 24 hours)
            generated_at = datetime.fromisoformat(cached['generated_at'])
            age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
            
            if age_hours < 24:
                logger.info(f"📦 Using cached context ({age_hours:.1f}h old)")
                return cached
            else:
                logger.info(f"⏰ Cache expired ({age_hours:.1f}h old), regenerating...")
    
    # Generate new context
    context = TradingContextService.analyze_historical_data(candles)
    service.save_context(context)
    
    return context
