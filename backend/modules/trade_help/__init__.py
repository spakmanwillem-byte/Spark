"""
Trader Help Service (v6_trade_help_001)
==========================================
Centrale uitleg-bron voor de Trader. Spark kan via chat
"hoe werkt de trader?" beantwoorden met deze content,
en de UI Trader-Help-tab leest hetzelfde.

Eén bron, twee weergaven (chat + UI).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/trade/help", tags=["trade-help"])


TRADER_HELP_DOC = {
    "title": "📖 Hoe werkt de Trader?",
    "intro": (
        "De Spark-Trader is een **multi-potjes systeem** dat live op Bitvavo handelt. "
        "Elk potje is een kleine, geïsoleerde trading-account met eigen kapitaal, "
        "positie en P&L. De bot beweegt potje voor potje door de markten — nooit "
        "alle eieren in één mandje."
    ),
    "sections": [
        {
            "id": "potjes_systeem",
            "icon": "🏺",
            "title": "Het potjes-systeem",
            "body": [
                "**Tier 1** (starter): 10 potjes à **€10** elk = €100 totaal trading-kapitaal.",
                "**Pot 1 = Staking-anker** 🔒: blijft permanent €10 voor ROAR-staking, doet NIET mee aan trades.",
                "**Pot 2 t/m 10**: actief tradingkapitaal, samen €90.",
                "",
                "**Groei**: winst blijft IN het potje (compound). Zodra alle potjes op €10 staan ",
                "wordt automatisch een 11e potje toegevoegd (volume-uitbreiding, tier 2 begint).",
                "",
                "**Spread**: bij meerdere markten verdeelt de bot potjes round-robin (5×2, 10×1 etc.).",
            ],
        },
        {
            "id": "buy_logic",
            "icon": "🟢",
            "title": "BUY-logica",
            "body": [
                "De monitor scant elke 30s de gekozen markt(en). Bij een **dip-detectie**:",
                "  • Pak het **eerste vrije potje** (laagste nummer, niet locked, niet in positie)",
                "  • Wacht op een **groene candle** als bevestiging",
                "  • Plaats **market-buy** voor het hele potje-bedrag",
                "  • Markeer potje als `is_open=True` met entry_price",
                "",
                "**Beschermingen**:",
                "  • Min-quote check (v6_trade_minorder_001): SOL/BTC/ETH minimum €5 per order",
                "  • Cycle-lock: per monitor-cycle slechts 1 nieuwe positie per user",
                "  • Quick-Buy van user mag wel meerdere tegelijk",
            ],
        },
        {
            "id": "sell_logic",
            "icon": "🔴",
            "title": "SELL-logica (Trailing Stop)",
            "body": [
                "Elk geopend potje volgt deze sell-flow:",
                "",
                "**1. Cent-niveau triggers** (v4_sell_trigger_002): elke prijs-tick check de cent-bewegingen.",
                "**2. Trailing-stop activeren**: zodra +0,5% boven entry → trailing volgt highest_price.",
                "**3. SELL**: wanneer prijs onder `highest_price * (1 - trail_pct)` zakt → market-sell.",
                "",
                "**Sell-balance bescherming** (v6_trade_sell_balance_001):",
                "  • Vóór sell wordt actuele Bitvavo-balance opgevraagd",
                "  • Verkocht wordt `min(potje_amount, api_balance) * 0.999` (anti-dust)",
                "  • Bij €0 balance → duidelijke `NO_BALANCE` error, geen crash",
                "",
                "**Force-sell** (admin): `POST /api/trade/potjes/{user_id}/{pot_id}/force-sell` ",
                "verkoopt direct, zonder trailing — alleen gradatie ≤ 1.",
            ],
        },
        {
            "id": "modes",
            "icon": "⚙️",
            "title": "Modes & Knoppen",
            "body": [
                "**Monitor (auto-trader)**: `POST /api/trade/bot/start/{user_id}` — bot scant continu.",
                "**Stop**: `POST /api/trade/bot/stop/{user_id}` — pauseert maar laat open posities staan.",
                "**Quick Buy**: `POST /api/trade/quick-buy-potje/{user_id}` — user-initiated 1-shot buy.",
                "**Force-sell**: `POST /api/trade/potjes/{user_id}/{pot_id}/force-sell` — admin-only.",
                "",
                "**Resize**: `POST /api/trade/potjes/{user_id}/resize-to-default` — terug naar €10 elk (vereist gesloten posities).",
                "**Toggle lock**: `POST /api/trade/potjes/{user_id}/toggle-lock` — potje (un)locken.",
                "**Distribute**: `POST /api/trade/potjes/{user_id}/distribute` — verdeel potjes over markten.",
            ],
        },
        {
            "id": "veiligheid",
            "icon": "🛡️",
            "title": "Veiligheid & Limieten",
            "body": [
                "**Bitvavo-keys** worden in `/data/system/settings/{user_id}/settings.json` opgeslagen, ",
                "nooit in code. Per user gescheiden.",
                "",
                "**operatorId** (verplicht sinds 2025): wordt automatisch meegestuurd in elke order.",
                "",
                "**Token-gate**: alleen users met **gradatie ≤ 5** mogen trade-bot starten ",
                "(v4_token_gate_001). Pot 1 staking-lock werkt voor iedereen.",
                "",
                "**Max-bedragen** per potje: tier 1 = €10. Bij 11e potje wordt het +€1 per potje.",
                "",
                "**Logs**: elke trade wordt vastgelegd in `/data/wallet/trade_history/{user_id}.json` ",
                "met fee, run_id, requested_amount + effective_amount voor traceability.",
            ],
        },
        {
            "id": "spark_brain",
            "icon": "🧠",
            "title": "Spark's stem in de trades",
            "body": [
                "**De Boekhouder** (`bot-boekhouder`) post elke BUY en SELL in community-chat.",
                "Voorbeeld: *\"📈 Pot 1-3 kocht BCH @ €312.45 voor €5.14 (cycle #1832)\"*.",
                "",
                "**Madelief Stouten** (`bot-madelief`) bewaakt errors in trade-flow. ",
                "Bij `phase=error` in logs → bark in community (max 3 per scan, anti-spam).",
                "",
                "**Closings**: `POST /api/boekhouder/close-cycle/{user_id}` rollupt audit-events ",
                "sinds vorige closing. Spark deelt het ritueel met gebruiker (\"terlens-terug-boek\").",
                "",
                "**Dagelijkse roundup**: elke dag rond 21:00 NL post Boekhouder een samenvatting ",
                "van closings + KB-gezondheid in community (v6_scheduler_001).",
            ],
        },
        {
            "id": "tips",
            "icon": "💡",
            "title": "Tips voor gebruik",
            "body": [
                "• Begin altijd met **kleine bedragen** (€10 per potje). Schaal pas als het stabiel draait.",
                "• Houd Pot 1 **gelocked** voor ROAR-staking — dat is je garantie-bodem.",
                "• Check **bots-status** elke ochtend (`/api/bots/status`). Wakker, daar gaan we.",
                "• Bij twijfel: **force-sell** alle open posities en doe `resize-to-default` voor schoon begin.",
                "• Productie test met **€5,01 SOL-buy** als smoke-test na elke redeploy.",
            ],
        },
    ],
    "links": {
        "monitor_state": "/api/trade/monitor-state",
        "bots_status": "/api/bots/status",
        "audit": "/api/audit/summary",
        "potjes_overzicht": "/api/trade/potjes/{user_id}",
        "trade_history": "/api/trade/history/{user_id}",
    },
}


@router.get("")
async def get_trader_help():
    """Returnt de volledige Trader-help documentatie."""
    return TRADER_HELP_DOC


@router.get("/markdown")
async def get_trader_help_markdown():
    """Returnt de documentatie als één markdown-string (voor Spark chat)."""
    lines = [f"# {TRADER_HELP_DOC['title']}", "", TRADER_HELP_DOC["intro"], ""]
    for sec in TRADER_HELP_DOC["sections"]:
        lines.append(f"## {sec['icon']} {sec['title']}")
        lines.append("")
        for ln in sec["body"]:
            lines.append(ln)
        lines.append("")
    return {"markdown": "\n".join(lines)}
