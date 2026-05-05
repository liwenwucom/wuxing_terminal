# -*- coding: utf-8 -*-
"""
陈南鹏·五行择时系统 —— 主引擎
========================================
严格遵循陈南鹏《仁者无敌》五行理论

五层架构：
  第一层：流年干支定全局基调（得令/受克/被泄）
  第二层：五行→行业映射（陈南鹏原版版图）
  第三层：流月轮动筛选（逐月热点预判）
  第四层：个股匹配筛选（名称偏旁+代码数字+量价）
  第五层：回避清单

数据源：akshare 全A股实时行情（排除688科创板/ST/退市/港股）
"""

import sys
import re
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import pandas as pd

try:
    from lunar_python import Lunar, Solar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False

# ============================================================
# 一、基础常量
# ============================================================

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

TIANGAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

DIZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 生克关系
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天干数字 (河图洛书: 甲1乙2丙3丁4戊5己6庚7辛8壬9癸10)
TIANGAN_NUMBER = {
    "甲": 1, "乙": 2, "丙": 3, "丁": 4, "戊": 5,
    "己": 6, "庚": 7, "辛": 8, "壬": 9, "癸": 10,
}

# 地支数字 (子1丑2寅3卯4辰5巳6午7未8申9酉10戌11亥12)
DIZHI_NUMBER = {
    "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
    "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12,
}

# ============================================================
# 二、陈南鹏行业→五行映射（原版版图）
# ============================================================

CHENNANPENG_INDUSTRY_WUXING = {
    # 水属性
    "水": [
        "食品饮料", "金融", "医药", "物流", "航运", "数字货币", "白酒",
        "电子商务", "跨境支付",
    ],
    # 木属性
    "木": [
        "农业", "文化传媒", "教育", "材料", "造纸", "纺织服装",
        "游戏", "出版", "广告包装",
    ],
    # 火属性
    "火": [
        "绿色电力", "软件", "互联网", "军工", "半导体", "新能源",
        "石油化工", "电气设备", "通信设备", "IT设备", "元器件",
        "汽车电子", "人工智能",
    ],
    # 土属性 (被克时回避)
    "土": [
        "房地产", "基建", "水泥", "建材", "稀土", "锂电池",
        "建筑工程", "装饰园林", "物业管理",
    ],
    # 金属性 (被泄时回避)
    "金": [
        "银行", "保险", "证券", "钢铁", "贵金属",
        "有色", "煤炭", "机械", "航空",
    ],
}

# 行业关键词→五行（用于模糊匹配akshare行业分类）
_INDUSTRY_KEYWORD_WUXING = {}
for _wx, _industries in CHENNANPENG_INDUSTRY_WUXING.items():
    for _ind in _industries:
        _INDUSTRY_KEYWORD_WUXING[_ind] = _wx


def map_industry_to_wuxing(industry_name):
    if not industry_name or not isinstance(industry_name, str):
        return None
    for keyword, wx in _INDUSTRY_KEYWORD_WUXING.items():
        if keyword in industry_name:
            return wx
    return None


# ============================================================
# 三、五行偏旁字根（用于个股名称匹配）
# ============================================================

WUXING_RADICALS = {
    "水": re.compile(r"[水氵雨云川海河江湖泉波涛洪酒沪滨洲洋润浪潮派]"),
    "木": re.compile(r"[木林森草艹竹禾苗花茶果农材纸艺药菜梅柳柏松杨]"),
    "火": re.compile(r"[火日光电影阳星能热油气电照晖煌炎灵]"),
    "土": re.compile(r"[土石矿山岩城地基泥沙壁坤圣均尘培坚]"),
    "金": re.compile(r"[金钅铁钢银铜铝锡鑫锋锐铭钧钧镍钻钟]"),
}


def check_name_wuxing(stock_name):
    scores = {}
    for wx, pattern in WUXING_RADICALS.items():
        matches = pattern.findall(stock_name)
        if matches:
            scores[wx] = len(matches)
    return scores


def check_code_number(code, year_gan, year_zhi):
    score = 0
    gan_num = TIANGAN_NUMBER.get(year_gan)
    zhi_num = DIZHI_NUMBER.get(year_zhi)
    code_str = str(code)
    if gan_num and str(gan_num) in code_str:
        score += 2
    if zhi_num and str(zhi_num) in code_str:
        score += 2
    return score


