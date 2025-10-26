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
    # 从环境变量获取CORS配置；默认包含常见本地端口(React/Vite/Streamlit)
    cors_origins_str = os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8501", "http://127.0.0.1:8501"]'
    )
    
    try:
        # 尝试解析JSON格式的origins
        import json
        cors_origins = json.loads(cors_origins_str)
    except (json.JSONDecodeError, TypeError):
        # 如果解析失败，使用逗号分割
        cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
    
    # 注意：当 allow_credentials=True 时，浏览器不允许通配符 *，因此显式列出常用开发来源
    # 如果仍需放宽，请在 .env 中设置 CORS_ORIGINS 覆盖
    
    # 如果未显式配置，则放宽为允许所有来源（开发场景更友好）。
    # 注意：当 allow_credentials=True 时不允许使用 "*"，此处关闭凭据支持以兼容任意来源预检
    if not os.getenv("CORS_ORIGINS"):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Session-ID"]
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins + ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Session-ID"]
        )

