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


# ============================================================
# 专业期权策略池（水洲·期权核心策略）
# ============================================================
PRO_OPTION_STRATEGIES = [
    {
        "id": "O1",
        "tool": "买入看跌期权 (Long Put)",
        "scenario": "纯碱/铁矿石/鸡蛋/房地产产业链品种",
        "purpose": "以有限权利金捕获市场潜在下跌，对反向波动风险不敏感",
        "recommendation": "纯碱短期压力最大(玻璃开工+光伏库存)，推荐直接买入看跌期权",
    },
    {
        "id": "O2",
        "tool": "卖出虚值看涨期权 (Short OTM Call)",
        "scenario": "碳酸锂/工业硅/螺纹钢",
        "purpose": "赚取时间价值，构建备兑开仓增厚现货/多单收益",
        "recommendation": "持有现货或标准仓单的产业客户可优先选择，增强持仓收益",
    },
    {
        "id": "O3",
        "tool": "牛市看涨价差 (Bull Call Spread)",
        "scenario": "黄金AU/白银AG/生猪LH",
        "purpose": "对上行方向有时间限制的上行判断，降低权利金成本",
        "recommendation": "黄金/白银上行确定性高但短期有波动，价差优于直接买Call",
    },
    {
        "id": "O4",
        "tool": "熊市看跌价差 (Bear Put Spread)",
        "scenario": "工业硅/碳酸锂",
        "purpose": "结合偏空趋势判断同时规避持续暴跌尾部风险",
        "recommendation": "供给压力持续释放但下方空间有限，价差结构更安全",
    },
    {
        "id": "O5",
        "tool": "买入跨式/宽跨式 (Long Straddle/Strangle)",
        "scenario": "原油SC/地缘突发事件窗口",
        "purpose": "事件驱动型策略，捕捉波动率放大带来的Gamma收益",
        "recommendation": "美伊局势存在反复风险，事件窗口前可低位建仓跨式博波动率",
    },
    {
        "id": "O6",
        "tool": "卖出宽跨式 (Short Strangle)",
        "scenario": "PTA/甲醇/震荡格局品种",
        "purpose": "震荡市场赚取双方向的时间衰减收益",
        "recommendation": "上述品种短期震荡格局清晰，Theta策略收益稳定",
    },
]

STOP_LOSS_DISCIPLINE = {
    "max_loss_per_trade": "单笔亏损不超过总资金的2%",
    "futures_stop": "突破关键支撑/阻力位2%应止损",
    "options_stop": "权利金亏损50%或Delta方向逆转时离场",
    "position_sizing": "单一品种持仓不超过总资金15%，杠杆不超过3倍",
    "drawdown_rule": "总资金回撤达20%时强制暂停所有新开仓",
    "disclaimer": "必须根据自身风险承受能力动态调整，所有策略均需自行设置止损线",
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
