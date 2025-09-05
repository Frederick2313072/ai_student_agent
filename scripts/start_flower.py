#!/usr/bin/env python3
"""
Flower 监控面板启动脚本

Flower 是 Celery 的 Web 监控工具，提供任务队列的实时监控界面。
可以查看任务状态、worker状态、队列情况等。

使用方法:
    python scripts/start_flower.py
    python scripts/start_flower.py --port 5555
    python scripts/start_flower.py --port 5555 --env-file environments/production.env
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def main():
    parser = argparse.ArgumentParser(description="启动 Flower 监控面板")
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="监控面板端口 (默认: 5555)"
    )
    parser.add_argument(
        "--host", 
        type=str,
        default="127.0.0.1",
        help="绑定地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--broker",
        type=str,
        help="Redis broker URL (如果不指定，从环境变量读取)"
    )
    parser.add_argument(
        "--env-file",
        type=str, 
        default="environments/test.env",
        help="环境配置文件路径 (默认: environments/test.env)"
    )
    parser.add_argument(
        "--basic-auth",
        type=str,
        help="基础认证，格式: username:password"
    )
    
    args = parser.parse_args()
    
    # 检查环境文件
    env_file = project_root / args.env_file
    if not env_file.exists():
        print(f"❌ 环境配置文件不存在: {env_file}")
        sys.exit(1)
    
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", str(project_root / "src"))
    
    # 从环境变量获取broker URL
    broker_url = args.broker
    if not broker_url:
        # 从环境变量读取Redis Cloud配置
        from dotenv import load_dotenv
        load_dotenv(env_file)
        broker_url = os.getenv("REDIS_URL")
        if not broker_url:
            print(f"❌ REDIS_URL环境变量未设置")
            print(f"   请检查配置文件: {env_file}")
            sys.exit(1)
    
    # 构建Flower命令 (新版本格式)
    cmd = [
        sys.executable, "-m", "flower", "flower"
    ]
    

    
    print("🌸 启动 Flower 监控面板...")
    print(f"📁 项目目录: {project_root}")
    print(f"⚙️  环境文件: {env_file}")
    print(f"🌐 Web监控面板: http://{args.host}:{args.port} (本地访问)")
    print(f"🔗 Redis连接: {broker_url} (云端)")
    print(f"🔨 执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    # 设置Flower环境变量
    env = os.environ.copy()
    env.update({
        "CELERY_BROKER_URL": broker_url,      # Redis数据库地址(云端)
        "FLOWER_PORT": str(args.port),        # Web界面端口
        "FLOWER_ADDRESS": args.host           # Web界面监听地址(本地)
    })
    
    # 如果有认证设置
    if args.basic_auth:
        env["FLOWER_BASIC_AUTH"] = args.basic_auth
    
    try:
        # 启动Flower
        subprocess.run(cmd, cwd=project_root, env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Flower 监控面板已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ Flower 启动失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Flower 未安装")
        print("请运行: uv add flower")
        sys.exit(1)


if __name__ == "__main__":
    main()
