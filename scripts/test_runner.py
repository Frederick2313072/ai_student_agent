#!/usr/bin/env python3
"""
测试运行器 - 独立运行各种测试而不依赖复杂的构建系统
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_output_parser_tests():
    """运行输出解析器测试"""
    print("🧪 运行输出解析器单元测试")
    print("=" * 50)
    
    try:
        from agent.output_parser import AgentOutputParser, AnalysisResult, UnclearPoint, ConfidenceLevel
        
        # 基础功能测试
        print("1. 测试基础JSON解析...")
        output = '["GIL的具体实现机制", "性能影响的量化数据", "替代方案的对比"]'
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 3
        assert result.unclear_points[0].content == "GIL的具体实现机制"
        print("   ✅ 通过")
        
        # 空列表测试
        print("2. 测试空列表解析...")
        output = 'AI分析结果：[]'
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 0
        assert result.is_complete
        print("   ✅ 通过")
        
        # 编号列表测试
        print("3. 测试编号列表解析...")
        output = '''
        根据分析，我发现以下疑点：
        1. GIL的具体实现机制不清楚
        2. 多线程性能影响的具体数据缺失
        3. 与其他语言的对比说明不足
        '''
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) >= 1
        print("   ✅ 通过")
        
        # 关键词提取测试
        print("4. 测试关键词提取...")
        output = "经过深入分析，我认为用户对GIL的解释完全理解，概念清晰，逻辑完整。"
        result = AgentOutputParser.parse_agent_output(output)
        assert result.is_complete
        print("   ✅ 通过")
        
        # 降级处理测试
        print("5. 测试降级处理...")
        output = "这是一段无法解析的随机文本内容"
        result = AgentOutputParser.parse_agent_output(output)
        assert len(result.unclear_points) == 1
        assert result.unclear_points[0].confidence == ConfidenceLevel.LOW
        print("   ✅ 通过")
        
        print("\n🎉 输出解析器测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_integration_tests():
    """运行集成测试"""
    print("\n🔧 运行集成测试")
    print("=" * 50)
    
    try:
        from tests.test_gap_identifier_integration import (
            test_gap_identifier_mock_simple,
            test_parser_edge_cases,
            test_real_world_scenarios,
            test_performance_and_reliability
        )
        
        print("运行模拟测试...")
        test_gap_identifier_mock_simple()
        
        print("\n运行边界测试...")
        test_parser_edge_cases()
        
        print("\n运行场景测试...")
        test_real_world_scenarios()
        
        print("\n运行性能测试...")
        test_performance_and_reliability()
        
        print("\n🎉 集成测试全部完成！")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_manual_verification():
    """手动验证测试"""
    print("\n🔍 手动验证测试")
    print("=" * 50)
    
    try:
        from agent.output_parser import AgentOutputParser
        
        # 交互式测试
        test_inputs = [
            "请测试一下这个Agent输出解析：['机器学习算法原理', '数据预处理步骤', '模型评估方法']",
            "分析结果：1. 概念定义不清 2. 缺少具体例子 3. 需要补充应用场景",
            "用户的解释非常完整，我完全理解了，没有任何疑点需要澄清。",
            "疑点：实现机制不明确\n问题：性能如何优化？\n• 缺少对比分析"
        ]
        
        for i, test_input in enumerate(test_inputs, 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"输入: {test_input}")
            
            result = AgentOutputParser.parse_agent_output(test_input)
            
            print(f"输出: {len(result.unclear_points)} 个疑点")
            print(f"完整度: {result.is_complete}")
            
            if result.unclear_points:
                for j, point in enumerate(result.unclear_points, 1):
                    print(f"  疑点{j}: {point.content}")
                    print(f"    类别: {point.category}, 置信度: {point.confidence}")
            
            if result.summary:
                print(f"总结: {result.summary}")
        
        print("\n🎉 手动验证完成！")
        return True
        
    except Exception as e:
        print(f"❌ 手动验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 AI学生Agent - gap_identifier_react 模块测试套件")
    print("=" * 60)
    
    results = []
    
    # 运行各种测试
    results.append(("输出解析器测试", run_output_parser_tests()))
    results.append(("集成测试", run_integration_tests()))
    results.append(("手动验证", run_manual_verification()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试套件通过")
    
    if passed == total:
        print("🎉 所有测试通过！gap_identifier_react 模块工作正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

