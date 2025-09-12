"""
InsightSynthesizer Agent - 洞察综合Agent

负责总结学习过程中的关键洞察、识别知识点之间的联系、生成学习报告。
这个Agent专门处理知识的整合和深层次理解的生成。
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
from datetime import datetime

from .agent_protocol import (
    AgentInterface, AgentMetadata, AgentCapability, AgentType, AgentTask, 
    ConversationContext, AgentResponse, TaskType, create_response
)
from feynman.core.config.settings import get_settings


class InsightType(str, Enum):
    """洞察类型"""
    CONCEPTUAL_BREAKTHROUGH = "conceptual_breakthrough"    # 概念突破
    CONNECTION_DISCOVERY = "connection_discovery"          # 连接发现
    MISCONCEPTION_CORRECTION = "misconception_correction"  # 误解纠正
    APPLICATION_INSIGHT = "application_insight"            # 应用洞察
    META_LEARNING = "meta_learning"                        # 元学习洞察
    KNOWLEDGE_GAP_IDENTIFICATION = "gap_identification"    # 知识缺口识别


class LearningInsight(BaseModel):
    """学习洞察"""
    insight_type: InsightType = Field(..., description="洞察类型")
    content: str = Field(..., description="洞察内容")
    related_concepts: List[str] = Field(default_factory=list, description="相关概念")
    significance_score: float = Field(..., description="重要性评分 0-1")
    evidence: List[str] = Field(default_factory=list, description="支持证据")
    implications: List[str] = Field(default_factory=list, description="学习意义")
    actionable_suggestions: List[str] = Field(default_factory=list, description="可行建议")


class KnowledgeConnection(BaseModel):
    """知识连接"""
    concept_a: str = Field(..., description="概念A")
    concept_b: str = Field(..., description="概念B")
    connection_type: str = Field(..., description="连接类型")
    relationship_description: str = Field(..., description="关系描述")
    strength: float = Field(..., description="连接强度 0-1")
    examples: List[str] = Field(default_factory=list, description="连接示例")


class LearningReport(BaseModel):
    """学习报告"""
    session_id: str = Field(..., description="会话ID")
    topic: str = Field(..., description="学习主题")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    
    # 核心内容
    key_insights: List[LearningInsight] = Field(default_factory=list, description="关键洞察")
    knowledge_connections: List[KnowledgeConnection] = Field(default_factory=list, description="知识连接")
    
    # 学习评估
    overall_understanding: float = Field(..., description="整体理解水平")
    concept_mastery: Dict[str, float] = Field(default_factory=dict, description="概念掌握度")
    learning_progress: float = Field(..., description="学习进度")
    
    # 改进建议
    strengths: List[str] = Field(default_factory=list, description="学习优势")
    areas_for_improvement: List[str] = Field(default_factory=list, description="改进领域")
    next_steps: List[str] = Field(default_factory=list, description="后续步骤")
    
    # 资源推荐
    recommended_resources: List[str] = Field(default_factory=list, description="推荐资源")
    practice_suggestions: List[str] = Field(default_factory=list, description="练习建议")


class InsightSynthesizer(AgentInterface):
    """洞察综合Agent"""
    
    def __init__(self):
        """初始化洞察综合Agent"""
        
        # 定义Agent能力
        capabilities = [
            AgentCapability(
                name="insight_extraction",
                description="从学习过程中提取关键洞察",
                input_types=["conversation_history", "analysis_results", "learning_context"],
                output_types=["learning_insights", "breakthrough_analysis"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="knowledge_connection_mapping",
                description="识别和映射知识点之间的连接",
                input_types=["concept_list", "explanation_analysis", "domain_knowledge"],
                output_types=["connection_map", "relationship_analysis"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="learning_report_generation",
                description="生成综合性学习报告",
                input_types=["learning_session", "progress_data", "assessment_results"],
                output_types=["learning_report", "progress_summary"],
                complexity_level="medium"
            ),
            AgentCapability(
                name="meta_learning_analysis",
                description="分析学习过程本身的特点和模式",
                input_types=["learning_behavior", "interaction_patterns"],
                output_types=["meta_insights", "learning_strategy_analysis"],
                complexity_level="complex"
            )
        ]
        
        # 初始化元数据
        metadata = AgentMetadata(
            agent_type=AgentType.INSIGHT_SYNTHESIZER,
            name="InsightSynthesizer",
            version="1.0.0",
            capabilities=capabilities,
            dependencies=[
                AgentType.EXPLANATION_ANALYZER,
                AgentType.KNOWLEDGE_VALIDATOR,
                AgentType.CONVERSATION_ORCHESTRATOR
            ],
            max_concurrent_tasks=2
        )
        
        super().__init__(metadata)
        
        # 初始化LLM
        self.llm = self._init_llm()
        
        # 初始化提示词模板
        self._init_prompts()
    
    def _init_llm(self):
        """初始化LLM模型"""
        settings = get_settings()
        
        # 优先使用OpenAI
        if settings.openai_api_key:
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.5  # 洞察综合需要平衡创造性和准确性
            )
        elif settings.llm_provider == "zhipu" and settings.zhipu_api_key:
            return ChatZhipuAI(
                api_key=settings.zhipu_api_key,
                model=settings.zhipu_model,
                temperature=0.5
            )
        else:
            raise ValueError("未配置可用的LLM模型")
    
    def _init_prompts(self):
        """初始化提示词模板"""
        
        # 洞察提取提示词
        self.insight_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位深度学习分析专家，擅长从学习过程中提取有价值的洞察和发现。

你的专长包括：
1. **概念突破识别**: 发现学习者理解上的重大进展
2. **连接发现**: 识别概念间的新联系和关系
3. **误解纠正分析**: 分析误解的根源和纠正过程
4. **应用洞察**: 发现知识的实际应用价值
5. **元学习洞察**: 理解学习过程本身的特点

洞察质量标准：
- **深度性**: 超越表面现象，触及本质
- **连接性**: 建立概念间的有意义联系
- **实用性**: 对后续学习具有指导意义
- **可验证性**: 基于具体证据和表现

分析维度：
- 理解的转变过程
- 概念掌握的里程碑
- 思维模式的改变
- 应用能力的发展
- 学习策略的优化

请提供深入而有价值的洞察分析。"""),
            
            ("human", """请从以下学习过程中提取关键洞察：

**学习主题**: {topic}

**对话历程**:
{conversation_history}

**分析结果汇总**:
{analysis_summary}

**学习者表现变化**:
{performance_changes}

**重点关注**:
- 理解上的突破性进展
- 概念间的新发现连接
- 误解的识别和纠正
- 应用思维的发展
- 学习策略的演进

请提供结构化的洞察分析。""")
        ])
        
        # 知识连接映射提示词
        self.connection_mapping_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位知识结构专家，专门识别和分析概念间的深层连接。

