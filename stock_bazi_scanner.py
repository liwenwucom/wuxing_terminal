# -*- coding: utf-8 -*-
"""
八字选股自动扫盘引擎 v1.0
—— 日元承载力(十二长生) + 券商金股人气 + 政策共振 = 综合评分

对标 futures_bazi_picker.py 的结构，专为 A 股设计：
1. 全量扫描（67只收录股票）
2. TOP10 排名 + 期权/卖方策略适配
3. 三重共振扫描（天时 x 人气 x 政策）
4. 帝旺/临官级龙头完整推演
"""

from datetime import datetime
from bazi_capacity import (
    get_riyuan_from_ipo, get_trade_day_info, get_chang_sheng,
    IPO_DATE_MAP, TIANGAN_WUXING, DIZHI_WUXING,
    CAPACITY_SCORES, STAGE_NAMES,
)
from wuxing_timing import STAR_RATINGS, get_timing_signal
from bazi_picker import generate_bazi_report, PRICE_VOLUME_RULES
from policy_analyzer import get_monthly_rotation, MONTHLY_ROTATION
from bazi_live_scanner import GOLD_STOCK_POPULARITY_2026_05


# ============================================================
# 股票行业→五行映射表
# ============================================================
STOCK_SECTOR_WUXING = {
    "600519": {"name": "贵州茅台", "sector": "白酒", "wuxing": "木", "market_cap": "大盘"},
    "000858": {"name": "五粮液", "sector": "白酒", "wuxing": "木", "market_cap": "大盘"},
    "002594": {"name": "比亚迪", "sector": "汽车/新能源", "wuxing": "金", "market_cap": "大盘"},
    "300750": {"name": "宁德时代", "sector": "新能源电池", "wuxing": "火", "market_cap": "大盘"},
    "601398": {"name": "工商银行", "sector": "银行", "wuxing": "金", "market_cap": "大盘"},
    "600036": {"name": "招商银行", "sector": "银行", "wuxing": "金", "market_cap": "大盘"},
    "601939": {"name": "建设银行", "sector": "银行", "wuxing": "金", "market_cap": "大盘"},
    "601288": {"name": "农业银行", "sector": "银行", "wuxing": "金", "market_cap": "大盘"},
    "600030": {"name": "中信证券", "sector": "证券", "wuxing": "金", "market_cap": "大盘"},
    "300059": {"name": "东方财富", "sector": "证券/互联网", "wuxing": "金", "market_cap": "大盘"},
    "601688": {"name": "华泰证券", "sector": "证券", "wuxing": "金", "market_cap": "大盘"},
    "601318": {"name": "中国平安", "sector": "保险", "wuxing": "金", "market_cap": "大盘"},
    "601628": {"name": "中国人寿", "sector": "保险", "wuxing": "金", "market_cap": "大盘"},
    "601319": {"name": "中国人保", "sector": "保险", "wuxing": "金", "market_cap": "大盘"},
    "601138": {"name": "工业富联", "sector": "算力/服务器", "wuxing": "火", "market_cap": "大盘"},
    "300308": {"name": "中际旭创", "sector": "光通信", "wuxing": "火", "market_cap": "大盘"},
    "000063": {"name": "中兴通讯", "sector": "通信设备", "wuxing": "火", "market_cap": "大盘"},
    "600941": {"name": "中国移动", "sector": "电信运营", "wuxing": "火", "market_cap": "大盘"},
    "600309": {"name": "万华化学", "sector": "化工", "wuxing": "火", "market_cap": "大盘"},
    "002001": {"name": "新和成", "sector": "化工/维生素", "wuxing": "火", "market_cap": "大盘"},
    "002415": {"name": "海康威视", "sector": "安防/AI", "wuxing": "火", "market_cap": "大盘"},
    "600988": {"name": "赤峰黄金", "sector": "贵金属", "wuxing": "金", "market_cap": "中盘"},
    "688256": {"name": "寒武纪", "sector": "AI芯片", "wuxing": "火", "market_cap": "大盘"},
    "601899": {"name": "紫金矿业", "sector": "有色/黄金", "wuxing": "金", "market_cap": "大盘"},
    "600150": {"name": "中国船舶", "sector": "造船/军工", "wuxing": "金", "market_cap": "大盘"},
    "601668": {"name": "中国建筑", "sector": "基建", "wuxing": "土", "market_cap": "大盘"},
    "601390": {"name": "中国中铁", "sector": "基建", "wuxing": "土", "market_cap": "大盘"},
    "600585": {"name": "海螺水泥", "sector": "建材", "wuxing": "土", "market_cap": "大盘"},
    "600031": {"name": "三一重工", "sector": "工程机械", "wuxing": "土", "market_cap": "大盘"},
    "600406": {"name": "国电南瑞", "sector": "电力设备", "wuxing": "火", "market_cap": "大盘"},
    "600900": {"name": "长江电力", "sector": "电力", "wuxing": "火", "market_cap": "大盘"},
    "601088": {"name": "中国神华", "sector": "煤炭", "wuxing": "火", "market_cap": "大盘"},
    "601699": {"name": "潞安环能", "sector": "煤炭", "wuxing": "火", "market_cap": "中盘"},
    "601857": {"name": "中国石油", "sector": "石油", "wuxing": "火", "market_cap": "大盘"},
    "002840": {"name": "华统股份", "sector": "养殖", "wuxing": "水", "market_cap": "小盘"},
    "603345": {"name": "安井食品", "sector": "食品/预制菜", "wuxing": "火", "market_cap": "中盘"},
    "600588": {"name": "用友网络", "sector": "软件/云服务", "wuxing": "火", "market_cap": "中盘"},
    "601615": {"name": "明阳智能", "sector": "风电", "wuxing": "火", "market_cap": "中盘"},
    "605499": {"name": "东鹏饮料", "sector": "饮料", "wuxing": "木", "market_cap": "中盘"},
    "000988": {"name": "华工科技", "sector": "激光/智能制造", "wuxing": "火", "market_cap": "中盘"},
    "688702": {"name": "盛科通信", "sector": "通信芯片", "wuxing": "火", "market_cap": "小盘"},
    "600048": {"name": "保利发展", "sector": "房地产", "wuxing": "土", "market_cap": "大盘"},
    "600438": {"name": "通威股份", "sector": "光伏/农业", "wuxing": "火", "market_cap": "大盘"},
    "300274": {"name": "阳光电源", "sector": "光伏逆变器", "wuxing": "火", "market_cap": "大盘"},
    "600276": {"name": "恒瑞医药", "sector": "医药", "wuxing": "土", "market_cap": "大盘"},
    "002714": {"name": "牧原股份", "sector": "养猪", "wuxing": "水", "market_cap": "大盘"},
    "300760": {"name": "迈瑞医疗", "sector": "医疗器械", "wuxing": "火", "market_cap": "大盘"},
    "601012": {"name": "隆基绿能", "sector": "光伏", "wuxing": "火", "market_cap": "大盘"},
    "688981": {"name": "中芯国际", "sector": "半导体制造", "wuxing": "火", "market_cap": "大盘"},
    "002371": {"name": "北方华创", "sector": "半导体设备", "wuxing": "火", "market_cap": "大盘"},
    "603501": {"name": "韦尔股份", "sector": "芯片设计", "wuxing": "火", "market_cap": "大盘"},
    "600584": {"name": "长电科技", "sector": "封装测试", "wuxing": "火", "market_cap": "大盘"},
    "600887": {"name": "伊利股份", "sector": "乳业", "wuxing": "水", "market_cap": "大盘"},
    "603288": {"name": "海天味业", "sector": "调味品", "wuxing": "水", "market_cap": "大盘"},
    "601888": {"name": "中国中免", "sector": "免税", "wuxing": "水", "market_cap": "大盘"},
    "600346": {"name": "恒力石化", "sector": "炼化", "wuxing": "火", "market_cap": "大盘"},
    "000651": {"name": "格力电器", "sector": "家电", "wuxing": "木", "market_cap": "大盘"},
    "000333": {"name": "美的集团", "sector": "家电", "wuxing": "木", "market_cap": "大盘"},
    "601919": {"name": "中远海控", "sector": "航运", "wuxing": "水", "market_cap": "大盘"},
    "600018": {"name": "上港集团", "sector": "港口", "wuxing": "水", "market_cap": "大盘"},
    "600760": {"name": "中航沈飞", "sector": "军工航空", "wuxing": "火", "market_cap": "大盘"},
    "600893": {"name": "航发动力", "sector": "航空发动机", "wuxing": "火", "market_cap": "大盘"},
    "002007": {"name": "华兰生物", "sector": "生物制品", "wuxing": "水", "market_cap": "中盘"},
    "600111": {"name": "北方稀土", "sector": "稀土", "wuxing": "金", "market_cap": "大盘"},
    "600019": {"name": "宝钢股份", "sector": "钢铁", "wuxing": "金", "market_cap": "大盘"},
    "601225": {"name": "陕西煤业", "sector": "煤炭", "wuxing": "火", "market_cap": "大盘"},
    "600905": {"name": "三峡能源", "sector": "新能源电力", "wuxing": "火", "market_cap": "大盘"},
    "600011": {"name": "华能国际", "sector": "火力发电", "wuxing": "火", "market_cap": "大盘"},
}


