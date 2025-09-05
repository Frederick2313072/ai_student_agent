"""
知识图谱依赖安装脚本

安装知识图谱功能所需的Python包和spaCy模型。
"""

import subprocess
import sys
import os


def install_packages():
    """安装Python包"""
    packages = [
        "networkx",
        "pyvis", 
        "plotly",
        "neo4j",
        "py2neo",
        "spacy",
        "spacy-transformers"
    ]
    
    print("📦 安装知识图谱依赖包...")
    
    try:
        # 使用uv安装（如果可用）
        subprocess.run(
            ["uv", "add"] + packages,
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print("✅ 使用uv安装依赖包成功")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 回退到pip
        print("⚠️ uv不可用，使用pip安装...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + packages,
                check=True
            )
            print("✅ 使用pip安装依赖包成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ 安装依赖包失败: {e}")
            return False
    
    return True


def install_spacy_models():
    """安装spaCy语言模型"""
    models = [
        "zh_core_web_sm",  # 中文模型
        "en_core_web_sm"   # 英文模型
    ]
    
    print("\n🧠 安装spaCy语言模型...")
    
    for model in models:
        try:
            print(f"   安装 {model}...")
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", model],
                check=True,
                capture_output=True
            )
            print(f"   ✅ {model} 安装成功")
            
        except subprocess.CalledProcessError:
            print(f"   ⚠️ {model} 安装失败（可能已安装或网络问题）")
        except Exception as e:
            print(f"   ❌ {model} 安装错误: {e}")


def create_data_directories():
    """创建数据目录"""
    directories = [
        "data",
        "data/temp",
        "data/exports"
    ]
    
    print("\n📁 创建数据目录...")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for directory in directories:
        dir_path = os.path.join(project_root, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"   ✅ {directory}")


def verify_installation():
    """验证安装"""
    print("\n🔍 验证安装...")
    
    # 测试Python包导入
    test_imports = [
        ("networkx", "NetworkX"),
        ("pyvis", "Pyvis"),
        ("plotly", "Plotly"),
        ("spacy", "spaCy")
    ]
    
    for module_name, display_name in test_imports:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} 导入失败")
    
    # 测试spaCy模型
    spacy_models = ["zh_core_web_sm", "en_core_web_sm"]
    
    try:
        import spacy
        for model in spacy_models:
            try:
                spacy.load(model)
                print(f"   ✅ spaCy模型: {model}")
            except OSError:
                print(f"   ❌ spaCy模型: {model} 未找到")
    except ImportError:
        print("   ❌ spaCy未安装")


def main():
    """主函数"""
    print("🚀 知识图谱依赖安装向导")
    print("=" * 50)
    
    # 1. 安装Python包
    if not install_packages():
        print("❌ 包安装失败，停止安装")
        return
    
    # 2. 安装spaCy模型
    install_spacy_models()
    
    # 3. 创建目录
    create_data_directories()
    
    # 4. 验证安装
    verify_installation()
    
    print("\n" + "=" * 50)
    print("🎉 知识图谱依赖安装完成！")
    print("\n📖 下一步:")
    print("1. 启动服务: python run_app.py")
    print("2. 访问Streamlit界面，在侧边栏启用知识图谱功能")
    print("3. 运行演示: python examples/knowledge_graph_demo.py")


if __name__ == "__main__":
    main()

