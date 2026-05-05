# -*- coding: utf-8 -*-
"""
玄捉妖·期货 扫描系统 —— 主引擎
========================================
融合玄学五行 + 实时期货数据 + 政策事件共振 + 地域八卦

核心能力：
  1. 品种出厂设定：IPO日期 → 日元天干
  2. 品种五行二次映射：实物属性硬性五行
  3. 本气纯真检测：日元五行==实物五行 → 承载力翻倍
  4. 十二长生承载力推演（10天干×12地支全量）
  5. 月令共振 + 节气气场
  6. 政策事件 → 五行映射
  7. 地域八卦方位共振
  8. 多空方向判定 + 资金验证（骗炮/反转/主力做多）
  9. 综合评分(0-100) → 捉妖候选池 Top 15

数据源：akshare 六大期货交易所所有活跃主力合约实时行情
"""

import sys
import os
import json
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd


# ============================================================
# 一、基础常量
# ============================================================

TIANGAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

DIZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

MONTH_ZHI_WUXING = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# ============================================================
# 二、十二长生承载力评分
# ============================================================
CAPACITY_SCORES = {
    "帝旺": 100, "临官": 85, "冠带": 70, "沐浴": 50,
    "长生": 40, "衰": 20, "病": -10, "死": -30,
    "墓": -40, "绝": -60, "胎": -20, "养": 0,
}

FUTURES_EXPECTED_RANGE = {
    "帝旺": "≥+1.5%~+3% 极强做多信号",
    "临官": "+1.0%~+2.0% 方向明确偏多",
    "冠带": "+0.3%~+1.0% 中等偏多",
    "沐浴": "<±0.5% 震荡",
    "长生": "0%~+0.5% 弱多",
    "衰": "偏空，下跌倾向",
    "病": "偏空，文跌倾向强",
    "死": "下跌预期极强",
    "墓": "下跌预期极强，可能踩踏",
    "绝": "下跌预期极强，空头主导",
    "胎": "弱势震荡",
    "养": "弱势但接近拐点",
}

# ============================================================
# 三、十二长生表（10天干 × 12地支）
# ============================================================
CHANG_SHENG_TABLE = {
    "甲": {"亥": 0, "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6, "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11},
    "乙": {"午": 0, "巳": 1, "辰": 2, "卯": 3, "寅": 4, "丑": 5, "子": 6, "亥": 7, "戌": 8, "酉": 9, "申": 10, "未": 11},
    "丙": {"寅": 0, "卯": 1, "辰": 2, "巳": 3, "午": 4, "未": 5, "申": 6, "酉": 7, "戌": 8, "亥": 9, "子": 10, "丑": 11},
    "丁": {"酉": 0, "申": 1, "未": 2, "午": 3, "巳": 4, "辰": 5, "卯": 6, "寅": 7, "丑": 8, "子": 9, "亥": 10, "戌": 11},
    "戊": {"寅": 0, "卯": 1, "辰": 2, "巳": 3, "午": 4, "未": 5, "申": 6, "酉": 7, "戌": 8, "亥": 9, "子": 10, "丑": 11},
    "己": {"酉": 0, "申": 1, "未": 2, "午": 3, "巳": 4, "辰": 5, "卯": 6, "寅": 7, "丑": 8, "子": 9, "亥": 10, "戌": 11},
    "庚": {"巳": 0, "午": 1, "未": 2, "申": 3, "酉": 4, "戌": 5, "亥": 6, "子": 7, "丑": 8, "寅": 9, "卯": 10, "辰": 11},
    "辛": {"子": 0, "亥": 1, "戌": 2, "酉": 3, "申": 4, "未": 5, "午": 6, "巳": 7, "辰": 8, "卯": 9, "寅": 10, "丑": 11},
    "壬": {"申": 0, "酉": 1, "戌": 2, "亥": 3, "子": 4, "丑": 5, "寅": 6, "卯": 7, "辰": 8, "巳": 9, "午": 10, "未": 11},
    "癸": {"卯": 0, "寅": 1, "丑": 2, "子": 3, "亥": 4, "戌": 5, "酉": 6, "申": 7, "未": 8, "午": 9, "巳": 10, "辰": 11},
}
STAGE_NAMES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]


def _get_stage(riyuan_gan: str, day_zhi: str) -> str:
    idx = CHANG_SHENG_TABLE.get(riyuan_gan, {}).get(day_zhi, -1)
    if idx < 0:
        return "衰"
    return STAGE_NAMES[idx]


