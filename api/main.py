"""
Vercel兼容的FastAPI应用入口
简化版本，移除了复杂的依赖和长期运行的服务
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 设置环境变量文件路径
env_file = project_root / "environments" / "test.env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

# 创建简化的FastAPI应用
app = FastAPI(
    title="Feynman Student Agent API (Vercel)",
    description="基于费曼学习法的AI学生Agent - Vercel部署版",
    version="3.2-vercel"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    topic: str
    explanation: str
    session_id: Optional[str] = None
    short_term_memory: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool
    message: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "message": "费曼学生Agent API - Vercel版本",
        "version": "3.2-vercel",
        "docs": "/docs",
        "limitations": [
            "简化版本，适用于Vercel Serverless环境",
            "不包含ChromaDB和复杂的AI工具链",
            "建议用于API测试和基础功能验证"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "platform": "vercel",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    简化的聊天端点 - 不包含实际的AI功能
    在Vercel环境中，复杂的AI处理应该移到其他服务
    """
    try:
        # 这里应该调用你的AI服务API
        # 由于Vercel的限制，建议将AI处理部署到其他平台
        response_text = f"感谢你教授关于'{request.topic}'的知识。由于这是Vercel简化版本，实际的AI处理功能需要部署到支持长时间运行的平台上。"
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id or "vercel-session",
            success=True,
            message="这是简化版本的响应"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    流式聊天端点的占位符
    Vercel对流式响应支持有限
    """
    return {
        "message": "流式响应在Vercel环境中支持有限",
        "recommendation": "建议使用Railway或Render部署完整功能"
    }

# Vercel要求的处理函数
def handler(request):
    return app(request)

# 兼容性导出
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
