# -*- coding: utf-8 -*-
"""
股票推荐引擎
支持 A股/美股/港股，输出标的、逻辑推导、上下游分析、PE/PB估值、实时股价、总市值
"""

from datetime import datetime
from config import (
    STOCK_POOL, SUPPLY_CHAIN, SIMULATE_MODE,
    WUXING_INDUSTRY_MAP,
)

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False


def pick_stocks(
    industries: list,
    wuxing: str,
    market: str = "A股",
    max_picks: int = 5,
) -> dict:
    """根据行业、五行、市场筛选推荐股票"""

    candidates = []
    pool = STOCK_POOL.get(market, {})
    seen_codes = set()

    for industry in industries:
        if industry in pool:
            for stock in pool[industry]:
                code = stock["code"]
                if code not in seen_codes:
                    seen_codes.add(code)
                    candidates.append({**stock, "matched_industry": industry})

    # 如果候选不够，尝试从五行映射的行业补充
    if len(candidates) < 2 and wuxing in WUXING_INDUSTRY_MAP:
        wuxing_industries = WUXING_INDUSTRY_MAP[wuxing]["industries"]
        for ind in wuxing_industries:
            if ind in pool:
                for stock in pool[ind]:
                    code = stock["code"]
                    if code not in seen_codes:
                        seen_codes.add(code)
                        candidates.append({**stock, "matched_industry": ind})

    top = candidates[:max_picks]

    # 获取实时价格（模拟模式下跳过）
    if not SIMULATE_MODE:
        top = enrich_with_realtime(top, market)

    # 添加上下游分析
    for stock in top:
        industry = stock.get("matched_industry", "")
        if industry in SUPPLY_CHAIN:
            stock["supply_chain"] = SUPPLY_CHAIN[industry]
        else:
            stock["supply_chain"] = {"upstream": ["数据缺失"], "midstream": ["数据缺失"], "downstream": ["数据缺失"]}

    logic = build_stock_logic(industries, wuxing, market)

    return {
        "stocks": top,
        "market": market,
        "logic": logic,
        "total_matched": len(candidates),
    }


def enrich_with_realtime(stocks: list, market: str) -> list:
    """用实时数据更新股票信息"""
    if market == "美股":
        return enrich_us(stocks)
    elif market == "A股":
        return enrich_a_shares(stocks)
    return stocks


def enrich_us(stocks: list) -> list:
    """通过 yfinance 获取美股实时数据"""
    if not HAS_YFINANCE:
        return stocks
    for stock in stocks:
        code = stock.get("code", "")
        try:
            ticker = yf.Ticker(code)
            info = ticker.info or {}
            stock["realtime_price"] = info.get("currentPrice") or info.get("regularMarketPrice")
            stock["realtime_pe"] = info.get("trailingPE")
            stock["realtime_pb"] = info.get("priceToBook")
            stock["market_cap"] = info.get("marketCap")
            stock["data_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        except Exception:
            stock["realtime_price"] = "获取失败"
    return stocks


def enrich_a_shares(stocks: list) -> list:
    """通过 akshare 获取 A 股实时数据"""
    if not HAS_AKSHARE:
        return stocks
    try:
        df = ak.stock_zh_a_spot_em()
        df_dict = df.set_index("代码").to_dict("index")
        for stock in stocks:
            code = stock.get("code", "")
            if code in df_dict:
                row = df_dict[code]
                stock["realtime_price"] = row.get("最新价")
                stock["realtime_pe"] = row.get("市盈率-动态")
                stock["realtime_pb"] = row.get("市净率")
                stock["market_cap"] = row.get("总市值")
                stock["data_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    except Exception:
        for stock in stocks:
            stock["realtime_price"] = "获取失败"
    return stocks


def build_stock_logic(industries: list, wuxing: str, market: str) -> str:
    """构建股票推荐的逻辑说明"""
    parts = []
    if industries:
        parts.append(f"新闻涉及行业：{'、'.join(industries[:5])}")
    if wuxing:
        parts.append(f"五行属性：{wuxing}")
    parts.append(f"市场：{market}")
    return "；".join(parts)


def get_supply_chain_analysis(industry: str) -> dict:
    """获取某行业的上下游产业链分析"""
    return SUPPLY_CHAIN.get(industry, {"upstream": [], "midstream": [], "downstream": []})
