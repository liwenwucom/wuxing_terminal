# -*- coding: utf-8 -*-
"""
五行算卦引擎
节气计算、五行生克、增强/削弱判断、天干地支辅助因子
"""

from datetime import datetime
from config import (
    SOLAR_TERM_DATES, SOLAR_TERMS,
    WUXING_SHENG, WUXING_KE,
    TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    WUXING_INDUSTRY_MAP, FUTURES_WUXING_MAP,
)

try:
    from lunar_python import Lunar, Solar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False


def get_current_solar_term(dt: datetime = None) -> dict:
    """根据日期获取当前节气"""
    if dt is None:
        dt = datetime.now()
    month = dt.month
    day = dt.day

    found = SOLAR_TERM_DATES[0]
    for i, (name, m, d) in enumerate(SOLAR_TERM_DATES):
        if (month > m) or (month == m and day >= d):
            found = (name, m, d)
        else:
            break

    term_name = found[0]
    term_info = SOLAR_TERMS.get(term_name, {})
    return {
        "name": term_name,
        "month": month,
        "dominant_wuxing": term_info.get("dominant", ""),
        "secondary_wuxing": term_info.get("secondary", ""),
        "phase": term_info.get("phase", ""),
    }


def get_ganzhi_info(dt: datetime = None) -> dict:
    """获取天干地支信息（尝试使用lunar-python，失败则用简化计算）"""
    if dt is None:
        dt = datetime.now()
    if HAS_LUNAR:
        try:
            solar = Solar.fromYmd(dt.year, dt.month, dt.day)
            lunar = solar.getLunar()
            return {
                "year_ganzhi": lunar.getYearInGanZhi(),
                "month_ganzhi": lunar.getMonthInGanZhi(),
                "day_ganzhi": lunar.getDayInGanZhi(),
                "day_gan": lunar.getDayGan(),
                "day_zhi": lunar.getDayZhi(),
                "day_wuxing": TIANGAN_WUXING.get(lunar.getDayGan(), ""),
            }
        except Exception:
            pass
    # 降级：简化计算
    base_year = 1984  # 甲子年
    offset = (dt.year - base_year) % 60
    gan_idx = offset % 10
    zhi_idx = offset % 12
    day_gan = TIANGAN[gan_idx]
    day_zhi = DIZHI[zhi_idx]
    return {
        "year_ganzhi": TIANGAN[gan_idx] + DIZHI[zhi_idx],
        "month_ganzhi": "未知",
        "day_ganzhi": day_gan + day_zhi,
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "day_wuxing": TIANGAN_WUXING.get(day_gan, ""),
    }


def analyze_wuxing_boost(news_wuxing: str, dt: datetime = None) -> dict:
    """分析新闻五行与当前节气的生克关系，返回增强/当令/削弱判断"""
    if dt is None:
        dt = datetime.now()

    term = get_current_solar_term(dt)
    ganzhi = get_ganzhi_info(dt)
    term_dominant = term["dominant_wuxing"]

    if not news_wuxing or news_wuxing == "未匹配":
        return {
            "boost_level": "中性",
            "boost_label": "五行未匹配",
            "detail": f"新闻未匹配到明确五行。当前节气「{term['name']}」主导{term_dominant}，可关注{term_dominant}属性行业。",
            "term": term,
            "ganzhi": ganzhi,
            "score_modifier": 0.0,
        }

    # 判断主气与新闻五行的生克关系
    if term_dominant in WUXING_SHENG and WUXING_SHENG[term_dominant] == news_wuxing:
        boost_level = "增强"
        detail = f"节气「{term['name']}」主导{term_dominant}，{term_dominant}生{news_wuxing}，新闻相关行业受到节气周期提振。"
        score_modifier = 0.3
    elif news_wuxing == term_dominant:
        boost_level = "当令"
        detail = f"新闻五行「{news_wuxing}」与节气主导五行一致，同气相求，行业处于当令周期。"
        score_modifier = 0.2
    elif term_dominant in WUXING_KE and WUXING_KE[term_dominant] == news_wuxing:
        boost_level = "削弱"
        detail = f"节气「{term['name']}」主导{term_dominant}，{term_dominant}克{news_wuxing}，新闻相关行业受节气周期压制。"
        score_modifier = -0.25
    elif news_wuxing in WUXING_KE and WUXING_KE[news_wuxing] == term_dominant:
        boost_level = "轻微削弱"
        detail = f"新闻五行「{news_wuxing}」克节气主导五行{term_dominant}，行业方向逆节气而动。"
        score_modifier = -0.1
    else:
        boost_level = "中性"
        detail = f"新闻五行「{news_wuxing}」与节气主导五行「{term_dominant}」无直接生克关系。"
        score_modifier = 0.0

    # 天干地支辅助因子（日干支五行与新闻五行一致时微调）
    ganzhi_boost = 0.0
    ganzhi_wuxing = ganzhi.get("day_wuxing", "")
    if ganzhi_wuxing and ganzhi_wuxing == news_wuxing:
        ganzhi_boost = 0.05
        detail += " 日干支五行与新闻五行一致，微幅增强。"

    return {
        "boost_level": boost_level,
        "boost_label": boost_level if boost_level != "轻微削弱" else "削弱",
        "detail": detail,
        "term": term,
        "ganzhi": ganzhi,
        "score_modifier": score_modifier + ganzhi_boost,
    }


def map_news_to_wuxing(news_text: str, keywords_hit: list = None) -> str:
    """根据新闻文本判断主要五行属性"""
    from config import find_wuxing_by_keywords
    hits = find_wuxing_by_keywords(news_text)
    if not hits:
        return "未匹配"
    main_wuxing = max(hits, key=lambda k: len(hits[k]))
    return main_wuxing


def get_wuxing_industries(wuxing: str) -> list:
    """获取某五行对应的所有行业"""
    if wuxing in WUXING_INDUSTRY_MAP:
        return WUXING_INDUSTRY_MAP[wuxing]["industries"]
    return []


def get_wuxing_futures(wuxing: str) -> list:
    """获取某五行对应的期货品种"""
    if wuxing in FUTURES_WUXING_MAP:
        return FUTURES_WUXING_MAP[wuxing]["contracts"]
    return []


def get_wuxing_market_color(wuxing: str) -> str:
    """获取五行对应的展示颜色"""
    colors = {"火": "red", "金": "gold", "土": "brown", "水": "blue", "木": "green"}
    return colors.get(wuxing, "gray")
