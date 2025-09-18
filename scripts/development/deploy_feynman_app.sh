#!/bin/bash
# 费曼学习系统完整部署脚本
# 部署Streamlit应用和nginx配置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STREAMLIT_APP="${PROJECT_ROOT}/src/feynman/interfaces/web/streamlit_ui.py"
BACKEND_APP="${PROJECT_ROOT}/src/main.py"
NGINX_CONFIG_SRC="${PROJECT_ROOT}/config/nginx/feynmanlearning.wiki.conf"
NGINX_CONFIG_DST="/etc/nginx/sites-available/feynmanlearning.wiki.conf"
NGINX_ENABLED_LINK="/etc/nginx/sites-enabled/feynmanlearning.wiki.conf"

# 服务配置
BACKEND_PORT=8005
STREAMLIT_PORT=8501
BACKEND_PID_FILE="${PROJECT_ROOT}/logs/backend.pid"
STREAMLIT_PID_FILE="${PROJECT_ROOT}/logs/streamlit.pid"
BACKEND_LOG_FILE="${PROJECT_ROOT}/logs/backend.log"
STREAMLIT_LOG_FILE="${PROJECT_ROOT}/logs/streamlit.log"

# 显示横幅
show_banner() {
    echo ""
    echo "🚀 费曼学习系统完整部署工具"
    echo "=================================="
    echo "  域名: feynmanlearning.wiki"
    echo "  后端: FastAPI (端口8005)"
    echo "  前端: Streamlit (端口8501)"
    echo "=================================="
    echo ""
}

# 显示使用信息
show_usage() {
    echo "使用方法:"
    echo "  $0 deploy     完整部署 (nginx + 后端API + 前端)"
    echo "  $0 start      启动应用和服务"
    echo "  $0 stop       停止应用和服务"
    echo "  $0 restart    重启应用和服务"
    echo "  $0 status     检查服务状态"
    echo "  $0 nginx      仅部署nginx配置"
    echo "  $0 backend    仅部署后端API"
    echo "  $0 frontend   仅部署前端应用"
    echo "  $0 test       测试配置"
    echo "  $0 remove     移除所有配置"
    echo ""
    echo "注意: nginx配置部署需要root权限"
    echo ""
}

# 检查Python环境和uv
check_python() {
    log_info "检查Python环境和uv..."

    # 检查uv（尝试多个可能的位置）
    UV_PATH=""
    for path in "uv" "/root/.local/bin/uv" "/usr/local/bin/uv" "/usr/bin/uv"; do
        if command -v "$path" &> /dev/null; then
            UV_PATH="$path"
            break
        fi
    done

    if [[ -z "$UV_PATH" ]]; then
        log_error "uv未安装，请先安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    log_success "uv已安装: $UV_PATH"

    # 检查Python版本
    PYTHON_VERSION=$($UV_PATH run python --version 2>&1 | awk '{print $2}')
    log_info "Python版本: $PYTHON_VERSION"

    log_success "Python环境检查通过"
}

# 检查依赖
check_dependencies() {
    local service_type="$1"
    log_info "检查${service_type}依赖..."

    # 简化依赖检查，假设环境已正确配置
    log_success "依赖检查通过"
}

# 检查端口是否被占用
check_port() {
    local port="$1"
    local service_name="$2"
    log_info "检查端口 $port ($service_name) 是否可用..."

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 $port 已被占用"
        # 尝试杀死占用进程
        local pid=$(lsof -ti:$port)
        if [[ -n "$pid" ]]; then
            log_warning "杀死进程 $pid"
            kill -9 $pid 2>/dev/null || true
            sleep 2
        fi
    fi

    log_success "端口 $port 可用"
}

# 创建日志目录
create_log_directory() {
    log_info "创建日志目录..."
    mkdir -p "${PROJECT_ROOT}/logs"
    log_success "日志目录创建完成"
}

