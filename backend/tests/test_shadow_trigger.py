"""
Smoke-test voor v6_shadow_cascade_002 — 3-slot shadow + bodemdetectie + recycle.

Run: cd /app/backend && python3 -m tests.test_shadow_trigger
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.trade import shadow_pots as shadow

TEST_USER_A = "test-shadow-user-A"
TEST_USER_B = "test-shadow-user-B"


def cleanup():
    data = shadow._load()
    data["shadows"] = [s for s in data["shadows"]
                       if s.get("owner_user_id") not in (TEST_USER_A, TEST_USER_B)]
    shadow._save(data)


def run():
    print("=== Shadow Cascade (3-slot) + Bodemdetectie Smoke Test ===")
    cleanup()

    # 1. 3 slots aanmaken voor user-A pot-001
    for slot in [1, 2, 3]:
        r = shadow.create_shadow_for_pot("pot-001", TEST_USER_A, "BCH-EUR", capital=10.0, slot=slot)
        assert r["created"], f"Should create slot {slot}: {r}"
    cap = shadow.shadow_capacity("pot-001", TEST_USER_A)
    assert cap["have"] == 3 and cap["idle"] == 3, f"Expected 3/3 idle, got {cap}"
    print(f"  [OK] 3 idle slots aangemaakt: {cap['slots']}")

    # 2. 4e create faalt netjes
    r4 = shadow.create_shadow_for_pot("pot-001", TEST_USER_A, "BCH-EUR")
    assert not r4["created"] and "alle 3" in r4.get("reason", ""), f"Should reject 4e: {r4}"
    print(f"  [OK] 4e shadow geweigerd: {r4['reason']}")

    # 3. Per-user scope: user-B's pot-001 staat naast user-A
    for slot in [1, 2, 3]:
        rb = shadow.create_shadow_for_pot("pot-001", TEST_USER_B, "BTC-EUR", slot=slot)
        assert rb["created"]
    cap_b = shadow.shadow_capacity("pot-001", TEST_USER_B)
    assert cap_b["have"] == 3
    print(f"  [OK] User-B krijgt eigen 3 slots (scope-isolatie OK)")

    # 4. Bodemdetectie: STABIEL na drop
    # Entry €100, huidige prijs €97 (-3%), 5 vlakke candles in range €96.50-€97.20 (≈0.72%)
    candles_stable = [
        {"high": 97.20, "low": 96.80, "close": 97.00},
        {"high": 97.10, "low": 96.70, "close": 96.95},
        {"high": 97.00, "low": 96.60, "close": 96.85},
        {"high": 97.10, "low": 96.75, "close": 96.90},
        {"high": 97.20, "low": 96.80, "close": 97.00},
    ]
    stab = shadow.is_stabilizing_after_drop(candles_stable, entry_price=100.0, current_price=97.0)
    assert stab["stable"], f"Stable case should pass: {stab}"
    print(f"  [OK] Stabilisatie GEDETECTEERD: {stab['reason']}")

    # 5. Bodemdetectie: NOG IN FREEFALL (laatste close lager dan vorige)
    candles_falling = [
        {"high": 99.0, "low": 98.0, "close": 98.5},
        {"high": 98.5, "low": 97.5, "close": 97.8},
        {"high": 97.8, "low": 96.8, "close": 97.0},
        {"high": 97.0, "low": 96.0, "close": 96.2},
        {"high": 96.2, "low": 95.0, "close": 95.1},  # nieuwe low
    ]
    stab2 = shadow.is_stabilizing_after_drop(candles_falling, entry_price=100.0, current_price=95.1)
    assert not stab2["stable"], f"Falling case should NOT trigger: {stab2}"
    print(f"  [OK] Freefall NIET getriggerd: {stab2['reason']}")

    # 6. Bodemdetectie: drop te klein
    candles_small = [{"high": 99.8, "low": 99.5, "close": 99.7}] * 5
    stab3 = shadow.is_stabilizing_after_drop(candles_small, entry_price=100.0, current_price=99.7)
    assert not stab3["stable"], f"Small drop should NOT trigger: {stab3}"
    print(f"  [OK] Te kleine drop geweigerd: {stab3['reason']}")

    # 7. Activate slot 1 (laagste eerst)
    act1 = shadow.activate_shadow("pot-001", entry_price=97.0, drop_pct=-0.03,
                                  owner_user_id=TEST_USER_A, trigger_reason="bodem €97 vlak")
    assert act1["success"] and act1["shadow"]["slot"] == 1
    print(f"  [OK] Activated slot 1: {act1['shadow']['shadow_id']}")

    # 8. Activate slot 2 (volgende drop)
    act2 = shadow.activate_shadow("pot-001", entry_price=94.0, drop_pct=-0.06,
                                  owner_user_id=TEST_USER_A, trigger_reason="bodem €94")
    assert act2["success"] and act2["shadow"]["slot"] == 2
    print(f"  [OK] Activated slot 2: {act2['shadow']['shadow_id']}")

    # 9. Activate slot 3 (3e drop)
    act3 = shadow.activate_shadow("pot-001", entry_price=91.0, drop_pct=-0.09,
                                  owner_user_id=TEST_USER_A, trigger_reason="bodem €91")
    assert act3["success"] and act3["shadow"]["slot"] == 3
    print(f"  [OK] Activated slot 3: {act3['shadow']['shadow_id']}")

    # 10. 4e activate faalt (alle slots actief)
    act4 = shadow.activate_shadow("pot-001", entry_price=88.0, drop_pct=-0.12, owner_user_id=TEST_USER_A)
    assert not act4["success"]
    print(f"  [OK] 4e activate correct geweigerd: {act4['error']}")

    # 11a. v6_shadow_safety_001 — recycle BLOKKEERT als shadows nog active zijn
    rec_blocked = shadow.recycle_pot_as_shadow_zero("pot-001", TEST_USER_A, current_price=88.0)
    assert not rec_blocked["success"] and "active" in rec_blocked.get("error", "").lower()
    print(f"  [OK] Recycle geblokkeerd (3 active shadows): {rec_blocked['error']}")

    # 11b. Sluit alle 3 actieve shadows eerst → daarna mag recycle wel
    for sh in shadow.get_active_shadows("pot-001", owner_user_id=TEST_USER_A):
        shadow.close_shadow(sh["shadow_id"], exit_price=95.0, profit=0.5)

    # 11c. Nu Recycle: 3 closed worden archived_cycle_1, nieuwe 3 idle slots in cycle 2
    rec = shadow.recycle_pot_as_shadow_zero("pot-001", TEST_USER_A, current_price=88.0)
    assert rec["success"] and rec["new_cycle"] == 2 and len(rec["new_shadow_ids"]) == 3
    cap_after = shadow.shadow_capacity("pot-001", TEST_USER_A)
    assert cap_after["idle"] == 3 and cap_after["active"] == 0
    print(f"  [OK] Recycled cyclus 1→2 na SELL van alle slots: {rec['new_shadow_ids']}")

    # 12. Close shadow (simuleer recovery)
    # We hebben net gerecycled, dus laat slot 1 nieuwe cyclus pakken
    act5 = shadow.activate_shadow("pot-001", entry_price=87.0, drop_pct=-0.13, owner_user_id=TEST_USER_A)
    assert act5["success"]
    cls = shadow.close_shadow(act5["shadow"]["shadow_id"], exit_price=95.0, profit=0.92)
    assert cls["success"] and cls["shadow"]["status"] == "closed"
    print(f"  [OK] Shadow closed @ €95 profit €0.92")

    cleanup()
    print("\n✅ Alle 13 tests passed. 3-slot cascade + bodemdetectie + safe recycle werken.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
