# -*- coding: utf-8 -*-
"""
五行韭菜盘 v3.0 —— 纯中国版日推引擎
每天自动：抓取中国新闻 → 五行算卦 → 股票(买入10/卖出10/回避10) + 期货(买入/卖出/回避)
每5分钟刷新新闻缓存
生成历史日推报告存档
"""

import json
import os
import time
import threading
import random
from datetime import datetime, timedelta
from pathlib import Path

from config import (
    SIMULATE_MODE, RISK_WARNING,
    STOCK_POOL, WUXING_INDUSTRY_MAP,
)
from news_fetcher import fetch_and_parse, force_refresh, get_cache_age
from five_elements import (
    get_current_solar_term, get_ganzhi_info,
    analyze_wuxing_boost, map_news_to_wuxing,
    get_wuxing_industries, WUXING_SHENG, WUXING_KE,
)
from stock_picker import pick_stocks
from futures_picker import pick_china_futures_categorized
from backtest import calculate_win_rate, save_event_log
from reporter import SCORE_WEIGHTS


REPORTS_DIR = Path(__file__).parent / "daily_reports"
REPORTS_DIR.mkdir(exist_ok=True)

_DAILY_STATE = {
    "last_report_time": None,
    "today_report": None,
    "is_running": False,
    "lock": threading.Lock(),
}


# ============================================================
# 核心：30只A股按买入/卖出/回避分三栏，各10只
# ============================================================
def pick_30_stocks_china(news_list: list) -> dict:
    """基于中国新闻+五行，选出30只A股：买入10 + 卖出10 + 回避10"""

    # 汇总新闻行业与五行
    all_industries = set()
    wuxing_scores = {}

    for news in news_list:
        industries = news.get("industries", [])
        all_industries.update(industries)
        wx = news.get("wuxing", "")
        sentiment = news.get("sentiment_score", 0)
        if wx and wx != "未匹配":
            if wx not in wuxing_scores:
                wuxing_scores[wx] = []
            wuxing_scores[wx].append(sentiment)

    # 主导五行
    if wuxing_scores:
        dominant_wx = max(wuxing_scores, key=lambda k: sum(wuxing_scores[k]) / len(wuxing_scores[k]))
    else:
        dominant_wx = "火"

    boost = analyze_wuxing_boost(dominant_wx)
    boost_level = boost["boost_level"]
    boost_modifier = boost.get("score_modifier", 0)

    # 扩展行业
    expanded_industries = list(all_industries)
    wx_industries = get_wuxing_industries(dominant_wx)
    for ind in wx_industries:
        if ind not in expanded_industries:
            expanded_industries.append(ind)
    if not expanded_industries:
        expanded_industries = ["军工", "新能源", "银行", "券商", "医药", "消费", "航运", "基建", "农业", "半导体", "煤炭", "电力", "钢铁"]

    # 从A股池捞出所有候选
    pool = STOCK_POOL.get("A股", {})
    candidates = []
    seen = set()
    for ind in expanded_industries:
        if ind in pool:
            for stock in pool[ind]:
                code = stock["code"]
                if code not in seen:
                    seen.add(code)
                    candidates.append({**stock, "matched_industry": ind, "market": "A股"})

    # 不够的话补全A股池
    if len(candidates) < 30:
        for ind, stocks in pool.items():
            for stock in stocks:
                code = stock["code"]
                if code not in seen:
                    seen.add(code)
                    candidates.append({**stock, "matched_industry": ind, "market": "A股"})
                    if len(candidates) >= 40:
                        break
            if len(candidates) >= 40:
                break

    # 给每只股票算五行多空综合分
    avg_news_sentiment = sum(sum(v)/len(v) for v in wuxing_scores.values()) / len(wuxing_scores) if wuxing_scores else 0.0

    for stock in candidates:
        stock_wx = _classify_stock_wuxing(stock)
        stock_direction = _calc_stock_direction(stock_wx, dominant_wx, boost_level, avg_news_sentiment)
        stock["wuxing"] = stock_wx
        stock["direction_score"] = stock_direction["score"]
        stock["direction_label"] = stock_direction["label"]
        stock["direction_reason"] = stock_direction["reason"]

    # 按分数排序
    candidates.sort(key=lambda x: x["direction_score"], reverse=True)

    # 分三组（按原始标签）
    _buy = [s for s in candidates if s["direction_label"] == "买入"]
    _sell = [s for s in candidates if s["direction_label"] == "卖出"]
    _avoid = [s for s in candidates if s["direction_label"] == "回避"]

    # 强制凑满每组10只：取全局排名
    ranked = sorted(candidates, key=lambda x: x["direction_score"], reverse=True)

    buy_stocks = ranked[:10]
    for s in buy_stocks:
        s["direction_label"] = "买入"
        s["action_icon"] = "买入"
        if s["direction_score"] < 0:
            s["direction_reason"] = "全局排名前10，综合评分偏向"

    seen_buy = {s["code"] for s in buy_stocks}
    remaining = [s for s in ranked if s["code"] not in seen_buy]
    sell_stocks = remaining[-10:] if len(remaining) >= 10 else remaining
    sell_stocks = list(reversed(sell_stocks))
    for s in sell_stocks:
        s["direction_label"] = "卖出"
        s["action_icon"] = "卖出"
        if s["direction_score"] > 0:
            s["direction_reason"] = "全局排名末10位，综合评分偏向"

    seen_all = {s["code"] for s in buy_stocks + sell_stocks}
    avoid_pool = [s for s in ranked if s["code"] not in seen_all]
    if len(avoid_pool) < 10:
        overflow = [s for s in ranked if s["code"] not in seen_all]
        avoid_pool = overflow[:10]
    avoid_stocks = avoid_pool[:10]
    if len(avoid_stocks) < 10:
        all_seen = set(seen_all)
        fill = [s for s in ranked if s["code"] not in all_seen][:10 - len(avoid_stocks)]
        avoid_stocks.extend(fill)
    for s in avoid_stocks:
        s["direction_label"] = "回避"
        s["action_icon"] = "回避"
        s["direction_reason"] = "全局排名居中，方向不明朗"

    winrate = calculate_win_rate(dominant_wx, "mixed")

    return {
        "buy_stocks": buy_stocks,
        "sell_stocks": sell_stocks,
        "avoid_stocks": avoid_stocks,
        "total_picks": len(buy_stocks) + len(sell_stocks) + len(avoid_stocks),
        "dominant_wuxing": dominant_wx,
        "boost_level": boost_level,
        "boost_detail": boost["detail"],
        "avg_sentiment": round(avg_news_sentiment, 2),
        "term": boost.get("term", {}),
        "ganzhi": boost.get("ganzhi", {}),
        "win_rate": winrate,
        "industries_covered": sorted(all_industries)[:15],
    }


