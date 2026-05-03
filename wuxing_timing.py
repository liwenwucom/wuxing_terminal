# -*- coding: utf-8 -*-
"""
五行择时推荐框架（股票、期货、期权综合版）
基于十二长生承载力 → 追/等/撤 三态决策 + 星级评级 + 预期涨幅区间

核心规则（用户原文确立）：
1. 承载力增强 + 涨幅同步放大 → 真实资金，低位可加仓
2. 承载力增强 + 涨幅不及预期 → 骗炮嫌疑，不宜追高
3. 承载力减弱 + 涨幅反而放大 → 短线透支，次日易回调
"""

from datetime import datetime
from bazi_capacity import (
    get_capacity_score_for_scoring, IPO_DATE_MAP,
    get_chang_sheng, get_riyuan_from_ipo, get_trade_day_info,
    TIANGAN_WUXING, DIZHI_WUXING, CAPACITY_SCORES, STAGE_NAMES,
)

# ============================================================
# 承载力 → 星级评级表
# ============================================================
STAR_RATINGS = {
    "帝旺":  (5, "★★★★★", "极强",  (2.0, 5.0)),
    "临官":  (4, "★★★★☆", "较强",  (1.5, 3.0)),
    "冠带":  (3, "★★★☆☆", "中等",  (1.0, 2.5)),
    "沐浴":  (3, "★★★☆☆", "中等",  (0.5, 1.5)),
    "长生":  (3, "★★★☆☆", "中等",  (0.5, 1.5)),
    "衰":    (2, "★★☆☆☆", "较弱",  (0.0, 1.0)),
    "病":    (2, "★★☆☆☆", "较弱",  (-0.5, 0.5)),
    "死":    (1, "★☆☆☆☆", "极弱",  (-1.0, 0.0)),
    "墓":    (1, "★☆☆☆☆", "极弱",  (-1.5, 0.0)),
    "绝":    (1, "★☆☆☆☆", "极弱",  (-2.5, -0.5)),
    "胎":    (2, "★★☆☆☆", "较弱",  (-1.0, 1.0)),
    "养":    (2, "★★☆☆☆", "较弱",  (-0.5, 1.5)),
}

# ============================================================
# 十二长生预期涨幅速查表（庚金/丙火/戊土三柱）
# ============================================================
EXPECTED_RANGE_BY_STEM = {
    "庚金": {
        "子": "死",   "丑": "墓",   "寅": "绝",
        "卯": "胎",   "辰": "养",   "巳": "长生",
        "午": "沐浴", "未": "冠带", "申": "临官",
        "酉": "帝旺", "戌": "衰",   "亥": "病",
    },
    "丙火": {
        "子": "胎",   "丑": "养",   "寅": "长生",
        "卯": "沐浴", "辰": "冠带", "巳": "临官",
        "午": "帝旺", "未": "衰",   "申": "病",
        "酉": "死",   "戌": "墓",   "亥": "绝",
    },
    "戊土": {
        "子": "帝旺",  "丑": "冠带", "寅": "病",
        "卯": "死",    "辰": "暮",   "巳": "临官",
        "午": "帝旺",  "未": "衰",   "申": "病",
        "酉": "死",    "戌": "墓",   "亥": "绝",
    },
}

# ============================================================
# 2026年5月重要宏观事件日历
# ============================================================
MAY_EVENTS_2026 = [
    {"date": "2026-05-01", "event": "对53个非洲建交国全面实施零关税（水属性利好贸易物流）"},
    {"date": "2026-05-05", "event": "立夏，进入己巳月（巳月五行属火）"},
    {"date": "2026-05-06", "event": "五一休市后首日开市，己酉日"},
    {"date": "2026-05-08", "event": "上期所非燃料油2605合约自然人最后交易日；上期所市价套利指令修订意见反馈截止"},
    {"date": "2026-05-09", "event": "沪深300 IF新主力合约切换"},
    {"date": "2026-05-11", "event": "中国4月CPI、PPI发布"},
    {"date": "2026-05-12", "event": "美国4月CPI发布"},
    {"date": "2026-05-13", "event": "EIA短期能源展望、IEA原油月报、OPEC月报发布"},
    {"date": "2026-05-17", "event": "期货公司监督管理办法（征求意见稿）反馈截止"},
    {"date": "2026-05-22", "event": "燃料油FU2606合约自然人最后交易日"},
    {"date": "2026-05-29", "event": "2606合约自然人最后交易日"},
]

