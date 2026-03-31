"""
Roadmap Service - Spark's Development Roadmap
Willem + Spark werken samen aan de toekomst
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from utils.data_manager import DataManager


class RoadmapService:
    ROADMAP_FILE = "system/roadmap.json"
    
    @staticmethod
    def get_roadmap() -> Dict:
        """Get complete roadmap"""
        return DataManager.load_data(RoadmapService.ROADMAP_FILE)
    
    @staticmethod
    def get_version(version: str) -> Optional[Dict]:
        """Get specific version roadmap"""
        roadmap = RoadmapService.get_roadmap()
        return roadmap.get("versions", {}).get(version)
    
    @staticmethod
    def get_current_version() -> Dict:
        """Get currently active version"""
        roadmap = RoadmapService.get_roadmap()
        for version, data in roadmap.get("versions", {}).items():
            if data.get("status") == "in_progress":
                return {"version": version, **data}
        return {}
    
    @staticmethod
    def get_summary() -> Dict:
        """Get roadmap summary for quick view"""
        roadmap = RoadmapService.get_roadmap()
        current = RoadmapService.get_current_version()
        
        if not current:
            return {"error": "No active version"}
        
        items = current.get("items", [])
        done = len([i for i in items if i["status"] == "done"])
        in_progress = len([i for i in items if i["status"] == "in_progress"])
        blocked = len([i for i in items if i["status"] == "blocked"])
        todo = len([i for i in items if i["status"] == "todo"])
        
        return {
            "current_version": current.get("version"),
            "version_name": current.get("naam"),
            "progress": current.get("progress", 0),
            "stats": {
                "done": done,
                "in_progress": in_progress,
                "blocked": blocked,
                "todo": todo,
                "total": len(items)
            },
            "next_up": RoadmapService._get_next_items(items, 3),
            "blockers": [i for i in items if i["status"] == "blocked"]
        }
    
    @staticmethod
    def _get_next_items(items: List[Dict], limit: int = 3) -> List[Dict]:
        """Get next items to work on"""
        # Priority order
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        # Get todo and in_progress items
        upcoming = [i for i in items if i["status"] in ["todo", "in_progress"]]
        
        # Sort by priority
        upcoming.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        return upcoming[:limit]
    
    @staticmethod
    def add_item(version: str, item: Dict) -> Dict:
        """Add new roadmap item"""
        roadmap = RoadmapService.get_roadmap()
        
        if version not in roadmap.get("versions", {}):
            return {"error": f"Version {version} not found"}
        
        # Generate ID
        existing_ids = [i["id"] for i in roadmap["versions"][version].get("items", [])]
        item_number = len(existing_ids) + 1
        item["id"] = f"rm_{version.replace('.', '')}_{item_number:03d}"
        
        # Add defaults
        item.setdefault("status", "todo")
        item.setdefault("progress", 0)
        item.setdefault("priority", "medium")
        item.setdefault("created_date", datetime.now().isoformat())
        
        # Add to roadmap
        roadmap["versions"][version]["items"].append(item)
        
        # Update metadata
        roadmap["metadata"]["total_items"] += 1
        roadmap["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save
        DataManager.save_data(RoadmapService.ROADMAP_FILE, roadmap)
        
        return {"success": True, "item": item}
    
    @staticmethod
    def update_item(item_id: str, updates: Dict) -> Dict:
        """Update roadmap item"""
        roadmap = RoadmapService.get_roadmap()
        
        # Find item
        for version_data in roadmap.get("versions", {}).values():
            for item in version_data.get("items", []):
                if item["id"] == item_id:
                    # Update fields
                    for key, value in updates.items():
                        item[key] = value
                    
                    # Update metadata
                    if updates.get("status") == "done" and "completed_date" not in item:
                        item["completed_date"] = datetime.now().isoformat()
                    
                    roadmap["metadata"]["last_updated"] = datetime.now().isoformat()
                    
                    # Recalculate stats
                    RoadmapService._recalculate_stats(roadmap)
                    
                    # Save
                    DataManager.save_data(RoadmapService.ROADMAP_FILE, roadmap)
                    
                    return {"success": True, "item": item}
        
        return {"error": f"Item {item_id} not found"}
    
    @staticmethod
    def _recalculate_stats(roadmap: Dict):
        """Recalculate metadata stats"""
        total = 0
        completed = 0
        in_progress = 0
        blocked = 0
        todo = 0
        
        for version_data in roadmap.get("versions", {}).values():
            for item in version_data.get("items", []):
                total += 1
                status = item.get("status")
                if status == "done":
                    completed += 1
                elif status == "in_progress":
                    in_progress += 1
                elif status == "blocked":
                    blocked += 1
                elif status == "todo":
                    todo += 1
        
        roadmap["metadata"].update({
            "total_items": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "todo": todo
        })
    
    @staticmethod
    def get_chat_summary() -> str:
        """Get roadmap summary for chat"""
        summary = RoadmapService.get_summary()
        
        if "error" in summary:
            return "Geen actieve roadmap gevonden."
        
        stats = summary["stats"]
        blockers = summary["blockers"]
        next_up = summary["next_up"]
        
        response = f"🗺️ **{summary['version_name']}** ({summary['current_version']})\n\n"
        response += f"📊 **Progress:** {summary['progress']}%\n"
        response += f"├─ ✅ Done: {stats['done']}\n"
        response += f"├─ 🔄 In Progress: {stats['in_progress']}\n"
        
        if stats['blocked'] > 0:
            response += f"├─ 🔒 Blocked: {stats['blocked']}\n"
        
        response += f"└─ ⏳ Todo: {stats['todo']}\n\n"
        
        if blockers:
            response += "🔴 **Blockers:**\n"
            for blocker in blockers:
                response += f"• {blocker['titel']}\n"
                if blocker.get("blocked_reason"):
                    response += f"  └─ {blocker['blocked_reason']}\n"
            response += "\n"
        
        if next_up:
            response += "🎯 **Next Up:**\n"
            for item in next_up:
                icon = "🔄" if item["status"] == "in_progress" else "⏳"
                response += f"• {icon} {item['titel']} ({item['priority']})\n"
        
        return response
