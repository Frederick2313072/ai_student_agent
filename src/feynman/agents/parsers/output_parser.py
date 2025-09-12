"""
多Agent系统输出解析器

为新的多Agent架构提供专业化的输出解析功能，支持不同Agent类型的结构化输出解析。
"""

import json
import re
from typing import List, Dict, Any, Optional, Union, Type
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class ConfidenceLevel(str, Enum):
    """疑点置信度等级"""
    HIGH = "high"      # 明确的逻辑问题或事实错误
    MEDIUM = "medium"  # 需要进一步澄清的概念
    LOW = "low"        # 可以深入探讨的话题


class UnclearPoint(BaseModel):
    """疑点数据结构"""
    content: str = Field(..., description="疑点描述")
    category: str = Field(default="unknown", description="疑点类别: concept/logic/mechanism/application/boundary")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="置信度")
    reasoning: Optional[str] = Field(default=None, description="识别此疑点的原因")
    educational_value: Optional[str] = Field(default=None, description="教育价值说明")
    suggested_approach: Optional[str] = Field(default=None, description="建议的澄清方式")
    priority: int = Field(default=2, description="优先级 1-5，1最高")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('疑点内容不能为空')
        return v.strip()
    
    @validator('priority')
    def priority_in_range(cls, v):
        if not 1 <= v <= 5:
            return 2  # 默认中等优先级
        return v


class AnalysisResult(BaseModel):
    """分析结果完整结构"""
    unclear_points: List[UnclearPoint] = Field(default_factory=list, description="识别出的疑点列表")
    is_complete: bool = Field(default=False, description="解释是否完整无疑点")
    summary: Optional[str] = Field(default=None, description="分析总结")
    
    # 新增字段
    understanding_quality: Optional[str] = Field(default=None, description="理解质量评估")
    key_concepts: List[str] = Field(default_factory=list, description="识别出的关键概念")
    knowledge_depth: Optional[str] = Field(default=None, description="知识深度评估")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")
    
    @validator('unclear_points')
    def validate_points(cls, v):
        # 去重并按优先级排序
        seen = set()
        unique_points = []
        for point in v:
            if point.content not in seen:
                seen.add(point.content)
                unique_points.append(point)
        
        # 按优先级排序（1最高，5最低）
        unique_points.sort(key=lambda x: x.priority)
        return unique_points


# Agent类型枚举
class AgentType(str, Enum):
    """Agent类型"""
    EXPLANATION_ANALYZER = "explanation_analyzer"
    KNOWLEDGE_VALIDATOR = "knowledge_validator"
    QUESTION_STRATEGIST = "question_strategist"
    CONVERSATION_ORCHESTRATOR = "conversation_orchestrator"
    INSIGHT_SYNTHESIZER = "insight_synthesizer"
    COORDINATOR = "coordinator"


# 知识验证相关数据模型
class ValidationIssue(BaseModel):
    """验证问题"""
    content: str = Field(..., description="问题内容")
    severity: str = Field(..., description="严重程度: critical/warning/info")
    source: Optional[str] = Field(None, description="问题来源")
    suggestion: Optional[str] = Field(None, description="修正建议")


class ValidationResult(BaseModel):
    """知识验证结果"""
    overall_accuracy: float = Field(..., description="整体准确性评分 0-1")
    factual_errors: List[ValidationIssue] = Field(default_factory=list, description="事实错误")
    conceptual_issues: List[ValidationIssue] = Field(default_factory=list, description="概念问题")
    critical_issues: List[ValidationIssue] = Field(default_factory=list, description="严重问题")
    validation_summary: Optional[str] = Field(None, description="验证总结")


# 问题生成相关数据模型
class Question(BaseModel):
    """问题数据结构"""
    content: str = Field(..., description="问题内容")
    category: str = Field(..., description="问题类别")
    difficulty: str = Field(..., description="难度等级: easy/medium/hard")
    educational_goal: str = Field(..., description="教育目标")
    estimated_time: int = Field(default=60, description="预估回答时间(秒)")
    follow_up_questions: List[str] = Field(default_factory=list, description="后续问题")


class QuestionSet(BaseModel):
    """问题集合"""
    primary_questions: List[Question] = Field(default_factory=list, description="主要问题")
    follow_up_questions: List[Question] = Field(default_factory=list, description="跟进问题")
    clarification_questions: List[Question] = Field(default_factory=list, description="澄清问题")
    total_estimated_time: int = Field(default=0, description="总预估时间")
    difficulty_distribution: Dict[str, int] = Field(default_factory=dict, description="难度分布")


