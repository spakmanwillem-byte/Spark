from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class User(BaseModel):
    id: str = Field(default_factory=lambda: f"user-{str(uuid.uuid4())[:8]}")
    naam: str
    volledige_naam: Optional[str] = None
    sleutelwoord: str
    gradatie: int = 7
    rol: str = "Onbekende"
    relatie_tot_willem: Optional[str] = None
    registered_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_active: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    gesprekken_count: int = 0
    trust_score: int = 0
    onboarding_completed: bool = False
    persoonlijke_info: Dict[str, Any] = Field(default_factory=dict)

class UserCreate(BaseModel):
    naam: str
    volledige_naam: Optional[str] = None
    sleutelwoord: str

class UserIdentification(BaseModel):
    naam: str
    sleutelwoord: Optional[str] = None
    masterkey: Optional[str] = None
