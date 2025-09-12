"""
QuestionStrategist Agent - 问题策略Agent

负责根据疑点生成不同类型的问题、调整问题难度和深度、选择最佳提问策略。
这个Agent专门优化问题生成的质量和教学效果。
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
    ConversationContext, AgentResponse, TaskType, create_response
)
from feynman.core.config.settings import get_settings


class QuestionType(str, Enum):
    """问题类型"""
    CLARIFICATION = "clarification"      # 澄清型问题
    ELABORATION = "elaboration"          # 详述型问题
    EXAMPLE = "example"                  # 举例型问题
    APPLICATION = "application"          # 应用型问题
    COMPARISON = "comparison"            # 比较型问题
    CAUSE_EFFECT = "cause_effect"        # 因果型问题
    EVALUATION = "evaluation"            # 评估型问题
    SYNTHESIS = "synthesis"              # 综合型问题


class DifficultyLevel(str, Enum):
    """难度级别"""
    BASIC = "basic"           # 基础级别
    INTERMEDIATE = "intermediate"  # 中级级别
    ADVANCED = "advanced"     # 高级级别
    EXPERT = "expert"         # 专家级别


class TeachingStrategy(str, Enum):
    """教学策略"""
    SOCRATIC = "socratic"           # 苏格拉底式提问
    SCAFFOLDING = "scaffolding"     # 脚手架式引导
    CHALLENGE = "challenge"         # 挑战式提问
    SUPPORTIVE = "supportive"       # 支持式提问
    EXPLORATORY = "exploratory"     # 探索式提问


class Question(BaseModel):
    """问题定义"""
    content: str = Field(..., description="问题内容")
    question_type: QuestionType = Field(..., description="问题类型")
    difficulty: DifficultyLevel = Field(..., description="难度级别")
    strategy: TeachingStrategy = Field(..., description="教学策略")
    target_concept: str = Field(..., description="目标概念")
    expected_outcome: str = Field(..., description="期望的学习成果")
    follow_up_questions: List[str] = Field(default_factory=list, description="后续问题")
    hints: List[str] = Field(default_factory=list, description="提示信息")


class QuestionSet(BaseModel):
    """问题集合"""
    primary_questions: List[Question] = Field(default_factory=list, description="主要问题")
    follow_up_questions: List[Question] = Field(default_factory=list, description="跟进问题")
    challenge_questions: List[Question] = Field(default_factory=list, description="挑战问题")
    total_estimated_time: int = Field(..., description="预估总时间(分钟)")
    learning_objectives: List[str] = Field(default_factory=list, description="学习目标")


class StrategyRecommendation(BaseModel):
    """策略推荐"""
    recommended_strategy: TeachingStrategy = Field(..., description="推荐策略")
    reasoning: str = Field(..., description="推荐理由")
    alternative_strategies: List[TeachingStrategy] = Field(default_factory=list, description="备选策略")
    adaptation_suggestions: List[str] = Field(default_factory=list, description="适应性建议")


class QuestionStrategist(AgentInterface):
    """问题策略Agent"""
    
    def __init__(self):
        """初始化问题策略Agent"""
        
        # 定义Agent能力
        capabilities = [
            AgentCapability(
                name="strategic_question_generation",
                description="基于策略生成高质量问题",
                input_types=["unclear_points", "context", "learning_goals"],
                output_types=["question_set", "strategy_recommendation"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="difficulty_adaptation",
                description="根据学习者水平调整问题难度",
                input_types=["learner_profile", "performance_history"],
                output_types=["adapted_questions", "difficulty_recommendation"],
                complexity_level="medium"
            ),
            AgentCapability(
                name="teaching_strategy_selection",
                description="选择最适合的教学策略",
                input_types=["learning_context", "concept_type", "learner_needs"],
                output_types=["strategy_recommendation", "teaching_plan"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="question_sequencing",
                description="优化问题顺序和逻辑流程",
                input_types=["question_list", "learning_objectives"],
                output_types=["sequenced_questions", "learning_path"],
                complexity_level="medium"
            )
        ]
        
        # 初始化元数据
        metadata = AgentMetadata(
            agent_type=AgentType.QUESTION_STRATEGIST,
            name="QuestionStrategist",
            version="1.0.0",
            capabilities=capabilities,
            dependencies=[AgentType.KNOWLEDGE_VALIDATOR],  # 依赖知识验证结果
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
                temperature=0.7  # 问题生成需要一定创造性
            )
        elif settings.llm_provider == "zhipu" and settings.zhipu_api_key:
            return ChatZhipuAI(
                api_key=settings.zhipu_api_key,
                model=settings.zhipu_model,
                temperature=0.7
            )
        else:
            raise ValueError("未配置可用的LLM模型")
    
    def _init_prompts(self):
        """初始化提示词模板"""
        
        # 策略问题生成提示词
        self.strategic_question_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位经验丰富的教育策略专家，擅长设计高质量的教学问题。

你的核心能力：
1. **苏格拉底式提问**: 通过层层递进的问题引导思考
2. **差异化教学**: 根据学习者水平调整问题难度
3. **多元化策略**: 运用不同类型的问题达成学习目标
4. **认知负荷管理**: 合理安排问题的复杂度和顺序

问题类型及其用途：
- **澄清型**: 明确概念定义和理解边界
- **详述型**: 深化对机制和原理的理解
- **举例型**: 通过具体实例加深理解
- **应用型**: 将知识运用到新情境
- **比较型**: 区分相似概念，突出差异
- **因果型**: 探讨原因和结果的关系
- **评估型**: 判断价值、效果或合理性
- **综合型**: 整合多个概念形成系统理解

教学策略：
- **苏格拉底式**: 通过问题引导学生自己发现答案
- **脚手架式**: 提供逐步递减的支持和提示
- **挑战式**: 提出有一定难度的问题促进深度思考
- **支持式**: 鼓励性问题建立学习信心
- **探索式**: 开放性问题鼓励创新思维

请始终考虑学习者的认知特点和学习目标。"""),
            
            ("human", """请为以下疑点设计高质量的教学问题：

**学习主题**: {topic}

**学习者解释**: 
{user_explanation}

**识别的疑点**:
{unclear_points}

**学习者水平**: {learner_level}

**上下文信息**:
{context_info}

**设计要求**:
1. 为每个疑点设计2-3个不同类型的问题
2. 问题应该循序渐进，由浅入深
3. 考虑学习者的认知负荷
4. 提供适当的提示和引导
5. 设计一些挑战性问题促进深度思考

请返回JSON格式的问题设计方案。""")
        ])
        
        # 策略选择提示词
        self.strategy_selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位教学策略顾问，专门为不同的学习情境推荐最适合的教学策略。

