from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from services.scripting_handler import ScriptingHandler

router = APIRouter()


class ScriptRequest(BaseModel):
    """
    JSON DSL Request format
    
    Example:
    {
        "action": "create_trade",
        "params": {"action": "BUY", "amount": 10, "symbol": "BCH-EUR"},
        "user_id": "001"
    }
    """
    action: str
    params: Dict[str, Any]
    user_id: str


@router.post("/execute")
async def execute_script(request: ScriptRequest):
    """
    Execute JSON-based scripting command
    
    Veilige vervanging van exec/eval met whitelisted actions:
    - create_trade: Trigger manual trade
    - get_position_state: Haal position state op
    - log_action: Log custom actie
    - calculate: Veilige math calculation
    
    Request format:
    {
        "action": "create_trade",
        "params": {"action": "BUY", "amount": 10},
        "user_id": "001"
    }
    """
    result = ScriptingHandler.execute(request.dict())
    
    # Return direct result (bevat success, result, error, etc.)
    return result


@router.get("/actions")
async def get_available_actions():
    """
    Lijst van alle beschikbare acties met documentatie en voorbeelden
    
    Vervangt oude /functions endpoint
    """
    return ScriptingHandler.get_available_actions()
