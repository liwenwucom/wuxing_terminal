# -*- coding: utf-8 -*-
"""
陈南鹏·五行期货择时系统 —— 主引擎
========================================
严格遵循陈南鹏《仁者无敌》五行理论，适配期货市场

五层架构：
  第一层：流年干支定全局基调（得令/受克 → 全年多空大方向）
  第二层：五行→期货品种映射（物理属性匹配）
  第三层：流月轮动与品种筛选（月令×年令双重叠加）
  第四层：持仓量验证 + 风控红线（杠杆产品特有）
  第五层：宏观事件修正（联网新闻→方向确认/冲突）

数据源：akshare 六大交易所主力合约实时行情
双向交易模式，同时输出多头和空头两个方向
"""

import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import pandas as pd

# 复用陈南鹏股票择时系统的分析函数
from chen_nanpeng_scanner import (
    analyze_year_pillar, MONTH_ZHI_WUXING, MONTH_ADVICE,
    WUXING_SHENG, WUXING_KE, TIANGAN_WUXING, DIZHI_WUXING,
    TIANGAN, DIZHI, HAS_LUNAR,
)

try:
    from lunar_python import Lunar, Solar
except ImportError:
    pass

# ============================================================
# 一、陈南鹏五行→期货品种映射（核心适配层）
# ============================================================

CN_FUTURES_WUXING_PHYSICAL = {
    # 水属性（走强时偏多）
    "水": [
        {"symbol": "SC",  "name": "原油",      "reason": "液态能源，流动之水"},
        {"symbol": "FU",  "name": "燃料油",     "reason": "液态燃油，水性流动"},
        {"symbol": "LU",  "name": "低硫燃油",   "reason": "液态燃油"},
        {"symbol": "BU",  "name": "沥青",       "reason": "液态建材"},
        {"symbol": "PG",  "name": "液化气",      "reason": "液态气体"},
        {"symbol": "SA",  "name": "纯碱",       "reason": "水溶液化工核心"},
        {"symbol": "MA",  "name": "甲醇",       "reason": "液体化工品"},
        {"symbol": "UR",  "name": "尿素",       "reason": "液体化肥"},
        {"symbol": "SH",  "name": "烧碱",       "reason": "水溶液化工"},
        {"symbol": "EC",  "name": "集运欧线",    "reason": "海运属水"},
        {"symbol": "LC",  "name": "碳酸锂",     "reason": "液态能源电池原料"},
    ],
    # 木属性（走强时偏多）
    "木": [
        {"symbol": "CF",  "name": "棉花",       "reason": "天然纤维，木性生长"},
        {"symbol": "SR",  "name": "白糖",       "reason": "甘蔗提取，木性生发"},
        {"symbol": "SP",  "name": "纸浆",       "reason": "木材加工品"},
        {"symbol": "RU",  "name": "橡胶",       "reason": "橡树产物"},
        {"symbol": "NR",  "name": "20号胶",     "reason": "天然橡胶"},
        {"symbol": "AP",  "name": "苹果",       "reason": "果树产物"},
        {"symbol": "CJ",  "name": "红枣",       "reason": "果树产物"},
        {"symbol": "PK",  "name": "花生",       "reason": "农作物"},
        {"symbol": "SM",  "name": "硅铁",       "reason": "合金→钢铁材料辅助"},
    ],
    # 火属性（走强时偏多）
    "火": [
        {"symbol": "J",   "name": "焦炭",       "reason": "煤焦化，火性炼烧"},
        {"symbol": "JM",  "name": "焦煤",       "reason": "煤矿冶炼，火性煅烧"},
        {"symbol": "ZC",  "name": "动力煤",     "reason": "煤能源燃烧"},
        {"symbol": "EG",  "name": "乙二醇",     "reason": "能源化工易燃"},
        {"symbol": "TA",  "name": "PTA",        "reason": "石化涤纶"},
        {"symbol": "PF",  "name": "短纤",       "reason": "石化纤维"},
        {"symbol": "L",   "name": "塑料",       "reason": "石化产品"},
        {"symbol": "V",   "name": "PVC",        "reason": "石化塑料"},
        {"symbol": "PP",  "name": "聚丙烯",     "reason": "石化产品"},
        {"symbol": "EB",  "name": "苯乙烯",     "reason": "石化芳烃"},
    ],
    # 土属性（被克时偏空）
    "土": [
        {"symbol": "A",   "name": "豆一",       "reason": "农作物生长于土"},
        {"symbol": "B",   "name": "豆二",       "reason": "农作物"},
        {"symbol": "M",   "name": "豆粕",       "reason": "植物加工品属土"},
        {"symbol": "Y",   "name": "豆油",       "reason": "油脂属土"},
        {"symbol": "P",   "name": "棕榈油",     "reason": "油脂属土"},
        {"symbol": "OI",  "name": "菜油",       "reason": "油脂属土"},
        {"symbol": "RM",  "name": "菜粕",       "reason": "植物加工品"},
        {"symbol": "C",   "name": "玉米",       "reason": "谷物属土"},
        {"symbol": "CS",  "name": "淀粉",       "reason": "谷物加工属土"},
        {"symbol": "LH",  "name": "生猪",       "reason": "畜产养殖属土"},
        {"symbol": "JD",  "name": "鸡蛋",       "reason": "禽类养殖属土"},
        {"symbol": "FG",  "name": "玻璃",       "reason": "石英砂建材属土"},
        {"symbol": "I",   "name": "铁矿石",     "reason": "矿石属土"},
        {"symbol": "SI",  "name": "工业硅",     "reason": "硅砂属土"},
        {"symbol": "IF",  "name": "沪深300股指","reason": "大盘指数属土"},
        {"symbol": "IC",  "name": "中证500股指","reason": "股指属土"},
        {"symbol": "IM",  "name": "中证1000股指","reason":"股指属土"},
        {"symbol": "IH",  "name": "上证50股指", "reason": "股指属土"},
        {"symbol": "T",   "name": "十年国债",   "reason": "固收属土"},
    ],
    # 金属性（被泄时偏空）
    "金": [
        {"symbol": "AU",  "name": "沪金",       "reason": "贵金属"},
        {"symbol": "AG",  "name": "沪银",       "reason": "贵金属"},
        {"symbol": "CU",  "name": "沪铜",       "reason": "有色金属"},
        {"symbol": "BC",  "name": "国际铜",     "reason": "有色金属"},
        {"symbol": "AL",  "name": "沪铝",       "reason": "有色金属"},
        {"symbol": "ZN",  "name": "沪锌",       "reason": "有色金属"},
        {"symbol": "PB",  "name": "沪铅",       "reason": "有色金属"},
        {"symbol": "NI",  "name": "沪镍",       "reason": "有色金属"},
        {"symbol": "SN",  "name": "沪锡",       "reason": "有色金属"},
        {"symbol": "RB",  "name": "螺纹钢",     "reason": "钢铁建材"},
        {"symbol": "HC",  "name": "热卷",       "reason": "钢铁制品"},
        {"symbol": "WR",  "name": "线材",       "reason": "钢铁制品"},
        {"symbol": "SS",  "name": "不锈钢",     "reason": "钢铁合金"},
        {"symbol": "SF",  "name": "锰硅",       "reason": "合金金属"},
    ],
}

