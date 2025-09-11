#!/usr/bin/env python3
"""
配置验证工具 - 费曼学习系统

独立的配置验证脚本，用于检查环境变量配置的完整性和正确性。
"""

import sys
import os
import argparse
from pathlib import Path

# 添加src到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feynman.core.config.settings import validate_configuration, get_api_key_setup_guide


def main():
    parser = argparse.ArgumentParser(description="费曼学习系统配置验证工具")
    parser.add_argument(
        "--env-file", 
        default=".env",
        help="环境变量文件路径 (默认: .env)"
    )
    parser.add_argument(
        "--show-guide",
        action="store_true", 
        help="显示API密钥设置指南"
    )
    parser.add_argument(
        "--check-apis",
        action="store_true",
        help="测试API连接状态"
    )
    
    args = parser.parse_args()
    
    print("🎓 费曼学习系统配置验证工具")
    print("=" * 50)
    
    if args.show_guide:
        print(get_api_key_setup_guide())
        return
    
    # 验证配置
    try:
        results = validate_configuration(args.env_file)
        
        # 总结状态
        print(f"\n📊 验证总结:")
        status = "✅ 就绪" if results["llm_available"] and not results["errors"] else "⚠️  需要配置"
        print(f"系统状态: {status}")
        
        if results["errors"]:
            print(f"\n❌ 发现 {len(results['errors'])} 个错误，需要修复后才能正常运行")
            sys.exit(1)
        elif results["warnings"]:
            print(f"\n⚠️  发现 {len(results['warnings'])} 个警告，建议完善配置以获得最佳体验")
            sys.exit(0)
        else:
            print("\n🎉 配置完美！可以正常运行所有功能")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ 配置验证失败: {e}")
        print(f"\n💡 建议:")
        print(f"  1. 检查环境变量文件是否存在: {args.env_file}")
        print(f"  2. 运行: python scripts/config_validator.py --show-guide")
        sys.exit(1)


if __name__ == "__main__":
    main()
