# -*- coding: utf-8 -*-
"""
联网版八字选股推演引擎
—— 天时分析 → 帝旺扫描 → 券商金股交叉 → 三重共振报告

推演流水线：
一、当日天时分析（四柱 + 大盘戊土承载力 + 各日元帝旺判定）
二、联网券商金股池（模拟版，可替换为真实 API）
三、帝旺共振扫描（天时 × 券商人气 × 日元承载力）
四、逐股完整推演报告（六段式）
五、数据来源附录
"""

from datetime import datetime
from bazi_capacity import (
    get_riyuan_from_ipo, get_trade_day_info, get_chang_sheng,
    IPO_DATE_MAP, TIANGAN_WUXING, DIZHI_WUXING,
    CAPACITY_SCORES, STAGE_NAMES, CHANG_SHENG_TABLE,
    get_market_annual_assessment,
)
from wuxing_timing import STAR_RATINGS, get_timing_signal, _classify_sheng_ke
from bazi_picker import generate_bazi_report, format_bazi_report, PRICE_VOLUME_RULES
from policy_analyzer import get_monthly_rotation, get_rotation_bonus


# ============================================================
# 一、联网券商金股池（2026年5月，16家券商）
# 数据来源：第一财经·Wind / 新浪财经券商研报
# ============================================================
BROKER_GOLD_POOL_2026_05 = [
    {
        "broker": "国联民生证券",
        "date": "2026-04-30",
        "picks": ["赤峰黄金", "潞安环能", "新和成", "比亚迪", "工业富联", "寒武纪", "中际旭创", "海信视像", "中国太保", "安井食品"],
        "codes": ["600988", "601699", "002001", "002594", "601138", "688256", "300308", "600060", "601601", "603345"],
    },
    {
        "broker": "中信证券",
        "date": "2026-04-30",
        "picks": ["制冷剂龙头", "涤纶长丝龙头", "海缆龙头", "建材龙头", "稀土龙头", "船舶发动机龙头"],
        "codes": [],  # 行业方向，非个股
        "themes": ["制冷剂", "涤纶长丝", "海缆", "建材", "稀土", "船舶发动机"],
    },
    {
        "broker": "太平洋证券",
        "date": "2026-04-30",
        "picks": ["TCL电子", "天康生物", "璞泰来", "美埃科技", "安井食品"],
        "codes": ["000100", "002100", "603659", "688376", "603345"],
    },
    {
        "broker": "华龙证券",
        "date": "2026-04-30",
        "picks": ["中际旭创", "比亚迪"],
        "codes": ["300308", "002594"],
    },
    {
        "broker": "光大证券",
        "date": "2026-04-30",
        "picks": ["中际旭创"],
        "codes": ["300308"],
    },
    {
        "broker": "中国银河",
        "date": "2026-04-30",
        "picks": ["中际旭创"],
        "codes": ["300308"],
    },
    {
        "broker": "国金证券",
        "date": "2026-04-30",
        "picks": ["工业富联"],
        "codes": ["601138"],
    },
]

# 5月金股人气排名（多券商共同推荐次数）
GOLD_STOCK_POPULARITY_2026_05 = {
    "603345": {"name": "安井食品", "count": 5},
    "300308": {"name": "中际旭创", "count": 4},
    "688041": {"name": "海光信息", "count": 2},
    "601088": {"name": "中国神华", "count": 2},
    "002594": {"name": "比亚迪", "count": 2},
    "601138": {"name": "工业富联", "count": 2},
    "600988": {"name": "赤峰黄金", "count": 1},
    "601699": {"name": "潞安环能", "count": 1},
    "002001": {"name": "新和成", "count": 1},
    "688256": {"name": "寒武纪", "count": 1},
    "601601": {"name": "中国太保", "count": 1},
}

# ============================================================
# 二、联网数据来源登记表
# ============================================================
DATA_SOURCES = [
    {"category": "A股年度IPO一览", "source": "同花顺·数据中心", "purpose": "上市日期数据源"},
    {"category": "十六家券商金股(5月)", "source": "第一财经·Wind数据", "purpose": "庚金标的识别 + 三重共振验证"},
    {"category": "国联民生五月金股组合", "source": "新浪财经·券商研报", "purpose": "个股推荐名单"},
    {"category": "中信证券亮马五月组合", "source": "中信证券研究", "purpose": "板块轮动+庚金方向"},
    {"category": "太平洋证券五月金股", "source": "新浪财经·券商研报", "purpose": "个股推荐名单"},
    {"category": "浙商证券板块轮动报告", "source": "浙商策略", "purpose": "五月大盘定性：成长扩散"},
    {"category": "央行买断式逆回购", "source": "中国人民银行公告", "purpose": "流动性判断"},
    {"category": "干支 + 黄历信息", "source": "君子阁/农历计算", "purpose": "天时基础"},
]


