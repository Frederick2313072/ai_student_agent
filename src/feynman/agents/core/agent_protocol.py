"""
多Agent系统通信协议和数据模型

定义Agent间的标准通信接口、数据结构和协议规范。
"""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class AgentType(str, Enum):
    """Agent类型枚举"""
    EXPLANATION_ANALYZER = "explanation_analyzer"
    KNOWLEDGE_VALIDATOR = "knowledge_validator"
    QUESTION_STRATEGIST = "question_strategist"
    CONVERSATION_ORCHESTRATOR = "conversation_orchestrator"
    INSIGHT_SYNTHESIZER = "insight_synthesizer"
    COORDINATOR = "coordinator"
    REACT_AGENT = "react_agent"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(BaseModel):
    """Agent能力描述"""
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    input_types: List[str] = Field(..., description="支持的输入类型")
    output_types: List[str] = Field(..., description="支持的输出类型")
    complexity_level: Literal["simple", "medium", "complex"] = Field(..., description="处理复杂度级别")


class AgentMetadata(BaseModel):
    """Agent元数据"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Agent唯一标识")
    agent_type: AgentType = Field(..., description="Agent类型")
    name: str = Field(..., description="Agent名称")
    version: str = Field(default="1.0.0", description="版本号")
    capabilities: List[AgentCapability] = Field(default_factory=list, description="Agent能力列表")
    dependencies: List[AgentType] = Field(default_factory=list, description="依赖的其他Agent")
    max_concurrent_tasks: int = Field(default=1, description="最大并发任务数")
    average_processing_time: float = Field(default=0.0, description="平均处理时间(秒)")


class AgentTask(BaseModel):
    """Agent任务定义"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务唯一标识")
    task_type: str = Field(..., description="任务类型")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="任务优先级")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    
    # 任务数据
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    
    # 执行信息
    assigned_agent: Optional[AgentType] = Field(default=None, description="分配的Agent")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 结果
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="输出数据")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    
    # 依赖关系
    depends_on: List[str] = Field(default_factory=list, description="依赖的任务ID")
    blocks: List[str] = Field(default_factory=list, description="阻塞的任务ID")


class AgentMessage(BaseModel):
    """Agent间消息"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息ID")
    sender: AgentType = Field(..., description="发送方Agent")
    receiver: AgentType = Field(..., description="接收方Agent")
    message_type: str = Field(..., description="消息类型")
    payload: Dict[str, Any] = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    correlation_id: Optional[str] = Field(default=None, description="关联ID")


class ConversationContext(BaseModel):
    """对话上下文"""
    session_id: str = Field(..., description="会话ID")
    topic: str = Field(..., description="学习主题")
    user_explanation: str = Field(..., description="用户解释")
    
    # 历史信息
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="对话历史")
    short_term_memory: List[Dict[str, Any]] = Field(default_factory=list, description="短期记忆")
    
    # 分析结果
    analysis_results: Dict[str, Any] = Field(default_factory=dict, description="各Agent分析结果")
    unclear_points: List[Dict[str, Any]] = Field(default_factory=list, description="疑点列表")
    
    # 学习状态
    learning_phase: str = Field(default="initial", description="学习阶段")
    complexity_level: str = Field(default="unknown", description="复杂度级别")
    confidence_score: float = Field(default=0.0, description="理解置信度")


class AgentResponse(BaseModel):
    """Agent响应标准格式"""
    agent_id: str = Field(..., description="响应Agent ID")
    agent_type: AgentType = Field(..., description="Agent类型")
    task_id: str = Field(..., description="任务ID")
    
    success: bool = Field(..., description="执行是否成功")
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    processing_time: float = Field(..., description="处理时间(秒)")
    confidence: float = Field(default=1.0, description="结果置信度")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    next_actions: List[str] = Field(default_factory=list, description="建议的下一步动作")


class WorkflowState(BaseModel):
    """工作流状态"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="工作流ID")
    context: ConversationContext = Field(..., description="对话上下文")
    
    # 任务管理
    active_tasks: List[AgentTask] = Field(default_factory=list, description="活跃任务")
    completed_tasks: List[AgentTask] = Field(default_factory=list, description="已完成任务")
    failed_tasks: List[AgentTask] = Field(default_factory=list, description="失败任务")
    
    # 执行状态
    current_phase: str = Field(default="initialization", description="当前阶段")
    next_agents: List[AgentType] = Field(default_factory=list, description="下一步要执行的Agent")
    
    # 结果聚合
    final_questions: List[str] = Field(default_factory=list, description="最终生成的问题")
    insights: List[str] = Field(default_factory=list, description="学习洞察")
    learning_report: Optional[Dict[str, Any]] = Field(default=None, description="学习报告")


