# API v1 路由聚合
from fastapi import APIRouter
from .endpoints import chat, monitoring, knowledge_graph

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监控"])
api_router.include_router(knowledge_graph.router, prefix="/kg", tags=["知识图谱"])
