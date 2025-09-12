"""
智能疑点分析演示

展示新的疑点理解Agent如何工作，相比传统的文本解析，
这个Agent能够真正理解用户的解释并识别需要澄清的知识点。
"""

import asyncio
import json
from typing import Dict, Any

# 确保能够导入项目模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.feynman.agents.core.explanation_analyzer import ExplanationAnalyzer
from src.feynman.agents.parsers.output_parser import AnalysisResult


def print_analysis_result(result: AnalysisResult, title: str):
    """美化输出分析结果"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    
    print(f"🎯 理解完整性: {'✅ 完整' if result.is_complete else '❓ 有疑点'}")
    print(f"📝 分析总结: {result.summary}")
    
    if result.understanding_quality:
        print(f"🎓 理解质量: {result.understanding_quality}")
    
    if result.key_concepts:
        print(f"🔑 关键概念: {', '.join(result.key_concepts)}")
    
    if result.knowledge_depth:
        print(f"🌊 知识深度: {result.knowledge_depth}")
    
    if result.unclear_points:
        print(f"\n❓ 识别到的疑点 ({len(result.unclear_points)}个):")
        for i, point in enumerate(result.unclear_points, 1):
            print(f"\n   {i}. 【{point.category.upper()}】{point.content}")
            print(f"      置信度: {point.confidence.value}")
            print(f"      优先级: {point.priority}/5")
            if point.reasoning:
                print(f"      分析原因: {point.reasoning}")
            if point.educational_value:
                print(f"      教育价值: {point.educational_value}")
            if point.suggested_approach:
                print(f"      建议方式: {point.suggested_approach}")
    
    if result.improvement_suggestions:
        print(f"\n💡 改进建议:")
        for suggestion in result.improvement_suggestions:
            print(f"   • {suggestion}")


async def demo_explanation_analysis():
    """演示疑点理解Agent的工作效果"""
    
    print("🚀 智能疑点分析系统演示")
    print("="*60)
    
    # 初始化分析器
    try:
        analyzer = ExplanationAnalyzer()
        print("✅ 疑点理解Agent初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 请确保已配置OpenAI或智谱AI的API密钥")
        return
    
    # 测试案例
    test_cases = [
        {
            "title": "表面理解 - 机器学习",
            "topic": "机器学习",
            "explanation": """
            机器学习就是让计算机自己学习。它有很多算法，比如决策树、神经网络等。
            通过训练数据，机器可以学会识别图片、翻译语言等任务。
            现在机器学习很火，到处都在用。
            """
        },
        {
            "title": "中等理解 - 量子计算",
            "topic": "量子计算", 
            "explanation": """
            量子计算利用量子力学原理进行计算。传统计算机用比特表示0或1，
            而量子计算机用量子比特，可以同时处于0和1的叠加态。
            这种叠加态让量子计算机能够并行处理多种可能性，
            理论上在某些问题上比传统计算机快指数倍。
            但量子态很脆弱，容易受环境干扰而发生退相干。
            """
        },
        {
            "title": "深入理解 - 区块链",
            "topic": "区块链技术",
            "explanation": """
            区块链是一种分布式账本技术，通过密码学哈希函数将交易数据组织成区块，
            并按时间顺序链接形成不可篡改的链式结构。每个区块包含前一区块的哈希值，
            确保了数据的完整性。共识机制如工作量证明(PoW)确保网络中的节点对账本状态达成一致。
            
            智能合约作为自执行的代码，在满足预定条件时自动执行，消除了对中介的需求。
            区块链的去中心化特性提供了抗审查性和容错性，但也带来了可扩展性三难困境：
            去中心化、安全性和可扩展性难以同时优化。
            
            不同的共识算法如PoS、DPoS在能耗和性能上各有权衡。
            """
        }
    ]
    
    # 逐一分析测试案例
    for case in test_cases:
        try:
            result = analyzer.analyze_explanation(
                topic=case["topic"],
                user_explanation=case["explanation"]
            )
            print_analysis_result(result, case["title"])
            
        except Exception as e:
            print(f"\n❌ 分析 '{case['title']}' 时出错: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 演示完成！")
    print("\n💡 对比观察：")
    print("• 表面理解：识别出概念定义和逻辑缺失")
    print("• 中等理解：发现需要深入解释的机制")  
    print("• 深入理解：提出边界条件和应用场景问题")


def demo_traditional_vs_intelligent():
    """对比传统解析器和智能分析器的差异"""
    
    print("\n" + "="*60)
    print("🔍 传统解析 vs 智能分析对比")
    print("="*60)
    
    # 导入传统解析器
    from src.feynman.agents.parsers.output_parser import AgentOutputParser
    
    # 模拟Agent输出（传统方式需要Agent先输出结构化文本）
    mock_agent_output = """
    基于用户对机器学习的解释，我识别出以下疑点：
    1. 什么是"让计算机自己学习"的具体机制？
    2. 决策树和神经网络的工作原理有何不同？
    3. 训练数据是如何影响学习效果的？
    """
    
    # 传统解析
    print("\n📜 传统文本解析结果:")
    traditional_result = AgentOutputParser.parse_agent_output(mock_agent_output)
    print(f"疑点数量: {len(traditional_result.unclear_points)}")
    for point in traditional_result.unclear_points:
        print(f"• {point.content}")
    
    # 智能分析
    print("\n🧠 智能语义分析结果:")
    try:
        analyzer = ExplanationAnalyzer()
        explanation = "机器学习就是让计算机自己学习。它有很多算法，比如决策树、神经网络等。"
        intelligent_result = analyzer.analyze_explanation("机器学习", explanation)
        
        print(f"疑点数量: {len(intelligent_result.unclear_points)}")
        for point in intelligent_result.unclear_points:
            print(f"• 【{point.category}】{point.content} (置信度: {point.confidence.value})")
    
    except Exception as e:
        print(f"智能分析暂不可用: {e}")
    
    print("\n💡 主要差异:")
    print("• 传统方式: 依赖Agent先输出结构化文本，然后文本解析")
    print("• 智能方式: 直接理解用户解释，基于语义分析识别疑点")
    print("• 智能方式提供更丰富的元信息：类别、置信度、教育价值等")


if __name__ == "__main__":
    print("🎓 费曼学习系统 - 智能疑点分析演示")
    
    # 检查环境配置 - 优先使用OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        if not os.getenv("ZHIPU_API_KEY"):
            print("\n⚠️  请先配置API密钥:")
            print("推荐使用: export OPENAI_API_KEY='your-key-here'")
            print("或备选: export ZHIPU_API_KEY='your-key-here'")
            exit(1)
        else:
            print("\n💡 检测到智谱AI密钥，但建议使用OpenAI以获得更好的性能")
    else:
        print("\n✅ 使用OpenAI API密钥")
    
    # 运行演示
    asyncio.run(demo_explanation_analysis())
    
    # 对比演示
    demo_traditional_vs_intelligent()