# ============================================================
# 四、第一层：流年干支定全局基调
# ============================================================

def analyze_year_pillar(year_ganzhi):
    if len(year_ganzhi) < 2:
        return {"error": f"无效年柱: {year_ganzhi}"}

    gan = year_ganzhi[0]
    zhi = year_ganzhi[1]
    gan_wx = TIANGAN_WUXING.get(gan, "?")
    zhi_wx = DIZHI_WUXING.get(zhi, "?")

    result = {
        "year_ganzhi": year_ganzhi,
        "year_gan": gan,
        "year_zhi": zhi,
        "gan_wuxing": gan_wx,
        "zhi_wuxing": zhi_wx,
        "relation": "",
        "de_ling": [],
        "shou_ke": [],
        "bei_xie": [],
        "analysis": "",
    }

    sheng_map = WUXING_SHENG
    ke_map = WUXING_KE

    if gan_wx == zhi_wx:
        result["relation"] = "干支同气"
        result["de_ling"] = [gan_wx]
        for s, t in sheng_map.items():
            if t == gan_wx:
                result["bei_xie"] = [s]
        for k, t in ke_map.items():
            if k == gan_wx:
                result["shou_ke"] = [t]
        result["analysis"] = (
            f"{gan_wx}气冲天，干支同旺。{gan_wx}属性板块全年核心主线；"
            f"{', '.join(result['shou_ke'])}属性回避；"
            f"{', '.join(result['bei_xie'])}属性被泄气须谨慎。"
        )

    elif sheng_map.get(gan_wx) == zhi_wx:
        result["relation"] = "干生支"
        result["de_ling"] = [gan_wx, zhi_wx]
        for s, t in sheng_map.items():
            if t == gan_wx:
                result["bei_xie"] = [s]
        for k, t in ke_map.items():
            if k == zhi_wx:
                result["shou_ke"] = [t]
        result["analysis"] = (
            f"{gan_wx}生{zhi_wx}，{gan_wx}+{zhi_wx}皆旺。{gan_wx}、{zhi_wx}属性板块全年重点关注；"
            f"{', '.join(result['shou_ke'])}属性受{ke_map.get(zhi_wx+'生','')}所克须回避；"
            f"{', '.join(result['bei_xie'])}属性泄气走弱。"
        )

    elif sheng_map.get(zhi_wx) == gan_wx:
        result["relation"] = "支生干"
        result["de_ling"] = [gan_wx, zhi_wx]
        for s, t in sheng_map.items():
            if t == zhi_wx:
                result["bei_xie"] = [s]
        for k, t in ke_map.items():
            if k == gan_wx:
                result["shou_ke"] = [t]
        result["analysis"] = (
            f"{zhi_wx}生{gan_wx}，{gan_wx}+{zhi_wx}皆旺。{gan_wx}、{zhi_wx}属性板块全年重点关注；"
            f"{', '.join(result['shou_ke'])}属性受{ke_map.get(gan_wx+'生','')}所克须回避；"
            f"{', '.join(result['bei_xie'])}属性泄气走弱。"
        )

    elif ke_map.get(gan_wx) == zhi_wx:
        result["relation"] = "干克支"
        result["de_ling"] = [gan_wx]
        result["shou_ke"] = [zhi_wx]
        result["analysis"] = (
            f"{gan_wx}克{zhi_wx}（凶），{gan_wx}旺而{zhi_wx}属性被压制。"
            f"{gan_wx}属性板块走强，{zhi_wx}属性全年回避。"
        )

    elif ke_map.get(zhi_wx) == gan_wx:
        result["relation"] = "支克干"
        result["de_ling"] = [zhi_wx]
        result["shou_ke"] = [gan_wx]
        result["analysis"] = (
            f"{zhi_wx}克{gan_wx}（凶），{zhi_wx}旺而{gan_wx}属性被压制。"
            f"{zhi_wx}属性板块走强，{gan_wx}属性全年回避。"
        )

    else:
        result["relation"] = "无直接生克"
        result["de_ling"] = [gan_wx, zhi_wx]
        result["analysis"] = f"干支无直接生克，{gan_wx}+{zhi_wx}为主基调。"

    return result


# ============================================================
# 五、第三层：流月轮动筛选
# ============================================================

