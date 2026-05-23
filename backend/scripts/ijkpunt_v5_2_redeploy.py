"""
v5_ijkpunt_redeploy_001 — Pre-redeploy setup.

Aanleiding: Willem heeft alles verkocht op Bitvavo + €1.20 bijgestort.
Totaal baseline ~€102.80 verdeeld over 20 gelijke potjes (€5.14/pot).

User-IDs (LET OP geen verwarring):
- user-000 = Spark (10 potjes, monitor 1u, auto_trade=TRUE)
- user-001 = Willem / De Willem (10 potjes, monitor 15m, auto_trade=FALSE)
- bot-* zijn ACTEURS (Boekhouder, Harry, Madelief, Smith, Dood) — geen wallets

Markt: BCH-EUR
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("/app/backend/data")
TOTAAL_EUR = 102.80
N_POTJES_PER_USER = 10
CAPITAL_PER_POT = round(TOTAAL_EUR / 20, 2)  # €5.14
MARKET = "BCH-EUR"


def now():
    return datetime.now(timezone.utc).isoformat()


# 1. Potjes reset
pots_path = DATA / "financial" / "user_potjes.json"
pots = json.load(open(pots_path))
for uid in ("user-000", "user-001"):
    new_potjes = []
    for i in range(N_POTJES_PER_USER):
        new_potjes.append({
            "id": f"pot-{uid[-3:]}-{i+1:02d}",
            "user_id": uid,
            "market": MARKET,
            "capital": CAPITAL_PER_POT,
            "live_value": CAPITAL_PER_POT,
            "status": "open",
            "side": None,
            "entry_price": None,
            "current_price": None,
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "pnl_eur": 0,
            "fees_eur": 0,
            "created_at": now(),
        })
    pots["users"][uid] = {
        "potjes": new_potjes,
        "baseline_eur": CAPITAL_PER_POT * N_POTJES_PER_USER,
        "overflow_pool": 0.0,
    }
json.dump(pots, open(pots_path, "w"), indent=2)
print(f"✅ 20 potjes aangemaakt: 2× {N_POTJES_PER_USER} × €{CAPITAL_PER_POT} = €{CAPITAL_PER_POT*20:.2f}")

# 2. Trader baseline
baseline_path = DATA / "trade" / "capital_baseline.json"
baseline = json.load(open(baseline_path)) if baseline_path.exists() else {}
for uid in ("user-000", "user-001"):
    baseline[uid] = CAPITAL_PER_POT * N_POTJES_PER_USER
json.dump(baseline, open(baseline_path, "w"), indent=2)
print(f"✅ Trader baseline gezet voor beide users")

# 3. Deposit log (€1.20 bijstorting)
dep_path = DATA / "trade" / "deposits.json"
dep = json.load(open(dep_path)) if dep_path.exists() else {}
dep.setdefault("user-001", []).append({
    "id": f"dep-{uuid.uuid4().hex[:6]}",
    "timestamp": now(),
    "type": "deposit",
    "amount_eur": 1.20,
    "source": "Bitvavo SEPA bijstorting",
    "description": "Bijstorting €1.20 → 20 gelijke potjes pre-redeploy ijkpunt v5.2",
})
json.dump(dep, open(dep_path, "w"), indent=2)
print(f"✅ €1.20 deposit gelogd op user-001")

# 4. Bot registry: Spark auto_trade ON 1h, Willem manual 15m
reg_path = DATA / "trade" / "bots_registry_state.json"
reg = json.load(open(reg_path))
reg["bots"] = []  # clean slate
# Spark — user-000, 1u, auto-trade
reg["bots"].append({
    "user_id": "user-000",
    "user_naam": "Spark",
    "market": MARKET,
    "markets": [MARKET],
    "candle_interval": "1h",
    "interval": 60,
    "auto_trade": True,
    "use_mock": True,
    "use_potjes": True,
    "running": True,
    "registered_at": now(),
})
# Willem — user-001, 15m, NO auto-trade
reg["bots"].append({
    "user_id": "user-001",
    "user_naam": "De Willem",
    "market": MARKET,
    "markets": [MARKET],
    "candle_interval": "15m",
    "interval": 60,
    "auto_trade": False,
    "use_mock": True,
    "use_potjes": True,
    "running": True,
    "registered_at": now(),
})
json.dump(reg, open(reg_path, "w"), indent=2)
print(f"✅ Bot registry: Spark 1h auto_trade=TRUE, Willem 15m auto_trade=FALSE")

# 5. Audit-log entry voor de setup
audit_path = DATA / "system" / "audit_log.json"
audit = json.load(open(audit_path)) if audit_path.exists() else {"entries": []}
audit["entries"].append({
    "ts": now(),
    "id": uuid.uuid4().hex[:12],
    "type": "ijkpunt_redeploy",
    "version": "v5.2",
    "totaal_eur": TOTAAL_EUR,
    "per_pot": CAPITAL_PER_POT,
    "n_potjes": 20,
    "spark_config": "user-000 · 1h · auto_trade=true · BCH-EUR",
    "willem_config": "user-001 · 15m · auto_trade=false · BCH-EUR",
    "note": "€1.20 bijgestort, alles in BCH op Bitvavo verkocht, ijkpunt v5.2 voor redeploy",
})
json.dump(audit, open(audit_path, "w"), indent=2)
print(f"✅ Audit-log entry geschreven")

print("\n" + "="*60)
print(f"IJkpunt v5.2 KLAAR voor redeploy:")
print(f"  Totaal:      €{TOTAAL_EUR:.2f}")
print(f"  Per potje:   €{CAPITAL_PER_POT:.2f}")
print(f"  Spark:       10 potjes · BCH-EUR · 1u · auto-trade AAN")
print(f"  Willem:      10 potjes · BCH-EUR · 15m · auto-trade UIT")
print(f"  ROAR balance: Spark 10 / Willem 10 (ongewijzigd)")
print(f"  Spark kasboek: €0 (begint te groeien bij elke buy via 21% BTW)")
print("="*60)