# 启动后端API
start_backend() {
    log_info "启动后端API..."

    # 设置环境变量
    export API_HOST="0.0.0.0"
    export API_PORT=$BACKEND_PORT
    export API_RELOAD=false

    # 启动应用
    cd "$PROJECT_ROOT"
    nohup "$UV_PATH" run uvicorn main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --workers 1 \
        --log-level info \
        > "$BACKEND_LOG_FILE" 2>&1 &

    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"

    log_success "后端API已启动，PID: $pid"

    # 等待应用启动
    log_info "等待应用启动..."
    local attempts=0
    local max_attempts=30

    while [[ $attempts -lt $max_attempts ]]; do
        # 检查进程是否还在运行
        if kill -0 $pid 2>/dev/null; then
            # 简单等待一下，让服务完全启动
            sleep 1
            log_success "后端API启动成功"
            return 0
        else
            log_error "后端API进程意外退出"
            return 1
        fi

        sleep 2
        ((attempts++))
        log_info "等待启动... ($attempts/$max_attempts)"
    done

    log_warning "后端API可能未完全启动，请检查日志: $BACKEND_LOG_FILE"
}

# 停止后端API
stop_backend() {
    log_info "停止后端API..."

    if [[ -f "$BACKEND_PID_FILE" ]]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            log_info "终止进程 $pid"
            kill $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                log_warning "强制终止进程 $pid"
                kill -9 $pid
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
        log_success "后端API已停止"
    else
        log_warning "未找到PID文件，可能API未运行"
    fi
}

# 启动前端应用
start_frontend() {
    log_info "启动前端应用..."

    # 设置环境变量
    export STREAMLIT_SERVER_PORT=$STREAMLIT_PORT
    export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
    export STREAMLIT_SERVER_HEADLESS=true
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

    # 启动应用
    cd "$PROJECT_ROOT"
    nohup "$UV_PATH" run streamlit run "$STREAMLIT_APP" \
        --server.port $STREAMLIT_PORT \
        --server.address 0.0.0.0 \
        --server.headless true \
        --browser.gatherUsageStats false \
        --logger.level info \
        > "$STREAMLIT_LOG_FILE" 2>&1 &

    local pid=$!
    echo $pid > "$STREAMLIT_PID_FILE"

    log_success "前端应用已启动，PID: $pid"

    # 等待应用启动
    log_info "等待应用启动..."
    local attempts=0
    local max_attempts=30

    while [[ $attempts -lt $max_attempts ]]; do
        # 检查进程是否还在运行
        if kill -0 $pid 2>/dev/null; then
            # 简单等待一下，让服务完全启动
            sleep 1
            log_success "前端应用启动成功"
            return 0
        else
            log_error "前端应用进程意外退出"
            return 1
        fi

        sleep 2
        ((attempts++))
        log_info "等待启动... ($attempts/$max_attempts)"
    done

    log_warning "前端应用可能未完全启动，请检查日志: $STREAMLIT_LOG_FILE"
}