策略选择考虑因素：
1. **学习者特征**: 知识基础、学习风格、动机水平
2. **内容特点**: 概念复杂度、抽象程度、实践性
3. **学习目标**: 理解深度、应用能力、批判思维
4. **情境约束**: 时间限制、互动方式、资源可用性

策略适用场景：
- **苏格拉底式**: 适合概念澄清和逻辑推理
- **脚手架式**: 适合复杂概念的分步理解
- **挑战式**: 适合有一定基础的学习者
- **支持式**: 适合缺乏信心或基础薄弱的学习者
- **探索式**: 适合培养创新思维和开放性思考

请提供具体的策略建议和实施要点。"""),
            
            ("human", """请为以下学习情境推荐最佳教学策略：

**学习主题**: {topic}
**疑点类型**: {doubt_types}
**学习者水平**: {learner_level}
**学习目标**: {learning_objectives}
**时间约束**: {time_constraint}

**学习者表现分析**:
{learner_analysis}

请提供策略推荐和具体的实施建议。""")
        ])
        
        # 难度调整提示词
        self.difficulty_adaptation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位适应性学习专家，擅长根据学习者的能力水平调整教学内容的难度。

难度级别特征：
- **基础级**: 关注核心概念，使用简单语言，提供充分支持
- **中级级**: 涉及概念间关系，要求一定的分析能力
- **高级级**: 需要综合运用，处理复杂情境
- **专家级**: 涉及创新应用，批判性评估

调整策略：
1. **降低难度**: 分解复杂概念，增加具体例子，提供更多提示
2. **提高难度**: 增加抽象层次，引入新变量，减少支持信息
3. **个性化**: 根据学习者的强项和弱项调整重点

调整原则：
- 保持适度挑战，避免过于简单或困难
- 循序渐进，建立学习信心
- 关注学习过程，及时调整策略"""),
            
            ("human", """请调整以下问题的难度级别：

**原始问题集**:
{original_questions}

**目标难度**: {target_difficulty}
**学习者能力评估**: {ability_assessment}
**调整理由**: {adjustment_reason}

请提供调整后的问题和调整说明。""")
        ])
    
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理问题策略任务"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.QUESTION_GENERATION:
                result = await self._generate_strategic_questions(task.input_data, context)
            elif task.task_type == TaskType.STRATEGY_SELECTION:
                result = await self._select_teaching_strategy(task.input_data, context)
            elif task.task_type == "difficulty_adaptation":
                result = await self._adapt_difficulty(task.input_data, context)
            elif task.task_type == "question_sequencing":
                result = await self._sequence_questions(task.input_data, context)
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
    
    async def _generate_strategic_questions(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """生成策略性问题"""
        unclear_points = input_data.get("unclear_points", context.unclear_points)
        learner_level = input_data.get("learner_level", "intermediate")
        
        # 构建上下文信息
        context_info = {
            "conversation_history": len(context.conversation_history),
            "knowledge_depth": context.analysis_results.get("knowledge_depth", "unknown"),
            "confidence_score": context.confidence_score
        }
        
        messages = self.strategic_question_prompt.format_messages(
            topic=context.topic,
            user_explanation=context.user_explanation,
            unclear_points=json.dumps(unclear_points, ensure_ascii=False),
            learner_level=learner_level,
            context_info=json.dumps(context_info, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            # 解析问题集合
            question_set = self._parse_question_set(result_data)
            
            # 生成策略推荐
            strategy_recommendation = self._generate_strategy_recommendation(
                unclear_points, learner_level, context
            )
            
            return {
                "question_set": question_set.dict(),
                "strategy_recommendation": strategy_recommendation.dict(),
                "total_questions": len(question_set.primary_questions) + len(question_set.follow_up_questions),
                "estimated_time": question_set.total_estimated_time,
                "success": True
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            # 降级处理：生成基础问题
            fallback_questions = self._generate_fallback_questions(unclear_points, context.topic)
            return {
                "question_set": {"primary_questions": fallback_questions},
                "strategy_recommendation": {"recommended_strategy": "supportive"},
                "total_questions": len(fallback_questions),
                "estimated_time": len(fallback_questions) * 3,
                "success": False,
                "error": f"解析失败，使用降级策略: {str(e)}"
            }
    
    async def _select_teaching_strategy(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """选择教学策略"""
        doubt_types = input_data.get("doubt_types", ["conceptual"])
        learner_level = input_data.get("learner_level", "intermediate")
        learning_objectives = input_data.get("learning_objectives", ["understanding"])
        time_constraint = input_data.get("time_constraint", "moderate")
        
        # 分析学习者表现
        learner_analysis = self._analyze_learner_performance(context)
        
        messages = self.strategy_selection_prompt.format_messages(
            topic=context.topic,
            doubt_types=", ".join(doubt_types),
            learner_level=learner_level,
            learning_objectives=", ".join(learning_objectives),
            time_constraint=time_constraint,
            learner_analysis=json.dumps(learner_analysis, ensure_ascii=False)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            recommendation = StrategyRecommendation(
                recommended_strategy=TeachingStrategy(result_data.get("recommended_strategy", "supportive")),
                reasoning=result_data.get("reasoning", "基于学习情境的综合考虑"),
                alternative_strategies=[TeachingStrategy(s) for s in result_data.get("alternatives", [])],
                adaptation_suggestions=result_data.get("adaptations", [])
            )
            
            return {
                "strategy_recommendation": recommendation.dict(),
                "implementation_guide": result_data.get("implementation_guide", []),
                "expected_outcomes": result_data.get("expected_outcomes", []),
                "success": True
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            # 降级处理
            return {
                "strategy_recommendation": {
                    "recommended_strategy": "supportive",
                    "reasoning": "使用默认支持式策略",
                    "alternative_strategies": ["socratic", "scaffolding"],
                    "adaptation_suggestions": ["根据学习者反馈调整"]
                },
                "success": False,
                "error": f"策略选择失败: {str(e)}"
            }
    
    async def _adapt_difficulty(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """调整问题难度"""
        original_questions = input_data.get("questions", [])
        target_difficulty = input_data.get("target_difficulty", "intermediate")
        ability_assessment = input_data.get("ability_assessment", {})
        
        messages = self.difficulty_adaptation_prompt.format_messages(
            original_questions=json.dumps(original_questions, ensure_ascii=False),
            target_difficulty=target_difficulty,
            ability_assessment=json.dumps(ability_assessment, ensure_ascii=False),
            adjustment_reason=input_data.get("reason", "优化学习体验")
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            adapted_questions = result_data.get("adapted_questions", original_questions)
            
            return {
                "adapted_questions": adapted_questions,
                "adjustment_summary": result_data.get("adjustment_summary", ""),
                "difficulty_changes": result_data.get("difficulty_changes", []),
                "success": True
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "adapted_questions": original_questions,
                "adjustment_summary": "难度调整失败，保持原始问题",
                "success": False,
                "error": str(e)
            }
    
    async def _sequence_questions(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """优化问题顺序"""
        questions = input_data.get("questions", [])
        learning_objectives = input_data.get("learning_objectives", [])
        
        # 简化的问题排序逻辑
        sequenced_questions = self._apply_question_sequencing_rules(questions, learning_objectives)
        
        return {
            "sequenced_questions": sequenced_questions,
            "sequencing_rationale": "按照认知负荷和逻辑依赖关系排序",
            "learning_path": self._generate_learning_path(sequenced_questions),
            "success": True
        }
    
    def _parse_question_set(self, result_data: Dict[str, Any]) -> QuestionSet:
        """解析问题集合"""
        primary_questions = []
        for q_data in result_data.get("primary_questions", []):
            question = Question(
                content=q_data.get("content", ""),
                question_type=QuestionType(q_data.get("type", "clarification")),
                difficulty=DifficultyLevel(q_data.get("difficulty", "intermediate")),
                strategy=TeachingStrategy(q_data.get("strategy", "supportive")),
                target_concept=q_data.get("target_concept", ""),
                expected_outcome=q_data.get("expected_outcome", ""),
                follow_up_questions=q_data.get("follow_ups", []),
                hints=q_data.get("hints", [])
            )
            primary_questions.append(question)
        
        return QuestionSet(
            primary_questions=primary_questions,
            follow_up_questions=[],  # 简化处理
            challenge_questions=[],  # 简化处理
            total_estimated_time=result_data.get("estimated_time", len(primary_questions) * 3),
            learning_objectives=result_data.get("learning_objectives", [])
        )
    
    def _generate_strategy_recommendation(self, unclear_points: List, learner_level: str, context: ConversationContext) -> StrategyRecommendation:
        """生成策略推荐"""
        # 简化的策略选择逻辑
        if len(unclear_points) > 3:
            strategy = TeachingStrategy.SCAFFOLDING
            reasoning = "疑点较多，采用脚手架式逐步引导"
        elif context.confidence_score < 0.5:
            strategy = TeachingStrategy.SUPPORTIVE
            reasoning = "学习者信心不足，采用支持式提问"
        else:
            strategy = TeachingStrategy.SOCRATIC
            reasoning = "适合使用苏格拉底式提问深化理解"
        
        return StrategyRecommendation(
            recommended_strategy=strategy,
            reasoning=reasoning,
            alternative_strategies=[TeachingStrategy.EXPLORATORY, TeachingStrategy.CHALLENGE],
            adaptation_suggestions=["根据学习者反应调整提问节奏"]
        )
    
    def _generate_fallback_questions(self, unclear_points: List, topic: str) -> List[Dict[str, Any]]:
        """生成降级问题"""
        questions = []
        for i, point in enumerate(unclear_points[:3]):  # 限制数量
            question = {
                "content": f"关于{topic}中的'{point}'，你能详细解释一下吗？",
                "type": "clarification",
                "difficulty": "basic",
                "strategy": "supportive"
            }
            questions.append(question)
        return questions
    
    def _analyze_learner_performance(self, context: ConversationContext) -> Dict[str, Any]:
        """分析学习者表现"""
        return {
            "explanation_length": len(context.user_explanation),
            "concept_coverage": len(context.analysis_results.get("key_concepts", [])),
            "confidence_indicators": context.confidence_score,
            "interaction_history": len(context.conversation_history)
        }
    
    def _apply_question_sequencing_rules(self, questions: List[Dict], objectives: List[str]) -> List[Dict]:
        """应用问题排序规则"""
        # 简单排序：澄清型 -> 详述型 -> 应用型
        type_priority = {
            "clarification": 1,
            "elaboration": 2,
            "example": 3,
            "application": 4,
            "evaluation": 5
        }
        
        return sorted(questions, key=lambda q: type_priority.get(q.get("type", "clarification"), 3))
    
    def _generate_learning_path(self, questions: List[Dict]) -> List[str]:
        """生成学习路径"""
        path = []
        for i, question in enumerate(questions):
            step = f"步骤{i+1}: {question.get('type', 'unknown')}型问题 - {question.get('target_concept', '概念理解')}"
            path.append(step)
        return path
    
    async def handle_message(self, message) -> Optional:
        """处理消息（暂时简化实现）"""
        return None
