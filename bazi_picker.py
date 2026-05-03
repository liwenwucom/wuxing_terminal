# -*- coding: utf-8 -*-
"""
八字选股助手 — 每日推演报告生成器
基于 IPO 日元 × 交易日地支 → 十二长生承载力 → 追/等/撤决策

报告模板（六段式）：
一、基础信息（品种+日元+窗口）
二、当日承载力（干支+十二长生+预期区间）
三、量价验证框架（承载力变化 × 涨幅变化 → 定性）
四、政策五行映射（事件→五行→对品种影响）
五、短线策略框架（追/等/撤+期权思路+止损）
六、综合结论（3句话以内）
"""

from datetime import datetime
from bazi_capacity import (
    get_riyuan_from_ipo, get_trade_day_info, get_chang_sheng,
    IPO_DATE_MAP, TIANGAN_WUXING, DIZHI_WUXING,
    CAPACITY_SCORES, STAGE_NAMES, CHANG_SHENG_TABLE,
)
from wuxing_timing import STAR_RATINGS, get_timing_signal, _classify_sheng_ke

# ============================================================
# 量价验证速判表
# ============================================================
PRICE_VOLUME_RULES = [
    {"capacity_change": "+", "return_change": "+", "verdict": "真实资金入场", "action": "顺势参与，仓位按风险承受能力设定"},
    {"capacity_change": "+", "return_change": "≤", "verdict": "骗炮嫌疑", "action": "不追高，已有仓位减磅或止盈"},
    {"capacity_change": "-", "return_change": "+", "verdict": "短线透支", "action": "勿追，有仓位者逢高部分止盈"},
    {"capacity_change": "-", "return_change": "≤", "verdict": "预期内自然调整", "action": "观望，等待下个承载力增强窗口"},
]


def classify_pv(capacity_up, return_up):
    """根据承载力变化和涨幅变化返回量价验证结果"""
    cap_sym = "+" if capacity_up else "-"
    ret_sym = "+" if return_up else "≤"
    for rule in PRICE_VOLUME_RULES:
        if rule["capacity_change"] == cap_sym and rule["return_change"] == ret_sym:
            return rule
    return PRICE_VOLUME_RULES[3]


def _summarize_stem_table(riyuan_gan):
    """生成指定天干的十二长生速查文本"""
    table = CHANG_SHENG_TABLE.get(riyuan_gan, {})
    lines = [f"{riyuan_gan}('{TIANGAN_WUXING.get(riyuan_gan,'')}')十二长生:"]
    ordered = sorted(table.items(), key=lambda x: x[1])
    stages = [f"{zhi}{STAGE_NAMES[idx]}" for zhi, idx in ordered]
    lines.append("  " + " → ".join(stages))
    return "\n".join(lines)