连接类型分析：
1. **因果关系**: 原因和结果的关系
2. **层次关系**: 上下级、包含关系
3. **对比关系**: 相似性和差异性
4. **功能关系**: 作用和影响关系
5. **时序关系**: 时间上的先后关系
6. **条件关系**: 前提和结果关系

连接强度评估：
- **强连接(0.8-1.0)**: 直接相关，密不可分
- **中等连接(0.5-0.8)**: 相关性明显，有重要联系
- **弱连接(0.2-0.5)**: 间接相关，有一定联系
- **微弱连接(0.0-0.2)**: 关系不明显或很间接

分析原则：
- 基于学习者的实际理解
- 关注有教育价值的连接
- 考虑概念的实际应用场景
- 识别潜在的混淆点"""),
            
            ("human", """请分析以下概念间的知识连接：

**学习主题**: {topic}

**涉及概念**: 
{concepts_list}

**学习者理解**: 
{learner_understanding}

**上下文信息**: 
{context_information}

请识别和分析重要的概念连接关系。""")
        ])
        
        # 学习报告生成提示词
        self.report_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的学习评估专家，擅长生成全面而有用的学习报告。

报告结构要求：
1. **执行摘要**: 简洁的整体评估
2. **关键成就**: 主要的学习收获
3. **洞察发现**: 重要的理解突破
4. **知识网络**: 概念间的连接图谱
5. **能力评估**: 各方面能力的发展水平
6. **改进建议**: 具体的提升方向
7. **学习路径**: 后续学习的建议

评估维度：
- **理解深度**: 从记忆到应用的层次
- **概念掌握**: 核心概念的准确性
- **连接能力**: 整合不同知识点的能力
- **应用思维**: 将知识用于解决问题的能力
- **元认知**: 对学习过程的反思能力

报告特点：
- 基于事实和证据
- 平衡优势和不足
- 提供可行的建议
- 鼓励持续学习"""),
            
            ("human", """请为以下学习会话生成综合报告：

**基本信息**:
- 主题: {topic}
- 会话时长: {duration}
- 互动轮次: {interaction_count}

**学习内容分析**:
{content_analysis}

**关键洞察**:
{key_insights}

**知识连接**:
{knowledge_connections}

**表现评估**:
{performance_assessment}

请生成详细的学习报告。""")
        ])
        
        # 元学习分析提示词
        self.meta_learning_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位元学习研究专家，专门分析学习过程本身的特点和模式。

