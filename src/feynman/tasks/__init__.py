"""
费曼学习系统任务队列模块

这个包包含了系统中所有的异步任务处理功能：
- Celery应用配置
- 记忆固化任务  
- 知识图谱构建任务
- 监控和成本追踪任务

使用方式:
    from feynman.tasks.celery_app import celery_app
    from feynman.tasks.memory import summarize_conversation_task
"""

from .celery_app import celery_app

__all__ = ["celery_app"]
