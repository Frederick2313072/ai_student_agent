#!/bin/bash
"""
重启整套服务脚本（后端API、前端Streamlit、Celery Worker、Flower）

用法:
  ./scripts/restart_all.sh            # 重启全部服务
  ./scripts/restart_all.sh stop       # 仅停止
  ./scripts/restart_all.sh start      # 仅启动

说明:
  - 依赖 uv 已安装并在 PATH 中
  - 日志与 PID 文件写入 logs/
"""

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

API_HOST="0.0.0.0"
API_PORT="8005"
STREAMLIT_PORT="8501"

mkdir -p logs

free_port() {
  local port="$1"
  echo "[free_port] ensure port $port is free"
  for _ in 1 2 3 4 5; do
    # 优先 lsof
    local pids=""
    if command -v lsof >/dev/null 2>&1; then
      pids=$(lsof -ti :"$port" 2>/dev/null || true)
    fi
    # 其次 fuser
    if [ -z "$pids" ] && command -v fuser >/dev/null 2>&1; then
      pids=$(fuser -n tcp "$port" 2>/dev/null | tr ' ' '\n' || true)
    fi
    # 兜底 ss
    if [ -z "$pids" ]; then
      pids=$(ss -lntp 2>/dev/null | awk -v p=":$port" '$4 ~ p {print $NF}' | sed 's/.*pid=\([0-9]*\).*/\1/' | sort -u || true)
    fi
    if [ -n "$pids" ]; then
      echo "[free_port] kill pids: $pids"
      kill $pids 2>/dev/null || true
      sleep 1
      for pid in $pids; do kill -9 "$pid" 2>/dev/null || true; done
    fi
    # 检查端口是否已释放
    if ! ss -lntp 2>/dev/null | grep -q ":$port\b"; then
      return 0
    fi
    sleep 1
  done
  return 0
}

stop_backend() {
  echo "[stop] backend (uvicorn)"
  if [ -f logs/backend.pid ]; then
    kill "$(cat logs/backend.pid)" 2>/dev/null || true
    rm -f logs/backend.pid
  fi
  pkill -f "uvicorn main:app" 2>/dev/null || true
  free_port "$API_PORT"
}

start_backend() {
  echo "[start] backend (uvicorn)"
  free_port "$API_PORT"
  nohup uv run uvicorn main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --workers 1 \
    --log-level info \
    > logs/backend.log 2>&1 &
  echo $! > logs/backend.pid
}

stop_frontend() {
  echo "[stop] streamlit"
  if [ -f logs/streamlit.pid ]; then
    kill "$(cat logs/streamlit.pid)" 2>/dev/null || true
    rm -f logs/streamlit.pid
  fi
  pkill -f "streamlit run src/feynman/interfaces/web/streamlit_ui.py" 2>/dev/null || true
  pkill -f "python .*streamlit_ui.py" 2>/dev/null || true
  free_port "$STREAMLIT_PORT"
}

start_frontend() {
  echo "[start] streamlit"
  free_port "$STREAMLIT_PORT"
  nohup uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py \
    --server.port "$STREAMLIT_PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    > logs/streamlit.log 2>&1 &
  echo $! > logs/streamlit.pid
}

stop_celery() {
  echo "[stop] celery worker"
  if [ -f logs/celery_worker.pid ]; then
    kill "$(cat logs/celery_worker.pid)" 2>/dev/null || true
    rm -f logs/celery_worker.pid
  fi
  pkill -f "celery.*feynman.tasks.celery_app.celery_app" 2>/dev/null || true
}

start_celery() {
  echo "[start] celery worker"
  nohup uv run celery -A feynman.tasks.celery_app.celery_app worker \
    --loglevel=info \
    --queues=default,memory,knowledge,monitoring \
    --concurrency=2 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --max-tasks-per-child=1000 \
    > logs/celery_worker.log 2>&1 &
  echo $! > logs/celery_worker.pid
}

stop_flower() {
  echo "[stop] flower"
  if [ -x scripts/archive/manage_flower.sh ]; then
    scripts/archive/manage_flower.sh stop || true
  else
    pkill -f "flower" 2>/dev/null || true
  fi
}

start_flower() {
  echo "[start] flower"
  if [ -x scripts/archive/manage_flower.sh ]; then
    scripts/archive/manage_flower.sh start || true
  else
    nohup uv run python scripts/start_flower.py > logs/flower.log 2>&1 &
  fi
}

stop_all() {
  stop_frontend
  stop_backend
  stop_celery
  stop_flower
}

start_all() {
  start_celery
  start_backend
  start_frontend
  start_flower
}

case "$1" in
  stop)
    stop_all
    ;;
  start)
    start_all
    ;;
  *)
    echo "[restart] stack"
    stop_all
    sleep 2
    start_all
    ;;
esac

echo "✅ done"


