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
from policy_analyzer import (get_policy_score, get_boost_level_from_policy,
                            generate_policy_summary, generate_global_summary, get_global_impact,
                            get_sensitive_bonus, get_long_track_bonus,
                            summarize_fire_sensitive, summarize_earth_tracks,
                            POLICY_REFERENCE_INDEX, APRIL_PERFORMANCE,
                            get_rotation_bonus, summarize_monthly_rotation)
from reporter import SCORE_WEIGHTS
from pro_recommendations import get_consensus_bonus, get_pro_recommendation
from options_picker import PRO_OPTION_STRATEGIES, STOP_LOSS_DISCIPLINE
from bazi_capacity import (get_capacity_score_for_scoring, IPO_DATE_MAP,
                           get_market_annual_assessment, get_chang_sheng,
                           get_riyuan_from_ipo, get_trade_day_info,
                           CHANG_SHENG_TABLE, STAGE_NAMES, CAPACITY_SCORES)
from wuxing_timing import (get_timing_for_stock, get_timing_signal_bonus,
                          summarize_timing, get_may_event_summary)


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
        stock_industry = stock.get("matched_industry", "")
        stock_code = stock.get("code", "")
        ipo_date = IPO_DATE_MAP.get(stock_code, "1990-01-01")
        riyuan = get_riyuan_from_ipo(ipo_date)
        trade_info = get_trade_day_info(datetime.now().strftime("%Y-%m-%d"))
        chang_sheng = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])
        capacity_score = chang_sheng["capacity_score"]
        stock_direction = _calc_stock_direction(stock_wx, dominant_wx, boost_level,
                                                avg_news_sentiment, stock_industry,
                                                stock_code)
        stock["wuxing"] = stock_wx
        stock["direction_score"] = stock_direction["score"]
        stock["direction_label"] = stock_direction["label"]
        stock["direction_reason"] = stock_direction["reason"]
        stock["ipo_date"] = ipo_date
        stock["riyuan_gan"] = riyuan["gan"]
        stock["riyuan_zhi"] = riyuan["zhi"]
        stock["chang_sheng_stage"] = chang_sheng["stage_index"]
        stock["chang_sheng_name"] = chang_sheng["stage_name"]
        stock["capacity_score"] = capacity_score

        timing = get_timing_for_stock(stock_code, stock.get("name", ""))
        stock["timing_signal"] = timing["signal"]
        stock["star_display"] = timing["star_display"]
        stock["stars"] = timing["stars"]
        stock["expected_range"] = timing["expected_range"]
        stock["option_hint"] = timing["option_hint"]

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


def _calc_stock_direction(stock_wx: str, dominant_wx: str, boost_level: str,
                         avg_sentiment: float, stock_industry: str = "",
                         stock_code: str = "") -> dict:
    """综合五行生克+气场+情绪+政策+机构共识 计算单只股票的多空方向"""

    wx_score = 0.0
    if stock_wx == dominant_wx:
        wx_score = 0.3 if boost_level in ("增强", "当令", "旺相") else 0.1
    elif dominant_wx in WUXING_SHENG and WUXING_SHENG[dominant_wx] == stock_wx:
        wx_score = 0.2
    elif dominant_wx in WUXING_KE and WUXING_KE[dominant_wx] == stock_wx:
        wx_score = -0.3

    boost_dict = {"增强": 0.4, "当令": 0.3, "旺相": 0.35, "中性": 0.0, "平和": 0.0, "轻微削弱": -0.2, "削弱": -0.4}
    boost_bonus = boost_dict.get(boost_level, 0)

    policy_score, matched_policies = get_policy_score(stock_industry, stock_wx, dominant_wx)

    consensus_bonus = get_consensus_bonus(stock_code)
    sensitive_bonus = get_sensitive_bonus(stock_code)
    long_track_bonus = get_long_track_bonus(stock_code)
    capacity_score = get_capacity_score_for_scoring(stock_code, IPO_DATE_MAP)
    rotation_bonus = get_rotation_bonus(stock_code)
    timing_bonus = get_timing_signal_bonus(
        get_timing_for_stock(stock_code).get("signal", "等")
    )

    total = (wx_score * 0.14 + boost_bonus * 0.12 + avg_sentiment * 0.10
             + policy_score * 0.14 + consensus_bonus * 0.09
             + sensitive_bonus * 0.04 + long_track_bonus * 0.03
             + capacity_score * 0.15 + rotation_bonus * 0.08
             + timing_bonus * 0.11)

    if total > 0.35:
        label = "买入"
        reason = "五星共振+政策加持+机构共识，多头信号明确"
    elif total > 0.12:
        label = "买入"
        reason = "综合评分偏多，政策面有支撑"
    elif total < -0.25:
        label = "卖出"
        reason = "五行受克+政策不利，空头信号明确"
    elif total < -0.04:
        label = "卖出"
        reason = "综合评分偏空，缺乏政策支撑"
    else:
        label = "回避"
        reason = "多空交织，方向不明朗"

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
        "policy_boost_level": get_boost_level_from_policy(stock_report["dominant_wuxing"]),
        "policy_summary": generate_policy_summary(),
        "global_summary": generate_global_summary(),
        "global_impact": get_global_impact(),
        "fire_sensitive_summary": summarize_fire_sensitive(),
        "earth_tracks_summary": summarize_earth_tracks(),
        "monthly_rotation_summary": summarize_monthly_rotation(),
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
        "pro_option_strategies": PRO_OPTION_STRATEGIES,
        "stop_loss_discipline": STOP_LOSS_DISCIPLINE,
        "win_rate": stock_report["win_rate"],
        "sandiao": sandiao,
        "risk_warning": RISK_WARNING,
        "annual_assessment": get_market_annual_assessment(),
        "may_events": get_may_event_summary(),
        "policy_reference_index": POLICY_REFERENCE_INDEX,
        "april_performance": APRIL_PERFORMANCE,
        "disclaimer": "本报告仅为基于宏观政策与公开信息的逻辑推演和整理呈现，不构成任何形式的投资建议、买卖指令或证券推荐。市场风险莫测，投资须怀敬畏之心。",
    }

    report["timing_summary"] = summarize_timing(report)

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
