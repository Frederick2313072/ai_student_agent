"""
AI学生费曼学习系统 - 主启动文件
使用LangGraph架构构建的智能学习助手
"""
from dotenv import load_dotenv

# 在所有其他导入之前加载环境变量，确保配置在模块初始化时可用
load_dotenv('test.env')

import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, AsyncGenerator
import asyncio
import json

# 导入我们重构后的Agent核心
from agent.agent import build_graph, summarize_conversation_for_memory

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
    version="3.2"
)

langgraph_app = build_graph()


# --- API端点定义 ---

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    与AI学生Agent进行对话。
    V3.2更新：将记忆固化操作移至后台任务，以加快响应速度。
    """
    print(f"--- 收到请求 /chat (Session: {request.session_id}) ---")
    
    # 构造LangGraph的输入，但移除 memory_manager 节点
    inputs = {
        "topic": request.topic,
        "user_explanation": request.explanation,
        "short_term_memory": request.short_term_memory,
    }
    
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        # 注意：这里的调用将不再经过 memory_manager 节点
        result = await langgraph_app.ainvoke(inputs, config)
        
        questions = result.get("question_queue", [])
        final_memory = result.get("short_term_memory", [])

        # --- 后台任务：处理记忆固化 ---
        # 将耗时的记忆总结和存储操作放入后台
        background_tasks.add_task(
            summarize_conversation_for_memory, 
            topic=request.topic,
            conversation_history=final_memory
        )
        
        print(f"--- 请求处理完成. 立即返回 {len(questions)} 个问题. 记忆固化已转入后台 ---")
        return ChatResponse(
            questions=questions, 
            session_id=request.session_id,
            short_term_memory=final_memory
        )
        
    except Exception as e:
        print(f"处理请求时发生错误: {e}")
        raise HTTPException(status_code=500, detail="Agent在处理时遇到内部错误。")

async def stream_generator(app, inputs: Dict, config: Dict) -> AsyncGenerator[str, None]:
    """
    一个异步生成器，用于运行LangGraph Agent，处理完整响应以移除思考过程，
    然后以打字机效果流式传输最终答案。
    """
    full_response = ""
    async for event in app.astream_events(inputs, config, version="v1"):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                full_response += content

    # --- Agent运行完毕，开始后处理 ---
    final_answer = full_response
    think_end_tag = "</think>"
    if think_end_tag in full_response:
        # 仅保留最后一个</think>标签之后的内容作为最终答案
        final_answer = full_response.rsplit(think_end_tag, 1)[-1].lstrip()
    
    # --- 以打字机效果模拟流式输出 ---
    # 按词发送，以获得更好的视觉效果
    words = final_answer.split(' ')
    for i, word in enumerate(words):
        token = word + (' ' if i < len(words) - 1 else '')
        # 使用json.dumps确保换行符等特殊字符被正确编码
        yield f"data: {json.dumps(token)}\n\n"
        await asyncio.sleep(0.05)  # 模拟打字的微小延迟

    # 发送流结束的特殊标记
    yield f"data: {json.dumps('[END_OF_STREAM]')}\n\n"


@app.post("/chat/stream")
async def chat_with_agent_stream(request: ChatRequest):
    """
    与AI学生Agent进行流式对话。
    """
    print(f"--- 收到流式请求 /chat/stream (Session: {request.session_id}) ---")
    
    inputs = {
        "topic": request.topic,
        "user_explanation": request.explanation,
        "short_term_memory": request.short_term_memory,
    }
    config = {"configurable": {"thread_id": request.session_id}}
    
    return StreamingResponse(stream_generator(langgraph_app, inputs, config), media_type="text/event-stream")


class MemorizeRequest(BaseModel):
    """记忆请求体模型"""
    topic: str
    conversation_history: List[Dict]

@app.post("/memorize", status_code=202)
async def memorize_conversation(request: MemorizeRequest, background_tasks: BackgroundTasks):
    """
    接收对话历史并将其放入后台任务进行记忆固化。
    """
    print(f"--- 收到记忆请求 /memorize (Topic: {request.topic}) ---")
    background_tasks.add_task(
        summarize_conversation_for_memory, 
        topic=request.topic,
        conversation_history=request.conversation_history
    )
    return {"message": "记忆任务已加入后台处理队列。"}


@app.get("/")
def read_root():
    return {"message": "欢迎来到费曼学生Agent API。请访问 /docs 查看API文档。"}

# 用于本地开发的启动命令: uvicorn main:app --reload 