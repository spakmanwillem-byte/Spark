"""
Potjes System Routes - Bookkeeping layer voor fund tracking
Bitvavo = externe wallet (totaal geld)
Spark = potjes administratie (interne logica)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timezone
from pathlib import Path

router = APIRouter()

POTJES_FILE = Path("/app/backend/data/financial/user_potjes.json")


def load_potjes_data():
    """Load potjes data"""
    if not POTJES_FILE.exists():
        # Initialize with empty data
        data = {
            "description": "Potjes systeem - Tracking van totaal fund vs gebruikt/beschikbaar",
            "users": {}
        }
        POTJES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(POTJES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return data
    
    with open(POTJES_FILE, 'r') as f:
        return json.load(f)


def save_potjes_data(data):
    """Save potjes data"""
    with open(POTJES_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@router.get("/status/{user_id}")
async def get_potjes_status(user_id: str):
    """
    Get potjes status voor user
    
    Returns:
        - Totaal fund (extern op Bitvavo)
        - Gebruikt (intern gelogd)
        - Beschikbaar (calculatie)
        - Per potje status
    """
    data = load_potjes_data()
    
    if user_id not in data.get("users", {}):
        raise HTTPException(
            status_code=404,
            detail=f"Geen potjes systeem gevonden voor {user_id}"
        )
    
    user_data = data["users"][user_id]
    
    return {
        "success": True,
        "user_id": user_id,
        "potjes_config": user_data["potjes_config"],
        "status": user_data["status"],
        "potjes": user_data["potjes"],
        "summary": {
            "total_fund_eur": user_data["potjes_config"]["total_fund_eur"],
            "total_potjes": user_data["potjes_config"]["total_potjes"],
            "potje_value_eur": user_data["potjes_config"]["potje_value_eur"],
            "used_count": user_data["status"]["used_count"],
            "available_count": user_data["status"]["available_count"],
            "used_eur": user_data["status"]["used_eur"],
            "available_eur": user_data["status"]["available_eur"],
            "external_location": user_data["potjes_config"]["external_location"]
        }
    }


@router.get("/available/{user_id}")
async def get_available_potjes(user_id: str):
    """
    Get lijst van beschikbare potjes
    """
    data = load_potjes_data()
    
    if user_id not in data.get("users", {}):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = data["users"][user_id]
    available = [p for p in user_data["potjes"] if p["status"] == "available"]
    
    return {
        "success": True,
        "user_id": user_id,
        "available_count": len(available),
        "available_potjes": available,
        "available_eur": len(available) * user_data["potjes_config"]["potje_value_eur"]
    }


@router.get("/used/{user_id}")
async def get_used_potjes(user_id: str):
    """
    Get lijst van gebruikte potjes
    """
    data = load_potjes_data()
    
    if user_id not in data.get("users", {}):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = data["users"][user_id]
    used = [p for p in user_data["potjes"] if p["status"] == "used"]
    
    return {
        "success": True,
        "user_id": user_id,
        "used_count": len(used),
        "used_potjes": used,
        "used_eur": user_data["status"]["used_eur"]
    }


class PotjeUseRequest(BaseModel):
    user_id: str
    run_id: str
    trade_value_eur: float
    note: Optional[str] = None


@router.post("/use")
async def use_potje(request: PotjeUseRequest):
    """
    Mark een potje als gebruikt
    Link aan een trade run_id
    """
    data = load_potjes_data()
    
    if request.user_id not in data.get("users", {}):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = data["users"][request.user_id]
    
    # Find first available potje
    available_potje = None
    for potje in user_data["potjes"]:
        if potje["status"] == "available":
            available_potje = potje
            break
    
    if not available_potje:
        raise HTTPException(status_code=400, detail="Geen potjes meer beschikbaar")
    
    # Mark as used
    available_potje["status"] = "used"
    available_potje["run_id"] = request.run_id
    available_potje["date_used"] = datetime.now(timezone.utc).isoformat()
    available_potje["trade_value_eur"] = request.trade_value_eur
    if request.note:
        available_potje["note"] = request.note
    
    # Update counts
    user_data["status"]["used_count"] += 1
    user_data["status"]["available_count"] -= 1
    user_data["status"]["used_eur"] += user_data["potjes_config"]["potje_value_eur"]
    user_data["status"]["available_eur"] -= user_data["potjes_config"]["potje_value_eur"]
    user_data["status"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # Add to history
    user_data["history"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "potje_used",
        "potje_id": available_potje["potje_id"],
        "run_id": request.run_id,
        "trade_value_eur": request.trade_value_eur
    })
    
    # Save
    save_potjes_data(data)
    
    return {
        "success": True,
        "message": f"Potje {available_potje['potje_id']} gemarkeerd als gebruikt",
        "potje": available_potje,
        "remaining": {
            "available_count": user_data["status"]["available_count"],
            "available_eur": user_data["status"]["available_eur"]
        }
    }


@router.get("/history/{user_id}")
async def get_potjes_history(user_id: str):
    """
    Get volledige potjes geschiedenis
    """
    data = load_potjes_data()
    
    if user_id not in data.get("users", {}):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = data["users"][user_id]
    
    return {
        "success": True,
        "user_id": user_id,
        "history": user_data.get("history", [])
    }


class PotjesInitRequest(BaseModel):
    user_id: str
    total_fund_eur: float
    potje_value_eur: float
    external_location: str = "bitvavo"
    note: Optional[str] = None


@router.post("/initialize")
async def initialize_potjes(request: PotjesInitRequest):
    """
    Initialize potjes systeem voor een user
    
    Berekent automatisch aantal potjes op basis van:
    total_fund_eur / potje_value_eur
    """
    data = load_potjes_data()
    
    # Calculate total potjes
    total_potjes = int(request.total_fund_eur / request.potje_value_eur)
    
    # Create potjes
    potjes = []
    for i in range(1, total_potjes + 1):
        potjes.append({
            "potje_id": i,
            "status": "available",
            "reserved_for": None
        })
    
    # Create user data
    user_data = {
        "potjes_config": {
            "total_fund_eur": request.total_fund_eur,
            "external_location": request.external_location,
            "potje_value_eur": request.potje_value_eur,
            "total_potjes": total_potjes,
            "note": request.note or f"Fund staat op {request.external_location} - Spark tracked alleen gebruik"
        },
        "status": {
            "used_count": 0,
            "available_count": total_potjes,
            "used_eur": 0.0,
            "available_eur": request.total_fund_eur,
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        "potjes": potjes,
        "history": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "initial_setup",
                "description": f"Potjes systeem opgezet - {total_potjes} potjes van €{request.potje_value_eur}"
            }
        ]
    }
    
    data["users"][request.user_id] = user_data
    save_potjes_data(data)
    
    return {
        "success": True,
        "message": f"Potjes systeem geïnitialiseerd voor {request.user_id}",
        "config": user_data["potjes_config"],
        "status": user_data["status"]
    }
