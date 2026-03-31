from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"know-{str(uuid.uuid4())[:8]}")
    begrip: str
    betekenis: str
    categorie: str = "algemeen"
    bron: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    vertrouwen: int = 100

class KnowledgeCreate(BaseModel):
    begrip: str
    betekenis: str
    categorie: Optional[str] = "algemeen"
    bron: Optional[str] = None
