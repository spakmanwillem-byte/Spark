"""
Spark Auth Module - Data Models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user fields"""
    naam: str
    volledige_naam: Optional[str] = None
    sleutelwoord: str
    gradatie: int = 7
    rol: str = "Onbekende"


class UserCreate(BaseModel):
    """Create user request"""
    naam: str
    volledige_naam: Optional[str] = None
    sleutelwoord: str


class User(UserBase):
    """Full user model"""
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    registered_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: Optional[str] = None
    gesprekken_count: int = 0
    trust_score: int = 0
    masterkey: Optional[str] = None
    xp: int = 0
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class LoginRequest(BaseModel):
    """Login request"""
    naam: str
    sleutelwoord: str
    masterkey: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    message: str
    user: Optional[dict] = None
    is_masterkey: bool = False


class SessionStatus(BaseModel):
    """Session status response"""
    status: str  # "active", "expired", "invalid"
    user_id: Optional[str] = None
    naam: Optional[str] = None
    gradatie: Optional[int] = None
    expires_in: Optional[int] = None
    last_active: Optional[str] = None