MONTH_ZHI_WUXING = {
    "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土",
    "亥": "水", "子": "水", "丑": "土",
}

MONTH_ADVICE = {
    1: ("寅", "木"), 2: ("卯", "木"), 3: ("辰", "土"),
    4: ("巳", "火"), 5: ("午", "火"), 6: ("未", "土"),
    7: ("申", "金"), 8: ("酉", "金"), 9: ("戌", "土"),
    10: ("亥", "水"), 11: ("子", "水"), 12: ("丑", "土"),
}


def analyze_month_overlay(lunar_month, month_zhi, year_result):
    month_wx = DIZHI_WUXING.get(month_zhi, "?")
    de_ling = year_result.get("de_ling", [])
    shou_ke = year_result.get("shou_ke", [])
    bei_xie = year_result.get("bei_xie", [])

    result = {
        "lunar_month": lunar_month,
        "month_zhi": month_zhi,
        "month_wuxing": month_wx,
        "supports_year": False,
        "opposes_year": False,
        "priority_wx": [],
        "priority_industries": [],
        "caution_industries": [],
        "analysis": "",
    }

    if month_wx in de_ling:
        result["supports_year"] = True
        result["priority_wx"] = [month_wx] + [w for w in de_ling if w != month_wx]
        result["analysis"] = (
            f"月令扶旺年令({', '.join(de_ling)})，{month_wx}属性本月重点关注，顺势做多。"
        )
    elif month_wx in shou_ke:
        result["opposes_year"] = True
        result["analysis"] = (
            f"月令{month_wx}恰逢年令受克方，本月或有反弹/逆转机会，但须极度谨慎。"
        )
        result["priority_wx"] = de_ling
    elif month_wx in bei_xie:
        result["analysis"] = (
            f"月令{month_wx}处于泄气位置，宜观望等待下一个得令月份。"
        )
        result["priority_wx"] = de_ling
    else:
        result["priority_wx"] = de_ling
        result["analysis"] = f"月令{month_wx}中性，维持年令主线{', '.join(de_ling)}。"
        if month_wx and month_wx not in de_ling:
            result["analysis"] += f" 月{month_wx}可作辅助轮动。"

    for wx in result["priority_wx"][:2]:
        if wx in CHENNANPENG_INDUSTRY_WUXING:
            result["priority_industries"].extend(CHENNANPENG_INDUSTRY_WUXING[wx])

    for wx in shou_ke:
        if wx in CHENNANPENG_INDUSTRY_WUXING:
            result["caution_industries"].extend(CHENNANPENG_INDUSTRY_WUXING[wx])

    return result


# ============================================================
# 六、第四层：个股匹配筛选 + 第五层：回避清单
# ============================================================

def _has_akshare():
    try:
        import akshare
        return True
    except ImportError:
        return False


def _fetch_all_stocks():
    if not _has_akshare():
        raise RuntimeError("akshare 未安装，请运行: pip install akshare>=1.17")
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    return df


def _is_valid_stock(code):
    code_str = str(code)
    if code_str.startswith("688"):
        return False
    if "ST" in code_str or "退" in code_str:
        return False
    if len(code_str) < 5:
        return False
    return True