def _resolve_stock_name(code):
    """解析股票名称"""
    return STOCK_SECTOR_WUXING.get(code, {}).get("name", code)


def _resolve_stock_wuxing(code):
    """解析股票行业五行"""
    return STOCK_SECTOR_WUXING.get(code, {}).get("wuxing", "未知")


def _resolve_stock_sector(code):
    """解析股票行业/板块名称"""
    return STOCK_SECTOR_WUXING.get(code, {}).get("sector", "未知")


# ============================================================
# 股票承载力星级 + 量价验证信号
# ============================================================
STOCK_CAPACITY_STAR_MAP = {
    "帝旺": ("★★★★★", "极强", "量比>=1.5+成交额放大+站稳分时均线=真实多头入场"),
    "临官": ("★★★★★", "极强", "量比>=1.2+成交额稳步放大=趋势做多确认"),
    "冠带": ("★★★★☆", "较强", "温和放量上涨>=0.5%,量比>1.0"),
    "沐浴": ("★★★★☆", "较强", "窄幅震荡预期,涨跌幅<±0.8%为正常"),
    "长生": ("★★★☆☆", "中等", "静待观察,量大涨幅>1%可轻仓试多"),
    "衰":   ("★★☆☆☆", "较弱", "不建议开新仓,缩量阴跌=下跌趋势"),
    "病":   ("★★☆☆☆", "较弱", "坚决不加仓,冲高即减仓"),
    "死":   ("★☆☆☆☆", "极弱", "空头主导,放量下跌=真看空"),
    "墓":   ("★☆☆☆☆", "极弱", "成交量爆发下跌可能踩踏,必须设止损"),
    "绝":   ("★☆☆☆☆", "极弱", "极弱日空头占优,宜做空或空仓"),
    "胎":   ("★☆☆☆☆", "极弱", "弱势震荡,不宜操作"),
    "养":   ("★☆☆☆☆", "极弱", "弱势,但接近回升拐点可关注"),
}

