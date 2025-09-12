"""
Agent注册表和管理系统

提供Agent的注册、发现、监控和管理功能，是多Agent系统的核心基础设施。
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json

from .agent_protocol import (
    AgentType, AgentMetadata, AgentInterface, AgentMessage, MessageType,
    AgentTask, TaskStatus, AgentResponse
)


class RegistrationStatus(str, Enum):
    """注册状态"""
    PENDING = "pending"         # 等待注册
    ACTIVE = "active"           # 活跃状态
    INACTIVE = "inactive"       # 非活跃状态
    SUSPENDED = "suspended"     # 暂停状态
    TERMINATED = "terminated"   # 已终止


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"         # 健康
    WARNING = "warning"         # 警告
    CRITICAL = "critical"       # 严重
    UNKNOWN = "unknown"         # 未知


class AgentRegistration(BaseModel):
    """Agent注册信息"""
    agent_id: str = Field(..., description="Agent唯一标识")
    agent_type: AgentType = Field(..., description="Agent类型")
    metadata: AgentMetadata = Field(..., description="Agent元数据")
    
    # 注册信息
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")
    last_heartbeat: datetime = Field(default_factory=datetime.now, description="最后心跳时间")
    status: RegistrationStatus = Field(default=RegistrationStatus.PENDING, description="注册状态")
    
    # 运行状态
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="健康状态")
    current_load: float = Field(default=0.0, description="当前负载 0-1")
    active_tasks: List[str] = Field(default_factory=list, description="活跃任务ID列表")
    
    # 性能统计
    total_tasks_completed: int = Field(default=0, description="完成任务总数")
    total_processing_time: float = Field(default=0.0, description="总处理时间")
    average_response_time: float = Field(default=0.0, description="平均响应时间")
    success_rate: float = Field(default=1.0, description="成功率")
    error_count: int = Field(default=0, description="错误计数")
    
    # 最后活动
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")
    last_error: Optional[str] = Field(default=None, description="最后错误信息")


class AgentRegistry:
    """Agent注册表"""
    
    def __init__(self):
        """初始化注册表"""
        self.registrations: Dict[str, AgentRegistration] = {}
        self.type_index: Dict[AgentType, Set[str]] = {}
        self.capability_index: Dict[str, Set[str]] = {}
        
        # 监控配置
        self.heartbeat_timeout = 60  # 心跳超时时间(秒)
        self.health_check_interval = 30  # 健康检查间隔(秒)
        
        # 启动后台任务
        self._start_background_tasks()
    
    def register_agent(self, agent: AgentInterface) -> str:
        """注册Agent"""
        agent_id = agent.metadata.agent_id
        agent_type = agent.metadata.agent_type
        
        # 创建注册记录
        registration = AgentRegistration(
            agent_id=agent_id,
            agent_type=agent_type,
            metadata=agent.metadata,
            status=RegistrationStatus.ACTIVE
        )
        
        # 存储注册信息
        self.registrations[agent_id] = registration
        
        # 更新索引
        if agent_type not in self.type_index:
            self.type_index[agent_type] = set()
        self.type_index[agent_type].add(agent_id)
        
        # 更新能力索引
        for capability in agent.metadata.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = set()
            self.capability_index[capability.name].add(agent_id)
        
        print(f"✅ Agent注册成功: {agent_type.value} (ID: {agent_id})")
        return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        if agent_id not in self.registrations:
            return False
        
        registration = self.registrations[agent_id]
        
        # 更新状态
        registration.status = RegistrationStatus.TERMINATED
        registration.last_activity = datetime.now()
        
        # 从索引中移除
        agent_type = registration.agent_type
        if agent_type in self.type_index:
            self.type_index[agent_type].discard(agent_id)
        
        for capability in registration.metadata.capabilities:
            if capability.name in self.capability_index:
                self.capability_index[capability.name].discard(agent_id)
        
        # 移除注册记录
        del self.registrations[agent_id]
        
        print(f"🗑️ Agent注销成功: {agent_type.value} (ID: {agent_id})")
        return True
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentRegistration]:
        """根据ID获取Agent"""
        return self.registrations.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentRegistration]:
        """根据类型获取Agent列表"""
        agent_ids = self.type_index.get(agent_type, set())
        return [self.registrations[aid] for aid in agent_ids if aid in self.registrations]
    
    def get_agents_by_capability(self, capability_name: str) -> List[AgentRegistration]:
        """根据能力获取Agent列表"""
        agent_ids = self.capability_index.get(capability_name, set())
        return [self.registrations[aid] for aid in agent_ids if aid in self.registrations]
    
    def get_available_agents(self, max_load: float = 0.8) -> List[AgentRegistration]:
        """获取可用Agent列表"""
        available = []
        for registration in self.registrations.values():
            if (registration.status == RegistrationStatus.ACTIVE and
                registration.health_status in [HealthStatus.HEALTHY, HealthStatus.WARNING] and
                registration.current_load <= max_load):
                available.append(registration)
        
        # 按负载排序，负载低的优先
        available.sort(key=lambda x: x.current_load)
        return available
    
    def find_best_agent_for_task(self, task_type: str, complexity: str = "medium") -> Optional[AgentRegistration]:
        """为任务找到最佳Agent"""
        candidates = []
        
        # 查找具备相关能力的Agent
        for registration in self.registrations.values():
            if registration.status != RegistrationStatus.ACTIVE:
                continue
            
            # 检查能力匹配
            for capability in registration.metadata.capabilities:
                if (task_type in capability.input_types and 
                    (complexity == capability.complexity_level or capability.complexity_level == "any")):
                    candidates.append(registration)
                    break
        
        if not candidates:
            return None
        
        # 选择最佳候选者（考虑负载、性能、错误率）
        def score_agent(reg: AgentRegistration) -> float:
            load_score = 1.0 - reg.current_load  # 负载越低越好
            performance_score = reg.success_rate  # 成功率越高越好
            health_score = 1.0 if reg.health_status == HealthStatus.HEALTHY else 0.5
            return (load_score * 0.4 + performance_score * 0.4 + health_score * 0.2)
        
        candidates.sort(key=score_agent, reverse=True)
        return candidates[0]
    
    def update_heartbeat(self, agent_id: str) -> bool:
        """更新Agent心跳"""
        if agent_id not in self.registrations:
            return False
        
        self.registrations[agent_id].last_heartbeat = datetime.now()
        self.registrations[agent_id].last_activity = datetime.now()
        return True
    
    def update_agent_status(self, agent_id: str, status_update: Dict[str, Any]) -> bool:
        """更新Agent状态"""
        if agent_id not in self.registrations:
            return False
        
        registration = self.registrations[agent_id]
        
        # 更新负载
        if "load" in status_update:
            registration.current_load = max(0.0, min(1.0, status_update["load"]))
        
        # 更新活跃任务
        if "active_tasks" in status_update:
            registration.active_tasks = status_update["active_tasks"]
        
        # 更新健康状态
        if "health_status" in status_update:
            registration.health_status = HealthStatus(status_update["health_status"])
        
        # 更新性能统计
        if "completed_task" in status_update:
            task_info = status_update["completed_task"]
            registration.total_tasks_completed += 1
            registration.total_processing_time += task_info.get("processing_time", 0)
            registration.average_response_time = (
                registration.total_processing_time / registration.total_tasks_completed
            )
            
            if not task_info.get("success", True):
                registration.error_count += 1
            
            registration.success_rate = (
                (registration.total_tasks_completed - registration.error_count) / 
                max(registration.total_tasks_completed, 1)
            )
        
        # 更新错误信息
        if "error" in status_update:
            registration.last_error = status_update["error"]
            registration.error_count += 1
        
        registration.last_activity = datetime.now()
        return True
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        total_agents = len(self.registrations)
        active_agents = len([r for r in self.registrations.values() 
                           if r.status == RegistrationStatus.ACTIVE])
        
        # 按类型统计
        type_stats = {}
        for agent_type, agent_ids in self.type_index.items():
            active_count = len([aid for aid in agent_ids 
                              if aid in self.registrations and 
                              self.registrations[aid].status == RegistrationStatus.ACTIVE])
            type_stats[agent_type.value] = {
                "total": len(agent_ids),
                "active": active_count
            }
        
        # 健康状态统计
        health_stats = {}
        for status in HealthStatus:
            count = len([r for r in self.registrations.values() 
                        if r.health_status == status])
            health_stats[status.value] = count
        
        # 性能统计
        if self.registrations:
            avg_load = sum(r.current_load for r in self.registrations.values()) / len(self.registrations)
            avg_response_time = sum(r.average_response_time for r in self.registrations.values()) / len(self.registrations)
            overall_success_rate = sum(r.success_rate for r in self.registrations.values()) / len(self.registrations)
        else:
            avg_load = avg_response_time = overall_success_rate = 0.0
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "type_statistics": type_stats,
            "health_statistics": health_stats,
            "performance": {
                "average_load": avg_load,
                "average_response_time": avg_response_time,
                "overall_success_rate": overall_success_rate
            }
        }
    
    def get_agent_list(self, status_filter: Optional[RegistrationStatus] = None) -> List[Dict[str, Any]]:
        """获取Agent列表"""
        agents = []
        for registration in self.registrations.values():
            if status_filter is None or registration.status == status_filter:
                agents.append({
                    "agent_id": registration.agent_id,
                    "agent_type": registration.agent_type.value,
                    "status": registration.status.value,
                    "health_status": registration.health_status.value,
                    "current_load": registration.current_load,
                    "success_rate": registration.success_rate,
                    "last_activity": registration.last_activity.isoformat(),
                    "capabilities": [cap.name for cap in registration.metadata.capabilities]
                })
        return agents
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 这里可以启动异步任务进行健康检查等
        # 由于这是同步类，简化实现
        pass
    
    def _check_agent_health(self):
        """检查Agent健康状态"""
        current_time = datetime.now()
        
        for agent_id, registration in self.registrations.items():
            # 检查心跳超时
            if (current_time - registration.last_heartbeat).total_seconds() > self.heartbeat_timeout:
                if registration.status == RegistrationStatus.ACTIVE:
                    registration.status = RegistrationStatus.INACTIVE
                    registration.health_status = HealthStatus.CRITICAL
                    print(f"⚠️ Agent心跳超时: {registration.agent_type.value} (ID: {agent_id})")
            
            # 检查错误率
            if registration.total_tasks_completed > 10:  # 至少完成10个任务后才检查
                if registration.success_rate < 0.8:
                    registration.health_status = HealthStatus.WARNING
                elif registration.success_rate < 0.5:
                    registration.health_status = HealthStatus.CRITICAL
    
    def cleanup_inactive_agents(self, inactive_threshold_hours: int = 24):
        """清理非活跃Agent"""
        current_time = datetime.now()
        threshold = timedelta(hours=inactive_threshold_hours)
        
        to_remove = []
        for agent_id, registration in self.registrations.items():
            if (registration.status in [RegistrationStatus.INACTIVE, RegistrationStatus.TERMINATED] and
                current_time - registration.last_activity > threshold):
                to_remove.append(agent_id)
        
        for agent_id in to_remove:
            self.unregister_agent(agent_id)
            print(f"🧹 清理非活跃Agent: {agent_id}")
    
    def export_registry_data(self) -> Dict[str, Any]:
        """导出注册表数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "registrations": {
                agent_id: {
                    "agent_type": reg.agent_type.value,
                    "status": reg.status.value,
                    "health_status": reg.health_status.value,
                    "current_load": reg.current_load,
                    "total_tasks_completed": reg.total_tasks_completed,
                    "success_rate": reg.success_rate,
                    "registered_at": reg.registered_at.isoformat(),
                    "last_activity": reg.last_activity.isoformat()
                }
                for agent_id, reg in self.registrations.items()
            },
            "statistics": self.get_system_statistics()
        }


# 全局注册表实例
_global_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """获取全局Agent注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(agent: AgentInterface) -> str:
    """注册Agent的便捷函数"""
    return get_agent_registry().register_agent(agent)


def unregister_agent(agent_id: str) -> bool:
    """注销Agent的便捷函数"""
    return get_agent_registry().unregister_agent(agent_id)


def find_agent_for_task(task_type: str, complexity: str = "medium") -> Optional[AgentRegistration]:
    """为任务查找Agent的便捷函数"""
    return get_agent_registry().find_best_agent_for_task(task_type, complexity)


def get_system_stats() -> Dict[str, Any]:
    """获取系统统计的便捷函数"""
    return get_agent_registry().get_system_statistics()
