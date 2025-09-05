"""
结构化日志模块 - 提供JSON格式的结构化日志记录
支持请求ID、会话ID、用户ID等上下文信息
"""

import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextvars import ContextVar

# 上下文变量用于存储请求相关信息
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        # 基础日志信息
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加上下文信息
        if request_id_var.get():
            log_entry["request_id"] = request_id_var.get()
        if session_id_var.get():
            log_entry["session_id"] = session_id_var.get()
        if user_id_var.get():
            log_entry["user_id"] = user_id_var.get()
            
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # 添加自定义字段
        if hasattr(record, 'extra') and record.extra:
            log_entry["extra"] = record.extra
            
        # 从record中提取其他自定义属性
        custom_attrs = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'levelno', 'levelname', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName',
                          'process', 'exc_info', 'exc_text', 'stack_info', 'msg',
                          'args', 'extra']:
                custom_attrs[key] = value
        
        if custom_attrs:
            log_entry.update(custom_attrs)
            
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ContextualAdapter(logging.LoggerAdapter):
    """带上下文的日志适配器"""
    
    def process(self, msg, kwargs):
        # 自动添加上下文信息
        extra = kwargs.get('extra', {})
        
        if request_id_var.get():
            extra['request_id'] = request_id_var.get()
        if session_id_var.get():
            extra['session_id'] = session_id_var.get()
        if user_id_var.get():
            extra['user_id'] = user_id_var.get()
            
        kwargs['extra'] = extra
        return msg, kwargs


def setup_structured_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: str = None
) -> None:
    """
    配置结构化日志
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式 ('json' 或 'text')
        log_file: 日志文件路径 (可选)
    """
    # 从环境变量获取配置
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = log_format or os.getenv("LOG_FORMAT", "json").lower()
    log_file = log_file or os.getenv("LOG_FILE")
    
    # 清除现有的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 选择格式化器
    if log_format == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 配置控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 配置文件输出（如果指定）
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 设置日志级别
    root_logger.setLevel(getattr(logging, log_level))
    
    # 配置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> ContextualAdapter:
    """
    获取带上下文的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        ContextualAdapter: 带上下文的日志适配器
    """
    logger = logging.getLogger(name)
    return ContextualAdapter(logger, {})


def set_request_context(
    request_id: str = None,
    session_id: str = None,
    user_id: str = None
) -> None:
    """
    设置请求上下文信息
    
    Args:
        request_id: 请求ID
        session_id: 会话ID  
        user_id: 用户ID
    """
    if request_id:
        request_id_var.set(request_id)
    if session_id:
        session_id_var.set(session_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """清除请求上下文信息"""
    request_id_var.set(None)
    session_id_var.set(None)
    user_id_var.set(None)


# 便捷的日志记录函数
def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_agent: str = None,
    ip: str = None
) -> None:
    """记录API请求日志"""
    logger = get_logger("api.request")
    logger.info("API请求", extra={
        "event": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "user_agent": user_agent,
        "ip": ip
    })


def log_tool_call(
    tool_name: str,
    success: bool,
    duration_ms: float,
    error: str = None,
    input_args: Dict[str, Any] = None,
    output_length: int = None
) -> None:
    """记录工具调用日志"""
    logger = get_logger("agent.tool")
    
    extra = {
        "event": "tool_call",
        "tool_name": tool_name,
        "success": success,
        "duration_ms": duration_ms
    }
    
    if error:
        extra["error"] = error
    if input_args:
        extra["input_args"] = str(input_args)[:500]  # 截断长参数
    if output_length is not None:
        extra["output_length"] = output_length
    
    if success:
        logger.info(f"工具调用成功: {tool_name}", extra=extra)
    else:
        logger.error(f"工具调用失败: {tool_name}", extra=extra)


def log_llm_call(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float,
    cost_usd: float = None
) -> None:
    """记录LLM调用日志"""
    logger = get_logger("llm.call")
    logger.info("LLM调用", extra={
        "event": "llm_call",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "duration_ms": duration_ms,
        "cost_usd": cost_usd
    })


def log_workflow_execution(
    node_name: str,
    success: bool,
    duration_ms: float,
    input_topic: str = None,
    output_questions_count: int = None,
    error: str = None
) -> None:
    """记录工作流执行日志"""
    logger = get_logger("workflow.execution")
    
    extra = {
        "event": "workflow_execution",
        "node_name": node_name,
        "success": success,
        "duration_ms": duration_ms
    }
    
    if input_topic:
        extra["input_topic"] = input_topic
    if output_questions_count is not None:
        extra["output_questions_count"] = output_questions_count
    if error:
        extra["error"] = error
    
    if success:
        logger.info(f"工作流节点执行成功: {node_name}", extra=extra)
    else:
        logger.error(f"工作流节点执行失败: {node_name}", extra=extra)

