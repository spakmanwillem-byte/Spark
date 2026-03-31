"""
Spark Decision Engine
Analyseert candles en genereert koop/verkoop beslissingen

BELANGRIJK:
- Per candle analyse (niet hele dataset)
- Identieke logica voor live en replay
- Alle indicators en config gelogd voor reproduceerbaarheid

WILLEM'S TRADING STRATEGIE:
- 10-Potjes Systeem: Lineair €5.08 → €10.16 over 10 trades (totaal ~€76)
- Bollinger Bands met Midline Groen/Rood zones
- Weekdag Awareness: Zo-Wo = "slechte dagen" (85% van de tijd)
  * Op slechte dagen: alleen kopen BOVEN groene midline
  * Op goede dagen (Do-Za): normaal (bij lower band)
- 4% Buffer van Upper Band (weerstand) om winst te garanderen
- Trailing stop loss (activate: +1%, trigger: -0.4% from high)
- Position state management
- Bitvavo Taker fees: 0.25% = €0.0125 per €5 trade
- REGEL: NOOIT verkopen met verlies - wacht op winst
- Bij extreme daling/tijd: manual reset mogelijk
- Buffer: €0.08 extra per trade voor mistrade/fee speling

FEE BEREKENING (CORRECT):
- Per €5.08 trade: ~€0.0127 buy + ~€0.0127 sell = ~€0.025 total (0.5%)
- Break-even: 0.5% price increase
- Target profit trigger: 1.0% (€0.05 bruto - €0.025 fees = €0.025 netto)
- Trailing stop: 0.4% drop protects gains (min €0.01 netto)
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
import statistics
import logging

logger = logging.getLogger(__name__)


class PositionState:
    """
    Houdt trading positie state bij
    """
    def __init__(self):
        self.position_type = "NONE"  # "LONG", "SHORT", "NONE"
        self.entry_price = None
        self.entry_time = None
        self.highest_price = None
        
        # 10-Potjes Systeem: Lineair van €5.08 → €10.16 over 10 trades
        self.current_pot = 0  # 0-9 (10 potten totaal)
        self.trade_amount = 5.08  # Start bij €5.08 (buffer voor mistrades)
        
        self.trailing_stop_active = False
        self.profit_threshold = 0.01   # +1% voor trailing stop activation
        self.trailing_stop_percent = 0.004  # -0.4% from high
        
    def enter_position(self, position_type: str, price: float, timestamp: int):
        """Open nieuwe positie"""
        self.position_type = position_type
        self.entry_price = price
        self.entry_time = timestamp
        self.highest_price = price
        self.trailing_stop_active = False
        
        # Bereken trade amount voor deze pot (lineair €5.08 → €10.16)
        # Pot 0 = €5.08, Pot 9 = €10.16
        self.trade_amount = 5.08 + (self.current_pot * 0.5644)  # 0.5644 = (10.16-5.08)/9
        
    def update_trailing_stop(self, current_price: float):
        """Update trailing stop logic"""
        if self.position_type == "NONE":
            return None
        
        # Update highest price
        if current_price > self.highest_price:
            self.highest_price = current_price
        
        # Check if trailing stop should activate
        profit_pct = (current_price - self.entry_price) / self.entry_price
        if profit_pct >= self.profit_threshold:
            self.trailing_stop_active = True
        
        # Check trailing stop trigger
        if self.trailing_stop_active:
            drop_from_high = (self.highest_price - current_price) / self.highest_price
            
            if drop_from_high >= self.trailing_stop_percent:
                # WILLEM'S FIX: ECHTE Bitvavo fees zijn €0.07 totaal!
                # Inkoop: 3-4 cent, Verkoop: 3-4 cent = 6-8 cent totaal
                # Voor 1 cent netto winst: €0.08 bruto winst nodig
                profit_per_euro = (current_price - self.entry_price) / self.entry_price
                absolute_profit = profit_per_euro * self.trade_amount
                min_profit_needed = 0.08  # €0.08 bruto = €0.01 netto na €0.07 fees
                
                # DEBUG logging
                logging.info(f"[TRAILING] Entry: €{self.entry_price:.2f}, Current: €{current_price:.2f}, Trade: €{self.trade_amount:.2f}")
                logging.info(f"[TRAILING] Profit: €{absolute_profit:.3f} (need €{min_profit_needed:.3f} for 1 cent netto)")
                
                if absolute_profit >= min_profit_needed:
                    logging.info("[TRAILING] ✅ SELL triggered (1 cent netto winst)")
                    return "TRIGGER_STOP"  # Sell signal (veilig)
                else:
                    # Niet verkopen: zou verlies geven na fees
                    logging.warning(f"[TRAILING] ❌ BLOCKED: Only €{absolute_profit:.3f}, need €{min_profit_needed:.3f}!")
                    # Reset trailing stop en wacht opnieuw op +1%
                    self.trailing_stop_active = False
                    return None
        
        return None
    
    def calculate_pnl(self, current_price: float) -> Dict:
        """Bereken current P&L"""
        if self.position_type == "NONE" or self.entry_price is None:
            return {"pnl_eur": 0, "pnl_percent": 0}
        
        pnl_percent = (current_price - self.entry_price) / self.entry_price
        pnl_eur = self.trade_amount * pnl_percent
        
        return {
            "pnl_eur": round(pnl_eur, 2),
            "pnl_percent": round(pnl_percent * 100, 2)
        }
    
    def exit_position(self):
        """Sluit positie"""
        self.position_type = "NONE"
        self.entry_price = None
        self.entry_time = None
        self.highest_price = None
        self.trailing_stop_active = False
        
        # Verhoog pot counter (cycle door 10 potten)
        self.current_pot = (self.current_pot + 1) % 10
    
    def to_dict(self) -> Dict:
        """Export state als dict"""
        return {
            "position_type": self.position_type,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "highest_price": self.highest_price,
            "trade_amount": round(self.trade_amount, 2),
            "current_pot": self.current_pot,
            "trailing_stop_active": self.trailing_stop_active
        }


class SparkDecisionEngine:
    """
    Decision Engine voor crypto trading simulation
    Gebruikt Bollinger Bands + Trailing Stop
    """
    
    DEFAULT_CONFIG = {
        "bb_period": 20,           # Bollinger Bands period
        "bb_std_dev": 2,           # Standard deviations
        "trade_amount": 5.08,      # €5.08 per trade (buffer voor mistrades)
        "trailing_profit": 0.01,   # +1% to activate
        "trailing_stop": 0.004,    # -0.4% from high
        "max_loss_lock": 0.03,     # -3% triggers trading lock
        "interval": "1h"           # 1-hour candles (OPTIMAL for 1% target)
    }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Optional[Dict]:
        """
        Calculate Bollinger Bands + Midlines (Groen/Rood zones)
        
        Returns:
            {
                "upper": float,
                "middle": float (SMA),
                "lower": float,
                "green_midline": float (tussen middle en lower),
                "red_midline": float (tussen middle en upper)
            }
        """
        if len(prices) < period:
            return None
        
        # CRITICAL: Ensure all prices are floats (not strings!)
        prices = [float(p) for p in prices]
        
        recent_prices = prices[-period:]
        middle = statistics.mean(recent_prices)
        std = statistics.stdev(recent_prices)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # Willem's Midline Strategie:
        # Groen zone: tussen lower en middle (midline op 50%)
        # Rood zone: tussen middle en upper (midline op 50%)
        green_midline = (middle + lower) / 2
        red_midline = (middle + upper) / 2
        
        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "green_midline": round(green_midline, 2),
            "red_midline": round(red_midline, 2)
        }
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI (voor extra confirmatie)"""
        if len(prices) < period + 1:
            return None
        
        # Ensure all prices are floats
        prices = [float(p) for p in prices]
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    @staticmethod
    def analyze_candle(
        candle: Dict,
        context: List[Dict],
        config: Optional[Dict] = None,
        position_state: Optional[PositionState] = None,
        trading_locked: bool = False,
        historical_context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze single candle met volledige trading logic
        
        Args:
            candle: Current candle
            context: Previous candles
            config: Config dict
            position_state: Current position state
            trading_locked: If True, no new trades allowed
            
        Returns:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": 0.0-1.0,
                "indicators": {...},
                "reason": str,
                "position_update": {...},
                "pnl": {...},
                "lock_triggered": bool
            }
        """
        if config is None:
            config = SparkDecisionEngine.DEFAULT_CONFIG.copy()
        
        if position_state is None:
            position_state = PositionState()
        
        # Extract prices (ENSURE FLOAT conversion!)
        all_candles = context + [candle]
        prices = [float(c["close"]) for c in all_candles]
        current_price = float(candle["close"])
        
        # Calculate indicators
        bb = SparkDecisionEngine.calculate_bollinger_bands(
            prices, 
            config["bb_period"], 
            config["bb_std_dev"]
        )
        rsi = SparkDecisionEngine.calculate_rsi(prices, 14)
        
        # Default response
        action = "HOLD"
        confidence = 0.0
        reason = "Wachten op signaal"
        lock_triggered = False
        
        # Check if sufficient data
        if bb is None:
            reason = "Onvoldoende data voor Bollinger Bands"
            return {
                "action": action,
                "confidence": confidence,
                "indicators": {"bb": None, "rsi": rsi, "price": current_price},
                "reason": reason,
                "position_update": position_state.to_dict(),
                "pnl": position_state.calculate_pnl(current_price),
                "lock_triggered": lock_triggered,
                "config_used": config
            }
        
        # === TRAILING STOP CHECK (altijd eerst) ===
        if position_state.position_type == "LONG":
            stop_trigger = position_state.update_trailing_stop(current_price)
            
            if stop_trigger == "TRIGGER_STOP":
                pnl = position_state.calculate_pnl(current_price)  # Bereken PnL VOOR exit
                action = "SELL"
                confidence = 1.0
                reason = f"Trailing stop triggered (-0.4% from high €{position_state.highest_price}). P&L: €{pnl['pnl_eur']:.2f} ({pnl['pnl_percent']:.2f}%)"
                
                # Check for trading lock (bad trade)
                if pnl["pnl_percent"] < -config["max_loss_lock"] * 100:
                    lock_triggered = True
                    reason += " | ⚠️ TRADING LOCK ACTIVATED (loss > 3%)"
                
                position_state.exit_position()
                
                return {
                    "action": action,
                    "confidence": confidence,
                    "indicators": {
                        "bb": bb,
                        "rsi": rsi,
                        "price": current_price
                    },
                    "reason": reason,
                    "position_update": position_state.to_dict(),
                    "pnl": pnl,  # Use pre-calculated PnL
                    "lock_triggered": lock_triggered,
                    "config_used": config
                }
        
        # === WEEKDAG DETECTIE ===
        # Detecteer "slechte dagen" (Zondag-Woensdag = 85% van de tijd)
        candle_dt = datetime.fromtimestamp(candle["timestamp"] / 1000, tz=timezone.utc)
        weekday = candle_dt.weekday()  # 0=Monday, 6=Sunday
        weekday_name = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"][weekday]
        
        # Zondag=6, Maandag=0, Dinsdag=1, Woensdag=2
        is_bad_day = weekday in [6, 0, 1, 2]  # Zo, Ma, Di, Wo
        
        # === NEW TRADE LOGIC (if no position) ===
        if position_state.position_type == "NONE" and not trading_locked:
            # WILLEM'S STRATEGIE (BALANCED):
            # Op slechte dagen (85%): voorkeur voor kopen BOVEN groene midline (hogere confidence)
            # Op goede dagen: normale Bollinger strategie
            
            buy_triggered = False
            
            # Check if prijs bij lower band (buy zone)
            at_lower_band = current_price <= bb["lower"] * 1.002
            above_green_midline = current_price >= bb["green_midline"]
            
            if at_lower_band:
                if is_bad_day:
                    # Slechte dag: Wel kopen, maar hogere confidence als boven groene midline
                    if above_green_midline:
                        action = "BUY"
                        confidence = 0.8  # Hoge confidence
                        reason = f"[{weekday_name}] Lower band (€{bb['lower']:.2f}) + BOVEN groene midline (€{bb['green_midline']:.2f}) ✅"
                        buy_triggered = True
                    else:
                        # Onder groene midline = lagere confidence, maar nog steeds kopen
                        action = "BUY"
                        confidence = 0.5  # Lage confidence
                        reason = f"[{weekday_name}] Lower band (€{bb['lower']:.2f}), onder groene midline (€{bb['green_midline']:.2f}) ⚠️"
                        buy_triggered = True
                else:
                    # Goede dag (Do-Za): Normale Bollinger strategie
                    action = "BUY"
                    confidence = 0.8
                    reason = f"[{weekday_name}] Goede dag: lower band (€{bb['lower']:.2f}) ✅"
                    buy_triggered = True
            
            # 4% BUFFER CHECK (weerstand check)
            # Voorkom kopen te dicht bij upper band (maximaal 4% van bovenkant)
            if buy_triggered:
                distance_from_upper = (bb["upper"] - current_price) / bb["upper"]
                if distance_from_upper < 0.04:  # Minder dan 4% ruimte
                    action = "HOLD"
                    confidence = 0.0
                    reason = f"[{weekday_name}] Te dicht bij upper band ({distance_from_upper*100:.1f}% < 4%) - geen ruimte voor winst ⚠️"
                    buy_triggered = False
            
            # Open position als buy triggered
            if buy_triggered:
                position_state.enter_position("LONG", current_price, candle["timestamp"])
        
        # === POSITION MONITORING ===
        elif position_state.position_type == "LONG":
            pnl = position_state.calculate_pnl(current_price)
            
            # WILLEM'S VERKOOP STRATEGIE:
            # 1. Wacht tot +1% winst (activates trailing stop)
            # 2. Trailing stop op 0.4% drop vanaf hoogste punt
            # 3. Resultaat: €0.05 - €0.02 - €0.025 fees = €0.005 (1 cent netto)
            # 4. Upper band check (4% buffer) alleen als emergency exit bij 2%+ winst
            
            should_sell = False
            
            # Check 1: Trailing stop (belangrijkste exit)
            # Dit is al gehandled bovenaan in de functie, maar we checken status
            if position_state.trailing_stop_active:
                # Trailing stop is actief, wacht op drop trigger
                action = "HOLD"
                confidence = 0.6
                reason = f"Trailing stop ACTIEF (pot {position_state.current_pot + 1}/10). Hoogste: €{position_state.highest_price:.2f}, Nu: €{current_price:.2f}. P&L: €{pnl['pnl_eur']:.2f} ({pnl['pnl_percent']:.2f}%)"
            
            # Check 2: Emergency exit bij upper band (alleen als ≥2% winst)
            elif pnl['pnl_percent'] >= 2.0:
                sell_threshold = bb["upper"] * 0.96  # 4% buffer
                if current_price >= sell_threshold:
                    action = "SELL"
                    confidence = 0.9
                    reason = f"Emergency exit: 2%+ winst bij upper band. P&L: €{pnl['pnl_eur']:.2f} ({pnl['pnl_percent']:.2f}%) ✅"
                    should_sell = True
                else:
                    action = "HOLD"
                    confidence = 0.7
                    reason = f"Goede winst ({pnl['pnl_percent']:.2f}%), wacht op upper band of trailing. P&L: €{pnl['pnl_eur']:.2f}"
            
            # Check 3: Normale hold (wacht op +1% voor trailing activation)
            else:
                action = "HOLD"
                confidence = 0.5
                if pnl['pnl_percent'] >= 0:
                    reason = f"In positie (pot {position_state.current_pot + 1}/10, €{position_state.trade_amount:.2f}). P&L: €{pnl['pnl_eur']:.2f} ({pnl['pnl_percent']:.2f}%). Wacht op +1% voor trailing..."
                else:
                    reason = f"In positie (pot {position_state.current_pot + 1}/10, €{position_state.trade_amount:.2f}). P&L: €{pnl['pnl_eur']:.2f} ({pnl['pnl_percent']:.2f}%). Hold..."
            
            # Exit position NA het loggen van PnL
            if should_sell:
                position_state.exit_position()
                # Return direct met PnL die we al berekend hebben (voor exit)
                return {
                    "action": action,
                    "confidence": confidence,
                    "indicators": {
                        "bb": bb,
                        "rsi": rsi,
                        "price": current_price
                    },
                    "reason": reason,
                    "position_update": position_state.to_dict(),
                    "pnl": pnl,  # Use pre-calculated PnL
                    "lock_triggered": lock_triggered,
                    "config_used": config
                }
        
        # === LOCKED STATE ===
        elif trading_locked:
            action = "HOLD"
            confidence = 0.0
            reason = "⚠️ TRADING LOCKED - handmatige reset vereist"
        
        # === CONTEXT WEGING (alleen confidence aanpassen, GEEN directe trades) ===
        base_confidence = confidence
        context_adjustments = []
        
        if historical_context and action in ['BUY', 'SELL']:
            # Max total impact: ±30%
            MAX_CONTEXT_IMPACT = 0.30
            total_adjustment = 0.0
            
            # 1. Support/Resistance proximity
            if action == "BUY" and historical_context.get('support_levels'):
                for sup in historical_context['support_levels']:
                    distance_pct = abs(current_price - sup['price']) / sup['price'] * 100
                    if distance_pct < 2:  # Within 2%
                        # Near strong support = extra buy confidence
                        adjustment = 0.10 * sup['strength']  # Max +10% per level
                        total_adjustment += adjustment
                        context_adjustments.append(f"Near support €{sup['price']} (str={sup['strength']:.2f}) +{adjustment:.2%}")
                        break
            
            if action == "BUY" and historical_context.get('resistance_levels'):
                for res in historical_context['resistance_levels']:
                    distance_pct = abs(current_price - res['price']) / res['price'] * 100
                    if distance_pct < 2:  # Within 2%
                        # Near strong resistance = lower buy confidence
                        adjustment = -0.10 * res['strength']  # Max -10% per level
                        total_adjustment += adjustment
                        context_adjustments.append(f"Near resistance €{res['price']} (str={res['strength']:.2f}) {adjustment:.2%}")
                        break
            
            # 2. Market trend
            market_state = historical_context.get('market_state', {})
            trend = market_state.get('trend')
            trend_conf = market_state.get('confidence', 0)
            
            if trend and trend_conf > 0.5:  # Only if confident trend
                if action == "BUY" and trend == "bull":
                    adjustment = 0.15 * trend_conf  # Max +15%
                    total_adjustment += adjustment
                    context_adjustments.append(f"Bull trend (conf={trend_conf:.2f}) +{adjustment:.2%}")
                elif action == "BUY" and trend == "bear":
                    adjustment = -0.15 * trend_conf  # Max -15%
                    total_adjustment += adjustment
                    context_adjustments.append(f"Bear trend (conf={trend_conf:.2f}) {adjustment:.2%}")
                elif action == "SELL" and trend == "bear":
                    adjustment = 0.10 * trend_conf  # Easier to sell in bear
                    total_adjustment += adjustment
                    context_adjustments.append(f"Bear trend (conf={trend_conf:.2f}) +{adjustment:.2%}")
            
            # Apply adjustment (capped at ±30%)
            total_adjustment = max(-MAX_CONTEXT_IMPACT, min(MAX_CONTEXT_IMPACT, total_adjustment))
            confidence = max(0.0, min(1.0, confidence + total_adjustment))
            
            # Log context weging
            if context_adjustments:
                logging.info("🧠 CONTEXT WEGING:")
                logging.info(f"   Base confidence: {base_confidence:.2%}")
                for adj in context_adjustments:
                    logging.info(f"   • {adj}")
                logging.info(f"   Final confidence: {confidence:.2%} (Δ {confidence - base_confidence:+.2%})")
        
        return {
            "action": action,
            "confidence": confidence,
            "base_confidence": base_confidence,  # Voor logging
            "context_adjustments": context_adjustments,  # Voor logging
            "indicators": {
                "bb": bb,
                "rsi": rsi,
                "price": current_price
            },
            "reason": reason,
            "position_update": position_state.to_dict(),
            "pnl": position_state.calculate_pnl(current_price),
            "lock_triggered": lock_triggered,
            "config_used": config
        }
