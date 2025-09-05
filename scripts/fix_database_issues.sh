#!/bin/bash
#
# 数据库问题修复脚本
# 解决Redis连接超限、API端点错误等问题
#

echo "🔧 数据库问题修复脚本"
echo "================================="
echo ""

# 1. 停止所有服务释放Redis连接
echo "1️⃣ 停止所有服务以释放Redis连接..."
echo ""

# 停止Flower
echo "🌸 停止Flower监控面板..."
./scripts/manage_flower.sh stop

# 停止可能的Worker进程
echo "👷 停止Celery Worker..."
pkill -f "celery.*worker" || echo "   ℹ️  没有发现Worker进程"

# 停止API服务
echo "🌐 停止API服务..."
pkill -f "uvicorn.*main" || echo "   ℹ️  没有发现API服务进程"
pkill -f "python.*main.py" || echo "   ℹ️  没有发现main.py进程"

echo ""
echo "✅ 服务停止完成，等待3秒..."
sleep 3

# 2. 验证Redis连接恢复
echo ""
echo "2️⃣ 验证Redis连接状态..."
uv run python -c "
import sys, os, redis
from dotenv import load_dotenv
sys.path.insert(0, 'src')
load_dotenv('environments/test.env')
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('   ✅ Redis连接已恢复正常')
except Exception as e:
    print(f'   ❌ Redis仍有问题: {e}')
    print('   💡 可能需要等待更长时间或联系Redis Cloud支持')
"

# 3. 创建必要的目录
echo ""
echo "3️⃣ 创建必要的数据目录..."
mkdir -p data/chroma
mkdir -p logs
echo "   ✅ ChromaDB数据目录已创建"

# 4. 检查并安装缺失依赖
echo ""
echo "4️⃣ 检查依赖模块..."
echo "   📦 检查supabase模块..."
uv run python -c "import supabase; print('   ✅ supabase模块已安装')" 2>/dev/null || {
    echo "   ⚠️  supabase模块缺失"
    echo "   💻 建议执行: uv add supabase"
}

# 5. 重新启动服务
echo ""
echo "5️⃣ 重新启动服务..."
echo ""

echo "🌸 启动Flower监控面板..."
./scripts/manage_flower.sh start &
FLOWER_PID=$!

echo "   等待Flower启动..."
sleep 3

echo ""
echo "🎉 修复完成！"
echo "================================="
echo ""
echo "📋 **下一步操作**:"
echo "   1. 新开终端启动Worker: make celery-worker"
echo "   2. 新开终端启动API: make run"
echo "   3. 访问监控面板: http://127.0.0.1:5555"
echo ""
echo "⚠️  **重要提醒**:"
echo "   📋 修复前端API调用路径:"
echo "   ❌ /api/v1/chat/memory → ✅ /api/v1/chat/memorize"
echo ""
echo "💡 如果问题仍然存在，请检查Redis Cloud的连接限制设置"