def generate_bazi_report(stock_code, stock_name=None, trade_date_str=None,
                         prev_return_pct=None, policy_events=None):
    """
    生成八字选股完整推演报告
    
    :param stock_code: 股票代码
    :param stock_name: 股票名称（可选）
    :param trade_date_str: 目标交易日 'YYYY-MM-DD'
    :param prev_return_pct: 前一日实际涨跌幅%（可选，用于量价验证）
    :param policy_events: 当日政策/事件列表（可选）
    :return: 完整报告 dict
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")

    ipo = IPO_DATE_MAP.get(stock_code, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    trade_info = get_trade_day_info(trade_date_str)
    chang_sheng = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])

    stage = chang_sheng["stage_name"]
    capacity = chang_sheng["capacity_score"]
    star_info = STAR_RATINGS.get(stage, (0, "☆☆☆☆☆", "未知", (-1.0, 1.0)))
    stars, star_str, star_label, exp_range = star_info
    sheng_ke = _classify_sheng_ke(riyuan["gan"], trade_info["day_zhi"])
    timing = get_timing_signal(stage, sheng_ke, capacity)

    # 获取前一日承载力（用于量价验证）
    from datetime import timedelta
    prev_date = (datetime.strptime(trade_date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_info = get_trade_day_info(prev_date)
    prev_cs = get_chang_sheng(riyuan["gan"], prev_info["day_zhi"])
    capacity_up = capacity > prev_cs["capacity_score"]

    # 量价验证
    pv_result = None
    if prev_return_pct is not None:
        # 简化：当前无法知道今日实际涨幅，仅给框架
        pv_result = {
            "framework": True,
            "prev_capacity": prev_cs["stage_name"],
            "curr_capacity": stage,
            "capacity_up": capacity_up,
            "prev_return": prev_return_pct,
            "rule_table": [f"{r['capacity_change']}容量 {r['return_change']}涨幅 → {r['verdict']}: {r['action']}" for r in PRICE_VOLUME_RULES],
        }

    report = {
        # 一、基础信息
        "stock_code": stock_code,
        "stock_name": stock_name or stock_code,
        "ipo_date": ipo,
        "riyuan_gan": riyuan["gan"],
        "riyuan_zhi": riyuan["zhi"],
        "riyuan_wuxing": riyuan["wuxing"],
        "riyuan_ganzhi": riyuan["ganzhi"],
        "target_date": trade_date_str,
        "prev_return": prev_return_pct,

        # 二、当日承载力
        "year_ganzhi": trade_info["year_ganzhi"],
        "month_ganzhi": trade_info["month_ganzhi"],
        "day_ganzhi": trade_info["day_ganzhi"],
        "day_gan": trade_info["day_gan"],
        "day_zhi": trade_info["day_zhi"],
        "chang_sheng_stage": stage,
        "capacity_score": capacity,
        "star_display": star_str,
        "star_label": star_label,
        "expected_range": f"{exp_range[0]:+.1f}% ~ {exp_range[1]:+.1f}%",
        "prev_stage": prev_cs["stage_name"],
        "prev_capacity": prev_cs["capacity_score"],
        "capacity_up": capacity_up,

        # 三、量价验证
        "pv_analysis": pv_result,

        # 四、政策五行
        "policy_events": policy_events or [],
        "sheng_ke_type": sheng_ke,
        "sheng_ke_desc": _describe_sheng_ke(riyuan["gan"], trade_info["day_zhi"], sheng_ke),

        # 五、短线策略
        "timing_signal": timing["signal"],
        "timing_rationale": timing["rationale"],
        "option_hint": timing["option_hint"],
        "stop_loss_reminder": "单笔最大亏损限额按自身风险承受能力设定，严禁借贷或使用短期生活必须资金",

        # 六、综合结论
        "stem_table": _summarize_stem_table(riyuan["gan"]),
        "annual_note": "2026丙午年天地皆火，生助戊土股市，大牛市基础年份",
    }

    report["conclusion"] = _generate_conclusion(report)
    return report


def _describe_sheng_ke(gan, zhi, sk_type):
    gan_wx = TIANGAN_WUXING.get(gan, "?")
    zhi_wx = DIZHI_WUXING.get(zhi, "?")
    if sk_type == "生助":
        return f"地支{zhi}({zhi_wx})生日元{gan}({gan_wx})→得生，承载力增强"
    elif sk_type == "受克":
        return f"地支{zhi}({zhi_wx})克日元{gan}({gan_wx})→受克，承载力被压制"
    elif sk_type == "平衡":
        if gan_wx == zhi_wx:
            return f"日元{gan}({gan_wx})与日支{zhi}({zhi_wx})同五行，气场平稳"
        return f"日元{gan}({gan_wx})与日支{zhi}({zhi_wx})生克平衡"
    return "关系待查"


def _generate_conclusion(report):
    sig = report["timing_signal"]
    stage = report["chang_sheng_stage"]
    name = report["stock_name"]
    sk = report["sheng_ke_type"]

    if sig == "追":
        return f"{name}今日承载力{stage}极强+天时{sk}，属时空共振窗口，短线顺势但需设止损。"
    elif sig == "撤":
        return f"{name}今日承载力{stage}偏弱+天时{sk}，建议观望回避，等待下个帝旺/临官日。"
    return f"{name}今日承载力{stage}中等+天时{sk}，方向不明朗，维持区间思路等待信号确认。"


def format_bazi_report(report):
    """将报告格式化为 Markdown 文本"""
    lines = [
        f"## 🧧 八字选股报告 — {report['stock_name']} ({report['stock_code']})",
        "",
        "### 一、基础信息",
        f"- 品种：{report['stock_name']} {report['stock_code']}",
        f"- 上市日期：{report['ipo_date']}",
        f"- 日元属性：{report['riyuan_gan']}({report['riyuan_wuxing']}) | 日柱：{report['riyuan_ganzhi']}",
        f"- 目标交易日：{report['target_date']}",
        f"- 前一日涨跌幅：{report['prev_return']}%（{'已提供' if report['prev_return'] is not None else '未提供'}）",
        "",
        "### 二、当日承载力",
        f"- 交易日四柱：{report['year_ganzhi']} {report['month_ganzhi']} {report['day_ganzhi']}",
        f"- 日元 × 日支：{report['riyuan_gan']}('{report['riyuan_wuxing']}') × {report['day_zhi']}('{DIZHI_WUXING.get(report['day_zhi'],'')}')",
        f"- 十二长生：**{report['chang_sheng_stage']}**",
        f"- 承载力等级：{report['star_display']} {report['star_label']}",
        f"- 预期涨幅区间：{report['expected_range']}",
        f"- 前一日承载力：{report['prev_stage']}({report['prev_capacity']}) → {'增强' if report['capacity_up'] else '减弱'}",
        "",
        "### 三、量价验证框架",
    ]

    pv = report.get("pv_analysis")
    if pv and pv.get("framework"):
        lines.append("- ⚠️ 需收盘后按以下规则判断：")
        for r in pv["rule_table"]:
            lines.append(f"  - {r}")
    else:
        lines.append("- 未提供前一日涨跌幅，收盘后可对照承载力变化自行验证")

    lines += [
        "",
        "### 四、政策五行映射",
        f"- 日柱生克：{report['sheng_ke_desc']}",
        f"- 生克类型：{report['sheng_ke_type']}",
    ]
    if report.get("policy_events"):
        lines.append("- 当日政策/事件：")
        for e in report["policy_events"]:
            lines.append(f"  - {e}")

    lines += [
        "",
        "### 五、短线策略框架",
        f"- 信号判断：**{'🔥追' if report['timing_signal']=='追' else '⏳等' if report['timing_signal']=='等' else '🛑撤'}**",
        f"- 策略叙述：{report['timing_rationale']}",
        f"- 期权思路：{report['option_hint']}",
        f"- 止损提醒：{report['stop_loss_reminder']}",
        "",
        "### 六、综合结论",
        report["conclusion"],
        "",
        f"*{report['annual_note']}*",
        "",
        "---",
        report["stem_table"],
    ]
    return "\n".join(lines)


# ============================================================
# 快捷函数：单行调用
# ============================================================
def quick_report(stock_code, date_str=None):
    """快捷生成某只股票某日的八字报告"""
    return generate_bazi_report(stock_code, trade_date_str=date_str)


def batch_report(codes, date_str=None):
    """批量生成多只股票的报告"""
    results = []
    for code in codes:
        code = code.strip()
        if code:
            results.append(generate_bazi_report(code, trade_date_str=date_str))
    return results


# ============================================================
# 后续3日承载力推演引擎
# ============================================================
def get_next_n_trading_days(base_date_str=None, n=3):
    """
    推算后续 N 个交易日（跳过周末，不含法定节假日）
    :param base_date_str: 基准日期 'YYYY-MM-DD'，默认今天
    :param n: 需要推算的交易日数量
    :return: [date_str1, date_str2, ...]
    """
    from datetime import timedelta
    base = datetime.strptime(base_date_str, "%Y-%m-%d") if base_date_str else datetime.now()
    trading_days = []
    cursor = base
    while len(trading_days) < n:
        cursor = cursor + timedelta(days=1)
        if cursor.weekday() < 5:
            trading_days.append(cursor.strftime("%Y-%m-%d"))
    return trading_days


# 承载力星级映射
CAPACITY_STAR_MAP = {
    "帝旺": ("★★★★★", "极强"), "临官": ("★★★★★", "极强"),
    "冠带": ("★★★★☆", "较强"), "沐浴": ("★★★★☆", "较强"),
    "长生": ("★★★☆☆", "中等"),
    "衰": ("★★☆☆☆", "较弱"), "病": ("★★☆☆☆", "较弱"),
    "死": ("★☆☆☆☆", "极弱"), "墓": ("★☆☆☆☆", "极弱"),
    "绝": ("★☆☆☆☆", "极弱"), "胎": ("★☆☆☆☆", "极弱"),
    "养": ("★☆☆☆☆", "极弱"),
}

# 承载力对应的量价验证阈值
CAPACITY_THRESHOLD = {
    "帝旺": "需放量上涨≥1.5%，开盘半小时量比≥1.3",
    "临官": "需放量上涨≥1.0%，开盘半小时量比≥1.2",
    "冠带": "温和放量上涨≥0.5%即可，量比≥1.0",
    "沐浴": "窄幅震荡预期，涨跌幅≤±0.8%为正常",
    "长生": "可静待观察，若量大涨幅>1%可轻仓试",
    "衰": "不建议开新仓，有仓位者减至半仓以下",
    "病": "坚决不加仓，冲高即减仓",
}


def generate_forward_report(stock_code, trade_date_str=None):
    """
    生成后续3个交易日承载力推演报告
    :return: 完整前瞻报告 dict
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    ipo = IPO_DATE_MAP.get(stock_code, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    gan = riyuan["gan"]
    wx = riyuan["wuxing"]

    # 推断 T+0 (基准日) 和 T+1 ~ T+3
    next_3 = get_next_n_trading_days(trade_date_str, 3)
    all_dates = [trade_date_str] + next_3

    daily_rows = []
    for i, d in enumerate(all_dates):
        info = get_trade_day_info(d)
        cs = get_chang_sheng(gan, info["day_zhi"])
        stage = cs["stage_name"]
        star, label = CAPACITY_STAR_MAP.get(stage, ("☆☆☆☆☆", "未知"))
        threshold = CAPACITY_THRESHOLD.get(stage, "—")

        daily_rows.append({
            "day_label": f"T+{i}" if i > 0 else "T+0(今日)",
            "date": d,
            "day_ganzhi": info["day_ganzhi"],
            "day_gan": info["day_gan"],
            "day_zhi": info["day_zhi"],
            "stage": stage,
            "star": star,
            "label": label,
            "capacity_score": cs["capacity_score"],
            "threshold": threshold,
        })

    # 节奏规划
    rhythm = _plan_rhythm(daily_rows)

    return {
        "stock_code": stock_code,
        "stock_name": _resolve_name(stock_code),
        "ipo_date": ipo,
        "riyuan_gan": gan,
        "riyuan_wuxing": wx,
        "riyuan_ganzhi": riyuan["ganzhi"],
        "base_date": trade_date_str,
        "next_dates": next_3,
        "daily_rows": daily_rows,
        "rhythm": rhythm,
    }


def _plan_rhythm(daily_rows):
    """根据承载力变化轨迹生成节奏规划"""
    actions = []
    prev_stage = None
    prev_score = None

    for row in daily_rows:
        stage = row["stage"]
        score = row["capacity_score"]
        dl = row["day_label"]
        date = row["date"]

        if stage in ("帝旺", "临官"):
            action = "加仓"
            detail = f"{row['star']} {stage}窗口，{row['threshold']}，满足条件可分批加仓"
        elif stage in ("冠带", "沐浴"):
            if prev_stage in ("帝旺", "临官"):
                action = "持有/轻减仓"
                detail = f"承载力从{prev_stage}降至{stage}，已获利仓位可部分止盈，剩余持有"
            else:
                action = "持有"
                detail = f"承载力{stage}中等偏强，维持现有仓位观察"
        elif stage in ("长生", "养"):
            action = "观望"
            detail = f"承载力{stage}中性，静待下一信号明确后再操作"
        elif stage in ("衰", "病"):
            action = "减仓"
            detail = f"承载力{stage}偏弱，减至半仓以下，不宜开新仓"
        else:
            action = "回避"
            detail = f"承载力{stage}极弱，建议空仓回避"

        # 轨迹变化加成
        if prev_score is not None:
            if score > prev_score and prev_stage in ("死", "墓", "绝", "病", "衰"):
                action = "试探性加仓"
                detail += f" | >> 承载力从{prev_stage}→{stage}，趋势逆转信号，可轻仓试探"

        actions.append({
            "day_label": dl,
            "date": date,
            "stage": stage,
            "action": action,
            "detail": detail,
        })
        prev_stage = stage
        prev_score = score

    # 整段总结
    stages = [a["stage"] for a in actions]
    if all(s in ("帝旺", "临官") for s in stages[1:]):
        overview = "连续极强窗口，核心做多周期，可滚动加仓"
    elif any(s in ("死", "墓", "绝") for s in stages[1:]):
        overview = "承载力出现极弱节点，短期回避为宜，等待下个帝旺日"
    elif any(s in ("帝旺", "临官") for s in stages[1:]) and any(s in ("衰", "病", "死") for s in stages[1:]):
        overview = "承载力波动剧烈，T+1如有帝旺则快进快出，后续乏力即收手"
    else:
        overview = "承载力整体平淡，短线无突出机会，维持轻仓或观望"

    return {
        "daily_actions": actions,
        "overview": overview,
    }


def format_forward_report(report):
    """格式化后续3日推演为 Markdown"""
    r = report
    lines = [
        f"## ⏭️ 后续3日承载力推演 — {r['stock_name']} ({r['stock_code']})",
        "",
        "### 一、基础信息",
        f"- 品种：{r['stock_name']} {r['stock_code']}",
        f"- 上市日期：{r['ipo_date']}",
        f"- 日元属性：{r['riyuan_gan']}({r['riyuan_wuxing']}) | 日柱：{r['riyuan_ganzhi']}",
        f"- 基准日期：{r['base_date']}",
        f"- 后续3个交易日：{' | '.join(r['next_dates'])}",
        "",
        "### 二、后续3日承载力变化表",
        "",
        "| 交易日 | 公历日期 | 日柱干支 | 日元×日支 | 十二长生位 | 承载力等级 | 量价验证信号 |",
        "|--------|----------|----------|------------|------------|------------|--------------|",
    ]
    for row in r["daily_rows"]:
        lines.append(
            f"| {row['day_label']} | {row['date']} | {row['day_ganzhi']} | {r['riyuan_gan']}({r['riyuan_wuxing']})×{row['day_zhi']} | {row['stage']} | {row['star']} {row['label']} | {row['threshold']} |"
        )

    rhythm = r["rhythm"]
    lines += [
        "",
        "### 三、离场/加仓节奏规划",
        "",
        "| 交易日 | 日期 | 承载力 | 操作建议 | 具体理由 |",
        "|--------|------|--------|----------|----------|",
    ]
    for a in rhythm["daily_actions"]:
        lines.append(f"| {a['day_label']} | {a['date']} | {a['stage']} | **{a['action']}** | {a['detail']} |")

    lines += [
        "",
        "### 四、综合节奏建议",
        f"> {rhythm['overview']}",
        "",
    ]
    for a in rhythm["daily_actions"]:
        lines.append(f"- **{a['day_label']}**（{a['date']}）：建议 **{a['action']}** — {a['stage']} | {a['detail']}")

    lines += [
        "",
        "### 五、重要免责声明",
        "> 本推演基于八字十二长生理论，仅为传统文化视角的沙盘演练，不构成任何投资建议。实际交易请结合自身风险承受能力、市场实时走势、持牌机构意见独立决策。期货/期权交易风险极高，可能亏损超过本金，严禁借贷交易。",
        "",
        "---",
    ]
    return "\n".join(lines)


def _resolve_name(code):
    """解析股票名称（尝试从多个数据源获取）"""
    try:
        from bazi_live_scanner import get_popularity_info
        info = get_popularity_info(code)
        if info["name"] != code:
            return info["name"]
    except ImportError:
        pass
    return code
