# -*- coding: utf-8 -*-
"""
八字选期货/期权推演引擎 v1.0
—— 日元承载力(十二长生) + 量价齐生(持仓量+升贴水) + 期权买/卖策略矩阵

核心功能：
1. 期货单日承载力报告（六段式）
2. 期货后续N日推演 + 离场/加仓节奏
3. 期权买权 vs 卖权策略自动选择
4. 月度轮动映射到期货品种方向
"""

from datetime import datetime
from bazi_capacity import (
    get_riyuan_from_ipo, get_trade_day_info, get_chang_sheng,
    TIANGAN_WUXING, DIZHI_WUXING, STAGE_NAMES, CAPACITY_SCORES,
)
from wuxing_timing import STAR_RATINGS, get_timing_signal
from futures_picker import (
    FUTURES_BAZI_BASE, FUTURES_IPO_DATE_MAP,
    OPTION_STRATEGY_TABLE, OPTION_BUYER_SELLER_MATRIX,
    get_option_strategy_for_stage, get_option_buyer_seller_for_stage,
    get_futures_stage_hint, PRO_FUTURES_LONG, PRO_FUTURES_SHORT,
    CHINA_FUTURES_POOL, get_futures_popularity, FUTURES_BROKER_POPULARITY,
    get_main_contract, MAIN_CONTRACT_EXAMPLES,
)
from policy_analyzer import get_monthly_rotation, MONTHLY_ROTATION
from bazi_picker import get_next_n_trading_days


# ============================================================
# 期货承载力星级映射 + 双向量价验证信号
# ============================================================
FUTURES_CAPACITY_STAR_MAP = {
    "帝旺": ("★★★★★", "极强", "成交放量+持仓增加+升贴水走强=多头真实入场"),
    "临官": ("★★★★★", "极强", "成交放量+持仓稳步增加=趋势做多确认"),
    "冠带": ("★★★★☆", "较强", "温和放量上涨≥0.5%,量比>1.0"),
    "沐浴": ("★★★★☆", "较强", "窄幅震荡预期,涨跌幅<±0.8%为正常"),
    "长生": ("★★★☆☆", "中等", "静待观察,量大涨幅>1%可轻仓试多"),
    "衰":   ("★★☆☆☆", "较弱", "不建议开新仓,持仓衰减+跌时放量=下跌趋势"),
    "病":   ("★★☆☆☆", "较弱", "坚决不加仓,冲高即减仓,升贴水疲软"),
    "死":   ("★☆☆☆☆", "极弱", "空头主导,放量下跌+贴水扩大=真看空"),
    "墓":   ("★☆☆☆☆", "极弱", "成交量爆发下跌可能踩踏,必须设止损"),
    "绝":   ("★☆☆☆☆", "极弱", "极弱日空头占优,宜做空或空仓"),
    "胎":   ("★☆☆☆☆", "极弱", "弱势震荡,不宜操作"),
    "养":   ("★☆☆☆☆", "极弱", "弱势,但接近回升拐点可关注"),
}

# 承载力对应的预期涨跌幅（期货版）
FUTURES_EXPECTED_RANGE = {
    "帝旺": ">=1.5%-3%甚至更高,做多信号最强",
    "临官": ">=1.0%-2%,方向明确偏多",
    "冠带": "0.8%-1.5%,方向预期中等偏上",
    "沐浴": "<±0.8%,震荡预期",
    "长生": "0%-1%,无明确方向",
    "衰":   "偏空,下跌倾向",
    "病":   "方向承压偏空,下跌倾向强",
    "死":   "下跌预期极强",
    "墓":   "下跌预期极强,可能踩踏",
    "绝":   "下跌预期极强",
    "胎":   "弱势震荡",
    "养":   "弱势但接近拐点",
}


def _resolve_futures_name(symbol):
    """解析期货品种名称"""
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            if c["symbol"] == symbol:
                return c["name"]
    return symbol