# 品种symbol→完整信息（快速查找）
_ALL_FUTURES_MAP = {}
for _wx, _items in CN_FUTURES_WUXING_PHYSICAL.items():
    for _it in _items:
        sym = _it["symbol"]
        _ALL_FUTURES_MAP[sym] = {
            "name": _it["name"],
            "wuxing": _wx,
            "reason": _it["reason"],
        }


def get_futures_wuxing(symbol):
    return _ALL_FUTURES_MAP.get(symbol, {}).get("wuxing")


def get_futures_name(symbol):
    return _ALL_FUTURES_MAP.get(symbol, {}).get("name", symbol)


# ============================================================
# 二、流月叠加分析（适配期货）
# ============================================================

def analyze_futures_month(lunar_month, month_zhi, year_result):
    month_wx = DIZHI_WUXING.get(month_zhi, "?")
    de_ling = year_result.get("de_ling", [])
    shou_ke = year_result.get("shou_ke", [])
    bei_xie = year_result.get("bei_xie", [])

    result = {
        "lunar_month": lunar_month,
        "month_zhi": month_zhi,
        "month_wx": month_wx,
        "supports_de_ling": month_wx in de_ling,
        "supports_shou_ke": month_wx in shou_ke,
        "double_de_ling": [],
        "double_shou_ke": [],
        "analysis": "",
    }

    if month_wx in de_ling:
        result["double_de_ling"] = [month_wx]
        result["analysis"] = (
            f"月令{month_wx}扶旺年令得令五行，{month_wx}属性品种获年+月双重扶持→最强做多候选。"
        )
    elif month_wx in shou_ke:
        result["double_shou_ke"] = [month_wx]
        result["analysis"] = (
            f"月令{month_wx}叠加年令受克，{month_wx}属性品种遭年+月双重压制→最强做空候选。"
        )
    elif month_wx in bei_xie:
        result["analysis"] = (
            f"月令{month_wx}处于泄气位，无明显方向，宜轻仓或观望。"
        )
    else:
        result["analysis"] = f"月令{month_wx}中性，维持年令主线判断。"

    return result


