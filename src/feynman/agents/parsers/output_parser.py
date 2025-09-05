"""
Agent输出解析器 - 稳定结构化输出协议

提供多层解析策略，确保从Agent输出中稳定提取结构化数据。
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ConfidenceLevel(str, Enum):
    """疑点置信度等级"""
    HIGH = "high"      # 明确的逻辑问题或事实错误
    MEDIUM = "medium"  # 需要进一步澄清的概念
    LOW = "low"        # 可以深入探讨的话题


class UnclearPoint(BaseModel):
    """疑点数据结构"""
    content: str = Field(..., description="疑点描述")
    category: str = Field(default="unknown", description="疑点类别: logic/definition/fact/mechanism")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM, description="置信度")
    reasoning: Optional[str] = Field(default=None, description="识别此疑点的原因")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('疑点内容不能为空')
        return v.strip()


class AnalysisResult(BaseModel):
    """分析结果完整结构"""
    unclear_points: List[UnclearPoint] = Field(default_factory=list, description="识别出的疑点列表")
    is_complete: bool = Field(default=False, description="解释是否完整无疑点")
    summary: Optional[str] = Field(default=None, description="分析总结")
    
    @validator('unclear_points')
    def validate_points(cls, v):
        # 去重
        seen = set()
        unique_points = []
        for point in v:
            if point.content not in seen:
                seen.add(point.content)
                unique_points.append(point)
        return unique_points


class AgentOutputParser:
    """Agent输出解析器 - 多层解析策略"""
    
    @staticmethod
    def parse_agent_output(raw_output: str) -> AnalysisResult:
        """
        主解析方法 - 依次尝试多种解析策略
        
        Args:
            raw_output: Agent的原始输出
            
        Returns:
            AnalysisResult: 结构化分析结果
        """
        if not raw_output or not raw_output.strip():
            return AnalysisResult(is_complete=True, summary="输出为空")
            
        # 策略1: 严格JSON解析
        result = AgentOutputParser._try_strict_json_parse(raw_output)
        if result:
            return result
            
        # 策略2: 模式匹配解析
        result = AgentOutputParser._try_pattern_parse(raw_output)
        if result:
            return result
            
        # 策略3: 关键词提取
        result = AgentOutputParser._try_keyword_extract(raw_output)
        if result:
            return result
            
        # 策略4: 智能分割
        result = AgentOutputParser._try_smart_split(raw_output)
        if result:
            return result
            
        # 最后降级：整体作为单个疑点
        return AgentOutputParser._fallback_parse(raw_output)
    
    @staticmethod
    def _try_strict_json_parse(output: str) -> Optional[AnalysisResult]:
        """策略1: 严格JSON解析"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    if not data:  # 空列表表示无疑点
                        return AnalysisResult(is_complete=True, summary="AI认为解释完整")
                    
                    points = []
                    for item in data:
                        if isinstance(item, str):
                            points.append(UnclearPoint(content=item))
                        elif isinstance(item, dict):
                            points.append(UnclearPoint(**item))
                    
                    return AnalysisResult(unclear_points=points)
                    
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"JSON解析失败: {e}")
            
        return None
    
    @staticmethod
    def _try_pattern_parse(output: str) -> Optional[AnalysisResult]:
        """策略2: 模式匹配解析"""
        patterns = [
            # 匹配明确的疑点列表格式
            r'疑点[:：]\s*(.*?)(?=\n\n|\n---|$)',
            r'unclear_points[:：]\s*\[(.*?)\]',
            r'不清楚的地方[:：]\s*(.*?)(?=\n\n|\n---|$)',
            # 匹配编号列表
            r'(\d+[\.\)]\s*[^0-9\n]+(?:\n(?!\d+[\.\)]).*?)*)',
            # 匹配破折号列表
            r'([•\-\*]\s*[^\n]+(?:\n(?![•\-\*]).*?)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.DOTALL)
            if matches:
                points = []
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    
                    # 清理和分割
                    cleaned = re.sub(r'^\d+[\.\)]\s*|^[•\-\*]\s*', '', match.strip())
                    if cleaned and len(cleaned) > 10:  # 过滤太短的内容
                        points.append(UnclearPoint(content=cleaned))
                
                if points:
                    return AnalysisResult(unclear_points=points)
        
        return None
    
    @staticmethod
    def _try_keyword_extract(output: str) -> Optional[AnalysisResult]:
        """策略3: 关键词提取"""
        # 查找表示完整理解的关键词
        complete_indicators = [
            "完全理解", "没有疑点", "非常清楚", "解释完整", 
            "no unclear points", "completely clear"
        ]
        
        for indicator in complete_indicators:
            if indicator in output.lower():
                return AnalysisResult(is_complete=True, summary=f"AI表示{indicator}")
        
        # 查找疑点关键词
        unclear_keywords = [
            "不理解", "不清楚", "模糊", "疑问", "需要解释", 
            "什么是", "如何", "为什么", "unclear", "confusing"
        ]
        
        points = []
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in unclear_keywords) and len(line) > 15:
                # 清理格式字符
                cleaned = re.sub(r'^[•\-\*\d\.\)]+\s*', '', line)
                if cleaned:
                    points.append(UnclearPoint(content=cleaned, confidence=ConfidenceLevel.LOW))
        
        if points:
            return AnalysisResult(unclear_points=points)
            
        return None
    
    @staticmethod
    def _try_smart_split(output: str) -> Optional[AnalysisResult]:
        """策略4: 智能分割"""
        # 按句子分割，查找疑问句或包含关键词的句子
        sentences = re.split(r'[。！？.!?]\s*', output)
        points = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            # 疑问句或包含疑点关键词的句子
            if (sentence.endswith('？') or sentence.endswith('?') or 
                any(word in sentence for word in ['不理解', '不清楚', '疑问', '需要', '什么', '如何', '为什么']) and
                len(sentence) > 20):
                
                points.append(UnclearPoint(content=sentence, confidence=ConfidenceLevel.LOW))
        
        if points:
            return AnalysisResult(unclear_points=points)
            
        return None
    
    @staticmethod
    def _fallback_parse(output: str) -> AnalysisResult:
        """最后降级策略"""
        # 截取合理长度，避免过长输出
        content = output.strip()[:200]
        if len(output) > 200:
            content += "..."
            
        return AnalysisResult(
            unclear_points=[
                UnclearPoint(
                    content=content, 
                    confidence=ConfidenceLevel.LOW,
                    reasoning="解析失败，使用降级策略"
                )
            ],
            summary="使用降级解析策略"
        )


def validate_unclear_points(points: List[str]) -> List[UnclearPoint]:
    """验证和标准化疑点列表"""
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

