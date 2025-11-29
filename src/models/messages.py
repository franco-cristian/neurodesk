from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="ID del empleado")
    message: str = Field(..., description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(default=None, description="ID único de la conversación")
    context: Optional[dict] = Field(default={})

class ChatResponse(BaseModel):
    response: str
    is_safe: bool
    sentiment: str = "Neutral"
    risk_level: str = "Low"
    actions_taken: List[str] = []
    ui_component: Optional[Dict[str, Any]] = None 
    next_steps: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)