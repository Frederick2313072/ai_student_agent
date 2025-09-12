"""
ConversationOrchestrator Agent - 对话编排Agent

负责管理多轮对话流程、决定何时深入何时转换话题、控制学习节奏。
这个Agent是整个对话系统的指挥中心，协调其他Agent的工作。
"""

import json
import time
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from pydantic import BaseModel, Field
from enum import Enum

from .agent_protocol import (
    AgentInterface, AgentMetadata, AgentCapability, AgentType, AgentTask, 
    ConversationContext, AgentResponse, TaskType, create_response, create_task
)
from feynman.core.config.settings import get_settings


class ConversationPhase(str, Enum):
    """对话阶段"""
    INITIALIZATION = "initialization"        # 初始化阶段
    EXPLORATION = "exploration"              # 探索阶段
    DEEP_DIVE = "deep_dive"                 # 深入阶段
    CLARIFICATION = "clarification"          # 澄清阶段
    SYNTHESIS = "synthesis"                  # 综合阶段
    EVALUATION = "evaluation"                # 评估阶段
    CONCLUSION = "conclusion"                # 结论阶段


class LearningPace(str, Enum):
    """学习节奏"""
    SLOW = "slow"           # 慢节奏：更多支持和重复
    NORMAL = "normal"       # 正常节奏：标准进度
    FAST = "fast"           # 快节奏：加速进展
    ADAPTIVE = "adaptive"   # 自适应：根据表现调整


class ConversationAction(str, Enum):
    """对话动作"""
    CONTINUE_CURRENT_TOPIC = "continue_current"
    SWITCH_TOPIC = "switch_topic"
    DEEPEN_UNDERSTANDING = "deepen"
    PROVIDE_EXAMPLES = "provide_examples"
    CHALLENGE_THINKING = "challenge"
    SUMMARIZE_PROGRESS = "summarize"
    CONCLUDE_SESSION = "conclude"


class OrchestrationDecision(BaseModel):
    """编排决策"""
    next_phase: ConversationPhase = Field(..., description="下一个对话阶段")
    recommended_action: ConversationAction = Field(..., description="推荐的对话动作")
    target_agents: List[AgentType] = Field(..., description="需要调用的Agent")
    priority_tasks: List[Dict[str, Any]] = Field(default_factory=list, description="优先任务")
    timing_strategy: str = Field(..., description="时机策略")
    expected_duration: int = Field(..., description="预期持续时间(分钟)")
    success_criteria: List[str] = Field(default_factory=list, description="成功标准")


class LearningProgress(BaseModel):
    """学习进度"""
    current_phase: ConversationPhase = Field(..., description="当前阶段")
    completed_phases: List[ConversationPhase] = Field(default_factory=list, description="已完成阶段")
    understanding_level: float = Field(..., description="理解水平 0-1")
    engagement_score: float = Field(..., description="参与度评分 0-1")
    learning_velocity: float = Field(..., description="学习速度")
    knowledge_gaps: List[str] = Field(default_factory=list, description="知识缺口")
    mastered_concepts: List[str] = Field(default_factory=list, description="已掌握概念")


