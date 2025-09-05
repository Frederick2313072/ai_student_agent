"""
LangFuse集成模块 - LLM观测与分析
提供对话追踪、成本分析、性能监控等功能
"""

import os
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from functools import wraps

try:
    from langfuse import Langfuse
    # LangFuse 3.x API - decorators和callback已被移除或重构
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

from ..logging.structured import get_logger

logger = get_logger("monitoring.langfuse")

# 全局LangFuse客户端
_langfuse_client = None
_is_initialized = False


def initialize_langfuse(
    public_key: str = None,
    secret_key: str = None,
    host: str = None,
    debug: bool = False
) -> bool:
    """
    初始化LangFuse客户端
    
    Args:
        public_key: LangFuse公钥
        secret_key: LangFuse私钥
        host: LangFuse主机地址
        debug: 是否启用调试模式
        
    Returns:
        bool: 初始化是否成功
    """
    global _langfuse_client, _is_initialized
    
    if _is_initialized:
        logger.warning("LangFuse已经初始化")
        return True
    
    if not LANGFUSE_AVAILABLE:
        logger.warning("LangFuse库未安装，跳过初始化")
        return False
    
    # 从环境变量获取配置
    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # 检查必需的配置
    if not public_key or not secret_key:
        logger.info("LangFuse密钥未配置，跳过初始化")
        return False
    
    try:
        # 创建LangFuse客户端
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            debug=debug
        )
        
        # 测试连接
        _langfuse_client.auth_check()
        
        _is_initialized = True
        logger.info(f"LangFuse初始化成功: {host}")
        return True
        
    except Exception as e:
        logger.error(f"LangFuse初始化失败: {e}")
        return False


def get_langfuse_client() -> Optional[Any]:
    """获取LangFuse客户端"""
    global _langfuse_client
    
    if not _is_initialized:
        initialize_langfuse()
    
    return _langfuse_client


def create_callback_handler(
    session_id: str = None,
    user_id: str = None,
    metadata: Dict[str, Any] = None
) -> Optional[Any]:
    """
    创建LangFuse回调处理器
    
    Args:
        session_id: 会话ID
        user_id: 用户ID
        metadata: 元数据
        
    Returns:
        CallbackHandler: 回调处理器
    """
    if not LANGFUSE_AVAILABLE or not _is_initialized:
        return None
    
    try:
        return CallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            session_id=session_id,
            user_id=user_id or "anonymous",
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"创建LangFuse回调处理器失败: {e}")
        return None


class LangFuseTracker:
    """LangFuse追踪器"""
    
    def __init__(self, session_id: str = None, user_id: str = None):
        self.client = get_langfuse_client()
        self.session_id = session_id
        self.user_id = user_id or "anonymous"
        self.current_trace = None
        self.current_generation = None
    
    def start_trace(
        self,
        name: str,
        input_data: Any = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Any]:
        """开始一个新的追踪"""
        if not self.client:
            return None
        
        try:
            self.current_trace = self.client.trace(
                name=name,
                input=input_data,
                session_id=self.session_id,
                user_id=self.user_id,
                metadata=metadata or {}
            )
            return self.current_trace
        except Exception as e:
            logger.error(f"开始LangFuse追踪失败: {e}")
            return None
    
    def start_generation(
        self,
        name: str,
        model: str,
        input_data: Any = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Any]:
        """开始一个LLM生成"""
        if not self.client or not self.current_trace:
            return None
        
        try:
            self.current_generation = self.current_trace.generation(
                name=name,
                model=model,
                input=input_data,
                metadata=metadata or {}
            )
            return self.current_generation
        except Exception as e:
            logger.error(f"开始LangFuse生成失败: {e}")
            return None
    
    def end_generation(
        self,
        output: Any = None,
        usage: Dict[str, int] = None,
        level: str = "DEFAULT"
    ):
        """结束LLM生成"""
        if not self.current_generation:
            return
        
        try:
            self.current_generation.end(
                output=output,
                usage=usage,
                level=level
            )
        except Exception as e:
            logger.error(f"结束LangFuse生成失败: {e}")
    
    def start_span(
        self,
        name: str,
        input_data: Any = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Any]:
        """开始一个Span"""
        if not self.client or not self.current_trace:
            return None
        
        try:
            return self.current_trace.span(
                name=name,
                input=input_data,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"开始LangFuse Span失败: {e}")
            return None
    
    def end_trace(
        self,
        output: Any = None,
        metadata: Dict[str, Any] = None
    ):
        """结束追踪"""
        if not self.current_trace:
            return
        
        try:
            self.current_trace.update(
                output=output,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"结束LangFuse追踪失败: {e}")
        finally:
            self.current_trace = None
            self.current_generation = None
    
    def record_feedback(
        self,
        trace_id: str,
        value: float,
        comment: str = None
    ):
        """记录用户反馈"""
        if not self.client:
            return
        
        try:
            self.client.score(
                trace_id=trace_id,
                name="user_feedback",
                value=value,
                comment=comment
            )
        except Exception as e:
            logger.error(f"记录LangFuse反馈失败: {e}")


def langfuse_observe(
    name: str = None,
    capture_input: bool = True,
    capture_output: bool = True,
    transform_to_string: bool = True
):
    """
    LangFuse观测装饰器的包装器
    
    Args:
        name: 操作名称
        capture_input: 是否捕获输入
        capture_output: 是否捕获输出
        transform_to_string: 是否转换为字符串
    """
    def decorator(func):
        if not LANGFUSE_AVAILABLE or not _is_initialized:
            # 如果LangFuse不可用，返回原函数
            return func
        
        # 使用LangFuse的observe装饰器
        return observe(
            name=name or func.__name__,
            capture_input=capture_input,
            capture_output=capture_output,
            transform_to_string=transform_to_string
        )(func)
    
    return decorator