# ============================================================
# 三、第四层：持仓量验证 + 风控
# ============================================================

def _verify_position_price(chg_pct, position_chg, symbol_wx, de_ling, shou_ke):
    verification = {
        "valid": True,
        "confidence": "中",
        "advice": "",
        "position_weight": "轻仓",
        "stop_loss_pct": 2.0,
    }

    if chg_pct > 0 and position_chg > 0:
        verification["confidence"] = "高"
        verification["advice"] = "量价齐升，五行信号有效，可进场"
    elif chg_pct > 0 and position_chg < 0:
        verification["confidence"] = "低"
        verification["advice"] = "持仓减少+价格上行→资金不认可，降低仓位或观望"
        verification["position_weight"] = "观望"
    elif chg_pct < 0 and position_chg > 0:
        verification["confidence"] = "低"
        verification["advice"] = "持仓增加+价格下跌→空头主导信号"
        verification["position_weight"] = "观望"
    elif chg_pct < 0 and position_chg < 0:
        verification["advice"] = "量价齐跌，趋势延续中"

    if verification["confidence"] == "高":
        if symbol_wx in de_ling:
            verification["position_weight"] = "中等"
            verification["stop_loss_pct"] = 2.0
            if symbol_wx not in shou_ke:
                verification["position_weight"] = "可重仓"
                verification["stop_loss_pct"] = 1.5

    if symbol_wx in shou_ke:
        verification["position_weight"] = "轻仓"
        verification["stop_loss_pct"] = 1.5
        if chg_pct > 0 and position_chg > 0:
            verification["advice"] += "（属受克五行但技术信号偏多→轻仓试多，设紧止损）"

    return verification


# ============================================================
# 四、综合评分（期货方向判定）
# ============================================================

def _score_futures_cn(symbol_wx, de_ling, shou_ke, bei_xie, month_result,
                      chg_pct, position_chg):
    score = 50.0
    direction = "中性"

    if symbol_wx in de_ling:
        score += 25
        direction = "偏多"
    if symbol_wx in month_result.get("double_de_ling", []):
        score += 15
        direction = "做多"

    if symbol_wx in shou_ke:
        score -= 25
        direction = "偏空"
    if symbol_wx in month_result.get("double_shou_ke", []):
        score -= 15
        direction = "做空"

    if symbol_wx in bei_xie:
        score -= 8

    if chg_pct > 1.5:
        score += 8
    elif chg_pct < -1.5:
        score -= 8

    if position_chg > 0:
        score += 5
    elif position_chg < 0:
        score -= 5

    score = round(max(0, min(100, score)), 1)

    if score >= 70:
        direction = "做多"
    elif score >= 60:
        direction = "偏多"
    elif score >= 45:
        direction = "中性"
    elif score >= 35:
        direction = "偏空"
    else:
        direction = "做空"

    return {"score": score, "direction": direction}


# ============================================================
# 五、获取实时期货数据
# ============================================================

def _fetch_futures_data():
    try:
        import akshare as ak
        df = ak.futures_main_sina()
        result = {}
        for _, row in df.iterrows():
            sym_raw = str(row.get("symbol", "")).strip()
            if sym_raw.endswith("0"):
                sym = sym_raw[:-1]
            else:
                sym = sym_raw
            try:
                result[sym] = {
                    "price": float(row.get("price", 0) or 0),
                    "chg_pct": float(row.get("chg", 0) or 0),
                    "volume": float(row.get("volume", 0) or 0),
                    "position": float(row.get("position", 0) or 0),
                    "position_chg": float(row.get("position_chg", 0) or 0),
                }
            except Exception:
                continue
        return result
    except ImportError:
        return {}
    except Exception:
        return {}


# ============================================================
# 六、主扫描函数
# ============================================================

