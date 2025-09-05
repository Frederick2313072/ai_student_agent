"""
OpenTelemetry分布式追踪模块 - 配置和管理分布式追踪
支持Jaeger、Zipkin等追踪后端
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

from ..logging.structured import get_logger

logger = get_logger("monitoring.tracing")

# 全局追踪器
_tracer = None
_is_initialized = False


def initialize_tracing(
    service_name: str = None,
    service_version: str = None,
    otlp_endpoint: str = None,
    console_export: bool = False
) -> None:
    """
    初始化OpenTelemetry追踪
    
    Args:
        service_name: 服务名称
        service_version: 服务版本
        otlp_endpoint: OTLP导出端点
        console_export: 是否启用控制台导出
    """
    global _tracer, _is_initialized
    
    if _is_initialized:
        logger.warning("OpenTelemetry追踪已经初始化")
        return
    
    # 从环境变量获取配置
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "feynman-learning-system")
    service_version = service_version or "3.2"
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # 如果追踪未启用，使用NoOp tracer
    if not os.getenv("TRACING_ENABLED", "true").lower() == "true":
        trace.set_tracer_provider(trace.NoOpTracerProvider())
        logger.info("分布式追踪已禁用")
        return
    
    try:
        # 创建资源
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # 创建TracerProvider
        tracer_provider = TracerProvider(resource=resource)
        
        # 配置导出器
        processors = []
        
        # OTLP导出器（推荐用于生产环境）
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
                processors.append(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP追踪导出器已配置: {otlp_endpoint}")
            except Exception as e:
                logger.error(f"配置OTLP导出器失败: {e}")
        
        # 控制台导出器（用于开发和调试）
        if console_export or os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
            console_exporter = ConsoleSpanExporter()
            processors.append(BatchSpanProcessor(console_exporter))
            logger.info("控制台追踪导出器已配置")
        
        # 如果没有配置任何导出器，使用控制台导出器作为默认
        if not processors:
            console_exporter = ConsoleSpanExporter()
            processors.append(BatchSpanProcessor(console_exporter))
            logger.info("使用默认控制台导出器")
        
        # 添加处理器到TracerProvider
        for processor in processors:
            tracer_provider.add_span_processor(processor)
        
        # 设置全局TracerProvider
        trace.set_tracer_provider(tracer_provider)
        
        # 获取追踪器
        _tracer = trace.get_tracer(__name__)
        
        # 注意: FastAPI自动装配需要在app创建后调用，这里只装配Requests
        _setup_requests_instrumentation()
        
        _is_initialized = True
        logger.info(f"OpenTelemetry追踪初始化成功: {service_name} v{service_version}")
        
    except Exception as e:
        logger.error(f"初始化OpenTelemetry追踪失败: {e}")
        # 降级到NoOp tracer
        trace.set_tracer_provider(trace.NoOpTracerProvider())


def _setup_requests_instrumentation():
    """设置Requests自动装配"""
    try:
        # Requests自动装配（不依赖app实例）
        RequestsInstrumentor().instrument()
        logger.info("Requests自动装配已启用")
        
    except Exception as e:
        logger.error(f"设置Requests自动装配失败: {e}")


def setup_fastapi_instrumentation(app):
    """设置FastAPI自动装配（需要在app创建后调用）"""
    try:
        # FastAPI自动装配需要传递app实例
        FastAPIInstrumentor().instrument_app(app)
        logger.info("FastAPI自动装配已启用")
        
    except Exception as e:
        logger.error(f"设置FastAPI自动装配失败: {e}")


def get_tracer() -> trace.Tracer:
    """获取追踪器"""
    global _tracer
    
    if not _is_initialized:
        initialize_tracing()
    
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    
    return _tracer


def trace_function(
    operation_name: str = None,
    span_kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: Dict[str, Any] = None
):
    """
    函数追踪装饰器
    
    Args:
        operation_name: 操作名称，默认使用函数名
        span_kind: Span类型
        attributes: 额外属性
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(
                op_name,
                kind=span_kind,
                attributes=attributes or {}
            ) as span:
                # 添加函数信息
                span.set_attributes({
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                    "function.args_count": len(args),
                    "function.kwargs_count": len(kwargs)
                })
                
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    
                    # 记录执行时间
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(
                op_name,
                kind=span_kind,
                attributes=attributes or {}
            ) as span:
                # 添加函数信息
                span.set_attributes({
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                    "function.args_count": len(args),
                    "function.kwargs_count": len(kwargs)
                })
                
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    
                    # 记录执行时间
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # 根据函数类型返回对应的包装器
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def trace_langchain_workflow(workflow_name: str):
    """
    LangChain工作流追踪装饰器
    
    Args:
        workflow_name: 工作流名称
    """
    return trace_function(
        operation_name=f"langchain.workflow.{workflow_name}",
        span_kind=trace.SpanKind.INTERNAL,
        attributes={
            "workflow.name": workflow_name,
            "workflow.type": "langchain"
        }
    )