def _classify_stock_wuxing(stock: dict) -> str:
    """根据股票所属行业判断五行"""
    industry = stock.get("matched_industry", "")
    for wx, info in WUXING_INDUSTRY_MAP.items():
        if industry in info["industries"]:
            return wx
    return "未匹配"


def _calc_stock_direction(stock_wx: str, dominant_wx: str, boost_level: str, avg_sentiment: float) -> dict:
    """综合五行生克+气场+情绪 计算单只股票的多空方向"""

    # 五行生克分数
    if stock_wx == dominant_wx:
        wx_score = 0.3 if boost_level in ("增强", "当令") else 0.1
    elif dominant_wx in WUXING_SHENG and WUXING_SHENG[dominant_wx] == stock_wx:
        wx_score = 0.2
    elif dominant_wx in WUXING_KE and WUXING_KE[dominant_wx] == stock_wx:
        wx_score = -0.3
    else:
        wx_score = 0.0

    # 气场修正
    boost_dict = {"增强": 0.4, "当令": 0.3, "中性": 0.0, "轻微削弱": -0.2, "削弱": -0.4}
    boost_bonus = boost_dict.get(boost_level, 0)

    # 综合分 = 生克×0.4 + 气场×0.3 + 情绪×0.3
    total = wx_score * 0.4 + boost_bonus * 0.3 + avg_sentiment * 0.3

    if total > 0.4:
        label = "买入"
        reason = "五行共振+气场支持，多头信号明确"
    elif total > 0.15:
        label = "买入"
        reason = "五行有利，震荡偏多"
    elif total < -0.3:
        label = "卖出"
        reason = "五行受克+气场压制，空头信号明确"
    elif total < -0.05:
        label = "卖出"
        reason = "五行不利，震荡偏空"
    else:
        label = "回避"
        reason = "五行气场中性，方向不明朗"

    return {"score": round(total, 3), "label": label, "reason": reason}


