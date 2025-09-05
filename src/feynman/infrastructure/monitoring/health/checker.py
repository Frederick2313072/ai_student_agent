"""
健康检查模块 - 监控系统各组件的健康状态
包括数据库连接、外部API、系统资源等
"""

import asyncio
import aiohttp
import time
import os
import psutil
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks = {}
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def check_system_resources(self) -> HealthCheck:
        """检查系统资源状态"""
        start_time = time.time()
        
        try:
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 检查内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 检查磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "available_disk_gb": round(disk.free / (1024**3), 2)
            }
            
            # 评估健康状态
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "系统资源严重不足"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = "系统资源紧张"
            else:
                status = HealthStatus.HEALTHY
                message = "系统资源正常"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc),
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"无法检查系统资源: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_chromadb(self) -> HealthCheck:
        """检查ChromaDB连接状态"""
        start_time = time.time()
        
        try:
            # 导入ChromaDB并尝试连接
            import chromadb
            
            # 使用与主应用相同的配置
            client = chromadb.PersistentClient(path="./chroma_db")
            
            # 尝试列出集合
            collections = client.list_collections()
            
            details = {
                "collections_count": len(collections),
                "collections": [col.name for col in collections[:5]]  # 只显示前5个
            }
            
            return HealthCheck(
                name="chromadb",
                status=HealthStatus.HEALTHY,
                message="ChromaDB连接正常",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc),
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                message=f"ChromaDB连接失败: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_openai_api(self) -> HealthCheck:
        """检查OpenAI API状态"""
        start_time = time.time()
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # 发送简单的测试请求
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            
            details = {
                "model_used": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return HealthCheck(
                name="openai_api",
                status=HealthStatus.HEALTHY,
                message="OpenAI API正常",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc),
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="openai_api",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API不可用: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_zhipu_api(self) -> HealthCheck:
        """检查智谱AI API状态"""
        start_time = time.time()
        
        try:
            zhipu_api_key = os.getenv("ZHIPU_API_KEY")
            if not zhipu_api_key:
                return HealthCheck(
                    name="zhipu_api",
                    status=HealthStatus.UNKNOWN,
                    message="智谱AI API密钥未配置",
                    duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc)
                )
            
            from langchain_community.chat_models import ChatZhipuAI
            
            # 创建测试客户端
            client = ChatZhipuAI(
                api_key=zhipu_api_key,
                model=os.getenv("ZHIPU_MODEL", "glm-4"),
                temperature=0.1
            )
            
            # 发送测试消息
            from langchain_core.messages import HumanMessage
            response = await client.ainvoke([HumanMessage(content="Hi")])
            
            return HealthCheck(
                name="zhipu_api",
                status=HealthStatus.HEALTHY,
                message="智谱AI API正常",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc),
                details={"response_length": len(response.content)}
            )
            
        except Exception as e:
            return HealthCheck(
                name="zhipu_api",
                status=HealthStatus.UNHEALTHY,
                message=f"智谱AI API不可用: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_external_apis(self) -> List[HealthCheck]:
        """检查外部API状态"""
        checks = []
        
        # 检查的外部API列表
        apis_to_check = [
            {
                "name": "tavily_search",
                "url": "https://api.tavily.com/search",
                "api_key_env": "TAVILY_API_KEY",
                "test_payload": {"api_key": "", "query": "test", "max_results": 1}
            },
            {
                "name": "baidu_translate",
                "url": "https://fanyi-api.baidu.com/api/trans/vip/translate",
                "api_key_env": "BAIDU_TRANSLATE_API_KEY",
                "method": "GET"  # 只测试连通性
            },
            {
                "name": "wolfram_alpha",
                "url": "http://api.wolframalpha.com/v1/query",
                "api_key_env": "WOLFRAM_API_KEY",
                "method": "GET"
            }
        ]
        
        session = await self._get_session()
        
        for api_config in apis_to_check:
            start_time = time.time()
            
            try:
                api_key = os.getenv(api_config["api_key_env"])
                if not api_key:
                    checks.append(HealthCheck(
                        name=api_config["name"],
                        status=HealthStatus.UNKNOWN,
                        message=f"{api_config['name']} API密钥未配置",
                        duration_ms=(time.time() - start_time) * 1000,
                        timestamp=datetime.now(timezone.utc)
                    ))
                    continue
                
                # 简单的连通性测试
                method = api_config.get("method", "HEAD")
                
                if method == "HEAD":
                    async with session.head(api_config["url"]) as response:
                        status_code = response.status
                elif method == "GET":
                    async with session.get(api_config["url"]) as response:
                        status_code = response.status
                else:
                    # POST请求
                    payload = api_config.get("test_payload", {})
                    if "api_key" in payload:
                        payload["api_key"] = api_key
                    
                    async with session.post(api_config["url"], json=payload) as response:
                        status_code = response.status
                
                if status_code < 500:  # 4xx也算可用，只是请求参数问题
                    status = HealthStatus.HEALTHY
                    message = f"{api_config['name']} API可用"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"{api_config['name']} API服务器错误 (HTTP {status_code})"
                
                checks.append(HealthCheck(
                    name=api_config["name"],
                    status=status,
                    message=message,
                    duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc),
                    details={"http_status": status_code}
                ))
                
            except asyncio.TimeoutError:
                checks.append(HealthCheck(
                    name=api_config["name"],
                    status=HealthStatus.UNHEALTHY,
                    message=f"{api_config['name']} API请求超时",
                    duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc)
                ))
            except Exception as e:
                checks.append(HealthCheck(
                    name=api_config["name"],
                    status=HealthStatus.UNHEALTHY,
                    message=f"{api_config['name']} API不可用: {str(e)}",
                    duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now(timezone.utc)
                ))
        
        return checks
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        start_time = time.time()
        
        try:
            # 并行运行所有检查
            results = await asyncio.gather(
                self.check_system_resources(),
                self.check_chromadb(),
                self.check_openai_api(),
                self.check_zhipu_api(),
                self.check_external_apis(),
                return_exceptions=True
            )
            
            checks = []
            
            # 处理单个检查结果
            for i, result in enumerate(results[:-1]):  # 最后一个是外部API列表
                if isinstance(result, Exception):
                    checks.append(HealthCheck(
                        name=f"check_{i}",
                        status=HealthStatus.UNKNOWN,
                        message=f"检查失败: {str(result)}",
                        duration_ms=0,
                        timestamp=datetime.now(timezone.utc)
                    ))
                else:
                    checks.append(result)
            
            # 处理外部API检查结果
            if isinstance(results[-1], list):
                checks.extend(results[-1])
            
            # 计算整体健康状态
            overall_status = self._calculate_overall_status(checks)
            
            # 统计信息
            status_counts = {}
            for status in HealthStatus:
                status_counts[status.value] = len([c for c in checks if c.status == status])
            
            return {
                "status": overall_status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": (time.time() - start_time) * 1000,
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status.value,
                        "message": check.message,
                        "duration_ms": check.duration_ms,
                        "timestamp": check.timestamp.isoformat(),
                        "details": check.details
                    }
                    for check in checks
                ],
                "summary": {
                    "total_checks": len(checks),
                    "status_counts": status_counts
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "checks": [],
                "summary": {"total_checks": 0, "status_counts": {}}
            }
    
    def _calculate_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """计算整体健康状态"""
        if not checks:
            return HealthStatus.UNKNOWN
        
        status_priority = {
            HealthStatus.UNHEALTHY: 4,
            HealthStatus.UNKNOWN: 3,
            HealthStatus.DEGRADED: 2,
            HealthStatus.HEALTHY: 1
        }
        
        # 核心组件（必须健康）
        core_components = ['system_resources', 'chromadb']
        core_checks = [c for c in checks if c.name in core_components]
        
        # 如果任何核心组件不健康，整体就不健康
        for check in core_checks:
            if check.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
        
        # 计算所有检查的最高优先级状态
        max_priority = max(status_priority[check.status] for check in checks)
        
        for status, priority in status_priority.items():
            if priority == max_priority:
                return status
        
        return HealthStatus.UNKNOWN
    
    async def get_readiness(self) -> Dict[str, Any]:
        """获取就绪状态（适用于K8s就绪探针）"""
        # 只检查关键组件
        checks = await asyncio.gather(
            self.check_system_resources(),
            self.check_chromadb(),
            return_exceptions=True
        )
        
        # 检查是否所有关键组件都健康
        ready = all(
            isinstance(check, HealthCheck) and check.status == HealthStatus.HEALTHY
            for check in checks
        )
        
        return {
            "ready": ready,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """获取存活状态（适用于K8s存活探针）"""
        # 简单的存活检查
        try:
            # 检查基本的系统资源
            psutil.cpu_percent()
            return {
                "alive": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception:
            return {
                "alive": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

