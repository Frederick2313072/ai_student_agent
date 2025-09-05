"""
Prometheus指标模块 - 定义和收集各种系统指标
包括API性能、工具调用、LLM使用、工作流执行等指标
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
import time
import psutil
import os
from typing import Dict, List, Optional
from functools import wraps
import asyncio


# 创建指标注册表
REGISTRY = CollectorRegistry()

# ======================
# 系统资源指标
# ======================

# 系统资源
SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'CPU使用率百分比',
    registry=REGISTRY
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_bytes', 
    '内存使用量(字节)',
    registry=REGISTRY
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    '磁盘使用量(字节)', 
    ['mount_point'],
    registry=REGISTRY
)

# 进程资源
PROCESS_CPU_USAGE = Gauge(
    'process_cpu_usage_percent',
    '进程CPU使用率',
    registry=REGISTRY
)

PROCESS_MEMORY_USAGE = Gauge(
    'process_memory_usage_bytes',
    '进程内存使用量',
    registry=REGISTRY
)

PROCESS_OPEN_FILES = Gauge(
    'process_open_files_count',
    '进程打开文件数',
    registry=REGISTRY
)

# ======================
# API性能指标  
# ======================

# API请求
API_REQUESTS_TOTAL = Counter(
    'fastapi_requests_total',
    'API请求总数',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

API_REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'API请求持续时间(秒)',
    ['method', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')),
    registry=REGISTRY
)

API_ACTIVE_CONNECTIONS = Gauge(
    'fastapi_active_connections',
    '当前活跃连接数',
    registry=REGISTRY
)

# 流式响应
SSE_CONNECTIONS_ACTIVE = Gauge(
    'sse_connections_active',
    '活跃SSE连接数',
    registry=REGISTRY
)

SSE_MESSAGES_TOTAL = Counter(
    'sse_messages_total',
    'SSE消息总数',
    ['session_id'],
    registry=REGISTRY
)

SSE_DISCONNECTS_TOTAL = Counter(
    'sse_disconnects_total',
    'SSE断开连接总数',
    ['reason'],
    registry=REGISTRY
)

SSE_CONNECTION_DURATION = Histogram(
    'sse_connection_duration_seconds',
    'SSE连接持续时间(秒)',
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, float('inf')),
    registry=REGISTRY
)

# ======================
# LangGraph工作流指标
# ======================

WORKFLOW_EXECUTIONS_TOTAL = Counter(
    'langgraph_workflow_executions_total',
    'LangGraph工作流执行总数',
    ['node_name', 'status'],
    registry=REGISTRY
)

WORKFLOW_DURATION = Histogram(
    'langgraph_workflow_duration_seconds',
    'LangGraph工作流执行时间(秒)',
    ['node_name'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0, float('inf')),
    registry=REGISTRY
)

WORKFLOW_QUEUE_SIZE = Gauge(
    'langgraph_workflow_queue_size',
    '工作流队列大小',
    registry=REGISTRY
)

# ======================
# 工具调用指标
# ======================

TOOL_CALLS_TOTAL = Counter(
    'agent_tool_calls_total',
    '工具调用总数',
    ['tool_name', 'status'],
    registry=REGISTRY
)

TOOL_CALL_DURATION = Histogram(
    'agent_tool_call_duration_seconds',
    '工具调用持续时间(秒)',
    ['tool_name'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf')),
    registry=REGISTRY
)

TOOL_ERRORS_TOTAL = Counter(
    'agent_tool_errors_total',
    '工具调用错误总数',
    ['tool_name', 'error_type'],
    registry=REGISTRY
)

# ======================
# 外部API指标
# ======================

EXTERNAL_API_REQUESTS_TOTAL = Counter(
    'external_api_requests_total',
    '外部API请求总数',
    ['service', 'endpoint', 'status_code'],
    registry=REGISTRY
)

EXTERNAL_API_DURATION = Histogram(
    'external_api_request_duration_seconds',
    '外部API请求持续时间(秒)',
    ['service', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf')),
    registry=REGISTRY
)

EXTERNAL_API_ERRORS_TOTAL = Counter(
    'external_api_errors_total',
    '外部API错误总数',
    ['service', 'error_type'],
    registry=REGISTRY
)

EXTERNAL_API_QUOTA_REMAINING = Gauge(
    'external_api_quota_remaining',
    '外部API剩余配额',
    ['service'],
    registry=REGISTRY
)

# ======================
# LLM使用指标
# ======================

LLM_TOKENS_USED_TOTAL = Counter(
    'llm_tokens_used_total',
    'LLM Token使用总数',
    ['model', 'type'],  # type: prompt/completion
    registry=REGISTRY
)

LLM_COSTS_TOTAL = Counter(
    'llm_costs_total_usd',
    'LLM调用总成本(USD)',
    ['model', 'provider'],
    registry=REGISTRY
)

LLM_REQUESTS_TOTAL = Counter(
    'llm_requests_total',
    'LLM请求总数',
    ['model', 'status'],
    registry=REGISTRY
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM请求持续时间(秒)',
    ['model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0, float('inf')),
    registry=REGISTRY
)

# ======================
# 数据库指标
# ======================

DATABASE_CONNECTIONS_ACTIVE = Gauge(
    'database_connections_active',
    '活跃数据库连接数',
    ['database'],
    registry=REGISTRY
)

CHROMADB_QUERIES_TOTAL = Counter(
    'chromadb_queries_total',
    'ChromaDB查询总数',
    ['operation'],  # operation: query/add/delete/update
    registry=REGISTRY
)

CHROMADB_QUERY_DURATION = Histogram(
    'chromadb_query_duration_seconds',
    'ChromaDB查询持续时间(秒)',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, float('inf')),
    registry=REGISTRY
)

# ======================
# 业务指标
# ======================

CONVERSATIONS_TOTAL = Counter(
    'conversations_total',
    '对话总数',
    ['status'],  # status: completed/abandoned/error
    registry=REGISTRY
)

CONVERSATION_DURATION = Histogram(
    'conversation_duration_seconds',
    '对话持续时间(秒)',
    buckets=(30, 60, 120, 300, 600, 1200, 1800, 3600, float('inf')),
    registry=REGISTRY
)

MEMORY_OPERATIONS_TOTAL = Counter(
    'memory_operations_total',
    '记忆操作总数',
    ['operation', 'status'],  # operation: add/retrieve/update
    registry=REGISTRY
)

USER_SATISFACTION_SCORE = Histogram(
    'user_satisfaction_score',
    '用户满意度评分',
    buckets=(1, 2, 3, 4, 5, float('inf')),
    registry=REGISTRY
)

# ======================
# 系统信息
# ======================

SYSTEM_INFO = Info(
    'system_info',
    '系统信息',
    registry=REGISTRY
)

# 初始化系统信息
SYSTEM_INFO.info({
    'version': '3.2',
    'python_version': os.sys.version.split()[0],
    'platform': os.name,
    'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
})


# ======================
# 指标收集器类
# ======================

class SystemMetricsCollector:
    """系统指标收集器"""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def collect_system_metrics(self):
        """收集系统资源指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # 内存使用
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.used)
            
            # 磁盘使用
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    SYSTEM_DISK_USAGE.labels(mount_point=partition.mountpoint).set(usage.used)
                except PermissionError:
                    # 跳过无权限的分区
                    continue
            
            # 进程指标
            PROCESS_CPU_USAGE.set(self.process.cpu_percent())
            
            memory_info = self.process.memory_info()
            PROCESS_MEMORY_USAGE.set(memory_info.rss)
            
            try:
                PROCESS_OPEN_FILES.set(self.process.num_fds())
            except (AttributeError, psutil.AccessDenied):
                # Windows不支持num_fds或权限不足
                pass
                
        except Exception as e:
            # 记录错误但不中断服务
            print(f"采集系统指标时出错: {e}")
    
    async def start_collection(self, interval: int = 30):
        """启动定期指标收集"""
        while True:
            self.collect_system_metrics()
            await asyncio.sleep(interval)