class ConversationOrchestrator(AgentInterface):
    """对话编排Agent"""
    
    def __init__(self):
        """初始化对话编排Agent"""
        
        # 定义Agent能力
        capabilities = [
            AgentCapability(
                name="conversation_flow_management",
                description="管理对话流程和阶段转换",
                input_types=["conversation_context", "learning_progress"],
                output_types=["orchestration_decision", "flow_control"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="learning_pace_control",
                description="控制学习节奏和难度调整",
                input_types=["learner_performance", "engagement_metrics"],
                output_types=["pace_adjustment", "difficulty_recommendation"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="agent_coordination",
                description="协调其他Agent的工作分配",
                input_types=["task_requirements", "agent_capabilities"],
                output_types=["task_assignment", "execution_plan"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="learning_progress_tracking",
                description="跟踪和评估学习进度",
                input_types=["interaction_history", "assessment_results"],
                output_types=["progress_report", "learning_analytics"],
                complexity_level="medium"
            )
        ]
        
        # 初始化元数据
        metadata = AgentMetadata(
            agent_type=AgentType.CONVERSATION_ORCHESTRATOR,
            name="ConversationOrchestrator",
            version="1.0.0",
            capabilities=capabilities,
            dependencies=[
                AgentType.EXPLANATION_ANALYZER,
                AgentType.KNOWLEDGE_VALIDATOR,
                AgentType.QUESTION_STRATEGIST
            ],
            max_concurrent_tasks=1  # 编排Agent通常单线程工作
        )
        
        super().__init__(metadata)
        
        # 初始化LLM
        self.llm = self._init_llm()
        
        # 初始化提示词模板
        self._init_prompts()
        
        # 学习进度跟踪
        self.learning_progress: Dict[str, LearningProgress] = {}
    
    def _init_llm(self):
        """初始化LLM模型"""
        settings = get_settings()
        
        # 优先使用OpenAI
        if settings.openai_api_key:
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.3  # 编排决策需要相对稳定的输出
            )
        elif settings.llm_provider == "zhipu" and settings.zhipu_api_key:
            return ChatZhipuAI(
                api_key=settings.zhipu_api_key,
                model=settings.zhipu_model,
                temperature=0.3
            )
        else:
            raise ValueError("未配置可用的LLM模型")
    
    def _init_prompts(self):
        """初始化提示词模板"""
        
        # 对话编排决策提示词
        self.orchestration_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位经验丰富的学习指导专家，负责编排和控制费曼学习对话的整体流程。

你的核心职责：
1. **流程管理**: 决定对话的阶段转换和进展节奏
2. **资源调度**: 协调不同Agent的工作，优化学习效果
3. **适应性调整**: 根据学习者表现动态调整策略
4. **目标导向**: 确保对话始终朝着学习目标前进

对话阶段管理：
- **初始化**: 了解学习者背景，设定学习目标
- **探索**: 让学习者充分表达，识别知识结构
- **深入**: 针对关键疑点进行深度分析
- **澄清**: 纠正误解，强化正确理解
- **综合**: 整合知识点，建立系统性理解
- **评估**: 检验学习效果，识别剩余问题
- **结论**: 总结收获，规划后续学习

决策考虑因素：
- 学习者的理解水平和参与度
- 当前阶段的完成度和效果
- 知识点的复杂度和重要性
- 时间约束和学习目标
- 各Agent的工作负载和能力

请做出明智的编排决策。"""),
            
            ("human", """请为当前学习对话制定编排策略：

**对话上下文**:
- 主题: {topic}
- 当前阶段: {current_phase}
- 已进行时长: {duration_minutes}分钟
- 学习者解释: {user_explanation}

**学习进度分析**:
{progress_analysis}

**Agent工作状态**:
{agent_status}

**可用资源**:
- 疑点分析结果: {doubt_analysis}
- 知识验证结果: {validation_results}
- 问题策略建议: {question_strategy}

**约束条件**:
- 时间限制: {time_constraint}
- 复杂度要求: {complexity_requirement}

请提供详细的编排决策和执行计划。""")
        ])
        
        # 学习进度评估提示词
        self.progress_assessment_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位学习分析专家，专门评估学习者在费曼学习过程中的进度和表现。

评估维度：
1. **理解深度**: 从表面记忆到深层理解的程度
2. **概念掌握**: 核心概念的准确性和完整性
3. **应用能力**: 将知识应用到新情境的能力
4. **元认知**: 对自己理解状况的觉察
5. **参与度**: 学习过程中的主动性和投入度

评估标准：
- 优秀(0.8-1.0): 深入理解，能够灵活应用
- 良好(0.6-0.8): 基本理解，部分能够应用
- 及格(0.4-0.6): 浅层理解，需要引导
- 不足(0.0-0.4): 理解有误，需要重新学习

请提供具体的评估结果和改进建议。"""),
            
            ("human", """请评估学习者的当前进度：

**学习主题**: {topic}
**对话历史**: {conversation_history}
**学习者表现**: {learner_performance}
**时间投入**: {time_spent}
**互动质量**: {interaction_quality}

请提供详细的进度评估报告。""")
        ])
        
        # 节奏控制提示词
        self.pace_control_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位学习节奏控制专家，擅长根据学习者的表现调整学习的速度和深度。

