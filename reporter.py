# -*- coding: utf-8 -*-
"""
报告整合引擎
整合所有子模块输出，生成沙雕点评，构建最终分析报告
"""

import random
from datetime import datetime

from config import (
    RISK_WARNING, get_sandiao_quote, get_random_slogan,
)

# 评分权重（固定）
SCORE_WEIGHTS = {"sentiment": 0.5, "industry_heat": 0.3, "wuxing_match": 0.2}


def build_report(
    parsed_news: dict,
    wuxing_boost: dict,
    stock_result: dict,
    futures_result: dict = None,
    options_result: dict = None,
    winrate: dict = None,
) -> dict:
    """整合所有模块结果，生成完整分析报告"""

    boost_level = wuxing_boost.get("boost_level", "中性")
    wuxing = parsed_news.get("wuxing", "未匹配")
    sentiment = parsed_news.get("sentiment_score", 0)

    # 综合评分
    total_score = calc_total_score(sentiment, parsed_news.get("industries", []), boost_level)

    # 沙雕点评
    sandiao_stock = get_sandiao_quote(boost_level, "stock")
    sandiao_futures = get_sandiao_quote(boost_level, "futures") if futures_result else ""
    sandiao_options = get_sandiao_quote(boost_level, "options") if options_result else ""

    # 操作建议
    action = derive_action(sentiment, boost_level)

    # 风险提示构建
    risks = build_risks(sentiment, boost_level, wuxing_boost, stock_result)

    report = {
        "meta": {
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": "规则引擎" if not __import__('os').getenv("OPENAI_API_KEY") else "LLM增强",
        },
        "news_summary": parsed_news.get("title", "") + " | " + parsed_news.get("content", "")[:80],
        "source": parsed_news.get("source", ""),
        "event_type": parsed_news.get("event_type", ""),
        "industries": parsed_news.get("industries", []),
        "wuxing": wuxing,
        "sentiment_score": sentiment,
        "term_name": wuxing_boost.get("term", {}).get("name", ""),
        "term_phase": wuxing_boost.get("term", {}).get("phase", ""),
        "boost_level": boost_level,
        "boost_detail": wuxing_boost.get("detail", ""),
        "ganzhi": wuxing_boost.get("ganzhi", {}).get("day_ganzhi", ""),
        "total_score": round(total_score, 3),
        "action": action,
        "sandiao_stock": sandiao_stock,
        "sandiao_futures": sandiao_futures,
        "sandiao_options": sandiao_options,
        "slogan": get_random_slogan(),
        "risk_warning": RISK_WARNING,
        "risks": risks,
        "stocks": stock_result.get("stocks", []),
        "stock_logic": stock_result.get("logic", ""),
        "futures": futures_result.get("futures", []) if futures_result else [],
        "futures_logic": futures_result.get("logic", "") if futures_result else "",
        "options": options_result.get("options", []) if options_result else [],
        "options_logic": options_result.get("logic", "") if options_result else "",
        "win_rate": winrate or {},
    }

    return report


def derive_action(sentiment: float, boost_level: str) -> str:
    """根据情绪和五行增强推导操作建议"""
    if sentiment >= 0.6 and boost_level in ("增强", "当令"):
        return "强烈买入 🟢"
    elif sentiment >= 0.3:
        return "买入/关注 🟡"
    elif sentiment <= -0.6 and boost_level in ("削弱", "轻微削弱"):
        return "回避/做空 🔴"
    elif sentiment <= -0.3:
        return "减仓/回避 🟠"
    else:
        return "观望 ⚪"


def calc_total_score(sentiment: float, industries: list, boost_level: str) -> float:
    """计算综合评分：情绪×0.5 + 行业热度×0.3 + 五行匹配×0.2"""
    sentiment_component = (sentiment + 1) / 2 * SCORE_WEIGHTS["sentiment"]
    industry_score = min(1.0, len(industries) / 5) if industries else 0.3
    industry_component = industry_score * SCORE_WEIGHTS["industry_heat"]

    boost_scores = {"增强": 1.0, "当令": 0.8, "轻微削弱": 0.35, "削弱": 0.2, "中性": 0.5}
    wuxing_score = boost_scores.get(boost_level, 0.5)
    wuxing_component = wuxing_score * SCORE_WEIGHTS["wuxing_match"]

    return sentiment_component + industry_component + wuxing_component


def build_risks(sentiment: float, boost_level: str, wuxing_boost: dict, stock_result: dict) -> list:
    """构建风险提示列表"""
    risks = []
    if sentiment <= -0.3:
        risks.append("[!] 情绪偏空，注意下行风险")
    if boost_level in ("削弱", "轻微削弱"):
        risks.append(f"[!] 节气周期不利：{boost_level}")
    if not stock_result.get("stocks"):
        risks.append("[!] 未匹配到推荐标的")
    if stock_result.get("total_matched", 0) < 2:
        risks.append("[!] 可选标的较少，选择面窄")
    return risks if risks else ["未检测到显著风险"]