def scan_chen_nanpeng(target_date_str=None, year_str=None):
    if target_date_str is None:
        target_date_str = datetime.now().strftime("%Y-%m-%d")

    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

    # ---- 农历转换 ----
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

    year_gan = year_ganzhi[0]
    year_zhi = year_ganzhi[1]

    year_result = analyze_year_pillar(year_ganzhi)

    # ---- 月支 ----
    month_zhi = month_ganzhi[1] if len(month_ganzhi) >= 2 else "?"
    if month_zhi == "?":
        mz_data = MONTH_ADVICE.get(lunar_month, ("?", "?"))
        month_zhi = mz_data[0]

    # ---- 月令分析 ----
    month_result = analyze_month_overlay(lunar_month, month_zhi, year_result)

    # ---- 拉取行情 ----
    has_data = False
    df = None
    try:
        df = _fetch_all_stocks()
        has_data = True
    except Exception:
        pass

    # ---- 个股筛选 ----
    candidates = []
    de_ling = year_result.get("de_ling", [])
    shou_ke = year_result.get("shou_ke", [])
    priority_industries = month_result.get("priority_industries", [])
    caution_industries = month_result.get("caution_industries", [])

    if has_data and df is not None:
        for _, row in df.iterrows():
            try:
                code = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()

                if not _is_valid_stock(code):
                    continue
                if "ST" in name or "*ST" in name or "退" in name:
                    continue

                price = float(row.get("最新价", 0) or 0)
                chg_pct = float(row.get("涨跌幅", 0) or 0)
                volume_yi = float(row.get("成交额", 0) or 0) / 100000000
                hsl = float(row.get("换手率", 0) or 0)
                amount = float(row.get("量比", 0) or 0)

                if price <= 0 or volume_yi <= 0:
                    continue

                # -- 行业五行匹配 --
                name_wx_scores = check_name_wuxing(name)
                code_number_score = check_code_number(code, year_gan, year_zhi)

                # 判断股票五行倾向
                stock_wx = None
                best_wx_score = 0
                for wx, sc in name_wx_scores.items():
                    if sc > best_wx_score:
                        best_wx_score = sc
                        stock_wx = wx

                # -- 第五层：回避清单 --
                is_avoid = False
                avoid_reason = ""
                if stock_wx and stock_wx in shou_ke:
                    is_avoid = True
                    avoid_reason = f"五行{stock_wx}为年令受克方"
                elif stock_wx and stock_wx in year_result.get("bei_xie", []):
                    is_avoid = True
                    avoid_reason = f"五行{stock_wx}为年令泄气方"

                # -- 综合评分 --
                score = 0.0
                reasons = []

                if stock_wx and stock_wx in de_ling:
                    score += 40
                    reasons.append(f"五行{stock_wx}得令(+40)")
                elif stock_wx and stock_wx not in shou_ke:
                    score += 20
                    reasons.append(f"五行{stock_wx}中性(+20)")

                score += code_number_score * 3
                if code_number_score > 0:
                    reasons.append(f"代码含干支数(+{code_number_score * 3})")

                if hsl > 5:
                    score += 15
                    reasons.append(f"换手率活跃{hsl:.1f}%(+15)")
                elif hsl > 2:
                    score += 8
                    reasons.append(f"换手率尚可{hsl:.1f}%(+8)")

                if amount > 1.5:
                    score += 10
                    reasons.append(f"量比放大{amount:.1f}(+10)")
                elif amount > 1.0:
                    score += 5

                if best_wx_score > 0:
                    score += best_wx_score * 3
                    reasons.append(f"名称含{stock_wx}偏旁(+{best_wx_score * 3})")

                if chg_pct > 3:
                    score += 5

                if is_avoid:
                    score -= 25
                    reasons.append(f"回避: {avoid_reason}(-25)")

                candidates.append({
                    "code": code,
                    "name": name,
                    "price": round(price, 2),
                    "chg_pct": round(chg_pct, 2),
                    "hsl": round(hsl, 2),
                    "amount": round(amount, 2),
                    "volume_yi": round(volume_yi, 2),
                    "stock_wx": stock_wx or "?",
                    "name_wx_score": best_wx_score,
                    "code_number_score": code_number_score,
                    "is_avoid": is_avoid,
                    "avoid_reason": avoid_reason,
                    "score": round(score, 1),
                    "reasons": reasons,
                    "action": "回避" if (is_avoid or score < 20) else
                              ("可轻仓试多" if score < 35 else "关注"),
                })
            except Exception:
                continue

    # -- 排序 --
    candidates.sort(key=lambda x: (-x["score"]))
    top_candidates = [c for c in candidates if c["score"] >= 10][:15]

    # -- 统计 --
    total_scanned = len(candidates)
    avoid_count = sum(1 for c in candidates if c["is_avoid"])
    focus_count = sum(1 for c in top_candidates if c["action"] == "关注")

    priority_wx_list = month_result.get("priority_wx", [])
    top_industries = list(dict.fromkeys(
        priority_industries[:3] if priority_industries else
        (CHENNANPENG_INDUSTRY_WUXING.get(priority_wx_list[0], [])[:3]
         if priority_wx_list else [])
    ))

    avoid_all = list(dict.fromkeys(caution_industries[:5]))

    return {
        "target_date": target_date_str,
        "lunar_month": lunar_month,
        "year_ganzhi": year_ganzhi,
        "month_ganzhi": month_ganzhi,
        "day_ganzhi": day_ganzhi,
        "month_zhi": month_zhi,
        "has_data": has_data,
        # 第一层
        "year_analysis": year_result,
        # 第三层
        "month_overlay": month_result,
        # 行业建议
        "top_industries": top_industries,
        "avoid_industries": avoid_all,
        # 个股
        "total_scanned": total_scanned,
        "avoid_count": avoid_count,
        "focus_count": focus_count,
        "candidates": top_candidates,
        "all_candidates": candidates,
    }


