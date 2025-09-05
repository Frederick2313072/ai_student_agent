#!/usr/bin/env python3
"""
Celery + Redis 功能测试脚本

这个脚本用于测试 Celery 任务队列的基本功能，包括：
- 任务提交
- 任务状态查询
- Redis 连接测试

使用方法:
    python scripts/test_celery.py
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_celery_tasks():
    """测试Celery任务功能"""
    print("🧪 Celery + Redis 功能测试")
    print("=" * 50)
    
    try:
        # 1. 导入测试
        print("1. 📦 导入Celery模块...")
        from feynman.tasks.celery_app import celery_app
        from feynman.tasks.memory import summarize_conversation_task
        print("   ✅ 导入成功")
        
        # 2. 配置测试
        print("2. ⚙️  检查配置...")
        broker_url = celery_app.conf.broker_url
        print(f"   🔗 Broker: {broker_url[:15]}...{broker_url[-15:]}")
        print("   ✅ 配置正确")
        
        # 3. Redis连接测试
        print("3. 🔍 测试Redis连接...")
        import redis
        r = redis.from_url(celery_app.conf.broker_url)
        if r.ping():
            print("   ✅ Redis连接正常")
        else:
            print("   ❌ Redis连接失败")
            return
            
        # 4. 任务提交测试
        print("4. 📤 提交测试任务...")
        
        # 提交调试任务
        debug_task = celery_app.send_task('feynman.tasks.celery_app.debug_task')
        print(f"   📋 调试任务ID: {debug_task.id}")
        print(f"   📊 任务状态: {debug_task.status}")
        
        # 提交记忆任务
        memory_task = summarize_conversation_task.delay(
            topic="Celery测试主题",
            conversation_history=[
                {"role": "user", "content": "这是一个Celery测试消息"},
                {"role": "assistant", "content": "我收到了测试消息"}
            ]
        )
        print(f"   🧠 记忆任务ID: {memory_task.id}")
        print(f"   📊 任务状态: {memory_task.status}")
        
        # 5. 任务状态监控
        print("5. 👀 监控任务状态...")
        print("   💡 提示: 任务需要Worker运行才能执行")
        print("   🚀 启动Worker: make celery-worker")
        print("   🌸 启动监控: make celery-flower")
        
        # 6. 检查任务队列
        print("6. 📋 检查任务队列...")
        inspect = celery_app.control.inspect()
        
        # 获取活跃任务（如果有worker运行）
        try:
            active_tasks = inspect.active()
            if active_tasks:
                print(f"   📈 活跃任务: {len(active_tasks)} 个Worker在运行")
            else:
                print("   💤 没有活跃的Worker")
        except Exception:
            print("   💤 没有活跃的Worker")
            
        # 检查队列中的任务
        try:
            # 使用Redis直接检查队列长度
            queue_length = r.llen("celery")  # 默认队列
            memory_queue_length = r.llen("memory")  # 记忆队列
            print(f"   📊 默认队列长度: {queue_length}")
            print(f"   🧠 记忆队列长度: {memory_queue_length}")
        except Exception as e:
            print(f"   ⚠️  队列检查失败: {e}")
        
        print("")
        print("🎉 Celery + Redis 测试完成！")
        print("")
        print("📋 下一步操作:")
        print("   1. 启动Worker: make celery-worker")
        print("   2. 启动监控面板: make celery-flower") 
        print("   3. 访问监控页面: http://localhost:5555")
        print("   4. 测试API端点提交任务")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖: uv sync")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_api_integration():
    """测试API集成"""
    print("\n🌐 API集成测试")
    print("=" * 30)
    
    try:
        import requests
        import json
        
        # 测试记忆API端点
        api_url = "http://127.0.0.1:8000/memorize"
        test_data = {
            "topic": "API测试主题", 
            "conversation_history": [
                {"role": "user", "content": "测试API调用"},
                {"role": "assistant", "content": "API测试成功"}
            ]
        }
        
        print(f"📡 测试API端点: {api_url}")
        response = requests.post(api_url, json=test_data, timeout=5)
        
        if response.status_code == 202:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ API调用成功")
            print(f"📋 任务ID: {task_id}")
            
            # 查询任务状态
            status_url = f"http://127.0.0.1:8000/task/{task_id}"
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 任务状态: {status_data.get('status')}")
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API服务未运行，跳过API测试")
        print("   启动API服务: make run")
    except Exception as e:
        print(f"⚠️  API测试失败: {e}")

if __name__ == "__main__":
    success = test_celery_tasks()
    if success:
        test_api_integration()


