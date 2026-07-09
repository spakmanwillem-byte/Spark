"""
Trader Intents Service (v8_trader_intents_001)

Spark herkent Nederlandse chat-commando's voor de trader en voert ze direct uit
zonder LLM-call. Volgt hetzelfde patroon als action_intents_service.py.

Ondersteunde intents:
  - trader_start           "start mijn bot" / "zet de trader aan"
  - trader_stop            "stop de bot" / "pauzeer trader"
  - trader_status          "hoe staat mijn bot" / "trader status"
  - trader_pnl             "wat heb ik verdiend" / "eerlijke winst"
  - trader_recent          "laatste trades" / "wat gekocht"
  - trader_baseline_reset  "reset baseline"
  - trader_events          "actieve events" / "shock events"
  - trader_explain         "hoe werkt de trader" / "leg trader uit"

Return-formaat (dict of None):
  {
    "intent": "trader_pnl",
    "message": "<Spark's antwoord in NL>",
    "action": "trader_pnl",       # frontend-hint
    "data": {...},                 # optionele payload
    "fast_path": True,
  }
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
TRADE_DIR = DATA_ROOT / "trade"

# ============================================================
# Trigger-patronen — NL, regex met word-boundaries
# ============================================================

# START
_START_PATTERNS = [
    r"\b(start|begin|zet\s+aan|aanzetten|activeer|opstarten)\s+(m'?n?|mijn|de)?\s*(trader|bot|monitor|handel|handelsbot|trading|traden)\b",
    r"\b(trader|bot|monitor)\s+(aan|starten|start|aanzetten|activeer)\b",
    r"\bzet\s+de?\s+trader\s+aan\b",
    r"\blaat\s+(de\s+)?bot\s+(weer\s+)?draaien\b",
]

# STOP / PAUZE
_STOP_PATTERNS = [
    r"\b(stop|pauzeer|pauze|uitzetten|zet\s+uit|deactiveer|hou\s+op|houd\s+op)\s+(m'?n?|mijn|de)?\s*(trader|bot|monitor|handel|handelsbot|trading|traden)\b",
    r"\b(trader|bot|monitor)\s+(uit|stoppen|stop|uitzetten|pauzeer|op\s+pauze)\b",
    r"\bzet\s+de?\s+trader\s+uit\b",
    r"\bhandel\s+niet\s+meer\b",
]

# STATUS
_STATUS_PATTERNS = [
    r"\b(hoe\s+staat|status|stand\s+van)\s+(m'?n?|mijn|de)\s*(trader|bot|handel)\b",
    r"\bdraait\s+(m'?n?|mijn|de)\s*(trader|bot)\b\??",
    r"\bis\s+(m'?n?|mijn|de)\s*(trader|bot)\s+(aan|actief|bezig)\b",
    r"\btrader\s+status\b",
    r"\bbot\s+status\b",
    r"\bwat\s+doet\s+(m'?n?|mijn|de)\s*(trader|bot)\b\??",
]

# PNL / WINST
_PNL_PATTERNS = [
    r"\b(wat|hoeveel)\s+(heb\s+ik\s+)?(verdiend|winst|gewonnen)\b",
    r"\b(eerlijke?|honest|echte?|netto)\s+(winst|pnl|resultaat)\b",
    r"\b(mijn|m'?n)\s+(winst|pnl|resultaat|opbrengst)\b",
    r"\bwinst[-\s]?verlies\b",
    r"\btrader\s+(winst|pnl|resultaat)\b",
    r"\bhoe\s+veel\s+heb\s+ik\s+(verdiend|winst)\b",
]

# RECENT / HISTORY
_RECENT_PATTERNS = [
    r"\b(laatste|recente)\s+(trades|aankopen|verkopen|orders)\b",
    r"\bwat\s+heb\s+(je|ik)\s+(recent|net|laatst|zojuist)?\s*(gekocht|verkocht|gedaan|gehandeld)\b",
    r"\btrade\s+(history|geschiedenis)\b",
    r"\bhandelsgeschiedenis\b",
    r"\btoon\s+trades\b",
    r"\btrades?\s+(van\s+)?(vandaag|gisteren|deze\s+week)\b",
]

# BASELINE
_BASELINE_PATTERNS = [
    r"\breset\s+(de\s+)?baseline\b",
    r"\bbaseline\s+(reset|opnieuw|herstellen)\b",
    r"\bnieuwe?\s+baseline\b",
]

# EVENTS
_EVENTS_PATTERNS = [
    r"\b(actieve?|welke)\s+(shock[-\s]?)?events?\b",
    r"\b(shock|crash|drop)[-\s]?events?\b",
    r"\bwelke\s+markten?\s+(zijn\s+)?(gepauzeerd|op\s+pauze|stil)\b",
    r"\bevent[-\s]?pauze\b",
]

# EXPLAIN
_EXPLAIN_PATTERNS = [
    r"\b(hoe\s+werkt|leg\s+uit|wat\s+doet|vertel\s+over)\s+(de\s+)?(trader|bot|handelsbot)\b",
    r"\bleg\s+(de\s+)?(trader|bot|handelsbot)\s+uit\b",
    r"\b(uitleg|toelichting)\s+(over\s+)?(de\s+)?(trader|bot|handelsbot)\b",
    r"\btrader\s+(uitleg|filosofie|strategie)\b",
    r"\b(vertel|zeg)\s+(eens\s+)?(iets\s+)?over\s+(de\s+)?(trader|bot|handelsbot)\b",
]


def _match(text: str, patterns: List[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


# ============================================================
# Formatters — Spark's stem in NL
# ============================================================

def _fmt_status(status: Dict[str, Any]) -> str:
    if not status:
        return "Ik kon de status van je bot niet ophalen."
    running = status.get("running") or status.get("active")
    interval = status.get("interval") or status.get("interval_sec")
    markets = status.get("markets") or status.get("active_markets") or []
    if isinstance(markets, list):
        markets_str = ", ".join(markets[:6]) if markets else "geen markten"
    else:
        markets_str = str(markets)
    if running:
        return f"✅ Je trader draait — cycle elke {interval or '?'}s op {markets_str}."
    return f"⏸️ Je trader staat stil. Zeg 'start mijn bot' om weer te beginnen."


def _fmt_pnl(pnl: Dict[str, Any]) -> str:
    realized = pnl.get("realized", {}) or {}
    open_ = pnl.get("open", {}) or {}
    echt = pnl.get("echt_netto_eur")
    ratio = pnl.get("honesty_ratio")
    rz_pnl = realized.get("total_pnl_eur", 0)
    rz_trades = realized.get("total_trades", 0)
    op_dd = open_.get("total_unrealized_eur", 0)
    op_pos = open_.get("positions", 0)
    lines = [
        f"💰 **Eerlijke PnL** ({rz_trades} trades):",
        f"  • Gerealiseerd: €{rz_pnl:+.2f}",
        f"  • Open drawdown ({op_pos} posities): €{op_dd:+.2f}",
        f"  • **ECHT netto: €{echt:+.2f}**" if echt is not None else "",
    ]
    if ratio is not None:
        if ratio >= 0.9:
            lines.append(f"  • Honesty ratio: {ratio} — geen verstopte verliezen ✓")
        elif ratio >= 0:
            lines.append(f"  • Honesty ratio: {ratio} — deel van 'winst' zit nog vast in open posities")
        else:
            lines.append(f"  • Honesty ratio: {ratio} — echt netto is verlies terwijl gerealiseerd winst toont ⚠️")
    return "\n".join(l for l in lines if l)


def _fmt_history(hist: List[Dict]) -> str:
    if not hist:
        return "📜 Geen recente trades gevonden."
    lines = ["📜 **Laatste trades:**"]
    for h in hist[:5]:
        ts = (h.get("timestamp") or h.get("ts") or "")[:16]
        side = h.get("side") or h.get("action") or "?"
        mkt = h.get("market") or "?"
        price = h.get("price") or h.get("entry_price") or "?"
        pnl = h.get("net_pnl_eur") or h.get("pnl_eur") or 0
        lines.append(f"  • {ts} · {side.upper()} {mkt} @ €{price} · PnL €{pnl:+.2f}")
    return "\n".join(lines)


def _fmt_events(events: Dict[str, Any]) -> str:
    active = events.get("active_pauses", []) or events.get("events", []) or []
    if not active:
        return "🌤️ Geen actieve shock-events — alle markten draaien normaal."
    lines = ["🚨 **Actieve event-pauzes:**"]
    for e in active[:6]:
        mkt = e.get("market", "?")
        drop = e.get("drop_pct")
        until = (e.get("pause_until") or "")[:16]
        lines.append(f"  • {mkt} — drop {drop}%, gepauzeerd tot {until}")
    return "\n".join(lines)


# ============================================================
# Uitvoerders — praten direct met modules/data (geen HTTP)
# ============================================================

async def _do_start(user_id: str) -> Dict[str, Any]:
    try:
        from modules.trade.monitor import get_user_monitor
        mon = get_user_monitor(user_id)
        # Token-gate (zelfde als bot_start endpoint)
        users_data = load_json(DATA_ROOT / "system" / "users.json", default={})
        users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
        user_entry = next((u for u in users_list if (u.get("id") or u.get("user_id")) == user_id), None)
        gradatie = (user_entry or {}).get("gradatie", 7)
        if gradatie > 1 and user_id != "user-000":
            roar = load_json(DATA_ROOT / "roar" / "roar_balances.json", default={})
            tokens = int(roar.get("balances", {}).get(user_id, 0))
            if tokens < 1:
                return {"success": False, "message": "Je hebt 0 tokens — bot kan niet starten. 1 token = 1 potje-slot."}
        r = mon.start(interval=300, candle_interval="15m", user_id=user_id, auto_trade=True)
        return {"success": True, "message": "✅ Je trader is gestart. Cycle elke 5 min, ik hou je op de hoogte.", "data": r}
    except Exception as e:
        return {"success": False, "message": f"Kon trader niet starten: {e}"}


async def _do_stop(user_id: str) -> Dict[str, Any]:
    try:
        from modules.trade.monitor import get_user_monitor
        r = get_user_monitor(user_id).stop()
        return {"success": True, "message": "⏸️ Je trader is gestopt.", "data": r}
    except Exception as e:
        return {"success": False, "message": f"Kon trader niet stoppen: {e}"}


def _do_status(user_id: str) -> Dict[str, Any]:
    try:
        from modules.trade.monitor import get_user_monitor
        st = get_user_monitor(user_id).get_status()
        return {"success": True, "message": _fmt_status(st), "data": st}
    except Exception as e:
        return {"success": False, "message": f"Status ophalen mislukt: {e}"}


def _do_pnl(user_id: str) -> Dict[str, Any]:
    """Lees eerlijke PnL direct uit potjes + market_stats (zelfde logica als /honest-pnl endpoint)."""
    try:
        from modules.trade.bitvavo_client import get_price as _get_price
        pots = load_json(TRADE_DIR / "user_potjes.json", default={})
        user_pots = pots.get(user_id, []) or []
        if isinstance(user_pots, dict):
            user_pots = user_pots.get("pots", [])
        stats = load_json(TRADE_DIR / "market_stats.json", default={})
        us = stats.get("users", {}).get(user_id, {}) if isinstance(stats, dict) else {}
        rz_pnl = float(us.get("total_pnl_eur", 0) or 0)
        rz_tr = int(us.get("total_trades", 0) or 0)
        open_pos = 0
        open_dd = 0.0
        for pot in user_pots:
            pos = pot.get("position") or {}
            if not pos.get("is_open"):
                continue
            entry = pos.get("entry_price") or 0
            size = pos.get("size") or 0
            cap = pot.get("capital", 0) or 0
            if not (entry and size and cap):
                continue
            mkt = pos.get("market") or pot.get("last_market")
            cp = entry
            try:
                p = _get_price(mkt) if mkt else None
                if p:
                    cp = float(p)
            except Exception:
                pass
            open_pos += 1
            open_dd += (size * cp) - cap
        echt = rz_pnl + open_dd
        ratio = round(echt / rz_pnl, 2) if rz_pnl > 0 else None
        payload = {
            "realized": {"total_pnl_eur": round(rz_pnl, 2), "total_trades": rz_tr},
            "open": {"positions": open_pos, "total_unrealized_eur": round(open_dd, 2)},
            "echt_netto_eur": round(echt, 2),
            "honesty_ratio": ratio,
        }
        return {"success": True, "message": _fmt_pnl(payload), "data": payload}
    except Exception as e:
        return {"success": False, "message": f"PnL ophalen mislukt: {e}"}


def _do_recent(user_id: str) -> Dict[str, Any]:
    try:
        # trade_history staat in wallet/trade_history/user-XXX.json
        wallet_hist = DATA_ROOT / "wallet" / "trade_history" / f"{user_id}.json"
        hist = load_json(wallet_hist, default=[])
        if not isinstance(hist, list):
            hist = hist.get("trades", []) if isinstance(hist, dict) else []
        hist_sorted = sorted(hist, key=lambda x: x.get("timestamp") or "", reverse=True)
        return {"success": True, "message": _fmt_history(hist_sorted), "data": {"trades": hist_sorted[:5]}}
    except Exception as e:
        return {"success": False, "message": f"Historie ophalen mislukt: {e}"}


def _do_baseline_reset(user_id: str) -> Dict[str, Any]:
    """Reset baseline (zelfde logica als POST /baseline/{user_id} met huidige Bitvavo balance)."""
    try:
        from modules.trade.bitvavo_client import get_balance_eur
        baseline_file = TRADE_DIR / "capital_baseline.json"
        data = load_json(baseline_file, default={}) or {}
        current = get_balance_eur() if callable(get_balance_eur) else None
        if not current:
            return {"success": False, "message": "Kon huidige Bitvavo-balance niet ophalen — baseline niet gereset."}
        data[user_id] = {"baseline_eur": float(current), "reset_at": None}
        # persist
        import json as _json
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_file, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": f"🔁 Baseline gereset naar huidige Bitvavo-balance: €{current:.2f}"}
    except Exception as e:
        return {"success": False, "message": f"Baseline reset mislukt: {e}"}


def _do_events() -> Dict[str, Any]:
    try:
        # events komen uit shared monitor state — vereenvoudigde read
        state = load_json(TRADE_DIR / "monitor_state.json", default={}) or {}
        events = state.get("active_events", []) or []
        payload = {"active_pauses": events}
        return {"success": True, "message": _fmt_events(payload), "data": payload}
    except Exception as e:
        return {"success": False, "message": f"Events ophalen mislukt: {e}"}


def _do_explain() -> Dict[str, Any]:
    """Korte samenvatting + link naar /api/trade/explained."""
    msg = (
        "🤖 **Spark Trader** — kort uitgelegd:\n"
        "• Autonome bot die elke 15 min 6 markten scant (BCH/BTC/ETH/SOL/ADA/ATOM-EUR)\n"
        "• Actieve strategie: **Gap Momentum 50** (confidence 82%) — Bollinger 2σ + gap-body 50% filter\n"
        "• Eigenschappen: mean_reversion · gap_body_50 · loss_cut_48h_3pct · event_pause_5pct_24h · honest_pnl · trailing_stop\n"
        "• Bescherming: 48u loss-cut (-3%), event-auto-pauze bij >5% daily drop, cooldowns\n"
        "• Transparant: eerlijke PnL via `/api/trade/honest-pnl/{user_id}`\n\n"
        "Volledige uitleg met alle test-resultaten: `GET /api/trade/explained`\n"
        "Live confidence-scores: `GET /api/trade/strategy/confidence`"
    )
    return {"success": True, "message": msg, "data": {"endpoints": ["/api/trade/explained", "/api/trade/strategy/confidence"]}}


# ============================================================
# Hoofd-entry — try_detect(text) → intent + reply
# ============================================================

async def try_detect(text: str, user_id: str = "user-001") -> Optional[Dict[str, Any]]:
    """Detecteer trader-intent + voer uit. Return None als geen match.

    Volgorde: specifieke intents (baseline/events/explain) VOOR bredere (start/stop),
    zodat 'reset baseline' niet matcht als 'stop trader'.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()

    intent = None
    result = None

    if _match(t, _BASELINE_PATTERNS):
        intent, result = "trader_baseline_reset", _do_baseline_reset(user_id)
    elif _match(t, _EVENTS_PATTERNS):
        intent, result = "trader_events", _do_events()
    elif _match(t, _EXPLAIN_PATTERNS):
        intent, result = "trader_explain", _do_explain()
    elif _match(t, _PNL_PATTERNS):
        intent, result = "trader_pnl", _do_pnl(user_id)
    elif _match(t, _RECENT_PATTERNS):
        intent, result = "trader_recent", _do_recent(user_id)
    elif _match(t, _STATUS_PATTERNS):
        intent, result = "trader_status", _do_status(user_id)
    elif _match(t, _STOP_PATTERNS):
        intent, result = "trader_stop", await _do_stop(user_id)
    elif _match(t, _START_PATTERNS):
        intent, result = "trader_start", await _do_start(user_id)

    if not intent:
        return None

    return {
        "intent": intent,
        "message": result.get("message", ""),
        "action": intent,
        "data": result.get("data"),
        "success": result.get("success", True),
        "fast_path": True,
    }
