"""v13c_trade_routes_split_001 (sessie 54) — Strategy + Explained + PnL + Engine
routes extracted from monolithic routes.py (3115 → 2357 regels).

Deelt de gedeelde `router` uit routes.py zodat endpoints identiek bereikbaar
blijven onder /api/trade/*. Geen breaking changes.
"""
from fastapi import Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import json
import re
from modules.core.storage import load_json, save_json
from .routes import router, DATA_DIR, SETTINGS_DIR, TRADE_DIR

# ============================================================
# v8_trader_explained_001 — Publieke uitleg-JSON voor privacyverklaring
# ============================================================

@router.get("/explained")
async def get_trader_explained():
    """Volledig transparante uitleg van Spark Trader voor bezoekers/auditors.

    Publieke leesroute — geen auth, geen user-id. Bedoeld voor:
    - Privacyverklaring "inhoudelijk bekijken"-link
    - Onafhankelijke auditors / journalistiek
    - Users die willen weten wat de bot precies doet

    Bron: backend/data/trade/spark_trader_public.json (single source of truth,
    handmatig onderhouden bij elke wezenlijke strategie-wijziging).
    """
    try:
        pad = TRADE_DIR / "spark_trader_public.json"
        data = load_json(pad) or {}
        return data
    except Exception as e:
        return {"success": False, "error": f"kan uitleg niet laden: {e}"}


# ============================================================
# v8_strategy_confidence_001 — Live confidence score per strategie
# ============================================================