# ======================
# 装饰器
# ======================

def monitor_api_call(endpoint: str = None):
    """
    API调用监控装饰器
    
    Args:
        endpoint: 端点名称，如果不提供则使用函数名
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            endpoint_name = endpoint or func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                API_REQUEST_DURATION.labels(
                    method="POST",  # 大多数API都是POST
                    endpoint=endpoint_name
                ).observe(duration)
                
                API_REQUESTS_TOTAL.labels(
                    method="POST",
                    endpoint=endpoint_name, 
                    status_code=200
                ).inc()
                
                return result
                
            except Exception as e:
                # 记录错误指标
                API_REQUESTS_TOTAL.labels(
                    method="POST",
                    endpoint=endpoint_name,
                    status_code=500
                ).inc()
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            endpoint_name = endpoint or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                API_REQUEST_DURATION.labels(
                    method="POST",
                    endpoint=endpoint_name
                ).observe(duration)
                
                API_REQUESTS_TOTAL.labels(
                    method="POST",
                    endpoint=endpoint_name,
                    status_code=200
                ).inc()
                
                return result
                
            except Exception as e:
                # 记录错误指标
                API_REQUESTS_TOTAL.labels(
                    method="POST",
                    endpoint=endpoint_name,
                    status_code=500
                ).inc()
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def monitor_tool_call(tool_name: str):
    """
    工具调用监控装饰器
    
    Args:
        tool_name: 工具名称
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status="success").inc()
                TOOL_CALL_DURATION.labels(tool_name=tool_name).observe(duration)
                
                return result
                
            except Exception as e:
                # 记录错误指标
                TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status="error").inc()
                TOOL_ERRORS_TOTAL.labels(
                    tool_name=tool_name,
                    error_type=type(e).__name__
                ).inc()
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status="success").inc()
                TOOL_CALL_DURATION.labels(tool_name=tool_name).observe(duration)
                
                return result
                
            except Exception as e:
                # 记录错误指标
                TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status="error").inc()
                TOOL_ERRORS_TOTAL.labels(
                    tool_name=tool_name,
                    error_type=type(e).__name__
                ).inc()
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def monitor_workflow_node(node_name: str):
    """
    工作流节点监控装饰器
    
    Args:
        node_name: 节点名称
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                WORKFLOW_EXECUTIONS_TOTAL.labels(node_name=node_name, status="success").inc()
                WORKFLOW_DURATION.labels(node_name=node_name).observe(duration)
                
                return result
                
            except Exception as e:
                # 记录错误指标
                WORKFLOW_EXECUTIONS_TOTAL.labels(node_name=node_name, status="error").inc()
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功指标
                duration = time.time() - start_time
                WORKFLOW_EXECUTIONS_TOTAL.labels(node_name=node_name, status="success").inc()
                WORKFLOW_DURATION.labels(node_name=node_name).observe(duration)
                
                return result
                
            except Exception as e:
                # 记录错误指标
                WORKFLOW_EXECUTIONS_TOTAL.labels(node_name=node_name, status="error").inc()
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ======================
# 便捷函数
# ======================

def record_conversation_start():
    """记录对话开始"""
    CONVERSATIONS_TOTAL.labels(status="started").inc()


def record_conversation_end(duration_seconds: float, status: str = "completed"):
    """
    记录对话结束
    
    Args:
        duration_seconds: 对话持续时间(秒)
        status: 对话状态 (completed/abandoned/error)
    """
    CONVERSATIONS_TOTAL.labels(status=status).inc()
    CONVERSATION_DURATION.observe(duration_seconds)


def record_llm_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_seconds: float,
    cost_usd: float = None,
    status: str = "success"
):
    """
    记录LLM使用情况
    
    Args:
        model: 模型名称
        prompt_tokens: 提示词token数
        completion_tokens: 回复token数
        duration_seconds: 请求持续时间
        cost_usd: 成本(美元)
        status: 请求状态
    """
    provider = "openai" if model.startswith("gpt") else "zhipu"
    
    LLM_TOKENS_USED_TOTAL.labels(model=model, type="prompt").inc(prompt_tokens)
    LLM_TOKENS_USED_TOTAL.labels(model=model, type="completion").inc(completion_tokens)
    LLM_REQUESTS_TOTAL.labels(model=model, status=status).inc()
    LLM_REQUEST_DURATION.labels(model=model).observe(duration_seconds)
    
    if cost_usd is not None:
        LLM_COSTS_TOTAL.labels(model=model, provider=provider).inc(cost_usd)


def record_memory_operation(operation: str, status: str = "success"):
    """
    记录记忆操作
    
    Args:
        operation: 操作类型 (add/retrieve/update)
        status: 操作状态 (success/error)
    """
    MEMORY_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()


def record_user_satisfaction(score: float):
    """
    记录用户满意度评分
    
    Args:
        score: 满意度评分 (1-5)
    """
    USER_SATISFACTION_SCORE.observe(score)


def get_registry():
    """获取指标注册表"""
    return REGISTRY

