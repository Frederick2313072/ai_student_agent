"""
AI学生费曼学习系统 - 主启动文件
使用LangGraph架构构建的智能学习助手，集成全面的监控与追踪功能
"""
from dotenv import load_dotenv

# 在所有其他导入之前加载环境变量，确保配置在模块初始化时可用
load_dotenv('environments/test.env')

import os
import uuid
from fastapi import FastAPI
from feynman.api.v1.endpoints.chat import router as chat_router
from feynman.api.v1.endpoints.monitoring import router as monitoring_router
from feynman.api.v1.endpoints.config import router as config_router
from feynman.api.v1.endpoints.knowledge_graph import router as knowledge_graph_router
from feynman.api.middleware.monitoring import MonitoringMiddleware, RequestSizeLimitMiddleware, RequestTimeoutMiddleware
from feynman.api.middleware.cors import setup_cors
from feynman.infrastructure.monitoring.logging.structured import setup_structured_logging

# 导入OpenTelemetry装配函数
try:
    from feynman.infrastructure.monitoring.tracing.otlp import setup_fastapi_instrumentation
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

setup_structured_logging()

app = FastAPI(
    title="Feynman Student Agent API",
    description="基于费曼学习法的AI学生Agent",
    version="3.2"
)

setup_cors(app)

# 中间件配置
if os.getenv("REQUEST_TIMEOUT_ENABLED", "true").lower() == "true":
    timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))
    app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=timeout_seconds)

if os.getenv("REQUEST_SIZE_LIMIT_ENABLED", "true").lower() == "true":
    max_size = int(os.getenv("MAX_REQUEST_SIZE_BYTES", "10485760"))
    app.add_middleware(RequestSizeLimitMiddleware, max_size=max_size)

if os.getenv("MONITORING_ENABLED", "true").lower() == "true":
    app.add_middleware(MonitoringMiddleware)

# 注册路由
app.include_router(chat_router, prefix="/api/v1/chat", tags=["对话"])
app.include_router(monitoring_router, tags=["监控"])
app.include_router(config_router, tags=["配置"])
app.include_router(knowledge_graph_router, prefix="/api/v1/kg", tags=["知识图谱"])


@app.get("/")
def read_root():
    return {
        "message": "费曼学生Agent API",
        "version": "3.2",
        "docs": "/docs",
        "health": "/health",
        "config": "/config/health"
    }


@app.on_event("startup")
async def startup_event():
    from feynman.infrastructure.monitoring.logging.structured import get_logger
    logger = get_logger("app.startup")
    
    # 设置OpenTelemetry FastAPI装配（在app启动后）
    if OTEL_AVAILABLE and os.getenv("TRACING_ENABLED", "false").lower() == "true":
        try:
            setup_fastapi_instrumentation(app)
            logger.info("OpenTelemetry FastAPI装配已完成")
        except Exception as e:
            logger.warning(f"OpenTelemetry FastAPI装配失败: {e}")
    
    logger.info("费曼学习系统启动", extra={"version": "3.2"})

@app.on_event("shutdown")
async def shutdown_event():
    from feynman.infrastructure.monitoring.logging.structured import get_logger
    logger = get_logger("app.shutdown")
    logger.info("费曼学习系统关闭")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    from feynman.infrastructure.monitoring.logging.structured import get_logger
    
    logger = get_logger("app.exception")
    logger.error(f"异常: {str(exc)}", extra={
        "type": type(exc).__name__,
        "path": str(request.url.path)
    })
    
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": "内部服务器错误"})


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print(f"🚀 启动费曼学习系统 API 服务器")
    print(f"   地址: http://{host}:{port}")
    print(f"   文档: http://{host}:{port}/docs")
    print(f"   重载: {reload}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