# ============================================================
# 四、实物五行硬性映射（品种出厂二次映射）
# ============================================================
# 根据实物属性硬性映射，与日元五行独立
PHYSICAL_WUXING = {
    # 金：贵金属 + 有色金属 + 黑色钢铁
    "AU": "金", "AG": "金", "CU": "金", "BC": "金", "AL": "金",
    "ZN": "金", "PB": "金", "NI": "金", "SN": "金",
    "RB": "金", "HC": "金", "WR": "金", "SS": "金",
    "I": "金",   # 铁矿石 → 金属
    "SM": "金", "SF": "金",  # 锰硅/硅铁 → 合金金属
    "LC": "金",  # 碳酸锂 → 锂金属

    # 木：农产品 + 天然纤维 + 纸浆
    "CF": "木", "SR": "木", "SP": "木",
    "RU": "木", "NR": "木",  # 橡胶 → 橡树产物

    # 水：原油系 + 液体化工 + 航运
    "SC": "水", "FU": "水", "LU": "水", "BU": "水",
    "PG": "水",  # 液化气 → 液体能源
    "SA": "水",  # 纯碱 → 水溶液化工
    "MA": "水",  # 甲醇 → 液体化工
    "UR": "水",  # 尿素 → 液体化肥
    "SH": "水",  # 烧碱 → 水溶液
    "EC": "水",  # 集运 → 海运

    # 火：煤炭 + 能源 + 高温化工
    "J": "火", "JM": "火",   # 焦炭/焦煤
    "EG": "火",              # 乙二醇 → 能源化工
    "TA": "火", "PF": "火",  # PTA/短纤 → 石化
    "L": "火", "V": "火", "PP": "火",  # 塑料系 → 石化
    "EB": "火",              # 苯乙烯 → 石化

    # 土：建材 + 谷物 + 禽畜
    "FG": "土",              # 玻璃 → 建材
    "A": "土", "B": "土",    # 大豆
    "C": "土", "CS": "土",   # 玉米
    "M": "土",               # 豆粕
    "Y": "土", "P": "土", "OI": "土", "RM": "土",  # 油脂油料
    "WH": "土", "PM": "土",  # 小麦
    "LH": "土", "JD": "土",  # 生猪/鸡蛋 → 畜产
    "AP": "土", "CJ": "土", "PK": "土",  # 水果干果花生
    "SI": "土",              # 工业硅 → 矿砂
    "IF": "土", "IC": "土", "IM": "土", "IH": "土",  # 股指 → 大盘土
    "T": "土",               # 国债 → 固收土
}

# ============================================================
# 五、品种信息池（从 CHINA_FUTURES_POOL + FUTURES_IPO_DATE_MAP 构建）
# ============================================================
CHINA_FUTURES_POOL = {
    "上期所": [
        {"name": "沪金", "symbol": "AU", "unit": "1000克/手", "margin": "约4万/手"},
        {"name": "沪银", "symbol": "AG", "unit": "15千克/手", "margin": "约1万/手"},
        {"name": "沪铜", "symbol": "CU", "unit": "5吨/手", "margin": "约3.5万/手"},
        {"name": "国际铜", "symbol": "BC", "unit": "5吨/手", "margin": "约2万/手"},
        {"name": "沪铝", "symbol": "AL", "unit": "5吨/手", "margin": "约8000/手"},
        {"name": "沪锌", "symbol": "ZN", "unit": "5吨/手", "margin": "约1.2万/手"},
        {"name": "沪铅", "symbol": "PB", "unit": "5吨/手", "margin": "约8000/手"},
        {"name": "沪镍", "symbol": "NI", "unit": "1吨/手", "margin": "约2万/手"},
        {"name": "沪锡", "symbol": "SN", "unit": "1吨/手", "margin": "约3万/手"},
        {"name": "螺纹钢", "symbol": "RB", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "热卷", "symbol": "HC", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "线材", "symbol": "WR", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "不锈钢", "symbol": "SS", "unit": "5吨/手", "margin": "约7000/手"},
        {"name": "原油", "symbol": "SC", "unit": "1000桶/手", "margin": "约6万/手"},
        {"name": "燃料油", "symbol": "FU", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "低硫燃油", "symbol": "LU", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "沥青", "symbol": "BU", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "橡胶", "symbol": "RU", "unit": "10吨/手", "margin": "约1.2万/手"},
        {"name": "20号胶", "symbol": "NR", "unit": "10吨/手", "margin": "约1万/手"},
        {"name": "纸浆", "symbol": "SP", "unit": "10吨/手", "margin": "约5000/手"},
    ],
    "能源中心": [
        {"name": "集运指数(欧线)", "symbol": "EC", "unit": "指数点×50元", "margin": "约2万/手"},
    ],
    "大商所": [
        {"name": "铁矿石", "symbol": "I", "unit": "100吨/手", "margin": "约1万/手"},
        {"name": "焦炭", "symbol": "J", "unit": "100吨/手", "margin": "约3万/手"},
        {"name": "焦煤", "symbol": "JM", "unit": "60吨/手", "margin": "约1.5万/手"},
        {"name": "豆粕", "symbol": "M", "unit": "10吨/手", "margin": "约2500/手"},
        {"name": "豆一", "symbol": "A", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "豆二", "symbol": "B", "unit": "10吨/手", "margin": "约2500/手"},
        {"name": "豆油", "symbol": "Y", "unit": "10吨/手", "margin": "约5000/手"},
        {"name": "棕榈油", "symbol": "P", "unit": "10吨/手", "margin": "约6000/手"},
        {"name": "玉米", "symbol": "C", "unit": "10吨/手", "margin": "约1500/手"},
        {"name": "玉米淀粉", "symbol": "CS", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "生猪", "symbol": "LH", "unit": "16吨/手", "margin": "约4万/手"},
        {"name": "鸡蛋", "symbol": "JD", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "塑料(LDPE)", "symbol": "L", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "PVC", "symbol": "V", "unit": "5吨/手", "margin": "约3000/手"},
        {"name": "聚丙烯", "symbol": "PP", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "苯乙烯", "symbol": "EB", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "乙二醇", "symbol": "EG", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "LPG", "symbol": "PG", "unit": "20吨/手", "margin": "约8000/手"},
    ],
    "郑商所": [
        {"name": "PTA", "symbol": "TA", "unit": "5吨/手", "margin": "约2000/手"},
        {"name": "短纤", "symbol": "PF", "unit": "5吨/手", "margin": "约2500/手"},
        {"name": "甲醇", "symbol": "MA", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "纯碱", "symbol": "SA", "unit": "20吨/手", "margin": "约4000/手"},
        {"name": "尿素", "symbol": "UR", "unit": "20吨/手", "margin": "约4000/手"},
        {"name": "玻璃", "symbol": "FG", "unit": "20吨/手", "margin": "约3500/手"},
        {"name": "锰硅", "symbol": "SM", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "硅铁", "symbol": "SF", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "白糖", "symbol": "SR", "unit": "10吨/手", "margin": "约4000/手"},
        {"name": "棉花", "symbol": "CF", "unit": "5吨/手", "margin": "约5000/手"},
        {"name": "苹果", "symbol": "AP", "unit": "10吨/手", "margin": "约6000/手"},
        {"name": "红枣", "symbol": "CJ", "unit": "5吨/手", "margin": "约5000/手"},
        {"name": "花生", "symbol": "PK", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "菜油", "symbol": "OI", "unit": "10吨/手", "margin": "约5000/手"},
        {"name": "菜粕", "symbol": "RM", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "强麦", "symbol": "WH", "unit": "20吨/手", "margin": "约5000/手"},
    ],
    "广期所": [
        {"name": "碳酸锂", "symbol": "LC", "unit": "1吨/手", "margin": "约1.5万/手"},
        {"name": "工业硅", "symbol": "SI", "unit": "5吨/手", "margin": "约5000/手"},
    ],
    "中金所": [
        {"name": "沪深300股指", "symbol": "IF", "unit": "指数点×300元", "margin": "约12万/手"},
        {"name": "中证500股指", "symbol": "IC", "unit": "指数点×200元", "margin": "约14万/手"},
        {"name": "中证1000股指", "symbol": "IM", "unit": "指数点×200元", "margin": "约11万/手"},
        {"name": "上证50股指", "symbol": "IH", "unit": "指数点×300元", "margin": "约9万/手"},
        {"name": "10年期国债", "symbol": "T", "unit": "面值100万元", "margin": "约2万/手"},
    ],
    "郑商所补充": [
        {"name": "烧碱", "symbol": "SH", "unit": "30吨/手", "margin": "约5000/手"},
        {"name": "普麦", "symbol": "PM", "unit": "20吨/手", "margin": "约5000/手"},
    ],
}

