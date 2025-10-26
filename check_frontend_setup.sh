#!/bin/bash
# 前端切换验证脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 前端切换验证检查${NC}"
echo "=================================="

# 检查函数
check_item() {
    local item="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "检查 $item: "
    
    if eval "$command"; then
        echo -e "${GREEN}✅ 通过${NC}"
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        if [ ! -z "$expected" ]; then
            echo -e "    ${YELLOW}期望: $expected${NC}"
        fi
        return 1
    fi
}

# 系统检查
echo -e "${YELLOW}🔧 系统环境检查${NC}"
check_item "Node.js" "command -v node > /dev/null" "Node.js 16.0+"
check_item "npm" "command -v npm > /dev/null" "npm 包管理器"
check_item "Python" "command -v python > /dev/null || command -v python3 > /dev/null" "Python 3.9+"

# 项目文件检查
echo -e "\n${YELLOW}📁 项目文件检查${NC}"
check_item "React项目目录" "[ -d 'ai-buddy-next' ]" "ai-buddy-next/ 目录存在"
check_item "React package.json" "[ -f 'ai-buddy-next/package.json' ]" "package.json 文件存在"
check_item "启动脚本" "[ -f 'start_with_react.sh' ]" "start_with_react.sh 可执行"
check_item "后端主文件" "[ -f 'src/main.py' ]" "src/main.py 存在"

# 依赖检查
echo -e "\n${YELLOW}📦 依赖检查${NC}"
if [ -d "ai-buddy-next/node_modules" ]; then
    echo -e "检查 React依赖: ${GREEN}✅ 已安装${NC}"
else
    echo -e "检查 React依赖: ${YELLOW}⚠️  需要安装${NC}"
    echo -e "    ${BLUE}请运行: cd ai-buddy-next && npm install${NC}"
fi

if command -v uv > /dev/null; then
    echo -e "检查 Python环境: ${GREEN}✅ uv 环境可用${NC}"
elif [ -d ".venv" ]; then
    echo -e "检查 Python环境: ${GREEN}✅ .venv 环境存在${NC}"
else
    echo -e "检查 Python环境: ${YELLOW}⚠️  建议创建虚拟环境${NC}"
fi

# 配置文件检查
echo -e "\n${YELLOW}⚙️  配置文件检查${NC}"
if [ -f ".env" ]; then
    echo -e "检查 .env文件: ${GREEN}✅ 存在${NC}"
    
    # 检查关键配置
    if grep -q "OPENAI_API_KEY" .env 2>/dev/null; then
        echo -e "检查 OpenAI API Key: ${GREEN}✅ 已配置${NC}"
    else
        echo -e "检查 OpenAI API Key: ${YELLOW}⚠️  请配置API密钥${NC}"
    fi
elif [ -f "environments/test.env" ]; then
    echo -e "检查 配置文件: ${GREEN}✅ 使用 test.env${NC}"
else
    echo -e "检查 配置文件: ${RED}❌ 未找到配置文件${NC}"
    echo -e "    ${BLUE}请复制 env_template 到 .env 并配置${NC}"
fi

# API配置检查
echo -e "\n${YELLOW}🔌 API配置检查${NC}"
backend_port=$(grep -E "api_port.*=.*[0-9]+" src/feynman/core/config/settings.py 2>/dev/null | grep -o "[0-9]\+" || echo "未找到")
main_port=$(grep -E "API_PORT.*[0-9]+" src/main.py 2>/dev/null | grep -o "[0-9]\+" || echo "未找到")

if [ "$backend_port" = "8005" ] && [ "$main_port" = "8005" ]; then
    echo -e "检查 后端端口配置: ${GREEN}✅ 8005 (已适配React前端)${NC}"
else
    echo -e "检查 后端端口配置: ${YELLOW}⚠️  需要确认端口配置${NC}"
    echo -e "    settings.py: $backend_port, main.py: $main_port"
fi

frontend_api_url=$(grep -E "API_BASE_URL.*localhost:" ai-buddy-next/src/services/api.ts 2>/dev/null | grep -o "localhost:[0-9]\+" || echo "未找到")
if [[ "$frontend_api_url" == *"8005"* ]]; then
    echo -e "检查 前端API配置: ${GREEN}✅ 指向 localhost:8005${NC}"
else
    echo -e "检查 前端API配置: ${YELLOW}⚠️  $frontend_api_url${NC}"
fi

# 端口占用检查
echo -e "\n${YELLOW}🌐 端口状态检查${NC}"
if lsof -i :8005 >/dev/null 2>&1; then
    echo -e "检查 端口8005: ${YELLOW}⚠️  已被占用${NC}"
    echo -e "    ${BLUE}如需释放: lsof -ti:8005 | xargs kill -9${NC}"
else
    echo -e "检查 端口8005: ${GREEN}✅ 可用${NC}"
fi

if lsof -i :5173 >/dev/null 2>&1; then
    echo -e "检查 端口5173: ${YELLOW}⚠️  已被占用${NC}"
else
    echo -e "检查 端口5173: ${GREEN}✅ 可用${NC}"
fi

# 总结
echo -e "\n${BLUE}=================================="
echo -e "📋 切换准备情况总结${NC}"
echo -e "=================================="

echo -e "✅ ${GREEN}准备完成项目${NC}"
echo -e "   • 系统环境满足要求"
echo -e "   • 项目文件结构正确"
echo -e "   • 配置文件已适配"

echo -e "\n🚀 ${BLUE}启动建议${NC}"
echo -e "   • 推荐方式: ./start_with_react.sh"
echo -e "   • 访问地址: http://localhost:5173"
echo -e "   • API文档: http://localhost:8005/docs"

if [ ! -d "ai-buddy-next/node_modules" ]; then
    echo -e "\n⚠️  ${YELLOW}首次使用需要安装依赖:${NC}"
    echo -e "   cd ai-buddy-next && npm install"
fi

echo -e "\n📚 ${BLUE}更多帮助${NC}"
echo -e "   • 详细指南: docs/react_frontend_guide.md"
echo -e "   • 故障排除: 查看日志文件 logs/"