# ============================================================
# 三、一键扫描：当日帝旺级品种
# ============================================================
def scan_daily_diwang(trade_date_str=None):
    """
    扫描当日所有收录股票，按十二长生阶段分组
    返回每种日元下帝旺/临官/冠带/其他 的品种列表
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    trade_info = get_trade_day_info(trade_date_str)
    day_zhi = trade_info["day_zhi"]

    stems = {}
    for code, ipo in IPO_DATE_MAP.items():
        riyuan = get_riyuan_from_ipo(ipo)
        gan = riyuan["gan"]
        cs = get_chang_sheng(gan, day_zhi)

        name = _resolve_stock_name(code)
        if gan not in stems:
            stems[gan] = {"帝旺": [], "临官": [], "冠带": [], "其他": [],
                          "wuxing": TIANGAN_WUXING.get(gan, "未知")}
        entry = {
            "code": code, "name": name, "ipo": ipo,
            "riyuan_gan": gan, "riyuan_wuxing": riyuan["wuxing"],
            "stage": cs["stage_name"], "capacity": cs["capacity_score"],
        }

        stage = cs["stage_name"]
        if stage in ("帝旺", "临官", "冠带"):
            stems[gan][stage].append(entry)
        else:
            stems[gan]["其他"].append(entry)

    return {
        "trade_date": trade_date_str,
        "day_zhi": day_zhi,
        "day_ganzhi": trade_info["day_ganzhi"],
        "month_ganzhi": trade_info["month_ganzhi"],
        "year_ganzhi": trade_info["year_ganzhi"],
        "stems": stems,
    }


# ============================================================
# 四、三重共振评分（天时 × 券商人气 × 日元承载力）
# ============================================================
def calculate_triple_resonance(stock_code, trade_date_str=None):
    """
    对某只股票计算三重共振得分
    - 天时(帝旺/临官)→ 满分 40
    - 券商人气(推荐次数)→ 满分 30
    - 板块与政策(五行共振)→ 满分 30
    总分 0-100
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    ipo = IPO_DATE_MAP.get(stock_code, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    trade_info = get_trade_day_info(trade_date_str)
    cs = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])
    stage = cs["stage_name"]

    # 1. 天时分（帝旺40 / 临官30 / 冠带20 / 其他0）
    tianshi_scores = {"帝旺": 40, "临官": 30, "冠带": 20, "沐浴": 10}
    tianshi = tianshi_scores.get(stage, 0)

    # 2. 券商人气分（最多5次推荐）
    pop = GOLD_STOCK_POPULARITY_2026_05.get(stock_code, {"count": 0})
    popularity = min(30, pop["count"] * 6)

    # 3. 板块政策分（基于月度轮动）
    rotation_bonus = get_rotation_bonus(stock_code)
    policy = int(rotation_bonus * 30)

    total = tianshi + popularity + policy
    return {
        "code": stock_code,
        "name": _resolve_stock_name(stock_code),
        "stage": stage,
        "tianshi": tianshi,
        "popularity": popularity,
        "pop_count": pop.get("count", 0),
        "policy": policy,
        "total": total,
        "resonance_level": "三重共振" if total >= 70 else ("双重共振" if total >= 45 else "单信号"),
    }


