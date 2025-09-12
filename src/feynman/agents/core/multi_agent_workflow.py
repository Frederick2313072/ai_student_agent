"""
多Agent系统工作流

重构的LangGraph工作流，支持动态Agent调度、智能任务分派和协调管理。
这是新的多Agent架构的核心工作流引擎。
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from operator import add
from datetime import datetime
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from .agent_protocol import (
    AgentType, AgentTask, ConversationContext, WorkflowState, 
    TaskStatus, TaskPriority, create_task, create_response
)
from .agent_registry import get_agent_registry, find_agent_for_task
from .coordinator import Coordinator
from .explanation_analyzer import ExplanationAnalyzer
from .knowledge_validator import KnowledgeValidator
from .question_strategist import QuestionStrategist
from .conversation_orchestrator import ConversationOrchestrator
from .insight_synthesizer import InsightSynthesizer

# 导入监控模块（可选）
try:
    from feynman.infrastructure.monitoring.tracing.otlp import trace_span, add_span_attribute, add_span_event
    from feynman.infrastructure.monitoring.metrics.prometheus import monitor_workflow_node
    from feynman.infrastructure.monitoring.logging.structured import get_logger
    MONITORING_AVAILABLE = True
except ImportError:
    def trace_span(name): return lambda f: f
    def add_span_attribute(*args): pass
    def add_span_event(*args): pass
    def monitor_workflow_node(name): return lambda f: f
    def get_logger(name): 
        import logging
        return logging.getLogger(name)
    MONITORING_AVAILABLE = False


class MultiAgentState(TypedDict):
    """多Agent工作流状态"""
    # 基础信息
    session_id: str
    topic: str
    user_explanation: str
    
    # 对话上下文
    conversation_context: Dict[str, Any]
    short_term_memory: List[Dict[str, Any]]
    
    # 工作流控制
    workflow_id: str
    current_phase: str
    coordinator_decision: Optional[Dict[str, Any]]
    
    # Agent结果
    analysis_results: Dict[str, Any]
    validation_results: Dict[str, Any]
    question_results: Dict[str, Any]
    orchestration_results: Dict[str, Any]
    insight_results: Dict[str, Any]
    
    # 最终输出
    final_questions: List[str]
    learning_insights: List[str]
    learning_report: Optional[Dict[str, Any]]
    
    # 系统状态
    active_agents: List[str]
    completed_tasks: List[str]
    error_log: List[Dict[str, Any]]


class MultiAgentWorkflow:
    """多Agent工作流管理器"""
    
    def __init__(self):
        """初始化工作流"""
        self.logger = get_logger("multi_agent_workflow")
        self.registry = get_agent_registry()
        
        # 初始化Agent实例
        self.agents = self._initialize_agents()
        
        # 构建工作流图
        self.workflow_graph = self._build_workflow_graph()
        
        self.logger.info("多Agent工作流初始化完成")
    
    def _initialize_agents(self) -> Dict[AgentType, Any]:
        """初始化所有Agent实例"""
        agents = {}
        
        try:
            # 创建Agent实例
            agents[AgentType.COORDINATOR] = Coordinator()
            agents[AgentType.EXPLANATION_ANALYZER] = ExplanationAnalyzer()
            agents[AgentType.KNOWLEDGE_VALIDATOR] = KnowledgeValidator()
            agents[AgentType.QUESTION_STRATEGIST] = QuestionStrategist()
            agents[AgentType.CONVERSATION_ORCHESTRATOR] = ConversationOrchestrator()
            agents[AgentType.INSIGHT_SYNTHESIZER] = InsightSynthesizer()
            
            # 注册到注册表
            for agent_type, agent in agents.items():
                self.registry.register_agent(agent)
                self.logger.info(f"Agent注册成功: {agent_type.value}")
            
        except Exception as e:
            self.logger.error(f"Agent初始化失败: {e}")
            raise
        
        return agents
    
    def _build_workflow_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(MultiAgentState)
        
        # 添加节点
        workflow.add_node("coordinator_entry", self._coordinator_entry_node)
        workflow.add_node("explanation_analysis", self._explanation_analysis_node)
        workflow.add_node("knowledge_validation", self._knowledge_validation_node)
        workflow.add_node("question_generation", self._question_generation_node)
        workflow.add_node("conversation_orchestration", self._conversation_orchestration_node)
        workflow.add_node("insight_synthesis", self._insight_synthesis_node)
        workflow.add_node("coordinator_finalization", self._coordinator_finalization_node)
        
        # 设置工作流路径
        workflow.set_entry_point("coordinator_entry")
        
        # 动态路由 - 由协调者决定下一步
        workflow.add_conditional_edges(
            "coordinator_entry",
            self._route_next_step,
            {
                "explanation_analysis": "explanation_analysis",
                "knowledge_validation": "knowledge_validation",
                "question_generation": "question_generation",
                "conversation_orchestration": "conversation_orchestration",
                "insight_synthesis": "insight_synthesis",
                "finalization": "coordinator_finalization",
                "end": END
            }
        )
        
        # 各节点完成后都返回协调者进行下一步决策
        for node in ["explanation_analysis", "knowledge_validation", "question_generation", 
                    "conversation_orchestration", "insight_synthesis"]:
            workflow.add_edge(node, "coordinator_entry")
        
        # 最终节点
        workflow.add_edge("coordinator_finalization", END)
        
        return workflow.compile(
            checkpointer=None,
            # 设置递归限制以避免无限循环
            debug=False,
        )
    
    @monitor_workflow_node("coordinator_entry")
    async def _coordinator_entry_node(self, state: MultiAgentState) -> MultiAgentState:
        """协调者入口节点"""
        self.logger.info(f"协调者入口节点: {state.get('session_id', 'unknown')}")
        
        with trace_span("coordinator_entry") as span:
            add_span_attribute("session_id", state.get("session_id", ""))
            add_span_attribute("current_phase", state.get("current_phase", ""))
            
            try:
                # 构建对话上下文
                context = ConversationContext(
                    session_id=state["session_id"],
                    topic=state["topic"],
                    user_explanation=state["user_explanation"],
                    conversation_history=state.get("short_term_memory", []),
                    short_term_memory=state.get("short_term_memory", []),
                    analysis_results=state.get("analysis_results", {}),
                    unclear_points=state.get("analysis_results", {}).get("unclear_points", [])
                )
                
                # 创建协调任务
                coordination_task = create_task(
                    task_type="global_coordination",
                    input_data={
                        "current_state": state,
                        "system_status": self.registry.get_system_statistics(),
                        "requirements": {
                            "quality": "high",
                            "urgency": "medium"
                        }
                    },
                    context={"session_id": state["session_id"]}
                )
                
                # 执行协调决策
                coordinator = self.agents[AgentType.COORDINATOR]
                response = await coordinator.process_task(coordination_task, context)
                
                if response.success:
                    decision = response.result.get("coordination_decision", {})
                    state["coordinator_decision"] = decision
                    state["current_phase"] = decision.get("next_phase", "analysis")
                    
                    add_span_event("coordination_decision_made", {
                        "strategy": decision.get("strategy", "unknown"),
                        "target_agents": decision.get("target_agents", []),
                        "next_phase": decision.get("next_phase", "unknown")
                    })
                else:
                    # 降级处理
                    state["coordinator_decision"] = {
                        "strategy": "sequential",
                        "next_phase": "explanation_analysis",
                        "target_agents": ["explanation_analyzer"]
                    }
                    state["current_phase"] = "explanation_analysis"
                
                return state
                
            except Exception as e:
                self.logger.error(f"协调者入口节点错误: {e}")
                add_span_event("coordinator_entry_error", {"error": str(e)})
                
                # 错误处理
                state["error_log"].append({
                    "node": "coordinator_entry",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
                # 设置降级决策
                state["coordinator_decision"] = {
                    "strategy": "fallback",
                    "next_phase": "explanation_analysis",
                    "target_agents": ["explanation_analyzer"]
                }
                state["current_phase"] = "explanation_analysis"
                
                return state
    
    @monitor_workflow_node("explanation_analysis")
    async def _explanation_analysis_node(self, state: MultiAgentState) -> MultiAgentState:
        """解释分析节点"""
        self.logger.info("执行解释分析")
        
        with trace_span("explanation_analysis") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建分析任务
                analysis_task = create_task(
                    task_type="explanation_analysis",
                    input_data={
                        "explanation": state["user_explanation"],
                        "topic": state["topic"]
                    }
                )
                
                # 执行分析
                analyzer = self.agents[AgentType.EXPLANATION_ANALYZER]
                response = await analyzer.process_task(analysis_task, context)
                
                if response.success:
                    state["analysis_results"] = response.result
                    state["completed_tasks"].append("explanation_analysis")
                    
                    add_span_event("explanation_analysis_completed", {
                        "unclear_points_count": len(response.result.get("unclear_points", [])),
                        "is_complete": response.result.get("is_complete", False)
                    })
                else:
                    state["error_log"].append({
                        "node": "explanation_analysis",
                        "error": response.error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return state
                
            except Exception as e:
                self.logger.error(f"解释分析节点错误: {e}")
                state["error_log"].append({
                    "node": "explanation_analysis",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                return state
    
    @monitor_workflow_node("knowledge_validation")
    async def _knowledge_validation_node(self, state: MultiAgentState) -> MultiAgentState:
        """知识验证节点"""
        self.logger.info("执行知识验证")
        
        with trace_span("knowledge_validation") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建验证任务
                validation_task = create_task(
                    task_type="knowledge_validation",
                    input_data={
                        "explanation": state["user_explanation"],
                        "analysis_results": state.get("analysis_results", {})
                    }
                )
                
                # 执行验证
                validator = self.agents[AgentType.KNOWLEDGE_VALIDATOR]
                response = await validator.process_task(validation_task, context)
                
                if response.success:
                    state["validation_results"] = response.result
                    state["completed_tasks"].append("knowledge_validation")
                    
                    add_span_event("knowledge_validation_completed", {
                        "overall_accuracy": response.result.get("validation_report", {}).get("overall_accuracy", 0.5),
                        "critical_issues": len(response.result.get("validation_report", {}).get("critical_issues", []))
                    })
                else:
                    state["error_log"].append({
                        "node": "knowledge_validation",
                        "error": response.error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return state
                
            except Exception as e:
                self.logger.error(f"知识验证节点错误: {e}")
                state["error_log"].append({
                    "node": "knowledge_validation",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                return state
    
    @monitor_workflow_node("question_generation")
    async def _question_generation_node(self, state: MultiAgentState) -> MultiAgentState:
        """问题生成节点"""
        self.logger.info("执行问题生成")
        
        with trace_span("question_generation") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建问题生成任务
                question_task = create_task(
                    task_type="question_generation",
                    input_data={
                        "unclear_points": state.get("analysis_results", {}).get("unclear_points", []),
                        "validation_results": state.get("validation_results", {}),
                        "learner_level": "intermediate"
                    }
                )
                
                # 执行问题生成
                strategist = self.agents[AgentType.QUESTION_STRATEGIST]
                response = await strategist.process_task(question_task, context)
                
                if response.success:
                    state["question_results"] = response.result
                    state["completed_tasks"].append("question_generation")
                    
                    # 提取最终问题
                    question_set = response.result.get("question_set", {})
                    primary_questions = question_set.get("primary_questions", [])
                    state["final_questions"] = [q.get("content", "") for q in primary_questions]
                    
                    add_span_event("question_generation_completed", {
                        "total_questions": len(state["final_questions"]),
                        "estimated_time": question_set.get("total_estimated_time", 0)
                    })
                else:
                    state["error_log"].append({
                        "node": "question_generation",
                        "error": response.error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return state
                
            except Exception as e:
                self.logger.error(f"问题生成节点错误: {e}")
                state["error_log"].append({
                    "node": "question_generation",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                return state
    
    @monitor_workflow_node("conversation_orchestration")
    async def _conversation_orchestration_node(self, state: MultiAgentState) -> MultiAgentState:
        """对话编排节点"""
        self.logger.info("执行对话编排")
        
        with trace_span("conversation_orchestration") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建编排任务
                orchestration_task = create_task(
                    task_type="workflow_orchestration",
                    input_data={
                        "current_state": state,
                        "available_results": {
                            "analysis": state.get("analysis_results", {}),
                            "validation": state.get("validation_results", {}),
                            "questions": state.get("question_results", {})
                        }
                    }
                )
                
                # 执行编排
                orchestrator = self.agents[AgentType.CONVERSATION_ORCHESTRATOR]
                response = await orchestrator.process_task(orchestration_task, context)
                
                if response.success:
                    state["orchestration_results"] = response.result
                    state["completed_tasks"].append("conversation_orchestration")
                    
                    add_span_event("conversation_orchestration_completed", {
                        "orchestration_decision": response.result.get("orchestration_decision", {}).get("recommended_action", "unknown")
                    })
                else:
                    state["error_log"].append({
                        "node": "conversation_orchestration",
                        "error": response.error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return state
                
            except Exception as e:
                self.logger.error(f"对话编排节点错误: {e}")
                state["error_log"].append({
                    "node": "conversation_orchestration",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                return state
    
    @monitor_workflow_node("insight_synthesis")
    async def _insight_synthesis_node(self, state: MultiAgentState) -> MultiAgentState:
        """洞察综合节点"""
        self.logger.info("执行洞察综合")
        
        with trace_span("insight_synthesis") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建综合任务
                synthesis_task = create_task(
                    task_type="insight_synthesis",
                    input_data={
                        "all_results": {
                            "analysis": state.get("analysis_results", {}),
                            "validation": state.get("validation_results", {}),
                            "questions": state.get("question_results", {}),
                            "orchestration": state.get("orchestration_results", {})
                        }
                    }
                )
                
                # 执行综合
                synthesizer = self.agents[AgentType.INSIGHT_SYNTHESIZER]
                response = await synthesizer.process_task(synthesis_task, context)
                
                if response.success:
                    state["insight_results"] = response.result
                    state["completed_tasks"].append("insight_synthesis")
                    
                    # 提取学习洞察
                    insights = response.result.get("insights", [])
                    state["learning_insights"] = [insight.get("content", "") for insight in insights]
                    
                    add_span_event("insight_synthesis_completed", {
                        "insights_count": len(state["learning_insights"])
                    })
                else:
                    state["error_log"].append({
                        "node": "insight_synthesis",
                        "error": response.error,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return state
                
            except Exception as e:
                self.logger.error(f"洞察综合节点错误: {e}")
                state["error_log"].append({
                    "node": "insight_synthesis",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                return state
    
    @monitor_workflow_node("coordinator_finalization")
    async def _coordinator_finalization_node(self, state: MultiAgentState) -> MultiAgentState:
        """协调者最终化节点"""
        self.logger.info("执行最终化处理")
        
        # 防止重复执行
        if "coordinator_finalization" in state.get("completed_tasks", []):
            self.logger.info("最终化任务已完成，跳过重复执行")
            return state
        
        with trace_span("coordinator_finalization") as span:
            try:
                context = self._build_context_from_state(state)
                
                # 创建最终化任务
                finalization_task = create_task(
                    task_type="report_generation",
                    input_data={
                        "session_summary": {
                            "completed_tasks": state["completed_tasks"],
                            "final_questions": state["final_questions"],
                            "learning_insights": state["learning_insights"],
                            "error_log": state["error_log"]
                        }
                    }
                )
                
                # 生成学习报告
                synthesizer = self.agents[AgentType.INSIGHT_SYNTHESIZER]
                response = await synthesizer.process_task(finalization_task, context)
                
                if response.success:
                    state["learning_report"] = response.result.get("learning_report", {})
                
                # 更新最终状态
                state["current_phase"] = "completed"
                
                add_span_event("workflow_finalization_completed", {
                    "total_questions": len(state["final_questions"]),
                    "total_insights": len(state["learning_insights"]),
                    "completed_tasks": len(state["completed_tasks"]),
                    "error_count": len(state["error_log"])
                })
                
                # 标记任务完成
                state["completed_tasks"].append("coordinator_finalization")
                
                return state
                
            except Exception as e:
                self.logger.error(f"最终化节点错误: {e}")
                state["error_log"].append({
                    "node": "coordinator_finalization",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                # 即使出错也要标记为已完成，避免重复执行
                state["completed_tasks"].append("coordinator_finalization")
                return state
    
    def _route_next_step(self, state: MultiAgentState) -> str:
        """路由下一步决策"""
        decision = state.get("coordinator_decision", {})
        current_phase = state.get("current_phase", "")
        completed_tasks = state.get("completed_tasks", [])
        
        # 添加调试日志
        self.logger.info(f"路由决策 - 当前阶段: {current_phase}, 已完成任务: {completed_tasks}")
        self.logger.info(f"协调者决策: {decision}")
        
        # 检查是否所有必要任务都已完成
        required_tasks = ["explanation_analysis", "question_generation"]
        all_required_completed = all(task in completed_tasks for task in required_tasks)
        
        # 强制终止条件：如果已经完成核心任务，直接结束
        if all_required_completed:
            self.logger.info("所有必要任务已完成，结束工作流")
            return "finalization"
        
        # 防止无限循环：如果coordinator_finalization已执行，强制结束
        if "coordinator_finalization" in completed_tasks:
            self.logger.info("最终化任务已完成，强制结束")
            return "end"
        
        # 根据协调者决策和当前状态决定下一步
        next_phase = decision.get("next_phase", "explanation_analysis")
        
        # 按优先级执行任务
        if next_phase == "explanation_analysis" and "explanation_analysis" not in completed_tasks:
            return "explanation_analysis"
        elif next_phase == "knowledge_validation" and "knowledge_validation" not in completed_tasks:
            return "knowledge_validation"
        elif next_phase == "question_generation" and "question_generation" not in completed_tasks:
            return "question_generation"
        elif next_phase == "conversation_orchestration" and "conversation_orchestration" not in completed_tasks:
            return "conversation_orchestration"
        elif next_phase == "insight_synthesis" and "insight_synthesis" not in completed_tasks:
            return "insight_synthesis"
        else:
            # 所有任务完成或无更多任务，进入最终化
            self.logger.info("无更多任务需要执行，进入最终化")
            return "finalization"
    
    def _build_context_from_state(self, state: MultiAgentState) -> ConversationContext:
        """从状态构建对话上下文"""
        return ConversationContext(
            session_id=state["session_id"],
            topic=state["topic"],
            user_explanation=state["user_explanation"],
            conversation_history=state.get("short_term_memory", []),
            short_term_memory=state.get("short_term_memory", []),
            analysis_results=state.get("analysis_results", {}),
            unclear_points=state.get("analysis_results", {}).get("unclear_points", []),
            learning_phase=state.get("current_phase", "initial"),
            confidence_score=state.get("analysis_results", {}).get("confidence_score", 0.5)
        )
    
    async def execute_workflow(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        start_time = time.time()
        
        # 初始化状态
        initial_state: MultiAgentState = {
            "session_id": inputs.get("session_id", str(uuid.uuid4())),
            "topic": inputs["topic"],
            "user_explanation": inputs["explanation"],
            "conversation_context": {},
            "short_term_memory": inputs.get("short_term_memory", []),
            "workflow_id": str(uuid.uuid4()),
            "current_phase": "initialization",
            "coordinator_decision": None,
            "analysis_results": {},
            "validation_results": {},
            "question_results": {},
            "orchestration_results": {},
            "insight_results": {},
            "final_questions": [],
            "learning_insights": [],
            "learning_report": None,
            "active_agents": [],
            "completed_tasks": [],
            "error_log": []
        }
        
        try:
            self.logger.info(f"开始执行多Agent工作流: {initial_state['session_id']}")
            
            # 执行工作流（设置递归限制）
            final_state = await self.workflow_graph.ainvoke(
                initial_state,
                config={"recursion_limit": 50}  # 增加递归限制
            )
            
            execution_time = time.time() - start_time
            
            # 构建返回结果
            result = {
                "session_id": final_state["session_id"],
                "questions": final_state["final_questions"],
                "learning_insights": final_state["learning_insights"],
                "learning_report": final_state.get("learning_report"),
                "short_term_memory": final_state["short_term_memory"],
                "execution_time": execution_time,
                "completed_tasks": final_state["completed_tasks"],
                "error_count": len(final_state["error_log"]),
                "success": len(final_state["error_log"]) == 0
            }
            
            self.logger.info(f"工作流执行完成: {execution_time:.2f}秒, 问题数: {len(final_state['final_questions'])}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"工作流执行失败: {e}")
            
            # 返回错误结果
            return {
                "session_id": initial_state["session_id"],
                "questions": [],
                "learning_insights": [],
                "learning_report": None,
                "short_term_memory": initial_state["short_term_memory"],
                "execution_time": execution_time,
                "completed_tasks": [],
                "error_count": 1,
                "success": False,
                "error": str(e)
            }


# 创建全局工作流实例
_global_workflow: Optional[MultiAgentWorkflow] = None


def get_multi_agent_workflow() -> MultiAgentWorkflow:
    """获取全局多Agent工作流实例"""
    global _global_workflow
    if _global_workflow is None:
        _global_workflow = MultiAgentWorkflow()
    return _global_workflow


async def execute_multi_agent_workflow(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """执行多Agent工作流的便捷函数"""
    workflow = get_multi_agent_workflow()
    return await workflow.execute_workflow(inputs)

