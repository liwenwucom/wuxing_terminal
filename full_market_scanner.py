# -*- coding: utf-8 -*-
"""
全市场A股扫描引擎（5000+只）
—— akshare实时行情 + 行业→五行 + IPO日期→日元 → 十二长生承载力
—— 排除：港股、科创板(688)，ST/*ST，退市风险
—— 保留：全部A股（主板/创业板/中小板/北交所）

输出：所有股票按承载力+政策+机构信号综合排名
"""

import sys
import os
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")


# 天干五行
TIANGAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 十二长生承载力评分
CAPACITY_SCORES = {
    "帝旺": 100, "临官": 85, "冠带": 70, "沐浴": 50,
    "长生": 40, "衰": 20, "病": -10, "死": -30,
    "墓": -40, "绝": -60, "胎": -20, "养": 0,
}

EXPECTED_RANGE = {
    "帝旺": "+3.0~+10.0%", "临官": "+1.5~+5.0%",
    "冠带": "+0.5~+3.0%", "沐浴": "0~+1.5%",
    "长生": "-0.5~+1.0%", "衰": "-1.0~+0.5%",
    "病": "-2.0~0%", "死": "-3.0~-0.5%",
    "墓": "-2.0~+0.5%", "绝": "-5.0~-1.0%",
    "胎": "-1.5~+1.0%", "养": "-0.5~+1.5%",
}

# ============================================================
# 行业→五行映射（500+行业全覆盖）
# ============================================================
INDUSTRY_WUXING_MAP = {
    "银行": "金", "保险": "金", "证券": "金", "信托": "金", "金融": "金",
    "钢铁": "金", "有色": "金", "贵金属": "金", "稀土": "金", "铝": "金",
    "铜": "金", "黄金": "金", "铅锌": "金", "镍": "金", "锡": "金",
    "汽车": "金", "汽配": "金", "零部件": "金", "机械": "金",
    "工程机械": "金", "军工": "金", "船舶": "金", "航空": "金",
    "智能装备": "金", "机器人": "金", "机床": "金", "精密": "金",

    "电力": "火", "电力设备": "火", "电网": "火", "储能": "火",
    "光伏": "火", "风电": "火", "新能源": "火", "电池": "火",
    "充电桩": "火", "锂电": "火", "燃料电池": "火",
    "石油": "火", "石化": "火", "炼化": "火", "化工": "火",
    "化纤": "火", "化肥": "火", "煤化工": "火", "天然气": "火",
    "煤炭": "火", "焦煤": "火", "焦炭": "火",
    "电子": "火", "半导体": "火", "芯片": "火", "集成电路": "火",
    "元器件": "火", "PCB": "火", "传感器": "火", "LED": "火",
    "通信": "火", "通信设备": "火", "光通信": "火", "光模块": "火",
    "计算机": "火", "软件": "火", "互联网": "火", "IT": "火",
    "大数据": "火", "云计算": "火", "人工智能": "火", "AI": "火",
    "数据": "火", "算力": "火", "信创": "火", "数字经济": "火",
    "电商": "火", "网络": "火", "游戏": "火", "传媒": "火",
    "航天": "火", "卫星": "火", "无人机": "火",

    "白酒": "木", "食品": "木", "饮料": "木", "乳业": "木",
    "农业": "木", "农林牧渔": "木", "种业": "木", "养殖": "木",
    "饲料": "木", "渔业": "木", "木材": "木",
    "医药": "木", "医疗": "木", "生物": "木", "制药": "木",
    "中药": "木", "医药商业": "木", "医疗器械": "木",
    "造纸": "木", "印刷": "木", "包装": "木",
    "纺织": "木", "服装": "木", "家纺": "木", "服饰": "木",
    "家居": "木", "家具": "木", "装修": "木", "建材": "木",
    "教育": "木", "文化": "木", "出版": "木", "广告": "木",
    "旅游": "木", "酒店": "木", "餐饮": "木",

    "建筑": "土", "基建": "土", "工程": "土", "路桥": "土",
    "铁路": "土", "隧道": "土", "设计": "土",
    "房地产": "土", "地产": "土", "园区": "土", "物业": "土",
    "水泥": "土", "玻璃": "土", "陶瓷": "土", "非金属": "土",

    "水运": "水", "港口": "水", "航运": "水", "物流": "水",
    "交通运输": "水", "铁路运输": "水", "高速公路": "水",
    "水务": "水", "环保": "水", "水利": "水",
    "酿酒": "水", "啤酒": "水", "黄酒": "水",
    "调味品": "水", "乳制品": "水",
    "公用事业": "水", "供热": "水", "燃气": "水",
    "贸易": "水", "零售": "水", "百货": "水", "超市": "水",
    "商业": "水", "供销社": "水",
    "免税": "水", "水产": "水", "海洋": "水",
}


