#!/bin/bash
#
# Flower 监控面板管理脚本
# 避免端口占用问题的便捷工具
#

FLOWER_PORT=5555

case "$1" in
    start)
        echo "🚀 启动 Flower 监控面板..."
        
        # 检查端口是否被占用
        if lsof -i :$FLOWER_PORT > /dev/null 2>&1; then
            echo "⚠️  端口 $FLOWER_PORT 已被占用"
            echo "🔍 正在查找占用进程..."
            lsof -i :$FLOWER_PORT
            echo ""
            echo "💡 请先运行: $0 stop"
            exit 1
        fi
        
        # 启动 Flower
        echo "✅ 端口 $FLOWER_PORT 可用，正在启动..."
        make celery-flower
        ;;
        
    stop)
        echo "🛑 停止 Flower 监控面板..."
        
        # 查找并终止Flower进程
        PIDS=$(lsof -t -i :$FLOWER_PORT 2>/dev/null)
        
        if [ -z "$PIDS" ]; then
            echo "ℹ️  没有进程占用端口 $FLOWER_PORT"
        else
            echo "🔍 发现占用进程: $PIDS"
            for PID in $PIDS; do
                echo "🔨 终止进程 $PID..."
                kill $PID
            done
            sleep 2
            echo "✅ Flower 已停止"
        fi
        ;;
        
    restart)
        echo "🔄 重启 Flower 监控面板..."
        $0 stop
        sleep 1
        $0 start
        ;;
        
    status)
        echo "🔍 检查 Flower 状态..."
        
        if lsof -i :$FLOWER_PORT > /dev/null 2>&1; then
            echo "✅ Flower 正在运行"
            echo "📋 进程信息:"
            lsof -i :$FLOWER_PORT
            echo ""
            echo "🌐 访问地址: http://127.0.0.1:$FLOWER_PORT"
        else
            echo "❌ Flower 未运行"
            echo "💡 启动命令: $0 start"
        fi
        ;;
        
    *)
        echo "🌸 Flower 监控面板管理工具"
        echo "================================"
        echo ""
        echo "使用方法:"
        echo "  $0 start    - 启动 Flower"
        echo "  $0 stop     - 停止 Flower"  
        echo "  $0 restart  - 重启 Flower"
        echo "  $0 status   - 检查状态"
        echo ""
        echo "访问地址: http://127.0.0.1:$FLOWER_PORT"
        exit 1
        ;;
esac
