#!/usr/bin/env python3
"""
Vercel API测试脚本
用于验证部署后的API是否正常工作
"""

import requests
import json
import sys

def test_api(base_url):
    """测试API端点"""
    print(f"🧪 测试API: {base_url}")
    print("=" * 50)
    
    # 测试主页
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 主页端点正常")
            data = response.json()
            print(f"   版本: {data.get('version', 'unknown')}")
        else:
            print(f"❌ 主页端点失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 主页端点错误: {e}")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 健康检查正常")
            data = response.json()
            print(f"   状态: {data.get('status', 'unknown')}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
    
    # 测试状态端点
    try:
        response = requests.get(f"{base_url}/api/v1/status")
        if response.status_code == 200:
            print("✅ 状态端点正常")
            data = response.json()
            print(f"   API版本: {data.get('api_version', 'unknown')}")
            print(f"   平台: {data.get('deployment', {}).get('platform', 'unknown')}")
        else:
            print(f"❌ 状态端点失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态端点错误: {e}")
    
    # 测试聊天端点
    try:
        chat_data = {
            "topic": "Python编程",
            "explanation": "Python是一种高级编程语言，具有简洁的语法和强大的功能。",
            "session_id": "test-session"
        }
        response = requests.post(f"{base_url}/api/v1/chat", json=chat_data)
        if response.status_code == 200:
            print("✅ 聊天端点正常")
            data = response.json()
            print(f"   响应长度: {len(data.get('response', ''))}")
            print(f"   会话ID: {data.get('session_id', 'unknown')}")
        else:
            print(f"❌ 聊天端点失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 聊天端点错误: {e}")
    
    print("=" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python test_vercel_api.py <your-vercel-url>")
        print("例如: python test_vercel_api.py https://your-project.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    test_api(base_url)
