from pydantic import BaseModel, Field
from typing import List, Dict
import uuid


class ChatRequest(BaseModel):
    topic: str
    explanation: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    short_term_memory: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    questions: List[str]
    session_id: str
    short_term_memory: List[Dict[str, str]]


class MemorizeRequest(BaseModel):
    topic: str
    conversation_history: List[Dict]



