"""
Card Claim Service (v4_009)

Fair-share claim systeem voor het Bijdrage-portaal.
- 1 actieve claim per user
- TTL standaard 24u; verloopt automatisch
- Geen botsing: 2 users krijgen automatisch verschillende kaarten
- Fair-share: als pool leeg, kan oudste claim worden verbeurd
"""
import time
import uuid
import random
from pathlib import Path
from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CLAIMS_FILE = DATA_DIR / "contributions_claims.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"

CLAIM_TTL_SECONDS = 24 * 3600  # 24 uur
FIELDS = ["wat", "wanneer", "waar", "wie", "waarom", "hoe"]


def _load_claims():
    return load_json(CLAIMS_FILE, default={"claims": []})


def _save_claims(data):
    save_json(CLAIMS_FILE, data)


def _now():
    return int(time.time())


def _prune_expired(data):
    """Verwijder verlopen claims."""
    cutoff = _now() - CLAIM_TTL_SECONDS
    before = len(data.get("claims", []))
    data["claims"] = [c for c in data.get("claims", []) if c.get("claimed_at", 0) >= cutoff]
    return before - len(data["claims"])


def _list_eligible_card_ids():
    """Kaarten die geclaimd kunnen worden:
    - Tag 'auto-generated' aanwezig
    - Minstens 1 leeg ws5-veld
    - Niet 'pending-review' (al ingediend)
    """
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    eligible = []
    for e in data.get("knowledge_entries", []):
        tags = e.get("tags") or []
        if "auto-generated" not in tags:
            continue
        if "pending-review" in tags:
            continue
        ws5 = e.get("ws5") or {}
        empty = any(not (ws5.get(f) or "").strip() for f in FIELDS)
        if not empty:
            continue
        eligible.append(e["id"])
    return eligible


def _current_claim_for(user_id, data=None):
    if data is None:
        data = _load_claims()
    for c in data.get("claims", []):
        if c.get("user_id") == user_id:
            return c
    return None


def get_or_create_claim(user_id: str) -> dict:
    """
    Pak de huidige claim van een user, of geef een nieuwe.
    Returns claim-dict {id, user_id, card_id, claimed_at} of None als geen kaarten beschikbaar.
    """
    if not user_id:
        return None
    data = _load_claims()
    _prune_expired(data)

    # Bestaande claim?
    existing = _current_claim_for(user_id, data)
    if existing:
        # Verify kaart bestaat nog en is nog eligible
        eligible_ids = set(_list_eligible_card_ids())
        if existing["card_id"] in eligible_ids:
            _save_claims(data)
            return existing
        # Kaart is in tussentijd ingevuld/verwijderd → claim verwijderen
        data["claims"] = [c for c in data["claims"] if c.get("user_id") != user_id]

    # Nieuwe claim — pak een willekeurige beschikbare kaart die niemand heeft
    claimed_ids = {c["card_id"] for c in data["claims"]}
    eligible_ids = _list_eligible_card_ids()
    available = [cid for cid in eligible_ids if cid not in claimed_ids]
    if not available:
        # Pool leeg → oudste claim verbeuren (fair-share, zoals user beschreef)
        if data["claims"]:
            oldest = min(data["claims"], key=lambda c: c.get("claimed_at", 0))
            data["claims"].remove(oldest)
            # Nu zou diens kaart vrij moeten zijn
            claimed_ids.discard(oldest["card_id"])
            available = [cid for cid in eligible_ids if cid not in claimed_ids]
    if not available:
        _save_claims(data)
        return None

    new_claim = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "card_id": random.choice(available),
        "claimed_at": _now(),
    }
    data["claims"].append(new_claim)
    _save_claims(data)
    return new_claim


def release_claim(user_id: str, reason: str = "released") -> bool:
    """Geef claim vrij (na voltooien, overslaan of intrekken)."""
    data = _load_claims()
    before = len(data.get("claims", []))
    data["claims"] = [c for c in data["claims"] if c.get("user_id") != user_id]
    if len(data["claims"]) != before:
        _save_claims(data)
        return True
    return False


def get_card(card_id: str) -> dict:
    """Haal kaart op."""
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    for e in data.get("knowledge_entries", []):
        if e.get("id") == card_id:
            return e
    return None


def save_partial(card_id: str, field_updates: dict) -> dict:
    """Sla partial ws5-updates op (alleen niet-lege strings). Return updated card."""
    if not field_updates:
        return get_card(card_id)
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    entries = data.get("knowledge_entries", [])
    target = None
    for e in entries:
        if e.get("id") == card_id:
            target = e
            break
    if not target:
        return None
    ws5 = target.get("ws5") or {f: "" for f in FIELDS}
    for f, v in field_updates.items():
        if f in FIELDS and isinstance(v, str):
            ws5[f] = v.strip()[:300]
    target["ws5"] = ws5
    save_json(KNOWLEDGE_FILE, {"knowledge_entries": entries})
    return target


