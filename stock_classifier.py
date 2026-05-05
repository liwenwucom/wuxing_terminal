# -*- coding: utf-8 -*-
"""
股票智能分类引擎
—— 科创板/A股分离 → 买入/卖出/观望 三栏分类

基于：
1. 预期涨幅（从 expected_range 解析上限）
2. 综合描述信号强度（五星共振/政策加持/机构共识 → 买入加分）
3. 十二长生阶段（帝旺/临官 → 加分，病/死/墓/绝 → 减分）
4. 承载力评分
"""

import re
from datetime import datetime


# ============================================================
# 长生阶段 → 多空倾向
# ============================================================
POSITIVE_STAGES = {"帝旺", "临官", "冠带", "沐浴", "长生"}
NEGATIVE_STAGES = {"病", "死", "墓", "绝", "胎", "养"}
NEUTRAL_STAGES = {"衰"}


# ============================================================
# 综合描述 → 信号强度评分
# ============================================================
DESCRIPTION_SCORE_PATTERNS = [
    (r"五星共振", 35),
    (r"政策加持|政策面有支撑|政策驱动", 25),
    (r"机构共识|机构推荐|券商金股", 20),
    (r"多头信号明确|强烈看多|趋势做多", 25),
    (r"承载力帝旺", 20),
    (r"承载力临官|承载力冠带", 12),
    (r"综合评分偏多", 8),
    (r"量价齐升|量价验证|量比放大", 10),
    (r"强趋势上行|趋势做多确认|方向明确偏多", 18),
    (r"偏强震荡", 5),
    (r"放量上涨|温和放量|量比>=1\.2", 8),
]

NEGATIVE_DESCRIPTION_PATTERNS = [
    (r"偏空|空头信号|看空|缺乏政策支撑", -25),
    (r"五行受克|天时相克", -18),
    (r"多空交织|方向不明|不明朗", -10),
    (r"承载力偏弱|承载力弱|综合评分偏空", -15),
    (r"避[险让]|不宜|不建议", -12),
    (r"弱势承压|极弱回避|下跌预期极强", -15),
    (r"空头主导|坚决不加仓|缩量阴跌", -18),
]


def _parse_expected_upper(expected_range: str) -> float:
    """从预期区间字符串中提取上限，如 '+2.0%~+5.0%' → 5.0"""
    if not expected_range:
        return 0.0
    nums = re.findall(r"([+-]?\d+\.?\d*)\s*%", expected_range)
    if len(nums) >= 2:
        return float(nums[1])
    if len(nums) == 1:
        return float(nums[0])
    return 0.0


def _parse_expected_lower(expected_range: str) -> float:
    """从预期区间字符串中提取下限，如 '+2.0%~+5.0%' → 2.0"""
    if not expected_range:
        return 0.0
    nums = re.findall(r"([+-]?\d+\.?\d*)\s*%", expected_range)
    if nums:
        return float(nums[0])
    return 0.0


def _score_description(text: str) -> int:
    """根据综合描述计算信号得分（-100 ~ +100）"""
    if not text:
        return 0
    score = 0
    for pattern, pts in DESCRIPTION_SCORE_PATTERNS:
        if re.search(pattern, text):
            score += pts
    for pattern, pts in NEGATIVE_DESCRIPTION_PATTERNS:
        if re.search(pattern, text):
            score += pts
    return max(-100, min(100, score))


def _stage_score(stage: str) -> int:
    """长生阶段得分"""
    if stage in POSITIVE_STAGES:
        return {"帝旺": 30, "临官": 25, "冠带": 15, "沐浴": 10, "长生": 8}.get(stage, 5)
    if stage in NEGATIVE_STAGES:
        return {"死": -25, "墓": -25, "绝": -30, "病": -15, "胎": -5, "养": -5}.get(stage, -10)
    return 0


def _timing_score(signal: str) -> int:
    """择时信号得分"""
    return {"追": 20, "等": 0, "撤": -20}.get(signal, 0)