# ============================================================
# 七、格式化报告
# ============================================================

def format_chen_nanpeng_report(data):
    lines = []
    lines.append("=" * 60)
    lines.append("  陈南鹏·五行择时系统 —— 完整分析报告")
    lines.append("=" * 60)
    lines.append(f"  分析日期: {data['target_date']}")
    lines.append(f"  农历月份: 第{data['lunar_month']}月")
    lines.append(f"  年柱: {data['year_ganzhi']}  |  月柱: {data['month_ganzhi']}  |  日柱: {data['day_ganzhi']}")

    ya = data["year_analysis"]
    lines.append("")
    lines.append(f"【第一层】流年五行基调：{ya.get('relation','')}")
    lines.append(f"  年干{ya.get('year_gan','')}({ya.get('gan_wuxing','')}) | "
                 f"年支{ya.get('year_zhi','')}({ya.get('zhi_wuxing','')})")
    lines.append(f"  得令五行: {', '.join(ya.get('de_ling',[])) or '无'}")
    lines.append(f"  受克五行: {', '.join(ya.get('shou_ke',[])) or '无'}")
    lines.append(f"  被泄五行: {', '.join(ya.get('bei_xie',[])) or '无'}")
    lines.append(f"  解读: {ya.get('analysis','')}")

    mo = data["month_overlay"]
    lines.append("")
    lines.append(f"【第三层】流月轮动: 月令{mo.get('month_wuxing','')}")
    lines.append(f"  {mo.get('analysis','')}")

    lines.append("")
    lines.append(f"  ✅ 本月看好行业 Top 3: {', '.join(data['top_industries'][:3]) if data['top_industries'] else '暂无法确定'}")
    lines.append(f"  ⛔ 本月回避行业: {', '.join(data['avoid_industries'][:5]) if data['avoid_industries'] else '暂无法确定'}")

    lines.append("")
    lines.append(f"【第四层】个股候选池 (共{data['total_scanned']}只合格, "
                 f"回避{data['avoid_count']}只, 重点关注{data['focus_count']}只)")

    for i, c in enumerate(data["candidates"][:10], 1):
        avoid_tag = "⛔避" if c["is_avoid"] else ""
        wx_tag = f"({c['stock_wx']})" if c['stock_wx'] != '?' else ""
        lines.append(
            f"  {i}. {c['name']}({c['code']}) {wx_tag} {avoid_tag}  "
            f"评分{c['score']}  |  {c['action']}"
            f"  {' | '.join(c['reasons'][:3])}"
        )

    lines.append("")
    lines.append("=" * 60)
    lines.append("  免责声明：以上基于陈南鹏《仁者无敌》五行理论的沙盘演练，")
    lines.append("  不构成任何投资建议。五行推演仅为传统文化视角参考。")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_single_stock(c, ya):
    de_ling = ya.get("de_ling", [])
    shou_ke = ya.get("shou_ke", [])

    wx_verdict = ""
    if c["stock_wx"] in de_ling:
        wx_verdict = "⭐ 五行得令"
    elif c["stock_wx"] in shou_ke:
        wx_verdict = "⚠️ 五行受克"
    else:
        wx_verdict = "· 五行中性"

    lines = []
    lines.append(f"**{wx_verdict}**")
    lines.append(f"- 个股: {c['name']}({c['code']}) | 属性: {c['stock_wx']}")
    lines.append(f"- 换手率: {c['hsl']}% | 量比: {c['amount']} | 涨跌: {c['chg_pct']}%")
    lines.append(f"- 筛选理由: {'; '.join(c['reasons'])}")
    lines.append(f"- 操作建议: **{c['action']}**")
    if c["is_avoid"]:
        lines.append(f"- 回避原因: {c['avoid_reason']}")
    return "\n".join(lines)
