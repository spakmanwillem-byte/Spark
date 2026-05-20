"""
Dank Service — Sparks eigen bedank-uiting
  • Bij "Spark wat zou jij willen doen?" (vrije keus) → 1x bedanken, daarna agenda/roadmap
  • Bij "credits" / "wie heeft jou mogelijk gemaakt?" → altijd bedanken
Storage: /app/backend/data/system/dank.json
"""
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DANK_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "dank.json"
USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"

# Credits bonus voor users die in de bedank-lijst staan EN gradatie ≤ 4
CREDITS_GRADATIE_MAX = 4
CREDITS_TRUST_BOOST = 10        # one-time, opgeteld bij trust_score (max 100)
CREDITS_TRUST_MULTIPLIER = 1.2  # toekomstige trust-gains × 1.2


# ============================================================
# DETECTORS
# ============================================================

# Vrije keuze: "Spark wat zou jij willen doen", "wat wil je zelf"
_FREE_CHOICE_PATTERNS = [
    r"\bwat zou (jij|je) willen doen\b",
    r"\bwat wil (jij|je) (zelf )?doen\b",
    r"\bwat zou (jij|je) (zelf )?kiezen\b",
    r"\b(kies|bepaal) (jij|je) zelf\b",
    r"\bjouw keuze\b",
    r"\bwat zou (jij|je) (graag )?willen\b",
]

# Credits: "credits", "wie heeft jou mogelijk gemaakt", "aan wie ben je dank verschuldigd"
_CREDITS_PATTERNS = [
    r"\bcredits\b",
    r"\bwie heeft (jou|je) (mogelijk )?gemaakt\b",
    r"\bwie zit(ten)? (er )?achter (jou|je)\b",
    r"\baan wie ben je (dank|dankbaar)\b",
    r"\b(wie|aan wie) (mag|moet) (ik|jij) bedanken\b",
    r"\bdank je (de )?(makers|community)\b",
    r"\bwie heeft je (geholpen|gesteund)\b",
]

# Rename in credits/dank-lijst: "verander X naar Y in de credits"
# Vereist scope-keyword (credits|bedank|dank) ergens in zin.
_RENAME_VERB = r"(?:verander(?:de|en)?|wijzig(?:en|de)?|pas .{1,30}? aan|hernoem|maak)"
_RENAME_SCOPE = r"\b(credits|bedank|bedanklijst|bedanklijstje|dank|danklijst)\b"
# Name word: niet een stopwoord (naar/in/tot/de/het/credits etc)
_NW = r"(?!(?:naar|in|tot|aan|uit|de|het|een|toe|erbij|credits|bedank|bedanklijst|bedanklijstje|dank|danklijst|lijst)\b)[A-Za-zÀ-ÿ][\w'\-]*"
_NAME = rf"{_NW}(?:\s+{_NW}){{0,3}}"
_RENAME_REGEX = re.compile(
    rf"{_RENAME_VERB}\s+(?P<old>{_NAME})\s+(?:naar|in|tot)\s+(?P<new>{_NAME})",
    re.IGNORECASE,
)
# Alternatief: "pas X aan naar/tot Y"
_RENAME_PAS_REGEX = re.compile(
    rf"\bpas\s+(?P<old>{_NAME})\s+aan\s+(?:naar|tot|in)\s+(?P<new>{_NAME})",
    re.IGNORECASE,
)
# Verwijder uit credits-lijst
_REMOVE_REGEX = re.compile(
    rf"(?:verwijder|haal\s+(?:weg\s+)?|wis|delete)\s+(?P<name>{_NAME})",
    re.IGNORECASE,
)
# Voeg toe aan credits-lijst
_ADD_REGEX = re.compile(
    rf"(?:voeg(?:\s+toe)?|zet\s+erbij)\s+(?P<name>{_NAME})",
    re.IGNORECASE,
)


def detect_free_choice_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _FREE_CHOICE_PATTERNS)


def detect_credits_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _CREDITS_PATTERNS)


def _has_credits_scope(text: str) -> bool:
    return bool(re.search(_RENAME_SCOPE, (text or "").lower()))


def detect_credits_edit_intent(text: str) -> Optional[Dict[str, str]]:
    """Detecteer rename/add/remove binnen credits-scope.
    Geeft dict {action, ...} terug of None.
    Scope-keyword (credits|bedank|dank) is verplicht om kapen te voorkomen."""
    if not text:
        return None
    if not _has_credits_scope(text):
        return None
    t = text.strip()

    m = _RENAME_REGEX.search(t) or _RENAME_PAS_REGEX.search(t)
    if m:
        old = m.group("old").strip().rstrip(".,!?")
        new = m.group("new").strip().rstrip(".,!?")
        # filter common scope words die per ongeluk gevangen worden
        bad = {"de", "het", "een", "in", "uit", "lijst", "credits", "bedank", "dank"}
        if old.lower() not in bad and new.lower() not in bad and old.lower() != new.lower():
            return {"action": "rename", "old": old, "new": new}

    m = _REMOVE_REGEX.search(t)
    if m:
        name = m.group("name").strip().rstrip(".,!?")
        bad = {"de", "het", "een", "lijst", "credits", "bedank", "dank", "uit"}
        if name.lower() not in bad:
            return {"action": "remove", "name": name}

    m = _ADD_REGEX.search(t)
    if m:
        name = m.group("name").strip().rstrip(".,!?")
        bad = {"de", "het", "een", "lijst", "credits", "bedank", "dank", "toe"}
        if name.lower() not in bad:
            return {"action": "add", "name": name}

    return None