@router.get("/strategy/confidence")
async def get_strategy_confidence(strategy_id: Optional[str] = None):
    """Live confidence-score per strategie op basis van blueprint + huidige data.

    Berekening (max 100):
      backtest_pass    → 30 (heeft ≥180d backtest met positieve gerealiseerd PnL)
      random_seed_pass → 15 (beter dan random-median of laagvariantie)
      bear_pass        → 15 (bear-market PnL > 0)
      honest_pnl_track → 20 (heeft honest_pnl loss-cut mechanisme)
      live_track       → 0-20 (opgebouwd uit live trade history; 0 = geen data)

    Return: dict per strategie of specifiek voor strategy_id.
    """
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    def score_one(sid: str, s: dict) -> Dict[str, Any]:
        conf = s.get("confidence", {}) or {}
        based = conf.get("gebaseerd_op", {}) or {}
        props = s.get("properties", []) or []

        # Bereken componenten live
        backtest_pass = 30 if (based.get("gerealiseerd_pnl_180d", 0) > 0 or based.get("gerealiseerd_pnl_360d", 0) > 0) else 10
        random_pass = 15 if based.get("random_seed_validatie") else 0
        bear_pass = 15 if based.get("bear_market_pnl", 0) > 0 else 0
        honest_track = 20 if ("loss_cut_48h_3pct" in props or "honest_pnl" in props) else 0
        # Live: check of er trade_history is voor deze strategie (proxy: is deze strategie actief?)
        live_track = 0
        if s.get("actief"):
            try:
                stats = load_json(TRADE_DIR / "market_stats.json", default={}) or {}
                total_users_trades = sum(u.get("total_trades", 0) for u in stats.get("users", {}).values())
                if total_users_trades > 0:
                    live_track = min(20, total_users_trades // 5)
            except Exception:
                pass

        computed_score = backtest_pass + random_pass + bear_pass + honest_track + live_track
        stored_score = conf.get("score", 0)

        return {
            "strategy_id": sid,
            "display_name": s.get("display_name", sid),
            "actief": bool(s.get("actief")),
            "properties": props,
            "confidence_score_stored": stored_score,
            "confidence_score_computed": min(100, computed_score),
            "breakdown": {
                "backtest_pass": backtest_pass,
                "random_seed_pass": random_pass,
                "bear_market_pass": bear_pass,
                "honest_pnl_track": honest_track,
                "live_track": live_track,
            },
            "hypothese_lineage": s.get("hypothese_lineage", {}),
            "spark_alignment": s.get("spark_alignment", {}),
        }

    if strategy_id:
        s = strategieën.get(strategy_id)
        if not s:
            return {"success": False, "error": f"strategie '{strategy_id}' niet gevonden"}
        return {"success": True, "strategy": score_one(strategy_id, s)}

    # Alle strategieën
    result = {sid: score_one(sid, s) for sid, s in strategieën.items()}
    return {
        "success": True,
        "actieve_strategie": bp.get("actieve_strategie"),
        "strategies": result,
        "_note": "computed = live berekening, stored = handmatig ingesteld in blueprint. Live groeit als trade_history data binnenkomt.",
    }



# ============================================================
# v8_strategy_synthesize_001 — Spark synthetiseert nieuwe strategieën uit properties
# ============================================================

# Property catalog — alle bekende bouwstenen met hun eigenschappen
_PROPERTY_CATALOG = {
    "bollinger_2sigma": {
        "categorie": "signaal",
        "beschrijving": "BUY-signaal wanneer prijs onder Bollinger lower band 2σ zakt (mean-reversion)",
        "conflicts_with": [],
        "requires": [],
    },
    "mean_reversion": {
        "categorie": "filosofie",
        "beschrijving": "Onderneemt kopen bij afwijking van gemiddelde, verwacht terugkeer",
        "conflicts_with": ["trend_following"],
        "requires": [],
    },
    "trend_following": {
        "categorie": "filosofie",
        "beschrijving": "Volgt bestaande momentum-richting (buy-high-sell-higher)",
        "conflicts_with": ["mean_reversion"],
        "requires": [],
    },
    "gap_body_50": {
        "categorie": "confirmatie",
        "beschrijving": "Laatste groene candle moet ≥50% van vorige rode body dekken",
        "conflicts_with": ["gap_body_95"],
        "requires": [],
    },
    "gap_body_95": {
        "categorie": "confirmatie",
        "beschrijving": "Strenge variant: 95% dekking (blokkeerde 100% signalen in backtest — niet aanbevolen)",
        "conflicts_with": ["gap_body_50"],
        "requires": [],
    },
    "n_red_green_pattern": {
        "categorie": "confirmatie",
        "beschrijving": "3 rode candles gevolgd door 1 groene (Neef's variant, extreme oversold)",
        "conflicts_with": [],
        "requires": [],
    },
    "loss_cut_48h_3pct": {
        "categorie": "bescherming",
        "beschrijving": "Forceer SELL na 48u als positie ≤-3% verlies staat (verlies zichtbaar realiseren)",
        "conflicts_with": ["hold_indefinitely"],
        "requires": [],
    },
    "hold_indefinitely": {
        "categorie": "bescherming",
        "beschrijving": "Verkoop nooit met verlies — geeft 100% win-rate maar verbergt drawdown",
        "conflicts_with": ["loss_cut_48h_3pct"],
        "requires": [],
    },
    "event_pause_5pct_24h": {
        "categorie": "bescherming",
        "beschrijving": "Bij daily drop >5% → markt 24u pauze + notificatie",
        "conflicts_with": [],
        "requires": [],
    },
    "trailing_stop": {
        "categorie": "exit",
        "beschrijving": "Activeert bij +0.5% winst, sluit bij -0.4% terugval vanaf top",
        "conflicts_with": [],
        "requires": [],
    },
    "fee_aware_sell": {
        "categorie": "exit",
        "beschrijving": "Weigert SELL als netto na 0.25% Bitvavo-fee < €0.01 winst",
        "conflicts_with": [],
        "requires": [],
    },
    "honest_pnl": {
        "categorie": "meta",
        "beschrijving": "Toont gerealiseerd + open drawdown + ECHT netto + honesty ratio",
        "conflicts_with": [],
        "requires": [],
    },
    "extreme_oversold": {
        "categorie": "signaal",
        "beschrijving": "Alleen kopen bij extreme dips (breed onder mean)",
        "conflicts_with": [],
        "requires": [],
    },
}


class StrategySynthesizeBody(BaseModel):
    display_name: Optional[str] = None
    properties: List[str] = []
    author: Optional[str] = "spark"
    notes: Optional[str] = None


@router.get("/strategy/properties")
async def list_strategy_properties():
    """Property catalog — alle bouwstenen met categorie + beschrijving + conflicts."""
    return {"success": True, "properties": _PROPERTY_CATALOG}


@router.post("/strategy/synthesize")
async def synthesize_strategy(body: StrategySynthesizeBody):
    """Combineer properties tot een nieuwe strategie-blueprint + backtest-plan.

    Valideert conflicts en genereert:
      - strategy_id (kebab_case van display_name)
      - beschrijving (autogenereerd uit properties)
      - spark_alignment (waarom/regels/data/hypothese/zekerheid — placeholder)
      - hypothese_lineage stub (wachtend op backtest)
      - backtest_plan met parameters die getest moeten worden

    Persistent: schrijft naar `spark_trader.json.strategieën[strategy_id]` als draft.
    Backtest zelf wordt niet automatisch gedraaid (dat is een aparte P2-taak).
    """
    props = [p.strip() for p in (body.properties or []) if p.strip()]
    if not props:
        return {"success": False, "error": "properties[] mag niet leeg zijn"}

    # Validate: onbekende properties
    unknown = [p for p in props if p not in _PROPERTY_CATALOG]
    if unknown:
        return {"success": False, "error": f"onbekende properties: {unknown}", "beschikbaar": list(_PROPERTY_CATALOG.keys())}

    # Validate: conflicts
    conflicts_found = []
    for p in props:
        for c in _PROPERTY_CATALOG[p].get("conflicts_with", []):
            if c in props:
                conflicts_found.append((p, c))
    if conflicts_found:
        return {"success": False, "error": "conflicterende properties", "conflicts": conflicts_found}

    # Genereer strategy_id
    disp = body.display_name or " + ".join(props[:3])
    strategy_id = disp.lower().replace(" ", "_").replace("+", "_plus_").replace("-", "_")
    strategy_id = re.sub(r"[^a-z0-9_]", "", strategy_id)[:60]

    # Genereer beschrijving
    signal_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "signaal"]
    conf_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "confirmatie"]
    prot_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "bescherming"]
    exit_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "exit"]

    beschrijving_parts = []
    if signal_props: beschrijving_parts.append(f"Signaal: {' + '.join(signal_props)}")
    if conf_props: beschrijving_parts.append(f"Confirmatie: {' + '.join(conf_props)}")
    if prot_props: beschrijving_parts.append(f"Bescherming: {' + '.join(prot_props)}")
    if exit_props: beschrijving_parts.append(f"Exit: {' + '.join(exit_props)}")
    beschrijving = ". ".join(beschrijving_parts) + "."

    # Genereer regels lijst
    regels = [_PROPERTY_CATALOG[p]["beschrijving"] for p in props]

    # Backtest plan
    backtest_plan = {
        "test_periode_dagen": 360,
        "vergelijking_met": ["mean_reversion_bollinger (baseline)", "gap_momentum_50 (actieve strategie)"],
        "success_criteria": {
            "echt_netto_pnl_beter_dan_baseline": True,
            "random_seed_check": True,
            "bear_market_pnl_positief": True,
            "honest_pnl_beschikbaar": "loss_cut_48h_3pct" in props,
        },
        "markten": ["BCH-EUR", "BTC-EUR", "ETH-EUR", "SOL-EUR", "ATOM-EUR"],
        "trade_bedrag_eur": 10,
        "bitvavo_fee_pct": 0.25,
    }

    strategy_obj = {
        "display_name": disp,
        "beschrijving": beschrijving,
        "actief": False,
        "status": "draft_synthesized",
        "author": body.author or "spark",
        "synthesized_at": datetime.now(timezone.utc).isoformat(),
        "notes": body.notes or "",
        "properties": props,
        "confidence": {
            "score": 0,
            "berekening": "geen backtest data — draft",
            "gebaseerd_op": {"backtest_dagen": 0, "live_resultaten": "geen"},
            "toelichting": "Nieuwe synthese — backtest nodig voor score",
        },
        "hypothese_lineage": {
            "hypothese": f"De combinatie {' + '.join(props)} presteert beter dan de individuele componenten",
            "backtest_run": "TODO",
            "resultaat": "TODO",
            "conclusie": "TODO",
        },
        "spark_alignment": {
            "waarom": f"Synthese door {body.author or 'spark'} — combineert {len(props)} bouwstenen uit property catalog",
            "regels": regels,
            "data_bronnen": ["property_catalog v1", "voorgaande backtest-runs v2..v5"],
            "onderliggende_hypothese": f"Property-combinatie levert emergent gedrag: {beschrijving}",
            "zekerheid": "0% — draft zonder backtest",
        },
        "backtest_plan": backtest_plan,
    }

    # Persist naar blueprint als draft
    try:
        bp_path = Path(__file__).parent / "blueprints" / "spark_trader.json"
        bp_data = json.loads(bp_path.read_text(encoding="utf-8"))
        strategies = bp_data.setdefault("strategieën", {})
        if strategy_id in strategies and not strategies[strategy_id].get("status", "").startswith("draft"):
            return {"success": False, "error": f"strategy_id '{strategy_id}' bestaat al als niet-draft — kies andere naam"}
        strategies[strategy_id] = strategy_obj
        bp_path.write_text(json.dumps(bp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        # clear cache
        try:
            from modules.core.blueprint import clear_blueprint_cache
            clear_blueprint_cache()
        except Exception:
            pass
    except Exception as e:
        return {"success": False, "error": f"blueprint schrijven mislukt: {e}", "draft": strategy_obj}

    # v9_adaptive_lab_001 — Auto-compare met actieve strategie voor directe feedback
    compared_to_active = None
    try:
        actieve = bp_data.get("actieve_strategie")
        if actieve and actieve != strategy_id:
            compared_to_active = await compare_strategies(a=strategy_id, b=actieve)
    except Exception as _e:
        pass

    return {
        "success": True,
        "message": f"Draft-strategie '{strategy_id}' opgeslagen. Backtest is nodig voor confidence-score.",
        "strategy_id": strategy_id,
        "strategy": strategy_obj,
        "compared_to_active": compared_to_active,
        "spark_feedback": _build_spark_synthesize_feedback(strategy_id, compared_to_active),
    }


def _build_spark_synthesize_feedback(new_id: str, comp: Optional[Dict]) -> str:
    """Genereer Spark's inhoudelijke feedback over een net gesynthetiseerde strategie."""
    if not comp or not comp.get("success"):
        return f"Je nieuwe draft '{new_id}' is opgeslagen. Backtest deze om confidence te bepalen."
    scores = comp.get("score", {})
    winner = comp.get("overall_winner")
    active_name = comp.get("strategies", {}).get("b", {}).get("display_name", "actieve strategie")
    new_name = comp.get("strategies", {}).get("a", {}).get("display_name", new_id)
    a_score = scores.get(new_id, 0)
    if winner == new_id:
        pref = f"🚀 Je nieuwe draft **{new_name}** scoort **{a_score}/5** secties beter dan **{active_name}**"
    elif winner == "tie":
        pref = f"⚖️ **{new_name}** eindigt gelijk met **{active_name}** ({a_score}/5)"
    else:
        pref = f"🤔 **{new_name}** scoort {a_score}/5 secties beter dan **{active_name}** — draft heeft nog werk"
    # Section highlights
    highlights = []
    for name, sec in (comp.get("sections", {}) or {}).items():
        if isinstance(sec, dict) and sec.get("winner") == new_id:
            label = {
                "confidence": "hogere confidence",
                "properties": "meer beschermings-eigenschappen",
                "bear_market_pnl": "beter in bear-markten",
                "honesty": "eerlijker (honesty ratio)",
                "maturity": "afgeronde hypothese",
            }.get(name, name)
            highlights.append(label)
    if highlights:
        pref += f". Sterk op: {', '.join(highlights)}."
    if a_score < 3:
        pref += f" Advies: voeg loss_cut_48h_3pct + event_pause_5pct_24h toe voor honesty."
    else:
        pref += f" Klaar voor backtest — draai backtest_v2.py met deze properties om confidence te valideren."
    return pref



# ============================================================
# v8_strategy_compare_001 — Confidence battle: side-by-side twee strategieën
# ============================================================

@router.get("/strategy/compare")
async def compare_strategies(a: str, b: str):
    """Vergelijk twee strategieën op alle relevante velden en bepaal winnaar per sectie."""
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    sa = strategieën.get(a)
    sb = strategieën.get(b)
    if not sa:
        return {"success": False, "error": f"strategie '{a}' niet gevonden"}
    if not sb:
        return {"success": False, "error": f"strategie '{b}' niet gevonden"}

    def _pick(obj, path, default=None):
        cur = obj
        for k in path.split("."):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k, default)
            if cur is None:
                return default
        return cur

    conf_a = int(_pick(sa, "confidence.score", 0) or 0)
    conf_b = int(_pick(sb, "confidence.score", 0) or 0)
    conf_winner = a if conf_a > conf_b else b if conf_b > conf_a else "tie"

    props_a = set(sa.get("properties", []) or [])
    props_b = set(sb.get("properties", []) or [])
    prot_props = {"loss_cut_48h_3pct", "event_pause_5pct_24h", "honest_pnl", "fee_aware_sell"}
    prot_a = len(props_a & prot_props)
    prot_b = len(props_b & prot_props)
    prot_winner = a if prot_a > prot_b else b if prot_b > prot_a else "tie"

    based_a = _pick(sa, "confidence.gebaseerd_op", {}) or {}
    based_b = _pick(sb, "confidence.gebaseerd_op", {}) or {}
    bear_a = float(based_a.get("bear_market_pnl", 0) or 0)
    bear_b = float(based_b.get("bear_market_pnl", 0) or 0)
    bear_winner = a if bear_a > bear_b else b if bear_b > bear_a else "tie"

    honesty_a = based_a.get("honesty_ratio")
    honesty_b = based_b.get("honesty_ratio")

    def _honesty_score(h):
        if h is None:
            return -999
        return -abs((h or 0) - 1.0) if (h or 0) > 0 else -1000 + (h or 0)

    honesty_winner = (
        a if _honesty_score(honesty_a) > _honesty_score(honesty_b)
        else b if _honesty_score(honesty_b) > _honesty_score(honesty_a)
        else "tie"
    )

    conc_a = bool(_pick(sa, "hypothese_lineage.conclusie") and _pick(sa, "hypothese_lineage.conclusie") != "TODO")
    conc_b = bool(_pick(sb, "hypothese_lineage.conclusie") and _pick(sb, "hypothese_lineage.conclusie") != "TODO")
    maturity_winner = a if conc_a and not conc_b else b if conc_b and not conc_a else "tie"

    winners = [conf_winner, prot_winner, bear_winner, honesty_winner, maturity_winner]
    scores = {a: winners.count(a), b: winners.count(b), "tie": winners.count("tie")}
    if scores[a] > scores[b]:
        overall = a
    elif scores[b] > scores[a]:
        overall = b
    else:
        overall = "tie"

    return {
        "success": True,
        "strategies": {
            "a": {"id": a, "display_name": sa.get("display_name", a), "actief": bool(sa.get("actief"))},
            "b": {"id": b, "display_name": sb.get("display_name", b), "actief": bool(sb.get("actief"))},
        },
        "sections": {
            "confidence": {
                "a_score": conf_a, "b_score": conf_b, "winner": conf_winner,
                "narrative": _narrate_confidence(a, b, conf_a, conf_b, sa, sb),
            },
            "properties": {
                "overlap": sorted(props_a & props_b),
                "unique_a": sorted(props_a - props_b),
                "unique_b": sorted(props_b - props_a),
                "protection_count_a": prot_a,
                "protection_count_b": prot_b,
                "winner": prot_winner,
                "toelichting": "Winnaar = meeste beschermings-eigenschappen (loss_cut, event_pause, honest_pnl, fee_aware_sell)",
                "narrative": _narrate_properties(a, b, props_a, props_b, prot_a, prot_b, sa, sb),
            },
            "bear_market_pnl": {
                "a_eur": bear_a, "b_eur": bear_b, "winner": bear_winner,
                "narrative": _narrate_bear(a, b, bear_a, bear_b, sa, sb),
            },
            "honesty": {
                "a_ratio": honesty_a, "b_ratio": honesty_b, "winner": honesty_winner,
                "toelichting": "Ratio dichter bij 1.0 = eerlijker. Negatief = verstopte verliezen.",
                "narrative": _narrate_honesty(a, b, honesty_a, honesty_b, sa, sb),
            },
            "spark_zekerheid": {
                "a": _pick(sa, "spark_alignment.zekerheid", ""),
                "b": _pick(sb, "spark_alignment.zekerheid", ""),
            },
            "maturity": {
                "a_has_conclusion": conc_a, "b_has_conclusion": conc_b, "winner": maturity_winner,
                "toelichting": "Winnaar = heeft afgeronde hypothese_lineage.conclusie (geen TODO)",
                "narrative": _narrate_maturity(a, b, conc_a, conc_b, sa, sb),
            },
        },
        "score": scores,
        "overall_winner": overall,
        "advies": (
            f"'{sa.get('display_name', a) if overall == a else sb.get('display_name', b)}' scoort beter op {scores.get(overall, 0)}/5 secties."
            if overall != "tie"
            else "Gelijkspel — beide strategieën scoren identiek. Kies op basis van filosofie."
        ),
        "spark_advies": _narrate_overall(a, b, overall, scores, sa, sb),
    }


# ============================================================
# v9_adaptive_lab_001 — Narrative helpers voor Spark's inhoudelijke analyse
# ============================================================

def _narrate_confidence(a, b, ca, cb, sa, sb):
    if ca == cb:
        return f"Beide strategieën scoren identiek ({ca}%). Confidence alleen zegt niet welke beter presteert live."
    winner_name = sa.get("display_name", a) if ca > cb else sb.get("display_name", b)
    diff = abs(ca - cb)
    interp = "significant" if diff >= 20 else "beperkt" if diff >= 10 else "marginaal"
    return f"**{winner_name}** wint met {ca if ca > cb else cb}% vs {min(ca, cb)}%. Verschil van {diff}p is {interp}."


def _narrate_properties(a, b, props_a, props_b, prot_a, prot_b, sa, sb):
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if prot_a == prot_b:
        return f"Beide hebben {prot_a} beschermings-eigenschappen. Focus op verschillen in signaal-eigenschappen."
    winner_name = a_name if prot_a > prot_b else b_name
    unique_pos = sorted(props_a - props_b) if prot_a > prot_b else sorted(props_b - props_a)
    return (
        f"**{winner_name}** heeft {max(prot_a, prot_b)} beschermings-eigenschappen vs {min(prot_a, prot_b)}. "
        f"Verschilmakers: {', '.join(unique_pos[:4]) if unique_pos else 'geen unieke'}."
    )


def _narrate_bear(a, b, bear_a, bear_b, sa, sb):
    if bear_a == 0 and bear_b == 0:
        return "Geen bear-market data voor beide — draai backtest v3 voor validatie."
    winner_name = sa.get("display_name", a) if bear_a > bear_b else sb.get("display_name", b)
    ratio = round(max(bear_a, bear_b) / max(abs(min(bear_a, bear_b)), 0.001), 1) if min(bear_a, bear_b) != 0 else "∞"
    return f"**{winner_name}** presteert €{max(bear_a, bear_b):.2f} in bear-markten ({ratio}× beter). Advies: gebruik deze bij dalende trend."


def _narrate_honesty(a, b, ha, hb, sa, sb):
    if ha is None and hb is None:
        return "Geen honesty-data voor beide (nog geen open posities in backtest)."
    if ha is None or hb is None:
        available = a if ha is not None else b
        val = ha if ha is not None else hb
        return f"Alleen {sa.get('display_name', a) if available == a else sb.get('display_name', b)} heeft honesty data ({val})."
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if ha < 0 or hb < 0:
        loser = a_name if ha < hb else b_name
        return f"⚠️ **{loser}** heeft negatieve honesty ratio — verstopte verliezen. Voeg loss_cut toe."
    dist_a = abs(ha - 1.0)
    dist_b = abs(hb - 1.0)
    winner_name = a_name if dist_a < dist_b else b_name
    return f"**{winner_name}** scoort eerlijker (ratio {ha if dist_a < dist_b else hb} — dichter bij 1.0 = geen verstopte verliezen)."


def _narrate_maturity(a, b, ca, cb, sa, sb):
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if ca and cb:
        return "Beide strategieën hebben afgeronde hypothese_lineage — mature."
    if not ca and not cb:
        return "Beide zijn drafts (geen conclusie). Draai backtest voor validatie."
    mature = a_name if ca else b_name
    draft = b_name if ca else a_name
    return f"**{mature}** is mature (backtest-conclusie aanwezig). **{draft}** is nog draft."


def _narrate_overall(a, b, overall, scores, sa, sb):
    if overall == "tie":
        return "Gelijkspel — kies op basis van filosofie: transparantie (honesty), snelheid (minder cooldowns) of exploratie (nieuwere hypotheses)."
    winner_name = sa.get("display_name", a) if overall == a else sb.get("display_name", b)
    loser_name = sb.get("display_name", b) if overall == a else sa.get("display_name", a)
    s = scores.get(overall, 0)
    if s >= 4:
        return f"🏆 **{winner_name}** wint duidelijk ({s}/5). Aanbevolen om deze actief te zetten via `/api/trade/engine/switch` of blueprint.active_strategy update."
    elif s == 3:
        return f"**{winner_name}** wint knap ({s}/5). {loser_name} blijft een goede backup — hou beide beschikbaar voor A/B."
    return f"**{winner_name}** wint nipt ({s}/5). Verschil is klein — draai nog een backtest-ronde voor zekerheid."


# ============================================================
# v8_engine_switch_001 — A/B decision-engine switch via blueprint config
# ============================================================

@router.get("/engine/status")
async def get_engine_status():
    """Toon actieve decision-engine + welke opties er zijn."""
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        active = bp.get("active_decision_engine", "v1")
    except Exception as e:
        return {"success": False, "error": str(e)}

    engines_available = {
        "v1": {
            "module": "strategy_decision",
            "beschrijving": "Bollinger 2σ + gap-body 50% + 48u loss-cut + event-pauze (huidige productie)",
            "status": "productie",
            "backtest_bewezen": True,
        },
        "v2": {
            "module": "strategy_decision_v2",
            "beschrijving": "Pure trend-following stub — koopt bij 3 stijgende candles, verkoopt bij 2 dalende. Experimenteel.",
            "status": "draft",
            "backtest_bewezen": False,
        },
    }

    return {
        "success": True,
        "active_engine": active,
        "engines_available": engines_available,
        "current_module": engines_available.get(active, {}).get("module"),
    }


class EngineSwitchBody(BaseModel):
    engine: str


@router.post("/engine/switch")
async def switch_engine(body: EngineSwitchBody):
    """Wissel actieve decision-engine via blueprint. MonitorService leest bij volgende cycle."""
    if body.engine not in ("v1", "v2"):
        return {"success": False, "error": "engine moet 'v1' of 'v2' zijn"}

    bp_path = Path(__file__).parent / "blueprints" / "spark_trader.json"
    try:
        bp_data = json.loads(bp_path.read_text(encoding="utf-8"))
        bp_data["active_decision_engine"] = body.engine
        # Atomair write via tmp+rename (fix code-review item iter46)
        tmp = bp_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(bp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(bp_path)
        try:
            from modules.core.blueprint import clear_blueprint_cache
            clear_blueprint_cache()
        except Exception:
            pass
    except Exception as e:
        return {"success": False, "error": f"blueprint schrijven mislukt: {e}"}

    return {
        "success": True,
        "message": f"Engine geswitcht naar {body.engine}.",
        "active_engine": body.engine,
        "note": "MonitorService leest engine bij volgende cycle (max 5 min wachttijd).",
    }


# ============================================================
# v9_adaptive_lab_002 — Strategy Genome view (DNA-matrix per strategie)
# ============================================================

@router.get("/strategy/genome")
async def get_strategy_genome():
    """Toon alle strategieën als 'genoom' — property-matrix waaruit blijkt welke
    strategie welk gen heeft. Fundament voor Adaptive Strategy Lab v9.

    Return:
      - genes: alle bekende properties uit blueprint + property catalog
      - matrix: {strategy_id: {display_name, actief, confidence, gene_count, genes:{gen:bool}}}
      - inheritance: draft-strategieën met candidate_parents (via property-overlap)
      - stats: gene usage stats, categorieën
    """
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    # 1. Verzamel alle unieke genen
    all_genes = set()
    for sid, s in strategieën.items():
        for p in (s.get("properties", []) or []):
            all_genes.add(p)
    for gen in _PROPERTY_CATALOG.keys():
        all_genes.add(gen)
    all_genes = sorted(all_genes)

    # 2. Matrix bouwen
    matrix = {}
    for sid, s in strategieën.items():
        props = set(s.get("properties", []) or [])
        raw_status = s.get("status", "")
        status = raw_status if raw_status.startswith("draft") else "productie"
        matrix[sid] = {
            "display_name": s.get("display_name", sid),
            "actief": bool(s.get("actief")),
            "status": status,
            "confidence": int((s.get("confidence") or {}).get("score", 0)),
            "gene_count": len(props),
            "genes": {gen: (gen in props) for gen in all_genes},
        }

    # 3. Inheritance tracking
    inheritance = {}
    for sid, s in strategieën.items():
        vorige = s.get("vorige_naam")
        if vorige and vorige != sid:
            inheritance[sid] = {
                "vorige_naam": vorige,
                "is_migration": True,
                "beschrijving": "Hernoemd van legacy-code naar semantic name",
            }
        if s.get("status", "").startswith("draft"):
            new_props = set(s.get("properties", []) or [])
            parents = []
            for other_id, other_s in strategieën.items():
                if other_id == sid or other_s.get("status", "").startswith("draft"):
                    continue
                other_props = set(other_s.get("properties", []) or [])
                if other_props and len(new_props & other_props) >= max(2, len(other_props) // 2):
                    overlap = len(new_props & other_props)
                    parents.append({
                        "parent_id": other_id,
                        "parent_name": other_s.get("display_name", other_id),
                        "shared_genes": overlap,
                        "unique_new_genes": sorted(new_props - other_props),
                    })
            if parents:
                inheritance[sid] = {
                    "is_synthesis": True,
                    "candidate_parents": sorted(parents, key=lambda x: -x["shared_genes"])[:3],
                }

    # 4. Stats
    gene_usage = {g: sum(1 for m in matrix.values() if m["genes"].get(g)) for g in all_genes}
    most_common = sorted(gene_usage.items(), key=lambda x: -x[1])[:5]
    unused_genes = [g for g, cnt in gene_usage.items() if cnt == 0]

    genes_by_category = {}
    for gen in all_genes:
        cat = (_PROPERTY_CATALOG.get(gen) or {}).get("categorie", "onbekend")
        genes_by_category.setdefault(cat, []).append(gen)

    return {
        "success": True,
        "total_genes": len(all_genes),
        "total_strategies": len(strategieën),
        "genes_by_category": genes_by_category,
        "matrix": matrix,
        "inheritance": inheritance,
        "stats": {
            "most_common_genes": [{"gene": g, "count": c} for g, c in most_common],
            "unused_genes": unused_genes,
            "protection_gene_count": len([g for g in all_genes if (_PROPERTY_CATALOG.get(g) or {}).get("categorie") == "bescherming"]),
            "signal_gene_count": len([g for g in all_genes if (_PROPERTY_CATALOG.get(g) or {}).get("categorie") == "signaal"]),
        },
        "_note": "Fundament voor Adaptive Strategy Lab v9. Genes = properties. Inheritance detecteert synthesized-drafts en migraties. Gebruik matrix voor UI DNA-heatmap.",
    }

