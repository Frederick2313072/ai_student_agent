#!/usr/bin/env python3
"""
异步任务队列系统演示

展示费曼学习系统的任务队列功能，包括：
- 任务添加和执行
- 优先级控制
- 重试机制
- 状态监控
"""

import asyncio
import random
import time
from core.task_queue import task_queue_manager, TaskStatus

# 模拟任务函数
async def simulate_memory_consolidation(topic: str, conversation_length: int):
    """模拟记忆固化任务"""
    print(f"🧠 开始记忆固化: {topic} (对话长度: {conversation_length})")
    
    # 模拟LLM调用耗时
    processing_time = random.uniform(1, 3)
    await asyncio.sleep(processing_time)
    
    # 10%概率失败（用于测试重试机制）
    if random.random() < 0.1:
        raise Exception(f"LLM调用失败: {topic}")
    
    result = f"已固化 '{topic}' 的记忆，处理了 {conversation_length} 轮对话"
    print(f"✅ 记忆固化完成: {result}")
    return result

def simulate_cost_calculation(session_id: str, tokens_used: int):
    """模拟成本计算任务（同步函数）"""
    print(f"💰 计算成本: 会话 {session_id}, Token用量 {tokens_used}")
    
    # 模拟计算耗时
    time.sleep(random.uniform(0.5, 1.5))
    
    cost = tokens_used * 0.002  # 假设单价
    result = f"会话 {session_id} 成本: ${cost:.4f}"
    print(f"✅ 成本计算完成: {result}")
    return result

async def simulate_user_feedback_analysis(feedback_text: str, rating: int):
    """模拟用户反馈分析任务"""
    print(f"📊 分析用户反馈: '{feedback_text[:30]}...' (评分: {rating})")
    
    # 模拟分析耗时
    await asyncio.sleep(random.uniform(2, 4))
    
    sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"
    result = f"反馈情感: {sentiment}, 评分: {rating}"
    print(f"✅ 反馈分析完成: {result}")
    return result

async def failing_task():
    """总是失败的任务（用于测试重试机制）"""
    print("❌ 执行注定失败的任务...")
    await asyncio.sleep(1)
    raise Exception("这个任务总是失败")

async def long_running_task(duration: int):
    """长时间运行的任务"""
    print(f"⏳ 开始长时间任务，预计耗时 {duration}s")
    await asyncio.sleep(duration)
    return f"长时间任务完成，实际耗时 {duration}s"

async def demonstrate_basic_usage():
    """演示基础用法"""
    print("🚀 任务队列基础功能演示")
    print("=" * 50)
    
    # 启动任务队列
    print("启动任务队列...")
    await task_queue_manager.start()
    
    # 添加各种任务
    tasks = []
    
    # 高优先级任务
    task_id_1 = await task_queue_manager.add_task(
        simulate_memory_consolidation,
        "机器学习基础",
        5,
        name="memory_consolidation_ml",
        priority=10,  # 高优先级
        max_retries=2
    )
    tasks.append(task_id_1)
    print(f"添加高优先级任务: {task_id_1}")
    
    # 中等优先级任务
    task_id_2 = await task_queue_manager.add_task(
        simulate_user_feedback_analysis,
        "这个AI学生问的问题很有深度，帮我理解了概念的不足",
        5,
        name="feedback_analysis",
        priority=5,
        max_retries=3
    )
    tasks.append(task_id_2)
    print(f"添加中等优先级任务: {task_id_2}")
    
    # 低优先级任务（同步函数）
    task_id_3 = await task_queue_manager.add_task(
        simulate_cost_calculation,
        "session_123",
        1500,
        name="cost_calculation",
        priority=1,  # 低优先级
        max_retries=1
    )
    tasks.append(task_id_3)
    print(f"添加低优先级任务: {task_id_3}")
    
    # 等待任务完成
    print("\n等待任务执行...")
    await asyncio.sleep(6)
    
    # 检查任务状态
    print("\n📊 任务执行结果:")
    print("-" * 30)
    
    for task_id in tasks:
        task = await task_queue_manager.get_task_status(task_id)
        if task:
            status_icon = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌", 
                TaskStatus.RUNNING: "🔄",
                TaskStatus.PENDING: "⏳",
                TaskStatus.RETRY: "🔁"
            }.get(task.status, "❓")
            
            print(f"{status_icon} {task.name}: {task.status.value}")
            if task.result:
                print(f"   结果: {task.result}")
            if task.error:
                print(f"   错误: {task.error}")
            if task.retry_count > 0:
                print(f"   重试次数: {task.retry_count}")