def submit_for_review(user_id: str, card_id: str, ws5_data: dict) -> dict:
    """
    Markeer kaart als ingediend voor admin review.
    - Sla ws5 op
    - Tag 'pending-review' + tag user-{user_id}-bijdrage
    - Release claim
    - Return: {success, fields_filled, percentage, eligible_for_xp}
    """
    target = save_partial(card_id, ws5_data or {})
    if not target:
        return {"success": False, "error": "card_not_found"}
    ws5 = target.get("ws5") or {}
    filled_count = sum(1 for f in FIELDS if (ws5.get(f) or "").strip())
    percentage = round(filled_count / len(FIELDS) * 100)

    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    for e in data["knowledge_entries"]:
        if e.get("id") == card_id:
            tags = e.get("tags") or []
            if "pending-review" not in tags:
                tags.append("pending-review")
            contrib_tag = f"bijdrage-{user_id}"
            if contrib_tag not in tags:
                tags.append(contrib_tag)
            e["tags"] = tags
            # Houd bij wie de bijdrage deed + % gevuld
            meta = e.get("metadata") or {}
            meta["contribution"] = {
                "user_id": user_id,
                "submitted_at": _now(),
                "fields_filled": filled_count,
                "percentage": percentage,
            }
            e["metadata"] = meta
            break
    save_json(KNOWLEDGE_FILE, data)
    release_claim(user_id, reason="submitted")
    return {
        "success": True,
        "fields_filled": filled_count,
        "percentage": percentage,
        "eligible_for_xp": percentage >= 75,
    }


def list_pending_for_admin() -> list:
    """Lijst van kaarten die wachten op admin-goedkeuring."""
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    out = []
    for e in data.get("knowledge_entries", []):
        tags = e.get("tags") or []
        if "pending-review" in tags:
            meta = (e.get("metadata") or {}).get("contribution") or {}
            out.append({
                "id": e["id"],
                "begrip": e["begrip"],
                "ws5": e.get("ws5"),
                "tags": tags,
                "contributor_user_id": meta.get("user_id"),
                "fields_filled": meta.get("fields_filled"),
                "percentage": meta.get("percentage"),
                "submitted_at": meta.get("submitted_at"),
            })
    out.sort(key=lambda x: x.get("submitted_at") or 0, reverse=True)
    return out


def approve(card_id: str, admin_id: str) -> dict:
    """Keur kaart goed: verwijder pending-review en auto-generated tags. Return contribution info."""
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    for e in data["knowledge_entries"]:
        if e.get("id") == card_id:
            tags = [t for t in (e.get("tags") or []) if t not in ("pending-review", "auto-generated", "scan-discovered")]
            e["tags"] = tags
            e["status"] = "approved"
            meta = e.get("metadata") or {}
            contrib = meta.get("contribution") or {}
            contrib["approved_at"] = _now()
            contrib["approved_by"] = admin_id
            meta["contribution"] = contrib
            e["metadata"] = meta
            save_json(KNOWLEDGE_FILE, data)
            return {
                "success": True,
                "contributor_user_id": contrib.get("user_id"),
                "percentage": contrib.get("percentage", 0),
                "eligible_for_xp": (contrib.get("percentage", 0) >= 75),
            }
    return {"success": False, "error": "card_not_found"}


def reject(card_id: str, admin_id: str, reason: str = "") -> dict:
    """Wijs kaart af: verwijder pending-review tag, kaart blijft in pool."""
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    for e in data["knowledge_entries"]:
        if e.get("id") == card_id:
            tags = [t for t in (e.get("tags") or []) if t != "pending-review"]
            e["tags"] = tags
            meta = e.get("metadata") or {}
            contrib = meta.get("contribution") or {}
            contrib["rejected_at"] = _now()
            contrib["rejected_by"] = admin_id
            contrib["reject_reason"] = reason
            meta["contribution"] = contrib
            e["metadata"] = meta
            save_json(KNOWLEDGE_FILE, data)
            return {"success": True}
    return {"success": False, "error": "card_not_found"}


def user_stats(user_id: str) -> dict:
    """Stats voor user dashboard."""
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    submitted = 0
    pending = 0
    approved = 0
    rejected = 0
    for e in data.get("knowledge_entries", []):
        meta = (e.get("metadata") or {}).get("contribution") or {}
        if meta.get("user_id") != user_id:
            continue
        submitted += 1
        if "pending-review" in (e.get("tags") or []):
            pending += 1
        elif meta.get("approved_at"):
            approved += 1
        elif meta.get("rejected_at"):
            rejected += 1
    active_claim = _current_claim_for(user_id)
    return {
        "submitted": submitted,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "active_claim": active_claim,
    }
