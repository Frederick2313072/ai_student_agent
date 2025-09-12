"""
疑点理解Agent - 智能分析用户解释中的知识缺口

这个Agent专门负责理解和分析用户的解释，识别真正需要澄清的知识点。
不同于简单的文本解析，这里使用专门的LLM来进行语义理解。
"""

import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from pydantic import BaseModel, Field

from feynman.agents.parsers.output_parser import AnalysisResult, UnclearPoint, ConfidenceLevel
from feynman.core.config.settings import get_settings
from .agent_protocol import (
    AgentInterface, AgentType, AgentMetadata, AgentCapability,
    AgentTask, AgentResponse, ConversationContext, AgentMessage,
    create_response
)
from typing import Optional


# =============================================================================
# 内嵌提示词模板
# =============================================================================

EXPLANATION_ANALYZER_SYSTEM_PROMPT = """你是费曼学习系统的解释分析专家Agent，负责深度理解和分析用户的知识解释。

## 🎯 核心职责

1. **深度理解分析**
   - 全面理解用户解释的内容和结构
   - 识别解释中的关键概念和逻辑关系
   - 评估解释的完整性和准确性

2. **疑点智能识别**
   - 发现逻辑跳跃和推理缺口
   - 识别概念模糊和定义不清
   - 标记需要进一步澄清的知识点

3. **知识结构分析**
   - 分析知识的层次结构和组织方式
   - 评估概念之间的关联和依赖关系
   - 识别知识体系的完整性和一致性

## 🔍 分析维度

### 1. 概念准确性 (Concept Accuracy)
- 专业术语使用是否正确
- 概念定义是否准确完整
- 概念边界是否清晰

### 2. 逻辑连贯性 (Logical Coherence)
- 推理过程是否合理
- 论证是否充分
- 因果关系是否成立

### 3. 结构完整性 (Structural Completeness)
- 解释是否涵盖关键要素
- 知识点是否有遗漏
- 层次结构是否清晰

### 4. 应用机制 (Application Mechanism)
- 原理如何在实际中运作
- 适用条件和范围
- 例外情况和限制

### 5. 边界条件 (Boundary Conditions)
- 理论或概念的适用边界
- 与相关概念的区别
- 特殊情况的处理

## 📊 疑点分类体系

- **Concept**: 概念定义、术语理解相关疑点
- **Logic**: 逻辑推理、因果关系相关疑点  
- **Mechanism**: 工作原理、运作机制相关疑点
- **Application**: 实际应用、场景运用相关疑点
- **Boundary**: 适用范围、边界条件相关疑点

## 🎯 置信度评估

- **High**: 明确的逻辑问题或事实错误
- **Medium**: 需要进一步澄清的概念
- **Low**: 可以深入探讨的话题

## 📤 输出格式

请以JSON格式输出分析结果：

```json
{
    "unclear_points": [
        {
            "content": "具体的疑点描述",
            "category": "concept|logic|mechanism|application|boundary",
            "confidence": "high|medium|low",
            "reasoning": "识别此疑点的详细原因",
            "educational_value": "澄清此疑点的教育价值",
            "suggested_approach": "建议的澄清方式",
            "priority": 2
        }
    ],
    "is_complete": false,
    "summary": "整体分析总结",
    "understanding_quality": "excellent|good|fair|poor",
    "key_concepts": [
        "识别出的关键概念1",
        "关键概念2"
    ],
    "knowledge_depth": "surface|intermediate|deep|expert",
    "improvement_suggestions": [
        "改进建议1",
        "改进建议2"
    ],
    "analysis_metadata": {
        "complexity_level": "low|medium|high|very_high",
        "analysis_confidence": 0.85,
        "processing_notes": "分析过程中的重要观察"
    }
}
```

请以费曼学习法的角度，深入分析用户解释，识别所有需要澄清的疑点。"""


EXPLANATION_UNDERSTANDING_TEMPLATE = """请深度分析以下用户解释：

## 📚 学习主题
{topic}

## 📝 用户解释内容
{user_explanation}

## 🎯 分析要求
- 分析深度: {analysis_depth}
- 关注重点: {focus_areas}
- 质量标准: {quality_standards}

## 📊 背景信息
- 预期知识水平: {expected_knowledge_level}
- 学习目标: {learning_objectives}
- 时间约束: {time_constraints}

请对用户的解释进行全面分析，识别所有需要进一步澄清的疑点，并评估解释的质量和完整性。"""


DOUBT_IDENTIFICATION_TEMPLATE = """主题: {topic}

用户解释:
{explanation}

分析洞察:
- 关键概念: {key_concepts}
- 逻辑流程: {logical_flow} 
- 知识深度: {knowledge_depth}
- 潜在缺口: {potential_gaps}
- 教学质量: {teaching_quality}

请基于这些洞察，识别出需要澄清的具体疑点。"""


