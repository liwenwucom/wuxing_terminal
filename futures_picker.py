# -*- coding: utf-8 -*-
"""
全球期货推荐引擎 v2.0
- 全球期货：CME(原油/黄金/铜/农产品), LME(金属), ICE(软商品), SGX(铁矿石)
- 中国期货：上期所/大商所/郑商所/中金所
- 每只期货给出：买/卖/观望 + 方向理由 + 全球关联分析 + 入场区间 + 止损位
- 每天推荐5只期货
"""

import random
from datetime import datetime

from config import (
    FUTURES_WUXING_MAP, SIMULATE_MODE, WUXING_KE, WUXING_SHENG,
    get_sandiao_quote,
)

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


# ============================================================
# 全球期货品种池
# ============================================================
GLOBAL_FUTURES_POOL = {
    "CME": [
        {"name": "WTI原油", "symbol": "CL", "wuxing": "火", "unit": "1000桶", "exchange": "NYMEX", "active_hours": "几乎24小时"},
        {"name": "布伦特原油", "symbol": "BZ", "wuxing": "火", "unit": "1000桶", "exchange": "ICE", "active_hours": "几乎24小时"},
        {"name": "天然气", "symbol": "NG", "wuxing": "火", "unit": "10000MMBtu", "exchange": "NYMEX", "active_hours": "几乎24小时"},
        {"name": "黄金", "symbol": "GC", "wuxing": "金", "unit": "100盎司", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "白银", "symbol": "SI", "wuxing": "金", "unit": "5000盎司", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "铜", "symbol": "HG", "wuxing": "金", "unit": "25000磅", "exchange": "COMEX", "active_hours": "几乎24小时"},
        {"name": "大豆", "symbol": "ZS", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "玉米", "symbol": "ZC", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "小麦", "symbol": "ZW", "wuxing": "木", "unit": "5000蒲式耳", "exchange": "CBOT", "active_hours": "日盘+夜盘"},
        {"name": "棉花", "symbol": "CT", "wuxing": "木", "unit": "50000磅", "exchange": "ICE", "active_hours": "日盘"},
        {"name": "糖", "symbol": "SB", "wuxing": "木", "unit": "112000磅", "exchange": "ICE", "active_hours": "日盘"},
        {"name": "咖啡", "symbol": "KC", "wuxing": "木", "unit": "37500磅", "exchange": "ICE", "active_hours": "日盘"},
    ],
    "LME": [
        {"name": "LME铜", "symbol": "CA", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
        {"name": "LME铝", "symbol": "AH", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
        {"name": "LME镍", "symbol": "NI", "wuxing": "金", "unit": "6吨", "exchange": "LME"},
        {"name": "LME锌", "symbol": "ZS", "wuxing": "金", "unit": "25吨", "exchange": "LME"},
    ],
}

CHINA_FUTURES_POOL = {
    "上期所": [
        {"name": "沪金", "symbol": "AU", "wuxing": "金", "unit": "1000克/手", "margin": "约4万/手"},
        {"name": "沪银", "symbol": "AG", "wuxing": "金", "unit": "15千克/手", "margin": "约1万/手"},
        {"name": "沪铜", "symbol": "CU", "wuxing": "金", "unit": "5吨/手", "margin": "约3.5万/手"},
        {"name": "国际铜", "symbol": "BC", "wuxing": "金", "unit": "5吨/手", "margin": "约2万/手"},
        {"name": "沪铝", "symbol": "AL", "wuxing": "金", "unit": "5吨/手", "margin": "约8000/手"},
        {"name": "沪锌", "symbol": "ZN", "wuxing": "金", "unit": "5吨/手", "margin": "约1.2万/手"},
        {"name": "沪铅", "symbol": "PB", "wuxing": "金", "unit": "5吨/手", "margin": "约8000/手"},
        {"name": "沪镍", "symbol": "NI", "wuxing": "金", "unit": "1吨/手", "margin": "约2万/手"},
        {"name": "沪锡", "symbol": "SN", "wuxing": "金", "unit": "1吨/手", "margin": "约3万/手"},
        {"name": "螺纹钢", "symbol": "RB", "wuxing": "金", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "热卷", "symbol": "HC", "wuxing": "金", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "线材", "symbol": "WR", "wuxing": "金", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "不锈钢", "symbol": "SS", "wuxing": "金", "unit": "5吨/手", "margin": "约7000/手"},
        {"name": "原油", "symbol": "SC", "wuxing": "火", "unit": "1000桶/手", "margin": "约6万/手"},
        {"name": "燃料油", "symbol": "FU", "wuxing": "火", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "低硫燃油", "symbol": "LU", "wuxing": "火", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "沥青", "symbol": "BU", "wuxing": "火", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "橡胶", "symbol": "RU", "wuxing": "土", "unit": "10吨/手", "margin": "约1.2万/手"},
        {"name": "20号胶", "symbol": "NR", "wuxing": "土", "unit": "10吨/手", "margin": "约1万/手"},
        {"name": "纸浆", "symbol": "SP", "wuxing": "土", "unit": "10吨/手", "margin": "约5000/手"},
    ],
    "能源中心": [
        {"name": "集运指数(欧线)", "symbol": "EC", "wuxing": "水", "unit": "指数点×50元", "margin": "约2万/手"},
    ],
    "大商所": [
        {"name": "铁矿石", "symbol": "I", "wuxing": "金", "unit": "100吨/手", "margin": "约1万/手"},
        {"name": "焦炭", "symbol": "J", "wuxing": "火", "unit": "100吨/手", "margin": "约3万/手"},
        {"name": "焦煤", "symbol": "JM", "wuxing": "火", "unit": "60吨/手", "margin": "约1.5万/手"},
        {"name": "豆粕", "symbol": "M", "wuxing": "木", "unit": "10吨/手", "margin": "约2500/手"},
        {"name": "豆一", "symbol": "A", "wuxing": "木", "unit": "10吨/手", "margin": "约3500/手"},
        {"name": "豆二", "symbol": "B", "wuxing": "木", "unit": "10吨/手", "margin": "约2500/手"},
        {"name": "豆油", "symbol": "Y", "wuxing": "木", "unit": "10吨/手", "margin": "约5000/手"},
        {"name": "棕榈油", "symbol": "P", "wuxing": "木", "unit": "10吨/手", "margin": "约6000/手"},
        {"name": "玉米", "symbol": "C", "wuxing": "木", "unit": "10吨/手", "margin": "约1500/手"},
        {"name": "玉米淀粉", "symbol": "CS", "wuxing": "木", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "生猪", "symbol": "LH", "wuxing": "水", "unit": "16吨/手", "margin": "约4万/手"},
        {"name": "鸡蛋", "symbol": "JD", "wuxing": "水", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "塑料(LDPE)", "symbol": "L", "wuxing": "土", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "PVC", "symbol": "V", "wuxing": "土", "unit": "5吨/手", "margin": "约3000/手"},
        {"name": "聚丙烯", "symbol": "PP", "wuxing": "土", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "苯乙烯", "symbol": "EB", "wuxing": "土", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "乙二醇", "symbol": "EG", "wuxing": "火", "unit": "10吨/手", "margin": "约3000/手"},
        {"name": "LPG", "symbol": "PG", "wuxing": "火", "unit": "20吨/手", "margin": "约8000/手"},
    ],
    "郑商所": [
        {"name": "PTA", "symbol": "TA", "wuxing": "火", "unit": "5吨/手", "margin": "约2000/手"},
        {"name": "短纤", "symbol": "PF", "wuxing": "火", "unit": "5吨/手", "margin": "约2500/手"},
        {"name": "甲醇", "symbol": "MA", "wuxing": "土", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "纯碱", "symbol": "SA", "wuxing": "土", "unit": "20吨/手", "margin": "约4000/手"},
        {"name": "尿素", "symbol": "UR", "wuxing": "土", "unit": "20吨/手", "margin": "约4000/手"},
        {"name": "玻璃", "symbol": "FG", "wuxing": "土", "unit": "20吨/手", "margin": "约3500/手"},
        {"name": "锰硅", "symbol": "SM", "wuxing": "土", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "硅铁", "symbol": "SF", "wuxing": "土", "unit": "5吨/手", "margin": "约3500/手"},
        {"name": "白糖", "symbol": "SR", "wuxing": "木", "unit": "10吨/手", "margin": "约4000/手"},
        {"name": "棉花", "symbol": "CF", "wuxing": "木", "unit": "5吨/手", "margin": "约5000/手"},
        {"name": "苹果", "symbol": "AP", "wuxing": "水", "unit": "10吨/手", "margin": "约6000/手"},
        {"name": "红枣", "symbol": "CJ", "wuxing": "水", "unit": "5吨/手", "margin": "约5000/手"},
        {"name": "花生", "symbol": "PK", "wuxing": "水", "unit": "5吨/手", "margin": "约4000/手"},
        {"name": "菜油", "symbol": "OI", "wuxing": "木", "unit": "10吨/手", "margin": "约5000/手"},
        {"name": "菜粕", "symbol": "RM", "wuxing": "木", "unit": "10吨/手", "margin": "约2000/手"},
        {"name": "强麦", "symbol": "WH", "wuxing": "木", "unit": "20吨/手", "margin": "约5000/手"},
    ],
    "广期所": [
        {"name": "碳酸锂", "symbol": "LC", "wuxing": "火", "unit": "1吨/手", "margin": "约1.5万/手"},
        {"name": "工业硅", "symbol": "SI", "wuxing": "火", "unit": "5吨/手", "margin": "约5000/手"},
    ],
    "中金所": [
        {"name": "沪深300股指", "symbol": "IF", "wuxing": "土", "unit": "指数点×300元", "margin": "约12万/手"},
        {"name": "中证500股指", "symbol": "IC", "wuxing": "土", "unit": "指数点×200元", "margin": "约14万/手"},
        {"name": "中证1000股指", "symbol": "IM", "wuxing": "土", "unit": "指数点×200元", "margin": "约11万/手"},
        {"name": "上证50股指", "symbol": "IH", "wuxing": "土", "unit": "指数点×300元", "margin": "约9万/手"},
        {"name": "10年期国债", "symbol": "T", "wuxing": "土", "unit": "面值100万元", "margin": "约2万/手"},
    ],
    "郑商所补充": [
        {"name": "烧碱", "symbol": "SH", "wuxing": "火", "unit": "30吨/手", "margin": "约5000/手"},
        {"name": "普麦", "symbol": "PM", "wuxing": "木", "unit": "20吨/手", "margin": "约5000/手"},
    ],
}


# ============================================================
# 期货品种上市日期映射（用于八字日元推算）
# ============================================================
FUTURES_IPO_DATE_MAP = {
    "AU": "2008-01-09",  # 沪金
    "AG": "2012-05-10",  # 沪银
    "CU": "1993-11-23",  # 沪铜
    "BC": "2020-11-19",  # 国际铜
    "AL": "1993-11-23",  # 沪铝
    "ZN": "2007-03-26",  # 沪锌
    "PB": "2011-03-24",  # 沪铅
    "NI": "2015-03-27",  # 沪镍
    "SN": "2015-03-27",  # 沪锡
    "RB": "2009-03-27",  # 螺纹钢
    "HC": "2014-03-21",  # 热卷
    "WR": "2009-03-27",  # 线材
    "SS": "2019-09-25",  # 不锈钢
    "I": "2013-10-18",   # 铁矿石
    "SC": "2018-03-26",  # 原油
    "FU": "2004-08-25",  # 燃料油
    "LU": "2020-06-22",  # 低硫燃油
    "BU": "2013-10-09",  # 沥青
    "J": "2011-04-15",   # 焦炭
    "JM": "2013-03-22",  # 焦煤
    "M": "2000-07-17",   # 豆粕
    "A": "2002-03-15",   # 豆一
    "B": "2004-12-22",   # 豆二
    "Y": "2006-01-09",   # 豆油
    "P": "2007-10-29",   # 棕榈油
    "C": "2004-09-22",   # 玉米
    "CS": "2014-12-19",  # 玉米淀粉
    "LH": "2021-01-08",  # 生猪
    "JD": "2013-11-08",  # 鸡蛋
    "L": "2007-07-31",   # 塑料
    "V": "2009-05-25",   # PVC
    "PP": "2014-02-28",  # 聚丙烯
    "EB": "2019-09-26",  # 苯乙烯
    "EG": "2018-12-10",  # 乙二醇
    "PG": "2020-03-30",  # LPG
    "TA": "2006-12-18",  # PTA
    "PF": "2020-10-12",  # 短纤
    "MA": "2011-10-28",  # 甲醇
    "SA": "2019-12-06",  # 纯碱
    "UR": "2019-08-09",  # 尿素
    "FG": "2012-12-03",  # 玻璃
    "SM": "2014-08-08",  # 锰硅
    "SF": "2014-08-08",  # 硅铁
    "SR": "2006-01-06",  # 白糖
    "CF": "2004-06-01",  # 棉花
    "AP": "2017-12-22",  # 苹果
    "CJ": "2019-04-30",  # 红枣
    "PK": "2021-02-01",  # 花生
    "OI": "2007-06-08",  # 菜油
    "RM": "2012-12-28",  # 菜粕
    "WH": "2003-03-28",  # 强麦
    "RU": "1993-11-23",  # 橡胶
    "NR": "2019-08-12",  # 20号胶
    "SP": "2018-11-27",  # 纸浆
    "EC": "2023-08-18",  # 集运指数
    "LC": "2023-07-21",  # 碳酸锂
    "SI": "2022-12-22",  # 工业硅
    "IF": "2010-04-16",  # 沪深300股指
    "IC": "2015-04-16",  # 中证500股指
    "IM": "2022-07-22",  # 中证1000股指
    "IH": "2015-04-16",  # 上证50股指
    "T":  "2015-03-20",  # 10年期国债期货
    "SH": "2023-09-15",  # 烧碱
    "PM": "2003-03-28",  # 普麦
}


# ============================================================
# 专业期货推荐知识库（水洲）
# F1-F10: 长期配置方向 | T1-T10: 短期交易方向
# ============================================================
PRO_FUTURES_LONG = [
    {"id": "F1", "name": "黄金(AU)", "direction": "偏多", "confidence": 85,
     "driver": "全球央行购金+降息周期+去美元化+地缘避险长周期化",
     "strategy": "逢低买入长期持有，重大回调(30日均线下3-5%)时加仓", "window": "12个月+",
     "symbol": "AU"},
    {"id": "F2", "name": "铜(CU)", "direction": "偏多", "confidence": 80,
     "driver": "新能源基建+AI算力中心耗铜+矿山资本开支不足+六张网电网建设",
     "strategy": "长期底仓持有，利用期权对冲短期回调", "window": "12个月+",
     "symbol": "CU"},
    {"id": "F3", "name": "原油(SC)", "direction": "中性偏多", "confidence": 55,
     "driver": "OPEC+供给侧管理+中东地缘政治溢价+中国需求稳健",
     "strategy": "区间震荡思路，不宜追高，可用看涨期权作价差", "window": "3-9个月",
     "symbol": "SC"},
    {"id": "F4", "name": "碳酸锂(LC)", "direction": "偏空", "confidence": 75,
     "driver": "产能持续释放+新能源车增速放缓+库存高企，价格中枢仍有下移压力",
     "strategy": "反弹逢高建立空头头寸，注意资金管理防逼仓", "window": "6个月+",
     "symbol": "LC"},
    {"id": "F5", "name": "工业硅(SI)", "direction": "偏空", "confidence": 70,
     "driver": "多晶硅光伏产能过剩持续，开工率低迷，供需格局恶化",
     "strategy": "偏空配置为主，可卖出虚值看涨期权赚时间价值", "window": "6个月+",
     "symbol": "SI"},
    {"id": "F6", "name": "生猪(LH)", "direction": "偏多", "confidence": 78,
     "driver": "能繁母猪去化传导至供给减量+肉牛缺口扩大，猪周期上行确定性高",
     "strategy": "分批建立期货多单或卖出虚值看跌期权", "window": "6-12个月",
     "symbol": "LH"},
    {"id": "F7", "name": "豆粕(M)", "direction": "区间偏多", "confidence": 55,
     "driver": "中美贸易不确定+南美供应炒作+国内饲料需求刚性",
     "strategy": "在重要技术支撑位(年线附近)布局多单", "window": "3-6个月",
     "symbol": "M"},
    {"id": "F8", "name": "螺纹/热卷(RB/HC)", "direction": "偏空", "confidence": 72,
     "driver": "房地产新开工持续向下+基建边际拉动有限，黑色系总体承压",
     "strategy": "逢高建立空头头寸，不宜左侧抄底", "window": "6-12个月",
     "symbol": "RB"},
    {"id": "F9", "name": "白银(AG)", "direction": "偏多", "confidence": 80,
     "driver": "工业需求(光伏银浆+新能源触点)+贵金属属性双重加持，金银比修复空间",
     "strategy": "长期多单，弹性>黄金但波动更大", "window": "12个月+",
     "symbol": "AG"},
    {"id": "F10", "name": "白糖(SR)", "direction": "区间偏空", "confidence": 58,
     "driver": "巴西+印度丰产预期+原糖高位回落+国内替代甜味剂渗透",
     "strategy": "反弹时寻找空头配置机会", "window": "3-6个月",
     "symbol": "SR"},
]

PRO_FUTURES_SHORT = [
    {"id": "T1", "name": "铁矿石(I)", "direction": "逢高放空", "confidence": 68,
     "driver": "环保限产+粗钢平控政策+港口库存累积", "window": "2026年5-7月",
     "symbol": "I"},
    {"id": "T2", "name": "纯碱(SA)", "direction": "震荡偏空", "confidence": 65,
     "driver": "玻璃企业开工下行+光伏玻璃库存高+检修结束供给放量",
     "strategy": "推荐看跌期权组合", "window": "2026年5-8月",
     "symbol": "SA"},
    {"id": "T3", "name": "焦煤(JM)", "direction": "逢高放空", "confidence": 62,
     "driver": "黑色系整体承压，双焦基本面弱于成材", "window": "2026年5-7月",
     "symbol": "JM"},
    {"id": "T4", "name": "PTA(TA)", "direction": "区间高抛低吸", "confidence": 50,
     "driver": "原油成本端有地缘溢价+聚酯需求平淡", "window": "2026年5-7月",
     "symbol": "TA"},
    {"id": "T5", "name": "甲醇(MA)", "direction": "窄幅震荡", "confidence": 45,
     "driver": "下游MTO利润受压制+进口到港量抬升", "window": "2026年5-6月",
     "symbol": "MA"},
    {"id": "T6", "name": "橡胶(RU)", "direction": "逢低做多", "confidence": 70,
     "driver": "海外产区天气不利+轮胎开工提升+汽车以旧换新加码",
     "strategy": "14500附近构建波段多单", "window": "2026年5-9月",
     "symbol": "RU"},
    {"id": "T7", "name": "苹果(AP)", "direction": "季节性偏多", "confidence": 55,
     "driver": "新季开花期天气炒作+交割标准严格", "window": "2026年5-6月",
     "symbol": "AP"},
    {"id": "T8", "name": "燃料油(FU)", "direction": "跟随原油波段", "confidence": 50,
     "driver": "中东发电旺季+高硫基本面相对强于低硫", "window": "2026年5-8月",
     "symbol": "FU"},
    {"id": "T9", "name": "鸡蛋(JD)", "direction": "季节性偏空", "confidence": 58,
     "driver": "梅雨季储存运输困难+产蛋率回升+端午后需求回落", "window": "2026年5-6月",
     "symbol": "JD"},
    {"id": "T10", "name": "锡(SN)", "direction": "逢低布局多单", "confidence": 65,
     "driver": "AI服务器+光伏焊料需求+缅甸佤邦复产低于预期", "window": "2026年5-10月",
     "symbol": "SN"},
]


# ============================================================
# 期货品种搜索索引（中文名→符号，支持模糊匹配）
# ============================================================
def build_futures_search_index():
    """构建 符号/中文名/拼音 等多维度搜索索引"""
    index = {}
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            sym = c["symbol"]
            name = c["name"]
            wuxing = c["wuxing"]
            # 核心key: 符号
            index[sym.upper()] = {"symbol": sym, "name": name, "wuxing": wuxing, "exchange": exchange}
            index[sym.lower()] = {"symbol": sym, "name": name, "wuxing": wuxing, "exchange": exchange}
            # 中文名（全称/简称）
            index[name] = {"symbol": sym, "name": name, "wuxing": wuxing, "exchange": exchange}
            # 别名
            aliases = {
                "黄金": "AU", "白银": "AG", "铜": "CU", "国际铜": "BC",
                "铝": "AL", "锌": "ZN", "铅": "PB", "镍": "NI", "锡": "SN",
                "螺纹": "RB", "螺纹钢": "RB", "热卷": "HC", "线材": "WR",
                "不锈钢": "SS", "铁矿石": "I", "铁矿": "I",
                "原油": "SC", "燃油": "FU", "燃料油": "FU", "低硫燃油": "LU",
                "沥青": "BU", "橡胶": "RU", "20号胶": "NR", "纸浆": "SP",
                "集运": "EC", "欧线": "EC", "集运指数": "EC",
                "焦炭": "J", "焦煤": "JM", "豆粕": "M", "豆一": "A",
                "豆二": "B", "豆油": "Y", "棕榈油": "P", "棕榈": "P",
                "玉米": "C", "淀粉": "CS", "玉米淀粉": "CS",
                "生猪": "LH", "鸡蛋": "JD", "塑料": "L", "PVC": "V",
                "聚丙烯": "PP", "苯乙烯": "EB", "乙二醇": "EG",
                "PTA": "TA", "短纤": "PF", "甲醇": "MA",
                "纯碱": "SA", "尿素": "UR", "玻璃": "FG",
                "锰硅": "SM", "硅铁": "SF", "白糖": "SR",
                "棉花": "CF", "苹果": "AP", "红枣": "CJ",
                "花生": "PK", "菜油": "OI", "菜粕": "RM",
                "强麦": "WH", "碳酸锂": "LC", "工业硅": "SI",
                "LPG": "PG", "液化气": "PG",
                "股指": "IF", "沪深300": "IF", "IF": "IF",
                "中证500": "IC", "中证1000": "IM", "上证50": "IH",
                "国债": "T", "十年国债": "T", "10年国债": "T",
                "烧碱": "SH", "普麦": "PM",
            }
            for alias, alias_sym in aliases.items():
                if alias_sym == sym:
                    index[alias] = {"symbol": sym, "name": name, "wuxing": wuxing, "exchange": exchange}
                    index[alias.upper()] = {"symbol": sym, "name": name, "wuxing": wuxing, "exchange": exchange}
    return index


FUTURES_SEARCH_INDEX = build_futures_search_index()


def search_futures(query):
    """模糊搜索期货品种，返回匹配列表"""
    query = query.strip()
    if not query:
        return []
    results = []
    query_lower = query.lower()
    # 精确匹配
    if query in FUTURES_SEARCH_INDEX:
        return [FUTURES_SEARCH_INDEX[query]]
    # 前缀匹配
    for key, info in FUTURES_SEARCH_INDEX.items():
        if key.lower().startswith(query_lower) or query_lower in key.lower():
            if info not in results:
                results.append(info)
        if len(results) >= 10:
            break
    return results[:10]


# ============================================================
# 期货品种的基础五行映射（八字选股扩展）
# ============================================================
FUTURES_BAZI_BASE = {
    "AU": {
        "name": "黄金(AU)", "base_wuxing": "纯金", "riyuan_ref": "庚金",
        "twelve_stage_hint": {
            "沐浴": "庚金遇午(沐浴)可震荡横盘，趋势不明朗",
            "帝旺": "庚金遇酉(帝旺)突破形态确认，主升浪概率大",
            "死": "庚金遇子(死)空头主导，不宜做多",
            "病": "庚金遇亥(病)动能衰减，多单需减仓",
        },
        "option_suitable": ["沪金期权"],
    },
    "CU": {
        "name": "铜(CU)", "base_wuxing": "金+火(火炼成器)", "riyuan_ref": "与股指同类",
        "twelve_stage_hint": {
            "临官": "金临官于申，铜价中枢抬升，适合趋势多",
            "帝旺": "金帝旺于酉，铜博士突破信号确认",
            "衰": "金衰于戌，铜价高位震荡，不宜追多",
        },
        "option_suitable": ["沪铜期权"],
    },
    "RB": {
        "name": "螺纹钢(RB)", "base_wuxing": "土金交界(土生金)", "riyuan_ref": "与基建/地产板块同论",
        "twelve_stage_hint": {
            "长生": "土长生于申(土金交界)，基建政策催化→多头信号",
            "冠带": "土冠带于戌(火库)，煤焦联动螺纹偏强",
            "病": "土病于寅(木克土)，地产数据走弱时螺纹承压",
        },
        "option_suitable": ["螺纹钢期权"],
    },
    "SC": {
        "name": "原油(SC)", "base_wuxing": "火", "riyuan_ref": "丙火",
        "twelve_stage_hint": {
            "帝旺": "丙火帝旺于午，油价情绪高点，波动率放大",
            "死": "丙火死于酉(金旺)，OPEC+增产压制多头",
        },
        "option_suitable": ["原油期权"],
    },
    "AG": {
        "name": "白银(AG)", "base_wuxing": "金", "riyuan_ref": "庚金/辛金",
        "twelve_stage_hint": {
            "帝旺": "金帝旺于酉，银价跟涨黄金+工业需求共振",
            "沐浴": "金沐浴于午，震荡但方向偏多",
        },
        "option_suitable": ["沪银期权"],
    },
}

# ============================================================
# 双向期权策略结构（八字选股扩展 → 映射十二长生）
# ============================================================
OPTION_STRATEGY_TABLE = [
    {
        "strategy": "买入看涨期权",
        "condition": "帝旺/临官 + 天时相生 + 量价齐生",
        "detail": "买看涨不超总资金10%，博方向性突破收益",
        "risk_note": "时间价值衰减快，需在预期突破窗口内布局",
        "stages": ["帝旺", "临官"],
    },
    {
        "strategy": "牛市看涨价差",
        "condition": "帝旺/临官但短期有回调空间预判",
        "detail": "买入低行权价Call + 卖出高行权价Call，降低长仓期权成本",
        "risk_note": "上行空间被锁定，适合温和看涨而非爆发式行情",
        "stages": ["帝旺", "临官", "冠带"],
    },
    {
        "strategy": "卖出宽跨式",
        "condition": "震荡横盘预判（沐浴/冠带/衰等中性阶段）",
        "detail": "同时卖出虚值Call和虚值Put，赚取时间价值",
        "risk_note": "需防跳空风险！重大事件前必须平仓或收紧行权价间距",
        "stages": ["沐浴", "冠带", "衰", "胎", "养"],
    },
    {
        "strategy": "熊市看跌价差组合",
        "condition": "死/衰/病承载力弱的品种",
        "detail": "买入高行权价Put + 卖出低行权价Put，做保护性下跌",
        "risk_note": "若市场快速反弹可能亏损，设好止损纪律",
        "stages": ["死", "病", "衰", "墓", "绝"],
    },
]


def get_option_strategy_for_stage(chang_sheng_stage):
    """根据十二长生阶段返回推荐期权策略"""
    strategies = []
    for s in OPTION_STRATEGY_TABLE:
        if chang_sheng_stage in s["stages"]:
            strategies.append(s)
    return strategies


def get_futures_bazi_info(symbol):
    """获取期货品种的八字基础信息"""
    return FUTURES_BAZI_BASE.get(symbol, None)


# ============================================================
# 期权买权 vs 卖权策略选择矩阵（八字选期货/期权版）
# ============================================================
OPTION_BUYER_SELLER_MATRIX = [
    {
        "level": "★★★★★ 极强",
        "stages": ["帝旺", "临官"],
        "buyer_strategy": "买入看涨期权 (Long Call)",
        "seller_strategy": "不优先推荐做卖方",
        "logic": "资金持续流入，买看涨的杠杆效率最优，保护效果好",
        "risk_note": "时间价值衰减快，需在预期突破窗口内布局",
    },
    {
        "level": "★★★★☆ 较强",
        "stages": ["冠带", "沐浴"],
        "buyer_strategy": "牛市看涨价差 / 买入看涨",
        "seller_strategy": "期权略贵时可卖出虚值看跌 (Short OTM Put)",
        "logic": "买方为主，卖方为辅；牛市价差降低权利金成本",
        "risk_note": "若核心标的震荡未暴涨，卖方虚值Put安全性高",
    },
    {
        "level": "★★★☆☆ 中等",
        "stages": ["长生"],
        "buyer_strategy": "不建议积极参与买方",
        "seller_strategy": "备兑开仓 / 卖出宽跨式 (Short Strangle)",
        "logic": "行情无明确趋势，双卖赚取时间价值性价比高",
        "risk_note": "赚取Theta为主，需防跳空风险",
    },
    {
        "level": "★★☆☆☆ 较弱",
        "stages": ["衰", "病"],
        "buyer_strategy": "买入看跌期权 — 强烈推荐 (Long Put)",
        "seller_strategy": "不做卖方",
        "logic": "下跌可能性大，买看跌的性价比极高",
        "risk_note": "权利金成本需控制，建议价差结构降成本",
    },
    {
        "level": "★☆☆☆☆ 极弱",
        "stages": ["死", "墓", "绝", "胎", "养"],
        "buyer_strategy": "买入看跌期权 (Long Put)",
        "seller_strategy": "坚决不做卖方",
        "logic": "跳空暴跌风险极高，极弱日为买方时机，做卖方风险极大",
        "risk_note": "波动率可能升高，买Put时注意IV高低选择行权价",
    },
]


def get_option_buyer_seller_for_stage(chang_sheng_stage):
    """根据十二长生阶段返回期权买/卖策略"""
    for m in OPTION_BUYER_SELLER_MATRIX:
        if chang_sheng_stage in m["stages"]:
            return m
    return None


# ============================================================
# 期货品种券商人气数据（联网扫盘版）
# 模拟：近一周券商金股推荐次数统计
# ============================================================
FUTURES_BROKER_POPULARITY = {
    "AU": {"name": "黄金", "count": 6, "brokers": "中信/国泰/华泰/海通/广发/银河"},
    "SC": {"name": "原油", "count": 5, "brokers": "中信/国泰/华泰/招商/申万"},
    "CU": {"name": "沪铜", "count": 4, "brokers": "中信/国泰/海通/广发"},
    "RB": {"name": "螺纹钢", "count": 4, "brokers": "中信/华泰/国泰/银河"},
    "I":  {"name": "铁矿石", "count": 3, "brokers": "中信/华泰/国泰"},
    "M":  {"name": "豆粕", "count": 3, "brokers": "中信/国泰/华泰"},
    "SA": {"name": "纯碱", "count": 3, "brokers": "华泰/中信/国泰"},
    "AG": {"name": "沪银", "count": 2, "brokers": "中信/国泰"},
    "TA": {"name": "PTA", "count": 2, "brokers": "华泰/中信"},
    "J":  {"name": "焦炭", "count": 2, "brokers": "中信/国泰"},
    "JM": {"name": "焦煤", "count": 2, "brokers": "中信/国泰"},
    "FG": {"name": "玻璃", "count": 2, "brokers": "华泰/中信"},
    "IF": {"name": "沪深300股指", "count": 5, "brokers": "中信/国泰/华泰/海通/广发"},
    "T":  {"name": "10年国债", "count": 3, "brokers": "中信/国泰/华泰"},
}

# 最大人气数（用于归一化）
MAX_FUTURES_POPULARITY = max(
    (v["count"] for v in FUTURES_BROKER_POPULARITY.values()), default=10
)


def get_futures_popularity(symbol):
    """获取期货品种的券商推荐人气（0-1归一化）"""
    info = FUTURES_BROKER_POPULARITY.get(symbol)
    if info:
        return info["count"] / MAX_FUTURES_POPULARITY
    return 0.0


def get_futures_stage_hint(symbol, chang_sheng_stage):
    """获取期货在特定十二长生阶段的操作提示"""
    info = FUTURES_BAZI_BASE.get(symbol)
    if info and chang_sheng_stage in info.get("twelve_stage_hint", {}):
        return info["twelve_stage_hint"][chang_sheng_stage]
    return None


def get_pro_futures_score(symbol):
    """获取专业期货推荐的综合评分"""
    score = 0.0
    direction = None
    for f in PRO_FUTURES_LONG:
        if f["symbol"] == symbol:
            confidence = f["confidence"] / 100.0
            if "偏多" in f["direction"] and "偏空" not in f["direction"]:
                score = confidence * 1.2
                direction = "偏多"
            elif "偏空" in f["direction"]:
                score = -confidence * 1.2
                direction = "偏空"
            return score, direction, f
    for f in PRO_FUTURES_SHORT:
        if f["symbol"] == symbol:
            confidence = f["confidence"] / 100.0
            if "做多" in f["direction"] and "空" not in f["direction"]:
                score = confidence * 0.8
                direction = "偏多"
            elif "空" in f["direction"] or "放空" in f["direction"]:
                score = -confidence * 0.8
                direction = "偏空"
            return score, direction, f
    return 0.0, None, None


# ============================================================
# 买入/抛出判断逻辑
# ============================================================
def _evaluate_direction(wuxing: str, boost_level: str, sentiment: float, region: str) -> dict:
    """综合五行气场+情绪+区域给出买入/卖出判断"""

    # 五行气场评分
    boost_scores = {"增强": 0.8, "当令": 0.6, "中性": 0.3, "轻微削弱": -0.2, "削弱": -0.5}
    boost_score = boost_scores.get(boost_level, 0.0)

    # 综合方向分 = 情绪×0.4 + 五行×0.4 + 区域×0.2
    region_bias = 0.1 if region == "中国" else (-0.05 if region == "美国" else 0.0)
    total = sentiment * 0.4 + boost_score * 0.4 + region_bias * 0.2

    if total > 0.3:
        direction = "买入" if total > 0.5 else "轻仓买入"
        confidence = min(90, int(50 + total * 50))
        entry_signal = "突破前高确认后入场" if total > 0.5 else "回调至支撑位附近轻仓试多"
    elif total < -0.2:
        direction = "卖出" if total < -0.4 else "轻仓卖出"
        confidence = min(90, int(50 + abs(total) * 50))
        entry_signal = "跌破支撑位确认后入场" if total < -0.4 else "反弹至阻力位附近轻仓试空"
    else:
        direction = "观望"
        confidence = 30
        entry_signal = "等待方向明确"

    return {
        "direction": direction,
        "confidence": confidence,
        "entry_signal": entry_signal,
        "total_score": round(total, 3),
    }


def _generate_price_analysis(contract: dict, direction: str) -> dict:
    """生成价格分析（入场区间/止损/目标）"""
    if direction in ("买入", "轻仓买入"):
        entry = "建议回调至5日/10日均线附近分批入场"
        stop_loss = "跌破20日均线或前低2%止损"
        target = "前高附近分批止盈，第二目标看突破前高"
    elif direction in ("卖出", "轻仓卖出"):
        entry = "建议反弹至5日/10日均线附近分批入场"
        stop_loss = "突破20日均线或前高2%止损"
        target = "前低附近分批止盈，第二目标看跌破前低"
    else:
        entry = "暂不入场，等待信号"
        stop_loss = "N/A"
        target = "N/A"

    return {"entry_zone": entry, "stop_loss": stop_loss, "target": target, "risk_reward": "约1:2 ~ 1:3" if direction != "观望" else "N/A"}


# ============================================================
# 核心推荐函数
# ============================================================
def pick_global_futures(news_list: list, max_picks: int = 5) -> list:
    """基于全球新闻筛选推荐期货品种（买入/卖出+理由）"""

    # 汇总新闻中的五行分布和情绪
    wuxing_signals = {}
    for news in news_list:
        wx = news.get("wuxing", "")
        sentiment = news.get("sentiment_score", 0)
        region = news.get("region", "全球")
        event = news.get("event_type", "")

        if wx and wx != "未匹配":
            if wx not in wuxing_signals:
                wuxing_signals[wx] = {"total_sentiment": 0.0, "count": 0, "regions": [], "events": []}
            wuxing_signals[wx]["total_sentiment"] += sentiment
            wuxing_signals[wx]["count"] += 1
            wuxing_signals[wx]["regions"].append(region)
            wuxing_signals[wx]["events"].append(event)

    # 从全局期货池中匹配
    candidates = []
    all_global = []
    for exchange, contracts in GLOBAL_FUTURES_POOL.items():
        all_global.extend(contracts)

    for contract in all_global:
        wx = contract["wuxing"]
        if wx in wuxing_signals:
            sig = wuxing_signals[wx]
            avg_sentiment = sig["total_sentiment"] / sig["count"]
            regions = list(set(sig["regions"]))

            # 分析买入/卖出
            eval_result = _evaluate_direction(wx, "中性", avg_sentiment, regions[0] if regions else "全球")
            price_analysis = _generate_price_analysis(contract, eval_result["direction"])

            # 全球关联逻辑
            global_logic = _build_global_logic(contract, sig["events"], regions, avg_sentiment)

            candidates.append({
                "name": contract["name"],
                "symbol": contract["symbol"],
                "exchange": contract.get("exchange", ""),
                "wuxing": wx,
                "unit": contract.get("unit", ""),
                "direction": eval_result["direction"],
                "confidence": eval_result["confidence"],
                "entry_signal": eval_result["entry_signal"],
                "score": eval_result["total_score"],
                "price_analysis": price_analysis,
                "global_logic": global_logic,
                "sentiment": round(avg_sentiment, 2),
            })

    # 按综合评分排序
    candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    return candidates[:max_picks]


def pick_china_futures(boost_level: str, wuxing: str, news_list: list, max_picks: int = 3) -> list:
    """基于中国新闻+五行气场推荐中国期货品种"""

    # 从五行映射中获取品种
    mapped_contracts = FUTURES_WUXING_MAP.get(wuxing, {}).get("contracts", [])

    candidates = []
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            if c["wuxing"] == wuxing or c["name"] in mapped_contracts:
                sentiment = 0.3 if boost_level in ("增强", "当令") else (-0.3 if "削弱" in boost_level else 0.0)

                eval_result = _evaluate_direction(wuxing, boost_level, sentiment, "中国")
                price_analysis = _generate_price_analysis(c, eval_result["direction"])

                # 中国特色分析
                china_logic = _build_china_logic(c, boost_level, news_list)

                candidates.append({
                    "name": c["name"],
                    "symbol": c["symbol"],
                    "exchange": exchange,
                    "wuxing": wuxing,
                    "unit": c.get("unit", ""),
                    "margin": c.get("margin", ""),
                    "direction": eval_result["direction"],
                    "confidence": eval_result["confidence"],
                    "entry_signal": eval_result["entry_signal"],
                    "score": eval_result["total_score"],
                    "price_analysis": price_analysis,
                    "china_logic": china_logic,
                    "boost": boost_level,
                })

    candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    return candidates[:max_picks]


def pick_china_futures_categorized(news_list: list, dominant_wx: str, boost_level: str) -> dict:
    """纯中国期货推荐：按买入/卖出/回避分类"""

    # 中国期货全池
    all_contracts = []
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            all_contracts.append({**c, "exchange": exchange})

    # 汇总新闻基于每个五行的情绪
    wx_sentiments = {}
    for news in news_list:
        wx = news.get("wuxing", "")
        sentiment = news.get("sentiment_score", 0)
        if wx and wx != "未匹配":
            if wx not in wx_sentiments:
                wx_sentiments[wx] = []
            wx_sentiments[wx].append(sentiment)

    avg_sentiments = {wx: sum(s)/len(s) for wx, s in wx_sentiments.items()} if wx_sentiments else {}

    buy_candidates = []
    sell_candidates = []
    avoid_candidates = []

    for c in all_contracts:
        wx = c["wuxing"]
        symbol = c["symbol"]
        sentiment = avg_sentiments.get(wx, 0.0)
        eval_result = _evaluate_direction(wx, boost_level, sentiment, "中国")
        price_analysis = _generate_price_analysis(c, eval_result["direction"])
        china_logic = _build_china_logic(c, boost_level, news_list)

        pro_score, pro_direction, pro_data = get_pro_futures_score(symbol)
        total_score = eval_result["total_score"] * 0.55 + pro_score * 0.45

        entry = {
            "name": c["name"],
            "symbol": c["symbol"],
            "exchange": c.get("exchange", ""),
            "wuxing": wx,
            "unit": c.get("unit", ""),
            "margin": c.get("margin", ""),
            "direction": eval_result["direction"],
            "confidence": eval_result["confidence"],
            "entry_signal": eval_result["entry_signal"],
            "score": round(total_score, 3),
            "price_analysis": price_analysis,
            "china_logic": china_logic,
            "boost": boost_level,
            "pro_direction": pro_direction,
        }

        direction = eval_result["direction"]
        if direction in ("买入", "轻仓买入"):
            buy_candidates.append(entry)
        elif direction in ("卖出", "轻仓卖出"):
            sell_candidates.append(entry)
        else:
            avoid_candidates.append(entry)

    buy_candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    sell_candidates.sort(key=lambda x: abs(x["score"]), reverse=True)
    avoid_candidates.sort(key=lambda x: abs(x["score"]))

    buy_futures = buy_candidates[:5]
    sell_futures = sell_candidates[:5]
    avoid_futures = avoid_candidates[:5]

    # 如果不够，从其他分组借
    if len(buy_futures) < 3:
        pool = avoid_candidates + sell_candidates
        pool.sort(key=lambda x: x["score"], reverse=True)
        for p in pool:
            if p not in buy_futures:
                p["direction"] = "买入"
                p["entry_signal"] = "经综合评分调整，建议轻仓试多"
                buy_futures.append(p)
                if len(buy_futures) >= 5:
                    break

    if len(sell_futures) < 3:
        pool = avoid_candidates + buy_candidates
        pool.sort(key=lambda x: x["score"])
        for p in pool:
            if p not in sell_futures and p not in buy_futures:
                p["direction"] = "卖出"
                p["entry_signal"] = "经综合评分调整，建议轻仓试空"
                sell_futures.append(p)
                if len(sell_futures) >= 5:
                    break

    total = len(buy_futures) + len(sell_futures) + len(avoid_futures)

    # 期权简要
    options_summary = _build_china_options_summary(buy_futures, sell_futures, boost_level)

    return {
        "buy_futures": buy_futures[:5],
        "sell_futures": sell_futures[:5],
        "avoid_futures": avoid_futures[:5],
        "total_count": total,
        "options_summary": options_summary,
    }


def _build_china_options_summary(buy_futures: list, sell_futures: list, boost_level: str) -> dict:
    """生成中国期权策略摘要"""
    strategies = {
        "增强": "买Call + 牛市价差",
        "当令": "卖Put收租 + 买Call",
        "削弱": "买Put + 熊市价差",
        "轻微削弱": "保护性Put + 铁鹰",
        "中性": "蝶式 + 铁鹰 + 卖跨",
    }
    strategy = strategies.get(boost_level, "观望")

    targets = []
    for f in buy_futures[:2]:
        if "金" in f["name"] or "银" in f["name"] or "铜" in f["name"]:
            targets.append(f"{f['name']}期权 — 买Call，博波动率")
    for f in sell_futures[:2]:
        if "金" in f["name"] or "螺纹" in f["name"] or "铁矿石" in f["name"]:
            targets.append(f"{f['name']}期权 — 买Put，对冲下行")

    return {
        "strategy": strategy,
        "suggested_targets": targets if targets else ["沪金期权", "沪铜期权", "铁矿石期权"],
        "note": "期权跟随标的五行，可用价差组合控制风险",
    }



def _build_global_logic(contract: dict, events: list, regions: list, sentiment: float) -> str:
    """构建全球期货关联逻辑"""
    parts = []
    name = contract["name"]
    wx = contract["wuxing"]

    if events:
        parts.append(f"触发事件：{'、'.join(events[:3])}")
    if regions:
        parts.append(f"影响区域：{'、'.join(set(regions))}")
    if sentiment > 0.3:
        parts.append(f"全球情绪偏多")
    elif sentiment < -0.3:
        parts.append(f"全球情绪偏空")
    else:
        parts.append("情绪中性")

    # 全球关联
    if "原油" in name or "oil" in name.lower():
        parts.append("联动：中东地缘→油价→通胀→美联储政策→美元→全球风险资产")
    elif "gold" in name.lower() or "金" in name:
        parts.append("联动：避险情绪→金价→实际利率→美元指数→央行购金")
    elif "铜" in name or "copper" in name.lower():
        parts.append("联动：全球经济预期→铜博士→制造业PMI→基建投资")
    elif "大豆" in name or "玉米" in name or "小麦" in name:
        parts.append("联动：天气→产量→USDA报告→贸易流→通胀预期")

    return "；".join(parts)


def _build_china_logic(contract: dict, boost_level: str, news_list: list) -> str:
    """构建中国期货特色分析"""
    name = contract["name"]
    wx = contract["wuxing"]

    if boost_level in ("增强", "当令"):
        wx_status = f"五行「{wx}」{boost_level}，周期有利"
    elif "削弱" in boost_level:
        wx_status = f"五行「{wx}」{boost_level}，周期不利"
    else:
        wx_status = f"五行「{wx}」中性"

    # 中国特色
    china_specific = ""
    if "螺纹" in name or "铁矿石" in name:
        china_specific = "国内基建开工率+房地产新开工数据是关键驱动"
    elif "豆粕" in name or "玉米" in name:
        china_specific = "进口依存度高，关注中美贸易和南美天气"
    elif "金" in name or "银" in name:
        china_specific = "人民币汇率影响沪金溢价，央行增持是中长期支撑"
    elif "原油" in name:
        china_specific = "国内需求恢复+OPEC政策，SC与Brent价差反映区域供需"

    return f"{wx_status}。{china_specific}"


# ============================================================
# 主力合约代码映射（2026年5月示例）
# ============================================================
MAIN_CONTRACT_EXAMPLES = {
    "AU": "AU2606", "AG": "AG2606", "CU": "CU2606", "AL": "AL2606",
    "ZN": "ZN2606", "PB": "PB2606", "NI": "NI2606", "SN": "SN2606",
    "RB": "RB2610", "HC": "HC2610", "FU": "FU2607", "BU": "BU2606",
    "RU": "RU2609", "SP": "SP2609", "SS": "SS2606",
    "I":  "I2609",  "JM": "JM2609", "J":  "J2609",
    "A":  "A2609",  "B":  "B2607",  "M":  "M2609",  "Y":  "Y2609",
    "P":  "P2609",  "C":  "C2609",  "CS": "CS2609",
    "JD": "JD2609", "LH": "LH2607",
    "L":  "L2609",  "PP": "PP2609", "V":  "V2609",
    "EG": "EG2609", "EB": "EB2607",
    "CF": "CF2609", "SR": "SR2609", "OI": "OI2609", "RM": "RM2609",
    "AP": "AP2610", "CJ": "CJ2609", "PK": "PK2610",
    "TA": "TA2609", "MA": "MA2609", "FG": "FG2609", "SA": "SA2609",
    "UR": "UR2607", "PF": "PF2607", "SH": "SH2607",
    "WH": "WH2607", "PM": "PM2607",
    "IF": "IF2605", "IC": "IC2605", "IM": "IM2605", "IH": "IH2605",
    "T":  "T2606",
    "SC": "SC2607", "NR": "NR2607", "LU": "LU2607", "BC": "BC2606",
    "EC": "EC2606",
}


def get_main_contract(symbol):
    """获取当前主力合约示例代码"""
    return MAIN_CONTRACT_EXAMPLES.get(symbol, f"{symbol}----")


# ============================================================
# 兼容旧接口
# ============================================================
def pick_futures(wuxing: str, boost_level: str, max_picks: int = 3) -> dict:
    """旧接口兼容：简版期货推荐"""
    contracts = FUTURES_WUXING_MAP.get(wuxing, {}).get("contracts", [])
    direction_map = {"增强": "做多", "当令": "做多", "削弱": "做空", "轻微削弱": "观望偏空", "中性": "观望"}

    picks = []
    for contract_name in contracts[:max_picks]:
        direction = direction_map.get(boost_level, "观望")
        picks.append({
            "name": contract_name,
            "wuxing": wuxing,
            "direction": direction,
            "symbol": contract_name,
            "basis": "实时价" if not SIMULATE_MODE else "模拟价",
            "open_interest": "实时" if not SIMULATE_MODE else "模拟持仓",
        })

    return {
        "futures": picks,
        "base_direction": direction_map.get(boost_level, "观望"),
        "wuxing": wuxing,
        "logic": f"五行「{wuxing}」当前{boost_level}",
    }