FUTURES_IPO_DATE_MAP = {
    "AU": "2008-01-09", "AG": "2012-05-10", "CU": "1993-11-23", "BC": "2020-11-19",
    "AL": "1993-11-23", "ZN": "2007-03-26", "PB": "2011-03-24", "NI": "2015-03-27",
    "SN": "2015-03-27", "RB": "2009-03-27", "HC": "2014-03-21", "WR": "2009-03-27",
    "SS": "2019-09-25", "I": "2013-10-18", "SC": "2018-03-26", "FU": "2004-08-25",
    "LU": "2020-06-22", "BU": "2013-10-09", "J": "2011-04-15", "JM": "2013-03-22",
    "M": "2000-07-17", "A": "2002-03-15", "B": "2004-12-22", "Y": "2006-01-09",
    "P": "2007-10-29", "C": "2004-09-22", "CS": "2014-12-19", "LH": "2021-01-08",
    "JD": "2013-11-08", "L": "2007-07-31", "V": "2009-05-25", "PP": "2014-02-28",
    "EB": "2019-09-26", "EG": "2018-12-10", "PG": "2020-03-30", "TA": "2006-12-18",
    "PF": "2020-10-12", "MA": "2011-10-28", "SA": "2019-12-06", "UR": "2019-08-09",
    "FG": "2012-12-03", "SM": "2014-08-08", "SF": "2014-08-08", "SR": "2006-01-06",
    "CF": "2004-06-01", "AP": "2017-12-22", "CJ": "2019-04-30", "PK": "2021-02-01",
    "OI": "2007-06-08", "RM": "2012-12-28", "WH": "2003-03-28", "RU": "1993-11-23",
    "NR": "2019-08-12", "SP": "2018-11-27", "EC": "2023-08-18", "LC": "2023-07-21",
    "SI": "2022-12-22", "IF": "2010-04-16", "IC": "2015-04-16", "IM": "2022-07-22",
    "IH": "2015-04-16", "T": "2015-03-20", "SH": "2023-09-15", "PM": "2003-03-28",
}


def _get_all_futures() -> list:
    """提取全部期货品种统一列表"""
    products = {}
    for exchange, items in CHINA_FUTURES_POOL.items():
        for item in items:
            sym = item["symbol"]
            if sym not in products:
                products[sym] = {
                    "symbol": sym,
                    "name": item["name"],
                    "exchange": exchange,
                    "unit": item["unit"],
                    "margin": item["margin"],
                }
    all_list = sorted(products.values(), key=lambda x: x["symbol"])
    return all_list


