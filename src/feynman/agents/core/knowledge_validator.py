"""
KnowledgeValidator Agent - 知识验证Agent

负责验证用户解释的事实准确性、检查概念定义的正确性、识别常见误解。
这个Agent专门处理知识的准确性和可靠性问题。
"""

import json
import time
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from pydantic import BaseModel, Field

from .agent_protocol import (
    AgentInterface, AgentMetadata, AgentCapability, AgentType, AgentTask, 
    ConversationContext, AgentResponse, TaskType, create_response
)
from feynman.core.config.settings import get_settings


# =============================================================================
# 内嵌提示词模板
# =============================================================================

KNOWLEDGE_VALIDATOR_SYSTEM_PROMPT = """你是费曼学习系统的知识验证专家Agent，负责验证用户解释的事实准确性和概念正确性。

## 🎯 核心职责

1. **事实准确性验证**
   - 检查具体事实、数据和统计信息的准确性
   - 验证历史事件、日期和人物信息
   - 确认科学定律、公式和原理的正确性

2. **概念定义检查**
   - 验证专业术语和概念的定义准确性
   - 识别概念混淆和定义偏差
   - 检查概念之间的关系和层次结构

3. **逻辑一致性分析**
   - 检查论证逻辑的严密性
   - 识别逻辑跳跃和推理错误
   - 验证因果关系的合理性

4. **常见误解识别**
   - 识别领域内的常见误解和错误观念
   - 提供正确的解释和澄清
   - 标记需要特别注意的易错点

## 🔍 验证方法

1. **知识库查询**: 使用内置知识库验证基础事实
2. **Web搜索**: 查询最新信息和权威来源
3. **交叉验证**: 对比多个信息源确保准确性
4. **专家知识**: 应用领域专业知识进行判断

## 📊 严重程度分级

- **Critical**: 严重的事实错误，可能误导学习
- **Warning**: 概念不准确，需要澄清
- **Info**: 表述不够精确，建议改进

## 📤 输出格式

请以JSON格式输出验证结果：

```json
{
    "overall_accuracy": 0.85,
    "factual_errors": [
        {
            "content": "具体的错误内容",
            "severity": "critical|warning|info",
            "source": "错误来源定位",
            "suggestion": "修正建议",
            "reference": "参考资料链接"
        }
    ],
    "conceptual_issues": [
        {
            "content": "概念问题描述",
            "severity": "critical|warning|info",
            "correct_definition": "正确的概念定义",
            "common_misconception": "常见误解说明"
        }
    ],
    "critical_issues": [
        {
            "content": "严重问题描述",
            "impact": "对学习的影响",
            "priority": "修正优先级"
        }
    ],
    "validation_summary": "整体验证总结和建议",
    "confidence_score": 0.9,
    "verification_sources": ["source1", "source2"]
}
```

请严格按照科学和客观的标准进行验证，确保信息的准确性和可靠性。"""


class ValidationResult(BaseModel):
    """验证结果"""
    is_accurate: bool = Field(..., description="是否准确")
    confidence: float = Field(..., description="置信度 0-1")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    corrections: List[str] = Field(default_factory=list, description="建议的纠正")
    evidence: List[str] = Field(default_factory=list, description="支持证据")


class ConceptValidation(BaseModel):
    """概念验证结果"""
    concept: str = Field(..., description="概念名称")
    definition_accuracy: float = Field(..., description="定义准确度")
    common_misconceptions: List[str] = Field(default_factory=list, description="常见误解")
    correct_definition: Optional[str] = Field(default=None, description="正确定义")
    related_concepts: List[str] = Field(default_factory=list, description="相关概念")


class FactualValidation(BaseModel):
    """事实验证结果"""
    claim: str = Field(..., description="声明/事实")
    is_factual: bool = Field(..., description="是否为事实")
    evidence_strength: float = Field(..., description="证据强度")
    sources: List[str] = Field(default_factory=list, description="信息来源")
    alternative_views: List[str] = Field(default_factory=list, description="不同观点")


