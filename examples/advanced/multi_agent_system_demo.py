"""
多Agent系统集成演示

展示新的多Agent架构如何协同工作，包括智能协调、动态调度和综合分析。
"""

import asyncio
import json
import time
from typing import Dict, Any

# 确保能够导入项目模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.feynman.agents.core.multi_agent_workflow import execute_multi_agent_workflow
from src.feynman.agents.core.agent_registry import get_system_stats


def print_banner(title: str):
    """打印标题横幅"""
    print(f"\n{'='*80}")
    print(f"🎯 {title}")
    print(f"{'='*80}")


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'─'*60}")
    print(f"📋 {title}")
    print(f"{'─'*60}")


def print_results(results: Dict[str, Any], title: str):
    """美化输出结果"""
    print_section(title)
    
    print(f"✅ 执行成功: {'是' if results.get('success', False) else '否'}")
    print(f"⏱️ 执行时间: {results.get('execution_time', 0):.2f}秒")
    print(f"📝 完成任务: {len(results.get('completed_tasks', []))}")
    print(f"❌ 错误数量: {results.get('error_count', 0)}")
    
    # 显示生成的问题
    questions = results.get('questions', [])
    if questions:
        print(f"\n🤔 生成的问题 ({len(questions)}个):")
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
    
    # 显示学习洞察
    insights = results.get('learning_insights', [])
    if insights:
        print(f"\n💡 学习洞察 ({len(insights)}个):")
        for i, insight in enumerate(insights, 1):
            print(f"   {i}. {insight}")
    
    # 显示学习报告摘要
    report = results.get('learning_report', {})
    if report:
        print(f"\n📊 学习报告摘要:")
        print(f"   整体理解水平: {report.get('overall_understanding', 0):.2f}")
        print(f"   学习进度: {report.get('learning_progress', 0):.2f}")
        
        strengths = report.get('strengths', [])
        if strengths:
            print(f"   优势: {', '.join(strengths[:3])}")
        
        improvements = report.get('areas_for_improvement', [])
        if improvements:
            print(f"   改进点: {', '.join(improvements[:3])}")


async def test_basic_workflow():
    """测试基础工作流"""
    print_section("基础工作流测试")
    
    inputs = {
        "topic": "机器学习",
        "explanation": """
        机器学习是人工智能的一个分支，它让计算机能够从数据中学习。
        主要有三种类型：监督学习、无监督学习和强化学习。
        监督学习使用标记的数据来训练模型，无监督学习从未标记的数据中发现模式。
        """,
        "session_id": "test_basic_001"
    }
    
    start_time = time.time()
    results = await execute_multi_agent_workflow(inputs)
    execution_time = time.time() - start_time
    
    print(f"工作流执行时间: {execution_time:.2f}秒")
    print_results(results, "基础工作流结果")
    
    return results


async def test_complex_workflow():
    """测试复杂工作流"""
    print_section("复杂工作流测试")
    
    inputs = {
        "topic": "量子计算",
        "explanation": """
        量子计算利用量子力学的奇特性质来处理信息。传统计算机使用比特，
        只能是0或1，而量子计算机使用量子比特，可以同时处于0和1的叠加态。
        这种叠加态让量子计算机能够并行处理大量计算。但是量子态很脆弱，
        容易受到环境干扰而发生退相干。量子纠缠是另一个重要现象，
        让相距很远的粒子能够瞬间影响彼此的状态。
        """,
        "session_id": "test_complex_002"
    }
    
    start_time = time.time()
    results = await execute_multi_agent_workflow(inputs)
    execution_time = time.time() - start_time
    
    print(f"工作流执行时间: {execution_time:.2f}秒")
    print_results(results, "复杂工作流结果")
    
    return results


async def test_error_handling():
    """测试错误处理"""
    print_section("错误处理测试")
    
    inputs = {
        "topic": "",  # 空主题，可能引发错误
        "explanation": "",  # 空解释，可能引发错误
        "session_id": "test_error_003"
    }
    
    start_time = time.time()
    results = await execute_multi_agent_workflow(inputs)
    execution_time = time.time() - start_time
    
    print(f"工作流执行时间: {execution_time:.2f}秒")
    print_results(results, "错误处理结果")
    
    return results


async def test_multi_session():
    """测试多会话并发"""
    print_section("多会话并发测试")
    
    test_cases = [
        {
            "topic": "深度学习",
            "explanation": "深度学习使用多层神经网络来学习数据的复杂模式。",
            "session_id": "concurrent_001"
        },
        {
            "topic": "区块链",
            "explanation": "区块链是一种分布式账本技术，通过密码学确保数据不可篡改。",
            "session_id": "concurrent_002"
        },
        {
            "topic": "云计算",
            "explanation": "云计算提供按需访问的计算资源池，包括服务器、存储和网络。",
            "session_id": "concurrent_003"
        }
    ]
    
    print(f"启动 {len(test_cases)} 个并发会话...")
    
    start_time = time.time()
    
    # 并发执行
    tasks = [execute_multi_agent_workflow(case) for case in test_cases]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    execution_time = time.time() - start_time
    
    print(f"并发执行总时间: {execution_time:.2f}秒")
    
    # 分析结果
    successful_sessions = 0
    total_questions = 0
    total_insights = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"   会话 {i+1} 失败: {result}")
        else:
            if result.get('success', False):
                successful_sessions += 1
            total_questions += len(result.get('questions', []))
            total_insights += len(result.get('learning_insights', []))
            
            print(f"   会话 {i+1}: 问题 {len(result.get('questions', []))} 个, "
                  f"洞察 {len(result.get('learning_insights', []))} 个")
    
    print(f"\n📊 并发测试统计:")
    print(f"   成功会话: {successful_sessions}/{len(test_cases)}")
    print(f"   总问题数: {total_questions}")
    print(f"   总洞察数: {total_insights}")
    print(f"   平均每会话时间: {execution_time/len(test_cases):.2f}秒")
    
    return results


