"""
Celery 任务队列应用配置

这个模块初始化 Celery 应用，使用 Redis 作为消息代理和结果后端。
支持费曼学习系统的异步任务处理，包括：
- 记忆固化任务
- 知识图谱构建任务
- 成本追踪任务
- 其他后台处理任务
"""

import os
from celery import Celery
from dotenv import load_dotenv

# 加载环境变量 - 优先根目录 .env，兼容旧路径
load_dotenv(".env")
load_dotenv("environments/test.env")

# 获取Redis连接URL - 优先使用环境变量中的Redis Cloud配置
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL环境变量未设置，请检查.env或environments/test.env配置文件")

print(f"🔗 Celery使用Redis: {redis_url[:20]}...{redis_url[-20:]}")

# 创建Celery应用实例
celery_app = Celery(
    "feynman_tasks",
    broker=redis_url,        # 使用Redis作为消息代理
    backend=redis_url        # 使用Redis存储任务结果
)

# Celery配置
celery_app.conf.update(
    # 序列化设置
    task_serializer="json",
    result_serializer="json", 
    accept_content=["json"],
    
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务追踪和超时
    task_track_started=True,
    task_time_limit=300,     # 单任务超时5分钟
    task_soft_time_limit=240, # 软超时4分钟
    
    # 重试设置
    task_acks_late=True,     # 任务执行后才确认
    task_reject_on_worker_lost=True,
    
    # 结果过期时间
    result_expires=3600,     # 1小时后清理结果
    
    # Worker设置
    worker_prefetch_multiplier=1,  # 每次只拉取一个任务
    worker_max_tasks_per_child=1000,  # 每个worker处理1000个任务后重启
    
    # 队列路由设置
    task_routes={
        'feynman.tasks.memory.*': {'queue': 'memory'},
        'feynman.tasks.knowledge.*': {'queue': 'knowledge'},
        'feynman.tasks.monitoring.*': {'queue': 'monitoring'},
    },
    
    # 默认队列
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # 监控设置
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# 任务发现配置 - 自动发现任务模块
celery_app.autodiscover_tasks([
    'feynman.tasks.memory',
    'feynman.tasks.knowledge', 
    'feynman.tasks.monitoring',
])

# 启动事件处理
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置周期性任务"""
    # 可以在这里添加定时任务
    # sender.add_periodic_task(300.0, cleanup_expired_sessions.s(), name='cleanup sessions every 5min')
    pass

# 任务失败处理
@celery_app.task(bind=True)
def debug_task(self):
    """调试任务，用于测试Celery连接"""
    print(f'Request: {self.request!r}')
    return "Debug task completed successfully"

if __name__ == '__main__':
    celery_app.start()