def track_llm_call(
    model: str,
    messages: List[Dict[str, str]],
    response: str,
    usage: Dict[str, int] = None,
    latency_ms: float = None,
    cost_usd: float = None,
    session_id: str = None
):
    """
    记录LLM调用
    
    Args:
        model: 模型名称
        messages: 消息列表
        response: 响应内容
        usage: 使用统计
        latency_ms: 延迟毫秒数
        cost_usd: 成本美元
        session_id: 会话ID
    """
    client = get_langfuse_client()
    if not client:
        return
    
    try:
        # 创建生成记录
        generation = client.generation(
            name=f"llm_call_{model}",
            model=model,
            input=messages,
            output=response,
            usage=usage,
            session_id=session_id,
            metadata={
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.debug(f"LangFuse记录LLM调用: {model}")
        
    except Exception as e:
        logger.error(f"记录LangFuse LLM调用失败: {e}")


def track_tool_usage(
    tool_name: str,
    input_args: Dict[str, Any],
    output_result: Any,
    success: bool,
    duration_ms: float,
    session_id: str = None
):
    """
    记录工具使用
    
    Args:
        tool_name: 工具名称
        input_args: 输入参数
        output_result: 输出结果
        success: 是否成功
        duration_ms: 持续时间毫秒
        session_id: 会话ID
    """
    client = get_langfuse_client()
    if not client:
        return
    
    try:
        # 创建Span记录
        span = client.span(
            name=f"tool_{tool_name}",
            input=input_args,
            output=output_result,
            session_id=session_id,
            metadata={
                "tool_name": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        logger.debug(f"LangFuse记录工具使用: {tool_name}")
        
    except Exception as e:
        logger.error(f"记录LangFuse工具使用失败: {e}")


def track_conversation_quality(
    session_id: str,
    topic: str,
    questions_generated: int,
    completion_status: str,
    user_satisfaction: float = None
):
    """
    记录对话质量指标
    
    Args:
        session_id: 会话ID
        topic: 主题
        questions_generated: 生成的问题数
        completion_status: 完成状态
        user_satisfaction: 用户满意度
    """
    client = get_langfuse_client()
    if not client:
        return
    
    try:
        # 创建评分记录
        client.score(
            name="conversation_quality",
            value=questions_generated,
            session_id=session_id,
            metadata={
                "topic": topic,
                "completion_status": completion_status,
                "user_satisfaction": user_satisfaction,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        if user_satisfaction is not None:
            client.score(
                name="user_satisfaction",
                value=user_satisfaction,
                session_id=session_id
            )
        
        logger.debug(f"LangFuse记录对话质量: {session_id}")
        
    except Exception as e:
        logger.error(f"记录LangFuse对话质量失败: {e}")


def get_session_analytics(session_id: str) -> Dict[str, Any]:
    """
    获取会话分析数据
    
    Args:
        session_id: 会话ID
        
    Returns:
        Dict[str, Any]: 分析数据
    """
    client = get_langfuse_client()
    if not client:
        return {}
    
    try:
        # 这里应该调用LangFuse的API获取会话数据
        # 由于API限制，这里返回模拟数据结构
        return {
            "session_id": session_id,
            "total_tokens": 0,
            "total_cost": 0.0,
            "llm_calls": 0,
            "tool_calls": 0,
            "avg_latency_ms": 0.0,
            "success_rate": 0.0
        }
        
    except Exception as e:
        logger.error(f"获取LangFuse会话分析失败: {e}")
        return {}


def flush_traces():
    """刷新所有待发送的追踪数据"""
    client = get_langfuse_client()
    if not client:
        return
    
    try:
        client.flush()
        logger.debug("LangFuse追踪数据已刷新")
    except Exception as e:
        logger.error(f"刷新LangFuse追踪数据失败: {e}")


def shutdown_langfuse():
    """关闭LangFuse客户端"""
    global _is_initialized, _langfuse_client
    
    if not _is_initialized:
        return
    
    try:
        if _langfuse_client:
            _langfuse_client.flush()
        
        _is_initialized = False
        _langfuse_client = None
        logger.info("LangFuse客户端已关闭")
        
    except Exception as e:
        logger.error(f"关闭LangFuse客户端失败: {e}")


# 便捷的上下文管理器
class LangFuseContext:
    """LangFuse上下文管理器"""
    
    def __init__(
        self,
        trace_name: str,
        session_id: str = None,
        user_id: str = None,
        input_data: Any = None,
        metadata: Dict[str, Any] = None
    ):
        self.tracker = LangFuseTracker(session_id, user_id)
        self.trace_name = trace_name
        self.input_data = input_data
        self.metadata = metadata
    
    def __enter__(self):
        self.tracker.start_trace(
            self.trace_name,
            self.input_data,
            self.metadata
        )
        return self.tracker
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 记录异常
            metadata = self.metadata or {}
            metadata.update({
                "error": str(exc_val),
                "error_type": exc_type.__name__
            })
        
        self.tracker.end_trace(metadata=self.metadata)


# 工厂函数
def create_conversation_tracker(session_id: str, topic: str, user_id: str = None):
    """创建对话追踪器"""
    return LangFuseContext(
        trace_name="feynman_conversation",
        session_id=session_id,
        user_id=user_id,
        input_data={"topic": topic},
        metadata={
            "conversation_type": "feynman_learning",
            "system": "ai_student_agent"
        }
    )

