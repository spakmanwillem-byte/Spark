"""
v6_rps_001 — Pure game-engine voor Steen-Papier-Schaar.

Herbruikbare module: bevat ALLEEN spel-logica, geen I/O.
Later inzetbaar voor D&D battles waar:
  - Schaar  = aanval
  - Steen   = verdediging
  - Papier  = ontwijken / inwijken

Functies:
  resolve(a, b) -> 'a' | 'b' | 'tie'
  counter_of(choice) -> choice that beats it
  predict_next(history, recent_window=10) -> aanbevolen counter-keuze
"""
import random
from typing import List, Literal

Choice = Literal['steen', 'papier', 'schaar']
CHOICES: List[Choice] = ['steen', 'papier', 'schaar']

# Wint-tabel: key verslaat value
BEATS = {
    'steen': 'schaar',
    'papier': 'steen',
    'schaar': 'papier',
}


def resolve(a: str, b: str) -> str:
    """Bepaal winnaar tussen twee keuzes.
    Returns: 'a' (a wint), 'b' (b wint), of 'tie'.
    """
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return 'tie'
    if BEATS.get(a) == b:
        return 'a'
    return 'b'


def counter_of(choice: str) -> str:
    """Returneer keuze die `choice` verslaat (de counter)."""
    choice = choice.lower().strip()
    for winner, loser in BEATS.items():
        if loser == choice:
            return winner
    return random.choice(CHOICES)


def predict_next(history: List[str], min_history: int = 10) -> str:
    """
    Voorspel Spark's optimale tegenzet op basis van speler-historie.

    Strategie:
      - Eerste `min_history` rondes: 100% random (Spark "leert nog")
      - Daarna: 60% counter-de-meest-voorkomende, 30% random, 10% mirror

    `history` = lijst van speler-keuzes (oudste eerst).
    """
    if len(history) < min_history:
        return random.choice(CHOICES)

    # Tel frequenties laatste 20 zetten (rolling window)
    recent = [h for h in history[-20:] if h in CHOICES]
    if not recent:
        return random.choice(CHOICES)

    freq = {c: recent.count(c) for c in CHOICES}
    most_common = max(freq, key=freq.get)

    r = random.random()
    if r < 0.60:
        return counter_of(most_common)
    if r < 0.90:
        return random.choice(CHOICES)
    return most_common  # mirror (anti-counter-counter)


def is_valid_choice(c: str) -> bool:
    return isinstance(c, str) and c.lower().strip() in CHOICES
