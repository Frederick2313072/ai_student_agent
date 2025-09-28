from typing import List, Dict, AsyncGenerator
import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from feynman.agents.core import execute_multi_agent_workflow
from feynman.api.schemas import ChatRequest, ChatResponse, MemorizeRequest
from feynman.tasks.memory import summarize_conversation_task, summarize_conversation_for_memory
from feynman.core.config.settings import get_settings
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage


router = APIRouter()
logger = logging.getLogger(__name__)
def _fallback_simple_chat(topic: str, explanation: str) -> Dict[str, List[str]]:
    """在工作流失败时的简易对话降级。

    优先使用OpenAI/智谱生成3个苏格拉底式问题与2条学习洞见；
    若无可用密钥，则基于启发式返回占位结果。

    Args:
        topic: 主题
        explanation: 用户解释

    Returns:
        Dict: {"questions": List[str], "learning_insights": List[str]}
    """
    try:
        settings = get_settings()
        llm = None
        if settings.openai_api_key:
            llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model, temperature=0.5)
        elif settings.zhipu_api_key:
            llm = ChatZhipuAI(api_key=settings.zhipu_api_key, model=settings.zhipu_model, temperature=0.5)

        if llm is not None:
            prompt = (
                "你是一名教学助理。基于下述主题与讲解，给出：\n"
                "1) 三个循序渐进的苏格拉底式问题（简短精炼）；\n"
                "2) 两条针对学习者的关键洞见或建议（简短）。\n"
                f"主题: {topic}\n"
                f"讲解: {explanation}\n"
                "请严格以JSON返回：{\"questions\":[...],\"insights\":[...]}"
            )
            msg = HumanMessage(content=prompt)
            resp = llm.invoke([msg])
            text = getattr(resp, "content", "") or str(resp)
            # 简单解析（宽松处理）
            import json as _json
            questions, insights = [], []
            try:
                data = _json.loads(text)
                questions = [q for q in data.get("questions", []) if isinstance(q, str)][:3]
                insights = [i for i in data.get("insights", []) if isinstance(i, str)][:2]
            except Exception:
                # 宽松拆分
                lines = [l.strip("- • ") for l in text.splitlines() if l.strip()]
                for l in lines:
                    if len(questions) < 3 and l.endswith("?"):
                        questions.append(l)
                    elif len(insights) < 2 and not l.endswith("?"):
                        insights.append(l)
            if not questions:
                questions = [f"你能从基础定义出发解释‘{topic}’吗？", "这个概念与已知知识有什么联系？", "能举一个贴近生活的例子吗？"]
            if not insights:
                insights = ["将复杂概念拆成可验证的子问题。", "结合实例与类比能快速建立直觉。"]
            return {"questions": questions[:3], "learning_insights": insights[:2]}
    except Exception:
        pass

    # 无密钥或调用失败时的启发式降级
    base = explanation.strip()[:30] or topic
    return {
        "questions": [
            f"用你的话复述‘{topic}’的核心是什么？",
            f"{base} 中最容易混淆的点是？为什么？",
            "如果向初学者解释，你会用哪两个比喻？",
        ],
        "learning_insights": [
            "先画出关键概念与关系图，再细化细节。",
            "通过自测题验证是否真正掌握。",
        ],
    }



@router.post(
    "/chat",
    response_model=ChatResponse,
    description="""与多Agent进行一次对话处理并返回结果。

    - 输入主题、解释与会话上下文，系统执行多Agent工作流分析并返回问题与洞察。
    - 若 Celery 异步记忆队列不可用，将自动降级为进程内轻量记忆固化，不影响主流程。
    """
)
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

        # 使用Celery异步任务进行记忆固化（失败时降级为进程内处理）
        if final_memory and request.topic:
            try:
                task_result = summarize_conversation_task.delay(
                    topic=request.topic,
                    conversation_history=final_memory
                )
                logger.info(f"记忆固化任务已提交: {task_result.id}")
            except Exception as e:
                logger.warning(f"Celery不可用，降级为进程内记忆固化: {e}")
                try:
                    summarize_conversation_for_memory(request.topic, final_memory)
                except Exception as inner_e:
                    logger.error(f"进程内记忆固化失败（忽略，不影响主流程）: {inner_e}")

        # 若失败或无有效结果，降级为普通对话
        if not result.get("success", False) and not (questions or learning_insights):
            fallback = _fallback_simple_chat(request.topic, request.explanation)
            questions = fallback["questions"]
            learning_insights = fallback["learning_insights"]
        
        return ChatResponse(
            questions=questions,
            session_id=request.session_id,
            short_term_memory=final_memory,
            learning_insights=learning_insights,
            execution_time=result.get("execution_time", 0),
            success=True,
            learning_report=result.get("learning_report", {})
        )
    except Exception as e:
        logger.error(f"多Agent系统处理请求时出错: {str(e)}")
        # 失败时同步降级
        fallback = _fallback_simple_chat(request.topic, request.explanation)
        return ChatResponse(
            questions=fallback["questions"],
            session_id=request.session_id,
            short_term_memory=request.short_term_memory,
            learning_insights=fallback["learning_insights"],
            execution_time=0,
            success=True,
            learning_report={}
        )


