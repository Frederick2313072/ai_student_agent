#!/usr/bin/env python3
"""
环境配置设置工具 - 费曼学习系统

交互式环境变量配置向导，帮助用户快速设置开发/生产环境。
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List


def create_env_template(env_type: str, target_file: str) -> None:
    """创建环境变量模板"""
    
    templates = {
        "minimal": {
            "description": "最小配置 - 仅核心功能",
            "required": ["OPENAI_API_KEY", "ZHIPU_API_KEY"],
            "config": {
                "ENVIRONMENT": "development",
                "DEBUG": "true",
                "OPENAI_API_KEY": "",
                "ZHIPU_API_KEY": "",
                "MONITORING_ENABLED": "false",
                "METRICS_ENABLED": "false"
            }
        },
        "development": {
            "description": "开发环境 - 包含常用工具",
            "required": ["OPENAI_API_KEY", "TAVILY_API_KEY"],
            "config": {
                "ENVIRONMENT": "development",
                "DEBUG": "true",
                "LOG_LEVEL": "DEBUG",
                "OPENAI_API_KEY": "",
                "OPENAI_MODEL": "gpt-4o",
                "TAVILY_API_KEY": "",
                "BAIDU_TRANSLATE_API_KEY": "",
                "BAIDU_TRANSLATE_SECRET_KEY": "",
                "MONITORING_ENABLED": "true",
                "METRICS_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "",
                "LANGFUSE_SECRET_KEY": "",
                "CORS_ORIGINS": '["http://localhost:3000", "http://127.0.0.1:3000"]'
            }
        },
        "production": {
            "description": "生产环境 - 完整监控和安全配置", 
            "required": ["OPENAI_API_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"],
            "config": {
                "ENVIRONMENT": "production",
                "DEBUG": "false",
                "LOG_LEVEL": "INFO",
                "OPENAI_API_KEY": "",
                "OPENAI_MODEL": "gpt-4o",
                "TAVILY_API_KEY": "",
                "MONITORING_ENABLED": "true",
                "TRACING_ENABLED": "true",
                "METRICS_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "",
                "LANGFUSE_SECRET_KEY": "",
                "LANGFUSE_HOST": "https://cloud.langfuse.com",
                "DAILY_COST_LIMIT_USD": "100",
                "MONTHLY_COST_LIMIT_USD": "1000",
                "COST_TRACKING_ENABLED": "true",
                "REQUEST_TIMEOUT_ENABLED": "true",
                "REQUEST_TIMEOUT_SECONDS": "60",
                "CORS_ORIGINS": '["https://your-domain.com"]',
                "API_HOST": "0.0.0.0",
                "API_PORT": "8000"
            }
        },
        "full": {
            "description": "完整配置 - 所有功能和工具",
            "required": [],
            "config": {
                "ENVIRONMENT": "development",
                "DEBUG": "true",
                "OPENAI_API_KEY": "",
                "ZHIPU_API_KEY": "",
                "TAVILY_API_KEY": "",
                "BAIDU_TRANSLATE_API_KEY": "",
                "BAIDU_TRANSLATE_SECRET_KEY": "",
                "WOLFRAM_API_KEY": "",
                "YOUTUBE_API_KEY": "",
                "NEWS_API_KEY": "",
                "JUDGE0_API_KEY": "",
                "QUICKCHART_API_KEY": "",
                "LANGFUSE_PUBLIC_KEY": "",
                "LANGFUSE_SECRET_KEY": "",
                "MONITORING_ENABLED": "true",
                "TRACING_ENABLED": "true",
                "METRICS_ENABLED": "true",
                "COST_TRACKING_ENABLED": "true"
            }
        }
    }
    
    if env_type not in templates:
        print(f"❌ 未知的环境类型: {env_type}")
        print(f"可用类型: {', '.join(templates.keys())}")
        return
    
    template = templates[env_type]
    
    # 生成环境文件内容
    content = [
        f"# 费曼学习系统 - {template['description']}",
        f"# 生成时间: {os.popen('date').read().strip()}",
        ""
    ]
    
    if template["required"]:
        content.extend([
            "# ======================",
            "# 必需配置 (请填写)",
            "# ======================",
            ""
        ])
        
        for key in template["required"]:
            if key in template["config"]:
                content.append(f"{key}=\"\"  # 必需！请设置此项")
    
    content.extend([
        "",
        "# ======================",
        "# 系统配置",
        "# ======================"
    ])
    
    for key, value in template["config"].items():
        if key not in template.get("required", []):
            if isinstance(value, str) and value.startswith(('["', '{')):
                content.append(f"{key}={value}")
            else:
                content.append(f"{key}={value}")
    
    # 写入文件
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"✅ 环境配置模板已创建: {target_file}")
    print(f"📝 配置类型: {template['description']}")
    
    if template["required"]:
        print(f"⚠️  请编辑文件并填写必需的API密钥:")
        for key in template["required"]:
            print(f"   - {key}")


def interactive_setup():
    """交互式配置设置"""
    print("🎓 费曼学习系统环境配置向导")
    print("=" * 50)
    
    # 选择环境类型
    print("\n📋 请选择配置类型:")
    print("1. minimal - 最小配置（仅核心功能）")
    print("2. development - 开发环境（推荐）")
    print("3. production - 生产环境")
    print("4. full - 完整配置（所有工具）")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    env_types = {"1": "minimal", "2": "development", "3": "production", "4": "full"}
    env_type = env_types.get(choice, "development")
    
    # 选择目标文件
    print(f"\n📁 配置类型: {env_type}")
    default_file = f"environments/{env_type}.env"
    target_file = input(f"目标文件 (默认: {default_file}): ").strip() or default_file
    
    # 确认是否覆盖
    if os.path.exists(target_file):
        overwrite = input(f"⚠️  文件 {target_file} 已存在，是否覆盖？ (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ 操作取消")
            return
    
    # 创建目录
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    # 生成配置
    create_env_template(env_type, target_file)
    
    print(f"\n🎉 配置创建完成！")
    print(f"\n📋 下一步:")
    print(f"  1. 编辑 {target_file} 填写API密钥")
    print(f"  2. 运行验证: python scripts/config_validator.py --env-file {target_file}")
    print(f"  3. 启动应用: uv run python run_app.py")


def main():
    parser = argparse.ArgumentParser(description="费曼学习系统环境配置工具")
    parser.add_argument(
        "--type",
        choices=["minimal", "development", "production", "full"],
        help="配置模板类型"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互式配置"
    )
    
    args = parser.parse_args()
    
    if args.interactive or (not args.type and not args.output):
        interactive_setup()
    elif args.type and args.output:
        create_env_template(args.type, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    import argparse
    main()
