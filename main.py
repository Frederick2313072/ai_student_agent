"""
AI学生费曼学习系统 - 主启动文件
使用LangGraph架构构建的智能学习助手
"""
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入我们重构后的Agent核心
from agent.agent import build_graph

# --- 数据模型定义 ---

class ChatRequest(BaseModel):
    """API请求体模型"""
    topic: str
    explanation: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # short_term_memory 对应 AgentState 中的同名字段
    short_term_memory: List[Dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    """API响应体模型"""
    questions: List[str]
    session_id: str
    # 返回更新后的短期记忆，以便客户端可以保持对话历史
    short_term_memory: List[Dict[str, str]]


# --- FastAPI应用初始化 ---

app = FastAPI(
    title="Feynman Student Agent API",
    description="一个基于费曼学习法的AI学生Agent，通过API提供服务。",
    version="3.1"
)

# --- CORS中间件配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的跨域请求
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)


langgraph_app = build_graph()


# --- API端点定义 ---

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    与AI学生Agent进行对话。
    """
    print(f"--- 收到请求 /chat (Session: {request.session_id}) ---")
    
    # 构造LangGraph的输入，传入整个短期记忆
    inputs = {
        "topic": request.topic,
        "user_explanation": request.explanation,
        "short_term_memory": request.short_term_memory,
    }
    
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        result = await langgraph_app.ainvoke(inputs, config)
        
        questions = result.get("question_queue", [])
        final_memory = result.get("short_term_memory", [])
        
        print(f"--- 请求处理完成. 返回 {len(questions)} 个问题 ---")
        return ChatResponse(
            questions=questions, 
            session_id=request.session_id,
            short_term_memory=final_memory
        )
        
    except Exception as e:
        print(f"处理请求时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Agent在处理时遇到内部错误。")

@app.get("/")
def read_root():
    return {"message": "欢迎来到费曼学生Agent API。请访问 /docs 查看API文档。"}

# 用于本地开发的启动命令: uvicorn main:app --reload 