from typing import List, Dict, AsyncGenerator
import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from feynman.agents.core.agent import build_graph
from feynman.api.schemas import ChatRequest, ChatResponse, MemorizeRequest
from feynman.tasks.memory import summarize_conversation_task


router = APIRouter()
langgraph_app = build_graph()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
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

        # 使用Celery异步任务进行记忆固化
        if final_memory and request.topic:
            task_result = summarize_conversation_task.delay(
                topic=request.topic,
                conversation_history=final_memory
            )
            logger.info(f"记忆固化任务已提交: {task_result.id}")

        return ChatResponse(
            questions=questions,
            session_id=request.session_id,
            short_term_memory=final_memory,
        )
    except Exception as e:
        logger.error(f"Agent处理请求时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent在处理时遇到内部错误。")


async def stream_generator(app, inputs: Dict, config: Dict) -> AsyncGenerator[str, None]:
    full_response = ""
    async for event in app.astream_events(inputs, config, version="v1"):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                full_response += content

    final_answer = full_response
    think_end_tag = "</think>"
    if think_end_tag in full_response:
        final_answer = full_response.rsplit(think_end_tag, 1)[-1].lstrip()

    words = final_answer.split(" ")
    for i, word in enumerate(words):
        token = word + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps(token)}\n\n"
        await asyncio.sleep(0.05)

    yield f"data: {json.dumps('[END_OF_STREAM]')}\n\n"


@router.post("/stream")
async def chat_with_agent_stream(request: ChatRequest):
    inputs = {
        "topic": request.topic,
        "user_explanation": request.explanation,
        "short_term_memory": request.short_term_memory,
    }
    config = {"configurable": {"thread_id": request.session_id}}

    return StreamingResponse(stream_generator(langgraph_app, inputs, config), media_type="text/event-stream")


@router.post("/memorize", status_code=202)
async def memorize_conversation(request: MemorizeRequest):
    """手动触发记忆固化任务"""
    try:
        task_result = summarize_conversation_task.delay(
            topic=request.topic,
            conversation_history=request.conversation_history
        )
        logger.info(f"手动记忆固化任务已提交: {task_result.id}")
        
        return {
            "message": "记忆任务已加入Celery队列处理。",
            "task_id": task_result.id,
            "status": "submitted"
        }
    except Exception as e:
        logger.error(f"提交记忆任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="提交记忆任务失败")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询Celery任务状态"""
    try:
        from feynman.tasks.celery_app import celery_app
        
        # 获取任务结果
        result = celery_app.AsyncResult(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "current": result.info.get("progress", 0) if isinstance(result.info, dict) else 0,
        }
        
        if result.status == "PENDING":
            response["message"] = "任务等待执行"
        elif result.status == "PROGRESS":
            response["message"] = result.info.get("status", "任务执行中")
            response["current"] = result.info.get("progress", 0)
        elif result.status == "SUCCESS":
            response["message"] = "任务执行成功"
            response["result"] = result.result
        elif result.status == "FAILURE":
            response["message"] = "任务执行失败"
            response["error"] = str(result.info)
        else:
            response["message"] = f"任务状态: {result.status}"
            
        return response
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


