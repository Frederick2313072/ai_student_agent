#!/usr/bin/env python3
"""
简化版 Flower 启动脚本 - 适配 Flower 2.0+
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    print("🌸 启动 Flower 监控面板...")
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = project_root / "environments" / "test.env"
    load_dotenv(env_path)
    
    # 获取Redis URL
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ REDIS_URL环境变量未设置")
        sys.exit(1)
    
    print(f"🔗 Redis连接: {redis_url[:30]}...{redis_url[-20:]} (云端)")
    print(f"🌐 Web监控面板: http://127.0.0.1:5555 (本地访问)")
    print("-" * 50)
    
    # 设置环境变量
    os.environ["CELERY_BROKER_URL"] = redis_url
    
    try:
        # 直接使用 Flower API 启动
        from flower.app import Flower
        from flower.options import default_options
        
        # 创建Flower应用
        app = Flower()
        
        # 设置基本选项
        options = default_options()
        options['port'] = 5555
        options['address'] = '127.0.0.1'  # Flower Web界面监听地址(本地)
        options['broker_api'] = redis_url  # Redis数据库地址(云端)
        options['broker'] = redis_url      # Redis数据库地址(云端)
        
        print("🚀 启动中...")
        app.start(options)
        
    except ImportError as e:
        print(f"❌ Flower导入失败: {e}")
        print("尝试使用命令行方式启动...")
        
        # 备用方案：使用subprocess
        import subprocess
        cmd = [sys.executable, "-m", "flower", "flower"]
        os.environ["FLOWER_PORT"] = "5555"
        os.environ["FLOWER_ADDRESS"] = "127.0.0.1"  # Web界面监听地址(本地)
        # Redis连接通过CELERY_BROKER_URL环境变量传递(云端)
        subprocess.run(cmd, cwd=project_root)
        
    except KeyboardInterrupt:
        print("\n👋 Flower已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