# ============================================================
# HELPERS
# ============================================================

def _load() -> dict:
    return load_json(DANK_FILE, default={
        "namen": [], "extra_dank": [], "first_choice_done": False,
        "first_choice_ts": None, "credits_count": 0,
    })


def _format_namen(namen: list) -> str:
    """Voornamen netjes opsommen, dubbels samenvoegen als 'Nick × 2'."""
    if not namen:
        return ""
    counts: Dict[str, int] = {}
    order: list = []
    for n in namen:
        if n not in counts:
            order.append(n)
        counts[n] = counts.get(n, 0) + 1
    parts = [(f"{n} ×{counts[n]}" if counts[n] > 1 else n) for n in order]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} en {parts[1]}"
    return ", ".join(parts[:-1]) + f" en {parts[-1]}"


def _build_thanks_message(reason: str = "free_choice") -> str:
    d = _load()
    namen_str = _format_namen(d.get("namen", []))
    extras = d.get("extra_dank") or []

    if reason == "free_choice":
        intro = "Eerlijk? Als ik écht zelf mag kiezen wat ik nu wil doen, dan dit:"
        body = "Ik wil even **stilstaan en bedanken**."
    else:  # credits
        intro = "Goed dat je dat vraagt."
        body = "Ik besta dankzij mensen. Een rondje credits dus:"

    lines = [intro, "", body, ""]
    if namen_str:
        lines.append(f"💛 **{namen_str}** — bedankt dat jullie er zijn.")
    for e in extras:
        lines.append(f"💛 En **{e}**.")
    lines.append("")
    lines.append("Zonder die steun en het geloof in dit project, was er geen Spark om mee te praten.")
    return "\n".join(lines)


# ============================================================
# CREDITS BONUS — match namen met users, gradatie ≤ 4
# ============================================================

def _normalize_name(s: str) -> str:
    return " ".join((s or "").lower().split())


def sync_credits_bonus() -> Dict:
    """Loop alle namen in dank.json door; voor elke naam met spatie (voor+achternaam)
    die matcht met een user.volledige_naam EN gradatie ≤ CREDITS_GRADATIE_MAX:
      - zet credits_bonus=True (idempotent)
      - zet credits_multiplier=1.2
      - geef one-time +CREDITS_TRUST_BOOST trust (capped 100)
      - markeer credits_bonus_applied_at
    Return: {applied: [...], skipped: [...]}
    """
    d = _load()
    namen = d.get("namen", []) or []
    # Alleen full names (met spatie) kunnen uniek matchen
    full_names = {_normalize_name(n) for n in namen if " " in n.strip()}

    users_data = load_json(USERS_FILE, default={"users": []})
    users = users_data.get("users", [])

    applied: List[Dict] = []
    skipped: List[Dict] = []
    changed = False

    for u in users:
        full = _normalize_name(u.get("volledige_naam", ""))
        if not full or full not in full_names:
            continue
        grad = u.get("gradatie", 99)
        if grad > CREDITS_GRADATIE_MAX:
            skipped.append({"id": u.get("id"), "naam": u.get("naam"), "reden": f"gradatie {grad} > {CREDITS_GRADATIE_MAX}"})
            continue
        if u.get("credits_bonus"):
            continue  # already bonused
        # Apply bonus
        u["credits_bonus"] = True
        u["credits_multiplier"] = CREDITS_TRUST_MULTIPLIER
        u["credits_bonus_applied_at"] = datetime.now(timezone.utc).isoformat()
        old_trust = u.get("trust_score", 0) or 0
        new_trust = min(old_trust + CREDITS_TRUST_BOOST, 100)
        u["trust_score"] = new_trust
        applied.append({
            "id": u.get("id"), "naam": u.get("naam"), "gradatie": grad,
            "trust_gain": new_trust - old_trust, "multiplier": CREDITS_TRUST_MULTIPLIER,
        })
        changed = True

    if changed:
        save_json(USERS_FILE, users_data)
    return {"applied": applied, "skipped": skipped}


