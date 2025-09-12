from typing import List, Dict, AsyncGenerator
import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from feynman.agents.core import execute_multi_agent_workflow
from feynman.api.schemas import ChatRequest, ChatResponse, MemorizeRequest
from feynman.tasks.memory import summarize_conversation_task


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    inputs = {
        "topic": request.topic,
        "explanation": request.explanation,
        "session_id": request.session_id,
        "short_term_memory": request.short_term_memory,
    }

    try:
        # 使用新的多Agent工作流
        result = await execute_multi_agent_workflow(inputs)
        
        questions = result.get("questions", [])
        final_memory = result.get("short_term_memory", [])
        learning_insights = result.get("learning_insights", [])

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
            learning_insights=learning_insights,
            execution_time=result.get("execution_time", 0),
            success=result.get("success", True),
            learning_report=result.get("learning_report", {})
        )
    except Exception as e:
        logger.error(f"多Agent系统处理请求时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="多Agent系统在处理时遇到内部错误。")


async def stream_multi_agent_workflow(inputs: Dict) -> AsyncGenerator[str, None]:
    """多Agent工作流的流式处理"""
    try:
        # 发送开始信号
        yield f"data: {json.dumps({'type': 'start', 'message': '启动多Agent工作流'})}\n\n"
        
        # 执行工作流（目前是同步的，未来可以改为流式）
        result = await execute_multi_agent_workflow(inputs)
        
        # 流式发送结果
        if result.get("success", False):
            # 发送问题
            questions = result.get("questions", [])
            for i, question in enumerate(questions):
                yield f"data: {json.dumps({'type': 'question', 'index': i, 'content': question})}\n\n"
                await asyncio.sleep(0.1)
            
            # 发送洞察
            insights = result.get("learning_insights", [])
            for i, insight in enumerate(insights):
                yield f"data: {json.dumps({'type': 'insight', 'index': i, 'content': insight})}\n\n"
                await asyncio.sleep(0.1)
            
            # 发送最终结果
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': result.get('error', '处理失败')})}\n\n"
        
        # 结束信号
        yield f"data: {json.dumps({'type': 'end', 'message': '工作流完成'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream")
async def chat_with_agent_stream(request: ChatRequest):
    inputs = {
        "topic": request.topic,
        "explanation": request.explanation,
        "session_id": request.session_id,
        "short_term_memory": request.short_term_memory,
    }

    return StreamingResponse(stream_multi_agent_workflow(inputs), media_type="text/event-stream")


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