# ============================================================
# 追/等/撤 三态决策规则
# ============================================================
def get_timing_signal(stage_name, sheng_ke_type, capacity_score, volume_confirmed=True):
    """
    综合承载力+生克+量价 → 追/等/撤 三态决策
    
    :param stage_name: 十二长生状态名（如"帝旺"）
    :param sheng_ke_type: 生克关系类型 "生助"/"平衡"/"受克"
    :param capacity_score: 承载力数值
    :param volume_confirmed: 量价是否验证通过
    :return: {"signal": "追/等/撤", "rationale": "...", "option_hint": "..."}
    """
    strong_stages = {"帝旺", "临官"}
    medium_stages = {"冠带", "沐浴", "长生", "养"}
    weak_stages = {"衰", "病", "死", "墓", "绝", "胎"}
    
    if stage_name in strong_stages and sheng_ke_type == "生助" and volume_confirmed:
        return {
            "signal": "追",
            "rationale": "承载力极强+天时生助+放量确认，顺势参与",
            "option_hint": "买实值看涨 / 牛市看涨价差",
        }
    elif stage_name in strong_stages and sheng_ke_type == "平衡":
        return {
            "signal": "追",
            "rationale": "承载力强+生克平衡，偏多但需注意节奏",
            "option_hint": "牛市看涨价差 / 卖出虚值看跌",
        }
    elif stage_name in strong_stages and sheng_ke_type == "受克":
        return {
            "signal": "等",
            "rationale": "承载力强但天时相克，等待生克关系改善",
            "option_hint": "卖宽跨式 / 观望",
        }
    elif stage_name in medium_stages and sheng_ke_type == "生助":
        return {
            "signal": "追",
            "rationale": "承载力中等+天时生助，可轻仓跟随",
            "option_hint": "牛市看涨价差 / 轻仓买Call",
        }
    elif stage_name in medium_stages:
        return {
            "signal": "等",
            "rationale": "承载力中等+无明显方向，区间思路等待信号确认",
            "option_hint": "卖宽跨式（双卖）赚时间价值",
        }
    elif stage_name in weak_stages and sheng_ke_type == "受克":
        return {
            "signal": "撤",
            "rationale": "承载力弱+天时相克，暂时回避，减仓观望",
            "option_hint": "买虚值看跌对现存仓位做保护",
        }
    elif stage_name in weak_stages:
        return {
            "signal": "撤",
            "rationale": "承载力弱，量价背离风险高，优先观望",
            "option_hint": "减仓 / 买看跌保护 / 观望",
        }
    return {
        "signal": "等",
        "rationale": "信号中性，等待进一步确认",
        "option_hint": "观望",
    }


def _classify_sheng_ke(riyuan_gan, trade_day_zhi):
    """简化的生克分类"""
    gan_wx = TIANGAN_WUXING.get(riyuan_gan, "")
    zhi_wx = DIZHI_WUXING.get(trade_day_zhi, "")
    
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    
    if gan_wx == zhi_wx:
        return "平衡"
    elif sheng.get(zhi_wx) == gan_wx:
        return "生助"
    elif sheng.get(gan_wx) == zhi_wx:
        return "平衡"
    elif ke.get(zhi_wx) == gan_wx:
        return "受克"
    elif ke.get(gan_wx) == zhi_wx:
        return "平衡"
    return "平衡"


def get_timing_report(stock_code, stock_name=None, trade_date_str=None):
    """
    生成单只标的的完整择时报告（股票/期货均可）
    返回 星级 + 追等撤 + 预期区间 + 期权提示
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    
    ipo = IPO_DATE_MAP.get(stock_code, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    trade_info = get_trade_day_info(trade_date_str)
    chang_sheng = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])
    
    stage_name = chang_sheng["stage_name"]
    capacity = chang_sheng["capacity_score"]
    
    star_info = STAR_RATINGS.get(stage_name, (0, "☆☆☆☆☆", "未知", (-1, 1)))
    stars, star_str, star_label, exp_range = star_info
    
    sheng_ke = _classify_sheng_ke(riyuan["gan"], trade_info["day_zhi"])
    timing = get_timing_signal(stage_name, sheng_ke, capacity)
    
    return {
        "stock_code": stock_code,
        "stock_name": stock_name or stock_code,
        "trade_date": trade_date_str,
        "riyuan_gan": riyuan["gan"],
        "riyuan_zhi": riyuan["zhi"],
        "riyuan_wuxing": riyuan["wuxing"],
        "trade_day_gan": trade_info["day_gan"],
        "trade_day_zhi": trade_info["day_zhi"],
        "trade_ganzhi": trade_info["day_ganzhi"],
        "chang_sheng_stage": stage_name,
        "capacity_score": capacity,
        "stars": stars,
        "star_display": star_str,
        "star_label": star_label,
        "expected_range": f"{exp_range[0]:+.1f}% ~ {exp_range[1]:+.1f}%",
        "sheng_ke": sheng_ke,
        "timing_signal": timing["signal"],
        "timing_rationale": timing["rationale"],
        "option_hint": timing["option_hint"],
    }


def get_timing_for_stock(stock_code, stock_name=None, trade_date_str=None):
    """快捷接口：返回股票的 信号+星级+预期区间（用于评分增强）"""
    r = get_timing_report(stock_code, stock_name, trade_date_str)
    return {
        "signal": r["timing_signal"],
        "stars": r["stars"],
        "star_display": r["star_display"],
        "expected_range": r["expected_range"],
        "option_hint": r["option_hint"],
    }


def get_timing_signal_bonus(signal):
    """追等撤 → 评分修正因子"""
    return {"追": 0.25, "等": 0.0, "撤": -0.25}.get(signal, 0.0)


def get_may_event_summary(date_str=None):
    """获取5月临近事件提醒"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    upcoming = []
    for e in MAY_EVENTS_2026:
        if e["date"] >= date_str:
            upcoming.append(f"  {e['date']}: {e['event'][:50]}")
    return "\n".join(upcoming[:5]) if upcoming else "暂无5月重点事件"


def summarize_timing(report):
    """生成追等撤汇总"""
    b = report.get("buy_stocks", [])
    s = report.get("sell_stocks", [])
    a = report.get("avoid_stocks", [])
    
    zhui = [x["name"] for x in b if x.get("timing_signal") == "追"]
    deng = [x["name"] for x in b + s + a if x.get("timing_signal") == "等"]
    che = [x["name"] for x in s + a if x.get("timing_signal") == "撤"]
    
    lines = []
    if zhui:
        lines.append(f"  🔥 追: {' | '.join(zhui)}")
    if deng:
        lines.append(f"  ⏳ 等: {' | '.join(deng[:6])}")
    if che:
        lines.append(f"  🛑 撤: {' | '.join(che[:6])}")
    return "\n".join(lines) if lines else "  信号中性"
