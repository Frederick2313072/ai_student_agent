"""
基于 asyncio 的异步任务队列实现

提供轻量级的任务队列功能，支持：
- 任务优先级
- 失败重试
- 状态追踪
- 并发控制
"""

import asyncio
import uuid
import time
from enum import Enum
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class Task:
    """任务数据结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Callable = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # 数字越大优先级越高
    max_retries: int = 3
    retry_count: int = 0
    timeout: Optional[float] = None  # 任务超时时间（秒）
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "timeout": self.timeout,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error
        }

class AsyncTaskQueue:
    """异步任务队列管理器"""
    
    def __init__(self, max_workers: int = 5, queue_size: int = 1000):
        """
        初始化任务队列
        
        Args:
            max_workers: 最大工作线程数
            queue_size: 队列最大大小
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.task_queue = asyncio.PriorityQueue(maxsize=queue_size)
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.semaphore = asyncio.Semaphore(max_workers)
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "pending_tasks": 0
        }
        
    async def start(self):
        """启动任务队列处理器"""
        if self.running:
            return
            
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        logger.info(f"任务队列已启动，工作线程数: {self.max_workers}")
        
    async def stop(self, graceful: bool = True):
        """
        停止任务队列处理器
        
        Args:
            graceful: 是否优雅停止（等待正在执行的任务完成）
        """
        self.running = False
        
        if graceful:
            # 等待正在执行的任务完成
            pending_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.RUNNING]
            if pending_tasks:
                logger.info(f"等待 {len(pending_tasks)} 个任务完成...")
                await asyncio.sleep(1)  # 给任务一些时间完成
        
        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()
            
        # 等待工作线程结束
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("任务队列已停止")
        
    async def add_task(
        self, 
        func: Callable,
        *args,
        name: str = "",
        priority: int = 0,
        max_retries: int = 3,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        添加任务到队列
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            name: 任务名称
            priority: 优先级（数字越大优先级越高）
            max_retries: 最大重试次数
            timeout: 任务超时时间（秒）
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        if not self.running:
            raise RuntimeError("任务队列未启动")
            
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        self.tasks[task.id] = task
        self.stats["total_tasks"] += 1
        self.stats["pending_tasks"] += 1
        
        # 优先级队列：负值使高优先级任务先执行
        # 使用创建时间作为第二排序条件，确保相同优先级的任务按FIFO顺序处理
        await self.task_queue.put((-task.priority, task.created_at.timestamp(), task.id))
        
        logger.debug(f"任务已添加到队列: {task.name}[{task.id}], 优先级: {task.priority}")
        return task.id
        
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self.tasks.get(task_id)
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        # 更新当前状态统计
        self.stats["pending_tasks"] = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        self.stats["running_tasks"] = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        
        return {
            **self.stats,
            "queue_size": self.task_queue.qsize(),
            "max_workers": self.max_workers,
            "active_workers": len([w for w in self.workers if not w.done()]),
            "total_managed_tasks": len(self.tasks)
        }
        
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的任务列表"""
        recent_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )[:limit]
        
        return [task.to_dict() for task in recent_tasks]
        
    async def _worker(self, worker_name: str):
        """工作线程处理任务"""
        logger.info(f"工作线程 {worker_name} 已启动")
        
        while self.running:
            try:
                # 从队列获取任务，设置超时避免阻塞
                try:
                    _, _, task_id = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                    
                task = self.tasks.get(task_id)
                if not task:
                    continue
                    
                # 使用信号量控制并发
                async with self.semaphore:
                    await self._execute_task(task, worker_name)
                    
            except asyncio.CancelledError:
                logger.info(f"工作线程 {worker_name} 被取消")
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 异常: {e}")
                
    async def _execute_task(self, task: Task, worker_name: str):
        """执行单个任务"""
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.stats["pending_tasks"] -= 1
            self.stats["running_tasks"] += 1
            
            logger.info(f"[{worker_name}] 开始执行任务 {task.name}[{task.id}]")
            
            # 执行任务（支持超时）
            if task.timeout:
                if asyncio.iscoroutinefunction(task.func):
                    result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, task.func, *task.args
                        ),
                        timeout=task.timeout
                    )
            else:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, task.func, *task.args
                    )
                
            # 任务成功
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            self.stats["completed_tasks"] += 1
            self.stats["running_tasks"] -= 1
            
            execution_time = (task.completed_at - task.started_at).total_seconds()
            logger.info(f"[{worker_name}] 任务 {task.name}[{task.id}] 执行成功，耗时: {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            # 任务超时
            task.error = f"任务超时 ({task.timeout}s)"
            await self._handle_task_failure(task, worker_name)
            
        except Exception as e:
            # 任务异常
            task.error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"[{worker_name}] 任务 {task.name}[{task.id}] 执行异常: {task.error}")
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            
            await self._handle_task_failure(task, worker_name)
            
    async def _handle_task_failure(self, task: Task, worker_name: str):
        """处理任务失败"""
        if task.retry_count < task.max_retries:
            # 重试任务
            task.retry_count += 1
            task.status = TaskStatus.RETRY
            
            # 计算退避延迟（指数退避）
            delay = min(2 ** task.retry_count, 60)  # 最大延迟60秒
            
            logger.info(f"[{worker_name}] 任务 {task.name}[{task.id}] 将在 {delay}s 后重试 ({task.retry_count}/{task.max_retries})")
            
            # 延迟后重新加入队列
            asyncio.create_task(self._schedule_retry(task, delay))
        else:
            # 重试次数耗尽
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.stats["failed_tasks"] += 1
            self.stats["running_tasks"] -= 1
            
            logger.error(f"[{worker_name}] 任务 {task.name}[{task.id}] 最终失败: {task.error}")
            
    async def _schedule_retry(self, task: Task, delay: float):
        """调度任务重试"""
        await asyncio.sleep(delay)
        
        if self.running:  # 确保队列仍在运行
            await self.task_queue.put((-task.priority, time.time(), task.id))
            logger.debug(f"任务 {task.name}[{task.id}] 已重新加入队列")

# 全局任务队列实例
task_queue_manager = AsyncTaskQueue(max_workers=5)
