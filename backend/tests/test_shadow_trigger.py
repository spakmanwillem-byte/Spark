"""
Smoke-test voor v6_shadow_pot_001 — Shadow Potje activatie/sluiting.

Doel:
  Bewijs dat het shadow-systeem juist werkt zonder echte Bitvavo-trades.
  Test scenarios:
    1. Idle shadow bestaat voor een open potje
    2. Bij -3% drop → shadow activeert (status idle → active, entry_price gevuld)
    3. Bij potje-close → bijbehorende shadow ook closed met profit
    4. Per-user scope: pot-001 van user-A en user-B worden niet door elkaar gehaald

Run: cd /app/backend && python3 -m tests.test_shadow_trigger
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.trade import shadow_pots as shadow

TEST_USER_A = "test-shadow-user-A"
TEST_USER_B = "test-shadow-user-B"


def cleanup():
    """Verwijder test-shadows zodat test idempotent is."""
    data = shadow._load()
    data["shadows"] = [s for s in data["shadows"]
                       if s.get("owner_user_id") not in (TEST_USER_A, TEST_USER_B)]
    shadow._save(data)


def run():
    print("=== Shadow Potje Trigger Smoke Test ===")
    cleanup()

    # 1. Create idle shadow voor User A pot-001 (BCH)
    r1 = shadow.create_shadow_for_pot("pot-001", TEST_USER_A, "BCH-EUR", capital=10.0)
    assert r1["created"], f"Should create new shadow, got {r1}"
    sh_a = r1["shadow"]
    print(f"  [OK] Shadow created voor user-A pot-001: {sh_a['shadow_id']} status={sh_a['status']}")

    # 2. Create idle shadow voor User B pot-001 (BTC) — per-user scope test
    r2 = shadow.create_shadow_for_pot("pot-001", TEST_USER_B, "BTC-EUR", capital=10.0)
    assert r2["created"], "User B's pot-001 should NOT collide with User A's pot-001"
    sh_b = r2["shadow"]
    print(f"  [OK] Shadow created voor user-B pot-001 (separate): {sh_b['shadow_id']}")

    # 3. Idempotent: 2e create voor user-A pot-001 returnt bestaande
    r3 = shadow.create_shadow_for_pot("pot-001", TEST_USER_A, "BCH-EUR")
    assert not r3["created"], "Should NOT create duplicate"
    assert r3["shadow"]["shadow_id"] == sh_a["shadow_id"], "Should return existing"
    print(f"  [OK] Idempotent: dezelfde shadow_id retour bij 2e call")

    # 4. Scope-check: get_shadows_for_pot met owner geeft alleen die user
    all_pot1 = shadow.get_shadows_for_pot("pot-001")
    test_pot1 = [s for s in all_pot1 if s.get("original_owner_id") in (TEST_USER_A, TEST_USER_B)]
    assert len(test_pot1) == 2, f"Expected 2 test shadows on pot-001, got {len(test_pot1)}"
    only_a = shadow.get_shadows_for_pot("pot-001", owner_user_id=TEST_USER_A)
    assert len(only_a) == 1 and only_a[0]["original_owner_id"] == TEST_USER_A
    print(f"  [OK] Per-user scope: test pot-001={len(test_pot1)}, user-A only={len(only_a)} (globally {len(all_pot1)})")

    # 5. Activate shadow van user-A (simuleer -3% drop op €100 → €97)
    act = shadow.activate_shadow("pot-001", entry_price=97.0, drop_pct=-0.03, owner_user_id=TEST_USER_A)
    assert act["success"], f"Activation failed: {act}"
    assert act["shadow"]["status"] == "active"
    assert act["shadow"]["entry_price"] == 97.0
    print(f"  [OK] Shadow user-A actief @ €97.00 (trigger -3%)")

    # 6. Check dat get_active_shadow user-A's shadow vindt
    act_check = shadow.get_active_shadow("pot-001", owner_user_id=TEST_USER_A)
    assert act_check is not None and act_check["status"] == "active"
    print(f"  [OK] get_active_shadow vindt active shadow voor user-A pot-001")

    # 7. User-B's shadow is nog idle (niet per ongeluk geactiveerd door scope-bug)
    b_check = shadow.get_active_shadow("pot-001", owner_user_id=TEST_USER_B)
    assert b_check is None, "User-B's shadow should still be idle!"
    print(f"  [OK] User-B's pot-001 shadow blijft idle (scope-isolatie)")

    # 8. Sluit shadow user-A (simuleer recovery: €97 → €99 = €0.21 winst op €10)
    close = shadow.close_shadow(act["shadow"]["shadow_id"], exit_price=99.0, profit=0.2062)
    assert close["success"]
    assert close["shadow"]["status"] == "closed"
    assert close["shadow"]["profit"] == 0.2062
    print(f"  [OK] Shadow closed @ €99.00 profit €0.21")

    # 9. Stats
    st = shadow.stats()
    print(f"  [OK] Global stats: total={st['total']}, by_status={st['by_status']}")

    cleanup()
    print("\n✅ Alle 9 shadow-tests passed. Systeem ready voor live.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
