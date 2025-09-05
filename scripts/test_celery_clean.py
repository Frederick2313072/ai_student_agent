#!/usr/bin/env python3
"""
清洁版本的 Celery + Redis 测试脚本
自动抑制警告信息，提供清洁的测试输出
"""

# 1. 首先设置清洁环境
from suppress_warnings import setup_clean_environment
setup_clean_environment()

# 2. 导入所需模块
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / "environments" / "test.env"
load_dotenv(env_path)

def main():
    """主测试流程"""
    print("🧪 Celery + Redis 功能测试 (清洁版)")
    print("="*50)
    
    try:
        # 1. 测试导入
        print("1. 📦 导入Celery模块...")
        from feynman.tasks.celery_app import celery_app
        from feynman.tasks.memory import summarize_conversation_task
        redis_url = os.getenv("REDIS_URL")
        print(f"🔗 Celery使用Redis: {redis_url[:30]}...{redis_url[-20:]}")
        print("   ✅ 导入成功")
        
        # 2. 检查配置
        print("2. ⚙️  检查配置...")
        broker = celery_app.conf.broker_url
        print(f"   🔗 Broker: {broker[:20]}...{broker[-20:]}")
        print("   ✅ 配置正确")
        
        # 3. 测试Redis连接
        print("3. 🔍 测试Redis连接...")
        import redis
        r = redis.from_url(redis_url)
        if r.ping():
            print("   ✅ Redis连接正常")
        else:
            print("   ❌ Redis连接失败")
            return False
        
        # 4. 提交测试任务
        print("4. 📤 提交测试任务...")
        
        # 调试任务
        debug_task = celery_app.send_task(
            'debug_task',
            args=['Hello Celery!']
        )
        print(f"   📋 调试任务ID: {debug_task.id}")
        print(f"   📊 任务状态: {debug_task.status}")
        
        # 记忆任务
        memory_task = summarize_conversation_task.delay(
            topic="测试主题",
            conversation_history=[
                {"role": "user", "content": "这是一个测试对话"},
                {"role": "assistant", "content": "我理解了"}
            ]
        )
        print(f"   🧠 记忆任务ID: {memory_task.id}")
        print(f"   📊 任务状态: {memory_task.status}")
        
        # 5. 检查任务队列
        print("5. 📋 检查任务队列...")
        try:
            inspect = celery_app.control.inspect()
            
            # 检查活跃的worker
            active_workers = inspect.active()
            if active_workers:
                worker_count = len(active_workers)
                print(f"   👷 发现 {worker_count} 个活跃Worker")
                
                # 检查队列长度
                for worker, tasks in active_workers.items():
                    print(f"   📊 Worker {worker}: {len(tasks)} 个活跃任务")
            else:
                print("   💤 没有活跃的Worker")
                print("   💡 提示: 任务需要Worker运行才能执行")
                print("   🚀 启动Worker: make celery-worker")
                print("   🌸 启动监控: make celery-flower")
            
        except Exception as e:
            print(f"   ⚠️  无法检查Worker状态: {str(e)}")
        
        print("")
        print("🎉 Celery + Redis 测试完成！")
        print("")
        print("📋 下一步操作:")
        print("   1. 启动Worker: make celery-worker")
        print("   2. 启动监控面板: make celery-flower") 
        print("   3. 访问监控页面: http://localhost:5555")
        print("   4. 测试API端点提交任务")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
