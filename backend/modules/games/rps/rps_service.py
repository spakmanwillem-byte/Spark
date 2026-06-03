"""
v6_rps_001 — Steen-Papier-Schaar service: sessies, stats, learning.
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from modules.core.storage import load_json, save_json
from modules.chat.xp_service import grant_xp
from modules.games.rps import rps_engine

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "games" / "rps"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSIONS_FILE = DATA_DIR / "sessions.json"
STATS_FILE = DATA_DIR / "stats.json"
LEARNING_FILE = DATA_DIR / "learning.json"

XP_PER_WIN = 10
XP_PER_TIE = 1
XP_PER_LOSS = 0
ACH_FIRST_WIN_BONUS = 25
ACH_FIRST_LOSS_BONUS = 10  # "voor de moed"
ACH_STREAK_5_BONUS = 50

# v6_rps_battle_001 — Battle = 10 rondes, ≥6 wins = battle won
BATTLE_ROUNDS = 10
BATTLE_WIN_THRESHOLD = 6
GOLD_PER_BATTLE_WIN = 10
STARTING_GOLD = 1000

GOLD_FILE = DATA_DIR.parent.parent / "users" / "gold_balances.json"
GOLD_FILE.parent.mkdir(parents=True, exist_ok=True)


def _get_gold(user_id: str) -> int:
    """Returneer goud-saldo. Eerste gebruik geeft default STARTING_GOLD."""
    d = load_json(GOLD_FILE, default={"balances": {}})
    bals = d.get("balances", {})
    if user_id not in bals:
        bals[user_id] = STARTING_GOLD
        d["balances"] = bals
        save_json(GOLD_FILE, d)
    return bals[user_id]


def _add_gold(user_id: str, delta: int, reason: str = "") -> int:
    d = load_json(GOLD_FILE, default={"balances": {}, "log": []})
    bals = d.setdefault("balances", {})
    bals[user_id] = bals.get(user_id, STARTING_GOLD) + delta
    d.setdefault("log", []).append({
        "ts": _now(), "user_id": user_id, "delta": delta,
        "balance": bals[user_id], "reason": reason,
    })
    save_json(GOLD_FILE, d)
    return bals[user_id]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_session(user_id: str) -> dict:
    data = load_json(SESSIONS_FILE, default={"sessions": {}})
    sessions = data.get("sessions", {})
    if user_id not in sessions:
        sessions[user_id] = {
            "wins": 0, "losses": 0, "ties": 0,
            "current_streak": 0, "best_streak_session": 0,
            "started_at": _now(),
        }
        data["sessions"] = sessions
        save_json(SESSIONS_FILE, data)
    return sessions[user_id]


def _save_session(user_id: str, session: dict):
    data = load_json(SESSIONS_FILE, default={"sessions": {}})
    data.setdefault("sessions", {})[user_id] = session
    save_json(SESSIONS_FILE, data)


def _get_stats(user_id: str) -> dict:
    data = load_json(STATS_FILE, default={"stats": {}})
    stats = data.get("stats", {})
    if user_id not in stats:
        stats[user_id] = {
            "wins": 0, "losses": 0, "ties": 0, "total": 0,
            "longest_streak": 0,
            "achievements": {},  # name -> awarded_at iso
            "first_played_at": _now(),
        }
        data["stats"] = stats
        save_json(STATS_FILE, data)
    return stats[user_id]


def _save_stats(user_id: str, stats: dict):
    data = load_json(STATS_FILE, default={"stats": {}})
    data.setdefault("stats", {})[user_id] = stats
    save_json(STATS_FILE, data)


def _get_history(user_id: str) -> list:
    data = load_json(LEARNING_FILE, default={"history": {}})
    return data.get("history", {}).get(user_id, [])


def _append_history(user_id: str, choice: str, max_keep: int = 100):
    data = load_json(LEARNING_FILE, default={"history": {}})
    h = data.setdefault("history", {}).setdefault(user_id, [])
    h.append(choice)
    if len(h) > max_keep:
        data["history"][user_id] = h[-max_keep:]
    save_json(LEARNING_FILE, data)


def start_session(user_id: str, opponent: str = "spark") -> dict:
    """Forceer fresh sessie-state (reset score). Stats blijven intact.

    opponent: "spark" (Spark zelf, leert) | "bot-dood" (slim/moeilijk) |
              "bot-madelief"/"bot-harry"/"bot-smith"/"bot-boekhouder" (random, makkelijk).
    """
    import random as _r
    if opponent == "bot":
        # Kies random bot — bot-dood = moeilijk, anderen = random
        opponent = _r.choice(["bot-madelief", "bot-harry", "bot-smith", "bot-boekhouder", "bot-dood"])
    session = {
        "wins": 0, "losses": 0, "ties": 0,
        "current_streak": 0, "best_streak_session": 0,
        "started_at": _now(),
        "opponent": opponent,  # v6_rps_opponent_001
    }
    _save_session(user_id, session)
    return session


def reset_session(user_id: str, opponent: str = None) -> dict:
    """Reset alleen huidige sessie-score (alias voor start).

    Als `opponent` niet gegeven, behoud huidige opponent.
    """
    if opponent is None:
        cur = _get_session(user_id)
        opponent = cur.get("opponent", "spark")
    return start_session(user_id, opponent=opponent)


def get_session(user_id: str) -> dict:
    return _get_session(user_id)


def get_stats(user_id: str) -> dict:
    """v6_rps_battle_001 — verrijk met battles + goud."""
    s = _get_stats(user_id)
    return {
        **s,
        "battles_won": s.get("battles_won", 0),
        "battles_lost": s.get("battles_lost", 0),
        "gold": _get_gold(user_id),
    }


def stop_session(user_id: str) -> dict:
    """Sluit sessie af, retourneert eind-samenvatting."""
    session = _get_session(user_id)
    # Sessie wissen
    data = load_json(SESSIONS_FILE, default={"sessions": {}})
    if user_id in data.get("sessions", {}):
        del data["sessions"][user_id]
        save_json(SESSIONS_FILE, data)
    return session


def play_round(user_id: str, player_choice: str) -> dict:
    """
    Speel één ronde. Returneert volledige uitkomst incl. tegenstander-keuze,
    sessie-score, XP-delta en eventuele nieuwe achievements.

    Tegenstander wordt afgeleid uit huidige sessie:
      - "spark" / "bot-dood": slim algoritme (eerste 10 random, dan counter)
      - andere bots: 100% random (makkelijk)
    """
    import random as _r
    if not rps_engine.is_valid_choice(player_choice):
        return {"success": False, "error": f"Ongeldige keuze: {player_choice}"}
    player_choice = player_choice.lower().strip()

    session = _get_session(user_id)
    opponent = session.get("opponent", "spark")

    # Bepaal tegenstander-keuze op basis van opponent-type
    history = _get_history(user_id)
    if opponent in ("spark", "bot-dood"):
        opp_choice = rps_engine.predict_next(history)
        is_learning = len(history) < 10
    else:
        # Easy bots — puur random, geen leren
        opp_choice = _r.choice(rps_engine.CHOICES)
        is_learning = False

    outcome = rps_engine.resolve(player_choice, opp_choice)  # 'a' = player wins

    # Update sessie
    if outcome == 'a':
        session["wins"] += 1
        session["current_streak"] += 1
        session["best_streak_session"] = max(session["best_streak_session"], session["current_streak"])
        result_label = "gewonnen"
        xp_delta = XP_PER_WIN
    elif outcome == 'b':
        session["losses"] += 1
        session["current_streak"] = 0
        result_label = "verloren"
        xp_delta = XP_PER_LOSS
    else:
        session["ties"] += 1
        result_label = "gelijkspel"
        xp_delta = XP_PER_TIE
    _save_session(user_id, session)

    # Update lifetime stats
    stats = _get_stats(user_id)
    stats["total"] += 1
    if outcome == 'a':
        stats["wins"] += 1
    elif outcome == 'b':
        stats["losses"] += 1
    else:
        stats["ties"] += 1
    stats["longest_streak"] = max(stats["longest_streak"], session["current_streak"])

    # v6_rps_battle_001 — Battle-evaluatie elke 10 rondes
    battle_event = None
    rounds_total = session["wins"] + session["losses"] + session["ties"]
    if rounds_total > 0 and rounds_total % BATTLE_ROUNDS == 0:
        battle_idx = rounds_total // BATTLE_ROUNDS
        # Tel wins in deze "batch" — verschil tussen huidige sessie-wins en
        # eerder geboekt voor battles
        wins_in_batch = session["wins"] - session.get("_battles_wins_accounted", 0)
        battle_won = wins_in_batch >= BATTLE_WIN_THRESHOLD
        session["_battles_wins_accounted"] = session["wins"]
        if battle_won:
            stats["battles_won"] = stats.get("battles_won", 0) + 1
            new_gold = _add_gold(user_id, GOLD_PER_BATTLE_WIN,
                                 reason=f"rps_battle_won_{battle_idx}")
        else:
            stats["battles_lost"] = stats.get("battles_lost", 0) + 1
            new_gold = _get_gold(user_id)
        battle_event = {
            "won": battle_won,
            "battle_index": battle_idx,
            "wins_in_battle": wins_in_batch,
            "gold_delta": GOLD_PER_BATTLE_WIN if battle_won else 0,
            "new_gold": new_gold,
        }
        _save_session(user_id, session)

    # Achievements
    new_achievements = []
    achievements = stats.setdefault("achievements", {})
    if outcome == 'a' and "rps_first_win" not in achievements:
        achievements["rps_first_win"] = _now()
        new_achievements.append({"key": "rps_first_win", "title": "Eerste overwinning",
                                 "text": "Je hebt voor het eerst gewonnen met Steen-Papier-Schaar!",
                                 "bonus_xp": ACH_FIRST_WIN_BONUS})
        xp_delta += ACH_FIRST_WIN_BONUS
    if outcome == 'b' and "rps_first_loss" not in achievements:
        achievements["rps_first_loss"] = _now()
        new_achievements.append({"key": "rps_first_loss", "title": "Eerste verlies",
                                 "text": "Verliezen mag — Spark eert je moed.",
                                 "bonus_xp": ACH_FIRST_LOSS_BONUS})
        xp_delta += ACH_FIRST_LOSS_BONUS
    if session["current_streak"] == 5 and "rps_streak_5" not in achievements:
        achievements["rps_streak_5"] = _now()
        new_achievements.append({"key": "rps_streak_5", "title": "5 op een rij!",
                                 "text": "Vijf keer achter elkaar gewonnen — meesterlijk.",
                                 "bonus_xp": ACH_STREAK_5_BONUS})
        xp_delta += ACH_STREAK_5_BONUS
    _save_stats(user_id, stats)

    # Update learning history
    _append_history(user_id, player_choice)

    # Grant XP
    new_xp = None
    if xp_delta > 0:
        xp_res = grant_xp(user_id, xp_delta, reason=f"rps_{result_label}")
        new_xp = xp_res.get("new_xp")

    return {
        "success": True,
        "player_choice": player_choice,
        "opponent": opponent,
        "opponent_choice": opp_choice,
        "spark_choice": opp_choice,  # backward-compat alias
        "outcome": result_label,  # gewonnen / verloren / gelijkspel
        "session": session,
        "lifetime_wins": stats["wins"],
        "lifetime_losses": stats["losses"],
        "lifetime_ties": stats["ties"],
        "longest_streak": stats["longest_streak"],
        "battles_won": stats.get("battles_won", 0),
        "battles_lost": stats.get("battles_lost", 0),
        "battle_event": battle_event,
        "gold": _get_gold(user_id),
        "xp_delta": xp_delta,
        "new_xp": new_xp,
        "new_achievements": new_achievements,
        "spark_is_learning": is_learning,
        "history_length": len(history) + 1,
    }
