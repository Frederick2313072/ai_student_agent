#!/bin/bash
"""
Celery Worker 简单启动脚本
"""

# 设置项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动 Celery Worker..."
echo "📁 项目目录: $PROJECT_ROOT"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 启动Celery Worker
uv run celery -A feynman.tasks.celery_app.celery_app worker \
    --loglevel=info \
    --queues=default,memory,knowledge,monitoring \
    --concurrency=2 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --max-tasks-per-child=1000