async def demonstrate_priority_and_retry():
    """演示优先级和重试机制"""
    print("\n🎯 优先级和重试机制演示") 
    print("=" * 50)
    
    # 添加多个不同优先级的任务
    task_ids = []
    
    # 低优先级任务（应该最后执行）
    for i in range(3):
        task_id = await task_queue_manager.add_task(
            simulate_cost_calculation,
            f"low_priority_session_{i}",
            100 * (i + 1),
            name=f"low_priority_task_{i}",
            priority=1
        )
        task_ids.append(task_id)
    
    # 高优先级任务（应该先执行）
    task_id = await task_queue_manager.add_task(
        simulate_memory_consolidation,
        "紧急记忆固化",
        10,
        name="urgent_memory_task",
        priority=20  # 很高的优先级
    )
    task_ids.append(task_id)
    
    # 会失败的任务（测试重试）
    task_id = await task_queue_manager.add_task(
        failing_task,
        name="failing_task_demo",
        priority=15,
        max_retries=3
    )
    task_ids.append(task_id)
    
    print(f"添加了 {len(task_ids)} 个任务，观察执行顺序...")
    
    # 等待执行
    await asyncio.sleep(8)
    
    print("\n执行结果分析:")
    print("-" * 30)
    
    for task_id in task_ids:
        task = await task_queue_manager.get_task_status(task_id)
        if task:
            duration = ""
            if task.started_at and task.completed_at:
                duration = f" (耗时: {(task.completed_at - task.started_at).total_seconds():.1f}s)"
            elif task.started_at:
                duration = f" (进行中: {(task.started_at).strftime('%H:%M:%S')})"
            
            print(f"[优先级 {task.priority:2d}] {task.name}: {task.status.value}{duration}")
            if task.retry_count > 0:
                print(f"                重试 {task.retry_count} 次")

async def demonstrate_monitoring():
    """演示监控功能"""
    print("\n📈 队列监控演示")
    print("=" * 50)
    
    # 添加多个任务制造负载
    print("添加多个任务...")
    task_ids = []
    
    for i in range(10):
        task_id = await task_queue_manager.add_task(
            long_running_task,
            2,  # 2秒的任务
            name=f"batch_task_{i}",
            priority=random.randint(1, 10)
        )
        task_ids.append(task_id)
    
    # 实时监控队列状态
    print("\n实时监控队列状态:")
    print("-" * 40)
    
    for _ in range(6):  # 监控6次
        stats = task_queue_manager.get_queue_stats()
        print(f"队列大小: {stats['queue_size']:2d} | "
              f"运行中: {stats['running_tasks']:2d} | "
              f"待处理: {stats['pending_tasks']:2d} | "
              f"已完成: {stats['completed_tasks']:2d} | "
              f"失败: {stats['failed_tasks']:2d}")
        
        await asyncio.sleep(2)
    
    # 显示最近任务
    print("\n最近任务状态:")
    print("-" * 30)
    
    recent_tasks = task_queue_manager.get_recent_tasks(limit=5)
    for task_info in recent_tasks:
        status_icon = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(task_info["status"], "❓")
        print(f"{status_icon} {task_info['name']} - {task_info['status']} (优先级: {task_info['priority']})")

async def demonstrate_timeout():
    """演示任务超时功能"""
    print("\n⏰ 任务超时演示")
    print("=" * 50)
    
    # 添加会超时的任务
    task_id = await task_queue_manager.add_task(
        long_running_task,
        10,  # 需要10秒
        name="timeout_task", 
        timeout=3.0,  # 但只给3秒超时
        max_retries=1
    )
    
    print("添加一个10秒的任务，但设置3秒超时...")
    
    # 等待任务完成或超时
    await asyncio.sleep(5)
    
    task = await task_queue_manager.get_task_status(task_id)
    if task:
        print(f"任务状态: {task.status.value}")
        if task.error:
            print(f"错误信息: {task.error}")

async def main():
    """主演示函数"""
    print("🎓 费曼学习系统 - 异步任务队列演示")
    print("=" * 60)
    
    try:
        await demonstrate_basic_usage()
        await demonstrate_priority_and_retry()
        await demonstrate_monitoring()
        await demonstrate_timeout()
        
        # 最终统计
        print("\n📊 最终统计信息:")
        print("=" * 50)
        final_stats = task_queue_manager.get_queue_stats()
        
        for key, value in final_stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\n🎉 演示完成！")
        print("\n💡 任务队列特性总结:")
        print("✅ 支持异步和同步函数")
        print("✅ 任务优先级控制") 
        print("✅ 失败自动重试（指数退避）")
        print("✅ 任务超时控制")
        print("✅ 实时状态监控")
        print("✅ 并发数量控制")
        print("✅ 优雅启动和停止")
        
    except KeyboardInterrupt:
        print("\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n💥 演示过程中出现错误: {e}")
    finally:
        # 清理：停止任务队列
        print("\n🛑 正在停止任务队列...")
        await task_queue_manager.stop(graceful=True)
        print("任务队列已停止")

if __name__ == "__main__":
    asyncio.run(main())