# ============================================================
# 五、联网版完整日报
# ============================================================
def generate_live_daily_report(trade_date_str=None):
    """
    生成联网版八字选股日报
    流程: 天时分析 → 帝旺扫描 → 券商交叉 → 共振排名 → 逐股推演
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")

    # Step 0: 基础信息
    trade_info = get_trade_day_info(trade_date_str)
    day_gan = trade_info["day_gan"]
    day_zhi = trade_info["day_zhi"]
    annual = get_market_annual_assessment(trade_info["year_ganzhi"])

    # 大盘承载力(戊土见日支)
    market_cs = get_chang_sheng("戊", day_zhi)
    market_stage = market_cs["stage_name"]
    market_stars = STAR_RATINGS.get(market_stage, (0, "☆☆☆☆☆", "未知", (-1.0, 1.0)))

    # Step 1: 帝旺扫描
    scan = scan_daily_diwang(trade_date_str)

    # Step 2: 各日元当日承载力速判
    stem_capacity = {}
    for gan in TIANGAN_WUXING:
        if gan not in CHANG_SHENG_TABLE:
            continue
        cs = get_chang_sheng(gan, day_zhi)
        star_info = STAR_RATINGS.get(cs["stage_name"], (0, "☆☆☆☆☆", "未知", (-1.0, 1.0)))
        stem_capacity[gan] = {
            "wuxing": TIANGAN_WUXING[gan],
            "stage": cs["stage_name"],
            "stars": star_info[1],
            "label": star_info[2],
            "range": f"{star_info[3][0]:+.1f}%~{star_info[3][1]:+.1f}%",
        }

    # Step 3: 三重共振评分（对所有收录股票）
    all_resonance = []
    for code in IPO_DATE_MAP:
        r = calculate_triple_resonance(code, trade_date_str)
        all_resonance.append(r)
    all_resonance.sort(key=lambda x: x["total"], reverse=True)

    # Step 4: 顶级共振标的（帝旺+高人气）
    top_resonance = [r for r in all_resonance if r["total"] >= 45][:10]

    # Step 5: 帝旺级标的逐股报告
    diwang_reports = []
    diwang_codes = []
    for r in all_resonance:
        if r["stage"] == "帝旺" and r["code"] in IPO_DATE_MAP:
            diwang_codes.append(r["code"])
    for code in diwang_codes[:6]:
        try:
            rep = generate_bazi_report(code, trade_date_str=trade_date_str)
            diwang_reports.append(rep)
        except Exception:
            pass

    # Step 6: 月度轮动参考
    rotation = get_monthly_rotation(trade_date_str)

    # Step 7: 构建报告
    report = {
        "trade_date": trade_date_str,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        # 天时分析
        "year_ganzhi": trade_info["year_ganzhi"],
        "month_ganzhi": trade_info["month_ganzhi"],
        "day_ganzhi": trade_info["day_ganzhi"],
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "day_wuxing": TIANGAN_WUXING.get(day_gan, "未知"),

        # 大盘
        "market_stage": market_stage,
        "market_stars": market_stars[1],
        "market_label": market_stars[2],
        "market_range": f"{market_stars[3][0]:+.1f}%~{market_stars[3][1]:+.1f}%",
        "market_note": _market_note(market_stage),

        # 年度
        "annual_grade": annual["grade"],
        "annual_ganzhi": annual["year_ganzhi"],

        # 各日元速判
        "stem_capacity": stem_capacity,

        # 帝旺扫描
        "scan_summary": {gan: {k: len(v) for k, v in info.items()}
                         for gan, info in scan["stems"].items()},

        # 三重共振排名
        "top_resonance": top_resonance[:15],

        # 帝旺级逐股报告
        "diwang_reports": diwang_reports,
        "diwang_count": len(diwang_reports),

        # 券商金股
        "broker_gold_pool": BROKER_GOLD_POOL_2026_05,
        "gold_popularity": GOLD_STOCK_POPULARITY_2026_05,

        # 月度轮动
        "rotation": rotation,

        # 数据来源
        "data_sources": DATA_SOURCES,
    }
    return report


# ============================================================
# 六、格式化输出
# ============================================================
def format_live_report(report):
    """将联网日报格式化为 Markdown"""
    lines = [
        f"# 🔮 {report['trade_date']} 联网八字选股推演日报",
        f"生成时间：{report['generated_at']}",
        "",
        "---",
        "## 一、当日天时分析",
        "",
        f"| 项目 | 信息 |",
        f"|------|------|",
        f"| 公历日期 | {report['trade_date']} |",
        f"| 四柱八字 | {report['year_ganzhi']} {report['month_ganzhi']} {report['day_ganzhi']} |",
        f"| 日柱干支 | {report['day_ganzhi']}（{report['day_gan']}{TIANGAN_WUXING.get(report['day_gan'],'')}日干，{report['day_zhi']}{DIZHI_WUXING.get(report['day_zhi'],'')}日支） |",
        f"| 大盘戊土 | {report['market_stars']} {report['market_stage']} |",
        f"| 预期区间 | {report['market_range']} |",
        f"| 年度格局 | {report['annual_grade']}（{report['annual_ganzhi']}年） |",
        "",
        report["market_note"],
        "",
        "---",
        "## 二、各日元承载力速判",
        "",
    ]

    # 承载力表
    gan_order = ["庚", "辛", "丙", "丁", "甲", "乙", "壬", "癸", "戊", "己"]
    for gan in gan_order:
        if gan in report["stem_capacity"]:
            sc = report["stem_capacity"][gan]
            signal = "🔥🔥🔥 当日最强" if sc["stage"] == "帝旺" else (
                "★★ 偏强" if sc["stage"] in ("临官", "冠带") else
                "· 一般" if sc["stage"] in ("沐浴", "长生", "衰", "养") else
                "⚠ 偏弱"
            )
            lines.append(f"- **{gan}({sc['wuxing']})** → {sc['stage']} | {sc['stars']} | {signal} | 预期{sc['range']}")

    lines += [
        "",
        "---",
        "## 三、三重共振扫描（天时×券商人气×板块政策）",
        "",
        "| 排名 | 品种 | 阶段 | 天时 | 人气(次) | 政策 | 总分 | 共振 |",
        "|------|------|------|------|----------|------|------|------|",
    ]
    for i, r in enumerate(report["top_resonance"][:12]):
        lines.append(
            f"| {i+1} | {r['name']}({r['code']}) | {r['stage']} | {r['tianshi']} | {r['pop_count']} | {r['policy']} | **{r['total']}** | {r['resonance_level']} |"
        )

    lines += [
        "",
        "---",
        "## 四、帝旺级品种完整推演",
        "",
    ]
    if report["diwang_reports"]:
        for rep in report["diwang_reports"]:
            lines.append(f"### {rep['stock_name']} ({rep['stock_code']})")
            lines.append("")
            lines.append(f"| 项目 | 判断 |")
            lines.append(f"|------|------|")
            lines.append(f"| 日元 | {rep['riyuan_gan']}({rep['riyuan_wuxing']}) | 日柱：{rep['riyuan_ganzhi']} | IPO：{rep['ipo_date']} |")
            lines.append(f"| 承载力 | {rep['star_display']} **{rep['chang_sheng_stage']}** |")
            pop = GOLD_STOCK_POPULARITY_2026_05.get(rep["stock_code"], {"count": 0, "name": ""})
            if pop["count"]:
                lines.append(f"| 券商人气 | {pop['name']} — {pop['count']}家券商推荐 |")
            lines.append(f"| 择时信号 | {'🔥追' if rep['timing_signal']=='追' else '⏳等' if rep['timing_signal']=='等' else '🛑撤'} |")
            lines.append(f"| 预期区间 | {rep['expected_range']} |")
            lines.append(f"| 综合结论 | {rep['conclusion']} |")
            lines.append("")
    else:
        lines.append("*当日无帝旺级品种*")
        lines.append("")

    lines += [
        "---",
        "## 五、联网数据来源",
        "",
    ]
    for ds in report["data_sources"]:
        lines.append(f"- **{ds['category']}**: {ds['source']} ({ds['purpose']})")

    lines += [
        "",
        "---",
        "",
        f"*报告自动生成于 {report['generated_at']} | 八字选股推演引擎 v3.1*",
        "",
        "> ⚠️ **免责声明**：本系统所有「帝旺」「买入」「追」等表述均是基于公开信息的五行框架推演练习，绝不构成任何形式的证券投资建议或收益承诺。期货和期权交易风险极高，可能造成超过本金投入的亏损。市场风险莫测，投资须怀敬畏之心。",
    ]

    return "\n".join(lines)


# ============================================================
# 辅助函数
# ============================================================
def _resolve_stock_name(code):
    pop = GOLD_STOCK_POPULARITY_2026_05.get(code)
    if pop:
        return pop["name"]
    return code


def _market_note(stage):
    if stage == "死":
        return "> ⚠️ 大盘自身承载力偏弱（戊土见酉为「死」），不应期待普涨。此时只有「其他五行属性能与当日形成帝旺/临官共振」的个股，才可能走出独立行情。"
    elif stage == "帝旺":
        return "> ✅ 大盘承载力极强，普涨窗口，帝旺共振品种可放大仓位。"
    elif stage in ("临官", "帝旺"):
        return "> ✅ 大盘承载力偏强，帝旺共振品种优先。"
    return "> 📊 大盘承载力中等，精选帝旺/临官共振品种。"


def get_popularity_info(code):
    """获取某只股票的券商推荐人气"""
    return GOLD_STOCK_POPULARITY_2026_05.get(code, {"name": code, "count": 0})