STOCK_EXPECTED_RANGE = {
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


# 最大券商推荐数（用于归一化）
MAX_STOCK_POPULARITY = max(
    (v["count"] for v in GOLD_STOCK_POPULARITY_2026_05.values()), default=10
)


def get_stock_popularity(code):
    """获取个股券商推荐人气（0-1归一化）"""
    info = GOLD_STOCK_POPULARITY_2026_05.get(code)
    if info:
        return info["count"] / MAX_STOCK_POPULARITY
    return 0.0


# ============================================================
# 一、全量股票当日承载力扫描
# ============================================================
def scan_all_stocks_daily(trade_date_str=None):
    """
    扫描全部收录股票的当日承载力
    返回按综合评分排序的品种列表
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    rotation = get_monthly_rotation(trade_date_str)
    rotation_elements = rotation["elements"] if rotation else []

    results = []
    for code, ipo in IPO_DATE_MAP.items():
        try:
            riyuan = get_riyuan_from_ipo(ipo)
            gan = riyuan["gan"]
            wx_stock = _resolve_stock_wuxing(code)

            trade_info = get_trade_day_info(trade_date_str)
            cs = get_chang_sheng(gan, trade_info["day_zhi"])
            stage = cs["stage_name"]
            capacity = cs["capacity_score"]

            star, label, verify = STOCK_CAPACITY_STAR_MAP.get(
                stage, ("☆☆☆☆☆", "未知", "—"))
            expected = STOCK_EXPECTED_RANGE.get(stage, "—")

            # 月度轮动加成（作为政策共振）
            rotation_bonus = 1.0 if wx_stock in rotation_elements else 0.5

            # 人气分（归一化 0-1）
            popularity = get_stock_popularity(code)

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
                "code": code,
                "name": _resolve_stock_name(code),
                "sector": _resolve_stock_sector(code),
                "riyuan_gan": gan,
                "riyuan_wuxing": riyuan["wuxing"],
                "stock_wuxing": wx_stock,
                "stage": stage,
                "star": star,
                "label": label,
                "capacity": capacity,
                "expected": expected,
                "rotation_bonus": rotation_bonus,
                "composite": round(composite, 3),
                "phase_label": phase_label,
                "verify_signal": verify,
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


# ============================================================
# 二、生成TOP10
# ============================================================
def generate_stock_top10(trade_date_str=None):
    scan = scan_all_stocks_daily(trade_date_str)
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
        "summary": _stock_top10_summary(top10),
    }


def _stock_top10_summary(top10):
    bullish = [r for r in top10 if r["composite"] >= 0.25]
    bearish = [r for r in top10 if r["composite"] < 0.0]

    if len(bullish) >= 5:
        return "多头氛围浓厚，多个品种承载力共振偏强，可积极布局帝旺/临官级个股"
    elif len(bearish) >= 5:
        return "空头主导，多数品种承载力极弱，以避险或减仓为主"
    else:
        return "市场分化明显，精选帝旺/临官级别个股做多，极弱品种回避"


# ============================================================
# 三、三重共振扫描（天时 x 券商人气 x 板块政策）
# ============================================================
def scan_stock_triple_resonance(trade_date_str=None):
    """
    扫描同时满足三个条件的个股：
    1. 承载力 >= ★★★★ (冠带/沐浴/帝旺/临官)
    2. 券商推荐人气 >= 3次（原始计数）
    3. 月度轮动五行匹配（政策正向共振）
    """
    scan = scan_all_stocks_daily(trade_date_str)
    rotation_elements = scan["rotation_elements"]
    trade_info = get_trade_day_info(scan["trade_date"])
    month_ganzhi = trade_info["month_ganzhi"]

    triple_hits = []
    for r in scan["results"]:
        stage = r["stage"]
        if stage not in ("帝旺", "临官", "冠带", "沐浴"):
            continue
        pop_info = GOLD_STOCK_POPULARITY_2026_05.get(r["code"])
        if not pop_info or pop_info["count"] < 3:
            continue
        if r["stock_wuxing"] not in rotation_elements:
            continue

        rating = "SSS" if stage in ("帝旺", "临官") else "SS" if stage == "冠带" else "S"
        resonance_note = f"{r['stock_wuxing']}属性板块与月度轮动{'+'.join(rotation_elements)}正向共振"

        triple_hits.append({
            "code": r["code"],
            "name": r["name"],
            "sector": r["sector"],
            "stage": r["stage"],
            "star": r["star"],
            "popularity_count": pop_info["count"],
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
# 四、帝旺/临官级龙头完整推演（选TOP2）
# ============================================================
def generate_stock_diwang_detail(trade_date_str=None):
    """
    从TOP10中筛选帝旺/临官级别的个股，选评分最高的2个做完整推演
    """
    top10 = generate_stock_top10(trade_date_str)
    diwang_candidates = [r for r in top10["top10"] if r["stage"] in ("帝旺", "临官")]

    if not diwang_candidates:
        diwang_candidates = [r for r in top10["top10"] if r["star"] in ("★★★★★", "★★★★☆")][:2]

    details = []
    for candidate in diwang_candidates[:2]:
        report = generate_bazi_report(candidate["code"], top10["trade_date"])
        pop_info = GOLD_STOCK_POPULARITY_2026_05.get(candidate["code"])
        popularity_str = f"{pop_info['count']}次" if pop_info else "暂无推荐"
        popularity_detail = f"{pop_info['count']}家券商推荐" if pop_info else "暂无券商推荐数据"

        direction = "做多" if candidate["composite"] >= 0.25 else "震荡偏多" if candidate["composite"] >= 0 else "偏空"

        details.append({
            "name": candidate["name"],
            "code": candidate["code"],
            "sector": candidate["sector"],
            "ipo_date": report["ipo_date"],
            "riyuan_ganzhi": report["riyuan_ganzhi"],
            "riyuan_gan": report["riyuan_gan"],
            "riyuan_wuxing": report["riyuan_wuxing"],
            "trade_ganzhi": report["day_ganzhi"],
            "chang_sheng": report["chang_sheng_stage"],
            "star_display": report["star_display"],
            "direction": direction,
            "composite": candidate["composite"],
            "popularity": popularity_str,
            "popularity_detail": popularity_detail,
            "entry_condition": "量比>=1.5且股价站稳分时均线，成交量较前一交易日放大20%以上",
            "scam_warning": "帝旺日若冲高回落或缩量阴跌=骗炮嫌疑，坚决规避，说明资金面不支持天时吉兆",
            "stop_loss": "止损价设为 -3% ~ -5% 区间，天时判断错误也需及时止损",
            "strategy": "分时均价线附近低吸，轻仓参与，不追涨",
        })

    return details


# ============================================================
# 五、格式化输出：完整报告
# ============================================================
def format_stock_top10_table(report):
    """格式化TOP10为Markdown表格（完整版：含三重共振 + 帝旺/临官推演）"""
    trade_date = report["trade_date"]

    lines = [
        f"## A股TOP10自动扫盘报告",
        f"扫描日期: {trade_date} | 月度轮动五行: {'+'.join(report['rotation_elements'])} | 共扫描 {report['total_scanned']} 只股票",
        "",
        "### TOP10 榜单",
        "",
        f"> {report['summary']}",
        "",
        "| 排名 | 股票 | 代码 | 日元 | 承载力(十二长生) | 星级 | 方向预期 | 综合评分 | 板块 |",
        "|------|------|------|------|------------------|------|----------|----------|------|",
    ]
    for i, r in enumerate(report["top10"]):
        emoji = "🔴" if r["composite"] >= 0.25 else ("⚪" if r["composite"] >= 0 else "🔵")
        lines.append(
            f"| {i+1} | {emoji}{r['name']} | {r['code']} | {r['riyuan_gan']}({r['riyuan_wuxing']}) | {r['stage']} | {r['star']} | {r['phase_label']} | {r['composite']:.2f} | {r['sector']} |"
        )

    lines += [
        "",
        f"多头品种: {report['bullish_count']}只 | 空头品种: {report['bearish_count']}只",
    ]

    # ============ 三重共振扫描 ============
    triple = scan_stock_triple_resonance(trade_date)
    lines += [
        "",
        "### 三重共振扫描（天时 x 券商人气 x 板块政策）",
        "",
    ]
    if triple["hits"]:
        lines.append(f"月度干支: {triple['month_ganzhi']} | 轮动五行: {'+'.join(triple['rotation_elements'])} | 共振品种: {triple['count']}只")
        lines.append("")
        lines.append("| 品种 | 板块 | 天时 | 人气(次) | 政策共振 | 综合评级 |")
        lines.append("|------|------|------|----------|----------|----------|")
        for h in triple["hits"]:
            lines.append(
                f"| {h['name']}({h['code']}) | {h['sector']} | {h['star']} {h['stage']} | {h['popularity_count']} | {h['rotation_match']}利好 | {h['rating']} |"
            )
    else:
        lines.append("> 当日无品种同时满足三重共振条件（承载力>=★★★★ + 人气>=3次 + 政策正向共振）")

    # ============ 帝旺/临官级完整推演 ============
    details = generate_stock_diwang_detail(trade_date)
    if details:
        lines += [
            "",
            "### 帝旺/临官级龙头完整推演",
            "",
        ]
        for d in details:
            lines += [
                f"#### 八字选股推演 — {d['name']} ({d['code']})",
                "",
                f"- 行业板块: {d['sector']}",
                f"- 上市日期: {d['ipo_date']} -> 日柱干支: {d['riyuan_ganzhi']} -> 日元: {d['riyuan_gan']}({d['riyuan_wuxing']})",
                f"- 目标交易日干支: {d['trade_ganzhi']}",
                f"- 承载力: {d['chang_sheng']} (十二长生) -> {d['star_display']}",
                f"- 方向预期: {d['direction']}",
                f"- 券商推荐: {d['popularity_detail']}",
                "",
                "**量价验证触发（买入标准）**",
                f"- 追加入场: {d['entry_condition']}",
                f"- 骗炮警告: {d['scam_warning']}",
                "",
                "**短线策略框架**",
                f"- 入场策略: {d['strategy']}",
                f"- 止损纪律: {d['stop_loss']}",
                "",
            ]

    lines += [
        "---",
        "",
        "### 风险提示与免责声明",
        "",
        "> 本报告基于八字五行推演和公开信息整理，仅供内部研究学习，不构成任何投资建议。"
        "股市有风险，所有策略均需投资者根据自身风险承受能力独立决策，并设置硬性止损。"
        "文中所有标的均为方法论演示，不构成对具体品种的买入推荐。"
        "入市须谨慎，盈亏自负。",
    ]
    return "\n".join(lines)


# ============================================================
# 六、A股年度大势评估（2026丙午年）
# ============================================================
STOCK_MARKET_ASSESSMENT_2026 = {
    "year": 2026,
    "year_ganzhi": "丙午",
    "market_riyuan": "戊",
    "market_wuxing": "土",
    "assessment": "丙午年天地皆火，火生土，大牛市格局。戊土喜火生，5月起火属性行业（科技/军工/能源）预期亮眼",
    "monthly_focus": {
        5: "聚焦中小市值成长风格，科技（通信/半导体/算力）+ 贵金属双重主线",
        6: "纯粹炎火月，半导体+消费+煤炭旺季",
    },
}
