# -*- coding: utf-8 -*-
"""
全球期货推荐引擎 v2.0
- 全球期货：CME(原油/黄金/铜/农产品), LME(金属), ICE(软商品), SGX(铁矿石)
- 中国期货：上期所/大商所/郑商所/中金所
- 每只期货给出：买/卖/观望 + 方向理由 + 全球关联分析 + 入场区间 + 止损位
- 每天推荐5只期货
"""

import random
from datetime import datetime

from config import (
    FUTURES_WUXING_MAP, SIMULATE_MODE, WUXING_KE, WUXING_SHENG,
    get_sandiao_quote,
)

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


# ============================================================
# 全球期货品种池
# ============================================================
GLOBAL_FUTURES_POOL = {
    "CME": [
        {"name": "WTI原油", "symbol": "CL", "wuxing": "火", "unit": "1000桶", "exchange": "NYMEX", "active_hours": "几乎24小时"},
        {"name": "布伦特原油", "symbol": "BZ", "wuxing": "火", "unit": "1000桶", "exchange": "ICE", "active_hours": "几乎24小时"},
        {"name": "天然气", "symbol": "NG", "wuxing": "火", "unit": "10000MMBtu", "exchange": "NYMEX", "active_hours": "几乎24小时"},
        {"name": "黄金", "symbol": "GC", "wuxing": "金", "unit": "100盎司", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "白银", "symbol": "SI", "wuxing": "金", "unit": "5000盎司", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "铜", "symbol": "HG", "wuxing": "金", "unit": "25000磅", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "大豆", "symbol": "ZS", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "玉米", "symbol": "ZC", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "小麦", "symbol": "ZW", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "棉花", "symbol": "CT", "wuxing": "木", "unit": "50000磅", "exchange": "ICE", "active_hours": "日盘"},
        {"name": "糖", "symbol": "SB", "wuxing": "木", "unit": "112000磅", "exchange": "ICE", "active_hours": "日盘"},
        {"name": "咖啡", "symbol": "KC", "wuxing": "木", "unit": "37500磅", "exchange": "ICE", "active_hours": "日盘"},
    ],
    "LME": [
        {"name": "LME铜", "symbol": "CA", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
        {"name": "LME铝", "symbol": "AH", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
        {"name": "LME镍", "symbol": "NI", "wuxing": "金", "unit": "6吨", "exchange": "LME"},
        {"name": "LME锌", "symbol": "ZS", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
    ],
}

CHINA_FUTURES_POOL = {
    "上期所": [
        {"name": "沪金", "symbol": "AU", "wuxing": "金", "unit": "1000克/手", "margin": "约4万/手"},
        {"name": "沪银", "symbol": "AG", "wuxing": "金", "unit": "15千克/手", "margin": "约1万/手"},
        {"name": "沪铜", "symbol": "CU", "wuxing": "金", "unit": "5吨/手", "margin": "约3.5万/手"},
        {"name": "螺纹钢", "symbol": "RB", "wuxing": "金", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "原油", "symbol": "SC", "wuxing": "火", "unit": "1000桶/手", "margin": "约6万/手"},
        {"name": "燃料油", "symbol": "FU", "wuxing": "火", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "沥青", "symbol": "BU", "wuxing": "火", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "橡胶", "symbol": "RU", "wuxing": "土", "unit": "10吨/手", "margin": "约1.2万/手"},
    ],
    "大商所": [
        {"name": "铁矿石", "symbol": "I", "wuxing": "土", "unit": "100吨/手", "margin": "约1万/手"},
        {"name": "焦炭", "symbol": "J", "wuxing": "火", "unit": "100吨/手", "margin": "约3万/手"},
        {"name": "豆粕", "symbol": "M", "wuxing": "木", "unit": "10吨/手", "margin": "约2500/手"},
        {"name": "玉米", "symbol": "C", "wuxing": "木", "unit": "10吨/手", "margin": "约1500/手"},
        {"name": "棕榈油", "symbol": "P", "wuxing": "木", "unit": "10吨/手", "margin": "约6000/手"},
        {"name": "聚丙烯", "symbol": "PP", "wuxing": "土", "unit": "5吨/手", "margin": "约3500/手"},
    ],
    "郑商所": [
        {"name": "PTA", "symbol": "TA", "wuxing": "土", "unit": "5吨/手", "margin": "约2000/手"},
        {"name": "甲醇", "symbol": "MA", "wuxing": "水", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "纯碱", "symbol": "SA", "wuxing": "水", "unit": "20吨/手", "margin": "约4000/手"},
        {"name": "白糖", "symbol": "SR", "wuxing": "木", "unit": "10吨/手", "margin": "约4000/手"},
        {"name": "棉花", "symbol": "CF", "wuxing": "木", "unit": "5吨/手", "margin": "约5000/手"},
        {"name": "尿素", "symbol": "UR", "wuxing": "水", "unit": "20吨/手", "margin": "约4000/手"},
    ],
}


# ============================================================
# 买入/抛出判断逻辑
# ============================================================
def _evaluate_direction(wuxing: str, boost_level: str, sentiment: float, region: str) -> dict:
    """综合五行气场+情绪+区域给出买入/卖出判断"""

    # 五行气场评分
    boost_scores = {"增强": 0.8, "当令": 0.6, "中性": 0.3, "轻微削弱": -0.2, "削弱": -0.5}
    boost_score = boost_scores.get(boost_level, 0.0)

    # 综合方向分 = 情绪×0.4 + 五行×0.4 + 区域×0.2
    region_bias = 0.1 if region == "中国" else (-0.05 if region == "美国" else 0.0)
    total = sentiment * 0.4 + boost_score * 0.4 + region_bias * 0.2

    if total > 0.3:
        direction = "买入" if total > 0.5 else "轻仓买入"
        confidence = min(90, int(50 + total * 50))
        entry_signal = "突破前高确认后入场" if total > 0.5 else "回调至支撑位附近轻仓试多"
    elif total < -0.2:
        direction = "卖出" if total < -0.4 else "轻仓卖出"
        confidence = min(90, int(50 + abs(total) * 50))
        entry_signal = "跌破支撑位确认后入场" if total < -0.4 else "反弹至阻力位附近轻仓试空"
    else:
        direction = "观望"
        confidence = 30
        entry_signal = "等待方向明确"

    return {
        "direction": direction,
        "confidence": confidence,
        "entry_signal": entry_signal,
        "total_score": round(total, 3),
    }


def _generate_price_analysis(contract: dict, direction: str) -> dict:
    """生成价格分析（入场区间/止损/目标）"""
    if direction in ("买入", "轻仓买入"):
        entry = "建议回调至5日/10日均线附近分批入场"
        stop_loss = "跌破20日均线或前低2%止损"
        target = "前高附近分批止盈，第二目标看突破前高"
    elif direction in ("卖出", "轻仓卖出"):
        entry = "建议反弹至5日/10日均线附近分批入场"
        stop_loss = "突破20日均线或前高2%止损"
        target = "前低附近分批止盈，第二目标看跌破前低"
    else:
        entry = "暂不入场，等待信号"
        stop_loss = "N/A"
        target = "N/A"

    return {"entry_zone": entry, "stop_loss": stop_loss, "target": target, "risk_reward": "约1:2 ~ 1:3" if direction != "观望" else "N/A"}


# ============================================================
# 核心推荐函数
# ============================================================
def pick_global_futures(news_list: list, max_picks: int = 5) -> list:
    """基于全球新闻筛选推荐期货品种（买入/卖出+理由）"""

    # 汇总新闻中的五行分布和情绪
    wuxing_signals = {}
    for news in news_list:
        wx = news.get("wuxing", "")
        sentiment = news.get("sentiment_score", 0)
        region = news.get("region", "全球")
        event = news.get("event_type", "")

        if wx and wx != "未匹配":
            if wx not in wuxing_signals:
                wuxing_signals[wx] = {"total_sentiment": 0.0, "count": 0, "regions": [], "events": []}
            wuxing_signals[wx]["total_sentiment"] += sentiment
            wuxing_signals[wx]["count"] += 1
            wuxing_signals[wx]["regions"].append(region)
            wuxing_signals[wx]["events"].append(event)

    # 从全局期货池中匹配
    candidates = []
    all_global = []
    for exchange, contracts in GLOBAL_FUTURES_POOL.items():
        all_global.extend(contracts)

    for contract in all_global:
        wx = contract["wuxing"]
        if wx in wuxing_signals:
            sig = wuxing_signals[wx]
            avg_sentiment = sig["total_sentiment"] / sig["count"]
            regions = list(set(sig["regions"]))

            # 分析买入/卖出
            eval_result = _evaluate_direction(wx, "中性", avg_sentiment, regions[0] if regions else "全球")
            price_analysis = _generate_price_analysis(contract, eval_result["direction"])

            # 全球关联逻辑
            global_logic = _build_global_logic(contract, sig["events"], regions, avg_sentiment)

            candidates.append({
                "name": contract["name"],
                "symbol": contract["symbol"],
                "exchange": contract.get("exchange", ""),
                "wuxing": wx,
                "unit": contract.get("unit", ""),
                "direction": eval_result["direction"],
                "confidence": eval_result["confidence"],
                "entry_signal": eval_result["entry_signal"],
                "score": eval_result["total_score"],
                "price_analysis": price_analysis,
                "global_logic": global_logic,
                "sentiment": round(avg_sentiment, 2),
            })

    # 按综合评分排序
    candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    return candidates[:max_picks]


def pick_china_futures(boost_level: str, wuxing: str, news_list: list, max_picks: int = 3) -> list:
    """基于中国新闻+五行气场推荐中国期货品种"""

    # 从五行映射中获取品种
    mapped_contracts = FUTURES_WUXING_MAP.get(wuxing, {}).get("contracts", [])

    candidates = []
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            if c["wuxing"] == wuxing or c["name"] in mapped_contracts:
                sentiment = 0.3 if boost_level in ("增强", "当令") else (-0.3 if "削弱" in boost_level else 0.0)

                eval_result = _evaluate_direction(wuxing, boost_level, sentiment, "中国")
                price_analysis = _generate_price_analysis(c, eval_result["direction"])

                # 中国特色分析
                china_logic = _build_china_logic(c, boost_level, news_list)

                candidates.append({
                    "name": c["name"],
                    "symbol": c["symbol"],
                    "exchange": exchange,
                    "wuxing": wuxing,
                    "unit": c.get("unit", ""),
                    "margin": c.get("margin", ""),
                    "direction": eval_result["direction"],
                    "confidence": eval_result["confidence"],
                    "entry_signal": eval_result["entry_signal"],
                    "score": eval_result["total_score"],
                    "price_analysis": price_analysis,
                    "china_logic": china_logic,
                    "boost": boost_level,
                })

    candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    return candidates[:max_picks]


def pick_china_futures_categorized(news_list: list, dominant_wx: str, boost_level: str) -> dict:
    """纯中国期货推荐：按买入/卖出/回避分类"""

    # 中国期货全池
    all_contracts = []
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            all_contracts.append({**c, "exchange": exchange})

    # 汇总新闻基于每个五行的情绪
    wx_sentiments = {}
    for news in news_list:
        wx = news.get("wuxing", "")
        sentiment = news.get("sentiment_score", 0)
        if wx and wx != "未匹配":
            if wx not in wx_sentiments:
                wx_sentiments[wx] = []
            wx_sentiments[wx].append(sentiment)

    avg_sentiments = {wx: sum(s)/len(s) for wx, s in wx_sentiments.items()} if wx_sentiments else {}

    buy_candidates = []
    sell_candidates = []
    avoid_candidates = []

    for c in all_contracts:
        wx = c["wuxing"]
        sentiment = avg_sentiments.get(wx, 0.0)
        eval_result = _evaluate_direction(wx, boost_level, sentiment, "中国")
        price_analysis = _generate_price_analysis(c, eval_result["direction"])
        china_logic = _build_china_logic(c, boost_level, news_list)

        entry = {
            "name": c["name"],
            "symbol": c["symbol"],
            "exchange": c.get("exchange", ""),
            "wuxing": wx,
            "unit": c.get("unit", ""),
            "margin": c.get("margin", ""),
            "direction": eval_result["direction"],
            "confidence": eval_result["confidence"],
            "entry_signal": eval_result["entry_signal"],
            "score": eval_result["total_score"],
            "price_analysis": price_analysis,
            "china_logic": china_logic,
            "boost": boost_level,
        }

        direction = eval_result["direction"]
        if direction in ("买入", "轻仓买入"):
            buy_candidates.append(entry)
        elif direction in ("卖出", "轻仓卖出"):
            sell_candidates.append(entry)
        else:
            avoid_candidates.append(entry)

    buy_candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    sell_candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    avoid_candidates.sort(key=lambda x: abs(x["score"]))

    buy_futures = buy_candidates[:5]
    sell_futures = sell_candidates[:5]
    avoid_futures = avoid_candidates[:5]

    # 如果不够，从其他分组借
    if len(buy_futures) < 3:
        pool = avoid_candidates + sell_candidates
        pool.sort(key=lambda x: x["score"], reverse=True)
        for p in pool:
            if p not in buy_futures:
                p["direction"] = "买入"
                p["entry_signal"] = "经综合评分调整，建议轻仓试多"
                buy_futures.append(p)
                if len(buy_futures) >= 5:
                    break

    if len(sell_futures) < 3:
        pool = avoid_candidates + buy_candidates
        pool.sort(key=lambda x: x["score"])
        for p in pool:
            if p not in sell_futures and p not in buy_futures:
                p["direction"] = "卖出"
                p["entry_signal"] = "经综合评分调整，建议轻仓试空"
                sell_futures.append(p)
                if len(sell_futures) >= 5:
                    break

    total = len(buy_futures) + len(sell_futures) + len(avoid_futures)

    # 期权简要
    options_summary = _build_china_options_summary(buy_futures, sell_futures, boost_level)

    return {
        "buy_futures": buy_futures[:5],
        "sell_futures": sell_futures[:5],
        "avoid_futures": avoid_futures[:5],
        "total_count": total,
        "options_summary": options_summary,
    }


def _build_china_options_summary(buy_futures: list, sell_futures: list, boost_level: str) -> dict:
    """生成中国期权策略摘要"""
    strategies = {
        "增强": "买Call + 牛市价差",
        "当令": "卖Put收租 + 买Call",
        "削弱": "买Put + 熊市价差",
        "轻微削弱": "保护性Put + 铁鹰",
        "中性": "蝶式 + 铁鹰 + 卖跨",
    }
    strategy = strategies.get(boost_level, "观望")

    targets = []
    for f in buy_futures[:2]:
        if "金" in f["name"] or "银" in f["name"] or "铜" in f["name"]:
            targets.append(f"{f['name']}期权 — 买Call，博波动率")
    for f in sell_futures[:2]:
        if "金" in f["name"] or "螺纹" in f["name"] or "铁矿石" in f["name"]:
            targets.append(f"{f['name']}期权 — 买Put，对冲下行")

    return {
        "strategy": strategy,
        "suggested_targets": targets if targets else ["沪金期权", "沪铜期权", "铁矿石期权"],
        "note": "期权跟随标的五行，可用价差组合控制风险",
    }



def _build_global_logic(contract: dict, events: list, regions: list, sentiment: float) -> str:
    """构建全球期货关联逻辑"""
    parts = []
    name = contract["name"]
    wx = contract["wuxing"]

    if events:
        parts.append(f"触发事件：{'、'.join(events[:3])}")
    if regions:
        parts.append(f"影响区域：{'、'.join(set(regions))}")
    if sentiment > 0.3:
        parts.append(f"全球情绪偏多")
    elif sentiment < -0.3:
        parts.append(f"全球情绪偏空")
    else:
        parts.append("情绪中性")

    # 全球关联
    if "原油" in name or "oil" in name.lower():
        parts.append("联动：中东地缘→油价→通胀→美联储政策→美元→全球风险资产")
    elif "gold" in name.lower() or "金" in name:
        parts.append("联动：避险情绪→金价→实际利率→美元指数→央行购金")
    elif "铜" in name or "copper" in name.lower():
        parts.append("联动：全球经济预期→铜博士→制造业PMI→基建投资")
    elif "大豆" in name or "玉米" in name or "小麦" in name:
        parts.append("联动：天气→产量→USDA报告→贸易流→通胀预期")

    return "；".join(parts)


def _build_china_logic(contract: dict, boost_level: str, news_list: list) -> str:
    """构建中国期货特色分析"""
    name = contract["name"]
    wx = contract["wuxing"]

    if boost_level in ("增强", "当令"):
        wx_status = f"五行「{wx}」{boost_level}，周期有利"
    elif "削弱" in boost_level:
        wx_status = f"五行「{wx}」{boost_level}，周期不利"
    else:
        wx_status = f"五行「{wx}」中性"

    # 中国特色
    china_specific = ""
    if "螺纹" in name or "铁矿石" in name:
        china_specific = "国内基建开工率+房地产新开工数据是关键驱动"
    elif "豆粕" in name or "玉米" in name:
        china_specific = "进口依存度高，关注中美贸易和南美天气"
    elif "金" in name or "银" in name:
        china_specific = "人民币汇率影响沪金溢价，央行增持是中长期支撑"
    elif "原油" in name:
        china_specific = "国内需求恢复+OPEC政策，SC与Brent价差反映区域供需"

    return f"{wx_status}。{china_specific}"


# ============================================================
# 兼容旧接口
# ============================================================
def pick_futures(wuxing: str, boost_level: str, max_picks: int = 3) -> dict:
    """旧接口兼容：简版期货推荐"""
    contracts = FUTURES_WUXING_MAP.get(wuxing, {}).get("contracts", [])
    direction_map = {"增强": "做多", "当令": "做多", "削弱": "做空", "轻微削弱": "观望偏空", "中性": "观望"}

    picks = []
    for contract_name in contracts[:max_picks]:
        direction = direction_map.get(boost_level, "观望")
        picks.append({
            "name": contract_name,
            "wuxing": wuxing,
            "direction": direction,
            "symbol": contract_name,
            "basis": "实时价" if not SIMULATE_MODE else "模拟价",
            "open_interest": "实时" if not SIMULATE_MODE else "模拟持仓",
        })

    return {
        "futures": picks,
        "base_direction": direction_map.get(boost_level, "观望"),
        "wuxing": wuxing,
        "logic": f"五行「{wuxing}」当前{boost_level}",
    }
