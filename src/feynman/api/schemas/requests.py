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
    learning_insights: List[str] = Field(default_factory=list, description="学习洞察")
    execution_time: float = Field(default=0.0, description="执行时间(秒)")
    success: bool = Field(default=True, description="处理是否成功")
    learning_report: Dict = Field(default_factory=dict, description="学习报告")


class MemorizeRequest(BaseModel):
    topic: str
    conversation_history: List[Dict]



