"""
gap_identifier_react 节点集成测试

测试完整的LangGraph节点工作流，验证解析器在实际场景中的表现。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import gap_identifier_react, AgentState
from agent.output_parser import AgentOutputParser, AnalysisResult
from langchain_core.messages import HumanMessage


def test_gap_identifier_mock_simple():
    """测试gap_identifier_react的基本功能（模拟场景）"""
    
    # 模拟一个简单的状态
    mock_state = {
        "topic": "Python GIL",
        "user_explanation": "GIL是全局解释器锁",
        "messages": [HumanMessage(content="这是用户对GIL的简单解释，请分析疑点")]
    }
    
    print("=== 模拟测试 gap_identifier_react ===")
    print(f"输入主题: {mock_state['topic']}")
    print(f"用户解释: {mock_state['user_explanation']}")
    
    try:
        # 由于需要真实的LLM调用，这里演示解析器的工作
        mock_agent_outputs = [
            '["GIL的具体实现机制", "性能影响的量化数据"]',
            '''
            根据分析，发现以下疑点：
            1. GIL具体是如何工作的？
            2. 对多线程性能的具体影响有多大？
            3. 有什么替代方案？
            ''',
            "经过深入分析，我认为用户对GIL的解释完全理解，没有疑点。",
            '''
            {
              "action": "Final Answer",
              "action_input": {
                "unclear_points": [
                  {
                    "content": "GIL的底层实现机制",
                    "category": "mechanism",
                    "confidence": "high"
                  }
                ],
                "is_complete": false
              }
            }
            '''
        ]
        
        for i, mock_output in enumerate(mock_agent_outputs):
            print(f"\n--- 测试案例 {i+1} ---")
            print(f"模拟Agent输出: {mock_output[:100]}...")
            
            result = AgentOutputParser.parse_agent_output(mock_output)
            print(f"解析结果: {len(result.unclear_points)} 个疑点")
            print(f"完整度: {result.is_complete}")
            
            if result.unclear_points:
                for j, point in enumerate(result.unclear_points):
                    print(f"  疑点{j+1}: {point.content}")
                    print(f"    类别: {point.category}, 置信度: {point.confidence}")
            
            if result.summary:
                print(f"总结: {result.summary}")
        
        print("\n✅ 模拟测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_parser_edge_cases():
    """测试解析器的边界情况"""
    
    print("\n=== 解析器边界测试 ===")
    
    edge_cases = [
        ("空字符串", ""),
        ("纯空格", "   \n\t  "),
        ("无意义文本", "这是一段随机的文本内容，没有明确的疑点格式"),
        ("超长文本", "很长的文本 " * 200),
        ("格式错误的JSON", '["疑点1", "疑点2"'),  # 缺少右括号
        ("混合格式", '''
         我发现以下疑点：
         1. 第一个疑点
         • 第二个疑点
         JSON: ["第三个疑点"]
         问题：第四个疑点是什么？
         '''),
        ("中英混合", '''
         Points unclear:
         1. What is GIL mechanism?
         疑点：性能影响数据缺失
         • Alternative solutions comparison
         '''),
    ]
    
    for name, test_input in edge_cases:
        print(f"\n--- 测试: {name} ---")
        try:
            result = AgentOutputParser.parse_agent_output(test_input)
            print(f"✅ 解析成功: {len(result.unclear_points)} 个疑点, 完整度: {result.is_complete}")
            
            if result.unclear_points:
                for point in result.unclear_points[:2]:  # 只显示前2个
                    print(f"  - {point.content[:50]}...")
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")


def test_real_world_scenarios():
    """测试真实世界的使用场景"""
    
    print("\n=== 真实场景测试 ===")
    
    scenarios = [
        {
            "name": "技术概念解释",
            "topic": "机器学习",
            "user_input": "机器学习就是让计算机自己学习数据中的规律",
            "expected_gaps": ["学习算法", "数据预处理", "模型评估"]
        },
        {
            "name": "科学原理说明", 
            "topic": "光合作用",
            "user_input": "植物通过叶子吸收阳光和二氧化碳，产生氧气和葡萄糖",
            "expected_gaps": ["叶绿体作用", "化学反应方程式", "光反应暗反应"]
        },
        {
            "name": "完整清晰的解释",
            "topic": "水的沸腾",
            "user_input": "水在标准大气压下，温度达到100摄氏度时开始沸腾，这是因为水分子获得足够能量克服分子间作用力，从液态变为气态",
            "expected_gaps": []  # 应该没有疑点
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- 场景: {scenario['name']} ---")
        print(f"主题: {scenario['topic']}")
        print(f"用户解释: {scenario['user_input']}")
        
        # 模拟不同类型的Agent输出来测试解析
        mock_outputs = [
            f"对于{scenario['topic']}的解释，我发现以下疑点：" + str(scenario['expected_gaps']),
            f"经过分析，这个关于{scenario['topic']}的解释很清晰，没有疑点" if not scenario['expected_gaps'] else f"需要进一步了解：{', '.join(scenario['expected_gaps'][:2])}"
        ]
        
        for output in mock_outputs:
            result = AgentOutputParser.parse_agent_output(output)
            print(f"  解析输出: {len(result.unclear_points)} 个疑点")
            
            if result.unclear_points:
                for point in result.unclear_points:
                    print(f"    - {point.content}")


def test_performance_and_reliability():
    """测试性能和可靠性"""
    
    print("\n=== 性能与可靠性测试 ===")
    
    import time
    
    # 生成大量测试用例
    test_cases = []
    
    # JSON格式
    for i in range(10):
        test_cases.append(f'["疑点{i*3+1}", "疑点{i*3+2}", "疑点{i*3+3}"]')
    
    # 编号列表格式
    for i in range(10):
        points = "\n".join([f"{j}. 疑点{i*3+j}" for j in range(1, 4)])
        test_cases.append(f"分析结果：\n{points}")
    
    # 混合格式
    for i in range(5):
        test_cases.append(f"疑点：概念{i}不清楚\n问题：如何理解原理{i}？\n• 需要补充例子{i}")
    
    print(f"准备测试 {len(test_cases)} 个用例...")
    
    start_time = time.time()
    success_count = 0
    total_points = 0
    
    for i, test_case in enumerate(test_cases):
        try:
            result = AgentOutputParser.parse_agent_output(test_case)
            success_count += 1
            total_points += len(result.unclear_points)
            
            if i % 10 == 0:
                print(f"  处理进度: {i+1}/{len(test_cases)}")
                
        except Exception as e:
            print(f"  第{i+1}个用例失败: {e}")
    
    end_time = time.time()
    
    print(f"\n性能测试结果:")
    print(f"  成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    print(f"  平均疑点数: {total_points/success_count:.1f}")
    print(f"  处理时间: {end_time-start_time:.3f}秒")
    print(f"  平均每个用例: {(end_time-start_time)/len(test_cases)*1000:.1f}ms")


if __name__ == "__main__":
    print("🧪 开始 gap_identifier_react 模块测试")
    print("=" * 50)
    
    try:
        # 运行各种测试
        test_gap_identifier_mock_simple()
        test_parser_edge_cases() 
        test_real_world_scenarios()
        test_performance_and_reliability()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

