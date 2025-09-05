"""
监控路由 - 健康检查、指标收集、系统状态等端点
"""

import asyncio
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import Response, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any, Optional

from feynman.infrastructure.monitoring.health.checker import HealthChecker
from feynman.infrastructure.monitoring.metrics.prometheus import get_registry, SystemMetricsCollector
from feynman.infrastructure.monitoring.cost.tracker import get_cost_tracker
from feynman.infrastructure.monitoring.logging.structured import get_logger


router = APIRouter()
logger = get_logger("api.monitoring")

# 全局健康检查器和指标收集器
health_checker = HealthChecker()
metrics_collector = SystemMetricsCollector()


@router.get("/health", summary="健康检查", tags=["监控"])
async def health_check():
    """
    完整的健康检查，返回系统各组件状态
    """
    try:
        health_data = await health_checker.run_all_checks()
        
        # 根据整体状态设置HTTP状态码
        status_code = 200
        if health_data["status"] in ["unhealthy", "unknown"]:
            status_code = 503
        elif health_data["status"] == "degraded":
            status_code = 200  # 降级但仍可服务
        
        return JSONResponse(
            content=health_data,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            content={
                "status": "unknown",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            },
            status_code=503
        )


@router.get("/health/ready", summary="就绪检查", tags=["监控"])
async def readiness_check():
    """
    就绪检查 - 适用于Kubernetes readiness probe
    只检查关键组件是否就绪
    """
    try:
        readiness_data = await health_checker.get_readiness()
        
        status_code = 200 if readiness_data["ready"] else 503
        
        return JSONResponse(
            content=readiness_data,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"就绪检查失败: {str(e)}")
        return JSONResponse(
            content={
                "ready": False,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            },
            status_code=503
        )


@router.get("/health/live", summary="存活检查", tags=["监控"])
async def liveness_check():
    """
    存活检查 - 适用于Kubernetes liveness probe
    简单检查进程是否存活
    """
    try:
        liveness_data = await health_checker.get_liveness()
        
        status_code = 200 if liveness_data["alive"] else 503
        
        return JSONResponse(
            content=liveness_data,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"存活检查失败: {str(e)}")
        return JSONResponse(
            content={
                "alive": False,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            },
            status_code=503
        )


@router.get("/metrics", summary="Prometheus指标", tags=["监控"])
async def get_metrics():
    """
    返回Prometheus格式的指标数据
    """
    try:
        # 更新系统指标
        metrics_collector.collect_system_metrics()
        
        # 生成Prometheus格式的指标
        registry = get_registry()
        metrics_data = generate_latest(registry)
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        logger.error(f"指标收集失败: {str(e)}")
        raise HTTPException(status_code=500, detail="指标收集失败")


@router.get("/monitoring/status", summary="监控状态概览", tags=["监控"])
async def monitoring_status():
    """
    获取监控系统状态概览
    """
    try:
        # 获取健康状态
        health_data = await health_checker.run_all_checks()
        
        # 获取成本状态
        cost_tracker = get_cost_tracker()
        budget_status = cost_tracker.get_budget_status()
        
        # 获取系统资源状态
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            "system_health": {
                "overall_status": health_data["status"],
                "checks_passed": len([c for c in health_data["checks"] if c["status"] == "healthy"]),
                "total_checks": len(health_data["checks"])
            },
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "available_memory_gb": round(memory.available / (1024**3), 2)
            },
            "cost_tracking": {
                "daily_budget_used_percent": budget_status["daily"]["percentage"],
                "monthly_budget_used_percent": budget_status["monthly"]["percentage"],
                "daily_cost_usd": budget_status["daily"]["used"],
                "monthly_cost_usd": budget_status["monthly"]["used"]
            },
            "monitoring_enabled": True,
            "timestamp": health_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取监控状态失败")