# 标准消息类型定义
class MessageType:
    """标准消息类型"""
    
    # 任务相关
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_STATUS_UPDATE = "task_status_update"
    
    # 协调相关
    COORDINATION_REQUEST = "coordination_request"
    AGENT_REGISTRATION = "agent_registration"
    CAPABILITY_QUERY = "capability_query"
    
    # 数据共享
    DATA_SHARE = "data_share"
    CONTEXT_UPDATE = "context_update"
    RESULT_BROADCAST = "result_broadcast"
    
    # 控制相关
    PAUSE_REQUEST = "pause_request"
    RESUME_REQUEST = "resume_request"
    CANCEL_REQUEST = "cancel_request"


class AgentInterface:
    """Agent标准接口(抽象基类)"""
    
    def __init__(self, metadata: AgentMetadata):
        self.metadata = metadata
        self.current_tasks: Dict[str, AgentTask] = {}
        
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理任务的标准接口"""
        raise NotImplementedError("子类必须实现process_task方法")
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """处理消息的标准接口"""
        raise NotImplementedError("子类必须实现handle_message方法")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """获取Agent能力"""
        return self.metadata.capabilities
    
    def can_handle_task(self, task_type: str, complexity: str) -> bool:
        """检查是否能处理指定任务"""
        for capability in self.metadata.capabilities:
            if task_type in capability.input_types and complexity in [capability.complexity_level, "any"]:
                return True
        return False


# 任务类型定义
class TaskType:
    """标准任务类型"""
    
    # 分析类任务
    EXPLANATION_ANALYSIS = "explanation_analysis"
    KNOWLEDGE_VALIDATION = "knowledge_validation"
    INSIGHT_SYNTHESIS = "insight_synthesis"
    
    # 生成类任务
    QUESTION_GENERATION = "question_generation"
    STRATEGY_SELECTION = "strategy_selection"
    
    # 协调类任务
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    TASK_COORDINATION = "task_coordination"
    
    # 监控类任务
    PERFORMANCE_MONITORING = "performance_monitoring"
    ERROR_HANDLING = "error_handling"


# 工具函数
def create_task(task_type: str, input_data: Dict[str, Any], 
                priority: TaskPriority = TaskPriority.MEDIUM,
                context: Optional[Dict[str, Any]] = None) -> AgentTask:
    """创建标准任务"""
    return AgentTask(
        task_type=task_type,
        priority=priority,
        input_data=input_data,
        context=context or {}
    )


def create_message(sender: AgentType, receiver: AgentType, 
                  message_type: str, payload: Dict[str, Any],
                  correlation_id: Optional[str] = None) -> AgentMessage:
    """创建标准消息"""
    return AgentMessage(
        sender=sender,
        receiver=receiver,
        message_type=message_type,
        payload=payload,
        correlation_id=correlation_id
    )


def create_response(agent_id: str, agent_type: AgentType, task_id: str,
                   success: bool, processing_time: float,
                   result: Optional[Dict[str, Any]] = None,
                   error: Optional[str] = None) -> AgentResponse:
    """创建标准响应"""
    return AgentResponse(
        agent_id=agent_id,
        agent_type=agent_type,
        task_id=task_id,
        success=success,
        processing_time=processing_time,
        result=result,
        error=error
    )
