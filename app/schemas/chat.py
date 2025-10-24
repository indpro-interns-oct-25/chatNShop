from pydantic import BaseModel
from typing import Any

class ChatRequest(BaseModel):
    query: str
    user_id: str

class ChatResponse(BaseModel):
    response_type: str  # e.g., "products", "text", "error"
    data: Any