# ============================================================
# 生成完整日推报告
# ============================================================
def generate_daily_report() -> dict:
    """生成当天完整日推报告（股票三栏 + 期货三栏 + 期权）"""

    news_list = fetch_and_parse(max_items=30)
    stock_report = pick_30_stocks_china(news_list)
    futures_report = pick_china_futures_categorized(news_list, stock_report["dominant_wuxing"], stock_report["boost_level"])

    sentiments = [n.get("sentiment_score", 0) for n in news_list if n.get("wuxing") != "未匹配"]
    median_sentiment = sorted(sentiments)[len(sentiments)//2] if sentiments else 0.0

    term = get_current_solar_term()
    sandiao = _pick_sandiao(stock_report["boost_level"])

    report = {
        "report_id": datetime.now().strftime("%Y%m%d"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market": "A股",
        "news_sources": len(news_list),
        "news_cache_age_sec": round(get_cache_age(), 0),
        "market_sentiment": round(median_sentiment, 2),
        "term": term,
        "dominant_wuxing": stock_report["dominant_wuxing"],
        "boost_level": stock_report["boost_level"],
        "boost_detail": stock_report["boost_detail"],
        "ganzhi": stock_report.get("ganzhi", {}).get("day_ganzhi", ""),
        "score_weights": SCORE_WEIGHTS,
        "buy_stocks": stock_report["buy_stocks"],
        "sell_stocks": stock_report["sell_stocks"],
        "avoid_stocks": stock_report["avoid_stocks"],
        "stock_count": stock_report["total_picks"],
        "buy_futures": futures_report["buy_futures"],
        "sell_futures": futures_report["sell_futures"],
        "avoid_futures": futures_report["avoid_futures"],
        "futures_count": futures_report["total_count"],
        "options_summary": futures_report.get("options_summary", {}),
        "win_rate": stock_report["win_rate"],
        "sandiao": sandiao,
        "risk_warning": RISK_WARNING,
        "disclaimer": "玄学有风险，梭哈需谨慎。本报告仅供娱乐，不构成任何投资建议。",
    }

    with _DAILY_STATE["lock"]:
        _DAILY_STATE["today_report"] = report
        _DAILY_STATE["last_report_time"] = datetime.now()

    save_report_to_file(report)
    save_event_log({
        "type": "daily_report_cn",
        "timestamp": datetime.now().isoformat(),
        "report_id": report["report_id"],
        "stocks": f"B{len(report['buy_stocks'])}/S{len(report['sell_stocks'])}/A{len(report['avoid_stocks'])}",
        "dominant_wuxing": report["dominant_wuxing"],
    })
    return report


def _pick_sandiao(boost_level: str) -> str:
    """根据气场选一条沙雕语"""
    from config import SHADIAO_QUOTES
    quotes_map = {
        "增强": ["🔥 今天的A股，老天爷都在给你递钱！", "💰 五行全开，这波不冲就是亏！"],
        "当令": ["🏠 主场作战，A股这波稳如老韭菜！", "🛋️ 坐等抬轿，别人恐慌我贪婪！"],
        "削弱": ["🍉 今日A股不宜重仓，宜吃瓜看戏！", "⚠️ 多头进去骨灰出来，管住手！"],
        "轻微削弱": ["🤔 A股方向不明，多看少动保平安！", "🌊 风浪越大鱼越贵，但鱼也可能吃你！"],
        "中性": ["🤷 A股今天也懵了，你看着办吧！", "🔮 天机不可泄露……其实AI也没算出来！"],
    }
    pool = quotes_map.get(boost_level, quotes_map["中性"])
    return random.choice(pool)


def save_report_to_file(report: dict):
    date_str = report["report_id"]
    filepath = REPORTS_DIR / f"daily_{date_str}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return str(filepath)


def load_today_report() -> dict:
    with _DAILY_STATE["lock"]:
        if _DAILY_STATE["today_report"]:
            return _DAILY_STATE["today_report"]
    date_str = datetime.now().strftime("%Y%m%d")
    filepath = REPORTS_DIR / f"daily_{date_str}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            report = json.load(f)
            _DAILY_STATE["today_report"] = report
            return report
    return None


def load_historical_reports(days: int = 7) -> list:
    reports = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        filepath = REPORTS_DIR / f"daily_{date.strftime('%Y%m%d')}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                reports.append(json.load(f))
    return reports


def get_daily_state() -> dict:
    with _DAILY_STATE["lock"]:
        return {
            "last_report_time": _DAILY_STATE["last_report_time"].strftime("%Y-%m-%d %H:%M:%S") if _DAILY_STATE["last_report_time"] else None,
            "has_today_report": _DAILY_STATE["today_report"] is not None,
            "is_running": _DAILY_STATE["is_running"],
            "cache_age_sec": round(get_cache_age(), 0),
        }


def start_auto_refresh(interval_minutes: int = 5):
    def _refresh_loop():
        while True:
            time.sleep(interval_minutes * 60)
            try:
                force_refresh()
                fetch_and_parse(max_items=20)
            except Exception:
                pass
    thread = threading.Thread(target=_refresh_loop, daemon=True)
    thread.start()
    return thread


def analyze_custom_news(news_text: str) -> dict:
    """用户自定义新闻分析"""
    from news_fetcher import parse_news
    parsed = parse_news({"title": "", "content": news_text})
    boost = analyze_wuxing_boost(parsed["wuxing"])
    stocks = pick_stocks(parsed["industries"], parsed["wuxing"], "A股", max_picks=10)
    futures = pick_china_futures_categorized([parsed], parsed["wuxing"], boost["boost_level"])
    winrate = calculate_win_rate(parsed["wuxing"], parsed["event_type"])

    from reporter import build_report
    report = build_report(parsed, boost, stocks, futures, None, winrate)
    return report