def _resolve_futures_wuxing(symbol):
    """获取期货品种的五行"""
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            if c["symbol"] == symbol:
                return c["wuxing"]
    return "未知"


# ============================================================
# 一、期货单日承载力报告
# ============================================================
def generate_futures_bazi_report(symbol, trade_date_str=None):
    """
    生成期货品种的单日八字承载力报告（六段式）
    :param symbol: 期货代码, 如 'AU' / 'SC' / 'RB'
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    ipo = FUTURES_IPO_DATE_MAP.get(symbol, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    gan = riyuan["gan"]
    wx_riyuan = riyuan["wuxing"]
    wx_futures = _resolve_futures_wuxing(symbol)

    trade_info = get_trade_day_info(trade_date_str)
    cs = get_chang_sheng(gan, trade_info["day_zhi"])
    stage = cs["stage_name"]
    star, label, verify_signal = FUTURES_CAPACITY_STAR_MAP.get(
        stage, ("☆☆☆☆☆", "未知", "—"))
    expected = FUTURES_EXPECTED_RANGE.get(stage, "—")
    timing = get_timing_signal(stage, None, cs["capacity_score"])
    timing_str = timing["signal"] if timing else "—"
    star_info = STAR_RATINGS.get(stage, (0, "☆☆☆☆☆", "未知", (-1.0, 1.0)))

    # 期权买/卖策略
    opt_strats = get_option_strategy_for_stage(stage)
    opt_bs = get_option_buyer_seller_for_stage(stage)

    # 专业推荐信息
    pro_direction = None
    pro_confidence = 0
    for f in PRO_FUTURES_LONG:
        if f["symbol"] == symbol:
            pro_direction = f["direction"]
            pro_confidence = f["confidence"]
            break
    if not pro_direction:
        for f in PRO_FUTURES_SHORT:
            if f["symbol"] == symbol:
                pro_direction = f["direction"]
                pro_confidence = f["confidence"]
                break

    # 月度轮动方向
    rotation = get_monthly_rotation(trade_date_str)
    rotation_wx = rotation["elements"] if rotation else []

    # 构建结论
    if stage in ("帝旺", "临官"):
        conclusion = f"{_resolve_futures_name(symbol)}当日承载力{stage}，天时配合多头力量极强。"
        if pro_direction and "多" in pro_direction:
            conclusion += f"叠加专业评级{pro_direction}(置信度{pro_confidence}%)，共振明确。需持仓量+升贴水双重验证。"
            action = "追"
        else:
            conclusion += "需等持仓量放大确认，不含糊追多。"
            action = "等"
    elif stage in ("冠带", "沐浴"):
        conclusion = f"{_resolve_futures_name(symbol)}承载力{stage}中等偏强，可维持现有仓位，但不宜重仓追高。"
        action = "等"
    elif stage in ("衰", "病"):
        conclusion = f"{_resolve_futures_name(symbol)}承载力{stage}偏弱，减仓至半仓以下，空头可顺势。"
        action = "撤"
    elif stage in ("死", "墓", "绝"):
        conclusion = f"{_resolve_futures_name(symbol)}承载力{stage}极弱，空仓或做空，严禁做多。"
        action = "撤"
    else:
        conclusion = f"{_resolve_futures_name(symbol)}承载力{stage}，方向不明，观望为宜。"
        action = "等"

    report = {
        "symbol": symbol,
        "name": _resolve_futures_name(symbol),
        "ipo_date": ipo,
        "riyuan_gan": gan,
        "riyuan_wuxing": wx_riyuan,
        "riyuan_ganzhi": riyuan["ganzhi"],
        "futures_wuxing": wx_futures,
        "trade_date": trade_date_str,
        "year_ganzhi": trade_info["year_ganzhi"],
        "month_ganzhi": trade_info["month_ganzhi"],
        "day_ganzhi": trade_info["day_ganzhi"],
        "day_gan": trade_info["day_gan"],
        "day_zhi": trade_info["day_zhi"],
        "chang_sheng_stage": stage,
        "capacity_score": cs["capacity_score"],
        "star_display": star,
        "star_label": label,
        "expected_range": expected,
        "verify_signal": verify_signal,
        "timing_signal": timing_str,
        "star_info": star_info,
        "option_strategies": opt_strats,
        "option_bs": opt_bs,
        "pro_direction": pro_direction,
        "pro_confidence": pro_confidence,
        "rotation_elements": rotation_wx,
        "conclusion": conclusion,
        "action": action,
    }
    return report


# ============================================================
# 二、格式化期货单日报告
# ============================================================
def format_futures_bazi_report(report):
    r = report
    lines = [
        f"## 八字期货推演 — {r['name']} ({r['symbol']})",
        "",
        "### 一、基础信息",
        f"- 品种名称/代码：{r['name']} ({r['symbol']})",
        f"- 合约上市日期：{r['ipo_date']}",
        f"- 日元五行属性：{r['riyuan_gan']}({r['riyuan_wuxing']}) | 日柱：{r['riyuan_ganzhi']}",
        f"- 品种五行归类：{r['futures_wuxing']}",
        f"- 目标交易日：{r['trade_date']}",
        "",
        "### 二、当日承载力",
        f"- 时间八字：{r['year_ganzhi']} {r['month_ganzhi']} {r['day_ganzhi']}",
        f"- {r['riyuan_gan']}({r['riyuan_wuxing']}) x {r['day_zhi']}日支 = **{r['chang_sheng_stage']}**",
        f"- 承载力等级：{r['star_display']} {r['star_label']}",
        f"- 理论预期涨跌方向：{r['expected_range']}",
        "",
        "### 三、期货量价验证框架",
        f"- 验证信号：{r['verify_signal']}",
        f"- 择时建议：{'追' if r['action']=='追' else '等' if r['action']=='等' else '撤'}",
        "",
        "### 四、期权策略框架",
    ]
    if r["option_bs"]:
        bs = r["option_bs"]
        lines += [
            f"- 买方策略：**{bs['buyer_strategy']}**",
            f"- 卖方策略：**{bs['seller_strategy']}**",
            f"- 逻辑：{bs['logic']}",
            f"- 风险提示：{bs['risk_note']}",
        ]
    if r["option_strategies"]:
        for s in r["option_strategies"]:
            lines.append(f"- {s['strategy']}: {s['detail']} ({s['risk_note']})")

    lines += [
        "",
        "### 五、专业配置方向",
    ]
    if r["pro_direction"]:
        lines.append(f"- 专业评级：{r['pro_direction']} (置信度 {r['pro_confidence']}%)")
    if r["rotation_elements"]:
        lines.append(f"- 月度轮动五行：{' + '.join(r['rotation_elements'])}")

    lines += [
        "",
        "### 六、综合结论",
        f"> {r['conclusion']}",
        "",
        "---",
        "> **免责声明**：本推演基于八字十二长生理论，仅为传统文化视角的沙盘演练，不构成任何投资建议。"
        "期货/期权交易风险极高，可能亏损超过本金，严禁借贷交易。",
    ]
    return "\n".join(lines)


# ============================================================
# 三、期货后续N日承载力推演
# ============================================================
def generate_futures_forward_report(symbol, trade_date_str=None, n_days=3):
    """
    生成期货后续N日承载力推演
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    ipo = FUTURES_IPO_DATE_MAP.get(symbol, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    gan = riyuan["gan"]

    next_dates = get_next_n_trading_days(trade_date_str, n_days)
    all_dates = [trade_date_str] + next_dates

    daily_rows = []
    for i, d in enumerate(all_dates):
        info = get_trade_day_info(d)
        cs = get_chang_sheng(gan, info["day_zhi"])
        stage = cs["stage_name"]
        star, label, verify = FUTURES_CAPACITY_STAR_MAP.get(
            stage, ("☆☆☆☆☆", "未知", "—"))
        expected = FUTURES_EXPECTED_RANGE.get(stage, "—")
        opt_bs = get_option_buyer_seller_for_stage(stage)

        daily_rows.append({
            "day_label": f"T+{i}" if i > 0 else "T+0(今日)",
            "date": d,
            "day_ganzhi": info["day_ganzhi"],
            "day_zhi": info["day_zhi"],
            "stage": stage,
            "star": star,
            "label": label,
            "capacity_score": cs["capacity_score"],
            "expected": expected,
            "verify": verify,
            "opt_buyer": opt_bs["buyer_strategy"] if opt_bs else "—",
            "opt_seller": opt_bs["seller_strategy"] if opt_bs else "—",
        })

    rhythm = _plan_futures_rhythm(daily_rows)

    return {
        "symbol": symbol,
        "name": _resolve_futures_name(symbol),
        "ipo_date": ipo,
        "riyuan_gan": gan,
        "riyuan_wuxing": riyuan["wuxing"],
        "base_date": trade_date_str,
        "next_dates": next_dates,
        "daily_rows": daily_rows,
        "rhythm": rhythm,
    }


def _plan_futures_rhythm(daily_rows):
    """期货节奏规划"""
    actions = []
    prev_stage = None
    prev_score = None

    for row in daily_rows:
        stage = row["stage"]
        score = row["capacity_score"]
        dl = row["day_label"]
        date = row["date"]

        if stage in ("帝旺", "临官"):
            action = "加仓做多"
            detail = f"{row['star']} {stage}窗口,{row['verify']},满足条件可分批建多"
        elif stage in ("冠带", "沐浴"):
            if prev_stage in ("帝旺", "临官"):
                action = "持有/部分止盈"
                detail = f"承载力从{prev_stage}降至{stage},已获利仓位部分止盈"
            else:
                action = "持有观察"
                detail = f"承载力{stage}中性偏强,维持仓位"
        elif stage in ("衰", "病"):
            if prev_score is not None and score > prev_score and prev_stage in ("死", "墓", "绝"):
                action = "试探性做多"
                detail += f" | 趋势逆转: {prev_stage}->{stage}"
            else:
                action = "减仓/做空"
                detail = f"承载力{stage}偏弱,减至半仓或顺势做空"
        else:
            action = "空仓/做空"
            detail = f"承载力{stage}极弱,空头窗口,不做多"

        actions.append({
            "day_label": dl,
            "date": date,
            "stage": stage,
            "action": action,
            "detail": detail,
        })
        prev_stage = stage
        prev_score = score

    stages = [a["stage"] for a in actions]
    if all(s in ("帝旺", "临官") for s in stages[1:]):
        overview = "连续极强窗口,核心做多周期,可滚动加仓"
    elif any(s in ("死", "墓", "绝") for s in stages[1:]):
        overview = "承载力出现极弱节点,短期回避多头,等待下个帝旺日"
    elif any(s in ("帝旺", "临官") for s in stages[1:]) and any(s in ("衰", "病", "死") for s in stages[1:]):
        overview = "承载力波动剧烈,帝旺日快进快出,极弱日坚决回避"
    else:
        overview = "承载力整体平淡,短线无突出机会,维持轻仓或观望"

    return {"daily_actions": actions, "overview": overview}


def format_futures_forward_report(report):
    r = report
    lines = [
        f"## 后续N日承载力推演 — {r['name']} ({r['symbol']})",
        "",
        "### 承载力变化表",
        "",
        "| 交易日 | 日期 | 日柱 | 日元x日支 | 十二长生 | 承载力 | 预期方向 | 期权买方 | 期权卖方 |",
        "|--------|------|------|-----------|----------|--------|----------|----------|----------|",
    ]
    for row in r["daily_rows"]:
        lines.append(
            f"| {row['day_label']} | {row['date']} | {row['day_ganzhi']} | {r['riyuan_gan']}x{row['day_zhi']} | {row['stage']} | {row['star']} {row['label']} | {row['expected']} | {row['opt_buyer']} | {row['opt_seller']} |"
        )

    rhythm = r["rhythm"]
    lines += [
        "",
        "### 离场/加仓节奏",
        "",
        "| 交易日 | 操作 | 理由 |",
        "|--------|------|------|",
    ]
    for a in rhythm["daily_actions"]:
        lines.append(f"| {a['day_label']} | **{a['action']}** | {a['detail']} |")

    lines += [
        "",
        f"### 综合节奏建议",
        f"> {rhythm['overview']}",
        "",
        "---",
    ]
    return "\n".join(lines)


# ============================================================
# 四、月度轮动 → 期货方向映射
# ============================================================
def get_monthly_futures_direction(trade_date_str=None):
    """
    基于月度轮动表，给出各五行方向下的期货品种做多/做空建议
    """
    rotation = get_monthly_rotation(trade_date_str)
    elements = rotation["elements"] if rotation else ["土"]

    directions = {}
    for element in elements:
        picks = []
        for exchange, contracts in CHINA_FUTURES_POOL.items():
            for c in contracts:
                if c["wuxing"] == element:
                    picks.append(c["name"])
        directions[element] = {
            "direction": "偏多",
            "picks": picks,
            "note": f"月度轮动{'+'.join(elements)}主导,{element}属性品种有利",
        }
    return {
        "month_elements": elements,
        "directions": directions,
    }


# ============================================================
# 五、全品种自动扫描 + TOP10 推荐（期货玄武）
# ============================================================
def scan_all_futures_daily(trade_date_str=None):
    """
    扫描全部收录期货品种的当日承载力
    返回按综合评分排序的品种列表
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    rotation = get_monthly_rotation(trade_date_str)
    rotation_elements = rotation["elements"] if rotation else []

    results = []
    for symbol, ipo in FUTURES_IPO_DATE_MAP.items():
        try:
            riyuan = get_riyuan_from_ipo(ipo)
            gan = riyuan["gan"]
            wx_futures = _resolve_futures_wuxing(symbol)

            trade_info = get_trade_day_info(trade_date_str)
            cs = get_chang_sheng(gan, trade_info["day_zhi"])
            stage = cs["stage_name"]
            capacity = cs["capacity_score"]

            star, label, verify = FUTURES_CAPACITY_STAR_MAP.get(
                stage, ("☆☆☆☆☆", "未知", "—"))
            expected = FUTURES_EXPECTED_RANGE.get(stage, "—")

            # 专业评级
            pro_bonus = 0.0
            pro_direction = ""
            for f in PRO_FUTURES_LONG:
                if f.get("symbol") == symbol:
                    pro_bonus = f["confidence"] / 100.0
                    pro_direction = f["direction"]
                    break
            if not pro_direction:
                for f in PRO_FUTURES_SHORT:
                    if f.get("symbol") == symbol:
                        pro_bonus = -f["confidence"] / 200.0
                        pro_direction = f["direction"]
                        break

            # 月度轮动加成（作为政策共振）
            rotation_bonus = 1.0 if wx_futures in rotation_elements else 0.5

            # 人气分（归一化 0-1）
            popularity = get_futures_popularity(symbol)

            # 期权策略
            opt_bs = get_option_buyer_seller_for_stage(stage)

            # 综合评分: 承载力0.60 + 人气0.20 + 政策共振0.20
            composite = capacity * 0.60 + popularity * 0.20 + rotation_bonus * 0.20

            # 阶段定性
            if stage in ("帝旺", "临官"):
                phase_label = "强趋势上行"
            elif stage in ("冠带", "沐浴"):
                phase_label = "偏强震荡"
            elif stage in ("长生", "养"):
                phase_label = "中性待变"
            elif stage in ("衰", "病", "胎"):
                phase_label = "弱势承压"
            else:
                phase_label = "极弱回避"

            results.append({
                "symbol": symbol,
                "name": _resolve_futures_name(symbol),
                "ipo_date": ipo,
                "riyuan_gan": gan,
                "riyuan_wuxing": riyuan["wuxing"],
                "futures_wuxing": wx_futures,
                "stage": stage,
                "star": star,
                "label": label,
                "capacity": capacity,
                "expected": expected,
                "pro_direction": pro_direction,
                "pro_bonus": pro_bonus,
                "rotation_bonus": rotation_bonus,
                "composite": round(composite, 3),
                "phase_label": phase_label,
                "opt_buyer": opt_bs["buyer_strategy"] if opt_bs else "—",
                "opt_seller": opt_bs["seller_strategy"] if opt_bs else "—",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["composite"], reverse=True)
    return {
        "trade_date": trade_date_str,
        "rotation_elements": rotation_elements,
        "total_scanned": len(results),
        "results": results,
    }


def generate_futures_top10(trade_date_str=None):
    """
    生成当日期货TOP10推荐 + 期权策略匹配表
    """
    scan = scan_all_futures_daily(trade_date_str)
    top10 = scan["results"][:10]

    bullish = [r for r in top10 if r["composite"] >= 0.25]
    bearish = [r for r in top10 if r["composite"] < 0.0]

    return {
        "trade_date": scan["trade_date"],
        "total_scanned": scan["total_scanned"],
        "rotation_elements": scan["rotation_elements"],
        "top10": top10,
        "bullish_count": len(bullish),
        "bearish_count": len(bearish),
        "summary": _top10_summary(top10),
    }


def _top10_summary(top10):
    bullish = [r for r in top10 if r["composite"] >= 0.25]
    bearish = [r for r in top10 if r["composite"] < 0.0]
    neutral = [r for r in top10 if 0.0 <= r["composite"] < 0.25]

    if len(bullish) >= 5:
        return "多头氛围浓厚，多个品种承载力共振偏强，可积极布局看涨方向"
    elif len(bearish) >= 5:
        return "空头主导，多数品种承载力极弱，以避险或做空为主，期权买方看跌优先"
    else:
        return "市场分化明显，强趋势品种与弱势品种并存，精选帝旺/临官级别品种做多，极弱品种做空或回避"


# ============================================================
# 六、三重共振扫描（天时 x 券商人气 x 板块政策）
# ============================================================
def scan_triple_resonance(trade_date_str=None):
    """
    扫描同时满足三个条件的品种：
    1. 承载力 >= ★★★★ (冠带/沐浴/帝旺/临官)
    2. 券商推荐人气 >= 3次（原始计数）
    3. 月度轮动五行匹配（政策正向共振）
    """
    scan = scan_all_futures_daily(trade_date_str)
    rotation_elements = scan["rotation_elements"]
    trade_info = get_trade_day_info(scan["trade_date"])
    month_ganzhi = trade_info["month_ganzhi"]

    triple_hits = []
    for r in scan["results"]:
        stage = r["stage"]
        if stage not in ("帝旺", "临官", "冠带", "沐浴"):
            continue
        pop_info = FUTURES_BROKER_POPULARITY.get(r["symbol"])
        if not pop_info or pop_info["count"] < 3:
            continue
        if r["futures_wuxing"] not in rotation_elements:
            continue

        rating = "SSS" if stage in ("帝旺", "临官") else "SS" if stage == "冠带" else "S"
        resonance_note = f"{r['futures_wuxing']}属性品种与月度轮动{'+'.join(rotation_elements)}正向共振"
        if r["pro_direction"] and "多" in r["pro_direction"]:
            resonance_note += " + 专业配置方向一致"

        triple_hits.append({
            "symbol": r["symbol"],
            "name": r["name"],
            "stage": r["stage"],
            "star": r["star"],
            "popularity_count": pop_info["count"],
            "popularity_brokers": pop_info["brokers"],
            "rotation_match": "+".join(rotation_elements),
            "resonance_note": resonance_note,
            "composite": r["composite"],
            "rating": rating,
        })

    triple_hits.sort(key=lambda x: x["composite"], reverse=True)
    return {
        "hits": triple_hits,
        "count": len(triple_hits),
        "month_ganzhi": month_ganzhi,
        "rotation_elements": rotation_elements,
    }


# ============================================================
# 七、帝旺/临官级品种完整推演（选TOP2）
# ============================================================
def generate_diwang_linguan_detail(trade_date_str=None):
    """
    从TOP10中筛选帝旺/临官级别的品种，选评分最高的2个做完整推演
    """
    top10 = generate_futures_top10(trade_date_str)
    diwang_candidates = [r for r in top10["top10"] if r["stage"] in ("帝旺", "临官")]

    if not diwang_candidates:
        diwang_candidates = [r for r in top10["top10"] if r["star"] in ("★★★★★", "★★★★☆")][:2]

    details = []
    for candidate in diwang_candidates[:2]:
        report = generate_futures_bazi_report(candidate["symbol"], top10["trade_date"])
        pop_info = FUTURES_BROKER_POPULARITY.get(candidate["symbol"])
        popularity_str = f"{pop_info['count']}次 ({pop_info['brokers']})" if pop_info else "无数据"

        direction = "做多" if candidate["composite"] >= 0.25 else "震荡偏多" if candidate["composite"] > 0 else "偏空"

        details.append({
            "name": report["name"],
            "symbol": report["symbol"],
            "ipo_date": report["ipo_date"],
            "riyuan_ganzhi": report["riyuan_ganzhi"],
            "riyuan_gan": report["riyuan_gan"],
            "riyuan_wuxing": report["riyuan_wuxing"],
            "trade_ganzhi": report["day_ganzhi"],
            "chang_sheng": report["chang_sheng_stage"],
            "star_display": report["star_display"],
            "direction": direction,
            "opt_buyer": candidate["opt_buyer"],
            "opt_seller": candidate["opt_seller"],
            "composite": candidate["composite"],
            "popularity": popularity_str,
            "entry_condition": "开盘后半小时站稳分时均线，成交量较前一交易日放大20%以上",
            "stop_loss": "按自身风险承受能力设定，例如跌破前一日最低价离场",
            "option_detail": f"买入平值/虚1档看涨期权，权利金不超过总资金2%",
        })

    return details


def format_futures_top10_table(report):
    """格式化TOP10为Markdown表格（完整版：含三重共振 + 帝旺/临官推演）"""
    trade_date = report["trade_date"]

    lines = [
        f"## 期货TOP10自动扫盘报告（主力合约智能版）",
        f"扫描日期: {trade_date} | 月度轮动五行: {'+'.join(report['rotation_elements'])} | 共扫描 {report['total_scanned']} 个品种",
        "",
        "### 合约选择说明",
        "",
        "> 本报告对每个品种自动选择**主力连续合约的八字原点**（首个合约上市日期）进行推演。",
        "> 当前实际交易请参考各品种具体主力合约代码（如 AU2606），但八字属性由首个合约决定。",
        "",
        "### TOP10 榜单",
        "",
        f"> {report['summary']}",
        "",
        "| 排名 | 品种 | 代码 | 主力合约示例 | 上市日期(首个) | 日元 | 承载力(十二长生) | 星级 | 方向预期 | 综合评分 | 期权买方策略 | 期权卖方策略 |",
        "|------|------|------|-------------|---------------|------|------------------|------|----------|----------|-------------|-------------|",
    ]
    for i, r in enumerate(report["top10"]):
        emoji = "🔴" if r["composite"] >= 0.25 else ("⚪" if r["composite"] >= 0 else "🔵")
        main_ct = get_main_contract(r["symbol"])
        lines.append(
            f"| {i+1} | {emoji}{r['name']} | {r['symbol']} | {main_ct} | {r['ipo_date']} | {r['riyuan_gan']}({r['futures_wuxing']}) | {r['stage']} | {r['star']} | {r['phase_label']} | {r['composite']:.2f} | {r['opt_buyer']} | {r['opt_seller']} |"
        )

    lines += [
        "",
        f"多头品种: {report['bullish_count']}个 | 空头品种: {report['bearish_count']}个",
    ]

    # ============ 三重共振扫描 ============
    triple = scan_triple_resonance(trade_date)
    lines += [
        "",
        "### 三重共振扫描（天时 x 券商人气 x 板块政策）",
        "",
    ]
    if triple["hits"]:
        lines.append(f"月度干支: {triple['month_ganzhi']} | 轮动五行: {'+'.join(triple['rotation_elements'])} | 共振品种: {triple['count']}个")
        lines.append("")
        lines.append("| 品种 | 天时 | 人气(次) | 推荐券商 | 政策共振 | 综合评级 |")
        lines.append("|------|------|----------|----------|----------|----------|")
        for h in triple["hits"]:
            lines.append(
                f"| {h['name']}({h['symbol']}) | {h['star']} {h['stage']} | {h['popularity_count']} | {h['popularity_brokers']} | {h['rotation_match']}利好 | {h['rating']} |"
            )
    else:
        lines.append("> 当日无品种同时满足三重共振条件（承载力>=★★★★ + 人气>=3次 + 政策正向共振）")

    # ============ 帝旺/临官级完整推演 ============
    details = generate_diwang_linguan_detail(trade_date)
    if details:
        lines += [
            "",
            "### 帝旺/临官级品种完整推演",
            "",
        ]
        for d in details:
            lines += [
                f"#### 八字期货推演 — {d['name']}（主力合约 {get_main_contract(d['symbol'])}）",
                "",
                f"- 上市日期: {d['ipo_date']} -> 日柱干支: {d['riyuan_ganzhi']} -> 日元: {d['riyuan_gan']}({d['riyuan_wuxing']})",
                f"- 目标交易日干支: {d['trade_ganzhi']}",
                f"- 承载力: {d['chang_sheng']} (十二长生) -> {d['star_display']}",
                f"- 期货方向: {d['direction']}",
                f"- 券商推荐: {d['popularity']}",
                f"- 开仓条件: {d['entry_condition']}",
                f"- 止损建议: {d['stop_loss']}",
                f"- 期权策略: {d['option_detail']}",
                "",
            ]

    lines += [
        "---",
        "",
        "### 风险提示与免责声明",
        "",
        "> 本报告基于八字五行推演和公开信息整理，仅供内部研究学习，不构成任何投资建议。"
        "期货、期权交易风险极高，可能造成超过本金投入的损失。"
        "所有策略均需投资者根据自身风险承受能力独立决策，并设置硬性止损。"
        "市场有风险，入市须谨慎。",
    ]
    return "\n".join(lines)


# ============================================================
# 五、联网数据来源集成参考
# ============================================================
FUTURES_DATA_SOURCES_REFERENCE = [
    {"category": "品种上市日期",       "search_suggestion": "搜索「[品种名称] 期货 上市日期 交易所」",               "purpose": "获取期货合约的日元五行"},
    {"category": "期权上市日期",       "search_suggestion": "搜索「[品种名称] 期权 上市 交易 通知」→ 上期所官网",        "purpose": "期权合约生日排盘"},
    {"category": "主力合约筛选",       "search_suggestion": "通过持仓量/成交量排名找主流交割月",                    "purpose": "确定当前活跃合约"},
    {"category": "每日收盘数据+量比",  "search_suggestion": "AI联网搜索每日市场数据+量比",                        "purpose": "量价齐生验证"},
    {"category": "期权合约IV",          "search_suggestion": "交易所官网/专业期权数据网站（隐含波动率曲线）",         "purpose": "波动率骗炮检测"},
    {"category": "交易日干支(黄历)",    "search_suggestion": "支持联网版AI；或用户提供基准排盘日期",                 "purpose": "天时承载力计算基础"},
    {"category": "最新交割/换月日历",  "search_suggestion": "实时联网，合约最后交易日查询",                       "purpose": "期货交割风险规避"},
    {"category": "政策/事件",           "search_suggestion": "与股票同步，每日手动输入或AI联网抓取",                "purpose": "五行政策映射"},
]
