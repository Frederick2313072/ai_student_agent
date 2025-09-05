"""
监控中间件 - FastAPI请求监控、指标收集、日志记录
"""

import time
import uuid
import asyncio
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp

from feynman.infrastructure.monitoring.metrics.prometheus import (
    API_REQUESTS_TOTAL, API_REQUEST_DURATION, API_ACTIVE_CONNECTIONS,
    SSE_CONNECTIONS_ACTIVE, SSE_MESSAGES_TOTAL, SSE_DISCONNECTS_TOTAL,
    SSE_CONNECTION_DURATION
)
from feynman.infrastructure.monitoring.logging.structured import (
    set_request_context, clear_request_context, log_api_request, get_logger
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件 - 收集API指标和日志"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.monitoring")
        self.active_streams = {}  # 跟踪活跃的流式连接
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集监控数据"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 提取会话信息
        session_id = self._extract_session_id(request)
        user_id = self._extract_user_id(request)
        
        # 设置上下文
        set_request_context(
            request_id=request_id,
            session_id=session_id,
            user_id=user_id
        )
        
        # 将请求ID添加到request状态中
        request.state.request_id = request_id
        request.state.session_id = session_id
        request.state.start_time = start_time
        
        # 增加活跃连接数
        API_ACTIVE_CONNECTIONS.inc()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            duration = time.time() - start_time
            
            # 记录指标
            self._record_metrics(request, response, duration)
            
            # 记录日志
            self._log_request(request, response, duration)
            
            # 处理流式响应的特殊监控
            if self._is_streaming_response(response):
                response = await self._wrap_streaming_response(response, request, session_id)
            
            return response
            
        except Exception as e:
            # 处理异常
            duration = time.time() - start_time
            
            # 记录错误指标
            API_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=500
            ).inc()
            
            # 记录错误日志
            self.logger.error(
                f"请求处理异常: {str(e)}",
                extra={
                    "error": str(e),
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": duration * 1000
                }
            )
            
            raise
            
        finally:
            # 清理
            API_ACTIVE_CONNECTIONS.dec()
            clear_request_context()
    
    def _extract_session_id(self, request: Request) -> str:
        """从请求中提取会话ID"""
        # 尝试从不同地方获取session_id
        session_id = None
        
        # 1. 从header获取
        session_id = request.headers.get("X-Session-ID")
        
        # 2. 从query参数获取
        if not session_id:
            session_id = request.query_params.get("session_id")
        
        # 3. 从请求体获取（对于POST请求）
        if not session_id and request.method == "POST":
            # 这里不能直接读取body，因为会影响后续处理
            # 在实际应用中，session_id通常通过header或query传递
            pass
        
        # 4. 如果都没有，生成一个新的
        if not session_id:
            session_id = f"auto-{uuid.uuid4().hex[:8]}"
        
        return session_id
    
    def _extract_user_id(self, request: Request) -> str:
        """从请求中提取用户ID"""
        # 尝试从header获取用户ID
        user_id = request.headers.get("X-User-ID")
        
        # 如果没有认证信息，使用匿名用户
        if not user_id:
            user_id = "anonymous"
        
        return user_id
    
    def _get_endpoint_name(self, request: Request) -> str:
        """获取端点名称"""
        path = request.url.path
        
        # 简化路径名称用于指标标签
        if path.startswith("/api/v1/chat"):
            if "stream" in path:
                return "/api/v1/chat/stream"
            elif "memorize" in path:
                return "/api/v1/chat/memorize"
            else:
                return "/api/v1/chat"
        elif path.startswith("/health"):
            return "/health"
        elif path.startswith("/metrics"):
            return "/metrics"
        elif path == "/":
            return "/"
        else:
            return "other"
    
    def _record_metrics(self, request: Request, response: Response, duration: float):
        """记录Prometheus指标"""
        endpoint = self._get_endpoint_name(request)
        status_code = response.status_code
        
        # 记录请求计数
        API_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        # 记录响应时间
        API_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
    
    def _log_request(self, request: Request, response: Response, duration: float):
        """记录结构化日志"""
        log_api_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration * 1000,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host if request.client else None
        )
    
    def _is_streaming_response(self, response: Response) -> bool:
        """判断是否为流式响应"""
        return isinstance(response, StreamingResponse)
    
    async def _wrap_streaming_response(
        self, 
        response: StreamingResponse, 
        request: Request, 
        session_id: str
    ) -> StreamingResponse:
        """包装流式响应以进行监控"""
        original_iterator = response.body_iterator
        stream_start_time = time.time()
        message_count = 0
        
        # 增加活跃流式连接数
        SSE_CONNECTIONS_ACTIVE.inc()
        self.active_streams[session_id] = stream_start_time
        
        async def monitored_stream():
            nonlocal message_count
            disconnect_reason = "completed"
            
            try:
                async for chunk in original_iterator:
                    message_count += 1
                    
                    # 记录消息数
                    SSE_MESSAGES_TOTAL.labels(session_id=session_id).inc()
                    
                    yield chunk
                    
            except asyncio.CancelledError:
                disconnect_reason = "cancelled"
                raise
            except Exception as e:
                disconnect_reason = "error"
                self.logger.error(
                    f"流式响应异常: {str(e)}",
                    extra={"session_id": session_id, "error": str(e)}
                )
                raise
            finally:
                # 记录连接结束
                stream_duration = time.time() - stream_start_time
                
                SSE_CONNECTIONS_ACTIVE.dec()
                SSE_DISCONNECTS_TOTAL.labels(reason=disconnect_reason).inc()
                SSE_CONNECTION_DURATION.observe(stream_duration)
                
                # 清理跟踪
                if session_id in self.active_streams:
                    del self.active_streams[session_id]
                
                # 记录流式响应日志
                self.logger.info(
                    f"流式响应结束",
                    extra={
                        "session_id": session_id,
                        "duration_seconds": stream_duration,
                        "message_count": message_count,
                        "disconnect_reason": disconnect_reason
                    }
                )
        
        # 创建新的StreamingResponse
        return StreamingResponse(
            monitored_stream(),
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.media_type
        )
    
    def get_active_streams(self) -> dict:
        """获取当前活跃的流式连接信息"""
        current_time = time.time()
        return {
            session_id: {
                "duration_seconds": current_time - start_time,
                "start_time": start_time
            }
            for session_id, start_time in self.active_streams.items()
        }


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""
    
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB默认
        super().__init__(app)
        self.max_size = max_size
        self.logger = get_logger("api.request_limit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查Content-Length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    self.logger.warning(
                        f"请求大小超过限制",
                        extra={
                            "content_length": size,
                            "max_size": self.max_size,
                            "path": str(request.url.path)
                        }
                    )
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=413,
                        detail=f"请求大小超过限制 {self.max_size} 字节"
                    )
            except ValueError:
                pass
        
        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """请求超时中间件"""
    
    def __init__(self, app: ASGIApp, timeout_seconds: float = 300):  # 5分钟默认
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger("api.timeout")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            self.logger.error(
                f"请求超时",
                extra={
                    "timeout_seconds": self.timeout_seconds,
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=408,
                detail=f"请求超时 ({self.timeout_seconds}秒)"
            )