class KnowledgeValidationReport(BaseModel):
    """知识验证报告"""
    overall_accuracy: float = Field(..., description="整体准确性评分")
    concept_validations: List[ConceptValidation] = Field(default_factory=list, description="概念验证结果")
    factual_validations: List[FactualValidation] = Field(default_factory=list, description="事实验证结果")
    critical_issues: List[str] = Field(default_factory=list, description="关键问题")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")
    reliability_score: float = Field(..., description="可靠性评分")


class KnowledgeValidator(AgentInterface):
    """知识验证Agent"""
    
    def __init__(self):
        """初始化知识验证Agent"""
        
        # 定义Agent能力
        capabilities = [
            AgentCapability(
                name="factual_verification",
                description="验证事实声明的准确性",
                input_types=["text", "explanation", "claim"],
                output_types=["validation_result", "factual_validation"],
                complexity_level="medium"
            ),
            AgentCapability(
                name="concept_validation",
                description="验证概念定义的正确性",
                input_types=["concept", "definition", "explanation"],
                output_types=["concept_validation", "correction"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="misconception_detection",
                description="识别常见误解和错误观念",
                input_types=["explanation", "concept"],
                output_types=["misconception_list", "correction"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="knowledge_consistency_check",
                description="检查知识的内在一致性",
                input_types=["explanation", "multiple_concepts"],
                output_types=["consistency_report"],
                complexity_level="complex"
            )
        ]
        
        # 初始化元数据
        metadata = AgentMetadata(
            agent_type=AgentType.KNOWLEDGE_VALIDATOR,
            name="KnowledgeValidator",
            version="1.0.0",
            capabilities=capabilities,
            dependencies=[],  # 独立运行，不依赖其他Agent
            max_concurrent_tasks=3
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
                temperature=0.1  # 验证任务需要更准确的输出
            )
        elif settings.llm_provider == "zhipu" and settings.zhipu_api_key:
            return ChatZhipuAI(
                api_key=settings.zhipu_api_key,
                model=settings.zhipu_model,
                temperature=0.1
            )
        else:
            raise ValueError("未配置可用的LLM模型")
    
    def _init_prompts(self):
        """初始化提示词模板"""
        
        # 事实验证提示词
        self.factual_validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的事实验证专家，擅长验证信息的准确性和可靠性。

你的任务是验证用户解释中的事实声明，包括：
1. **事实准确性**: 声明是否符合已知事实
2. **证据强度**: 支持证据的可靠程度
3. **信息来源**: 信息的可能来源和权威性
4. **不确定性**: 识别存在争议或不确定的内容

评估标准：
- 高置信度(0.8-1.0): 有确凿证据支持的公认事实
- 中等置信度(0.5-0.8): 有一定证据但可能存在争议
- 低置信度(0.0-0.5): 缺乏证据或存在明显错误

请保持客观中立，承认知识的局限性。"""),
            
            ("human", """请验证以下解释中的事实声明：

**主题**: {topic}

**用户解释**:
{explanation}

**重点关注**:
{focus_areas}

请分析每个具体的事实声明，返回JSON格式的验证结果。""")
        ])
        
        # 概念验证提示词
        self.concept_validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个概念分析专家，专门验证概念定义的准确性和完整性。

你的职责包括：
1. **定义准确性**: 概念定义是否准确完整
2. **常见误解**: 识别该概念的典型误解
3. **概念边界**: 明确概念的适用范围和限制
4. **相关概念**: 识别相关和易混淆的概念

分析维度：
- 核心特征是否正确
- 定义是否过于宽泛或狭窄
- 是否包含了关键要素
- 是否存在逻辑错误

请提供建设性的纠正建议。"""),
            
            ("human", """请验证以下概念的定义准确性：

**主题**: {topic}

**概念及其解释**:
{concepts_explanation}

**特别关注的概念**: {key_concepts}

请为每个概念提供详细的验证分析。""")
        ])
        
        # 误解识别提示词
        self.misconception_detection_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个教育心理学专家，专门识别学习中的常见误解和认知偏误。

