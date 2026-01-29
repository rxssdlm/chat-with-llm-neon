from pydantic import BaseModel
from datetime import datetime


class AgentCreate(BaseModel):
    name: str
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 1024


class AgentRead(BaseModel):
    id: int
    name: str
    model: str
    temperature: float
    max_tokens: int
    created_at: datetime

    class Config:
        from_attributes = True