# 对话编排相关数据模型
class OrchestrationDecision(BaseModel):
    """编排决策"""
    recommended_action: str = Field(..., description="推荐行动")
    reasoning: str = Field(..., description="决策理由")
    next_phase: Optional[str] = Field(None, description="下一阶段")
    learning_pace: str = Field(default="normal", description="学习节奏")
    engagement_level: float = Field(default=0.5, description="参与度评估")


# 洞察综合相关数据模型
class LearningInsight(BaseModel):
    """学习洞察"""
    content: str = Field(..., description="洞察内容")
    category: str = Field(..., description="洞察类别")
    importance: float = Field(..., description="重要性评分")
    actionable_suggestion: Optional[str] = Field(None, description="可行建议")


class LearningReport(BaseModel):
    """学习报告"""
    overall_understanding: float = Field(..., description="整体理解水平")
    learning_progress: float = Field(..., description="学习进度")
    strengths: List[str] = Field(default_factory=list, description="优势")
    areas_for_improvement: List[str] = Field(default_factory=list, description="改进领域")
    recommended_next_steps: List[str] = Field(default_factory=list, description="建议下一步")
    insights: List[LearningInsight] = Field(default_factory=list, description="学习洞察")


class MultiAgentOutputParser:
    """多Agent系统输出解析器"""
    
    @staticmethod
    def parse_agent_output(raw_output: str, agent_type: AgentType) -> Dict[str, Any]:
        """
        根据Agent类型解析输出
        
        Args:
            raw_output: Agent的原始输出
            agent_type: Agent类型
            
        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        if not raw_output or not raw_output.strip():
            return {"error": "输出为空", "success": False}
        
        try:
            # 根据Agent类型选择解析策略
            if agent_type == AgentType.EXPLANATION_ANALYZER:
                return MultiAgentOutputParser._parse_analysis_output(raw_output)
            elif agent_type == AgentType.KNOWLEDGE_VALIDATOR:
                return MultiAgentOutputParser._parse_validation_output(raw_output)
            elif agent_type == AgentType.QUESTION_STRATEGIST:
                return MultiAgentOutputParser._parse_question_output(raw_output)
            elif agent_type == AgentType.CONVERSATION_ORCHESTRATOR:
                return MultiAgentOutputParser._parse_orchestration_output(raw_output)
            elif agent_type == AgentType.INSIGHT_SYNTHESIZER:
                return MultiAgentOutputParser._parse_insight_output(raw_output)
            elif agent_type == AgentType.COORDINATOR:
                return MultiAgentOutputParser._parse_coordination_output(raw_output)
            else:
                return MultiAgentOutputParser._fallback_parse(raw_output)
                
        except Exception as e:
            return {
                "error": f"解析失败: {str(e)}",
                "success": False,
                "raw_output": raw_output[:200] + "..." if len(raw_output) > 200 else raw_output
            }
    
    @staticmethod
    def _parse_analysis_output(raw_output: str) -> Dict[str, Any]:
        """解析解释分析Agent的输出"""
        try:
            # 尝试JSON解析
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                result = AnalysisResult(**json_data)
                return {
                    "success": True,
                    "analysis_result": result.dict(),
                    "unclear_points": [point.content for point in result.unclear_points],
                    "is_complete": result.is_complete,
                    "summary": result.summary
                }
            
            # 降级到模式匹配
            return MultiAgentOutputParser._pattern_parse_analysis(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _parse_validation_output(raw_output: str) -> Dict[str, Any]:
        """解析知识验证Agent的输出"""
        try:
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                result = ValidationResult(**json_data)
                return {
                    "success": True,
                    "validation_report": result.dict(),
                    "overall_accuracy": result.overall_accuracy,
                    "critical_issues": [issue.content for issue in result.critical_issues]
                }
            
            return MultiAgentOutputParser._pattern_parse_validation(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _parse_question_output(raw_output: str) -> Dict[str, Any]:
        """解析问题策略Agent的输出"""
        try:
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                result = QuestionSet(**json_data)
                return {
                    "success": True,
                    "question_set": result.dict(),
                    "primary_questions": [q.content for q in result.primary_questions],
                    "total_estimated_time": result.total_estimated_time
                }
            
            return MultiAgentOutputParser._pattern_parse_questions(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _parse_orchestration_output(raw_output: str) -> Dict[str, Any]:
        """解析对话编排Agent的输出"""
        try:
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                result = OrchestrationDecision(**json_data)
                return {
                    "success": True,
                    "orchestration_decision": result.dict(),
                    "recommended_action": result.recommended_action,
                    "next_phase": result.next_phase
                }
            
            return MultiAgentOutputParser._pattern_parse_orchestration(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _parse_insight_output(raw_output: str) -> Dict[str, Any]:
        """解析洞察综合Agent的输出"""
        try:
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                if "learning_report" in json_data:
                    result = LearningReport(**json_data["learning_report"])
                    return {
                        "success": True,
                        "learning_report": result.dict(),
                        "overall_understanding": result.overall_understanding,
                        "insights": [insight.content for insight in result.insights]
                    }
                elif "insights" in json_data:
                    insights = [LearningInsight(**insight) if isinstance(insight, dict) else 
                              LearningInsight(content=str(insight), category="general", importance=0.5)
                              for insight in json_data["insights"]]
                    return {
                        "success": True,
                        "insights": [insight.dict() for insight in insights],
                        "insight_contents": [insight.content for insight in insights]
                    }
            
            return MultiAgentOutputParser._pattern_parse_insights(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _parse_coordination_output(raw_output: str) -> Dict[str, Any]:
        """解析协调者Agent的输出"""
        try:
            json_data = MultiAgentOutputParser._extract_json(raw_output)
            if json_data:
                return {
                    "success": True,
                    "coordination_decision": json_data,
                    "strategy": json_data.get("strategy", "sequential"),
                    "next_phase": json_data.get("next_phase", "analysis")
                }
            
            return MultiAgentOutputParser._pattern_parse_coordination(raw_output)
            
        except Exception as e:
            return MultiAgentOutputParser._fallback_parse(raw_output)
    
    # 辅助方法
    @staticmethod
    def _extract_json(output: str) -> Optional[Dict[str, Any]]:
        """从输出中提取JSON数据"""
        try:
            # 尝试直接解析整个输出
            return json.loads(output.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'\{.*?\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, output, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    # 模式匹配解析方法
    @staticmethod
    def _pattern_parse_analysis(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析分析结果"""
        unclear_points = []
        
        # 查找疑点列表
        patterns = [
            r'疑点[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'不清楚的地方[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'(\d+[\.\)]\s*[^0-9\n]+)',
            r'([•\-\*]\s*[^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, raw_output, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                
                cleaned = re.sub(r'^\d+[\.\)]\s*|^[•\-\*]\s*', '', match.strip())
                if cleaned and len(cleaned) > 10:
                    unclear_points.append(cleaned)
        
        if unclear_points:
            return {
                "success": True,
                "unclear_points": unclear_points,
                "is_complete": False,
                "summary": f"通过模式匹配识别出{len(unclear_points)}个疑点"
            }
        
        # 检查是否表示完整理解
        complete_indicators = ["完全理解", "没有疑点", "非常清楚", "解释完整"]
        for indicator in complete_indicators:
            if indicator in raw_output:
                return {
                    "success": True,
                    "unclear_points": [],
                    "is_complete": True,
                    "summary": f"表示{indicator}"
                }
        
        return MultiAgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _pattern_parse_validation(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析验证结果"""
        # 简化的验证结果解析
        accuracy_match = re.search(r'准确性[:：]\s*(\d+(?:\.\d+)?)', raw_output)
        accuracy = float(accuracy_match.group(1)) if accuracy_match else 0.8
        
        return {
            "success": True,
            "validation_report": {
                "overall_accuracy": accuracy,
                "validation_summary": raw_output[:200] + "..." if len(raw_output) > 200 else raw_output
            },
            "overall_accuracy": accuracy
        }
    
    @staticmethod
    def _pattern_parse_questions(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析问题"""
        questions = []
        
        # 查找问题列表
        question_patterns = [
            r'问题[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'(\d+[\.\)]\s*[^0-9\n]+\？)',
            r'([•\-\*]\s*[^\n]+\？)',
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, raw_output, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                
                cleaned = re.sub(r'^\d+[\.\)]\s*|^[•\-\*]\s*', '', match.strip())
                if cleaned and '？' in cleaned:
                    questions.append(cleaned)
        
        return {
            "success": True,
            "primary_questions": questions,
            "question_set": {"primary_questions": questions},
            "total_estimated_time": len(questions) * 60
        }
    
    @staticmethod
    def _pattern_parse_orchestration(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析编排决策"""
        return {
            "success": True,
            "orchestration_decision": {
                "recommended_action": "continue_learning",
                "reasoning": raw_output[:200] + "..." if len(raw_output) > 200 else raw_output
            },
            "recommended_action": "continue_learning"
        }
    
    @staticmethod
    def _pattern_parse_insights(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析洞察"""
        insights = []
        
        # 查找洞察列表
        insight_patterns = [
            r'洞察[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'关键发现[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'(\d+[\.\)]\s*[^0-9\n]+)',
            r'([•\-\*]\s*[^\n]+)',
        ]
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, raw_output, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                
                cleaned = re.sub(r'^\d+[\.\)]\s*|^[•\-\*]\s*', '', match.strip())
                if cleaned and len(cleaned) > 10:
                    insights.append(cleaned)
        
        return {
            "success": True,
            "insights": insights,
            "insight_contents": insights
        }
    
    @staticmethod
    def _pattern_parse_coordination(raw_output: str) -> Dict[str, Any]:
        """模式匹配解析协调决策"""
        return {
            "success": True,
            "coordination_decision": {
                "strategy": "sequential",
                "next_phase": "explanation_analysis"
            },
            "strategy": "sequential",
            "next_phase": "explanation_analysis"
        }
    
    @staticmethod
    def _fallback_parse(raw_output: str) -> Dict[str, Any]:
        """降级解析策略"""
        content = raw_output.strip()[:200]
        if len(raw_output) > 200:
            content += "..."
        
        return {
            "success": False,
            "error": "使用降级解析策略",
            "raw_content": content,
            "timestamp": datetime.now().isoformat()
        }


# 便捷函数和兼容性支持
def parse_agent_output(raw_output: str, agent_type: str = "explanation_analyzer") -> Dict[str, Any]:
    """
    便捷的解析函数，兼容旧接口
    
    Args:
        raw_output: 原始输出
        agent_type: Agent类型字符串
        
    Returns:
        解析结果
    """
    try:
        agent_enum = AgentType(agent_type)
        return MultiAgentOutputParser.parse_agent_output(raw_output, agent_enum)
    except ValueError:
        # 未知Agent类型，使用降级解析
        return MultiAgentOutputParser._fallback_parse(raw_output)


def validate_unclear_points(points: List[str]) -> List[UnclearPoint]:
    """验证和标准化疑点列表（保持向后兼容）"""
    validated = []
    for point in points:
        if isinstance(point, str) and point.strip():
            validated.append(UnclearPoint(content=point.strip()))
        elif isinstance(point, dict):
            try:
                validated.append(UnclearPoint(**point))
            except Exception:
                # 字典格式不符合，尝试提取content
                content = point.get('content') or str(point)
                if content:
                    validated.append(UnclearPoint(content=str(content)))
    
    return validated


# 向后兼容性：保持旧的解析器类名
class AgentOutputParser:
    """旧版解析器的兼容性包装"""
    
    @staticmethod
    def parse_agent_output(raw_output: str) -> AnalysisResult:
        """兼容旧版解析方法"""
        result = MultiAgentOutputParser.parse_agent_output(raw_output, AgentType.EXPLANATION_ANALYZER)
        
        if result.get("success", False):
            # 转换为旧格式的AnalysisResult
            unclear_points = []
            for point_content in result.get("unclear_points", []):
                unclear_points.append(UnclearPoint(content=point_content))
            
            return AnalysisResult(
                unclear_points=unclear_points,
                is_complete=result.get("is_complete", False),
                summary=result.get("summary", "")
            )
        else:
            # 降级处理
            return AnalysisResult(
                unclear_points=[UnclearPoint(
                    content=result.get("raw_content", raw_output[:200]),
                    confidence=ConfidenceLevel.LOW,
                    reasoning="兼容性解析失败"
                )],
                is_complete=False,
                summary=result.get("error", "解析失败")
            )


# 导出主要类和函数
__all__ = [
    # 数据模型
    "ConfidenceLevel",
    "UnclearPoint", 
    "AnalysisResult",
    "ValidationIssue",
    "ValidationResult",
    "Question",
    "QuestionSet",
    "OrchestrationDecision",
    "LearningInsight",
    "LearningReport",
    "AgentType",
    
    # 解析器
    "MultiAgentOutputParser",
    "AgentOutputParser",  # 向后兼容
    
    # 便捷函数
    "parse_agent_output",
    "validate_unclear_points"
]

