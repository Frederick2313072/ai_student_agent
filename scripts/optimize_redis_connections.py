#!/usr/bin/env python3
"""
Redis连接优化脚本
解决连接数超限问题，优化连接池使用
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def check_redis_connections():
    """检查当前Redis连接使用情况"""
    print("🔍 检查Redis连接使用情况...")
    
    load_dotenv("environments/test.env")
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        print("❌ 未找到REDIS_URL配置")
        return False
    
    try:
        import redis
        
        # 创建连接池
        pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=5,  # 限制最大连接数
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={}
        )
        
        # 测试连接
        r = redis.Redis(connection_pool=pool)
        result = r.ping()
        
        if result:
            print("✅ Redis连接池测试成功")
            
            # 获取连接信息
            try:
                info = r.info()
                connected_clients = info.get('connected_clients', 'N/A')
                max_clients = info.get('maxclients', 'N/A')
                print(f"📊 当前连接数: {connected_clients}")
                print(f"📊 最大连接数: {max_clients}")
                
                if isinstance(connected_clients, int) and isinstance(max_clients, int):
                    usage_percent = (connected_clients / max_clients) * 100
                    print(f"📊 连接使用率: {usage_percent:.1f}%")
                    
                    if usage_percent > 80:
                        print("⚠️  连接使用率过高，建议优化")
                    
            except Exception as e:
                print(f"⚠️  无法获取连接统计: {e}")
            
        else:
            print("❌ Redis连接池测试失败")
            return False
            
        # 清理连接
        pool.disconnect()
        print("🧹 连接池已清理")
        
        return True
        
    except redis.exceptions.ConnectionError as e:
        if "max number of clients reached" in str(e):
            print("❌ Redis连接数已达上限")
            print("💡 建议:")
            print("   1. 等待连接自动释放 (5-15分钟)")
            print("   2. 使用本地Redis: ./scripts/setup_local_redis.sh")
            print("   3. 升级Redis Cloud套餐")
            return False
        else:
            print(f"❌ Redis连接错误: {e}")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def create_optimized_celery_config():
    """创建优化的Celery配置"""
    print("\n🔧 创建优化的Celery配置...")
    
    config_content = '''
# Celery Redis连接优化配置
# 添加到 src/feynman/tasks/celery_app.py

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv("environments/test.env")

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL环境变量未设置")

# 优化的Celery配置
celery_app = Celery(
    "feynman_tasks",
    broker=redis_url,
    backend=redis_url
)

# Redis连接池优化配置
celery_app.conf.update(
    # 连接池设置
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=3,
    
    # 连接池大小限制
    broker_pool_limit=5,  # 限制连接池大小
    
    # 连接超时设置
    broker_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPINTVL': 1,
            'TCP_KEEPCNT': 3,
            'TCP_KEEPIDLE': 1,
        },
        'health_check_interval': 30,
        'retry_on_timeout': True,
        'max_connections': 3,  # 每个worker的最大连接数
    },
    
    # Result backend优化
    result_backend_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPINTVL': 1,
            'TCP_KEEPCNT': 3,
            'TCP_KEEPIDLE': 1,
        },
        'health_check_interval': 30,
        'retry_on_timeout': True,
        'max_connections': 3,
    },
    
    # 任务路由优化
    task_routes={
        'feynman.tasks.memory.*': {'queue': 'memory'},
        'feynman.tasks.knowledge.*': {'queue': 'knowledge'},
        'feynman.tasks.monitoring.*': {'queue': 'monitoring'},
    },
    
    # Worker预取设置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 结果存储优化
    result_expires=3600,  # 1小时后清理结果
    task_ignore_result=False,
)
'''
    
    config_path = project_root / "docs" / "optimized_celery_config.py"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 优化配置已保存到: {config_path}")
    print("💡 可以参考此配置优化现有的Celery设置")

def main():
    """主函数"""
    print("🔧 Redis连接优化工具")
    print("=" * 40)
    print()
    
    # 检查连接状况
    if check_redis_connections():
        print("\n✅ Redis连接正常，但建议应用连接池优化")
    else:
        print("\n❌ Redis连接有问题，需要解决")
    
    # 创建优化配置
    create_optimized_celery_config()
    
    print("\n📋 解决方案总结:")
    print("1️⃣ 立即解决: ./scripts/setup_local_redis.sh")
    print("2️⃣ 优化配置: 参考 docs/optimized_celery_config.py")
    print("3️⃣ 长期方案: 升级Redis Cloud套餐")

if __name__ == "__main__":
    main()