def _estimate_price_level(stock: dict) -> str:
    """根据市值/行业估算价格档次"""
    cap = stock.get("market_cap", "")
    if cap in ("大盘",):
        return "中高价"
    elif cap in ("中盘",):
        return "中等"
    else:
        return "低价/小盘"


def classify_stock(stock: dict) -> dict:
    """
    对单只股票打分，返回 dict:
    {code, name, score, label(买入/卖出/观望), reason, expected_upper, policy_score, price_level}
    """
    expected_range = stock.get("expected_range", "")
    upper = _parse_expected_upper(expected_range)
    lower = _parse_expected_lower(expected_range)

    reason = stock.get("direction_reason", "") or stock.get("reason", "")
    desc_score = _score_description(reason)

    stage = stock.get("chang_sheng_name", "")
    ss = _stage_score(stage)

    timing = stock.get("timing_signal", "等")
    ts = _timing_score(timing)

    capacity = stock.get("capacity_score", 0)

    # 预期涨幅直接映射为分数（上限高 = 正面）
    expected_score = 0
    if upper >= 5.0:
        expected_score = 20
    elif upper >= 3.0:
        expected_score = 15
    elif upper >= 1.5:
        expected_score = 8
    elif upper >= 0.5:
        expected_score = 3
    elif upper < 0 and lower < 0:
        expected_score = -15
    elif upper < 1.0:
        expected_score = -5

    total = (
        desc_score * 0.40 +
        ss * 0.18 +
        ts * 0.12 +
        expected_score * 0.18 +
        capacity * 0.12
    )

    if total >= 22:
        label = "买入"
    elif total >= 8:
        label = "观望"
    else:
        label = "卖出"

    price_level = _estimate_price_level(stock)

    policy_score = "高" if desc_score >= 60 else ("中" if desc_score >= 30 else "低")

    return {
        "code": stock.get("code", ""),
        "name": stock.get("name", ""),
        "sector": stock.get("sector", "") or stock.get("matched_industry", ""),
        "wuxing": stock.get("wuxing", ""),
        "riyuan": stock.get("riyuan_gan", ""),
        "stage": stage,
        "timing": timing,
        "expected_range": expected_range,
        "expected_upper": upper,
        "expected_lower": lower,
        "direction_reason": reason,
        "desc_score": desc_score,
        "stage_score": ss,
        "timing_score": ts,
        "expected_score": expected_score,
        "capacity_score": capacity,
        "total_score": round(total, 1),
        "label": label,
        "price_level": price_level,
        "policy_score": policy_score,
    }