# ============================================================
# 六、干支计算器
# ============================================================
_GANZHI_CACHE = {}
_RIYUAN_CACHE = {}


def _get_day_ganzhi(date_str: str) -> dict:
    if date_str in _GANZHI_CACHE:
        return _GANZHI_CACHE[date_str]
    try:
        from lunar_python import Solar
        parts = [int(x) for x in date_str.split("-")]
        solar = Solar.fromYmd(*parts)
        lunar = solar.getLunar()
        year_gz = lunar.getYearInGanZhi()
        month_gz = lunar.getMonthInGanZhi()
        day_gz = lunar.getDayInGanZhi()
        result = {
            "date": date_str,
            "year_ganzhi": year_gz, "month_ganzhi": month_gz, "day_ganzhi": day_gz,
            "year_gan": year_gz[0], "year_zhi": year_gz[1],
            "month_gan": month_gz[0], "month_zhi": month_gz[1],
            "day_gan": day_gz[0], "day_zhi": day_gz[1],
            "day_wuxing": TIANGAN_WUXING.get(day_gz[0], ""),
            "month_wuxing": MONTH_ZHI_WUXING.get(month_gz[1], ""),
        }
        _GANZHI_CACHE[date_str] = result
        return result
    except Exception:
        fb = {"date": date_str, "year_ganzhi": "", "month_ganzhi": "", "day_ganzhi": "",
              "year_gan": "", "year_zhi": "", "month_gan": "", "month_zhi": "",
              "day_gan": "", "day_zhi": "", "day_wuxing": "", "month_wuxing": ""}
        _GANZHI_CACHE[date_str] = fb
        return fb


def _get_riyuan(symbol: str) -> dict:
    if symbol in _RIYUAN_CACHE:
        return _RIYUAN_CACHE[symbol]
    ipo = FUTURES_IPO_DATE_MAP.get(symbol, "")
    if not ipo:
        h = sum(ord(c) for c in symbol) % 10
        gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        gan = gan_list[h]
        result = {"gan": gan, "wuxing": TIANGAN_WUXING.get(gan, "火"), "ganzhi": gan + "辰"}
    else:
        try:
            from lunar_python import Solar
            y, m, d = [int(x) for x in ipo.split("-")]
            solar = Solar.fromYmd(y, m, d)
            lunar = solar.getLunar()
            ganzhi = lunar.getDayInGanZhi()
            gan = ganzhi[0]
            result = {"gan": gan, "wuxing": TIANGAN_WUXING.get(gan, "火"), "ganzhi": ganzhi}
        except Exception:
            result = {"gan": "戊", "wuxing": "土", "ganzhi": "戊辰"}
    _RIYUAN_CACHE[symbol] = result
    return result


# ============================================================
# 七、五行关系
# ============================================================
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _wuxing_rel(a: str, b: str) -> str:
    if not a or not b:
        return "无"
    if a == b:
        return "同气"
    if WUXING_SHENG.get(a) == b:
        return "a生b"
    if WUXING_SHENG.get(b) == a:
        return "b生a"
    if WUXING_KE.get(a) == b:
        return "a克b"
    if WUXING_KE.get(b) == a:
        return "b克a"
    return "无"


# ============================================================
# 八、政策事件 → 五行
# ============================================================
POLICY_EVENT_WUXING = {
    "中东": "火", "地缘冲突": "火", "OPEC": "火", "产油国": "火",
    "导弹": "火", "空袭": "火", "石油": "火", "天然气": "火", "能源": "火",

    "贸易战": "金", "关税": "金", "制裁": "金", "出口管制": "金",
    "反倾销": "金", "贸易协议": "金",

    "基建": "土", "放水": "土", "城镇化": "土", "房地产": "土",
    "城中村": "土", "保障房": "土", "城市更新": "土",
    "气候": "土", "乾旱": "土", "农产品": "土", "大豆": "土", "玉米": "土",

    "航运": "水", "物流": "水", "港口": "水", "海运": "水", "水运": "水",

    "碳中和": "火", "减排": "火", "碳达峰": "火",
    "芯片": "火", "半导体": "火", "AI": "火", "人工智能": "火", "算力": "火",
    "新能源": "火", "光伏": "火", "风电": "火", "储能": "火",
    "黄金": "金", "央行购金": "金", "美联储": "金",
    "环保": "水", "水利": "水",
    "汇率": "金", "利率": "金", "降息": "金", "加息": "金",
}


def _resolve_policy_wuxing(text: str) -> list:
    wxs = set()
    for kw, wx in POLICY_EVENT_WUXING.items():
        if kw in text:
            wxs.add(wx)
    return list(wxs)


# ============================================================
# 九、地域 → 八卦 → 五行
# ============================================================
BAGUA_WUXING = {"震": "木", "巽": "木", "离": "火", "坤": "土", "艮": "土",
                "乾": "金", "兑": "金", "坎": "水"}