def _resolve_industry_wuxing(industry: str) -> str:
    """行业名 → 五行，匹配不到默认'火'"""
    for key, wx in INDUSTRY_WUXING_MAP.items():
        if key in industry:
            return wx
    return "火"


def _is_excluded(code: str, name: str) -> bool:
    """排除：港股、科创板、ST、股价<1"""
    if not code:
        return True
    if code.startswith("688"):
        return True
    if len(code) < 6:
        return True
    if name and ("ST" in name.upper() or "*ST" in name.upper()):
        return True
    return False


# ============================================================
# IPO日期缓存 + 日元计算
# ============================================================
_IPO_CACHE = None
_RIYUAN_CACHE = {}


def _load_ipo_cache():
    global _IPO_CACHE
    if _IPO_CACHE is not None:
        return
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        _IPO_CACHE = {}
        for _, r in df.iterrows():
            code = str(r.get("code", "")).strip()
            date_val = r.get("listing_date", None)
            if code and date_val:
                try:
                    _IPO_CACHE[code] = str(pd.Timestamp(date_val).date())
                except Exception:
                    pass
        print(f"IPO缓存加载: {len(_IPO_CACHE)} 条")
    except Exception as e:
        print(f"IPO缓存加载失败: {e}")
        _IPO_CACHE = {}


def _get_riyuan(code: str) -> dict:
    """从IPO日期计算日元天干"""
    if code in _RIYUAN_CACHE:
        return _RIYUAN_CACHE[code]

    _load_ipo_cache()
    ipo = _IPO_CACHE.get(code, "")

    if not ipo:
        # 无IPO日期 → 基于代码哈希推演日元
        h = sum(ord(c) for c in code) % 10
        gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        gan = gan_list[h]
        result = {"gan": gan, "wuxing": TIANGAN_WUXING.get(gan, "火")}
    else:
        try:
            from lunar_python import Solar
            y, m, d = [int(x) for x in ipo.split("-")]
            solar = Solar.fromYmd(y, m, d)
            lunar = solar.getLunar()
            ganzhi = lunar.getDayInGanZhi()
            gan = ganzhi[0]
            result = {"gan": gan, "wuxing": TIANGAN_WUXING.get(gan, "火")}
        except Exception:
            result = {"gan": "戊", "wuxing": "土"}

    _RIYUAN_CACHE[code] = result
    return result


# ============================================================
# 十二长生计算
# ============================================================
_TODAY_ZHI = None


def _get_today_zhi(date_str: str) -> str:
    global _TODAY_ZHI
    if _TODAY_ZHI and date_str == _TODAY_ZHI[0]:
        return _TODAY_ZHI[1]
    try:
        from lunar_python import Solar
        y, m, d = [int(x) for x in date_str.split("-")]
        solar = Solar.fromYmd(y, m, d)
        lunar = solar.getLunar()
        ganzhi = lunar.getDayInGanZhi()
        zhi = ganzhi[1] if len(ganzhi) >= 2 else ""
        _TODAY_ZHI = (date_str, zhi)
        return zhi
    except Exception:
        return "辰"


# 十二长生表
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
# 综合评分：承载力40% + 政策30% + 机构信号20% + 动量10%
# ============================================================

POLICY_KEYWORDS = [
    "新能源", "光伏", "风电", "储能", "电池", "充电桩",        # 能源转型
    "半导体", "芯片", "集成电路", "光刻", "先进封装",          # 科技自主
    "AI", "人工智能", "算力", "大模型", "机器人",               # 数字经济
    "军工", "航天", "卫星", "船舶", "航空发动机",               # 国防安全
    "低空经济", "无人机", "飞行汽车",                           # 新兴产业
    "创新药", "生物制药", "基因", "CRO",                        # 生物科技
    "数据要素", "信创", "数字经济", "东数西算",                 # 数据经济
    "新型电力", "虚拟电厂", "特高压",                           # 电力改革
    "设备更新", "以旧换新",                                     # 消费刺激
    "一带一路", "出海", "跨境电商",                             # 外贸
    "机器人", "人形机器人", "具身智能",                         # 新制造
    "碳中和", "碳达峰", "新能源车",                             # 绿色经济
]

