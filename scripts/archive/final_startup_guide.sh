#!/bin/bash
#
# 完整系统启动指南
# 解决所有Redis、依赖和API问题后的最终验证
#

echo "🚀 费曼学习系统 - 完整启动指南"
echo "=========================================="
echo ""

# 1. 系统状态检查
echo "1️⃣ 系统状态检查..."
echo ""

# 检查Redis状态
echo "🔍 检查Redis状态:"
if pgrep redis-server > /dev/null; then
    echo "   ✅ Redis服务运行中"
else
    echo "   ❌ Redis服务未启动"
    echo "   🚀 启动Redis: brew services start redis"
    if command -v brew &> /dev/null; then
        echo "   正在启动Redis..."
        brew services start redis
    fi
fi

# 检查Redis连接
echo ""
echo "🔍 检查Redis连接:"
if redis-cli ping &> /dev/null; then
    echo "   ✅ Redis连接正常"
else
    echo "   ❌ Redis连接失败"
fi

# 检查环境配置
echo ""
echo "🔍 检查环境配置:"
if [ -f "environments/test.env" ]; then
    REDIS_URL=$(grep "REDIS_URL=" environments/test.env | cut -d'=' -f2)
    if [[ "$REDIS_URL" == *"localhost:6379"* ]]; then
        echo "   ✅ 已配置本地Redis: $REDIS_URL"
    else
        echo "   ⚠️ Redis配置: $REDIS_URL"
    fi
else
    echo "   ❌ 环境配置文件缺失"
fi

echo ""
echo "=========================================="
echo "2️⃣ 启动服务步骤"
echo "=========================================="
echo ""

echo "📋 **请按顺序在不同终端窗口执行以下命令**:"
echo ""

echo "🏠 **终端1 - API服务 (主服务)**:"
echo "   make run"
echo "   # 或者: uv run python src/main.py"
echo ""

echo "👷 **终端2 - Celery Worker (后台任务)**:"
echo "   make celery-worker"
echo "   # 或者: uv run python scripts/start_celery_worker.py"
echo ""

echo "🌸 **终端3 - Flower监控 (可选)**:"
echo "   ./scripts/manage_flower.sh start"
echo "   # 访问: http://127.0.0.1:5555"
echo ""

echo "🖥️  **终端4 - Streamlit前端 (用户界面)**:"
echo "   uv run streamlit run src/feynman/interfaces/web/streamlit_ui.py"
echo "   # 访问: http://localhost:8501"
echo ""

echo "=========================================="
echo "3️⃣ 验证功能"
echo "=========================================="
echo ""

echo "🧪 **测试检查清单**:"
echo ""

echo "✅ **API服务测试**:"
echo "   curl http://127.0.0.1:8000/health"
echo "   # 应该返回: {\"status\":\"healthy\"}"
echo ""

echo "✅ **Celery任务测试**:"
echo "   uv run python scripts/test_celery_ultra_clean.sh"
echo "   # 应该看到任务提交和完成"
echo ""

echo "✅ **前端功能测试**:"
echo "   1. 打开 http://localhost:8501"
echo "   2. 测试对话功能"
echo "   3. 检查记忆功能不再报错"
echo "   4. 测试知识图谱功能"
echo ""

echo "=========================================="
echo "4️⃣ 预期结果"
echo "=========================================="
echo ""

echo "🚫 **不应再看到这些错误**:"
echo "   🚫 'max number of clients reached' (Redis连接)"
echo "   🚫 'Could not import zhipuai' (依赖缺失)" 
echo "   🚫 '后台记忆请求失败: 连接超时' (任务队列)"
echo "   🚫 '获取图数据失败: 404 Not Found' (API路径)"
echo "   🚫 'LangFuse初始化失败' (监控错误)"
echo ""

echo "✅ **应该看到这些成功**:"
echo "   ✅ API服务正常启动 (端口8000)"
echo "   ✅ Celery Worker正常运行"
echo "   ✅ Streamlit界面正常加载"
echo "   ✅ 对话功能正常工作"
echo "   ✅ 记忆功能正常保存"
echo "   ✅ 知识图谱功能可用"
echo ""

echo "=========================================="
echo "🆘 故障排除"
echo "=========================================="
echo ""

echo "如果遇到问题，可以使用以下工具:"
echo "   📄 ./scripts/fix_database_issues.sh - 数据库问题"
echo "   📄 ./scripts/manage_flower.sh status - Flower状态"
echo "   📄 ./scripts/optimize_redis_connections.py - Redis优化"
echo ""

echo "🔄 **恢复Redis Cloud配置**:"
echo "   cp environments/test.env.backup environments/test.env"
echo "   # 然后重启所有服务"
echo ""

echo "🎉 **系统启动指南完成！**"
echo "现在按照步骤启动各个服务，验证所有功能正常工作。"
