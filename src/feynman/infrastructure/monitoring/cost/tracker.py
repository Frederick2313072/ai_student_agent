"""
成本追踪模块 - 追踪LLM调用成本和Token使用情况
支持OpenAI和智谱AI的成本计算与预算控制
"""

import os
import time
import json
from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio
# 移除循环导入，直接实现记录功能


# 模型定价表 (2024年最新价格，单位：USD per 1K tokens)
MODEL_PRICING = {
    # OpenAI模型
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
    "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
    "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    "text-embedding-3-small": {"prompt": 0.00002, "completion": 0},
    "text-embedding-3-large": {"prompt": 0.00013, "completion": 0},
    
    # 智谱AI模型 (转换为USD，假设汇率1 CNY = 0.14 USD)
    "glm-4": {"prompt": 0.0014, "completion": 0.0014},  # 0.01 CNY/1K tokens
    "glm-4-airx": {"prompt": 0.007, "completion": 0.007},  # 0.05 CNY/1K tokens
    "glm-4-air": {"prompt": 0.0014, "completion": 0.0014},
    "glm-4-flash": {"prompt": 0.0001, "completion": 0.0001},  # 0.001 CNY/1K tokens
    "embedding-2": {"prompt": 0.00007, "completion": 0},  # 0.0005 CNY/1K tokens
    "embedding-3": {"prompt": 0.00007, "completion": 0}
}


