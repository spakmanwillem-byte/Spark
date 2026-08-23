"""v13c_rest_bonus_cap_001 — regressie voor ATOM-drift fix.

Bug: monitor SELL-pad greep alle overtollige coins op Bitvavo mee als
'rest_bonus', ook legacy/andere-user holdings. Bij ATOM: bot probeerde
61.4 ATOM te verkopen terwijl pot 7.6 bezat.

Fix: rest max 10% van pot-eigen coins (echte dust). Skip bij proxied users.

Run: cd /app && pytest backend/tests/test_rest_bonus_cap_v13c.py -v
"""
from __future__ import annotations
import pytest


def _simulate_rest_bonus(
    actual_coins: float,
    expected_coins: float,
    price: float,
    is_proxied: bool = False,
) -> float:
    """Extract van monitor.py's rest_bonus-logica voor unit-testing."""
    rest_coins = actual_coins - expected_coins
    max_dust_coins = expected_coins * 0.10
    if rest_coins > max_dust_coins:
        rest_coins = 0.0
    if is_proxied and rest_coins > 0:
        rest_coins = 0.0
    if rest_coins > 0 and (rest_coins * price) > 0.02:
        return rest_coins * price
    return 0.0


def test_atom_drift_scenario():
    """Origineel bug-scenario: pot bezat 7.6 ATOM, Bitvavo had 45 ATOM
    (legacy). Vóór fix: rest_bonus_eur = 37 * 1.34 = €50 → sell_amount_eur
    = €60. Nu: cap kicks in, rest = 0."""
    bonus = _simulate_rest_bonus(
        actual_coins=45.0, expected_coins=7.6, price=1.34,
    )
    assert bonus == 0.0, f"Cap moest 45>0.76 rest weigeren, kreeg €{bonus:.2f}"


def test_true_dust_wel_meegepakt():
    """Echte dust (2% extra) moet wél mee — dat was het punt van rest_bonus."""
    # 7.6 pot + 0.15 dust (2%)
    bonus = _simulate_rest_bonus(
        actual_coins=7.75, expected_coins=7.6, price=1.34,
    )
    assert bonus > 0, "Kleine dust moet wél meegaan"
    assert 0.15 < bonus < 0.25, f"Dust-bonus ~€0.20, kreeg €{bonus:.4f}"


def test_exact_10pct_cap_grens():
    """Op de exacte 10%-grens: nog geldig (rest == max_dust)."""
    # 10 pot + 1.0 rest = 10% cap
    bonus = _simulate_rest_bonus(
        actual_coins=11.0, expected_coins=10.0, price=1.0,
    )
    assert bonus > 0, "Op 10% cap moet nog meegaan"


def test_boven_10pct_cap_weggehald():
    """1% boven cap → hele rest weg."""
    bonus = _simulate_rest_bonus(
        actual_coins=11.1, expected_coins=10.0, price=1.0,
    )
    assert bonus == 0.0, "Boven 10% cap moet rest → 0"


def test_proxied_user_skip():
    """Proxy-users (niet user-000) delen Bitvavo-keys met andere users
    → nooit rest sweep, ook al is het weinig."""
    bonus = _simulate_rest_bonus(
        actual_coins=7.7, expected_coins=7.6, price=1.34,
        is_proxied=True,
    )
    assert bonus == 0.0, "Proxied user moet 0 rest krijgen"


def test_geen_extra_coins():
    """Als er precies genoeg coins zijn: geen bonus."""
    bonus = _simulate_rest_bonus(
        actual_coins=7.6, expected_coins=7.6, price=1.34,
    )
    assert bonus == 0.0


def test_te_kleine_dust_filter():
    """Dust die minder dan €0.02 waard is: skip."""
    # 100 pot + 0.001 rest * €1 = €0.001 < €0.02
    bonus = _simulate_rest_bonus(
        actual_coins=100.001, expected_coins=100.0, price=1.0,
    )
    assert bonus == 0.0, "Sub-cent dust moet niet meegepakt worden"


def test_realistic_bcn_scenario():
    """Realistisch: BCH pot van €10 op €250 = 0.04 BCH, Bitvavo heeft
    0.041 BCH (2.5% dust). Bonus moet meegaan."""
    bonus = _simulate_rest_bonus(
        actual_coins=0.041, expected_coins=0.04, price=250.0,
    )
    assert bonus > 0, "Legitiem 2.5% dust moet meegaan"
    assert 0.2 < bonus < 0.3, f"Bonus ~€0.25, kreeg €{bonus:.4f}"