def classify_stocks(stocks: list) -> dict:
    """
    输入一批股票 dict → 输出分类结果
    
    Returns:
    {
        "kechuang": {"buy": [...], "sell": [...], "hold": [...]},
        "ashares": {"buy": [...], "sell": [...], "hold": [...]},
        "excluded": [...],  # 被排除的（港股等）
        "generated_at": str,
    }
    """
    kechuang_all = []
    ashares_all = []
    excluded = []

    for s in stocks:
        code = s.get("code", "")
        if not code:
            continue

        # 排除港股（4位/5位数字代码且非6位）
        if len(code) < 6 and not code.startswith("688"):
            excluded.append({"code": code, "name": s.get("name", ""), "reason": "港股/非A股"})
            continue

        result = classify_stock(s)

        if code.startswith("688"):
            kechuang_all.append(result)
        else:
            ashares_all.append(result)

    def _sort_and_split(items):
        buy = []
        sell = []
        hold = []
        for item in sorted(items, key=lambda x: x["total_score"], reverse=True):
            if item["label"] == "买入":
                buy.append(item)
            elif item["label"] == "卖出":
                sell.append(item)
            else:
                hold.append(item)
        return {
            "buy": buy[:10],
            "sell": sell[:10],
            "hold": hold[:10],
            "total": len(items),
        }

    return {
        "kechuang": _sort_and_split(kechuang_all),
        "ashares": _sort_and_split(ashares_all),
        "excluded": excluded,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def scan_and_classify(trade_date_str: str = None) -> dict:
    """
    全自动：运行现有扫描 → 调用分类引擎 → 返回分类结果
    """
    if trade_date_str is None:
        trade_date_str = datetime.now().strftime("%Y-%m-%d")

    from stock_bazi_scanner import scan_all_stocks_daily
    scan_result = scan_all_stocks_daily(trade_date_str)

    stocks = []
    for s in scan_result.get("results", []):
        stage = s.get("stage", "")
        phase = s.get("phase_label", "")
        verify = s.get("verify_signal", "")

        # 从阶段推导择时信号
        if stage in ("帝旺", "临官"):
            timing = "追"
        elif stage in ("死", "墓", "绝"):
            timing = "撤"
        else:
            timing = "等"

        # 从阶段推导方向标签
        if stage in ("帝旺", "临官"):
            direction_label = "买入"
        elif stage in ("死", "墓", "绝"):
            direction_label = "卖出"
        else:
            direction_label = "观望"

        # 构造综合描述
        direction_reason = f"{phase} | {verify}"

        stocks.append({
            "code": s.get("code", ""),
            "name": s.get("name", ""),
            "sector": s.get("sector", ""),
            "wuxing": s.get("stock_wuxing", ""),
            "riyuan_gan": s.get("riyuan_gan", ""),
            "chang_sheng_name": stage,
            "timing_signal": timing,
            "expected_range": _parse_expected_from_stage(stage),
            "direction_reason": direction_reason,
            "direction_label": direction_label,
            "capacity_score": s.get("capacity", 0),
            "market_cap": "",
            "star_display": s.get("star", ""),
        })

    return classify_stocks(stocks)


def _parse_expected_from_stage(stage: str) -> str:
    """把文字描述的预期转成数值区间，方便评分"""
    mapping = {
        "帝旺": "+2.0%~+5.0%",
        "临官": "+1.0%~+3.0%",
        "冠带": "+0.5%~+1.5%",
        "沐浴": "-0.8%~+0.8%",
        "长生": "+0.0%~+1.0%",
        "衰": "-1.5%~+0.0%",
        "病": "-3.0%~-0.5%",
        "死": "-5.0%~-1.5%",
        "墓": "-5.0%~-1.5%",
        "绝": "-5.0%~-1.5%",
        "胎": "-2.0%~+0.0%",
        "养": "-1.0%~+0.5%",
    }
    return mapping.get(stage, "0%")


def format_classification_report(result: dict) -> str:
    """将分类结果格式化为 Markdown 报告"""
    lines = []
    lines.append(f"# 股票智能分类报告")
    lines.append(f"生成时间: {result['generated_at']}")
    lines.append("")

    if result.get("excluded"):
        exc_names = ", ".join(f"{e['name']}({e['code']})" for e in result["excluded"])
        lines.append(f"> ⚠️ 已排除: {exc_names}")
        lines.append("")

    for board_key, board_name in [("kechuang", "科创板"), ("ashares", "A股（非科创板）")]:
        board = result.get(board_key, {})
        lines.append(f"## {board_name}")
        lines.append(f"共 {board.get('total', 0)} 只")
        lines.append("")

        for group_key, group_label, icon in [
            ("buy", "买入（推荐）", "🟢"),
            ("sell", "卖出（回避）", "🔴"),
            ("hold", "观望/中性", "⚪"),
        ]:
            items = board.get(group_key, [])
            lines.append(f"### {icon} {group_label} ({len(items)}只)")
            lines.append("")
            if items:
                lines.append("| 股票 | 代码 | 行业 | 五行 | 长生 | 择时 | 预期 | 评分 | 政策 |")
                lines.append("|------|------|------|------|------|------|------|------|------|")
                for item in items:
                    lines.append(
                        f"| {item['name']} | {item['code']} | {item['sector']} | "
                        f"{item['wuxing']} | {item['stage']} | {item['timing']} | "
                        f"{item['expected_range']} | {item['total_score']} | {item['policy_score']} |"
                    )
            lines.append("")

    return "\n".join(lines)
