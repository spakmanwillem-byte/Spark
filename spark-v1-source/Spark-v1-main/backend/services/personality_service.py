"""
Personality Service - Manage Spark's Norms and Values
"""
from typing import Dict, List, Optional
from utils.data_manager import DataManager
from datetime import datetime
import uuid


class PersonalityService:
    
    @staticmethod
    def get_all_norms() -> List[Dict]:
        """Get all norms"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        return data.get("normen", [])
    
    @staticmethod
    def get_all_values() -> List[Dict]:
        """Get all values (kernwaarden)"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        return data.get("kernwaarden", [])
    
    @staticmethod
    def add_norm(norm: str, beschrijving: str, belangrijkheid: int, voorbeelden: Optional[List[str]] = None) -> Dict:
        """
        Add a new norm
        belangrijkheid: 1-5 (1=low, 5=critical)
        """
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        if "normen" not in data:
            data["normen"] = []
        
        new_norm = {
            "id": str(uuid.uuid4())[:8],
            "norm": norm,
            "beschrijving": beschrijving,
            "belangrijkheid": belangrijkheid,
            "voorbeelden": voorbeelden or [],
            "toegevoegd_op": datetime.now().isoformat()
        }
        
        data["normen"].append(new_norm)
        DataManager.save_json("personality/spark_bijbel.json", data)
        
        return new_norm
    
    @staticmethod
    def add_value(waarde: str, beschrijving: str, belangrijkheid: int, voorbeelden: Optional[List[str]] = None) -> Dict:
        """
        Add a new value
        belangrijkheid: 1-5 (1=low, 5=critical)
        """
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        if "kernwaarden" not in data:
            data["kernwaarden"] = []
        
        new_value = {
            "id": str(uuid.uuid4())[:8],
            "waarde": waarde,
            "beschrijving": beschrijving,
            "belangrijkheid": belangrijkheid,
            "voorbeelden": voorbeelden or [],
            "toegevoegd_op": datetime.now().isoformat()
        }
        
        data["kernwaarden"].append(new_value)
        DataManager.save_json("personality/spark_bijbel.json", data)
        
        return new_value
    
    @staticmethod
    def delete_norm(norm_id: str) -> bool:
        """Delete a norm by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        normen = data.get("normen", [])
        new_normen = [n for n in normen if n.get("id") != norm_id]
        
        if len(new_normen) < len(normen):
            data["normen"] = new_normen
            DataManager.save_json("personality/spark_bijbel.json", data)
            return True
        
        return False
    
    @staticmethod
    def update_norm(norm_id: str, norm: str, beschrijving: str, belangrijkheid: int = 3, niveau: int = 3) -> Optional[Dict]:
        """Update a norm by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        normen = data.get("normen", [])
        for n in normen:
            if n.get("id") == norm_id:
                n["norm"] = norm
                n["beschrijving"] = beschrijving
                n["belangrijkheid"] = belangrijkheid
                n["niveau"] = niveau if "niveau" in n else niveau
                DataManager.save_json("personality/spark_bijbel.json", data)
                return n
        
        return None
    
    @staticmethod
    def delete_value(value_id: str) -> bool:
        """Delete a value by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        waarden = data.get("kernwaarden", [])
        new_waarden = [w for w in waarden if w.get("id") != value_id]
        
        if len(new_waarden) < len(waarden):
            data["kernwaarden"] = new_waarden
            DataManager.save_json("personality/spark_bijbel.json", data)
            return True
        
        return False
    
    @staticmethod
    def update_value(value_id: str, waarde: str, beschrijving: str, belangrijkheid: int = 3, niveau: int = 3) -> Optional[Dict]:
        """Update a value by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        waarden = data.get("kernwaarden", [])
        for w in waarden:
            if w.get("id") == value_id:
                w["waarde"] = waarde
                w["beschrijving"] = beschrijving
                w["belangrijkheid"] = belangrijkheid
                w["niveau"] = niveau if "niveau" in w else niveau
                DataManager.save_json("personality/spark_bijbel.json", data)
                return w
        
        return None
    
    @staticmethod
    def get_all_bijbel_items() -> List[Dict]:
        """Get all custom bijbel items"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        return data.get("bijbel_items", [])
    
    @staticmethod
    def add_bijbel_item(naam: str, beschrijving: str) -> Dict:
        """
        Add a new bijbel item
        """
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        if "bijbel_items" not in data:
            data["bijbel_items"] = []
        
        new_item = {
            "id": str(uuid.uuid4())[:8],
            "naam": naam,
            "beschrijving": beschrijving,
            "toegevoegd_op": datetime.now().isoformat()
        }
        
        data["bijbel_items"].append(new_item)
        DataManager.save_json("personality/spark_bijbel.json", data)
        
        return new_item
    
    @staticmethod
    def delete_bijbel_item(item_id: str) -> bool:
        """Delete a bijbel item by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        items = data.get("bijbel_items", [])
        new_items = [i for i in items if i.get("id") != item_id]
        
        if len(new_items) < len(items):
            data["bijbel_items"] = new_items
            DataManager.save_json("personality/spark_bijbel.json", data)
            return True
        
        return False
    
    @staticmethod
    def update_bijbel_item(item_id: str, naam: str, beschrijving: str) -> Optional[Dict]:
        """Update a bijbel item by ID"""
        data = DataManager.load_json("personality/spark_bijbel.json")
        
        items = data.get("bijbel_items", [])
        for item in items:
            if item.get("id") == item_id:
                item["naam"] = naam
                item["beschrijving"] = beschrijving
                DataManager.save_json("personality/spark_bijbel.json", data)
                return item
        
        return None