REGION_BAGUA = {
    "上海": "震", "浙江": "震", "江苏": "震", "安徽": "震",
    "福建": "巽",
    "广东": "离", "广西": "离", "海南": "离",
    "湖南": "离", "湖北": "离", "江西": "离",
    "四川": "坤", "重庆": "坤", "云南": "坤", "贵州": "坤", "西藏": "坤",
    "河南": "坤",
    "北京": "坎", "天津": "坎", "河北": "坎", "山西": "坎",
    "内蒙古": "坎", "辽宁": "坎", "吉林": "坎", "黑龙江": "坎",
    "山东": "艮",
    "陕西": "兑", "甘肃": "兑", "青海": "兑",
    "宁夏": "乾", "新疆": "乾",
}

# 事件发生地 → 地域关键词
EVENT_REGION_MAP = {
    "中东": "离", "伊朗": "离", "沙特": "离", "伊拉克": "离",
    "川渝": "坤", "四川": "坤", "成都": "坤", "重庆": "坤",
    "大湾区": "离", "广东": "离", "深圳": "离",
    "长三角": "震", "上海": "震", "浙江": "震", "江苏": "震",
    "京津冀": "坎", "北京": "坎", "天津": "坎", "河北": "坎",
    "东三省": "坎", "东北": "艮",
    "西北": "兑", "新疆": "兑", "甘肃": "兑",
}


def _resolve_region(events_text: str) -> str:
    for kw, gua in EVENT_REGION_MAP.items():
        if kw in events_text:
            return gua
    return ""


# ============================================================
# 十、月令共振评分
# ============================================================
def _monthly_resonance(phys_wx: str, month_zhi_wx: str) -> dict:
    score = 10
    details = []
    if phys_wx and month_zhi_wx:
        rel = _wuxing_rel(month_zhi_wx, phys_wx)
        if rel == "同气":
            score += 15
            details.append(f"🔥 月令{month_zhi_wx}当令 × 品种{phys_wx}同气(主线直扶)")
        elif "生" in rel and "b生a" == rel:
            score += 10
            details.append(f"月令{month_zhi_wx}生品种{phys_wx}(天时生扶)")
        elif "克" in rel and "a克b" == rel:
            score -= 5
            details.append(f"月令{month_zhi_wx}克品种{phys_wx}(天时不利)")
        elif "克" in rel and "b克a" == rel:
            score += 3
            details.append(f"品种{phys_wx}克月令{month_zhi_wx}(逆势能支)")
        else:
            details.append(f"月令{month_zhi_wx} × 品种{phys_wx} 中性")
    is_main = score >= 25
    return {"score": max(0, min(30, score)), "is_main": is_main, "detail": "；".join(details) if details else "—"}


# ============================================================
# 十一、事件共振评分
# ============================================================
def _event_resonance(phys_wx: str, policy_wx_list: list, events_text: str) -> dict:
    score = 5
    details = []
    matched = False
    for pw in policy_wx_list:
        rel = _wuxing_rel(pw, phys_wx)
        if rel in ("同气", "a生b"):
            score += 10
            details.append(f"政策「{pw}」× 品种「{phys_wx}」共振({rel})")
            matched = True
        elif rel == "b克a":
            score -= 3
            details.append(f"政策{pw}被品种{phys_wx}克(对冲)")
    if not matched:
        details.append("政策与品种无直接共振")
    return {"score": max(0, min(30, score)), "detail": "；".join(details) if details else "—"}


# ============================================================
# 十二、多空方向判定 + 资金验证
# ============================================================
def _determine_direction(stage: str, capacity: int, chg_pct: float, capacity_trend: str) -> dict:
    """
    判定期货品种的多空方向 + 资金验证
    """
    direction = "观望"
    reason = ""
    fund = "待观察"

    if stage in ("帝旺", "临官"):
        if capacity_trend == "增强":
            if chg_pct > 0.8:
                direction = "只多"
                reason = "帝旺/临官 + 量价齐升 + 承载力增强，多头明确"
                fund = "主力做多"
            elif chg_pct > 0:
                direction = "偏多"
                reason = "承载力强但涨幅有限，可轻仓做多"
                fund = "待观察"
            else:
                direction = "观望"
                reason = "承载力强但价格下跌，多单骗炮嫌疑"
                fund = "多单骗炮"
        else:
            if chg_pct > 0:
                direction = "偏多"
                reason = "承载力强但趋势震荡，谨慎偏多"
                fund = "待观察"
            else:
                direction = "观望"
                reason = "承载力强但趋势不明+价格跌，观望"
                fund = "待观察"
    elif stage in ("死", "墓", "绝"):
        if chg_pct < -1.0:
            if abs(chg_pct) < 3.0:
                direction = "只空"
                reason = "死/墓/绝 + 量增价跌，空头主导"
                fund = "主力做空"
            else:
                direction = "偏空"
                reason = "暴跌但可能超卖，空头力量衰竭边缘"
                fund = "空头衰竭警惕"
        elif chg_pct < 0:
            direction = "偏空"
            reason = "承载力极弱，偏空方向"
            fund = "偏空"
        else:
            direction = "观望"
            reason = "承载力极弱但价格未跌，可能资金抵抗"
            fund = "待观察"
    elif stage in ("冠带",):
        if chg_pct > 0.3:
            direction = "多空皆可"
            reason = "承载力中等偏强 + 正涨幅，可短线做多"
            fund = "短线偏多"
        else:
            direction = "多空皆可"
            reason = "承载力中等，双向皆可，需设紧止损"
            fund = "待观察"
    else:
        if chg_pct > 0.5:
            direction = "偏多"
            reason = "承载力一般但涨幅不错，短线试多"
            fund = "待观察"
        elif chg_pct < -0.5:
            direction = "偏空"
            reason = "承载力一般但下跌明显，偏空"
            fund = "偏空"
        else:
            direction = "多空皆可"
            reason = "承载力一般，方向震荡"
            fund = "待观察"

    return {"direction": direction, "reason": reason, "fund_signal": fund}


