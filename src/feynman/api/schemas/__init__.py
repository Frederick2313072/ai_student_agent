"""
API数据模型 - 统一的请求和响应模式定义

包含所有API端点的Pydantic模型，确保数据验证和序列化的一致性。
"""

from .requests import (
    ChatRequest,
    ChatResponse,
    MemorizeRequest
)

__all__ = [
    "ChatRequest",
    "ChatResponse", 
    "MemorizeRequest"
]