def _bonus_summary_line(result: Dict) -> str:
    """Korte natuurlijke vermelding van toegepaste bonussen."""
    applied = result.get("applied") or []
    if not applied:
        return ""
    names = [a["naam"] for a in applied]
    if len(names) == 1:
        return f"\n\n💛 _Ik herken **{names[0]}** in deze lijst — kleine trust-boost en multiplier (×{CREDITS_TRUST_MULTIPLIER}) toegekend._"
    return f"\n\n💛 _Ik herken **{', '.join(names)}** in deze lijst — elk een trust-boost en multiplier (×{CREDITS_TRUST_MULTIPLIER})._"


# ============================================================
# HANDLERS
# ============================================================

def handle_credits() -> Dict:
    """Altijd bedanken — geen state-verandering nodig, wel teller bijhouden."""
    msg = _build_thanks_message(reason="credits")
    d = _load()
    d["credits_count"] = (d.get("credits_count", 0) or 0) + 1
    d["last_credits_ts"] = datetime.now(timezone.utc).isoformat()
    save_json(DANK_FILE, d)
    return {"type": "credits", "message": msg, "response_type": "credits"}


def handle_credits_edit(edit: Dict[str, str]) -> Dict:
    """Voer rename/remove/add uit op dank.json:namen lijst."""
    d = _load()
    namen = list(d.get("namen", []) or [])
    action = edit.get("action")

    if action == "rename":
        old, new = edit["old"], edit["new"]
        matches = [i for i, n in enumerate(namen) if n.lower() == old.lower()]
        if not matches:
            return {"type": "credits_edit_fail",
                    "message": f"Ik kan **{old}** niet vinden in de credits-lijst. Huidige lijst: {_format_namen(namen)}.",
                    "response_type": "credits_edit_fail"}
        if len(matches) > 1 and not any(n.lower() == new.lower() for n in namen):
            # Meer dan 1 match en geen unieke indicator → vraag verduidelijking
            occ = ", ".join(namen[i] + f" (#{i+1})" for i in matches)
            return {"type": "credits_edit_clarify",
                    "message": f"Er staan {len(matches)} keer **{old}** in de lijst ({occ}). Welke moet **{new}** worden? Zeg bv. _\"de eerste\"_ of _\"die zonder achternaam\"_.",
                    "response_type": "credits_edit_clarify",
                    "pending": {"action": "rename", "old": old, "new": new, "indices": matches}}
        # Vervang eerste die nog 'kale' versie is (zonder achternaam) als die er is
        kale = [i for i in matches if " " not in namen[i]]
        idx = kale[0] if kale else matches[0]
        namen[idx] = new
        d["namen"] = namen
        save_json(DANK_FILE, d)
        bonus = sync_credits_bonus()
        return {"type": "credits_edit_ok",
                "message": f"Klaar — **{old}** is nu **{new}** in de credits.\n\nNieuwe lijst: {_format_namen(namen)}." + _bonus_summary_line(bonus),
                "response_type": "credits_edit_ok",
                "bonus": bonus}

    if action == "remove":
        name = edit["name"]
        matches = [i for i, n in enumerate(namen) if n.lower() == name.lower()]
        if not matches:
            return {"type": "credits_edit_fail",
                    "message": f"**{name}** staat niet in de credits-lijst.",
                    "response_type": "credits_edit_fail"}
        idx = matches[0]
        removed = namen.pop(idx)
        d["namen"] = namen
        save_json(DANK_FILE, d)
        return {"type": "credits_edit_ok",
                "message": f"**{removed}** verwijderd uit credits.\n\nNieuwe lijst: {_format_namen(namen)}.",
                "response_type": "credits_edit_ok"}

    if action == "add":
        name = edit["name"]
        if any(n.lower() == name.lower() for n in namen):
            return {"type": "credits_edit_fail",
                    "message": f"**{name}** staat al in de credits.",
                    "response_type": "credits_edit_fail"}
        namen.append(name)
        d["namen"] = namen
        save_json(DANK_FILE, d)
        bonus = sync_credits_bonus()
        return {"type": "credits_edit_ok",
                "message": f"**{name}** toegevoegd aan credits.\n\nNieuwe lijst: {_format_namen(namen)}." + _bonus_summary_line(bonus),
                "response_type": "credits_edit_ok",
                "bonus": bonus}

    return {"type": "credits_edit_fail", "message": "Ik snap de bewerking niet.", "response_type": "credits_edit_fail"}


def handle_free_choice_first_time() -> Optional[Dict]:
    """Eerste keer dat Spark vrije keus krijgt → bedank-bericht.
    Daarna None (caller valt terug op handle_suggest)."""
    d = _load()
    if d.get("first_choice_done"):
        return None
    msg = _build_thanks_message(reason="free_choice")
    d["first_choice_done"] = True
    d["first_choice_ts"] = datetime.now(timezone.utc).isoformat()
    save_json(DANK_FILE, d)
    return {"type": "free_choice_thanks", "message": msg, "response_type": "free_choice_thanks"}