def scan_chen_nanpeng_futures(target_date_str=None, year_str=None, events_text=""):
    if target_date_str is None:
        target_date_str = datetime.now().strftime("%Y-%m-%d")

    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

    # 农历转换
    day_gan = "?"
    day_zhi = "?"
    year_ganzhi = ""
    month_ganzhi = ""
    day_ganzhi = ""
    lunar_month = target_date.month

    if HAS_LUNAR:
        try:
            solar = Solar.fromYmd(target_date.year, target_date.month, target_date.day)
            lunar = solar.getLunar()
            year_ganzhi = lunar.getYearInGanZhi()
            month_ganzhi = lunar.getMonthInGanZhi()
            day_ganzhi = lunar.getDayInGanZhi()
            day_gan = lunar.getDayGan()
            day_zhi = lunar.getDayZhi()
            lunar_month = lunar.getMonth()
        except Exception:
            pass

    if year_str:
        year_ganzhi = year_str
    elif year_ganzhi:
        pass
    else:
        idx = (target_date.year - 4) % 10
        zidx = (target_date.year - 4) % 12
        year_ganzhi = TIANGAN[idx] + DIZHI[zidx]

    if not year_ganzhi or len(year_ganzhi) < 2:
        year_ganzhi = "丙午"

    year_result = analyze_year_pillar(year_ganzhi)
    de_ling = year_result.get("de_ling", [])
    shou_ke = year_result.get("shou_ke", [])
    bei_xie = year_result.get("bei_xie", [])

    month_zhi = month_ganzhi[1] if len(month_ganzhi) >= 2 else "?"
    if month_zhi == "?":
        mz_data = MONTH_ADVICE.get(lunar_month, ("?", "?"))
        month_zhi = mz_data[0]

    month_result = analyze_futures_month(lunar_month, month_zhi, year_result)

    # 拉取行情
    prices = _fetch_futures_data()

    # 逐个品种评分
    long_candidates = []
    short_candidates = []
    neutral_candidates = []

    for wx, items in CN_FUTURES_WUXING_PHYSICAL.items():
        for item in items:
            sym = item["symbol"]
            pd_data = prices.get(sym, {})

            chg_pct = pd_data.get("chg_pct", 0) if pd_data else 0
            pos_chg_sign = 1 if pd_data.get("position_chg", 0) > 0 else (-1 if pd_data.get("position_chg", 0) < 0 else 0)

            score_info = _score_futures_cn(
                wx, de_ling, shou_ke, bei_xie, month_result,
                chg_pct, pos_chg_sign,
            )

            verify = _verify_position_price(
                chg_pct, pos_chg_sign, wx, de_ling, shou_ke,
            )

            effective_score = score_info["score"]
            if verify["confidence"] == "低":
                effective_score -= 10
            elif verify["confidence"] == "高":
                effective_score += 5

            effective_score = round(max(0, min(100, effective_score)), 1)

            entry = {
                "symbol": sym,
                "name": item["name"],
                "wuxing": wx,
                "wuxing_reason": item["reason"],
                "price": round(pd_data.get("price", 0), 2),
                "chg_pct": round(chg_pct, 2),
                "position_chg_sign": pos_chg_sign,
                "raw_score": score_info["score"],
                "score": effective_score,
                "direction": score_info["direction"],
                "verify": verify,
                "stop_loss": round(
                    pd_data.get("price", 0) * (1 - verify["stop_loss_pct"] / 100), 2
                ) if pd_data.get("price", 0) > 0 else 0,
            }

            if score_info["direction"] in ("做多", "偏多"):
                long_candidates.append(entry)
            elif score_info["direction"] in ("做空", "偏空"):
                short_candidates.append(entry)
            else:
                neutral_candidates.append(entry)

    long_candidates.sort(key=lambda x: -x["score"])
    short_candidates.sort(key=lambda x: x["score"])
    neutral_candidates.sort(key=lambda x: -abs(x["score"] - 50))

    # 事件修正
    event_note = ""
    if events_text.strip():
        event_keywords = {
            "中东": "火", "OPEC": "水", "降息": "水", "加息": "金",
            "贸易战": "金", "战争": "火", "干旱": "火", "洪水": "水",
            "基建": "土", "减排": "木", "新能源": "火", "衰退": "土",
            "制裁": "金", "减产": "火", "增产": "木",
        }
        event_wx_set = set()
        for kw, ewv in event_keywords.items():
            if kw in events_text:
                event_wx_set.add(ewv)
        event_wx_list = list(event_wx_set)

        conflicts = []
        for ew in event_wx_list:
            if ew in de_ling:
                conflicts.append(f"事件{ew}与得令{ew}方向一致 → 加分")
            elif ew in shou_ke:
                conflicts.append(f"⚠️ 事件{ew}落入受克方 → 冲突提示，降低该品种方向权重")
        if conflicts:
            event_note = " | ".join(conflicts)
        else:
            event_note = "事件与五行判断方向无显著冲突"

    return {
        "target_date": target_date_str,
        "lunar_month": lunar_month,
        "year_ganzhi": year_ganzhi,
        "month_ganzhi": month_ganzhi,
        "day_ganzhi": day_ganzhi,
        "month_zhi": month_zhi,
        "year_analysis": year_result,
        "month_overlay": month_result,
        "event_note": event_note,
        "long_top5": long_candidates[:5],
        "short_top5": short_candidates[:5],
        "neutral": neutral_candidates[:5],
        "long_count": len(long_candidates),
        "short_count": len(short_candidates),
        "neutral_count": len(neutral_candidates),
        "de_ling": de_ling,
        "shou_ke": shou_ke,
        "bei_xie": bei_xie,
    }


