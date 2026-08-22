"""Sync + Mint operations for Finance Hub (v10_finance_hub_ops_001).

Muterende operaties (schrijven data). Aparte module om readonly-hub schoon te houden.
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from modules.core.storage import load_json, save_json
from .agents import TokenAgent, PriceAgent, PotjesAgent

DATA = Path(__file__).parent.parent.parent / "data"


def sync_wallet_mirror(dry_run: bool = True) -> Dict[str, Any]:
    """Sync user_wallets.spark_tokens ← roar_balances.balances (authoritative).

    Fix voor de drift die we zagen: wallet toont 15, roar zegt 0.
    Regel: roar_balances is single source of truth.
    """
    roar_fp = DATA / "roar" / "roar_balances.json"
    uw_fp = DATA / "wallet" / "user_wallets.json"
    roar = load_json(roar_fp, default={"balances": {}}) or {}
    uw = load_json(uw_fp, default={"user_wallets": {}}) or {}
    balances = roar.get("balances", {}) or {}
    wallets = uw.get("user_wallets", {}) or {}

    fixes: List[Dict[str, Any]] = []
    for uid, w in wallets.items():
        current_mirror = int((w or {}).get("spark_tokens", 0) or 0)
        authoritative = int(balances.get(uid, 0) or 0)
        if current_mirror != authoritative:
            fixes.append({
                "user_id": uid,
                "was": current_mirror,
                "becomes": authoritative,
                "delta": authoritative - current_mirror,
            })
            if not dry_run:
                w["spark_tokens"] = authoritative
                w["_last_synced_at"] = datetime.now(timezone.utc).isoformat()
                w["_synced_by"] = "finance_hub_sync_all"

    if not dry_run and fixes:
        uw["_last_full_sync"] = datetime.now(timezone.utc).isoformat()
        save_json(uw_fp, uw)

    return {
        "success": True,
        "dry_run": dry_run,
        "fixes_needed": len(fixes),
        "fixes": fixes,
        "authoritative_source": "roar_balances.balances",
        "mirror_target": "user_wallets.spark_tokens",
    }


def mint_tokens(user_id: str, n_tokens: int, source: str = "manual",
                dry_run: bool = True) -> Dict[str, Any]:
    """Mint N tokens naar user's roar-balance + user_wallets mirror + potje-per-token.

    Hybride regel: 1 token = 1 pot (hybride regel).
    """
    if n_tokens <= 0:
        return {"success": False, "error": "n_tokens moet > 0"}

    # 1. Lees huidige staat
    roar_fp = DATA / "roar" / "roar_balances.json"
    uw_fp = DATA / "wallet" / "user_wallets.json"
    pot_fp = DATA / "financial" / "user_potjes.json"

    roar = load_json(roar_fp, default={"balances": {}, "treasury_pool": 999973, "total_supply": 1000000, "transactions": []}) or {}
    uw = load_json(uw_fp, default={"user_wallets": {}}) or {}
    pots = load_json(pot_fp, default={"users": {}}) or {}

    treasury = int(roar.get("treasury_pool", 0) or 0)
    if n_tokens > treasury:
        return {"success": False, "error": f"Treasury heeft maar {treasury} tokens over"}

    # 2. Huidige prijs voor pot.capital
    price_info = PriceAgent().compute_price()
    price = price_info["current_price_eur"]

    # 3. Bereken mutaties
    prev_roar_balance = int((roar.get("balances", {}) or {}).get(user_id, 0) or 0)
    prev_wallet_tokens = int(((uw.get("user_wallets", {}) or {}).get(user_id, {}) or {}).get("spark_tokens", 0) or 0)
    prev_potjes_count = len(((pots.get("users", {}) or {}).get(user_id, {}) or {}).get("potjes", []) or [])

    new_roar_balance = prev_roar_balance + n_tokens
    new_treasury = treasury - n_tokens

    # 4. Preview
    preview = {
        "n_tokens": n_tokens,
        "user_id": user_id,
        "source": source,
        "token_price_at_mint": price,
        "total_value_eur": round(n_tokens * price, 2),
        "before": {
            "roar_balance": prev_roar_balance,
            "wallet_mirror": prev_wallet_tokens,
            "potjes_count": prev_potjes_count,
            "treasury_pool": treasury,
        },
        "after": {
            "roar_balance": new_roar_balance,
            "wallet_mirror": new_roar_balance,
            "potjes_count": prev_potjes_count + n_tokens,
            "treasury_pool": new_treasury,
        },
    }

    if dry_run:
        return {"success": True, "dry_run": True, "preview": preview}

    # 5. Muteer roar_balances
    roar.setdefault("balances", {})[user_id] = new_roar_balance
    roar["treasury_pool"] = new_treasury
    roar.setdefault("transactions", []).append({
        "type": "mint",
        "user_id": user_id,
        "n_tokens": n_tokens,
        "price_per_token_eur": price,
        "total_eur": round(n_tokens * price, 2),
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_json(roar_fp, roar)

    # 6. Sync user_wallets mirror
    uw.setdefault("user_wallets", {}).setdefault(user_id, {})
    uw["user_wallets"][user_id]["spark_tokens"] = new_roar_balance
    uw["user_wallets"][user_id]["_last_mint_at"] = datetime.now(timezone.utc).isoformat()
    save_json(uw_fp, uw)

    # 7. Voeg N potjes toe (1 token = 1 pot)
    pots.setdefault("users", {}).setdefault(user_id, {
        "user_id": user_id, "market": "BCH-EUR",
        "overflow_pool": 0.0, "created_at": datetime.now(timezone.utc).isoformat(),
        "potjes": [], "tokens": []
    })
    user_pots = pots["users"][user_id]
    existing = user_pots.get("potjes", []) or []
    next_idx = max((p.get("index", 0) for p in existing), default=-1) + 1
    minted_ids = []
    for i in range(n_tokens):
        pid = f"pot-{next_idx + i + 1:03d}"
        existing.append({
            "id": pid,
            "index": next_idx + i,
            "nummer": next_idx + i + 1,
            "capital": price,          # HYBRIDE: pot.capital = token_price at mint
            "max_size": price * 5.0,   # 5x buffer per pot
            "pot_locked": False,
            "market": "EUR",
            "minted_at": datetime.now(timezone.utc).isoformat(),
            "minted_from": source,
            "position": {"is_open": False},
            "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
        })
        minted_ids.append(pid)
    user_pots["potjes"] = existing
    save_json(pot_fp, pots)

    # v10_mint_container_sync_001 — Voor niet-Spark users: sync via de bestaande
    # potjes-service zodat mint gedraagt zich identiek aan shop-buy/gift
    # (container-koppeling, round-robin market-toewijzing uit bots_registry).
    # user-000 (Spark) heeft eigen base-potjes-logic en wordt geskipt door de sync.
    if user_id != "user-000":
        try:
            from modules.trade.potjes import sync_potjes_to_tokens
            # We hebben net N potjes toegevoegd; sync verifieert count == new_balance
            sync_potjes_to_tokens(user_id, new_roar_balance)
        except Exception as _ex:
            print(f"[mint] container sync (non-blocking): {_ex}")

        # v13_auto_baseline_on_mint_001 — trigger auto_provision zodat mint-only
        # users (bijv. via boekhouding auto-mint scheduler) ook een bot-config
        # + baseline krijgen. Idempotent: als bot al configured is, alleen
        # baseline-hook draait. Voorkomt dat nieuwe users vast lopen op
        # "live_pnl = alles is winst".
        try:
            from modules.trade.monitor import auto_provision_bot_for_token_holder
            auto_provision_bot_for_token_holder(user_id, use_mock=False, auto_trade=True, autostart=False)
        except Exception as _ex:
            print(f"[mint] auto-provision (non-blocking): {_ex}")

    # v10_log_reserve_001 — Log-agent + Reserve-kluis
    try:
        from .agents.log_agent import LogAgent
        from .agents.reserve_kluis_agent import ReserveKluisAgent
        mint_total_eur = round(n_tokens * price, 4)
        # Reserve-kluis: 5% split (2/2/1)
        reserve_result = ReserveKluisAgent().reserve_from_mint(
            mint_total_eur=mint_total_eur, mint_event_id="pending", source=source)
        # Log event
        log_result = LogAgent().record(
            topic="mint", event_type="mint_tokens", actor=user_id,
            data={
                "n_tokens": n_tokens, "price_per_token_eur": price,
                "total_eur": mint_total_eur, "source": source,
                "minted_pot_ids": minted_ids,
                "reserve": reserve_result["reserved"],
            })
        preview["log_event_id"] = log_result["event_id"]
        preview["reserve"] = reserve_result["reserved"]
    except Exception as e:
        print(f"[mint] log/reserve failed (non-blocking): {e}")

    return {
        "success": True,
        "dry_run": False,
        "preview": preview,
        "minted_pot_ids": minted_ids,
        "message": f"✅ {n_tokens} token(s) gemint voor {user_id} @ €{price} — {len(minted_ids)} nieuwe potjes",
    }


def check_auto_mint_hook(user_id: str) -> Dict[str, Any]:
    """Hook die aangeroepen wordt na trade close.

    Roept staking_growth.run_auto_mint_only aan (bestaande motor), maar
    UPDATE de gemake potjes: capital = current_token_price (hybride).
    """
    try:
        from modules.trade import staking_growth
        result = staking_growth.run_auto_mint_only()
        # Als er iets gemint is, revalue de nieuwe potjes met dynamische prijs
        if result.get("success") and result.get("n_minted", 0) > 0:
            price_info = PriceAgent().compute_price()
            price = price_info["current_price_eur"]
            pot_fp = DATA / "financial" / "user_potjes.json"
            pots = load_json(pot_fp, default={"users": {}}) or {}
            spark_pots = ((pots.get("users") or {}).get("user-000") or {}).get("potjes", []) or []
            revalued = 0
            for pid in result.get("minted_pots", []):
                for p in spark_pots:
                    if p.get("id") == pid:
                        p["capital"] = price  # hybride revalue
                        p["max_size"] = price * 5.0
                        p["_hybrid_revalued_at"] = datetime.now(timezone.utc).isoformat()
                        revalued += 1
            if revalued:
                save_json(pot_fp, pots)
            result["hybrid_revalued"] = revalued
            result["token_price_at_mint"] = price
        return result
    except Exception as e:
        return {"success": False, "error": f"auto_mint_hook failed: {e}"}
