# -*- coding: utf-8 -*-
"""
回测模块
查询历史上同类五行事件发生后 5/10/20 日标的涨跌概率
给出"玄学胜率"
维护 event_log.json 事件库
"""

import json
import random
from datetime import datetime, timedelta
from config import (
    EVENT_LOG_PATH, load_event_log, save_event_log,
    WUXING_INDUSTRY_MAP, SIMULATE_MODE,
)


def calculate_win_rate(
    wuxing: str,
    event_type: str,
    hold_days: int = 10,
) -> dict:
    """计算历史上同类五行事件的胜率"""

    event_log = load_event_log()

    # 筛选同类事件
    similar = []
    for entry in event_log:
        entry_wx = entry.get("wuxing", "")
        entry_et = entry.get("event_type", "")
        if entry_wx == wuxing or entry_et == event_type:
            similar.append(entry)

    if not similar and SIMULATE_MODE:
        # 模拟模式下生成模拟胜率
        return generate_simulated_winrate(wuxing, event_type)

    # 计算实际回测结果
    wins = sum(1 for e in similar if e.get("result", {}).get("pnl_pct", 0) > 0)
    total = len(similar)
    win_rate = wins / total if total > 0 else 0

    avg_return = sum(e.get("result", {}).get("pnl_pct", 0) for e in similar) / total if total > 0 else 0

    return {
        "wuxing": wuxing,
        "event_type": event_type,
        "total_events": total,
        "win_count": wins,
        "win_rate": f"{win_rate:.1%}",
        "win_rate_num": round(win_rate, 3),
        "avg_return": f"{avg_return:.2%}",
        "hold_days": hold_days,
        "sample_size": total,
        "confidence": "高" if total >= 30 else ("中" if total >= 10 else "低(样本不足)"),
        "note": f"历史{wuxing}属性{event_type}类事件共{total}次，{hold_days}日胜率{win_rate:.1%}" if total > 0 else "暂无同类事件记录",
    }


def generate_simulated_winrate(wuxing: str, event_type: str = "") -> dict:
    """在模拟/无历史数据时，基于五行特征生成合理的模拟胜率"""

    # 不同五行的"历史表现"不同（模拟）
    base_rates = {"火": 0.55, "金": 0.52, "水": 0.48, "木": 0.50, "土": 0.45}

    # 加入随机波动
    base = base_rates.get(wuxing, 0.50)
    noise = random.uniform(-0.05, 0.05)
    win_rate_5 = min(0.75, max(0.30, base + noise))
    win_rate_10 = win_rate_5 + random.uniform(-0.03, 0.03)
    win_rate_20 = win_rate_10 + random.uniform(-0.05, 0.05)

    sample_sizes = {"5日": 45, "10日": 42, "20日": 38}

    return {
        "wuxing": wuxing,
        "event_type": event_type,
        "simulated": True,
        "multi_period": {
            "5日胜率": f"{win_rate_5:.1%}",
            "10日胜率": f"{win_rate_10:.1%}",
            "20日胜率": f"{win_rate_20:.1%}",
        },
        "win_rate_num": round(win_rate_10, 3),
        "avg_return": f"{random.uniform(0.01, 0.05):.2%}",
        "sample_size": random.choice([38, 42, 45, 50]),
        "confidence": "中(模拟数据)",
        "note": f"⚠ 基于模拟数据，真实胜率需积累event_log。五行「{wuxing}」类事件模拟胜率约{win_rate_10:.1%}",
    }


def record_event(news_text: str, analysis: dict, dt: datetime = None) -> dict:
    """记录一次分析事件到 event_log"""

    if dt is None:
        dt = datetime.now()

    entry = {
        "timestamp": dt.isoformat(),
        "news_summary": news_text[:100],
        "wuxing": analysis.get("五行属性", ""),
        "event_type": analysis.get("事件类型", ""),
        "sentiment_score": analysis.get("情绪评分", 0),
        "boost_level": analysis.get("五行增强", ""),
        "win_rate": analysis.get("胜率", {}),
        "stocks_recommended": [
            {"name": s.get("name", ""), "code": s.get("code", "")}
            for s in analysis.get("推荐股票", [])
        ][:3],
        "result": {},  # 后续可填入实际结果
    }

    save_event_log(entry)
    return entry


def backtest_historical(start_date: datetime, end_date: datetime, wuxing: str = "") -> dict:
    """对 event_log 中指定时间段的事件做回测"""
    log = load_event_log()
    filtered = []

    for entry in log:
        ts = entry.get("timestamp", "")
        try:
            entry_dt = datetime.fromisoformat(ts)
        except ValueError:
            continue

        if start_date <= entry_dt <= end_date:
            if not wuxing or entry.get("wuxing") == wuxing:
                filtered.append(entry)

    if not filtered:
        return {"error": "暂无符合条件的记录", "count": 0}

    # 统计有结果的事件
    with_results = [e for e in filtered if e.get("result") and e["result"].get("pnl_pct") is not None]
    wins = sum(1 for e in with_results if e.get("result", {}).get("pnl_pct", 0) > 0)

    return {
        "total_analyzed": len(filtered),
        "with_results": len(with_results),
        "wins": wins,
        "win_rate": f"{wins / len(with_results):.1%}" if with_results else "N/A",
        "period": f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
    }
