"""
Achievements Routes
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from .service import AchievementService
from modules.core.storage import load_json

router = APIRouter(prefix="/achievements", tags=["achievements"])
service = AchievementService()


@router.get("/all")
async def get_all_achievements():
    """Get all available achievements"""
    return service.get_all()


@router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's achievement progress (auto-unlocks retroactively)"""
    result = service.get_user_progress(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return result


# v4_leaderboard_001 — Echte data uit user-progress (ipv frontend mock)
@router.get("/leaderboard")
async def get_leaderboard(period: str = "alltime", limit: int = 25):
    """
    Ranglijst van alle users op basis van XP / unlocks / word_count.
    period: 'alltime' (default), 'week', 'month' (laatste twee gebaseerd op recente unlocks).
    """
    users_file = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users_data = load_json(users_file, default={"users": []})
    results = []
    for u in users_data.get("users", []):
        uid = u.get("id")
        if not uid:
            continue
        try:
            prog = service.get_user_progress(uid)
        except Exception:
            prog = None
        if not prog:
            continue
        xp = prog.get("total_xp_earned", 0)
        unlocked_list = prog.get("unlocked", []) or []
        # Period filter
        if period in ("week", "month"):
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - (timedelta(days=7) if period == "week" else timedelta(days=30))
            recent_unlocks = []
            recent_xp = 0
            for a in unlocked_list:
                ts = a.get("unlocked_at")
                if not ts:
                    continue
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt >= cutoff:
                        recent_unlocks.append(a)
                        recent_xp += a.get("xp_reward", 0)
                except Exception:
                    continue
            xp = recent_xp
            achievements_count = len(recent_unlocks)
        else:
            achievements_count = len(unlocked_list)
        results.append({
            "user_id": uid,
            "naam": prog.get("user_naam") or u.get("naam") or uid,
            "gradatie": prog.get("user_gradatie") or u.get("gradatie", 7),
            "gradatie_titel": u.get("rol") or "",
            "xp": int(xp),
            "level": int(xp // 100) if xp else 0,
            "achievements": achievements_count,
            "words": prog.get("word_count", 0),
            "is_bot": uid.startswith("bot-"),
        })
    # Sort op XP desc
    results.sort(key=lambda r: r["xp"], reverse=True)
    # Rank toevoegen
    for i, r in enumerate(results[:limit], start=1):
        r["rank"] = i
    return {"period": period, "leaderboard": results[:limit], "total_users": len(results)}
