#!/usr/bin/env python3
"""
开发辅助工具 - 费曼学习系统

提供开发过程中常用的命令和检查功能，简化开发流程。
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_command(cmd: List[str], description: str) -> bool:
    """运行命令并显示结果"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            print(f"✅ {description}完成")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败")
        if e.stderr:
            print(f"   错误: {e.stderr.strip()}")
        return False


def check_dependencies():
    """检查项目依赖"""
    print("\n📦 检查项目依赖...")
    
    # 检查uv
    if run_command(["uv", "--version"], "检查uv"):
        run_command(["uv", "sync"], "同步依赖")
    else:
        print("⚠️  uv未安装，使用pip")
        run_command(["pip", "install", "-r", "requirements.txt"], "安装依赖")


def validate_config():
    """验证配置"""
    print("\n🔍 验证系统配置...")
    try:
        from feynman.core.config.settings import validate_configuration
        validate_configuration()
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    return True


def test_imports():
    """测试关键模块导入"""
    print("\n🔄 测试模块导入...")
    
    test_modules = [
        ("feynman.api.v1.endpoints.chat", "Chat API"),
        ("feynman.agents.core.agent", "Agent核心"),
        ("feynman.agents.tools", "Agent工具"),
        ("feynman.api.v1.endpoints.monitoring", "监控API"),
        ("feynman.api.v1.endpoints.config", "配置API")
    ]
    
    success_count = 0
    for module, description in test_modules:
        try:
            __import__(module)
            print(f"✅ {description}: 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {description}: 导入失败 - {e}")
    
    print(f"\n📊 导入测试结果: {success_count}/{len(test_modules)} 成功")
    return success_count == len(test_modules)


def start_dev_server():
    """启动开发服务器"""
    print("\n🚀 启动开发服务器...")
    
    # 检查配置
    if not validate_config():
        print("⚠️  配置有问题，但将以受限模式启动")
    
    # 启动服务器
    try:
        subprocess.run(["uv", "run", "python", "run_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")


def run_tests():
    """运行测试套件"""
    print("\n🧪 运行测试...")
    
    # 运行不同类型的测试
    test_commands = [
        (["uv", "run", "pytest", "tests/unit/", "-v"], "单元测试"),
        (["uv", "run", "pytest", "tests/integration/", "-v"], "集成测试"),
    ]
    
    for cmd, description in test_commands:
        if not run_command(cmd, f"运行{description}"):
            print(f"⚠️  {description}失败，继续其他测试...")


def lint_code():
    """代码风格检查"""
    print("\n📝 代码风格检查...")
    
    # 尝试运行各种linter
    linters = [
        (["uv", "run", "black", "--check", "src/"], "Black格式检查"),
        (["uv", "run", "isort", "--check-only", "src/"], "导入排序检查"),
        (["uv", "run", "flake8", "src/"], "代码风格检查")
    ]
    
    for cmd, description in linters:
        run_command(cmd, description)


def show_system_info():
    """显示系统信息"""
    print("🖥️  系统信息:")
    print(f"  Python版本: {sys.version.split()[0]}")
    print(f"  工作目录: {os.getcwd()}")
    print(f"  项目根目录: {Path(__file__).parent.parent}")
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("  虚拟环境: ✅ 已激活")
    else:
        print("  虚拟环境: ⚠️  未激活")


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="费曼学习系统开发辅助工具")
    parser.add_argument("action", choices=[
        "setup", "check", "test", "lint", "start", "info", "all"
    ], help="要执行的操作")
    
    args = parser.parse_args()
    
    print("🎓 费曼学习系统开发辅助工具")
    print("=" * 50)
    
    if args.action == "info":
        show_system_info()
    elif args.action == "setup":
        check_dependencies()
        validate_config()
    elif args.action == "check":
        validate_config()
        test_imports()
    elif args.action == "test":
        run_tests()
    elif args.action == "lint":
        lint_code()
    elif args.action == "start":
        start_dev_server()
    elif args.action == "all":
        show_system_info()
        check_dependencies()
        validate_config()
        test_imports()
        run_tests()
        lint_code()
        print("\n🎉 开发环境检查完成！")
    
    print("\n👋 完成！")


if __name__ == "__main__":
    main()
