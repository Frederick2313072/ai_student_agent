"""
记忆相关的 Celery 任务

处理费曼学习系统中的记忆固化、总结和存储任务。
这些任务在后台异步执行，不影响用户的交互体验。
"""

from typing import List, Dict, Any
import logging
from celery import current_task

from feynman.tasks.celery_app import celery_app
from feynman.agents.core.agent import summarize_conversation_for_memory
from feynman.infrastructure.monitoring.tracing import trace_span, add_span_attribute

logger = logging.getLogger(__name__)


@celery_app.task(
    name="memory.summarize_conversation",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    soft_time_limit=180,  # 3分钟软限制
    time_limit=240       # 4分钟硬限制
)
def summarize_conversation_task(self, topic: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    异步记忆固化任务
    
    将用户的对话历史总结并存储到长期记忆中。
    这个任务会在用户完成一轮对话后在后台执行。
    
    Args:
        topic: 对话主题
        conversation_history: 对话历史记录列表
        
    Returns:
        Dict包含任务执行结果和统计信息
    """
    task_id = self.request.id
    
    with trace_span("celery_memory_task") as span:
        # 添加追踪属性
        add_span_attribute("task.id", task_id)
        add_span_attribute("task.type", "memory_summarization")
        add_span_attribute("memory.topic", topic)
        add_span_attribute("memory.conversation_length", len(conversation_history))
        
        try:
            logger.info(f"开始执行记忆固化任务 {task_id}，主题: {topic}")
            
            # 更新任务状态为进行中
            self.update_state(
                state='PROGRESS',
                meta={'status': '正在处理对话历史...', 'progress': 25}
            )
            
            # 验证输入数据
            if not topic or not topic.strip():
                raise ValueError("主题不能为空")
                
            if not conversation_history:
                logger.warning(f"任务 {task_id} 收到空的对话历史，跳过处理")
                return {
                    "task_id": task_id,
                    "status": "skipped",
                    "reason": "empty_conversation_history",
                    "topic": topic
                }
            
            # 更新进度
            self.update_state(
                state='PROGRESS', 
                meta={'status': '正在生成摘要...', 'progress': 50}
            )
            
            # 调用原有的记忆固化函数
            summarize_conversation_for_memory(topic, conversation_history)
            
            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'status': '记忆固化完成', 'progress': 100}
            )
            
            logger.info(f"记忆固化任务 {task_id} 成功完成")
            
            return {
                "task_id": task_id,
                "status": "success",
                "topic": topic,
                "conversation_length": len(conversation_history),
                "message": "记忆固化任务成功完成"
            }
            
        except Exception as e:
            logger.error(f"记忆固化任务 {task_id} 执行失败: {str(e)}")
            
            # 添加错误信息到追踪
            span.set_attribute("error", True) 
            span.set_attribute("error.message", str(e))
            
            # 重新抛出异常让Celery处理重试
            raise


@celery_app.task(
    name="memory.cleanup_expired",
    bind=True,
    soft_time_limit=120,
    time_limit=180
)
def cleanup_expired_memories_task(self, days_old: int = 30) -> Dict[str, Any]:
    """
    清理过期记忆任务
    
    定期清理超过指定天数的旧记忆数据，释放存储空间。
    
    Args:
        days_old: 清理多少天前的记忆，默认30天
        
    Returns:
        Dict包含清理统计信息
    """
    task_id = self.request.id
    
    logger.info(f"开始执行记忆清理任务 {task_id}，清理 {days_old} 天前的数据")
    
    try:
        # TODO: 实现记忆清理逻辑
        # 这里可以调用 memory_manager 的清理方法
        
        cleaned_count = 0  # 实际清理的记录数
        
        logger.info(f"记忆清理任务 {task_id} 完成，清理了 {cleaned_count} 条记录")
        
        return {
            "task_id": task_id,
            "status": "success", 
            "cleaned_count": cleaned_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"记忆清理任务 {task_id} 失败: {str(e)}")
        raise