元学习分析维度：
1. **学习策略**: 学习者采用的方法和技巧
2. **认知模式**: 思维和理解的特点
3. **学习节奏**: 进展的速度和节奏控制
4. **反思能力**: 对自己学习的觉察和调整
5. **适应性**: 根据反馈调整学习方法的能力

关注要点：
- 学习行为的模式和变化
- 有效和无效的学习策略
- 认知负荷的管理
- 动机和参与度的变化
- 自我调节的表现

分析价值：
- 帮助学习者了解自己的学习特点
- 识别可以优化的学习策略
- 提供个性化的学习建议
- 促进更有效的学习方法"""),
            
            ("human", """请分析以下学习过程的元学习特征：

**学习行为数据**:
{learning_behavior}

**互动模式**:
{interaction_patterns}

**策略使用情况**:
{strategy_usage}

**反思表现**:
{reflection_indicators}

请提供元学习分析和改进建议。""")
        ])
    
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理洞察综合任务"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.INSIGHT_SYNTHESIS:
                result = await self._synthesize_insights(task.input_data, context)
            elif task.task_type == "connection_mapping":
                result = await self._map_knowledge_connections(task.input_data, context)
            elif task.task_type == "report_generation":
                result = await self._generate_learning_report(task.input_data, context)
            elif task.task_type == "meta_learning_analysis":
                result = await self._analyze_meta_learning(task.input_data, context)
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
    
    async def _synthesize_insights(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """综合学习洞察"""
        
        # 构建分析数据
        conversation_history = json.dumps(context.conversation_history, ensure_ascii=False)
        analysis_summary = json.dumps(context.analysis_results, ensure_ascii=False)
        performance_changes = self._analyze_performance_changes(context)
        
        messages = self.insight_extraction_prompt.format_messages(
            topic=context.topic,
            conversation_history=conversation_history,
            analysis_summary=analysis_summary,
            performance_changes=json.dumps(performance_changes, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 解析洞察
            insights = []
            for insight_data in result_data.get("insights", []):
                insight = LearningInsight(
                    insight_type=InsightType(insight_data.get("type", "conceptual_breakthrough")),
                    content=insight_data.get("content", ""),
                    related_concepts=insight_data.get("concepts", []),
                    significance_score=insight_data.get("significance", 0.5),
                    evidence=insight_data.get("evidence", []),
                    implications=insight_data.get("implications", []),
                    actionable_suggestions=insight_data.get("suggestions", [])
                )
                insights.append(insight.dict())
            
            return {
                "insights": insights,
                "insight_summary": result_data.get("summary", ""),
                "breakthrough_moments": result_data.get("breakthroughs", []),
                "learning_patterns": result_data.get("patterns", []),
                "success": True
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # 降级处理
            fallback_insights = self._generate_fallback_insights(context)
            return {
                "insights": fallback_insights,
                "insight_summary": "洞察提取使用降级策略",
                "success": False,
                "error": str(e)
            }
    
    async def _map_knowledge_connections(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """映射知识连接"""
        
        # 提取概念列表
        concepts_list = input_data.get("concepts", context.analysis_results.get("key_concepts", []))
        learner_understanding = context.user_explanation
        context_info = json.dumps({
            "topic": context.topic,
            "unclear_points": context.unclear_points,
            "confidence": context.confidence_score
        }, ensure_ascii=False)
        
        messages = self.connection_mapping_prompt.format_messages(
            topic=context.topic,
            concepts_list=json.dumps(concepts_list, ensure_ascii=False),
            learner_understanding=learner_understanding,
            context_information=context_info
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 解析连接
            connections = []
            for conn_data in result_data.get("connections", []):
                connection = KnowledgeConnection(
                    concept_a=conn_data.get("concept_a", ""),
                    concept_b=conn_data.get("concept_b", ""),
                    connection_type=conn_data.get("type", "related"),
                    relationship_description=conn_data.get("description", ""),
                    strength=conn_data.get("strength", 0.5),
                    examples=conn_data.get("examples", [])
                )
                connections.append(connection.dict())
            
            return {
                "connections": connections,
                "connection_summary": result_data.get("summary", ""),
                "network_analysis": result_data.get("network_analysis", {}),
                "success": True
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            return {
                "connections": self._generate_basic_connections(concepts_list),
                "connection_summary": "连接映射使用基础策略",
                "success": False,
                "error": str(e)
            }
    
    async def _generate_learning_report(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """生成学习报告"""
        
        # 收集报告数据
        duration = input_data.get("duration", self._estimate_duration(context))
        interaction_count = len(context.conversation_history)
        
        # 构建分析数据
        content_analysis = self._analyze_learning_content(context)
        key_insights = input_data.get("insights", [])
        knowledge_connections = input_data.get("connections", [])
        performance_assessment = self._assess_overall_performance(context)
        
        messages = self.report_generation_prompt.format_messages(
            topic=context.topic,
            duration=f"{duration}分钟",
            interaction_count=interaction_count,
            content_analysis=json.dumps(content_analysis, ensure_ascii=False),
            key_insights=json.dumps(key_insights, ensure_ascii=False),
            knowledge_connections=json.dumps(knowledge_connections, ensure_ascii=False),
            performance_assessment=json.dumps(performance_assessment, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 构建学习报告
            report = LearningReport(
                session_id=context.session_id,
                topic=context.topic,
                key_insights=[],  # 简化处理
                knowledge_connections=[],  # 简化处理
                overall_understanding=result_data.get("overall_understanding", context.confidence_score),
                concept_mastery=result_data.get("concept_mastery", {}),
                learning_progress=result_data.get("learning_progress", 0.5),
                strengths=result_data.get("strengths", []),
                areas_for_improvement=result_data.get("improvements", []),
                next_steps=result_data.get("next_steps", []),
                recommended_resources=result_data.get("resources", []),
                practice_suggestions=result_data.get("practice", [])
            )
            
            return {
                "learning_report": report.dict(),
                "executive_summary": result_data.get("executive_summary", ""),
                "recommendations": result_data.get("recommendations", []),
                "success": True
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # 生成基础报告
            basic_report = self._generate_basic_report(context)
            return {
                "learning_report": basic_report,
                "executive_summary": "学习报告生成使用基础模板",
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_meta_learning(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """分析元学习特征"""
        
        learning_behavior = self._extract_learning_behavior(context)
        interaction_patterns = self._analyze_interaction_patterns(context)
        strategy_usage = self._identify_strategy_usage(context)
        reflection_indicators = self._assess_reflection_ability(context)
        
        messages = self.meta_learning_prompt.format_messages(
            learning_behavior=json.dumps(learning_behavior, ensure_ascii=False),
            interaction_patterns=json.dumps(interaction_patterns, ensure_ascii=False),
            strategy_usage=json.dumps(strategy_usage, ensure_ascii=False),
            reflection_indicators=json.dumps(reflection_indicators, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            return {
                "meta_learning_analysis": result_data.get("analysis", {}),
                "learning_style_profile": result_data.get("style_profile", {}),
                "strategy_recommendations": result_data.get("strategy_recommendations", []),
                "improvement_areas": result_data.get("improvement_areas", []),
                "success": True
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "meta_learning_analysis": {"error": "分析失败"},
                "learning_style_profile": {"style": "未知"},
                "success": False,
                "error": str(e)
            }
    
    def _analyze_performance_changes(self, context: ConversationContext) -> Dict[str, Any]:
        """分析表现变化"""
        return {
            "confidence_trend": "improving" if context.confidence_score > 0.5 else "stable",
            "explanation_quality": len(context.user_explanation) / 100,
            "concept_coverage": len(context.analysis_results.get("key_concepts", [])),
            "interaction_depth": len(context.conversation_history)
        }
    
    def _generate_fallback_insights(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """生成降级洞察"""
        insights = []
        
        if context.confidence_score > 0.7:
            insights.append({
                "type": "conceptual_breakthrough",
                "content": f"学习者对{context.topic}表现出良好的理解",
                "significance": 0.7
            })
        
        if len(context.unclear_points) > 0:
            insights.append({
                "type": "gap_identification", 
                "content": f"识别出{len(context.unclear_points)}个需要澄清的知识点",
                "significance": 0.6
            })
        
        return insights
    
    def _generate_basic_connections(self, concepts: List[str]) -> List[Dict[str, Any]]:
        """生成基础连接"""
        connections = []
        for i in range(min(len(concepts)-1, 3)):  # 限制数量
            connections.append({
                "concept_a": concepts[i],
                "concept_b": concepts[i+1],
                "type": "related",
                "description": f"{concepts[i]}与{concepts[i+1]}相关",
                "strength": 0.5
            })
        return connections
    
    def _estimate_duration(self, context: ConversationContext) -> int:
        """估算学习时长"""
        return len(context.conversation_history) * 3  # 每轮约3分钟
    
    def _analyze_learning_content(self, context: ConversationContext) -> Dict[str, Any]:
        """分析学习内容"""
        return {
            "topic_coverage": context.topic,
            "concept_count": len(context.analysis_results.get("key_concepts", [])),
            "explanation_length": len(context.user_explanation),
            "clarity_level": context.confidence_score
        }
    
    def _assess_overall_performance(self, context: ConversationContext) -> Dict[str, Any]:
        """评估整体表现"""
        return {
            "understanding_level": context.confidence_score,
            "participation": len(context.conversation_history),
            "concept_accuracy": len(context.analysis_results.get("key_concepts", [])) / max(len(context.unclear_points), 1)
        }
    
    def _generate_basic_report(self, context: ConversationContext) -> Dict[str, Any]:
        """生成基础报告"""
        return {
            "session_id": context.session_id,
            "topic": context.topic,
            "overall_understanding": context.confidence_score,
            "learning_progress": 0.5,
            "strengths": ["积极参与学习过程"],
            "areas_for_improvement": ["可以进一步深化理解"],
            "next_steps": ["继续练习相关概念"]
        }
    
    def _extract_learning_behavior(self, context: ConversationContext) -> Dict[str, Any]:
        """提取学习行为"""
        return {
            "explanation_style": "详细" if len(context.user_explanation) > 200 else "简洁",
            "question_response": "积极" if len(context.conversation_history) > 2 else "被动",
            "concept_usage": len(context.analysis_results.get("key_concepts", []))
        }
    
    def _analyze_interaction_patterns(self, context: ConversationContext) -> Dict[str, Any]:
        """分析互动模式"""
        return {
            "interaction_frequency": len(context.conversation_history),
            "response_depth": len(context.user_explanation) / max(len(context.conversation_history), 1),
            "engagement_consistency": "stable"
        }
    
    def _identify_strategy_usage(self, context: ConversationContext) -> Dict[str, Any]:
        """识别策略使用"""
        return {
            "explanation_strategy": "narrative" if len(context.user_explanation) > 100 else "concise",
            "concept_organization": "structured" if context.confidence_score > 0.6 else "loose"
        }
    
    def _assess_reflection_ability(self, context: ConversationContext) -> Dict[str, Any]:
        """评估反思能力"""
        return {
            "self_awareness": context.confidence_score,
            "uncertainty_acknowledgment": len(context.unclear_points) > 0,
            "improvement_orientation": True
        }
    
    async def handle_message(self, message) -> Optional:
        """处理消息（暂时简化实现）"""
        return None
