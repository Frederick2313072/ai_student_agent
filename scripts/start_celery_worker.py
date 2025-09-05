#!/usr/bin/env python3
"""
Celery Worker 启动脚本

这个脚本用于启动费曼学习系统的 Celery Worker 进程。
支持不同的队列配置和worker数量设置。

使用方法:
    python scripts/start_celery_worker.py
    python scripts/start_celery_worker.py --queues memory,knowledge
    python scripts/start_celery_worker.py --workers 4 --loglevel debug
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def main():
    parser = argparse.ArgumentParser(description="启动 Celery Worker")
    parser.add_argument(
        "--workers", 
        type=int, 
        default=2,
        help="Worker进程数量 (默认: 2)"
    )
    parser.add_argument(
        "--queues",
        type=str,
        default="default,memory,knowledge,monitoring",
        help="处理的队列名称，用逗号分隔 (默认: default,memory,knowledge,monitoring)"
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="日志级别 (默认: info)"
    )
    parser.add_argument(
        "--autoscale",
        type=str,
        help="自动扩展配置，格式: max,min (例如: 10,3)"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default="environments/test.env",
        help="环境配置文件路径 (默认: environments/test.env)"
    )
    
    args = parser.parse_args()
    
    # 检查环境文件是否存在
    env_file = project_root / args.env_file
    if not env_file.exists():
        print(f"❌ 环境配置文件不存在: {env_file}")
        print("请确保配置文件存在并包含正确的Redis连接信息")
        sys.exit(1)
    
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", str(project_root / "src"))
    
    # 构建Celery命令
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "feynman.tasks.celery_app.celery_app",
        "worker",
        "--loglevel", args.loglevel,
        "--queues", args.queues,
    ]
    
    # 添加worker配置
    if args.autoscale:
        cmd.extend(["--autoscale", args.autoscale])
    else:
        cmd.extend(["--concurrency", str(args.workers)])
    
    # 添加其他有用的选项
    cmd.extend([
        "--time-limit", "300",        # 任务硬超时5分钟
        "--soft-time-limit", "240",   # 任务软超时4分钟
        "--max-tasks-per-child", "1000",  # 每个worker处理1000任务后重启
    ])
    
    print("🚀 启动 Celery Worker...")
    print(f"📁 项目目录: {project_root}")
    print(f"⚙️  环境文件: {env_file}")
    print(f"📋 处理队列: {args.queues}")
    print(f"👷 Worker数量: {args.workers}")
    print(f"📊 日志级别: {args.loglevel}")
    print(f"🔨 执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # 启动Celery Worker
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n👋 Celery Worker 已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ Celery Worker 启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Celery 未安装或不在PATH中")
        print("请运行: uv add celery")
        sys.exit(1)


if __name__ == "__main__":
    main()


