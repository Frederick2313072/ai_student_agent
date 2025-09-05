"""
CORS中间件配置 - 跨域资源共享设置
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List


def setup_cors(app: FastAPI) -> None:
    """
    配置CORS中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 从环境变量获取CORS配置
    cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8501"]')
    
    try:
        # 尝试解析JSON格式的origins
        import json
        cors_origins = json.loads(cors_origins_str)
    except (json.JSONDecodeError, TypeError):
        # 如果解析失败，使用逗号分割
        cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
    
    # 开发环境允许所有来源
    if os.getenv("ENVIRONMENT", "development") == "development":
        cors_origins.append("*")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Session-ID"]
    )