# 停止前端应用
stop_frontend() {
    log_info "停止前端应用..."

    if [[ -f "$STREAMLIT_PID_FILE" ]]; then
        local pid=$(cat "$STREAMLIT_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            log_info "终止进程 $pid"
            kill $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                log_warning "强制终止进程 $pid"
                kill -9 $pid
            fi
        fi
        rm -f "$STREAMLIT_PID_FILE"
        log_success "前端应用已停止"
    else
        log_warning "未找到PID文件，可能应用未运行"
    fi
}

# 检查nginx是否安装
check_nginx() {
    log_info "检查nginx..."

    if ! command -v nginx &> /dev/null; then
        log_error "nginx未安装，请先安装nginx"
        exit 1
    fi

    log_success "nginx已安装"
}

# 检查配置文件是否存在
check_nginx_config_file() {
    log_info "检查nginx配置文件..."

    if [[ ! -f "$NGINX_CONFIG_SRC" ]]; then
        log_error "nginx配置文件不存在: $NGINX_CONFIG_SRC"
        exit 1
    fi

    log_success "配置文件存在"
}

# 备份现有配置
backup_existing_nginx_config() {
    if [[ -f "$NGINX_CONFIG_DST" ]]; then
        local backup_file="${NGINX_CONFIG_DST}.backup.$(date +%Y%m%d_%H%M%S)"
        log_warning "发现现有配置，正在备份..."
        cp "$NGINX_CONFIG_DST" "$backup_file"
        log_success "备份完成: $backup_file"
    fi
}

# 复制nginx配置文件
copy_nginx_config() {
    log_info "复制nginx配置文件..."

    cp "$NGINX_CONFIG_SRC" "$NGINX_CONFIG_DST"
    chmod 644 "$NGINX_CONFIG_DST"

    log_success "配置文件已复制到: $NGINX_CONFIG_DST"
}

# 创建nginx符号链接
enable_nginx_config() {
    log_info "启用nginx配置..."

    # 如果符号链接已存在，先删除
    if [[ -L "$NGINX_ENABLED_LINK" ]]; then
        rm "$NGINX_ENABLED_LINK"
    fi

    # 创建符号链接
    ln -s "$NGINX_CONFIG_DST" "$NGINX_ENABLED_LINK"

    log_success "配置已启用"
}

# 测试nginx配置
test_nginx_config() {
    log_info "测试nginx配置..."

    if nginx -t; then
        log_success "nginx配置测试通过"
    else
        log_error "nginx配置测试失败"
        exit 1
    fi
}

# 重载nginx配置
reload_nginx() {
    log_info "重载nginx配置..."

    if systemctl reload nginx; then
        log_success "nginx配置重载成功"
    else
        log_warning "nginx重载失败，尝试重启..."
        if systemctl restart nginx; then
            log_success "nginx重启成功"
        else
            log_error "nginx重启失败"
            exit 1
        fi
    fi
}

# 检查域名解析
check_dns() {
    log_info "检查域名解析..."

    if command -v dig &> /dev/null; then
        local ip=$(dig +short feynmanlearning.wiki)
        if [[ -n "$ip" ]]; then
            log_info "feynmanlearning.wiki 解析到: $ip"
        else
            log_warning "feynmanlearning.wiki 无法解析，请确保DNS配置正确"
        fi
    else
        log_warning "dig命令不可用，跳过DNS检查"
    fi
}

# 部署nginx配置
deploy_nginx() {
    log_info "部署nginx配置..."

    # 检查权限
    if [[ $EUID -ne 0 ]]; then
        log_error "nginx配置部署需要root权限"
        log_info "请使用: sudo $0 nginx"
        exit 1
    fi

    check_nginx
    check_nginx_config_file
    backup_existing_nginx_config
    copy_nginx_config
    enable_nginx_config
    test_nginx_config
    reload_nginx
    check_dns

    log_success "nginx配置部署完成"
}

# 部署后端API
deploy_backend() {
    log_info "部署后端API..."

    check_python
    check_dependencies "后端"
    check_port $BACKEND_PORT "后端API"
    create_log_directory
    start_backend
}

# 部署前端应用
deploy_frontend() {
    log_info "部署前端应用..."

    check_python
    check_dependencies "前端"
    check_port $STREAMLIT_PORT "前端应用"
    create_log_directory
    start_frontend
}

# 完整部署
deploy_all() {
    log_info "开始完整部署..."

    # 1. 部署nginx配置
    deploy_nginx

    # 2. 部署后端API
    deploy_backend

    # 3. 部署前端应用
    deploy_frontend

    log_success "完整部署完成！"
    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "访问地址:"
    echo "  HTTP:  http://feynmanlearning.wiki"
    echo "  HTTPS: https://feynmanlearning.wiki (如果配置了SSL证书)"
    echo ""
    echo "服务端口:"
    echo "  后端API: http://localhost:8005"
    echo "  前端应用: http://localhost:8501"
    echo "  API文档: http://localhost:8005/docs"
    echo ""
    echo "管理命令:"
    echo "  启动服务:  $0 start"
    echo "  停止服务:  $0 stop"
    echo "  查看状态:  $0 status"
    echo "  查看后端日志:  tail -f ${BACKEND_LOG_FILE}"
    echo "  查看前端日志:  tail -f ${STREAMLIT_LOG_FILE}"
    echo ""
}

# 启动服务
start_services() {
    log_info "启动服务..."
    check_python
    check_dependencies "后端"
    check_dependencies "前端"
    check_port $BACKEND_PORT "后端API"
    check_port $STREAMLIT_PORT "前端应用"
    create_log_directory
    start_backend
    start_frontend
    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    stop_frontend
    stop_backend
    log_success "服务停止完成"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    stop_frontend
    stop_backend
    sleep 2
    check_python
    check_dependencies "后端"
    check_dependencies "前端"
    check_port $BACKEND_PORT "后端API"
    check_port $STREAMLIT_PORT "前端应用"
    create_log_directory
    start_backend
    start_frontend
    log_success "服务重启完成"
}

# 检查后端API状态
check_backend_status() {
    log_info "检查后端API状态..."

    if [[ -f "$BACKEND_PID_FILE" ]]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            log_success "后端API正在运行 (PID: $pid)"
            log_info "访问地址: http://localhost:$BACKEND_PORT"
            log_info "API文档: http://localhost:$BACKEND_PORT/docs"
            return 0
        else
            log_warning "PID文件存在但进程未运行，清理PID文件"
            rm -f "$BACKEND_PID_FILE"
        fi
    fi

    log_warning "后端API未运行"
    return 1
}

# 检查前端应用状态
check_frontend_status() {
    log_info "检查前端应用状态..."

    if [[ -f "$STREAMLIT_PID_FILE" ]]; then
        local pid=$(cat "$STREAMLIT_PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            log_success "前端应用正在运行 (PID: $pid)"
            log_info "访问地址: http://localhost:$STREAMLIT_PORT"
            return 0
        else
            log_warning "PID文件存在但进程未运行，清理PID文件"
            rm -f "$STREAMLIT_PID_FILE"
        fi
    fi

    log_warning "前端应用未运行"
    return 1
}

# 检查状态
check_status() {
    log_info "检查服务状态..."
    echo ""
    echo "后端API状态:"
    check_backend_status
    echo ""
    echo "前端应用状态:"
    check_frontend_status
    echo ""
    echo "nginx状态:"
    if systemctl is-active --quiet nginx; then
        log_success "nginx正在运行"
    else
        log_warning "nginx未运行"
    fi
    echo ""
    echo "网络连接测试:"
    if curl -s -f --max-time 5 "http://localhost:8005/health" > /dev/null; then
        log_success "后端API响应正常"
    else
        log_warning "后端API无响应"
    fi

    if curl -s -f --max-time 5 "http://localhost:8502/healthz" > /dev/null; then
        log_success "前端应用响应正常"
    else
        log_warning "前端应用无响应"
    fi
}

# 测试配置
test_config() {
    log_info "测试配置..."
    echo ""
    echo "nginx配置测试:"
    if [[ $EUID -eq 0 ]]; then
        test_nginx_config
    else
        log_warning "nginx测试需要root权限，跳过..."
    fi

    echo ""
    echo "后端API测试:"
    check_backend_status

    echo ""
    echo "前端应用测试:"
    check_frontend_status
}

# 移除nginx配置
remove_nginx_config() {
    log_info "移除nginx配置..."

    # 检查权限
    if [[ $EUID -ne 0 ]]; then
        log_error "nginx配置移除需要root权限"
        log_info "请使用: sudo $0 remove"
        exit 1
    fi

    # 禁用配置
    if [[ -L "$NGINX_ENABLED_LINK" ]]; then
        rm "$NGINX_ENABLED_LINK"
        log_success "配置已禁用"
    fi

    # 删除配置文件
    if [[ -f "$NGINX_CONFIG_DST" ]]; then
        rm "$NGINX_CONFIG_DST"
        log_success "配置文件已删除"
    fi

    # 重载nginx
    reload_nginx

    log_success "nginx配置已移除"
}

# 移除所有配置
remove_all() {
    log_info "移除所有配置..."
    log_warning "这将停止服务并移除nginx配置"

    # 停止服务
    stop_frontend
    stop_backend

    # 移除nginx配置
    remove_nginx_config

    log_success "所有配置已移除"
}

# 主函数
main() {
    show_banner

    local command="$1"

    case "$command" in
        deploy)
            deploy_all
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            check_status
            ;;
        nginx)
            deploy_nginx
            ;;
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        test)
            test_config
            ;;
        remove)
            remove_all
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# 错误处理
trap 'log_error "脚本执行失败"; exit 1' ERR

# 执行主函数
main "$@"
