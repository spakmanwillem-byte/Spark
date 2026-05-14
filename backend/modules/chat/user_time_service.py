"""
User-time helper (v4_025) — Spark is altijd bewust van de juiste lokale tijd
per gebruiker. Cascade:
  1. user.timezone (expliciet)
  2. user.adres.land → land→tz lookup
  3. user.persoonlijke_info.land → idem
  4. systeem-locale (server) als laatste vangnet
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# Minimal land→TZ lookup voor Spark's voornaamste markt (NL + omringende landen).
# Uitbreidbaar via /data/system/timezone_overrides.json indien nodig.
LAND_TIMEZONE = {
    "nederland": "Europe/Amsterdam",
    "the netherlands": "Europe/Amsterdam",
    "holland": "Europe/Amsterdam",
    "nl": "Europe/Amsterdam",
    "belgië": "Europe/Brussels",
    "belgium": "Europe/Brussels",
    "duitsland": "Europe/Berlin",
    "germany": "Europe/Berlin",
    "frankrijk": "Europe/Paris",
    "france": "Europe/Paris",
    "verenigd koninkrijk": "Europe/London",
    "uk": "Europe/London",
    "united kingdom": "Europe/London",
    "spanje": "Europe/Madrid",
    "italië": "Europe/Rome",
    "portugal": "Europe/Lisbon",
    "ierland": "Europe/Dublin",
    "zwitserland": "Europe/Zurich",
    "verenigde staten": "America/New_York",
    "vs": "America/New_York",
    "usa": "America/New_York",
    "canada": "America/Toronto",
    "australië": "Australia/Sydney",
    "japan": "Asia/Tokyo",
    "china": "Asia/Shanghai",
    "indonesië": "Asia/Jakarta",
    "indonesie": "Asia/Jakarta",
}

DEFAULT_TZ = "Europe/Amsterdam"


def resolve_user_timezone(user: Optional[dict]) -> str:
    """Geef tz-string voor user. Valt veilig terug op Europe/Amsterdam."""
    if not user:
        return DEFAULT_TZ
    # 1. Expliciet veld
    tz = user.get("timezone") or user.get("tz")
    if tz:
        return tz
    # 2. adres.land
    for path in (("adres", "land"), ("persoonlijke_info", "land")):
        block = user.get(path[0])
        if isinstance(block, dict):
            land = (block.get(path[1]) or "").lower().strip()
            if land in LAND_TIMEZONE:
                return LAND_TIMEZONE[land]
    return DEFAULT_TZ


def now_for_user(user: Optional[dict]) -> datetime:
    """Lokale datetime voor deze user. Gebruikt zoneinfo (Python 3.9+)."""
    tz_name = resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        # Fallback: server-tijd als naive
        return datetime.now()


def time_awareness_block(user: Optional[dict]) -> dict:
    """Volledig overzicht voor chat-debug + observer. Bevat:
      - now_iso: huidige lokale tijd
      - timezone: gebruikte tz
      - weekdag, datum, tijd, dagdeel (ochtend/middag/avond/nacht)
      - source: waaruit timezone is afgeleid
    """
    tz = resolve_user_timezone(user)
    now = now_for_user(user)
    h = now.hour
    if 5 <= h < 12:
        dagdeel = "ochtend"
    elif 12 <= h < 18:
        dagdeel = "middag"
    elif 18 <= h < 23:
        dagdeel = "avond"
    else:
        dagdeel = "nacht"

    source = "default"
    if user:
        if user.get("timezone") or user.get("tz"):
            source = "user.timezone"
        elif (user.get("adres") or {}).get("land"):
            source = "user.adres.land"
        elif (user.get("persoonlijke_info") or {}).get("land"):
            source = "user.persoonlijke_info.land"

    dagen_nl = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
    return {
        "now_iso": now.isoformat(),
        "timezone": tz,
        "weekdag": dagen_nl[now.weekday()],
        "datum": now.strftime("%Y-%m-%d"),
        "tijd": now.strftime("%H:%M"),
        "dagdeel": dagdeel,
        "tz_source": source,
    }
