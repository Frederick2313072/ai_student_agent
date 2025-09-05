#!/bin/bash
#
# 本地Redis设置脚本 - 解决Redis Cloud连接数超限问题
# 临时切换到本地Redis进行测试
#

echo "🔧 本地Redis设置脚本"
echo "=================================="
echo ""

# 1. 检查是否已安装Redis
echo "1️⃣ 检查Redis安装状态..."
if command -v redis-server &> /dev/null; then
    echo "   ✅ Redis已安装"
    redis-server --version
else
    echo "   ❌ Redis未安装"
    echo "   💻 安装命令 (Mac): brew install redis"
    echo "   💻 安装命令 (Ubuntu): sudo apt-get install redis-server"
    echo ""
    echo "请先安装Redis后再运行此脚本"
    exit 1
fi

# 2. 启动本地Redis服务
echo ""
echo "2️⃣ 启动本地Redis服务..."
if pgrep redis-server > /dev/null; then
    echo "   ✅ Redis服务已在运行"
else
    echo "   🚀 启动Redis服务..."
    if command -v brew &> /dev/null; then
        # Mac使用brew services
        brew services start redis
        echo "   ✅ Redis服务已启动 (brew services)"
    else
        # Linux直接启动
        redis-server --daemonize yes
        echo "   ✅ Redis服务已启动 (daemon)"
    fi
fi

# 3. 测试本地Redis连接
echo ""
echo "3️⃣ 测试本地Redis连接..."
if redis-cli ping | grep -q PONG; then
    echo "   ✅ 本地Redis连接正常"
else
    echo "   ❌ 本地Redis连接失败"
    exit 1
fi

# 4. 备份当前环境配置
echo ""
echo "4️⃣ 备份环境配置..."
cp environments/test.env environments/test.env.backup
echo "   ✅ 已备份为 test.env.backup"

# 5. 修改为本地Redis配置
echo ""
echo "5️⃣ 切换到本地Redis配置..."
cat > environments/test.env.local << 'EOF'
# 本地Redis测试配置
# 从 test.env.backup 复制的基础配置

# ======================
# 基础配置
# ======================
ENVIRONMENT=development
DEBUG=true

# ======================
# API 服务配置
# ======================
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# ======================
# OpenAI 配置
# ======================
EOF

# 复制原始配置但替换Redis设置
grep -v "REDIS_URL\|REDIS_PASSWORD" environments/test.env.backup >> environments/test.env.local

# 添加本地Redis配置
cat >> environments/test.env.local << 'EOF'

# ======================
# 本地Redis配置 (临时测试)
# ======================
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0
EOF

# 替换环境配置文件
cp environments/test.env.local environments/test.env
echo "   ✅ 已切换到本地Redis配置"

# 6. 验证配置
echo ""
echo "6️⃣ 验证新配置..."
uv run python -c "
import sys, os, redis
from dotenv import load_dotenv
sys.path.insert(0, 'src')
load_dotenv('environments/test.env')
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('   ✅ 本地Redis配置验证成功')
except Exception as e:
    print(f'   ❌ 配置验证失败: {e}')
"

echo ""
echo "🎉 本地Redis设置完成！"
echo "=================================="
echo ""
echo "📋 **重要说明**:"
echo "   ✅ 已切换到本地Redis (无连接数限制)"
echo "   💾 原配置已备份为 test.env.backup"
echo "   🔄 需要重启所有服务以应用新配置"
echo ""
echo "🚀 **下一步操作**:"
echo "   1. 重启服务:"
echo "      ./scripts/manage_flower.sh restart"
echo "      # 重启Worker和API服务"
echo ""
echo "   2. 恢复Redis Cloud配置:"
echo "      cp environments/test.env.backup environments/test.env"
echo ""
echo "⚠️  **注意**: 这是临时测试配置，生产环境请使用Redis Cloud"
