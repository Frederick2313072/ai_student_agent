"""
配置管理模块 - 环境变量验证、配置加载、设置管理

提供统一的配置接口，支持多环境配置、验证和热重载功能。
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FeynmanSettings(BaseSettings):
    """费曼学习系统配置"""
    
    # 基础配置
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: LogLevel = LogLevel.INFO
    
    # API服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_workers: int = 1
    
    # LLM模型配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_base_url: Optional[str] = None
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    zhipu_api_key: Optional[str] = None
    zhipu_model: str = "glm-4.5-airx"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    
    # 第三方API配置
    tavily_api_key: Optional[str] = None
    baidu_translate_api_key: Optional[str] = None
    baidu_translate_secret_key: Optional[str] = None
    wolfram_api_key: Optional[str] = None
    youtube_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    judge0_api_key: Optional[str] = None
    quickchart_api_key: Optional[str] = None
    
    # 监控配置
    monitoring_enabled: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    prometheus_port: int = 9090
    
    # LangFuse配置
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # OpenTelemetry配置
    otel_service_name: str = "feynman-learning-system"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    
    # 成本控制
    daily_cost_limit_usd: float = 100.0
    monthly_cost_limit_usd: float = 1000.0
    cost_tracking_enabled: bool = True
    token_rate_limit: int = 10000
    
    # 请求限制
    request_timeout_enabled: bool = True
    request_timeout_seconds: float = 300.0
    request_size_limit_enabled: bool = True
    max_request_size_bytes: int = 10485760
    
    # CORS配置
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # 知识图谱配置
    kg_backend: str = Field("local", env="KG_BACKEND")
    kg_storage_path: str = Field("data/knowledge_graph.json", env="KG_STORAGE_PATH")
    kg_max_nodes: int = Field(1000, env="KG_MAX_NODES")
    kg_max_edges: int = Field(5000, env="KG_MAX_EDGES")
    
    # Neo4j配置
    neo4j_uri: Optional[str] = Field(None, env="NEO4J_URI")
    neo4j_username: Optional[str] = Field(None, env="NEO4J_USERNAME")
    neo4j_password: Optional[str] = Field(None, env="NEO4J_PASSWORD")
    neo4j_database: str = Field("neo4j", env="NEO4J_DATABASE")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('openai_api_key', 'zhipu_api_key')
    def validate_llm_keys(cls, v, values):
        # 至少需要一个LLM API密钥
        openai_key = values.get('openai_api_key')
        zhipu_key = values.get('zhipu_api_key')
        if not openai_key and not zhipu_key:
            print("⚠️  警告：未设置LLM API密钥，系统将以受限模式运行")
        return v
    
    class Config:
        env_file = [".env", "environments/test.env"]  # 优先级: .env > environments/test.env
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量，专注于核心配置


def load_settings(env_file: Optional[str] = None) -> FeynmanSettings:
    """加载配置设置"""
    if env_file:
        load_dotenv(env_file)
    
    return FeynmanSettings()


def validate_configuration(env_file: Optional[str] = None) -> Dict[str, Any]:
    """验证配置完整性"""
    print("🔍 正在验证配置...")
    
    settings = load_settings(env_file)
    
    validation_results = {
        "environment": settings.environment.value,
        "llm_available": bool(settings.openai_api_key or settings.zhipu_api_key),
        "monitoring_enabled": settings.monitoring_enabled,
        "tools_status": {},
        "warnings": [],
        "errors": []
    }
    
    # 验证LLM配置
    if settings.openai_api_key:
        validation_results["tools_status"]["openai"] = "✅ 已配置"
    elif settings.zhipu_api_key:
        validation_results["tools_status"]["zhipu"] = "✅ 已配置"
    else:
        validation_results["errors"].append("未设置任何LLM API密钥")
    
    # 验证工具API
    tool_apis = {
        "网络搜索": settings.tavily_api_key,
        "翻译功能": settings.baidu_translate_api_key and settings.baidu_translate_secret_key,
        "数学计算": settings.wolfram_api_key,
        "视频搜索": settings.youtube_api_key,
        "新闻搜索": settings.news_api_key,
        "代码执行": settings.judge0_api_key,
        "高级图表": settings.quickchart_api_key
    }
    
    for tool_name, api_key in tool_apis.items():
        if api_key:
            validation_results["tools_status"][tool_name] = "✅ 已配置"
        else:
            validation_results["tools_status"][tool_name] = "⚠️  未配置（功能受限）"
    
    # 验证监控配置
    if settings.monitoring_enabled:
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            validation_results["tools_status"]["LangFuse追踪"] = "✅ 已配置"
        else:
            validation_results["warnings"].append("监控已启用但LangFuse未配置")
    
    # 验证成本控制
    if settings.cost_tracking_enabled:
        if settings.daily_cost_limit_usd > 0:
            validation_results["tools_status"]["成本控制"] = f"✅ 每日限制: ${settings.daily_cost_limit_usd}"
        else:
            validation_results["warnings"].append("成本追踪已启用但未设置限制")
    
    # 打印验证结果
    print(f"\n📊 配置验证结果 ({settings.environment.value} 环境):")
    print(f"🔑 LLM可用: {'✅' if validation_results['llm_available'] else '❌'}")
    print(f"📈 监控启用: {'✅' if validation_results['monitoring_enabled'] else '❌'}")
    
    print(f"\n🛠️  工具状态:")
    for tool, status in validation_results["tools_status"].items():
        print(f"  {tool}: {status}")
    
    if validation_results["warnings"]:
        print(f"\n⚠️  警告:")
        for warning in validation_results["warnings"]:
            print(f"  - {warning}")
    
    if validation_results["errors"]:
        print(f"\n❌ 错误:")
        for error in validation_results["errors"]:
            print(f"  - {error}")
    
    return validation_results


def get_api_key_setup_guide() -> str:
    """返回API密钥设置指南"""
    return """
🔑 API密钥设置指南

📋 必需配置:
1. OpenAI API密钥: https://platform.openai.com/api-keys
   或
2. 智谱AI API密钥: https://open.bigmodel.cn/

🛠️  可选工具API密钥:
- Tavily搜索: https://tavily.com
- 百度翻译: https://fanyi-api.baidu.com
- WolframAlpha: https://developer.wolframalpha.com
- YouTube Data API: https://developers.google.com/youtube/v3
- NewsAPI: https://newsapi.org
- Judge0代码执行: https://rapidapi.com/judge0-official
- QuickChart图表: https://quickchart.io

📈 监控服务API密钥:
- LangFuse: https://langfuse.com

配置完成后运行: uv run python -c "
import sys; sys.path.insert(0, 'src')
from feynman.core.config.settings import validate_configuration
validate_configuration()
"
"""


# 全局配置实例
_settings_instance = None

def get_settings() -> FeynmanSettings:
    """获取全局配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = load_settings()
    return _settings_instance