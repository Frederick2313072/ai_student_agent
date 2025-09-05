"""
测试 Agent 输出解析器的稳定性和准确性
"""

import pytest
from agent.output_parser import AgentOutputParser, AnalysisResult, UnclearPoint, ConfidenceLevel


class TestAgentOutputParser:
    """Agent输出解析器测试"""
    
    def test_strict_json_parse_success(self):
        """测试严格JSON解析 - 成功案例"""
        output = '''
        我分析了用户的解释，发现以下疑点：
        ["GIL的具体实现机制", "性能影响的量化数据", "替代方案的对比"]
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 3
        assert result.unclear_points[0].content == "GIL的具体实现机制"
        assert not result.is_complete
    
    def test_strict_json_parse_empty_list(self):
        """测试严格JSON解析 - 空列表（完整解释）"""
        output = '''
        经过分析，用户的解释非常完整：
        []
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 0
        assert result.is_complete
    
    def test_structured_json_parse(self):
        """测试结构化JSON解析"""
        output = '''
        Action:
        ```json
        {
          "action": "Final Answer",
          "action_input": {
            "unclear_points": [
              {
                "content": "GIL的具体工作机制",
                "category": "mechanism",
                "confidence": "high",
                "reasoning": "用户只提到了GIL的作用但没有说明实现原理"
              }
            ],
            "is_complete": false,
            "summary": "需要进一步解释实现机制"
          }
        }
        ```
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 1
        assert result.unclear_points[0].category == "mechanism"
        assert result.unclear_points[0].confidence == ConfidenceLevel.HIGH
        assert not result.is_complete
    
    def test_pattern_parse_numbered_list(self):
        """测试模式匹配 - 编号列表"""
        output = '''
        根据分析，我发现以下疑点：
        1. GIL的具体实现机制不清楚
        2. 多线程性能影响的具体数据缺失
        3. 与其他语言的对比说明不足
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) >= 2  # 至少识别出部分疑点
    
    def test_pattern_parse_bullet_list(self):
        """测试模式匹配 - 项目符号列表"""
        output = '''
        疑点分析：
        • GIL对不同类型任务的影响差异
        • Python版本间GIL实现的演变
        • 未来GIL优化的具体路线图
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) >= 1
    
    def test_keyword_extract_complete(self):
        """测试关键词提取 - 完整理解"""
        output = '''
        经过深入分析，我认为用户对GIL的解释完全理解，
        概念清晰，逻辑完整，没有疑点需要进一步澄清。
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert result.is_complete
        assert len(result.unclear_points) == 0
    
    def test_keyword_extract_unclear(self):
        """测试关键词提取 - 发现疑点"""
        output = '''
        用户的解释中有几个地方我不理解：
        首先，什么是GIL的具体实现？
        其次，为什么多线程会变慢？
        最后，如何选择合适的并发方案？
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) >= 1
        assert any("实现" in point.content for point in result.unclear_points)
    
    def test_smart_split_questions(self):
        """测试智能分割 - 疑问句识别"""
        output = '''
        用户提到了GIL，但是具体的工作原理是什么？
        多线程为什么会受到影响？性能损失有多大？
        有没有其他替代方案可以考虑？
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) >= 1
    
    def test_fallback_parse(self):
        """测试降级解析"""
        output = "这是一段无法解析的文本内容..."
        
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 1
        assert result.unclear_points[0].confidence == ConfidenceLevel.LOW
        assert "降级" in result.summary
    
    def test_empty_output(self):
        """测试空输出"""
        result = AgentOutputParser.parse_agent_output("")
        assert result.is_complete
        assert len(result.unclear_points) == 0
        assert "空" in result.summary
    
    def test_very_long_output(self):
        """测试超长输出"""
        long_output = "这是一段很长的文本 " * 100
        
        result = AgentOutputParser.parse_agent_output(long_output)
        assert len(result.unclear_points) >= 1
        # 验证内容被截断
        assert len(result.unclear_points[0].content) <= 203  # 200 + "..."
    
    def test_mixed_format_resilience(self):
        """测试混合格式的容错性"""
        output = '''
        我的分析结果：
        疑点1: GIL机制不清楚
        2. 性能数据缺失
        • 替代方案对比不足
        
        JSON格式：["额外疑点"]
        
        问题：什么是具体实现？
        '''
        
        result = AgentOutputParser.parse_agent_output(output)
        # 应该能从混合格式中提取出疑点
        assert len(result.unclear_points) >= 1


if __name__ == "__main__":
    # 运行一些基本测试
    parser = TestAgentOutputParser()
    
    print("测试严格JSON解析...")
    parser.test_strict_json_parse_success()
    print("✓ 通过")
    
    print("测试模式匹配...")
    parser.test_pattern_parse_numbered_list()
    print("✓ 通过")
    
    print("测试关键词提取...")
    parser.test_keyword_extract_complete()
    print("✓ 通过")
    
    print("测试降级处理...")
    parser.test_fallback_parse()
    print("✓ 通过")
    
    print("\n所有基本测试通过！✅")