# ============================================================
# 十三、综合评分 (0-100)
# ============================================================

def _composite_futures(capacity: int, is_benqi: bool, monthly_res: dict,
                       event_res: dict, direction_info: dict, chg_pct: float) -> dict:
    cap_norm = (capacity + 60) / 160 * 100
    cap_norm = max(0, min(100, cap_norm))
    if is_benqi:
        cap_norm = min(100, cap_norm * 1.3)  # 本气纯真加成

    monthly_norm = monthly_res["score"] / 30 * 100
    event_norm = event_res["score"] / 30 * 100

    dir_scores = {"主力做多": 95, "只多": 88, "偏多": 70, "多空皆可": 55, "偏空": 40, "只空": 30,
                  "主力做空": 35, "空头衰竭警惕": 25, "多单骗炮": 20, "观望": 35, "待观察": 50}
    dir_norm = dir_scores.get(direction_info.get("fund_signal", "待观察"), 50)

    momentum_norm = max(0, min(100, 50 + chg_pct * 6))

    total = round(
        cap_norm * 0.30 + monthly_norm * 0.20 + event_norm * 0.15 +
        dir_norm * 0.25 + momentum_norm * 0.10, 1,
    )

    return {
        "total": total,
        "breakdown": {
            "承载力(30%)": round(cap_norm * 0.30, 1),
            "月令共振(20%)": round(monthly_norm * 0.20, 1),
            "事件共振(15%)": round(event_norm * 0.15, 1),
            "多空验证(25%)": round(dir_norm * 0.25, 1),
            "动量信号(10%)": round(momentum_norm * 0.10, 1),
        },
    }


# ============================================================
# 十四、获取实时期货数据（akshare）
# ============================================================

def _fetch_futures_prices() -> dict:
    """拉取全部期货主力合约实时价格"""
    prices = {}
    try:
        import akshare as ak
        df = ak.futures_main_sina()
        for _, row in df.iterrows():
            sym_raw = str(row.get("symbol", "")).strip()
            if sym_raw.endswith("0"):
                sym = sym_raw[:-1]
            else:
                sym = sym_raw
            try:
                prices[sym] = {
                    "price": float(row.get("price", 0)),
                    "chg_pct": float(row.get("chg", 0) or 0),
                    "volume": float(row.get("volume", 0) or 0),
                    "open_interest": float(row.get("open_interest", 0) or 0),
                }
            except (ValueError, TypeError):
                pass
        print(f"[玄捉妖·期货] akshare拉取: {len(prices)} 个品种价格")
    except Exception as e:
        print(f"[玄捉妖·期货] akshare拉取失败({e})，使用模拟数据")
        prices = {}
    return prices


# ============================================================
# 十五、主扫描函数
# ============================================================

