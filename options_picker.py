# -*- coding: utf-8 -*-
"""
期权策略引擎
基于推荐股票/期货标的，给出期权策略（买Call/Put、价差组合）
计算隐含波动率、希腊字母简要、建议合约月份
"""

import math
from config import SIMULATE_MODE, SHADIAO_QUOTES


OPTION_STRATEGIES = {
    "增强": {
        "aggressive": "买入看涨期权 (Long Call)",
        "moderate": "牛市看涨价差 (Bull Call Spread)",
        "description": "预期标的上涨，用期权杠杆放大收益",
    },
    "当令": {
        "aggressive": "卖出看跌期权 (Short Put)",
        "moderate": "备兑看涨 (Covered Call) 或 买入看涨",
        "description": "标的趋势明确，可收租或顺势",
    },
    "削弱": {
        "aggressive": "买入看跌期权 (Long Put)",
        "moderate": "熊市看跌价差 (Bear Put Spread)",
        "description": "预期标的下跌，用Put对冲或做空",
    },
    "轻微削弱": {
        "aggressive": "熊市看跌价差 (Bear Put Spread)",
        "moderate": "保护性看跌 (Protective Put)",
        "description": "偏空但不确定，用价差限制风险",
    },
    "中性": {
        "aggressive": "蝶式价差 (Butterfly Spread)",
        "moderate": "铁鹰策略 (Iron Condor) 或 跨式卖出 (Short Straddle)",
        "description": "预期震荡，赚取时间价值",
    },
}


def pick_options(boost_level: str, underlying_stocks: list, risk_level: str = "moderate") -> dict:
    """根据增强/削弱级别和标的股票推荐期权策略"""

    strategy_config = OPTION_STRATEGIES.get(boost_level, OPTION_STRATEGIES["中性"])
    strategy = strategy_config.get(risk_level, strategy_config.get("moderate", "观望"))

    # 计算IV（模拟模式下估算）
    iv = estimate_iv(boost_level, underlying_stocks)

    # 希腊字母简要
    greeks = estimate_greeks(boost_level, risk_level)

    # 建议合约月份
    suggested_month = suggest_contract_month()

    picks = []
    for stock in underlying_stocks[:3]:
        picks.append({
            "underlying": stock.get("name", stock.get("code", "")),
            "underlying_code": stock.get("code", ""),
            "strategy": strategy,
            "iv_estimate": iv,
            "greeks": greeks,
            "suggested_month": suggested_month,
        })

    return {
        "options": picks,
        "strategy_name": strategy,
        "strategy_desc": strategy_config.get("description", ""),
        "risk_level": risk_level,
        "logic": f"当前五行气场「{boost_level}」，采用「{strategy}」策略。{strategy_config.get('description', '')}",
    }


def estimate_iv(boost_level: str, stocks: list) -> str:
    """估算隐含波动率"""
    if SIMULATE_MODE:
        if boost_level in ("增强", "削弱"):
            return "25-35%（高波动预期）"
        elif boost_level in ("当令", "轻微削弱"):
            return "18-25%（中等波动）"
        else:
            return "12-18%（低波动）"
    # 真实模式下尝试从 yfinance 获取
    try:
        import yfinance as yf
        for stock in stocks[:1]:
            code = stock.get("code", "")
            if code:
                ticker = yf.Ticker(code)
                # 获取最近的期权链
                if ticker.options:
                    expiry = ticker.options[0]
                    chain = ticker.option_chain(expiry)
                    atm_iv = chain.calls.iloc[len(chain.calls)//2].impliedVolatility
                    return f"{atm_iv:.1%}（实时）"
    except Exception:
        pass
    return "数据不可用"


def estimate_greeks(boost_level: str, risk_level: str) -> dict:
    """估算希腊字母简要"""
    if boost_level == "增强":
        return {"Delta": "0.6-0.8", "Gamma": "中高", "Theta": "关注时间衰减", "Vega": "Long Vega(利好波动率上升)"}
    elif boost_level == "削弱":
        return {"Delta": "-0.6 ~ -0.8", "Gamma": "中高", "Theta": "关注时间衰减", "Vega": "Long Vega(利好波动率上升)"}
    elif boost_level == "中性":
        return {"Delta": "接近0(Delta中性)", "Gamma": "低", "Theta": "正Theta(时间朋友)", "Vega": "Short Vega"}
    else:
        return {"Delta": "0.3-0.5", "Gamma": "中", "Theta": "中性", "Vega": "中性"}


def suggest_contract_month() -> str:
    """建议合约月份（最近+次月）"""
    from datetime import datetime
    now = datetime.now()
    next_month = now.month % 12 + 1
    return f"当月({now.month}月) 或 次月({next_month}月)合约"