节奏控制策略：
1. **加速**: 学习者理解快速，可以增加难度或扩展内容
2. **减速**: 学习者跟不上，需要放慢节奏，增加支持
3. **维持**: 当前节奏合适，继续保持
4. **调整**: 根据具体情况灵活调整

影响因素：
- 学习者的认知负荷
- 概念的复杂程度
- 时间压力
- 学习动机
- 疲劳程度

调整原则：
- 保持适度挑战，避免过于简单或困难
- 及时响应学习者的反馈信号
- 平衡深度和广度
- 考虑长期学习效果"""),
            
            ("human", """请为当前学习情况制定节奏控制策略：

**当前状态**: {current_status}
**学习者反馈**: {learner_feedback}
**表现指标**: {performance_metrics}
**时间约束**: {time_constraints}
**学习目标**: {learning_goals}

请提供节奏调整建议。""")
        ])
    
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理编排任务"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.WORKFLOW_ORCHESTRATION:
                result = await self._orchestrate_conversation(task.input_data, context)
            elif task.task_type == "progress_assessment":
                result = await self._assess_learning_progress(task.input_data, context)
            elif task.task_type == "pace_control":
                result = await self._control_learning_pace(task.input_data, context)
            elif task.task_type == "agent_coordination":
                result = await self._coordinate_agents(task.input_data, context)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            processing_time = time.time() - start_time
            
            return create_response(
                agent_id=self.metadata.agent_id,
                agent_type=self.metadata.agent_type,
                task_id=task.task_id,
                success=True,
                processing_time=processing_time,
                result=result
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return create_response(
                agent_id=self.metadata.agent_id,
                agent_type=self.metadata.agent_type,
                task_id=task.task_id,
                success=False,
                processing_time=processing_time,
                error=str(e)
            )
    
    async def _orchestrate_conversation(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """编排对话流程"""
        
        # 分析当前状态
        current_phase = self._determine_current_phase(context)
        progress_analysis = self._analyze_learning_progress(context)
        agent_status = self._get_agent_status(input_data)
        
        # 构建编排提示
        messages = self.orchestration_prompt.format_messages(
            topic=context.topic,
            current_phase=current_phase.value,
            duration_minutes=self._calculate_duration(context),
            user_explanation=context.user_explanation,
            progress_analysis=json.dumps(progress_analysis, ensure_ascii=False),
            agent_status=json.dumps(agent_status, ensure_ascii=False),
            doubt_analysis=json.dumps(context.analysis_results.get("unclear_points", []), ensure_ascii=False),
            validation_results=json.dumps(context.analysis_results.get("validation", {}), ensure_ascii=False),
            question_strategy=json.dumps(context.analysis_results.get("questions", {}), ensure_ascii=False),
            time_constraint=input_data.get("time_constraint", "normal"),
            complexity_requirement=input_data.get("complexity", "medium")
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 解析编排决策
            decision = OrchestrationDecision(
                next_phase=ConversationPhase(result_data.get("next_phase", "exploration")),
                recommended_action=ConversationAction(result_data.get("action", "continue_current")),
                target_agents=[AgentType(agent) for agent in result_data.get("target_agents", [])],
                priority_tasks=result_data.get("priority_tasks", []),
                timing_strategy=result_data.get("timing_strategy", "immediate"),
                expected_duration=result_data.get("duration", 10),
                success_criteria=result_data.get("success_criteria", [])
            )
            
            # 生成执行计划
            execution_plan = self._create_execution_plan(decision, context)
            
            return {
                "orchestration_decision": decision.dict(),
                "execution_plan": execution_plan,
                "next_steps": result_data.get("next_steps", []),
                "success": True
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # 降级处理
            fallback_decision = self._create_fallback_decision(context)
            return {
                "orchestration_decision": fallback_decision.dict(),
                "execution_plan": self._create_execution_plan(fallback_decision, context),
                "success": False,
                "error": f"编排决策失败，使用降级策略: {str(e)}"
            }
    
    async def _assess_learning_progress(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """评估学习进度"""
        
        # 构建评估数据
        conversation_history = json.dumps(context.conversation_history, ensure_ascii=False)
        learner_performance = self._analyze_learner_performance(context)
        
        messages = self.progress_assessment_prompt.format_messages(
            topic=context.topic,
            conversation_history=conversation_history,
            learner_performance=json.dumps(learner_performance, ensure_ascii=False),
            time_spent=self._calculate_duration(context),
            interaction_quality=self._assess_interaction_quality(context)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 更新学习进度
            progress = LearningProgress(
                current_phase=ConversationPhase(result_data.get("current_phase", "exploration")),
                completed_phases=[ConversationPhase(p) for p in result_data.get("completed_phases", [])],
                understanding_level=result_data.get("understanding_level", 0.5),
                engagement_score=result_data.get("engagement_score", 0.5),
                learning_velocity=result_data.get("learning_velocity", 0.5),
                knowledge_gaps=result_data.get("knowledge_gaps", []),
                mastered_concepts=result_data.get("mastered_concepts", [])
            )
            
            # 保存进度
            self.learning_progress[context.session_id] = progress
            
            return {
                "learning_progress": progress.dict(),
                "assessment_summary": result_data.get("summary", ""),
                "recommendations": result_data.get("recommendations", []),
                "success": True
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "learning_progress": self._create_default_progress(),
                "assessment_summary": "进度评估失败",
                "success": False,
                "error": str(e)
            }
    
    async def _control_learning_pace(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """控制学习节奏"""
        
        current_status = self._get_current_status(context)
        performance_metrics = self._get_performance_metrics(context)
        
        messages = self.pace_control_prompt.format_messages(
            current_status=json.dumps(current_status, ensure_ascii=False),
            learner_feedback=input_data.get("feedback", "无特殊反馈"),
            performance_metrics=json.dumps(performance_metrics, ensure_ascii=False),
            time_constraints=input_data.get("time_constraints", "normal"),
            learning_goals=json.dumps(input_data.get("goals", []), ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            return {
                "pace_recommendation": result_data.get("pace", "normal"),
                "adjustments": result_data.get("adjustments", []),
                "reasoning": result_data.get("reasoning", ""),
                "expected_impact": result_data.get("impact", ""),
                "success": True
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "pace_recommendation": "normal",
                "adjustments": ["保持当前节奏"],
                "success": False,
                "error": str(e)
            }
    
    async def _coordinate_agents(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """协调其他Agent"""
        
        # 分析任务需求
        task_requirements = input_data.get("requirements", {})
        available_agents = input_data.get("available_agents", [])
        
        # 创建任务分配计划
        task_assignments = []
        
        # 根据需求分配任务
        if task_requirements.get("need_validation", False):
            task = create_task(
                task_type="knowledge_validation",
                input_data={"explanation": context.user_explanation},
                context={"session_id": context.session_id}
            )
            task_assignments.append({
                "agent": AgentType.KNOWLEDGE_VALIDATOR,
                "task": task.dict(),
                "priority": "high"
            })
        
        if task_requirements.get("need_questions", False):
            task = create_task(
                task_type="question_generation",
                input_data={"unclear_points": context.unclear_points},
                context={"session_id": context.session_id}
            )
            task_assignments.append({
                "agent": AgentType.QUESTION_STRATEGIST,
                "task": task.dict(),
                "priority": "medium"
            })
        
        return {
            "task_assignments": task_assignments,
            "execution_order": self._determine_execution_order(task_assignments),
            "coordination_strategy": "parallel_execution",
            "success": True
        }
    
    def _determine_current_phase(self, context: ConversationContext) -> ConversationPhase:
        """确定当前对话阶段"""
        # 简化的阶段判断逻辑
        if len(context.conversation_history) == 0:
            return ConversationPhase.INITIALIZATION
        elif len(context.unclear_points) > 3:
            return ConversationPhase.EXPLORATION
        elif context.confidence_score < 0.6:
            return ConversationPhase.CLARIFICATION
        else:
            return ConversationPhase.DEEP_DIVE
    
    def _analyze_learning_progress(self, context: ConversationContext) -> Dict[str, Any]:
        """分析学习进度"""
        return {
            "interaction_count": len(context.conversation_history),
            "concept_coverage": len(context.analysis_results.get("key_concepts", [])),
            "clarity_score": context.confidence_score,
            "engagement_indicators": self._get_engagement_indicators(context)
        }
    
    def _get_agent_status(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "explanation_analyzer": {"status": "ready", "load": 0.3},
            "knowledge_validator": {"status": "ready", "load": 0.2},
            "question_strategist": {"status": "ready", "load": 0.1}
        }
    
    def _calculate_duration(self, context: ConversationContext) -> int:
        """计算对话持续时间"""
        # 简化计算：每轮对话约3分钟
        return len(context.conversation_history) * 3
    
    def _create_execution_plan(self, decision: OrchestrationDecision, context: ConversationContext) -> Dict[str, Any]:
        """创建执行计划"""
        return {
            "phase": decision.next_phase.value,
            "action": decision.recommended_action.value,
            "agents_to_call": [agent.value for agent in decision.target_agents],
            "estimated_time": decision.expected_duration,
            "success_metrics": decision.success_criteria
        }
    
    def _create_fallback_decision(self, context: ConversationContext) -> OrchestrationDecision:
        """创建降级决策"""
        return OrchestrationDecision(
            next_phase=ConversationPhase.EXPLORATION,
            recommended_action=ConversationAction.CONTINUE_CURRENT_TOPIC,
            target_agents=[AgentType.QUESTION_STRATEGIST],
            priority_tasks=[],
            timing_strategy="immediate",
            expected_duration=10,
            success_criteria=["生成有效问题"]
        )
    
    def _analyze_learner_performance(self, context: ConversationContext) -> Dict[str, Any]:
        """分析学习者表现"""
        return {
            "explanation_quality": len(context.user_explanation) / 100,  # 简化评分
            "concept_accuracy": context.confidence_score,
            "interaction_frequency": len(context.conversation_history),
            "depth_indicators": len(context.analysis_results.get("key_concepts", []))
        }
    
    def _assess_interaction_quality(self, context: ConversationContext) -> float:
        """评估互动质量"""
        # 简化评估
        return min(1.0, len(context.conversation_history) * 0.2)
    
    def _create_default_progress(self) -> Dict[str, Any]:
        """创建默认进度"""
        return {
            "current_phase": "exploration",
            "understanding_level": 0.5,
            "engagement_score": 0.5,
            "learning_velocity": 0.5
        }
    
    def _get_current_status(self, context: ConversationContext) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "phase": self._determine_current_phase(context).value,
            "progress": context.confidence_score,
            "time_spent": self._calculate_duration(context)
        }
    
    def _get_performance_metrics(self, context: ConversationContext) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "understanding_trend": "improving" if context.confidence_score > 0.5 else "needs_support",
            "engagement_level": "high" if len(context.conversation_history) > 3 else "moderate",
            "concept_mastery": len(context.analysis_results.get("key_concepts", []))
        }
    
    def _get_engagement_indicators(self, context: ConversationContext) -> Dict[str, Any]:
        """获取参与度指标"""
        return {
            "response_length": len(context.user_explanation),
            "question_asking": 0,  # 简化
            "elaboration_tendency": context.confidence_score
        }
    
    def _determine_execution_order(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """确定执行顺序"""
        # 按优先级排序
        sorted_assignments = sorted(assignments, key=lambda x: {"high": 1, "medium": 2, "low": 3}.get(x["priority"], 2))
        return [a["agent"] for a in sorted_assignments]
    
    async def handle_message(self, message) -> Optional:
        """处理消息（暂时简化实现）"""
        return None
