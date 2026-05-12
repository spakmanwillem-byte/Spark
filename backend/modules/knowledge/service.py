"""
Knowledge Service - Business logic voor kennisbank
Leest en schrijft naar knowledge_base.json
"""
from pathlib import Path
from modules.core.storage import load_json, save_json

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"


class KnowledgeService:
    def _load_entries(self):
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        return data.get("knowledge_entries", [])

    def _save_entries(self, entries):
        save_json(KNOWLEDGE_FILE, {"knowledge_entries": entries})

    def _needs_audit(self, entry):
        if entry.get("type") == "action":
            action = entry.get("action", {})
            if isinstance(action, dict) and action.get("type") == "placeholder":
                return True
        trigger_types = ["greeting", "farewell", "action"]
        if entry.get("type") in trigger_types:
            response = entry.get("response")
            if not response or not isinstance(response, dict) or not response.get("text"):
                return True
            text = response.get("text", "")
            if isinstance(text, list):
                text = text[0] if text else ""
            if isinstance(text, str) and len(text) < 10:
                return True
        return False

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
        te_herzien = sum(1 for e in entries if self._needs_audit(e))
        return {
            "total": total,
            "answered": answered,
            "unanswered": unanswered,
            "te_herzien": te_herzien,
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
        elif status_filter == "te-herzien":
            entries = [e for e in entries if self._needs_audit(e)]

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
        if sort_by == "alpha-asc":
            entries.sort(key=lambda e: (e.get("begrip") or "").lower())
        elif sort_by == "alpha-desc":
            entries.sort(key=lambda e: (e.get("begrip") or "").lower(), reverse=True)
        elif sort_by == "importance-high":
            entries.sort(key=lambda e: e.get("belangrijkheid") or 0, reverse=True)
        elif sort_by == "importance-low":
            entries.sort(key=lambda e: e.get("belangrijkheid") or 0)

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
                "status": e.get("status"),
                "is_answered": self._is_answered(e),
                "needs_audit": self._needs_audit(e),
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
                if "begrip" in data:
                    entries[i]["begrip"] = data["begrip"]
                if "lagen" in data:
                    entries[i]["lagen"] = data["lagen"]
                if "topic" in data:
                    entries[i]["topic"] = data["topic"]
                if "tags" in data:
                    entries[i]["tags"] = data["tags"]
                if "belangrijkheid" in data:
                    entries[i]["belangrijkheid"] = data["belangrijkheid"]
                if "ws5" in data:
                    entries[i]["ws5"] = data["ws5"]
                self._save_entries(entries)
                return True
        return False

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