@dataclass
class TokenUsage:
    """Token使用情况"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def efficiency_ratio(self) -> float:
        """计算token效率比率（输出/输入）"""
        return self.completion_tokens / max(self.prompt_tokens, 1)


@dataclass
class CostBreakdown:
    """成本详细分解"""
    prompt_cost: float
    completion_cost: float
    total_cost: float
    model: str
    provider: str
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UsageRecord:
    """使用记录"""
    timestamp: datetime
    model: str
    provider: str
    token_usage: TokenUsage
    cost_breakdown: CostBreakdown
    session_id: Optional[str] = None
    request_type: str = "chat"  # chat, embedding, etc.
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "provider": self.provider,
            "token_usage": asdict(self.token_usage),
            "cost_breakdown": self.cost_breakdown.to_dict(),
            "session_id": self.session_id,
            "request_type": self.request_type
        }


class CostTracker:
    """成本追踪器"""
    
    def __init__(self, storage_path: str = "logs/cost_tracking.json"):
        self.storage_path = storage_path
        self.daily_costs = defaultdict(float)  # date -> cost
        self.hourly_costs = defaultdict(float)  # datetime_hour -> cost
        self.session_costs = defaultdict(float)  # session_id -> cost
        self.model_costs = defaultdict(float)  # model -> cost
        self.usage_records = []
        
        # 预算设置
        self.daily_budget_usd = float(os.getenv("DAILY_COST_LIMIT_USD", "100"))
        self.monthly_budget_usd = float(os.getenv("MONTHLY_COST_LIMIT_USD", "1000"))
        
        # 加载历史数据
        self._load_usage_data()
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> CostBreakdown:
        """
        计算模型调用成本
        
        Args:
            model: 模型名称
            prompt_tokens: 提示词token数
            completion_tokens: 回复token数
            
        Returns:
            CostBreakdown: 成本分解详情
        """
        if model not in MODEL_PRICING:
            # 未知模型，使用GPT-4的价格作为默认值
            pricing = MODEL_PRICING["gpt-4"]
            print(f"警告: 未知模型 {model}，使用默认定价")
        else:
            pricing = MODEL_PRICING[model]
        
        # 计算成本
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        total_cost = prompt_cost + completion_cost
        
        # 判断提供商
        provider = "openai" if model.startswith("gpt") or "embedding" in model else "zhipu"
        
        return CostBreakdown(
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            model=model,
            provider=provider
        )
    
    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
        request_type: str = "chat",
        duration_seconds: float = 0
    ) -> UsageRecord:
        """
        记录模型使用情况
        
        Args:
            model: 模型名称
            prompt_tokens: 提示词token数
            completion_tokens: 回复token数
            session_id: 会话ID
            request_type: 请求类型
            duration_seconds: 请求持续时间
            
        Returns:
            UsageRecord: 使用记录
        """
        # 创建token使用记录
        token_usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        
        # 计算成本
        cost_breakdown = self.calculate_cost(model, prompt_tokens, completion_tokens)
        
        # 创建使用记录
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc),
            model=model,
            provider=cost_breakdown.provider,
            token_usage=token_usage,
            cost_breakdown=cost_breakdown,
            session_id=session_id,
            request_type=request_type
        )
        
        # 更新内存中的统计
        today = date.today().isoformat()
        current_hour = record.timestamp.replace(minute=0, second=0, microsecond=0)
        
        self.daily_costs[today] += cost_breakdown.total_cost
        self.hourly_costs[current_hour.isoformat()] += cost_breakdown.total_cost
        self.model_costs[model] += cost_breakdown.total_cost
        
        if session_id:
            self.session_costs[session_id] += cost_breakdown.total_cost
        
        # 保存记录
        self.usage_records.append(record)
        
        # 记录到Prometheus指标
        # 记录到内部统计（移除外部依赖，简化代码）
        try:
            from prometheus_client import Counter
            llm_usage_counter = Counter('llm_usage_total', 'LLM使用统计', ['model'])
            llm_usage_counter.labels(model=model).inc(prompt_tokens + completion_tokens)
        except:
            pass  # 监控不可用时静默失败
        
        # 智能保存到文件（同步/异步兼容）
        self._safe_save_usage_data()
        
        # 检查预算
        self._check_budget_limits()
        
        return record
    
    def get_daily_cost(self, target_date: date = None) -> float:
        """获取指定日期的总成本"""
        if target_date is None:
            target_date = date.today()
        
        return self.daily_costs.get(target_date.isoformat(), 0.0)
    
    def get_monthly_cost(self, year: int = None, month: int = None) -> float:
        """获取指定月份的总成本"""
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        month_prefix = f"{year:04d}-{month:02d}"
        return sum(
            cost for date_str, cost in self.daily_costs.items()
            if date_str.startswith(month_prefix)
        )
    
    def get_session_cost(self, session_id: str) -> float:
        """获取指定会话的总成本"""
        return self.session_costs.get(session_id, 0.0)
    
    def get_model_usage_stats(self) -> Dict[str, Dict[str, float]]:
        """获取各模型的使用统计"""
        stats = {}
        
        for model in self.model_costs:
            # 计算该模型的token统计
            model_records = [r for r in self.usage_records if r.model == model]
            
            total_prompt_tokens = sum(r.token_usage.prompt_tokens for r in model_records)
            total_completion_tokens = sum(r.token_usage.completion_tokens for r in model_records)
            total_cost = self.model_costs[model]
            
            avg_efficiency = sum(r.token_usage.efficiency_ratio for r in model_records) / len(model_records) if model_records else 0
            
            stats[model] = {
                "total_cost": total_cost,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
                "call_count": len(model_records),
                "avg_efficiency_ratio": avg_efficiency,
                "cost_per_1k_tokens": (total_cost * 1000) / max(total_prompt_tokens + total_completion_tokens, 1)
            }
        
        return stats
    
    def get_cost_trends(self, days: int = 7) -> Dict[str, List[Dict]]:
        """获取成本趋势数据"""
        from datetime import timedelta
        
        today = date.today()
        trends = {
            "daily": [],
            "hourly": []
        }
        
        # 日趋势
        for i in range(days):
            target_date = today - timedelta(days=i)
            daily_cost = self.get_daily_cost(target_date)
            trends["daily"].append({
                "date": target_date.isoformat(),
                "cost": daily_cost
            })
        
        trends["daily"].reverse()  # 最早的日期在前
        
        # 小时趋势（最近24小时）
        now = datetime.now(timezone.utc)
        for i in range(24):
            target_hour = now - timedelta(hours=i)
            hour_key = target_hour.replace(minute=0, second=0, microsecond=0).isoformat()
            hourly_cost = self.hourly_costs.get(hour_key, 0.0)
            trends["hourly"].append({
                "datetime": hour_key,
                "cost": hourly_cost
            })
        
        trends["hourly"].reverse()  # 最早的小时在前
        
        return trends
    
    def get_budget_status(self) -> Dict[str, any]:
        """获取预算使用状态"""
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        return {
            "daily": {
                "used": daily_cost,
                "budget": self.daily_budget_usd,
                "percentage": (daily_cost / self.daily_budget_usd) * 100,
                "remaining": max(0, self.daily_budget_usd - daily_cost),
                "exceeded": daily_cost > self.daily_budget_usd
            },
            "monthly": {
                "used": monthly_cost,
                "budget": self.monthly_budget_usd,
                "percentage": (monthly_cost / self.monthly_budget_usd) * 100,
                "remaining": max(0, self.monthly_budget_usd - monthly_cost),
                "exceeded": monthly_cost > self.monthly_budget_usd
            }
        }
    
    def _check_budget_limits(self) -> None:
        """检查预算限制并发出警告"""
        budget_status = self.get_budget_status()
        
        # 检查日预算
        if budget_status["daily"]["exceeded"]:
            print(f"⚠️  每日成本预算超支: ${budget_status['daily']['used']:.4f} > ${self.daily_budget_usd}")
        elif budget_status["daily"]["percentage"] > 80:
            print(f"⚠️  每日成本预算使用超过80%: {budget_status['daily']['percentage']:.1f}%")
        
        # 检查月预算
        if budget_status["monthly"]["exceeded"]:
            print(f"⚠️  每月成本预算超支: ${budget_status['monthly']['used']:.4f} > ${self.monthly_budget_usd}")
        elif budget_status["monthly"]["percentage"] > 80:
            print(f"⚠️  每月成本预算使用超过80%: {budget_status['monthly']['percentage']:.1f}%")
    
    def _safe_save_usage_data(self) -> None:
        """智能保存使用数据到文件（同步/异步兼容）"""
        try:
            # 检测是否有运行中的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果有事件循环，创建异步任务
                asyncio.create_task(self._save_usage_data_async())
            except RuntimeError:
                # 没有事件循环，使用同步保存
                self._save_usage_data_sync()
        except Exception as e:
            print(f"保存成本数据失败: {e}")
    
    async def _save_usage_data_async(self) -> None:
        """异步保存使用数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # 只保存最近的记录（避免文件过大）
            recent_records = self.usage_records[-1000:]  # 保留最近1000条记录
            
            data = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "daily_costs": dict(self.daily_costs),
                "hourly_costs": dict(self.hourly_costs),
                "session_costs": dict(self.session_costs),
                "model_costs": dict(self.model_costs),
                "recent_records": [record.to_dict() for record in recent_records]
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"异步保存成本数据失败: {e}")
    
    def _save_usage_data_sync(self) -> None:
        """同步保存使用数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # 只保存最近的记录（避免文件过大）
            recent_records = self.usage_records[-1000:]  # 保留最近1000条记录
            
            data = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "daily_costs": dict(self.daily_costs),
                "hourly_costs": dict(self.hourly_costs),
                "session_costs": dict(self.session_costs),
                "model_costs": dict(self.model_costs),
                "recent_records": [record.to_dict() for record in recent_records]
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"同步保存成本数据失败: {e}")
    
    def _load_usage_data(self) -> None:
        """从文件加载使用数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载统计数据
                self.daily_costs.update(data.get("daily_costs", {}))
                self.hourly_costs.update(data.get("hourly_costs", {}))
                self.session_costs.update(data.get("session_costs", {}))
                self.model_costs.update(data.get("model_costs", {}))
                
                # 加载最近的记录
                recent_records_data = data.get("recent_records", [])
                for record_data in recent_records_data:
                    try:
                        # 重建UsageRecord对象
                        token_usage = TokenUsage(**record_data["token_usage"])
                        cost_breakdown = CostBreakdown(**record_data["cost_breakdown"])
                        
                        record = UsageRecord(
                            timestamp=datetime.fromisoformat(record_data["timestamp"]),
                            model=record_data["model"],
                            provider=record_data["provider"],
                            token_usage=token_usage,
                            cost_breakdown=cost_breakdown,
                            session_id=record_data.get("session_id"),
                            request_type=record_data.get("request_type", "chat")
                        )
                        
                        self.usage_records.append(record)
                        
                    except Exception as e:
                        print(f"加载使用记录失败: {e}")
                        continue
                
                print(f"成功加载 {len(self.usage_records)} 条使用记录")
                
        except Exception as e:
            print(f"加载成本数据失败: {e}")
    
    def export_usage_report(self, start_date: date = None, end_date: date = None) -> Dict:
        """导出使用报告"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)  # 默认最近30天
        if end_date is None:
            end_date = date.today()
        
        # 筛选记录
        filtered_records = [
            record for record in self.usage_records
            if start_date <= record.timestamp.date() <= end_date
        ]
        
        # 计算统计信息
        total_cost = sum(record.cost_breakdown.total_cost for record in filtered_records)
        total_tokens = sum(record.token_usage.total_tokens for record in filtered_records)
        
        # 按提供商分组
        provider_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "calls": 0})
        for record in filtered_records:
            provider = record.provider
            provider_stats[provider]["cost"] += record.cost_breakdown.total_cost
            provider_stats[provider]["tokens"] += record.token_usage.total_tokens
            provider_stats[provider]["calls"] += 1
        
        # 按模型分组
        model_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "calls": 0})
        for record in filtered_records:
            model = record.model
            model_stats[model]["cost"] += record.cost_breakdown.total_cost
            model_stats[model]["tokens"] += record.token_usage.total_tokens
            model_stats[model]["calls"] += 1
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "summary": {
                "total_cost_usd": total_cost,
                "total_tokens": total_tokens,
                "total_calls": len(filtered_records),
                "avg_cost_per_call": total_cost / len(filtered_records) if filtered_records else 0,
                "avg_cost_per_1k_tokens": (total_cost * 1000) / total_tokens if total_tokens else 0
            },
            "by_provider": dict(provider_stats),
            "by_model": dict(model_stats),
            "cost_trends": self.get_cost_trends((end_date - start_date).days + 1)
        }


# 全局成本追踪器实例
_cost_tracker_instance = None


def get_cost_tracker() -> CostTracker:
    """获取全局成本追踪器实例"""
    global _cost_tracker_instance
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker()
    return _cost_tracker_instance