def trace_tool_call(tool_name: str):
    """
    工具调用追踪装饰器
    
    Args:
        tool_name: 工具名称
    """
    return trace_function(
        operation_name=f"agent.tool.{tool_name}",
        span_kind=trace.SpanKind.CLIENT,
        attributes={
            "tool.name": tool_name,
            "tool.type": "agent_tool"
        }
    )


def trace_llm_call(model_name: str, provider: str = "unknown"):
    """
    LLM调用追踪装饰器
    
    Args:
        model_name: 模型名称
        provider: 提供商名称
    """
    return trace_function(
        operation_name=f"llm.{provider}.{model_name}",
        span_kind=trace.SpanKind.CLIENT,
        attributes={
            "llm.model": model_name,
            "llm.provider": provider,
            "llm.type": "completion"
        }
    )


@contextmanager
def trace_span(
    name: str,
    attributes: Dict[str, Any] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    上下文管理器形式的Span追踪
    
    Args:
        name: Span名称
        attributes: 属性字典
        kind: Span类型
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attribute(key: str, value: Any):
    """向当前活跃的Span添加属性"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, value)


def add_span_event(name: str, attributes: Dict[str, Any] = None):
    """向当前活跃的Span添加事件"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def record_span_exception(exception: Exception):
    """记录异常到当前Span"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.record_exception(exception)


class TracingContext:
    """追踪上下文管理器"""
    
    def __init__(self, operation_name: str, **attributes):
        self.operation_name = operation_name
        self.attributes = attributes
        self.span = None
        self.tracer = get_tracer()
    
    def __enter__(self):
        self.span = self.tracer.start_span(
            self.operation_name,
            attributes=self.attributes
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))
            
            self.span.end()


def get_trace_id() -> str:
    """获取当前追踪ID"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        trace_id = current_span.get_span_context().trace_id
        return format(trace_id, '032x')
    return ""


def get_span_id() -> str:
    """获取当前SpanID"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_id = current_span.get_span_context().span_id
        return format(span_id, '016x')
    return ""


def create_child_span(name: str, attributes: Dict[str, Any] = None):
    """创建子Span"""
    tracer = get_tracer()
    return tracer.start_span(name, attributes=attributes or {})


def shutdown_tracing():
    """关闭追踪系统"""
    global _is_initialized
    
    if not _is_initialized:
        return
    
    try:
        # 获取TracerProvider并关闭
        provider = trace.get_tracer_provider()
        if hasattr(provider, 'shutdown'):
            provider.shutdown()
        
        logger.info("OpenTelemetry追踪已关闭")
        _is_initialized = False
        
    except Exception as e:
        logger.error(f"关闭追踪系统失败: {e}")


# 便捷的追踪工具函数
def trace_conversation_flow(session_id: str, topic: str):
    """追踪对话流程"""
    return trace_span(
        "conversation.flow",
        attributes={
            "conversation.session_id": session_id,
            "conversation.topic": topic,
            "conversation.type": "feynman_learning"
        }
    )


def trace_memory_operation(operation: str, memory_type: str = "short_term"):
    """追踪记忆操作"""
    return trace_span(
        f"memory.{operation}",
        attributes={
            "memory.operation": operation,
            "memory.type": memory_type
        }
    )


def trace_knowledge_retrieval(query: str, source: str = "chromadb"):
    """追踪知识检索"""
    return trace_span(
        "knowledge.retrieval",
        attributes={
            "knowledge.query": query[:100],  # 截断长查询
            "knowledge.source": source
        }
    )




