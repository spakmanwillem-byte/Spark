"""
v6_emotion_pipeline_001 — endpoints voor 7-laags emotie-pipeline (dry-run modus).
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .pipeline import run_pipeline

router = APIRouter(prefix="/emotion-pipeline", tags=["emotion-pipeline"])


class PipelineRunRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


@router.post("/run")
async def run(req: PipelineRunRequest):
    """Dry-run: draait alle 7 lagen en returnt trace + summary.
    Haakt NIET in op chat-flow."""
    return run_pipeline(req.text, user_id=req.user_id)


@router.get("/layers")
async def layers():
    """Documenteer welke 7 lagen bestaan + hun rol (voor UI)."""
    return {
        "success": True,
        "layers": [
            {"n": 1, "name": "Detectie",        "rol": "Emotionele context herkennen",
             "bron": "EmotionDetectionService (bestaand)"},
            {"n": 2, "name": "Weging",          "rol": "Kracht/prioriteit toekennen",
             "bron": "score → bracket (licht/midden/sterk/escalerend)"},
            {"n": 3, "name": "Contextfilter",   "rol": "Emotie kleurt betekenis",
             "bron": "lens per emotie (nieuwsgierig/frustratie/twijfel/...)"},
            {"n": 4, "name": "Identiteitstoets", "rol": "Gespiegeld aan Spark core",
             "bron": "identity_axes (transparantie/autonomie/menselijkheid/rust)"},
            {"n": 5, "name": "Norm/waarden",    "rol": "Passendheidstoets",
             "bron": "spark_bijbel.json (11 kernwaarden + 5 normen)"},
            {"n": 6, "name": "Actierouting",    "rol": "Welke behavior_class activeren",
             "bron": "mapping emotie → begrenzen/vertragen/exploreren/kalmeren"},
            {"n": 7, "name": "Expressie",       "rol": "Tempo/toon/directheid/detail",
             "bron": "presets per behavior_class"},
        ],
    }


# v6_emotion_pipeline_shadow_001 — Live shadow-runs uit chat-flow
@router.get("/shadow/recent")
async def shadow_recent(limit: int = 25):
    """Recente shadow-runs uit /data/emotions/pipeline_shadow/. Voor UI 'Live activity'."""
    from pathlib import Path as _P
    import json as _json
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    shadow_dir = _P(__file__).parent.parent.parent / "data" / "emotions" / "pipeline_shadow"
    runs = []
    # Lees laatste 7 dagen
    for i in range(7):
        day = (_dt.now(_tz.utc) - _td(days=i)).strftime("%Y-%m-%d")
        f = shadow_dir / f"{day}.jsonl"
        if not f.exists():
            continue
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    runs.append(_json.loads(line))
                except Exception:
                    pass
        except Exception:
            continue
    runs.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return {"success": True, "total": len(runs), "runs": runs[:limit]}


@router.get("/shadow/stats")
async def shadow_stats():
    """Aggregatie: hoe vaak welke emotie/behavior/kernwaarde getriggerd in shadow-modus."""
    from collections import Counter
    r = await shadow_recent(limit=10000)
    runs = r.get("runs", [])
    emo_c = Counter()
    beh_c = Counter()
    kw_c = Counter()
    for x in runs:
        s = x.get("summary") or {}
        if s.get("emotie"):
            emo_c[s["emotie"]] += 1
        if s.get("behavior"):
            beh_c[s["behavior"]] += 1
        if s.get("kernwaarde"):
            kw_c[s["kernwaarde"]] += 1
    return {
        "success": True,
        "total_runs": len(runs),
        "by_emotie": dict(emo_c.most_common()),
        "by_behavior": dict(beh_c.most_common()),
        "by_kernwaarde": dict(kw_c.most_common()),
    }
