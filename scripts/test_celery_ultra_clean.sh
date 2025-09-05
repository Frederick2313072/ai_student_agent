#!/bin/bash
#
# 超清洁版本的 Celery + Redis 测试脚本
# 通过环境变量在Python启动时就抑制所有警告
#

echo "🧪 超清洁版 Celery + Redis 测试"
echo "======================================="

# 设置Python警告抑制环境变量
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::FutureWarning,ignore::UserWarning"
export LANGFUSE_ENABLED="false"
export OTEL_SDK_DISABLED="true"

echo "🧹 已设置警告抑制环境变量"
echo "   📊 PYTHONWARNINGS: 已配置抑制废弃/未来/用户警告"  
echo "   📈 LANGFUSE_ENABLED: false"
echo "   🔍 OTEL_SDK_DISABLED: true"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 运行测试（使用原始测试脚本）
echo "🚀 启动测试..."
echo ""
uv run python scripts/test_celery.py 2>/dev/null || {
    echo "❌ 测试失败，显示完整输出："
    echo ""
    uv run python scripts/test_celery.py
}

echo ""
echo "✨ 超清洁测试完成！"
