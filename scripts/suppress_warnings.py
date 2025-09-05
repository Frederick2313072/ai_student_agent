#!/usr/bin/env python3
"""
抑制警告和错误信息的配置脚本
用于创建更清洁的测试环境
"""

import warnings
import os
import sys

def setup_clean_environment():
    """设置清洁的测试环境，抑制非关键警告"""
    
    print("🧹 配置清洁测试环境...")
    
    # 1. 抑制 LangChain 废弃警告
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.*")
    warnings.filterwarnings("ignore", message=".*Chroma.*deprecated.*")
    print("✅ 已抑制 LangChain Chroma 废弃警告")
    
    # 2. 抑制其他常见警告
    warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.*")
    warnings.filterwarnings("ignore", category=UserWarning, module="torch.*")
    print("✅ 已抑制其他常见库警告")
    
    # 3. 设置环境变量禁用详细追踪
    os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
    os.environ["LANGFUSE_ENABLED"] = "false"
    print("✅ 已设置环境变量抑制警告")
    
    print("🎉 清洁测试环境配置完成！")
    return True

if __name__ == "__main__":
    setup_clean_environment()
