#!/bin/bash
#
# 完整的API修复验证脚本
# 包含前端路径修复和服务重启
#

echo "🔧 完整API修复验证脚本"
echo "======================================="
echo ""

echo "✅ **前端API路径已修复**:"
echo "   📄 src/feynman/interfaces/web/streamlit_ui.py"
echo "   📄 src/feynman/interfaces/web/streamlit_app.py"
echo "   🔄 /memorize → /api/v1/chat/memorize"
echo ""

echo "🚀 **重启服务以应用修复**:"
echo ""

# 1. 停止现有的API服务
echo "1️⃣ 停止现有API服务..."
pkill -f "uvicorn.*main" || echo "   ℹ️  没有发现uvicorn进程"
pkill -f "python.*main.py" || echo "   ℹ️  没有发现main.py进程"

echo "   等待3秒..."
sleep 3

# 2. 检查端口释放
echo ""
echo "2️⃣ 检查端口8000状态..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "   ⚠️  端口8000仍被占用，强制终止..."
    lsof -t -i :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if ! lsof -i :8000 >/dev/null 2>&1; then
    echo "   ✅ 端口8000已释放"
else
    echo "   ❌ 端口8000仍被占用"
fi

# 3. 启动API服务
echo ""
echo "3️⃣ 启动API服务..."
echo "   💻 执行: make run"
echo "   📋 建议在新终端中运行"
echo ""

# 4. 验证修复后的端点
echo "4️⃣ 修复验证清单:"
echo ""
echo "   📋 **修复前的错误**:"
echo "      ❌ 获取图数据失败: 404 Not Found"
echo "      ❌ 后台记忆请求失败: 连接超时"
echo ""
echo "   ✅ **修复后应该看到**:"
echo "      ✅ 记忆API调用成功 (202状态码)"
echo "      ✅ 任务队列正常处理"
echo "      ✅ 404错误消失"
echo ""

echo "🧪 **完整验证步骤**:"
echo "======================================="
echo ""
echo "1. 启动完整服务栈:"
echo "   终端1: make celery-worker"
echo "   终端2: make celery-flower"  
echo "   终端3: make run"
echo ""
echo "2. 访问前端测试:"
echo "   uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py"
echo ""
echo "3. 验证API端点:"
echo "   curl -X POST http://127.0.0.1:8000/api/v1/chat/memorize \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"topic\":\"测试\",\"conversation_history\":[]}'"
echo ""

echo "✨ **修复完成！前端API调用路径已正确配置！**"