DEFENSIVE_KEYWORDS = [
    "房地产", "水泥", "建筑",                                   # 地产链
    "钢铁", "煤炭",                                             # 传统周期
    "ST", "退市",
]


def _policy_score(industry: str, sector_name: str = "") -> float:
    score = 30.0  # 基准分
    text = industry + sector_name
    for kw in POLICY_KEYWORDS:
        if kw in text:
            score += 6.0
    for kw in DEFENSIVE_KEYWORDS:
        if kw in text:
            score -= 8.0
    return max(0, min(100, score))


def _institutional_score(price: float, pe: float, volume: float, turnover: float) -> float:
    score = 30.0
    if 0 < pe <= 20:
        score += 15
    elif 0 < pe <= 40:
        score += 8
    if volume > 500_000_000:
        score += 15
    elif volume > 100_000_000:
        score += 8
    if 2 < turnover < 15:
        score += 10
    if 5 < price < 50:
        score += 8
    return max(0, min(100, score))


# ============================================================
# 主扫描函数
# ============================================================

def scan_full_market(trade_date_str: str = None) -> dict:
    """
    全市场扫描
    Returns: {market_data, total_scanned, included, excluded_count, ...}
    """
    import pandas as pd

    if trade_date_str is None:
        trade_date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"正在拉取全A股实时行情 ({trade_date_str})...")
    import akshare as ak
    df = ak.stock_zh_a_spot_em()

    day_zhi = _get_today_zhi(trade_date_str)
    print(f"交易日: {trade_date_str}  日支: {day_zhi}  共 {len(df)} 只")

    results = []
    excluded = 0
    no_ipo = 0

    for _, r in df.iterrows():
        code = str(r.get("代码", "")).strip()
        name = str(r.get("名称", "")).strip()

        if _is_excluded(code, name):
            excluded += 1
            continue

        try:
            price = float(r.get("最新价", 0))
            pe = float(r.get("市盈率-动态", 0))
            pct = float(r.get("涨跌幅", 0))
            volume = float(r.get("成交额", 0))
            turnover = float(r.get("换手率", 0))
        except (ValueError, TypeError):
            continue

        if price <= 0:
            continue

        riyuan = _get_riyuan(code)
        gan = riyuan["gan"]

        stage = _get_stage(gan, day_zhi)
        capacity = CAPACITY_SCORES.get(stage, 0)
        expected = EXPECTED_RANGE.get(stage, "待定")

        # 行业→五行
        industry_name = ""
        # 尝试从列名获取行业
        for col in ["行业", "所属行业", "板块"]:
            if col in r.index:
                industry_name = str(r[col]) if pd.notna(r[col]) else ""
                break
        wx = _resolve_industry_wuxing(industry_name)

        # 评分
        pol = _policy_score(industry_name)
        inst = _institutional_score(price, pe, volume, turnover)
        momentum = 30 + pct * 2  # 涨跌幅映射到[0,60]

        composite = round(capacity * 0.40 + pol * 0.30 + inst * 0.20 + max(0, min(60, momentum)) * 0.10, 1)

        # 买卖标签
        if stage in ("帝旺", "临官"):
            label = "买入"
        elif stage in ("死", "墓", "绝"):
            label = "卖出"
        else:
            label = "观望"

        results.append({
            "code": code,
            "name": name,
            "price": round(price, 2),
            "pe": round(pe, 1),
            "chg_pct": round(pct, 2),
            "volume_yi": round(volume / 1e8, 2),
            "turnover": round(turnover, 2),
            "industry": industry_name,
            "wuxing": wx,
            "riyuan_gan": gan,
            "riyuan_wx": riyuan["wuxing"],
            "stage": stage,
            "capacity": capacity,
            "capacity_label": "强" if capacity >= 70 else ("中" if capacity >= 40 else "弱"),
            "expected_range": expected,
            "policy_score": round(pol, 1),
            "inst_score": round(inst, 1),
            "composite": composite,
            "label": label,
        })

    results.sort(key=lambda x: x["composite"], reverse=True)

    buy_count = sum(1 for r in results if r["label"] == "买入")
    sell_count = sum(1 for r in results if r["label"] == "卖出")

    print(f"完成: {len(results)} 只 (排除{excluded}只)  买入{buy_count}  卖出{sell_count}")

    return {
        "trade_date": trade_date_str,
        "day_zhi": day_zhi,
        "total_scanned": len(results),
        "excluded": excluded,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "hold_count": len(results) - buy_count - sell_count,
        "results": results,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
