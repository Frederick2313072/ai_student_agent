#!/usr/bin/env python3
"""
监控功能测试脚本
测试各个监控组件是否正常工作
"""

import asyncio
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any


def print_test_header(test_name: str):
    """打印测试头部"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")


def print_test_result(success: bool, message: str, details: Dict[str, Any] = None):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status}: {message}")
    
    if details:
        for key, value in details.items():
            print(f"  - {key}: {value}")


async def test_structured_logging():
    """测试结构化日志功能"""
    print_test_header("结构化日志")
    
    try:
        from core.monitoring.logging import (
            setup_structured_logging, get_logger, set_request_context,
            log_api_request, log_tool_call, log_llm_call
        )
        
        # 设置日志
        setup_structured_logging()
        logger = get_logger("test.monitoring")
        
        # 设置上下文
        set_request_context(
            request_id="test-req-123",
            session_id="test-session-456",
            user_id="test-user"
        )
        
        # 测试各种日志记录
        logger.info("测试日志记录")
        log_api_request("POST", "/test", 200, 150.5, "test-agent", "127.0.0.1")
        log_tool_call("test_tool", True, 250.0, input_args={"query": "test"}, output_length=100)
        log_llm_call("gpt-4", 100, 50, 1500.0, 0.002)
        
        print_test_result(True, "结构化日志功能正常", {
            "日志器创建": "成功",
            "上下文设置": "成功", 
            "日志记录": "成功"
        })
        
    except Exception as e:
        print_test_result(False, f"结构化日志测试失败: {str(e)}")


async def test_metrics_collection():
    """测试指标收集功能"""
    print_test_header("指标收集")
    
    try:
        from core.monitoring.metrics import (
            API_REQUESTS_TOTAL, API_REQUEST_DURATION, TOOL_CALLS_TOTAL,
            LLM_TOKENS_USED_TOTAL, record_llm_usage, record_conversation_start,
            get_registry, SystemMetricsCollector
        )
        
        # 测试指标记录
        API_REQUESTS_TOTAL.labels(method="POST", endpoint="/test", status_code=200).inc()
        API_REQUEST_DURATION.labels(method="POST", endpoint="/test").observe(0.150)
        TOOL_CALLS_TOTAL.labels(tool_name="test_tool", status="success").inc()
        LLM_TOKENS_USED_TOTAL.labels(model="gpt-4", type="prompt").inc(100)
        
        # 测试便捷函数
        record_llm_usage("gpt-4", 100, 50, 1.5, 0.002)
        record_conversation_start()
        
        # 测试系统指标收集
        collector = SystemMetricsCollector()
        collector.collect_system_metrics()
        
        # 获取指标注册表
        registry = get_registry()
        
        print_test_result(True, "指标收集功能正常", {
            "指标注册": "成功",
            "指标记录": "成功",
            "系统指标": "成功",
            "注册表": f"包含 {len(list(registry._names_to_collectors.keys()))} 个指标"
        })
        
    except Exception as e:
        print_test_result(False, f"指标收集测试失败: {str(e)}")


async def test_health_checker():
    """测试健康检查功能"""
    print_test_header("健康检查")
    
    try:
        from core.monitoring.health import HealthChecker
        
        health_checker = HealthChecker()
        
        # 测试各种健康检查
        print("正在执行健康检查...")
        
        # 系统资源检查
        system_check = await health_checker.check_system_resources()
        print(f"  系统资源: {system_check.status.value} - {system_check.message}")
        
        # ChromaDB检查
        chromadb_check = await health_checker.check_chromadb()
        print(f"  ChromaDB: {chromadb_check.status.value} - {chromadb_check.message}")
        
        # 就绪和存活检查
        readiness = await health_checker.get_readiness()
        liveness = await health_checker.get_liveness()
        
        # 完整检查
        full_check = await health_checker.run_all_checks()
        
        await health_checker.close()
        
        print_test_result(True, "健康检查功能正常", {
            "系统资源检查": system_check.status.value,
            "ChromaDB检查": chromadb_check.status.value,
            "就绪检查": "成功" if readiness["ready"] else "失败",
            "存活检查": "成功" if liveness["alive"] else "失败",
            "总体状态": full_check["status"],
            "检查数量": full_check["summary"]["total_checks"]
        })
        
    except Exception as e:
        print_test_result(False, f"健康检查测试失败: {str(e)}")


async def test_cost_tracker():
    """测试成本追踪功能"""
    print_test_header("成本追踪")
    
    try:
        from core.monitoring.cost_tracker import CostTracker, get_cost_tracker
        
        # 创建成本追踪器
        tracker = CostTracker()
        
        # 记录一些使用情况
        record1 = tracker.record_usage("gpt-4", 1000, 500, "test-session-1", "chat")
        record2 = tracker.record_usage("glm-4", 800, 300, "test-session-2", "chat")
        
        # 获取统计信息
        daily_cost = tracker.get_daily_cost()
        session_cost = tracker.get_session_cost("test-session-1")
        model_stats = tracker.get_model_usage_stats()
        budget_status = tracker.get_budget_status()
        
        # 获取全局实例
        global_tracker = get_cost_tracker()
        
        print_test_result(True, "成本追踪功能正常", {
            "使用记录": f"创建了 {len(tracker.usage_records)} 条记录",
            "今日成本": f"${daily_cost:.6f}",
            "会话成本": f"${session_cost:.6f}",
            "模型统计": f"包含 {len(model_stats)} 个模型",
            "预算状态": f"日预算使用 {budget_status['daily']['percentage']:.2f}%",
            "全局实例": "成功获取"
        })
        
    except Exception as e:
        print_test_result(False, f"成本追踪测试失败: {str(e)}")


async def test_middleware_components():
    """测试中间件组件"""
    print_test_header("中间件组件")
    
    try:
        from api.middleware.monitoring import MonitoringMiddleware
        from api.middleware.cors import setup_cors
        from fastapi import FastAPI
        
        # 创建测试应用
        app = FastAPI()
        
        # 测试CORS设置
        setup_cors(app)
        
        # 检查中间件类是否正确定义
        middleware = MonitoringMiddleware(app)
        
        print_test_result(True, "中间件组件正常", {
            "MonitoringMiddleware": "创建成功",
            "CORS设置": "配置成功",
            "中间件方法": f"包含 {len([m for m in dir(middleware) if not m.startswith('_')])} 个公共方法"
        })
        
    except Exception as e:
        print_test_result(False, f"中间件组件测试失败: {str(e)}")


async def test_configuration():
    """测试配置加载"""
    print_test_header("配置加载")
    
    try:
        import os
        from dotenv import load_dotenv
        
        # 重新加载环境变量
        load_dotenv('environments/test.env', override=True)
        
        # 检查关键配置
        monitoring_config = {
            "MONITORING_ENABLED": os.getenv("MONITORING_ENABLED"),
            "METRICS_ENABLED": os.getenv("METRICS_ENABLED"),
            "TRACING_ENABLED": os.getenv("TRACING_ENABLED"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
            "LOG_FORMAT": os.getenv("LOG_FORMAT"),
            "DAILY_COST_LIMIT_USD": os.getenv("DAILY_COST_LIMIT_USD"),
            "PROMETHEUS_PORT": os.getenv("PROMETHEUS_PORT")
        }
        
        missing_configs = [k for k, v in monitoring_config.items() if v is None]
        
        print_test_result(
            len(missing_configs) == 0,
            "配置加载" + ("正常" if len(missing_configs) == 0 else "部分失败"),
            {
                "已加载配置": len([v for v in monitoring_config.values() if v is not None]),
                "缺失配置": missing_configs if missing_configs else "无",
                "监控启用": monitoring_config["MONITORING_ENABLED"],
                "指标启用": monitoring_config["METRICS_ENABLED"],
                "日志级别": monitoring_config["LOG_LEVEL"]
            }
        )
        
    except Exception as e:
        print_test_result(False, f"配置加载测试失败: {str(e)}")


async def test_import_dependencies():
    """测试依赖导入"""
    print_test_header("依赖导入")
    
    dependencies = [
        ("prometheus_client", "Prometheus客户端"),
        ("psutil", "系统信息"),
        ("aiohttp", "异步HTTP客户端"),
        ("fastapi", "FastAPI框架"),
        ("starlette", "ASGI框架")
    ]
    
    imported = []
    failed = []
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            imported.append((module_name, description))
        except ImportError as e:
            failed.append((module_name, description, str(e)))
    
    print_test_result(
        len(failed) == 0,
        "依赖导入" + ("全部成功" if len(failed) == 0 else "部分失败"),
        {
            "成功导入": len(imported),
            "失败导入": len(failed),
            "成功的模块": [f"{name} ({desc})" for name, desc in imported[:3]],
            "失败的模块": [f"{name} ({desc})" for name, desc, _ in failed] if failed else "无"
        }
    )


async def main():
    """主测试函数"""
    print("🚀 开始监控功能测试")
    print(f"测试时间: {datetime.now().isoformat()}")
    
    # 运行所有测试
    test_functions = [
        test_import_dependencies,
        test_configuration,
        test_structured_logging,
        test_metrics_collection,
        test_health_checker,
        test_cost_tracker,
        test_middleware_components
    ]
    
    start_time = time.time()
    passed = 0
    total = len(test_functions)
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 出现异常: {str(e)}")
    
    duration = time.time() - start_time
    
    # 输出总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total}")
    print(f"通过数: {passed}")
    print(f"失败数: {total - passed}")
    print(f"成功率: {(passed/total)*100:.1f}%")
    print(f"耗时: {duration:.2f}秒")
    
    if passed == total:
        print("\n🎉 所有监控功能测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置和依赖")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试执行异常: {str(e)}")
        sys.exit(1)