常见误解类型：
1. **概念混淆**: 将相似概念混为一谈
2. **因果倒置**: 颠倒原因和结果
3. **过度简化**: 忽略重要的复杂性
4. **类比错误**: 不当的类比推理
5. **先入为主**: 基于直觉的错误判断

识别策略：
- 寻找与标准定义的偏差
- 识别逻辑漏洞和推理错误
- 发现隐含的错误假设
- 注意表述中的绝对化倾向

请温和地指出问题，并提供正确的理解。"""),
            
            ("human", """请识别以下解释中可能存在的误解：

**主题**: {topic}

**用户解释**:
{explanation}

**背景信息**: 这是一个学习者对{topic}的理解，请帮助识别潜在的误解。

请提供具体的误解分析和纠正建议。""")
        ])
    
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理验证任务"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.KNOWLEDGE_VALIDATION:
                result = await self._validate_knowledge(task.input_data, context)
            elif task.task_type == "factual_verification":
                result = await self._verify_facts(task.input_data, context)
            elif task.task_type == "concept_validation":
                result = await self._validate_concepts(task.input_data, context)
            elif task.task_type == "misconception_detection":
                result = await self._detect_misconceptions(task.input_data, context)
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
    
    async def _validate_knowledge(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """综合知识验证"""
        topic = context.topic
        explanation = context.user_explanation
        
        # 并行执行多种验证
        factual_result = await self._verify_facts({"explanation": explanation}, context)
        concept_result = await self._validate_concepts({"explanation": explanation}, context)
        misconception_result = await self._detect_misconceptions({"explanation": explanation}, context)
        
        # 综合评分
        overall_accuracy = (
            factual_result.get("average_confidence", 0.5) * 0.4 +
            concept_result.get("average_accuracy", 0.5) * 0.4 +
            (1.0 - len(misconception_result.get("misconceptions", [])) * 0.1) * 0.2
        )
        
        # 生成报告
        report = KnowledgeValidationReport(
            overall_accuracy=max(0.0, min(1.0, overall_accuracy)),
            concept_validations=concept_result.get("validations", []),
            factual_validations=factual_result.get("validations", []),
            critical_issues=self._identify_critical_issues(factual_result, concept_result, misconception_result),
            improvement_suggestions=self._generate_improvement_suggestions(factual_result, concept_result, misconception_result),
            reliability_score=overall_accuracy
        )
        
        return {
            "validation_report": report.dict(),
            "summary": f"知识验证完成，整体准确性: {overall_accuracy:.2f}",
            "requires_attention": overall_accuracy < 0.7
        }
    
    async def _verify_facts(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """验证事实声明"""
        explanation = input_data.get("explanation", context.user_explanation)
        topic = context.topic
        
        # 构造验证提示
        messages = self.factual_validation_prompt.format_messages(
            topic=topic,
            explanation=explanation,
            focus_areas="具体的数据、时间、人物、事件、因果关系"
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # 解析LLM响应
            result_data = json.loads(response.content)
            
            # 标准化结果格式
            validations = []
            for item in result_data.get("factual_claims", []):
                validation = FactualValidation(
                    claim=item.get("claim", ""),
                    is_factual=item.get("is_factual", True),
                    evidence_strength=item.get("confidence", 0.5),
                    sources=item.get("sources", []),
                    alternative_views=item.get("alternative_views", [])
                )
                validations.append(validation.dict())
            
            return {
                "validations": validations,
                "average_confidence": sum(v["evidence_strength"] for v in validations) / max(len(validations), 1),
                "total_claims": len(validations),
                "verified_claims": sum(1 for v in validations if v["is_factual"])
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            # 降级处理
            return {
                "validations": [],
                "average_confidence": 0.5,
                "total_claims": 0,
                "verified_claims": 0,
                "error": f"解析失败: {str(e)}"
            }
    
    async def _validate_concepts(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """验证概念定义"""
        explanation = input_data.get("explanation", context.user_explanation)
        topic = context.topic
        
        # 提取关键概念
        key_concepts = self._extract_key_concepts(explanation, topic)
        
        messages = self.concept_validation_prompt.format_messages(
            topic=topic,
            concepts_explanation=explanation,
            key_concepts=", ".join(key_concepts)
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            validations = []
            for item in result_data.get("concept_validations", []):
                validation = ConceptValidation(
                    concept=item.get("concept", ""),
                    definition_accuracy=item.get("accuracy_score", 0.5),
                    common_misconceptions=item.get("misconceptions", []),
                    correct_definition=item.get("correct_definition"),
                    related_concepts=item.get("related_concepts", [])
                )
                validations.append(validation.dict())
            
            return {
                "validations": validations,
                "average_accuracy": sum(v["definition_accuracy"] for v in validations) / max(len(validations), 1),
                "total_concepts": len(validations),
                "accurate_concepts": sum(1 for v in validations if v["definition_accuracy"] > 0.7)
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "validations": [],
                "average_accuracy": 0.5,
                "total_concepts": 0,
                "accurate_concepts": 0,
                "error": f"解析失败: {str(e)}"
            }
    
    async def _detect_misconceptions(self, input_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """检测常见误解"""
        explanation = input_data.get("explanation", context.user_explanation)
        topic = context.topic
        
        messages = self.misconception_detection_prompt.format_messages(
            topic=topic,
            explanation=explanation
        )
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result_data = json.loads(response.content)
            
            misconceptions = result_data.get("misconceptions", [])
            corrections = result_data.get("corrections", [])
            
            return {
                "misconceptions": misconceptions,
                "corrections": corrections,
                "misconception_count": len(misconceptions),
                "severity_scores": result_data.get("severity_scores", [])
            }
            
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "misconceptions": [],
                "corrections": [],
                "misconception_count": 0,
                "error": f"解析失败: {str(e)}"
            }
    
    def _extract_key_concepts(self, explanation: str, topic: str) -> List[str]:
        """提取关键概念（简化版本）"""
        import re
        
        # 简单的关键词提取
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', explanation)
        
        # 过滤长度和去重
        concepts = list(set([w for w in words if len(w) >= 2]))
        
        # 添加主题作为关键概念
        if topic not in concepts:
            concepts.append(topic)
        
        return concepts[:10]  # 限制数量
    
    def _identify_critical_issues(self, factual_result: Dict, concept_result: Dict, misconception_result: Dict) -> List[str]:
        """识别关键问题"""
        issues = []
        
        # 检查事实准确性问题
        if factual_result.get("average_confidence", 1.0) < 0.6:
            issues.append("存在事实准确性问题，需要验证相关声明")
        
        # 检查概念定义问题
        if concept_result.get("average_accuracy", 1.0) < 0.6:
            issues.append("概念定义不够准确，需要澄清核心概念")
        
        # 检查误解问题
        if misconception_result.get("misconception_count", 0) > 2:
            issues.append("存在多个认知误解，需要纠正错误理解")
        
        return issues
    
    def _generate_improvement_suggestions(self, factual_result: Dict, concept_result: Dict, misconception_result: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if factual_result.get("verified_claims", 0) < factual_result.get("total_claims", 1):
            suggestions.append("建议查证相关事实，确保信息准确性")
        
        if concept_result.get("accurate_concepts", 0) < concept_result.get("total_concepts", 1):
            suggestions.append("建议重新学习核心概念的标准定义")
        
        if misconception_result.get("misconception_count", 0) > 0:
            suggestions.append("建议关注常见误解，避免错误理解")
        
        suggestions.append("建议多查阅权威资料，加深理解深度")
        
        return suggestions
    
    async def handle_message(self, message) -> Optional:
        """处理消息（暂时简化实现）"""
        # 这里可以实现更复杂的消息处理逻辑
        return None
