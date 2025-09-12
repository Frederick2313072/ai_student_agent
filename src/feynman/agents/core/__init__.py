"""Agent核心模块 - 多Agent系统"""

# 多Agent系统核心组件
from .explanation_analyzer import ExplanationAnalyzer
from .knowledge_validator import KnowledgeValidator
from .question_strategist import QuestionStrategist
from .conversation_orchestrator import ConversationOrchestrator
from .insight_synthesizer import InsightSynthesizer
from .coordinator import Coordinator

# 工作流和协调
from .multi_agent_workflow import MultiAgentWorkflow, execute_multi_agent_workflow
from .agent_registry import AgentRegistry, get_agent_registry
from .agent_protocol import AgentInterface, AgentType, AgentTask, AgentMessage

__all__ = [
    # 专业Agent
    "ExplanationAnalyzer",
    "KnowledgeValidator",
    "QuestionStrategist", 
    "ConversationOrchestrator",
    "InsightSynthesizer",
    "Coordinator",
    
    # 工作流系统
    "MultiAgentWorkflow",
    "execute_multi_agent_workflow",
    
    # 管理和协议
    "AgentRegistry",
    "get_agent_registry",
    "AgentInterface",
    "AgentType",
    "AgentTask", 
    "AgentMessage"
]