def test_system_statistics():
    """测试系统统计"""
    print_section("系统统计信息")
    
    try:
        stats = get_system_stats()
        
        print(f"📈 系统统计:")
        print(f"   总Agent数: {stats.get('total_agents', 0)}")
        print(f"   活跃Agent数: {stats.get('active_agents', 0)}")
        print(f"   平均负载: {stats.get('performance', {}).get('average_load', 0):.2f}")
        print(f"   平均响应时间: {stats.get('performance', {}).get('average_response_time', 0):.2f}秒")
        print(f"   整体成功率: {stats.get('performance', {}).get('overall_success_rate', 0):.2f}")
        
        # Agent类型统计
        type_stats = stats.get('type_statistics', {})
        if type_stats:
            print(f"\n🤖 Agent类型分布:")
            for agent_type, counts in type_stats.items():
                print(f"   {agent_type}: {counts.get('active', 0)}/{counts.get('total', 0)} 活跃")
        
        # 健康状态统计
        health_stats = stats.get('health_statistics', {})
        if health_stats:
            print(f"\n💚 健康状态分布:")
            for status, count in health_stats.items():
                if count > 0:
                    print(f"   {status}: {count}")
        
        return stats
        
    except Exception as e:
        print(f"❌ 获取系统统计失败: {e}")
        return {}


async def performance_benchmark():
    """性能基准测试"""
    print_section("性能基准测试")
    
    test_cases = [
        ("简单", "机器学习是AI的一部分。"),
        ("中等", "机器学习包括监督学习、无监督学习和强化学习三种主要类型。"),
        ("复杂", """
        机器学习是人工智能的核心技术之一，通过算法让计算机从数据中自动学习模式。
        主要分为监督学习、无监督学习和强化学习。监督学习使用标记数据训练模型，
        如分类和回归问题。无监督学习从无标记数据中发现隐藏模式，如聚类分析。
        强化学习通过与环境交互来学习最优策略，广泛应用于游戏和机器人控制。
        """)
    ]
    
    results = {}
    
    for complexity, explanation in test_cases:
        print(f"\n测试复杂度: {complexity}")
        
        inputs = {
            "topic": "机器学习",
            "explanation": explanation,
            "session_id": f"benchmark_{complexity.lower()}"
        }
        
        # 多次测试取平均
        times = []
        question_counts = []
        
        for i in range(3):
            start_time = time.time()
            result = await execute_multi_agent_workflow(inputs)
            execution_time = time.time() - start_time
            
            times.append(execution_time)
            question_counts.append(len(result.get('questions', [])))
            
            print(f"   第 {i+1} 次: {execution_time:.2f}秒, {len(result.get('questions', []))}个问题")
        
        avg_time = sum(times) / len(times)
        avg_questions = sum(question_counts) / len(question_counts)
        
        results[complexity] = {
            "average_time": avg_time,
            "average_questions": avg_questions,
            "times": times
        }
        
        print(f"   平均时间: {avg_time:.2f}秒")
        print(f"   平均问题数: {avg_questions:.1f}")
    
    print(f"\n📊 性能基准总结:")
    for complexity, data in results.items():
        print(f"   {complexity}: {data['average_time']:.2f}秒, {data['average_questions']:.1f}问题")
    
    return results


async def main():
    """主演示函数"""
    print_banner("多Agent系统集成演示")
    
    print("🚀 启动多Agent系统演示...")
    print("💡 本演示将展示智能协调、动态调度和综合分析能力")
    
    # 检查环境配置 - 优先使用OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        if not os.getenv("ZHIPU_API_KEY"):
            print("\n⚠️  请先配置API密钥:")
            print("推荐使用: export OPENAI_API_KEY='your-key-here'")
            print("或备选: export ZHIPU_API_KEY='your-key-here'")
            return
        else:
            print("\n💡 检测到智谱AI密钥，但建议使用OpenAI以获得更好的性能")
    else:
        print("\n✅ 使用OpenAI API密钥")
    
    try:
        # 1. 系统统计
        test_system_statistics()
        
        # 2. 基础工作流测试
        await test_basic_workflow()
        
        # 3. 复杂工作流测试
        await test_complex_workflow()
        
        # 4. 错误处理测试
        await test_error_handling()
        
        # 5. 多会话并发测试
        await test_multi_session()
        
        # 6. 性能基准测试
        await performance_benchmark()
        
        # 7. 最终系统统计
        print_section("最终系统状态")
        test_system_statistics()
        
        print_banner("演示完成")
        print("✅ 多Agent系统演示成功完成！")
        print("🎯 系统展现了出色的协调能力、容错性和性能表现")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🎓 费曼学习系统 - 多Agent架构演示")
    
    # 运行演示
    asyncio.run(main())