# ============================================================
# 七、格式化报告
# ============================================================

def format_cn_futures_report(data):
    lines = []
    lines.append("=" * 60)
    lines.append("  陈南鹏·五行期货择时系统 —— 完整分析报告")
    lines.append("=" * 60)
    lines.append(f"  分析日期: {data['target_date']}")
    lines.append(f"  农历月份: 第{data['lunar_month']}月 | 年柱: {data['year_ganzhi']}")

    ya = data["year_analysis"]
    lines.append("")
    lines.append(f"【第一层】流年五行: {ya.get('relation','')}")
    lines.append(f"  得令: {', '.join(data['de_ling'])} | "
                 f"受克: {', '.join(data['shou_ke'])} | "
                 f"泄气: {', '.join(data['bei_xie'])}")
    lines.append(f"  → 全年：{'/'.join(data['de_ling'])}品种偏多, "
                 f"{'/'.join(data['shou_ke'])}品种偏空")

    mo = data["month_overlay"]
    lines.append("")
    lines.append(f"【第三层】流月: 月令{mo['month_wx']} → {mo['analysis']}")

    lines.append("")
    lines.append(f"【做多 TOP 5】({data['long_count']}只偏多品种)")
    for i, c in enumerate(data["long_top5"], 1):
        lines.append(
            f"  {i}. {c['name']}({c['wuxing']}) "
            f"评分{c['score']} | 涨跌{c['chg_pct']}% | "
            f"{c['verify']['position_weight']} | 止损{c['stop_loss']}"
        )

    lines.append("")
    lines.append(f"【做空 TOP 5】({data['short_count']}只偏空品种)")
    for i, c in enumerate(data["short_top5"], 1):
        lines.append(
            f"  {i}. {c['name']}({c['wuxing']}) "
            f"评分{c['score']} | 涨跌{c['chg_pct']}% | "
            f"{c['verify']['position_weight']}"
        )

    if data["neutral"]:
        lines.append("")
        lines.append(f"【中性/观望】({data['neutral_count']}只)")
        for c in data["neutral"][:3]:
            lines.append(f"  · {c['name']}({c['wuxing']}) 评分{c['score']}")

    if data["event_note"]:
        lines.append("")
        lines.append(f"【事件修正】{data['event_note']}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("  风控红线: 单品种≤15%仓位 | 2%硬止损 | 双向交易特别提示")
    lines.append("  期货杠杆风险极高，以上仅为五行推演参考，不构成投资建议。")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_futures_single_cn(c, ya):
    lines = []
    lines.append(f"**{c['name']}({c['symbol']}) [{c['wuxing']}]**")
    lines.append(f"- 五行理由: {c['wuxing_reason']}")
    lines.append(f"- 现价: {c['price']} | 涨跌: {c['chg_pct']}%")
    lines.append(f"- 方向: {c['direction']} | 评分: {c['score']}")
    v = c["verify"]
    lines.append(f"- 量价验证: {v['confidence']} | {v['advice']}")
    lines.append(f"- 仓位: {v['position_weight']} | 止损: {c['stop_loss']}")
    lines.append(f"- 仓位上限: ≤总资金15%")
    return "\n".join(lines)
