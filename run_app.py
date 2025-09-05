#!/usr/bin/env python3
"""
费曼学习系统应用启动器

这是一个简化的启动脚本，将调用新重构后的主应用。
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # 导入并运行主应用
    from main import app
    import uvicorn
    
    print("🚀 启动费曼学习系统...")
    print("📁 使用重构后的项目结构")
    print("🌐 访问 http://127.0.0.1:8000 查看API文档")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir="src"
    )