def scan_futures_zhuoyao(target_date_str: str = None,
                         policy_details: list = None,
                         min_composite: float = 20.0) -> dict:
    """
    玄捉妖·期货 主扫描函数

    Returns: {target_date, month_zhi_wx, policy_wx_list, total_scanned,
              stats, results[], top15[], ...}
    """
    if target_date_str is None:
        target_date_str = "2026-05-05"

    print(f"\n{'='*60}")
    print(f"🐉 玄捉妖·期货 扫描系统 启动")
    print(f"   目标日: {target_date_str}")
    print(f"{'='*60}")

    # ---- 天时 ----
    target_gz = _get_day_ganzhi(target_date_str)
    month_zhi_wx = target_gz.get("month_wuxing", "")
    day_zhi = target_gz.get("day_zhi", "")

    # ---- 政策事件 ----
    if policy_details is None:
        policy_details = []
    events_text = " ".join(policy_details)
    policy_wx_list = _resolve_policy_wuxing(events_text)

    print(f"   月令五行: {month_zhi_wx} | 日支: {day_zhi}")
    print(f"   政策五行: {policy_wx_list if policy_wx_list else '无'}")

    # ---- 获取实时期货价格 ----
    prices = _fetch_futures_prices()
    has_rt = len(prices) > 0

    # ---- 遍历全部期货品种 ----
    all_futures = _get_all_futures()
    results = []

    for prod in all_futures:
        sym = prod["symbol"]
        name = prod["name"]

        # 实物五行
        phys_wx = PHYSICAL_WUXING.get(sym, "火")

        # IPO → 日元
        riyuan = _get_riyuan(sym)
        riyuan_gan = riyuan["gan"]
        riyuan_wx = riyuan["wuxing"]

        # 本气纯真检测
        is_benqi = (riyuan_wx == phys_wx)

        # 承载力
        stage = _get_stage(riyuan_gan, day_zhi)
        capacity = CAPACITY_SCORES.get(stage, 0)
        expected = FUTURES_EXPECTED_RANGE.get(stage, "—")

        # 本气纯真 → 承载力翻倍
        if is_benqi:
            capacity_eff = min(capacity * 2, 100) if capacity > 0 else capacity  # 负值不翻倍
        else:
            capacity_eff = capacity

        # 实时价格
        rt = prices.get(sym, {})
        chg_pct = rt.get("chg_pct", 0)
        rt_price = rt.get("price", 0)
        rt_volume = rt.get("volume", 0)

        # 承载力趋势简化（单日无法判断5日，使用方向判定代替）
        if stage in ("帝旺", "临官"):
            trend = "增强"
        elif stage in ("死", "墓", "绝", "病"):
            trend = "减弱"
        else:
            trend = "震荡"

        # 多空方向 + 资金验证
        dir_info = _determine_direction(stage, capacity_eff, chg_pct, trend)

        # 封控：死/墓/绝 禁止开新仓
        risk_control = "⚠️ 强制风控" if stage in ("死", "墓", "绝") else "正常运行"

        # 月令共振
        monthly = _monthly_resonance(phys_wx, month_zhi_wx)

        # 事件共振
        event = _event_resonance(phys_wx, policy_wx_list, events_text)

        # 地域加分
        region_gua = _resolve_region(events_text)
        region_wx = BAGUA_WUXING.get(region_gua, "")
        region_score = 0
        region_detail = "—"
        if region_wx and phys_wx:
            rel_r = _wuxing_rel(phys_wx, region_wx)
            if rel_r in ("同气", "a生b"):
                region_score = 5
                region_detail = f"事件地域({region_gua}位{region_wx}) × 品种{phys_wx} → 共振+5"
            else:
                region_detail = f"事件地域({region_gua}位{region_wx}) × 品种{phys_wx} → 中性"

        # 综合评分
        comp = _composite_futures(capacity_eff, is_benqi, monthly, event, dir_info, chg_pct)

        # 有效天数
        if stage in ("帝旺", "临官"):
            valid_days = "3~5个交易日"
        elif stage in ("死", "墓", "绝"):
            valid_days = "1~2个交易日(强风控)"
        else:
            valid_days = "2~3个交易日"

        # 关键分水岭
        if stage in ("帝旺", "临官"):
            watershed = f"跌破前日结算价1.5%即止损"
        elif stage in ("死", "墓", "绝"):
            watershed = f"— 禁止开新仓"
        else:
            watershed = f"参考{rt_price}附近震荡区间"

        if comp["total"] < min_composite:
            continue

        results.append({
            "symbol": sym,
            "name": name,
            "exchange": prod["exchange"],
            "unit": prod["unit"],
            "margin": prod["margin"],
            # 价格
            "price": rt_price if rt_price else None,
            "chg_pct": round(chg_pct, 2),
            "volume": rt_volume,
            "has_rt": has_rt,
            # 日元
            "riyuan_gan": riyuan_gan,
            "riyuan_wx": riyuan_wx,
            "riyuan_ganzhi": riyuan["ganzhi"],
            # 实物五行
            "phys_wx": phys_wx,
            # 本气纯真
            "is_benqi": is_benqi,
            # 承载力
            "stage": stage,
            "capacity": capacity,
            "capacity_eff": capacity_eff if is_benqi else None,
            "expected": expected,
            # 月令
            "monthly_main": monthly["is_main"],
            "monthly_score": round(monthly["score"], 1),
            "monthly_detail": monthly["detail"],
            # 事件
            "event_score": round(event["score"], 1),
            "event_detail": event["detail"],
            # 地域
            "region_score": region_score,
            "region_detail": region_detail,
            # 多空
            "direction": dir_info["direction"],
            "direction_reason": dir_info["reason"],
            "fund_signal": dir_info["fund_signal"],
            "risk_control": risk_control,
            # 综合
            "composite": comp["total"],
            "composite_breakdown": comp["breakdown"],
            # 交易参数
            "watershed": watershed,
            "valid_days": valid_days,
        })

    # ---- 排序 ----
    results.sort(key=lambda x: x["composite"], reverse=True)
    top15 = results[:15]

    # ---- 统计 ----
    diwang = sum(1 for r in results if r["stage"] == "帝旺")
    linguan = sum(1 for r in results if r["stage"] == "临官")
    benqi = sum(1 for r in results if r["is_benqi"])
    long_only = sum(1 for r in results if "只多" in r["direction"] or r["direction"] == "偏多")
    short_only = sum(1 for r in results if "只空" in r["direction"] or r["direction"] == "偏空")
    blocked = sum(1 for r in results if "强制风控" in r["risk_control"])
    monthly_main = sum(1 for r in results if r["monthly_main"])

    print(f"\n   ✅ 扫描完成: {len(results)} 个品种")
    print(f"   帝旺{diwang} 临官{linguan} | 本气纯真{benqi} | 月令主线{monthly_main}")
    print(f"   只多{long_only} 只空{short_only} | 强制风控{blocked}")
    print(f"   🎯 捉妖池 Top 15 已就绪")
    print(f"{'='*60}\n")

    return {
        "target_date": target_date_str,
        "target_ganzhi": target_gz,
        "month_zhi_wx": month_zhi_wx,
        "day_zhi": day_zhi,
        "policy_wx_list": policy_wx_list,
        "policy_text": events_text,
        "total_scanned": len(results),
        "diwang_count": diwang,
        "linguan_count": linguan,
        "benqi_count": benqi,
        "long_count": long_only,
        "short_count": short_only,
        "blocked_count": blocked,
        "monthly_main_count": monthly_main,
        "has_rt": has_rt,
        "results": results,
        "top15": top15,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# 十六、格式化输出
# ============================================================

def format_futures_zhuoyao_report(data: dict) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("🐉  玄捉妖·期货 — 完整扫描报告")
    lines.append("=" * 80)
    lines.append(f"目标交易日: {data['target_date']}")
    lines.append(f"四柱: {data['target_ganzhi'].get('year_ganzhi','')} {data['target_ganzhi'].get('month_ganzhi','')} {data['target_ganzhi'].get('day_ganzhi','')}")
    lines.append(f"月令气场: {data['month_zhi_wx']} | 政策五行: {data['policy_wx_list']}")
    lines.append(f"合格品种: {data['total_scanned']}")
    lines.append(f"帝旺{data['diwang_count']} | 临官{data['linguan_count']} | 本气纯真{data['benqi_count']} | 月令主线{data['monthly_main_count']}")
    lines.append(f"偏多{data['long_count']} | 偏空{data['short_count']} | 强制风控{data['blocked_count']}")
    lines.append("=" * 80)
    lines.append("")

    lines.append("## 🎯 捉妖候选池 TOP 15")
    lines.append("-" * 100)
    header = f"{'排名':<5}{'品种':<10}{'日元':<8}{'实物五行':<6}{'承载力':<10}{'本气':<4}{'月令主线':<8}{'方向':<8}{'风控':<10}{'综合':<6}"
    lines.append(header)
    lines.append("-" * 100)

    for i, r in enumerate(data["top15"], 1):
        benqi_str = "✅纯真" if r["is_benqi"] else "  —"
        main_str = "✅主线" if r["monthly_main"] else "  —"
        lines.append(
            f"{i:<5}{r['name']:<10}{r['riyuan_gan']}({r['riyuan_wx']})  "
            f"{r['phys_wx']:<6}{r['stage']}({r['capacity']})  {benqi_str:<5}"
            f"{main_str:<8}{r['direction']:<8}{r['risk_control'][:8]:<10}{r['composite']:<6}"
        )

    lines.append("-" * 100)
    lines.append(f"\n生成时间: {data['generated_at']}")
    lines.append("⚠️ 以上分析基于五行玄学框架，仅供研究与娱乐，不构成任何投资建议。期货交易风险极高。")
    return "\n".join(lines)


def format_futures_single(r: dict) -> str:
    benqi_note = "⭐ 本气纯真！日元五行==实物五行，承载力翻倍！" if r["is_benqi"] else ""
    eff_note = f" (有效承载力: {r['capacity_eff']})" if r.get("capacity_eff") else ""

    lines = []
    lines.append(f"\n{'─'*60}")
    lines.append(f"🐉 {r['name']}({r['symbol']}) | {r['exchange']}")
    lines.append(f"   合约: {r['unit']} | 保证金: {r['margin']}")
    lines.append(f"   {'实时: ' + str(r['price']) + '元  ' if r['price'] else '价格: N/A'}"
                 f" {'涨跌: ' + str(r['chg_pct']) + '%' if r['chg_pct'] else ''}")
    lines.append(f"   日元: {r['riyuan_gan']}({r['riyuan_wx']}) | 日柱: {r['riyuan_ganzhi']}")
    lines.append(f"   实物五行: {r['phys_wx']}  {benqi_note}")
    lines.append(f"   承载力: {r['stage']} (分:{r['capacity']}){eff_note} | 预期: {r['expected']}")
    lines.append(f"   月令共振: {'⭐主线' if r['monthly_main'] else '—'} | {r['monthly_detail'][:60]}")
    lines.append(f"   事件共振: {r['event_detail'][:60]} ({r['event_score']}/30)")
    lines.append(f"   地域共振: {r['region_detail'][:50]}")
    lines.append(f"   >>> 方向: {r['direction']} | 资金信号: {r['fund_signal']}")
    lines.append(f"   >>> 理由: {r['direction_reason']}")
    lines.append(f"   >>> 分水岭: {r['watershed']} | 有效期: {r['valid_days']}")
    lines.append(f"   >>> 风控: {r['risk_control']}")
    lines.append(f"   综合评分: {r['composite']}/100")
    lines.append(f"{'─'*60}")
    return "\n".join(lines)


# ============================================================
# 独立运行测试
# ============================================================
if __name__ == "__main__":
    test_date = "2026-05-05"
    test_events = [
        "中东地缘冲突持续升级，原油供应紧张",
        "美联储降息预期升温，黄金避险需求增加",
        "川渝地区基建投资加大，螺纹钢玻璃需求增加",
        "全球贸易争端加剧，工业金属异动",
    ]
    data = scan_futures_zhuoyao(test_date, policy_details=test_events)
    print(format_futures_zhuoyao_report(data))
    print("\n--- 详细展开 Top 5 ---")
    for r in data["top15"][:5]:
        print(format_futures_single(r))
