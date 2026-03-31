"""
Bank Configuration Routes
Admin manages bank details for deposits
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime, timezone

router = APIRouter()

BANK_CONFIG_FILE = "/app/backend/data/system/bank_config.json"


class BankConfig(BaseModel):
    iban: str
    account_holder: str = "Willem Spakman"
    bank_name: Optional[str] = None
    bic_swift: Optional[str] = None
    reference_prefix: str = "SPARK"


class UpdateBankConfigRequest(BaseModel):
    config: BankConfig
    user_id: str  # Admin user making the change


def load_bank_config():
    """Load bank configuration"""
    if os.path.exists(BANK_CONFIG_FILE):
        with open(BANK_CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    # Default config
    return {
        "bank_details": {
            "iban": "",
            "account_holder": "Willem Spakman",
            "bank_name": "",
            "bic_swift": "",
            "reference_prefix": "SPARK"
        },
        "payment_info": {
            "enabled": False,
            "manual_approval": True,
            "auto_credit_after_hours": 24
        },
        "updated_at": None,
        "updated_by": None
    }


def save_bank_config(data):
    """Save bank configuration"""
    os.makedirs(os.path.dirname(BANK_CONFIG_FILE), exist_ok=True)
    with open(BANK_CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@router.get("/bank/config")
async def get_bank_config():
    """Get bank configuration (public info only)"""
    try:
        config = load_bank_config()
        bank_details = config.get("bank_details", {})
        
        # Return safe public info
        return {
            "success": True,
            "config": {
                "iban": bank_details.get("iban", ""),
                "account_holder": bank_details.get("account_holder", ""),
                "bank_name": bank_details.get("bank_name", ""),
                "reference_prefix": bank_details.get("reference_prefix", "SPARK"),
                "is_configured": bool(bank_details.get("iban"))
            },
            "payment_enabled": config.get("payment_info", {}).get("enabled", False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bank/config")
async def update_bank_config(request: UpdateBankConfigRequest):
    """Update bank configuration (admin only)"""
    try:
        # TODO: Add admin check for user_id
        
        config = load_bank_config()
        
        # Update bank details
        config["bank_details"] = {
            "iban": request.config.iban,
            "account_holder": request.config.account_holder,
            "bank_name": request.config.bank_name or "",
            "bic_swift": request.config.bic_swift or "",
            "reference_prefix": request.config.reference_prefix
        }
        
        # Enable payments if IBAN is set
        config["payment_info"]["enabled"] = bool(request.config.iban)
        config["updated_at"] = datetime.now(timezone.utc).isoformat()
        config["updated_by"] = request.user_id
        
        save_bank_config(config)
        
        return {
            "success": True,
            "message": "Bank configuratie opgeslagen",
            "config": config["bank_details"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bank/deposit-info")
async def get_deposit_info(user_id: str):
    """Get deposit information for a user"""
    try:
        config = load_bank_config()
        bank_details = config.get("bank_details", {})
        
        if not bank_details.get("iban"):
            raise HTTPException(
                status_code=400, 
                detail="Bank details niet geconfigureerd. Neem contact op met admin."
            )
        
        # Generate unique reference
        reference = f"{bank_details.get('reference_prefix', 'SPARK')}-{user_id.upper()}"
        
        return {
            "success": True,
            "deposit_info": {
                "iban": bank_details.get("iban"),
                "account_holder": bank_details.get("account_holder"),
                "bank_name": bank_details.get("bank_name"),
                "reference": reference,
                "instructions": [
                    "Maak een overschrijving naar bovenstaande IBAN",
                    f"Gebruik referentie: {reference}",
                    "Je wallet wordt gecrediteerd na ontvangst (meestal binnen 24 uur)"
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
