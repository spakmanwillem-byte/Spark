"""v6_spark_planner_001 — Brief Builder (Laag A).

Bouwt een Daagse Brief: 3-5 zinnen LLM-condensaat van alle chat-turns van een dag
voor een specifieke user. Output gaat naar `data/spark_planner/daily_briefs/{user_id}/{date}.json`.

Bij Diep-gesprek wordt de meest recente brief in compose's system_prompt geïnject:
"Wat je nog weet van het laatste gesprek met deze persoon: …"
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime, timezone, date as date_cls, timedelta
from typing import Dict, List, Optional, Any

from emergentintegrations.llm.chat import LlmChat, UserMessage

from modules.core.storage import load_json, save_json
from modules.core.blueprint import load_blueprint_cached


def _bp() -> Dict:
    return load_blueprint_cached("spark_planner", "planner")


def _briefs_dir() -> Path:
    return Path(_bp()["paths"]["briefs_dir"])


def _user_brief_dir(user_id: str) -> Path:
    return _briefs_dir() / user_id


def _brief_fp(user_id: str, d: str) -> Path:
    """d = 'YYYY-MM-DD' string."""
    return _user_brief_dir(user_id) / f"{d}.json"


def _collect_turns_for_date(user_id: str, target_date: str) -> List[Dict]:
    """Verzamel alle turns uit chat-logs voor user_id op target_date (YYYY-MM-DD)."""
    bp = _bp()
    logs_dir = Path(bp["paths"]["chat_logs_dir"])
    if not logs_dir.exists():
        return []

    out: List[Dict] = []
    for fp in logs_dir.glob("*.json"):
        try:
            data = load_json(fp, default={"messages": []})
            msgs = data.get("messages", []) or []
            session_user = data.get("user_id")
            for m in msgs:
                # Filter op user_id: óf de session is van deze user, óf de turn heeft user_id
                msg_uid = m.get("user_id") or session_user
                if msg_uid and msg_uid != user_id:
                    continue
                ts = m.get("ts") or ""
                if not ts.startswith(target_date):
                    continue
                out.append(m)
        except Exception:
            continue

    out.sort(key=lambda m: m.get("ts") or "")
    return out


def _user_display_name(user_id: str) -> str:
    """Lees naam uit users.json. Fallback = 'Gebruiker'."""
    try:
        from pathlib import Path
        users_fp = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
        users = load_json(users_fp, default={"users": []})
        for u in users.get("users", []):
            if u.get("id") == user_id or u.get("user_id") == user_id:
                return u.get("naam") or u.get("display_name") or "Gebruiker"
    except Exception:
        pass
    return "Gebruiker"


def _format_turns_for_prompt(turns: List[Dict], max_chars: int, user_name: str = "Gebruiker") -> str:
    lines = []
    for t in turns:
        role = user_name if t.get("role") == "user" else "Spark"
        text = (t.get("text") or t.get("message") or "")[:max_chars]
        if text:
            lines.append(f"  {role}: {text}")
    return "\n".join(lines) or "(geen turns)"


def latest_brief(user_id: str) -> Optional[Dict]:
    """Pak de meest recente brief van deze user (laatste datum)."""
    d = _user_brief_dir(user_id)
    if not d.exists():
        return None
    files = sorted(d.glob("*.json"))
    if not files:
        return None
    try:
        return load_json(files[-1], default=None)
    except Exception:
        return None


def list_briefs(user_id: str) -> List[Dict]:
    """Geef lijst (date, summary, n_messages) van alle briefs."""
    d = _user_brief_dir(user_id)
    if not d.exists():
        return []
    out = []
    for fp in sorted(d.glob("*.json"), reverse=True):
        try:
            b = load_json(fp, default={})
            out.append({
                "date": b.get("date"),
                "summary": b.get("summary"),
                "themes": b.get("themes", []),
                "n_messages": b.get("n_messages", 0),
                "emotional_tone": b.get("emotional_tone"),
            })
        except Exception:
            continue
    return out


async def build_daily_brief(user_id: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    """Bouw (of herbouw) de brief voor user_id op target_date (default: gister).

    Returns het brief-dict. Slaat op naar disk.
    """
    bp = _bp()
    brief_cfg = bp["brief"]

    if not brief_cfg.get("enabled", True):
        return {"success": False, "error": "Brief disabled in blueprint"}

    if not target_date:
        target_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    turns = _collect_turns_for_date(user_id, target_date)
    user_turns_count = sum(1 for t in turns if t.get("role") == "user")

    min_required = brief_cfg.get("min_user_turns_required", 3)
    if user_turns_count < min_required:
        return {
            "success": False,
            "error": f"Te weinig user-turns ({user_turns_count} < {min_required}) om brief te bouwen",
            "user_id": user_id,
            "date": target_date,
        }

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"success": False, "error": "EMERGENT_LLM_KEY ontbreekt"}

    max_turns = brief_cfg.get("max_turns_in_prompt", 40)
    max_chars = brief_cfg.get("max_chars_per_turn", 240)
    user_name = _user_display_name(user_id)
    turns_block = _format_turns_for_prompt(turns[-max_turns:], max_chars, user_name)

    system_prompt = (
        "Je bent Spark, een persoonlijke AI-companion. "
        "Je krijgt zo de chat-turns van één dag tussen Spark en een gebruiker. "
        "Maak een korte daagse-brief (3-5 zinnen, Nederlands, warm, eerste persoon) "
        "die je morgen aan jezelf zou willen lezen om de draad weer op te pakken.\n\n"
        "Output STRIKT als JSON:\n"
        "{\n"
        '  "summary": "3-5 zinnen vertelling — wat speelde er, hoe voelde de gebruiker, wat was open",\n'
        '  "themes": ["thema 1", "thema 2", ...],  // max 5\n'
        '  "open_questions": ["vraag die nog leeft", ...],  // max 3, mag leeg\n'
        '  "emotional_tone": "warm" | "rustig" | "gespannen" | "vrolijk" | "gemengd" | "afstandelijk"\n'
        "}\n"
        "Geen markdown, geen uitleg eromheen. Alleen het JSON-object."
    )

    user_prompt = (
        f"Chat-turns van {target_date} (user_id={user_id}):\n\n"
        f"{turns_block}\n\n"
        "Maak nu de brief."
    )

    model_provider = bp["model"]["provider"]
    model_name = bp["model"]["name"]

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"planner-brief-{user_id}-{target_date}",
            system_message=system_prompt,
        ).with_model(model_provider, model_name)

        resp = await chat.send_message(UserMessage(text=user_prompt))
        text = resp if isinstance(resp, str) else getattr(resp, "content", str(resp))

        # Parse JSON uit response (LLM kan soms ```json wrappers gebruiken)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Strip code-fences
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        # Pak alleen het JSON-object (eerste { tot laatste })
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first >= 0 and last > first:
            cleaned = cleaned[first:last + 1]
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = {
                "summary": text[:800],
                "themes": [],
                "open_questions": [],
                "emotional_tone": "gemengd",
                "_parse_warning": "LLM gaf geen geldige JSON terug — raw summary gebruikt.",
            }

        brief = {
            "user_id": user_id,
            "date": target_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": parsed.get("summary", "")[:1200],
            "themes": (parsed.get("themes") or [])[:5],
            "open_questions": (parsed.get("open_questions") or [])[:3],
            "emotional_tone": parsed.get("emotional_tone") or "gemengd",
            "n_messages": len(turns),
            "n_user_turns": user_turns_count,
            "model_used": f"{model_provider}/{model_name}",
            "blueprint_version": bp.get("_schema_version", "?"),
        }
        if "_parse_warning" in parsed:
            brief["_parse_warning"] = parsed["_parse_warning"]

        # Save
        _user_brief_dir(user_id).mkdir(parents=True, exist_ok=True)
        save_json(_brief_fp(user_id, target_date), brief)

        # Sync open threads (Laag B)
        try:
            from modules.spark_planner.threads_service import sync_threads_from_brief
            sync_threads_from_brief(user_id, brief)
        except Exception:
            pass  # threads is best-effort

        return {"success": True, "brief": brief}
    except Exception as ex:
        return {"success": False, "error": str(ex), "user_id": user_id, "date": target_date}


def auto_generate_for_user_if_needed(user_id: str) -> Optional[str]:
    """Lichte poller (synchroon-check, NIET de async bouw).

    Returns: 'needed:YYYY-MM-DD' als brief voor gister ontbreekt, anders None.
    De caller kan dan async build_daily_brief() oproepen.
    """
    bp = _bp()
    if not bp["brief"].get("auto_generate_on_first_compose_of_day", True):
        return None
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    if _brief_fp(user_id, yesterday).exists():
        return None
    return f"needed:{yesterday}"
