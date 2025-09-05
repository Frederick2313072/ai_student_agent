"""
配置管理API - 配置验证、状态检查、动态更新

提供RESTful接口来管理系统配置，包括验证、查看和更新功能。
"""

import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from feynman.core.config.settings import (
    validate_configuration, get_settings, get_api_key_setup_guide,
    FeynmanSettings
)


router = APIRouter()


class ConfigValidationResponse(BaseModel):
    """配置验证响应模型"""
    environment: str
    llm_available: bool
    monitoring_enabled: bool
    tools_status: Dict[str, str]
    warnings: List[str]
    errors: List[str]
    recommendations: List[str] = []


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    key: str
    value: str
    restart_required: bool = True


@router.get("/config/validation", response_model=ConfigValidationResponse)
async def get_config_validation():
    """获取当前配置验证结果"""
    try:
        results = validate_configuration()
        
        # 添加建议
        recommendations = []
        if not results["llm_available"]:
            recommendations.append("设置OpenAI或智谱AI密钥以启用核心功能")
        
        if not results["monitoring_enabled"]:
            recommendations.append("启用监控以获得更好的可观测性")
        
        # 检查工具配置完整性
        missing_tools = [name for name, status in results["tools_status"].items() 
                        if "未配置" in status]
        if missing_tools:
            recommendations.append(f"配置更多工具API密钥以增强功能: {', '.join(missing_tools[:3])}")
        
        return ConfigValidationResponse(
            **results,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")


@router.get("/config/status")
async def get_config_status():
    """获取当前配置状态摘要"""
    try:
        settings = get_settings()
        
        # 统计可用功能
        llm_providers = []
        if settings.openai_api_key:
            llm_providers.append("OpenAI")
        if settings.zhipu_api_key:
            llm_providers.append("智谱AI")
        
        tool_count = sum([
            bool(settings.tavily_api_key),
            bool(settings.baidu_translate_api_key),
            bool(settings.wolfram_api_key),
            bool(settings.youtube_api_key),
            bool(settings.news_api_key),
            bool(settings.judge0_api_key),
            bool(settings.quickchart_api_key)
        ])
        
        monitoring_features = []
        if settings.monitoring_enabled:
            monitoring_features.append("基础监控")
        if settings.langfuse_public_key:
            monitoring_features.append("LangFuse追踪")
        if settings.tracing_enabled:
            monitoring_features.append("分布式追踪")
        
        return {
            "environment": settings.environment.value,
            "status": "运行中",
            "llm_providers": llm_providers,
            "available_tools": tool_count,
            "monitoring_features": monitoring_features,
            "cost_tracking": settings.cost_tracking_enabled,
            "daily_cost_limit": settings.daily_cost_limit_usd if settings.cost_tracking_enabled else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")


@router.get("/config/guide")
async def get_setup_guide():
    """获取API密钥设置指南"""
    return {
        "title": "API密钥设置指南",
        "guide": get_api_key_setup_guide(),
        "quick_links": {
            "OpenAI": "https://platform.openai.com/api-keys",
            "智谱AI": "https://open.bigmodel.cn/",
            "Tavily": "https://tavily.com",
            "百度翻译": "https://fanyi-api.baidu.com",
            "LangFuse": "https://langfuse.com"
        }
    }


@router.get("/config/health")
async def get_config_health():
    """配置健康检查 - 快速状态概览"""
    try:
        settings = get_settings()
        
        # 基础健康检查
        health_status = {
            "status": "healthy",
            "checks": {},
            "score": 0,
            "max_score": 10
        }
        
        # LLM配置检查 (4分)
        if settings.openai_api_key or settings.zhipu_api_key:
            health_status["checks"]["llm_configured"] = True
            health_status["score"] += 4
        else:
            health_status["checks"]["llm_configured"] = False
            health_status["status"] = "unhealthy"
        
        # 搜索工具检查 (2分)
        if settings.tavily_api_key:
            health_status["checks"]["search_enabled"] = True
            health_status["score"] += 2
        else:
            health_status["checks"]["search_enabled"] = False
        
        # 监控配置检查 (2分)
        if settings.monitoring_enabled:
            health_status["checks"]["monitoring_enabled"] = True
            health_status["score"] += 2
        else:
            health_status["checks"]["monitoring_enabled"] = False
        
        # 追踪配置检查 (1分)
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            health_status["checks"]["tracing_configured"] = True
            health_status["score"] += 1
        else:
            health_status["checks"]["tracing_configured"] = False
        
        # 成本控制检查 (1分)
        if settings.cost_tracking_enabled and settings.daily_cost_limit_usd > 0:
            health_status["checks"]["cost_control_enabled"] = True
            health_status["score"] += 1
        else:
            health_status["checks"]["cost_control_enabled"] = False
        
        # 确定整体状态
        if health_status["score"] >= 8:
            health_status["status"] = "excellent"
        elif health_status["score"] >= 6:
            health_status["status"] = "good"
        elif health_status["score"] >= 4:
            health_status["status"] = "fair"
        elif health_status["score"] >= 2:
            health_status["status"] = "poor"
        else:
            health_status["status"] = "critical"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "score": 0,
            "max_score": 10
        }


@router.post("/config/validate")
async def validate_config_endpoint():
    """API端点形式的配置验证"""
    try:
        results = validate_configuration()
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置验证失败: {str(e)}")


@router.get("/config/environment")
async def get_environment_info():
    """获取当前环境信息"""
    try:
        settings = get_settings()
        
        return {
            "environment": settings.environment.value,
            "debug": settings.debug,
            "api_configuration": {
                "host": settings.api_host,
                "port": settings.api_port,
                "reload": settings.api_reload,
                "workers": settings.api_workers
            },
            "feature_flags": {
                "monitoring": settings.monitoring_enabled,
                "metrics": settings.metrics_enabled,
                "tracing": settings.tracing_enabled,
                "cost_tracking": settings.cost_tracking_enabled
            },
            "resource_limits": {
                "request_timeout_seconds": settings.request_timeout_seconds,
                "max_request_size_bytes": settings.max_request_size_bytes,
                "daily_cost_limit_usd": settings.daily_cost_limit_usd
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境信息失败: {str(e)}")
