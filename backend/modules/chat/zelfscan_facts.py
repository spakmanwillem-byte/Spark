"""v13_zelfscan_facts_001 — feiten-helpers voor Spark's Zelfscan.

Voorkomt LLM-hallucinaties zoals '73% blij' terwijl de shadow-pipeline
95% neutraal registreert. Lees echte JSONL-events uit
`data/emotions/pipeline_shadow/*.jsonl`.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DATA = Path(__file__).parent.parent.parent / "data"
_SHADOW_DIR = _DATA / "emotions" / "pipeline_shadow"


def _read_jsonl(fp: Path) -> List[Dict]:
    """Best-effort JSONL reader — skip corrupte regels."""
    out: List[Dict] = []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return out


def get_emotion_stats(
    days: int = 7,
    user_id: Optional[str] = None,
) -> Dict:
    """Aggregeer echte emotie-distributie uit shadow-pipeline.

    Args:
      days:    hoeveel dagen terug (default 7)
      user_id: filter op user; None = alle

    Returns:
      {
        "total": N,
        "days_covered": M,
        "distribution": {"neutral": 45, "blij": 3, "boos": 1, ...},
        "distribution_pct": {"neutral": 91.8, "blij": 6.1, ...},
        "dominant": "neutral",
        "sample_range": ["YYYY-MM-DD", "YYYY-MM-DD"],
      }
    """
    if not _SHADOW_DIR.exists():
        return {"total": 0, "distribution": {}, "distribution_pct": {}, "dominant": None,
                "days_covered": 0, "sample_range": []}

    today = datetime.now(timezone.utc).date()
    cutoff_date = today - timedelta(days=days)

    counter: Counter = Counter()
    days_seen = set()
    dates_used: List[str] = []

    for fp in sorted(_SHADOW_DIR.glob("*.jsonl")):
        try:
            file_date = datetime.strptime(fp.stem, "%Y-%m-%d").date()
        except Exception:
            continue
        if file_date < cutoff_date or file_date > today:
            continue
        events = _read_jsonl(fp)
        if user_id:
            events = [e for e in events if e.get("user_id") == user_id]
        if not events:
            continue
        days_seen.add(fp.stem)
        dates_used.append(fp.stem)
        for e in events:
            emo = ((e.get("summary") or {}).get("emotie") or "onbekend").lower().strip()
            # v13: normalize NL/EN duplicates
            if emo in ("neutral", "neutraal", "neutral/neutraal"):
                emo = "neutraal"
            counter[emo] += 1

    total = sum(counter.values())
    if total == 0:
        return {"total": 0, "distribution": {}, "distribution_pct": {}, "dominant": None,
                "days_covered": len(days_seen), "sample_range": dates_used[:2]}

    distribution = dict(counter.most_common())
    distribution_pct = {k: round(v * 100 / total, 1) for k, v in distribution.items()}
    dominant = counter.most_common(1)[0][0]

    return {
        "total": total,
        "days_covered": len(days_seen),
        "distribution": distribution,
        "distribution_pct": distribution_pct,
        "dominant": dominant,
        "sample_range": [dates_used[0], dates_used[-1]] if dates_used else [],
    }


def format_emotion_stats_for_prompt(stats: Dict) -> str:
    """Compact snippet voor injectie in Zelfscan-output of LLM-context."""
    if not stats or stats.get("total", 0) == 0:
        return "🎭 **Emoties**: geen shadow-data in laatste periode"

    total = stats["total"]
    pct = stats["distribution_pct"]
    top3 = list(pct.items())[:3]
    top_str = " · ".join(f"{k} {v}%" for k, v in top3)
    days = stats.get("days_covered", 0)
    return f"🎭 **Emotie-distributie** (laatste {days} dagen, {total} events): {top_str}"