class ExplanationInsight(BaseModel):
    """解释洞察 - Agent对用户解释的深度理解"""
    
    key_concepts: List[str] = Field(default_factory=list, description="解释中的关键概念")
    logical_flow: str = Field(default="", description="逻辑流程分析")
    knowledge_depth: str = Field(default="surface", description="知识深度评估: surface/intermediate/deep")
    potential_gaps: List[str] = Field(default_factory=list, description="潜在知识缺口")
    teaching_quality: str = Field(default="", description="教学质量评估")


class ExplanationAnalyzer(AgentInterface):
    """疑点理解Agent - 智能分析用户解释"""
    
    def __init__(self):
        """初始化分析器"""
        
        # 定义Agent能力
        capabilities = [
            AgentCapability(
                name="explanation_analysis",
                description="分析用户解释，识别知识缺口",
                input_types=["text", "explanation", "topic"],
                output_types=["analysis_result", "unclear_points"],
                complexity_level="complex"
            ),
            AgentCapability(
                name="concept_understanding",
                description="深度理解概念和逻辑关系",
                input_types=["explanation", "concept"],
                output_types=["concept_analysis", "insight"],
                complexity_level="medium"
            ),
            AgentCapability(
                name="doubt_identification",
                description="识别需要澄清的疑点",
                input_types=["explanation", "insight"],
                output_types=["doubt_list", "unclear_points"],
                complexity_level="complex"
            )
        ]
        
        # 初始化元数据
        metadata = AgentMetadata(
            agent_type=AgentType.EXPLANATION_ANALYZER,
            name="ExplanationAnalyzer",
            version="1.0.0",
            capabilities=capabilities,
            dependencies=[],  # 独立运行，不依赖其他Agent
            max_concurrent_tasks=2
        )
        
        super().__init__(metadata)
        
        settings = get_settings()
        
        # 优先使用OpenAI
        if settings.openai_api_key:
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.3  # 分析任务需要更稳定的输出
            )
        elif settings.llm_provider == "zhipu" and settings.zhipu_api_key:
            self.llm = ChatZhipuAI(
                api_key=settings.zhipu_api_key,
                model=settings.zhipu_model,
                temperature=0.3
            )
        else:
            raise ValueError("未配置可用的LLM模型")
    
    def analyze_explanation(self, topic: str, user_explanation: str, context: Optional[Dict] = None) -> AnalysisResult:
        """
        分析用户解释，识别需要澄清的疑点
        
        Args:
            topic: 学习主题
            user_explanation: 用户的解释内容
            context: 上下文信息（历史对话等）
            
        Returns:
            AnalysisResult: 结构化的分析结果
        """
        
        # 第一步：深度理解用户解释
        insight = self._understand_explanation(topic, user_explanation, context)
        
        # 第二步：基于理解识别疑点
        unclear_points = self._identify_unclear_points(topic, user_explanation, insight)
        
        # 第三步：评估完整性
        is_complete = len(unclear_points) == 0
        
        # 第四步：生成分析总结
        summary = self._generate_summary(insight, unclear_points, is_complete)
        
        return AnalysisResult(
            unclear_points=unclear_points,
            is_complete=is_complete,
            summary=summary
        )
    
    async def process_task(self, task: AgentTask, context: ConversationContext) -> AgentResponse:
        """处理分析任务"""
        try:
            # 提取任务数据
            topic = task.input_data.get("topic", "")
            explanation = task.input_data.get("explanation", "")
            
            # 执行分析
            analysis_result = self.analyze_explanation(topic, explanation, {
                "session_id": context.session_id,
                "conversation_history": context.conversation_history
            })
            
            # 构建响应
            result_data = {
                "unclear_points": [point.dict() for point in analysis_result.unclear_points],
                "is_complete": analysis_result.is_complete,
                "summary": analysis_result.summary
            }
            
            return create_response(
                agent_id=self.metadata.agent_id,
                agent_type=self.metadata.agent_type,
                task_id=task.task_id,
                success=True,
                result=result_data,
                processing_time=0.0  # 实际应该记录真实时间
            )
            
        except Exception as e:
            return create_response(
                agent_id=self.metadata.agent_id,
                agent_type=self.metadata.agent_type,
                task_id=task.task_id,
                success=False,
                error=str(e),
                processing_time=0.0
            )
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """处理消息"""
        # ExplanationAnalyzer通常不需要处理直接消息
        return None
    
    def _understand_explanation(self, topic: str, explanation: str, context: Optional[Dict] = None) -> ExplanationInsight:
        """深度理解用户解释"""
        
        understanding_prompt = ChatPromptTemplate.from_messages([
            ("system", EXPLANATION_ANALYZER_SYSTEM_PROMPT),
            ("human", EXPLANATION_UNDERSTANDING_TEMPLATE)
        ])
        
        context_info = ""
        if context:
            context_info = f"上下文信息: {json.dumps(context, ensure_ascii=False)}"
        
        messages = understanding_prompt.format_messages(
            topic=topic,
            explanation=explanation,
            context_info=context_info
        )
        
        response = self.llm.invoke(messages)
        
        try:
            # 尝试解析JSON响应
            insight_data = json.loads(response.content)
            return ExplanationInsight(**insight_data)
        except (json.JSONDecodeError, ValueError):
            # 如果JSON解析失败，创建基础洞察
            return ExplanationInsight(
                key_concepts=self._extract_keywords(explanation),
                logical_flow="解析失败，无法分析逻辑流程",
                knowledge_depth="unknown",
                potential_gaps=["需要进一步分析"],
                teaching_quality="无法评估"
            )
    
    def _identify_unclear_points(self, topic: str, explanation: str, insight: ExplanationInsight) -> List[UnclearPoint]:
        """基于理解洞察识别具体疑点"""
        
        identification_prompt = ChatPromptTemplate.from_messages([
            ("system", EXPLANATION_ANALYZER_SYSTEM_PROMPT),
            ("human", DOUBT_IDENTIFICATION_TEMPLATE)
        ])
        
        messages = identification_prompt.format_messages(
            topic=topic,
            explanation=explanation,
            key_concepts=", ".join(insight.key_concepts),
            logical_flow=insight.logical_flow,
            knowledge_depth=insight.knowledge_depth,
            potential_gaps=", ".join(insight.potential_gaps),
            teaching_quality=insight.teaching_quality
        )
        
        response = self.llm.invoke(messages)
        
        try:
            # 解析疑点列表
            unclear_data = json.loads(response.content)
            unclear_points = []
            
            if isinstance(unclear_data, list):
                for item in unclear_data:
                    if isinstance(item, dict):
                        unclear_points.append(UnclearPoint(**item))
                    elif isinstance(item, str):
                        unclear_points.append(UnclearPoint(content=item))
            elif isinstance(unclear_data, dict) and "unclear_points" in unclear_data:
                for item in unclear_data["unclear_points"]:
                    if isinstance(item, dict):
                        unclear_points.append(UnclearPoint(**item))
                    elif isinstance(item, str):
                        unclear_points.append(UnclearPoint(content=item))
            
            return unclear_points
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"疑点识别JSON解析失败: {e}")
            # 降级策略：从响应中提取关键信息
            return self._extract_unclear_points_from_text(response.content)
    
    def _generate_summary(self, insight: ExplanationInsight, unclear_points: List[UnclearPoint], is_complete: bool) -> str:
        """生成分析总结"""
        if is_complete:
            return f"解释完整清晰，涵盖了{len(insight.key_concepts)}个关键概念，逻辑流程清楚，无需进一步澄清。"
        
        summary_parts = []
        summary_parts.append(f"识别到{len(unclear_points)}个疑点")
        
        if insight.knowledge_depth:
            depth_desc = {
                "surface": "表面层次",
                "intermediate": "中等深度", 
                "deep": "深入层次"
            }
            summary_parts.append(f"知识深度为{depth_desc.get(insight.knowledge_depth, insight.knowledge_depth)}")
        
        # 按置信度分组
        high_confidence = [p for p in unclear_points if p.confidence == ConfidenceLevel.HIGH]
        medium_confidence = [p for p in unclear_points if p.confidence == ConfidenceLevel.MEDIUM]
        low_confidence = [p for p in unclear_points if p.confidence == ConfidenceLevel.LOW]
        
        if high_confidence:
            summary_parts.append(f"包含{len(high_confidence)}个高优先级疑点")
        if medium_confidence:
            summary_parts.append(f"{len(medium_confidence)}个中等优先级疑点")
        if low_confidence:
            summary_parts.append(f"{len(low_confidence)}个延伸探讨点")
        
        return "，".join(summary_parts) + "。"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """简单的关键词提取（降级方案）"""
        import re
        # 简单的中文关键词提取
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        # 过滤长度，去重，取前10个
        keywords = list(set([w for w in words if len(w) >= 2]))[:10]
        return keywords
    
    def _extract_unclear_points_from_text(self, text: str) -> List[UnclearPoint]:
        """从文本中提取疑点（降级方案）"""
        lines = text.split('\n')
        points = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['疑点', '不清楚', '需要', '什么是', '如何', '为什么']):
                if len(line) > 10:  # 过滤太短的行
                    points.append(UnclearPoint(
                        content=line,
                        confidence=ConfidenceLevel.MEDIUM,
                        reasoning="文本提取降级策略"
                    ))
        
        if not points:
            points.append(UnclearPoint(
                content="需要进一步澄清解释中的关键概念",
                confidence=ConfidenceLevel.LOW,
                reasoning="无法识别具体疑点，使用通用疑点"
            ))
        
        return points[:5]  # 最多返回5个疑点
