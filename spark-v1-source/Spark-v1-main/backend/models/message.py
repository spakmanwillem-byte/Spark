from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Message(BaseModel):
    id: str
    user_id: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_spark: bool = False

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: Optional[str] = None
    user_gradatie: Optional[int] = None
    context: Optional[dict] = None
    auto_fill: Optional[dict] = None  # {updated_fields: [...], updates: {...}}
