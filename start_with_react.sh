#!/bin/bash
# AI费曼学习系统 - React前端启动脚本
# 此脚本将启动后端API和React前端

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI费曼学习系统 - React前端启动${NC}"
echo "================================================"

# 检查必要的工具
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 未安装，请先安装 $1${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}📋 检查必要工具...${NC}"
check_command "node"
check_command "npm"

# 检查Python环境
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run"
    echo -e "${GREEN}✅ 使用 uv 环境${NC}"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON_CMD="python"
    echo -e "${GREEN}✅ 使用 .venv 环境${NC}"
else
    PYTHON_CMD="python"
    echo -e "${YELLOW}⚠️  使用系统Python环境${NC}"
fi

# 检查环境变量
if [ ! -f ".env" ] && [ ! -f "environments/test.env" ]; then
    echo -e "${RED}❌ 未找到环境配置文件，请先配置环境变量${NC}"
    echo -e "${YELLOW}提示: 复制 env_template 到 .env 并填入你的API密钥${NC}"
    exit 1
fi

# 安装前端依赖
echo -e "${YELLOW}📦 安装前端依赖...${NC}"
cd ai-buddy-next
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 前端依赖已存在${NC}"
fi
cd ..

# 创建日志目录
mkdir -p logs

# 启动函数
start_backend() {
    echo -e "${YELLOW}🔧 启动后端API服务器 (端口: 8005)...${NC}"
    cd src
    $PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ 后端启动成功 (PID: $BACKEND_PID)${NC}"
    echo -e "${BLUE}📚 API文档: http://localhost:8005/docs${NC}"
}

start_frontend() {
    echo -e "${YELLOW}🎨 启动React前端 (端口: 5173)...${NC}"
    cd ai-buddy-next
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ 前端启动成功 (PID: $FRONTEND_PID)${NC}"
    echo -e "${BLUE}🌐 应用地址: http://localhost:5173${NC}"
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🔄 正在停止服务...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    fi
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 启动服务
start_backend
sleep 3  # 等待后端启动
start_frontend
sleep 3  # 等待前端启动

echo "================================================"
echo -e "${GREEN}🎉 所有服务启动完成！${NC}"
echo -e "${BLUE}📱 前端应用: http://localhost:5173${NC}"
echo -e "${BLUE}📚 API文档: http://localhost:8005/docs${NC}"
echo -e "${BLUE}📋 健康检查: http://localhost:8005/health${NC}"
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo -e "  • 按 Ctrl+C 停止所有服务"
echo -e "  • 日志文件保存在 logs/ 目录"
echo -e "  • 如需单独启动，请查看 docs/deployment_guide.md"
echo "================================================"

# 等待服务运行
wait