@router.get("/monitoring/costs", summary="成本统计", tags=["监控"])
async def get_cost_stats(
    days: Optional[int] = 7,
    session_id: Optional[str] = None
):
    """
    获取成本使用统计
    
    Args:
        days: 查看最近多少天的数据 (默认7天)
        session_id: 特定会话的成本 (可选)
    """
    try:
        cost_tracker = get_cost_tracker()
        
        if session_id:
            # 返回特定会话的成本
            session_cost = cost_tracker.get_session_cost(session_id)
            return {
                "session_id": session_id,
                "total_cost_usd": session_cost,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        else:
            # 返回整体统计
            budget_status = cost_tracker.get_budget_status()
            model_stats = cost_tracker.get_model_usage_stats()
            cost_trends = cost_tracker.get_cost_trends(days)
            
            return {
                "budget_status": budget_status,
                "model_usage": model_stats,
                "cost_trends": cost_trends,
                "period_days": days
            }
            
    except Exception as e:
        logger.error(f"获取成本统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取成本统计失败")


@router.get("/monitoring/costs/report", summary="成本报告", tags=["监控"])
async def get_cost_report(days: Optional[int] = 30):
    """
    生成详细的成本使用报告
    
    Args:
        days: 报告期间天数 (默认30天)
    """
    try:
        from datetime import date, timedelta
        
        cost_tracker = get_cost_tracker()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        report = cost_tracker.export_usage_report(start_date, end_date)
        
        return report
        
    except Exception as e:
        logger.error(f"生成成本报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="生成成本报告失败")


@router.get("/monitoring/streams", summary="流式连接状态", tags=["监控"])
async def get_streaming_status(request: Request):
    """
    获取当前活跃的流式连接状态
    """
    try:
        # 从中间件获取流式连接信息
        monitoring_middleware = None
        for middleware in request.app.middleware_stack:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'MonitoringMiddleware':
                monitoring_middleware = middleware
                break
        
        if monitoring_middleware:
            active_streams = monitoring_middleware.get_active_streams()
            return {
                "active_stream_count": len(active_streams),
                "active_streams": active_streams,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        else:
            return {
                "active_stream_count": 0,
                "active_streams": {},
                "timestamp": "2024-01-01T00:00:00Z",
                "note": "监控中间件未找到"
            }
            
    except Exception as e:
        logger.error(f"获取流式连接状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取流式连接状态失败")


@router.post("/monitoring/collect", summary="手动触发指标收集", tags=["监控"])
async def trigger_metrics_collection():
    """
    手动触发系统指标收集
    """
    try:
        metrics_collector.collect_system_metrics()
        
        return {
            "message": "指标收集完成",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"手动指标收集失败: {str(e)}")
        raise HTTPException(status_code=500, detail="指标收集失败")


# 启动时开始定期收集系统指标
@router.on_event("startup")
async def start_metrics_collection():
    """启动定期指标收集"""
    try:
        # 启动后台任务收集系统指标
        asyncio.create_task(metrics_collector.start_collection(interval=30))
        logger.info("系统指标收集已启动 (30秒间隔)")
    except Exception as e:
        logger.error(f"启动指标收集失败: {str(e)}")


# 关闭时清理资源
@router.on_event("shutdown")
async def cleanup_monitoring():
    """清理监控资源"""
    try:
        await health_checker.close()
        logger.info("监控资源清理完成")
    except Exception as e:
        logger.error(f"清理监控资源失败: {str(e)}")


# 可选：导出配置信息
@router.get("/monitoring/config", summary="监控配置信息", tags=["监控"])
async def get_monitoring_config():
    """
    获取当前监控配置信息
    """
    import os
    
    return {
        "monitoring_enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true",
        "metrics_enabled": os.getenv("METRICS_ENABLED", "true").lower() == "true",
        "tracing_enabled": os.getenv("TRACING_ENABLED", "true").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_format": os.getenv("LOG_FORMAT", "json"),
        "daily_cost_limit_usd": float(os.getenv("DAILY_COST_LIMIT_USD", "100")),
        "monthly_cost_limit_usd": float(os.getenv("MONTHLY_COST_LIMIT_USD", "1000")),
        "langfuse_enabled": bool(os.getenv("LANGFUSE_PUBLIC_KEY")),
        "prometheus_port": os.getenv("PROMETHEUS_PORT", "9090"),
        "otel_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    }

