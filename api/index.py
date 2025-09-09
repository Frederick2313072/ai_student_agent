"""
Vercel兼容的FastAPI应用入口
简化版本，移除了复杂的依赖和长期运行的服务
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import datetime

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
        "status": "running",
        "timestamp": datetime.datetime.now().isoformat(),
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
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": os.getenv("VERCEL_ENV", "development")
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    简化的聊天端点 - 不包含实际的AI功能
    在Vercel环境中，复杂的AI处理应该移到其他服务
    """
    try:
        # 模拟AI响应
        response_text = f"""感谢你教授关于'{request.topic}'的知识！

作为AI学生，我对你的讲解很感兴趣。你提到：
{request.explanation[:200]}{'...' if len(request.explanation) > 200 else ''}

由于这是Vercel简化版本，完整的AI分析功能需要部署到支持长时间运行的平台上。

如需完整功能，请访问完整版本的部署。"""
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id or f"vercel-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            success=True,
            message="Vercel简化版本响应"
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
        "recommendation": "建议使用Railway或Render部署完整功能",
        "fallback_response": f"关于'{request.topic}'的学习内容已收到，完整的流式响应功能请使用完整版部署。"
    }

@app.get("/api/v1/status")
def get_status():
    """获取API状态信息"""
    return {
        "api_version": "3.2-vercel",
        "status": "operational",
        "features": {
            "basic_chat": True,
            "streaming": False,
            "ai_processing": False,
            "memory": False,
            "knowledge_graph": False
        },
        "deployment": {
            "platform": "vercel",
            "region": os.getenv("VERCEL_REGION", "unknown"),
            "env": os.getenv("VERCEL_ENV", "development")
        }
    }

# Vercel要求的处理函数
def handler(event, context):
    """Vercel serverless函数处理器"""
    return app

# 兼容性导出
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
