from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class DiaryEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"diary-{str(uuid.uuid4())[:8]}")
    user_id: str
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content: str
    mood: Optional[str] = None
    private: bool = True

class DiaryCreate(BaseModel):
    content: str
    mood: Optional[str] = None
