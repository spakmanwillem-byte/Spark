"""
Knowledge Service - Business logic voor kennisbank
Leest en schrijft naar knowledge_base.json
"""
from datetime import datetime, timezone
from pathlib import Path
from modules.core.storage import load_json, save_json

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
KBV2_LADES = ["doen", "weten", "voelen", "spreken"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class KnowledgeService:
    def _load_entries(self):
        """v6_v2_first_001 — V2 lades + inbox als platte lijst (V1-vorm)."""
        out = []
        for fname in [f"knowledge_v2_{l}" for l in KBV2_LADES] + ["knowledge_inbox"]:
            d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
            out.extend(d.get("kaarten", []) or [])
        return out

    def _save_entries(self, entries):
        """v6_v2_first_001 — schrijf per V2-lade-bestand. snap-* (V1) overslaan."""
        by_lade = {l: [] for l in KBV2_LADES + ["inbox"]}
        for e in entries:
            eid = e.get("id") or ""
            if eid.startswith("snap-"):
                continue  # V1 = archief
            lade = (e.get("lade") or "").lower().strip()
            if lade not in KBV2_LADES:
                lade = "inbox"
            by_lade[lade].append(e)
        for lade, items in by_lade.items():
            fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
            save_json(KBV2_DIR / f"{fname}.json", {"kaarten": items})

    def _is_answered(self, entry):
        lagen = entry.get("lagen", {})
        if not isinstance(lagen, dict):
            return False
        laag1 = lagen.get("laag1", "")
        return bool(laag1 and str(laag1).strip())

    def get_stats(self):
        entries = self._load_entries()
        total = len(entries)
        answered = sum(1 for e in entries if self._is_answered(e))
        unanswered = total - answered
        # v4_019: Review-pending = nog nooit gereviewd (reviewed_at == null) — alle kaarten
        review_pending = sum(
            1 for e in entries
            if not ((e.get("metadata") or {}).get("reviewed_at"))
        )
        return {
            "total": total,
            "answered": answered,
            "unanswered": unanswered,
            "review_pending": review_pending,
        }

    def get_all_tags(self):
        entries = self._load_entries()
        tags_set = set()
        for e in entries:
            tags = e.get("tags", [])
            if isinstance(tags, list):
                for t in tags:
                    if t:
                        tags_set.add(t)
        return sorted(tags_set)

    def get_all(self, search=None, status_filter="all", sort_by="recent", importance="all", page=1, per_page=50):
        entries = self._load_entries()

        # Status filter
        if status_filter == "unanswered":
            entries = [e for e in entries if not self._is_answered(e)]
        elif status_filter == "answered":
            entries = [e for e in entries if self._is_answered(e)]
        elif status_filter == "review":
            # v4_019: Review-mode = nog nooit gereviewd of langst geleden gereviewd
            # Sortering wordt verderop forced toegepast
            sort_by = "review-priority"

        # Search
        if search and search.strip():
            q = search.lower()
            filtered = []
            for e in entries:
                begrip = (e.get("begrip") or "").lower()
                lagen = e.get("lagen", {}) or {}
                laag1 = (lagen.get("laag1") or "").lower() if isinstance(lagen, dict) else ""
                laag2 = (lagen.get("laag2") or "").lower() if isinstance(lagen, dict) else ""
                topic = (e.get("topic") or "").lower()
                tags = " ".join(e.get("tags", []) or []).lower()
                if q in begrip or q in laag1 or q in laag2 or q in topic or q in tags:
                    filtered.append(e)
            entries = filtered

        # Importance filter
        if importance == "low":
            entries = [e for e in entries if 1 <= (e.get("belangrijkheid") or 0) <= 5]
        elif importance == "high":
            entries = [e for e in entries if (e.get("belangrijkheid") or 0) >= 6]

        # Sort
        def _ts(e, key):
            m = e.get("metadata") or {}
            return m.get(key) or e.get("detected_at") or ""

        if sort_by == "alpha-asc":
            entries.sort(key=lambda e: (e.get("begrip") or "").lower())
        elif sort_by == "alpha-desc":
            entries.sort(key=lambda e: (e.get("begrip") or "").lower(), reverse=True)
        elif sort_by == "importance-high":
            entries.sort(key=lambda e: e.get("belangrijkheid") or 0, reverse=True)
        elif sort_by == "importance-low":
            entries.sort(key=lambda e: e.get("belangrijkheid") or 0)
        elif sort_by == "recent":
            # v6_kb_sort_recent — nieuwste aangemaakt eerst (fallback: detected_at)
            entries.sort(key=lambda e: _ts(e, "created_at"), reverse=True)
        elif sort_by == "updated":
            # Recent bewerkt eerst
            entries.sort(key=lambda e: _ts(e, "updated_at"), reverse=True)
        elif sort_by == "review-priority":
            # Nooit gereviewd eerst (reviewed_at == None), daarna oudste reviewed_at,
            # binnen gelijke groep: oudste created_at eerst (oudste kaarten dus eerst).
            def review_key(e):
                m = e.get("metadata") or {}
                reviewed = m.get("reviewed_at")
                created = m.get("created_at") or e.get("detected_at") or ""
                # None reviewed → sorteer-key '' zodat ze bovenaan staan
                return (reviewed or "", created)
            entries.sort(key=review_key)

        total = len(entries)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = entries[start:end]

        # Strip heavy fields for list view
        light_entries = []
        for e in paginated:
            lagen = e.get("lagen", {}) or {}
            laag1 = ""
            if isinstance(lagen, dict):
                laag1 = lagen.get("laag1") or ""
            light_entries.append({
                "id": e.get("id"),
                "begrip": e.get("begrip"),
                "laag1_preview": laag1[:120] if laag1 else "",
                "topic": e.get("topic"),
                "tags": e.get("tags", []),
                "belangrijkheid": e.get("belangrijkheid", 0),
                "type": e.get("type"),
                "kaart_type": e.get("kaart_type") or "concept",
                "status": e.get("status"),
                "is_answered": self._is_answered(e),
                "reviewed_at": (e.get("metadata") or {}).get("reviewed_at"),
                "review_count": (e.get("metadata") or {}).get("review_count") or 0,
                "created_at": (e.get("metadata") or {}).get("created_at") or e.get("detected_at"),
                "updated_at": (e.get("metadata") or {}).get("updated_at"),
            })

        return {
            "entries": light_entries,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-total // per_page)),
        }

    def get_by_id(self, entry_id):
        entries = self._load_entries()
        for e in entries:
            if e.get("id") == entry_id:
                return e
        return None

    def update_entry(self, entry_id, data):
        entries = self._load_entries()
        for i, e in enumerate(entries):
            if e.get("id") == entry_id:
                for fld in ("begrip", "lagen", "topic", "tags", "belangrijkheid", "ws5", "kaart_type"):
                    if fld in data:
                        entries[i][fld] = data[fld]
                # Stamp updated_at
                m = entries[i].setdefault("metadata", {})
                m["updated_at"] = _now_iso()
                if "created_at" not in m:
                    m["created_at"] = e.get("detected_at") or m["updated_at"]
                self._save_entries(entries)
                return True
        return False

    def mark_reviewed(self, entry_id):
        """v4_019: registreer een review-actie zonder content te wijzigen."""
        entries = self._load_entries()
        for i, e in enumerate(entries):
            if e.get("id") == entry_id:
                m = entries[i].setdefault("metadata", {})
                m["reviewed_at"] = _now_iso()
                m["review_count"] = int(m.get("review_count") or 0) + 1
                self._save_entries(entries)
                return entries[i]
        return None

    def get_next_review(self, after_id=None):
        """v4_019: pak volgende kaart om te reviewen (nooit-reviewed eerst,
        daarna langst-niet-reviewed). Indien after_id meegegeven: sla die over."""
        entries = self._load_entries()
        def key(e):
            m = e.get("metadata") or {}
            reviewed = m.get("reviewed_at")
            created = m.get("created_at") or e.get("detected_at") or ""
            return (reviewed or "", created)
        entries.sort(key=key)
        for e in entries:
            if after_id and e.get("id") == after_id:
                continue
            return e
        return None

    def delete_entry(self, entry_id):
        entries = self._load_entries()
        new_entries = [e for e in entries if e.get("id") != entry_id]
        if len(new_entries) == len(entries):
            return False
        self._save_entries(new_entries)
        # Graph auto-sync: verwijder node + edges
        try:
            from modules.graph.sync_service import remove_node
            remove_node(entry_id)
        except Exception as ex:
            print(f"[graph-sync] delete remove_node failed: {ex}")
        return True

    def exists_begrip(self, begrip):
        """v4_kb_create_001: exact-match check (case-insensitive, whitespace-trimmed).
        Eén letter anders telt als ander concept."""
        if not begrip:
            return None
        q = str(begrip).strip().lower()
        if not q:
            return None
        for e in self._load_entries():
            if str(e.get("begrip", "")).strip().lower() == q:
                return {"id": e.get("id"), "begrip": e.get("begrip"), "topic": e.get("topic", "")}
        return None

    def create_entry(self, data):
        """v4_kb_create_001: maak een nieuwe knowledge kaart aan.
        Faalt met (None, 'duplicate') als begrip al exact bestaat.
        Velden uit data: begrip (verplicht), topic, tags, lagen, ws5, belangrijkheid, kaart_type.
        """
        import uuid
        begrip = (data.get("begrip") or "").strip()
        if not begrip:
            return None, "begrip_required"
        dup = self.exists_begrip(begrip)
        if dup:
            return None, "duplicate"
        now = _now_iso()
        entry = {
            "id": f"kb-{uuid.uuid4().hex[:8]}",
            "begrip": begrip,
            "topic": (data.get("topic") or "").strip(),
            "tags": data.get("tags") or [],
            "lagen": data.get("lagen") or {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": data.get("ws5") or {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "belangrijkheid": int(data.get("belangrijkheid") or 3),
            "kaart_type": data.get("kaart_type") or "concept",
            "is_sentence": False,
            "bron": "manual",
            "detected_at": now,
            "metadata": {
                "created_at": now,
                "updated_at": now,
                "reviewed_at": None,
                "review_count": 0,
            },
        }
        entries = self._load_entries()
        entries.append(entry)
        self._save_entries(entries)
        # Graph auto-sync
        try:
            from modules.graph.sync_service import upsert_node_from_entry
            upsert_node_from_entry(entry)
        except Exception as ex:
            print(f"[graph-sync] create upsert failed: {ex}")
        return entry, None