async def stream_multi_agent_workflow(inputs: Dict) -> AsyncGenerator[str, None]:
    """多Agent工作流的流式处理"""
    try:
        # 发送开始信号
        yield f"data: {json.dumps({'type': 'start', 'message': '启动多Agent工作流'})}\n\n"
        
        # 执行工作流（目前是同步的，未来可以改为流式）
        result = await execute_multi_agent_workflow(inputs)
        
        # 流式发送结果（支持降级补全空结果）
        questions = result.get("questions", [])
        insights = result.get("learning_insights", [])

        if not questions and not insights:
            # 触发降级生成最小可用结果
            fallback = _fallback_simple_chat(inputs.get("topic", ""), inputs.get("explanation", ""))
            questions = fallback.get("questions", [])
            insights = fallback.get("learning_insights", [])

        # 发送问题
        for i, question in enumerate(questions):
            yield f"data: {json.dumps({'type': 'question', 'index': i, 'content': question})}\n\n"
            await asyncio.sleep(0.05)

        # 发送洞察
        for i, insight in enumerate(insights):
            yield f"data: {json.dumps({'type': 'insight', 'index': i, 'content': insight})}\n\n"
            await asyncio.sleep(0.05)

        # 合并回结果并发送最终块
        result = dict(result)
        result["questions"] = questions
        result["learning_insights"] = insights
        result["success"] = True
        yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
        
        # 结束信号
        yield f"data: {json.dumps({'type': 'end', 'message': '工作流完成'})}\n\n"
        
    except Exception as e:
        # 错误事件
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        # 尝试降级为普通对话并继续流式输出
        try:
            fallback = _fallback_simple_chat(inputs.get("topic", ""), inputs.get("explanation", ""))
            for i, q in enumerate(fallback.get("questions", [])):
                yield f"data: {json.dumps({'type': 'question', 'index': i, 'content': q})}\n\n"
                await asyncio.sleep(0.05)
            for i, ins in enumerate(fallback.get("learning_insights", [])):
                yield f"data: {json.dumps({'type': 'insight', 'index': i, 'content': ins})}\n\n"
                await asyncio.sleep(0.05)
            yield f"data: {json.dumps({'type': 'result', 'data': {'success': True}})}\n\n"
        except Exception:
            pass


@router.post(
    "/stream",
    description="""以Server-Sent Events流式返回多Agent工作流的执行过程与结果。

    - 首先发送 `start` 事件，随后按序发送 `question` 与 `insight`，最终发送 `result` 与 `end`。
    - 发生异常时发送 `error` 事件。
    """
)
async def chat_with_agent_stream(request: ChatRequest):
    inputs = {
        "topic": request.topic,
        "explanation": request.explanation,
        "session_id": request.session_id,
        "short_term_memory": request.short_term_memory,
    }

    return StreamingResponse(stream_multi_agent_workflow(inputs), media_type="text/event-stream")


@router.post(
    "/memorize",
    status_code=202,
    description="""手动触发对话记忆固化任务。

    - 优先投递到 Celery 队列；若不可用，自动降级为进程内轻量固化并仍返回 202。
    - 降级不会影响主流程响应。
    """
)
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
            "status": "submitted",
            "queued": True
        }
    except Exception as e:
        # 降级为进程内记忆固化，并返回202告知客户端已处理
        logger.warning(f"Celery不可用，记忆任务降级为进程内执行: {e}")
        try:
            summarize_conversation_for_memory(request.topic, request.conversation_history)
            return {
                "message": "Celery不可用，已在进程内完成记忆固化。",
                "status": "processed_inline",
                "queued": False
            }
        except Exception as inner_e:
            logger.error(f"进程内记忆固化失败: {inner_e}")
            # 最后兜底仍返回错误
            raise HTTPException(status_code=500, detail="提交记忆任务失败：队列与降级均失败")


@router.get(
    "/task/{task_id}",
    description="""查询Celery任务状态。

    - 返回任务当前状态与可用的进度信息；若任务不存在返回404。
    """
)
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


