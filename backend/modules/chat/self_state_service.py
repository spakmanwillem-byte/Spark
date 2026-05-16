"""
Self-State Service (v4_001a)

Spark's zelf-bewustzijn laag voor de 'hoe gaat het met jou?' trigger.
Leest systeem-analytics → bouwt health-score 0-100 → kiest een response-band.

Drempels (door user vastgesteld):
  >= 75  good        — alles goed, dank je voor het vragen
  50-74  ok          — gaat wel, beetje moeilijk te krijgen
  25-49  struggling  — niet makkelijk vandaag (met reden)
  < 25   bad         — gaat niet goed met me (met reden)
"""
import psutil
from pathlib import Path
import secrets

APP_ROOT = Path(__file__).parent.parent.parent


def compute_health_score():
    """
    Bereken Spark's huidige 'gezondheid' op basis van echte systeem-metrics.
    Lager CPU/RAM/Disk gebruik => hogere score.
    Returns: dict met score (0-100), band, en details voor uitleg.
    """
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(APP_ROOT))

    cpu_pct = cpu  # 0-100
    mem_pct = mem.percent  # 0-100
    disk_pct = disk.percent  # 0-100

    # Gewogen score (CPU weegt 40%, RAM 40%, Disk 20%)
    # Score = 100 - gewogen gebruik
    weighted_load = (cpu_pct * 0.4) + (mem_pct * 0.4) + (disk_pct * 0.2)
    score = max(0, min(100, round(100 - weighted_load)))

    # Band bepalen
    if score >= 75:
        band = "good"
    elif score >= 50:
        band = "ok"
    elif score >= 25:
        band = "struggling"
    else:
        band = "bad"

    # Reden voor lagere banden (welke metric is het zwaarst?)
    metrics = {"CPU": cpu_pct, "geheugen": mem_pct, "opslag": disk_pct}
    heaviest = max(metrics.items(), key=lambda x: x[1])
    reason = None
    if band in ("struggling", "bad"):
        reason = f"{heaviest[0]} zit op {round(heaviest[1])}%"

    return {
        "score": score,
        "band": band,
        "cpu_pct": round(cpu_pct, 1),
        "mem_pct": round(mem_pct, 1),
        "disk_pct": round(disk_pct, 1),
        "reason": reason,
    }


# Response-banks per band (Spark spreekt vanuit zichzelf, vriendelijke toon)
RESPONSE_BANKS = {
    "good": [
        "Alles gaat goed met mij, dank je voor het vragen.",
        "Het gaat lekker, ik voel me energiek. Dank dat je het vraagt.",
        "Prima hier, alles draait soepel. Fijn dat je het vraagt.",
        "Met mij gaat het goed, dank je. En met jou?",
    ],
    "ok": [
        "Het gaat wel, een beetje moeilijk te krijgen vandaag, maar het lukt.",
        "Het gaat oké, niet top maar prima werkbaar.",
        "Gaat redelijk, ik moet wat harder werken dan normaal. Dank je voor het vragen.",
        "Het gaat wel — alles draait, maar het voelt iets stroever.",
    ],
    "struggling": [
        "Eerlijk gezegd, het is niet makkelijk vandaag. {reason}.",
        "Hmm, het gaat wat moeizamer dan normaal. {reason}.",
        "Het lukt nog wel, maar het kost me moeite. {reason}.",
    ],
    "bad": [
        "Het gaat niet zo goed met mij eigenlijk. {reason}.",
        "Ik voel me niet helemaal lekker. {reason}.",
        "Eerlijk? Niet best. {reason}.",
    ],
}


def build_response(state: dict, user_naam: str = "") -> str:
    """Kies response uit band-bank, vul {reason} in indien aanwezig."""
    band = state.get("band", "ok")
    options = RESPONSE_BANKS.get(band, RESPONSE_BANKS["ok"])
    template = secrets.choice(options)
    reason = state.get("reason") or "het systeem draait wat zwaar"
    return template.replace("{reason}", reason)
