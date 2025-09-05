#!/bin/bash
# 费曼学习系统监控栈启动脚本

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

# 检查Docker和Docker Compose
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服务未启动，请启动Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查配置文件
check_configs() {
    log_info "检查配置文件..."
    
    local configs=(
        "config/prometheus.yml"
        "config/alerting_rules.yml"
        "config/alertmanager.yml"
        "config/blackbox.yml"
        "config/grafana/provisioning/datasources/prometheus.yml"
        "config/grafana/provisioning/dashboards/dashboard.yml"
    )
    
    for config in "${configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            log_error "配置文件不存在: $config"
            exit 1
        fi
    done
    
    log_success "配置文件检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    local dirs=(
        "logs"
        "data/prometheus"
        "data/grafana"
        "data/alertmanager"
        "data/jaeger"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
    
    log_success "目录创建完成"
}

# 启动监控栈
start_monitoring_stack() {
    log_info "启动监控栈..."
    
    # 进入配置目录
    cd config
    
    # 拉取最新镜像
    log_info "拉取Docker镜像..."
    docker-compose -f docker-compose.monitoring.yml pull
    
    # 启动服务
    log_info "启动监控服务..."
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose -f docker-compose.monitoring.yml ps
    
    log_success "监控栈启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local services=(
        "http://localhost:9090/-/healthy|Prometheus"
        "http://localhost:3000/api/health|Grafana"
        "http://localhost:16686/|Jaeger"
        "http://localhost:9093/-/healthy|AlertManager"
        "http://localhost:8000/health|Feynman API"
    )
    
    for service in "${services[@]}"; do
        IFS='|' read -r url name <<< "$service"
        
        if curl -s -f "$url" > /dev/null; then
            log_success "$name 健康检查通过"
        else
            log_warning "$name 健康检查失败"
        fi
    done
}

# 显示访问信息
show_access_info() {
    log_info "监控服务访问信息:"
    echo ""
    echo "🔍 Prometheus:     http://localhost:9090"
    echo "📊 Grafana:        http://localhost:3000 (admin/admin)"
    echo "🔗 Jaeger:         http://localhost:16686"
    echo "🚨 AlertManager:   http://localhost:9093"
    echo "🤖 Feynman API:    http://localhost:8000"
    echo "📈 API指标:        http://localhost:8000/metrics"
    echo "❤️  健康检查:      http://localhost:8000/health"
    echo ""
    log_info "监控状态概览:     http://localhost:8000/monitoring/status"
    log_info "成本统计:         http://localhost:8000/monitoring/costs"
}

# 主函数
main() {
    echo "🚀 费曼学习系统监控栈启动器"
    echo "=============================="
    
    # 检查环境
    check_docker
    check_configs
    
    # 创建目录
    create_directories
    
    # 启动监控栈
    start_monitoring_stack
    
    # 健康检查
    sleep 10
    health_check
    
    # 显示访问信息
    show_access_info
    
    log_success "监控栈启动完成！"
    echo ""
    log_info "使用 'docker-compose -f config/docker-compose.monitoring.yml logs -f' 查看日志"
    log_info "使用 'docker-compose -f config/docker-compose.monitoring.yml down' 停止服务"
}

# 错误处理
trap 'log_error "脚本执行失败"; exit 1' ERR

# 执行主函数
main "$@"


