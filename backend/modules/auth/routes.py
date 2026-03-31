"""
Spark Auth Module - API Routes
All auth endpoints in one place
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from .service import AuthService
from .models import LoginRequest, LoginResponse, SessionStatus, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


# ============== LOGIN / LOGOUT ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with naam + sleutelwoord
    
    Returns user data if successful
    """
    user, is_masterkey = AuthService.authenticate(
        naam=request.naam,
        sleutelwoord=request.sleutelwoord,
        masterkey=request.masterkey
    )
    
    if not user:
        return LoginResponse(
            success=False,
            message="Ongeldige inloggegevens",
            user=None,
            is_masterkey=False
        )
    
    # Update activity
    AuthService.heartbeat(user.get("id"))
    
    return LoginResponse(
        success=True,
        message="Welkom terug!" if not is_masterkey else "Masterkey toegang",
        user=user,
        is_masterkey=is_masterkey
    )


@router.post("/logout")
async def logout(user_id: str):
    """
    Logout user (clear session)
    """
    # For now, just acknowledge - session will expire naturally
    return {"success": True, "message": "Uitgelogd"}


# ============== SESSION ==============

@router.post("/session/heartbeat", response_model=SessionStatus)
async def heartbeat(user_id: str):
    """
    Session heartbeat - keeps session alive
    
    Should be called every 30 seconds from frontend
    """
    result = AuthService.heartbeat(user_id)
    
    if result.get("status") == "invalid":
        raise HTTPException(status_code=401, detail="Sessie ongeldig")
    
    return SessionStatus(**result)


@router.get("/session/validate")
async def validate_session(user_id: str):
    """
    Check if session is still valid
    """
    is_valid = AuthService.validate_session(user_id)
    
    if not is_valid:
        return {"valid": False, "message": "Sessie verlopen"}
    
    user = AuthService.get_user_by_id(user_id)
    return {
        "valid": True,
        "user": user
    }


# ============== USER MANAGEMENT ==============

@router.get("/users")
async def get_users():
    """
    Get all users (admin only in production)
    """
    users = AuthService.get_all_users()
    # Remove sensitive fields
    safe_users = []
    for u in users:
        safe_user = {k: v for k, v in u.items() if k not in ["masterkey"]}
        safe_users.append(safe_user)
    return {"users": safe_users, "count": len(safe_users)}


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Get user by ID
    """
    user = AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return user


@router.post("/users")
async def create_user(user_data: UserCreate):
    """
    Create new user
    """
    user, error = AuthService.create_user(user_data)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"success": True, "user": user}


@router.put("/users/{user_id}")
async def update_user(user_id: str, updates: dict):
    """
    Update user fields
    """
    # Protect sensitive fields
    protected = ["id", "masterkey", "registered_date"]
    updates = {k: v for k, v in updates.items() if k not in protected}
    
    if not AuthService.update_user(user_id, updates):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    return {"success": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """
    Delete user
    """
    if not AuthService.delete_user(user_id):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    return {"success": True}


# ============== GRADATIE ==============

@router.get("/gradaties")
async def get_gradaties():
    """
    Get all gradatie definitions
    """
    return {"gradaties": AuthService.get_gradaties()}


@router.put("/users/{user_id}/gradatie")
async def update_gradatie(user_id: str, gradatie: int, reden: str = ""):
    """
    Update user gradatie
    """
    if gradatie < 1 or gradatie > 7:
        raise HTTPException(status_code=400, detail="Gradatie moet tussen 1 en 7 zijn")
    
    if not AuthService.update_gradatie(user_id, gradatie, reden):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    return {"success": True}
