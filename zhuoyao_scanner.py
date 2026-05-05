# -*- coding: utf-8 -*-
"""
玄捉妖扫描系统 —— 主引擎
========================================
融合玄学五行 + 实时市场数据 + 政策事件共振

核心能力：
  1. 5日窗口扫描（目标日±2天）
  2. 十二长生承载力推演（10天干×12地支全量）
  3. 资金验证：量价齐升 vs 骗炮嫌疑
  4. 主线共振：月令五行 × 政策事件 × 行业五行 × 地域八卦
  5. 综合评分(0-100) → 捉妖候选池 Top 20

数据源：akshare 全A股实时行情（排除688科创板/ST/港股）
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

# 月支 → 当令五行（寅卯木、巳午火、申酉金、亥子水、辰戌丑未土）
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

EXPECTED_RANGE = {
    "帝旺": "+3.0~+10.0%", "临官": "+1.5~+5.0%",
    "冠带": "+0.5~+3.0%", "沐浴": "0~+1.5%",
    "长生": "-0.5~+1.0%", "衰": "-1.0~+0.5%",
    "病": "-2.0~0%", "死": "-3.0~-0.5%",
    "墓": "-2.0~+0.5%", "绝": "-5.0~-1.0%",
    "胎": "-1.5~+1.0%", "养": "-0.5~+1.5%",
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
# 四、行业 → 五行映射
# ============================================================
INDUSTRY_WUXING_MAP = {
    "银行": "金", "保险": "金", "证券": "金", "信托": "金", "金融": "金",
    "钢铁": "金", "有色": "金", "贵金属": "金", "稀土": "金", "铝": "金",
    "铜": "金", "黄金": "金", "铅锌": "金", "镍": "金", "锡": "金",
    "汽车": "金", "汽配": "金", "零部件": "金", "机械": "金",
    "工程机械": "金", "军工": "金", "船舶": "金", "航空": "金",
    "智能装备": "金", "机器人": "金", "机床": "金", "精密": "金",
    "家电": "金",

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
    "林业": "木",

    "建筑": "土", "基建": "土", "工程": "土", "路桥": "土",
    "铁路": "土", "隧道": "土", "设计": "土",
    "房地产": "土", "地产": "土", "园区": "土", "物业": "土",
    "水泥": "土", "玻璃": "土", "陶瓷": "土", "非金属": "土",
    "消费": "土",

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
    for key, wx in INDUSTRY_WUXING_MAP.items():
        if key in industry:
            return wx
    return "火"


# ============================================================
# 五、地域 → 八卦方位 → 五行
# ============================================================
BAGUA_WUXING = {
    "震": "木", "巽": "木",
    "离": "火",
    "坤": "土", "艮": "土",
    "乾": "金", "兑": "金",
    "坎": "水",
}

PROVINCE_BAGUA = {
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

PROVINCE_CACHE = {}


def _resolve_province_bagua_wx(province: str) -> str:
    """省份 → 八卦 → 五行"""
    if not province:
        return ""
    for key, gua in PROVINCE_BAGUA.items():
        if key in province:
            return BAGUA_WUXING.get(gua, "")
    return ""


# ============================================================
# 六、政策事件 → 五行映射
# ============================================================
POLICY_EVENT_WUXING = {
    "贸易战": "金", "关税": "金", "制裁": "金", "出口管制": "金",
    "关税解除": "金", "贸易协议": "金", "反倾销": "金",

    "新能源补贴": "火", "碳中和": "火", "碳达峰": "火", "减排": "火",
    "能源转型": "火", "光伏补贴": "火", "风电补贴": "火",
    "新能源汽车": "火", "充电桩建设": "火", "储能政策": "火",

    "芯片法案": "火", "半导体补贴": "火", "科技自主": "火",
    "大基金": "火", "集成电路": "火", "算力基建": "火",

    "水利工程": "水", "南水北调": "水", "航运政策": "水",
    "港口建设": "水", "海洋经济": "水", "环保督察": "水",

    "基建投资": "土", "房地产调控": "土", "新型城镇化": "土",
    "城中村改造": "土", "保障房": "土", "土地政策": "土",
    "城市更新": "土", "老旧小区改造": "土",

    "乡村振兴": "木", "农业补贴": "木", "种业振兴": "木",
    "医保谈判": "木", "集采": "木", "医药创新": "木",
    "教育改革": "木", "减税降费": "木",

    "一带一路": "金", "出海": "金", "跨境电商": "水",
    "数字货币": "水", "数字人民币": "水",
    "低空经济": "火", "通用航空": "火", "飞行汽车": "火",
    "设备更新": "金", "以旧换新": "木",
    "人工智能": "火", "大模型": "火", "东数西算": "火",
    "国防预算": "金", "军民融合": "金",
    "数据要素": "火", "数据安全": "火",
    "新型电力": "火", "虚拟电厂": "火", "特高压": "火",
}


def _resolve_policy_wuxing(news_text: str) -> list:
    """政策新闻 → 五行标签列表"""
    wuxing_set = set()
    for keyword, wx in POLICY_EVENT_WUXING.items():
        if keyword in news_text:
            wuxing_set.add(wx)
    return list(wuxing_set) if wuxing_set else []


def _get_policy_events(policy_details: list) -> list:
    """结构化政策事件列表 → 五行"""
    events = []
    for item in policy_details:
        if isinstance(item, str):
            events.append(item)
        elif isinstance(item, dict):
            events.append(item.get("title", item.get("event", "")))
    return events


# ============================================================
# 七、五行相生关系
# ============================================================
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _wuxing_rel(a: str, b: str) -> str:
    """a对b的五行关系: '同气'/'相生'/'被生'/'相克'/'被克'/'无'"""
    if not a or not b:
        return "无"
    if a == b:
        return "同气"
    if WUXING_SHENG.get(a) == b:
        return "相生"
    if WUXING_SHENG.get(b) == a:
        return "被生"
    if WUXING_KE.get(a) == b:
        return "相克"
    if WUXING_KE.get(b) == a:
        return "被克"
    return "无"


# ============================================================
# 八、干支计算器（多日支持）
# ============================================================
_GANZHI_CACHE = {}


def _get_day_ganzhi(date_str: str) -> dict:
    """公历日期 → 年柱+月柱+日柱（含天干地支+五行）"""
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
            "year_ganzhi": year_gz,
            "month_ganzhi": month_gz,
            "day_ganzhi": day_gz,
            "year_gan": year_gz[0], "year_zhi": year_gz[1],
            "month_gan": month_gz[0], "month_zhi": month_gz[1],
            "day_gan": day_gz[0], "day_zhi": day_gz[1],
            "day_wuxing": TIANGAN_WUXING.get(day_gz[0], ""),
            "month_wuxing": MONTH_ZHI_WUXING.get(month_gz[1], ""),
        }
        _GANZHI_CACHE[date_str] = result
        return result
    except Exception:
        fallback = {
            "date": date_str, "year_ganzhi": "", "month_ganzhi": "", "day_ganzhi": "",
            "year_gan": "", "year_zhi": "", "month_gan": "", "month_zhi": "",
            "day_gan": "", "day_zhi": "", "day_wuxing": "", "month_wuxing": "",
        }
        _GANZHI_CACHE[date_str] = fallback
        return fallback


def _get_window_dates(target_date_str: str, days_before: int = 2, days_after: int = 2) -> list:
    """生成扫描窗口日期列表 [T-2, T-1, T, T+1, T+2]"""
    parts = [int(x) for x in target_date_str.split("-")]
    base = datetime(*parts)
    dates = []
    for offset in range(-days_before, days_after + 1):
        d = base + timedelta(days=offset)
        dates.append(d.strftime("%Y-%m-%d"))
    return dates


# ============================================================
# 九、IPO缓存 + 日元计算
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
        print(f"[玄捉妖] IPO缓存加载: {len(_IPO_CACHE)} 条")
    except Exception as e:
        print(f"[玄捉妖] IPO缓存加载失败: {e}")
        _IPO_CACHE = {}


def _get_riyuan(code: str) -> dict:
    if code in _RIYUAN_CACHE:
        return _RIYUAN_CACHE[code]

    _load_ipo_cache()
    ipo = _IPO_CACHE.get(code, "")

    if not ipo:
        h = sum(ord(c) for c in code) % 10
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

    _RIYUAN_CACHE[code] = result
    return result


# ============================================================
# 十、排除规则
# ============================================================
def _is_excluded(code: str, name: str) -> bool:
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
# 十一、5日窗口承载力推演 + 资金验证
# ============================================================

def _trace_5day_capacity(riyuan_gan: str, window_dates: list) -> dict:
    """
    对一只股票，推演5日窗口内每天的十二长生状态
    Returns: {date: {stage, capacity, expected}, trend: '增强'/'减弱'/'震荡'}
    """
    days = {}
    capacities = []
    stages_list = []

    for date_str in window_dates:
        gz = _get_day_ganzhi(date_str)
        day_zhi = gz["day_zhi"]
        if not day_zhi:
            continue
        stage = _get_stage(riyuan_gan, day_zhi)
        cap = CAPACITY_SCORES.get(stage, 0)
        exp = EXPECTED_RANGE.get(stage, "待定")
        days[date_str] = {
            "date": date_str,
            "day_zhi": day_zhi,
            "day_ganzhi": gz["day_ganzhi"],
            "stage": stage,
            "capacity": cap,
            "expected_range": exp,
        }
        capacities.append(cap)
        stages_list.append(stage)

    if len(capacities) >= 3:
        first_half = sum(capacities[:2]) / 2 if len(capacities[:2]) == 2 else capacities[0]
        second_half = sum(capacities[-2:]) / 2 if len(capacities[-2:]) == 2 else capacities[-1]
        diff = second_half - first_half
        if diff > 10:
            trend = "增强"
        elif diff < -10:
            trend = "减弱"
        else:
            trend = "震荡"
    else:
        trend = "震荡"

    return {"days": days, "trend": trend, "capacities": capacities, "stages": stages_list}


def _verify_fund(capacity_trend: str, target_date: str, chg_pct: float,
                 prices_5d: list = None) -> dict:
    """
    资金验证：
      - 承载力逐日增强 + 股价涨幅放大 → '符合预期，主力做多'
      - 承载力增强 + 股价滞涨/下跌 → '骗炮嫌疑，资金未入场'
      - 承载力震荡 → '待观察'
      - 承载力减弱 + 股价下跌 → '主力撤退'
    Returns: {status, reason, confidence}
    """
    if capacity_trend == "增强":
        if chg_pct > 1.5:
            return {"status": "符合预期", "reason": "量价齐升，主力真实做多", "confidence": "高"}
        elif chg_pct > 0:
            return {"status": "待观察", "reason": "承载力增强但涨幅有限，需继续跟踪", "confidence": "中"}
        else:
            return {"status": "骗炮嫌疑", "reason": "承载力增强但股价滞涨/下跌，资金未入场", "confidence": "高"}
    elif capacity_trend == "减弱":
        if chg_pct < -1.0:
            return {"status": "主力撤退", "reason": "承载力减弱且股价下跌，短线回避", "confidence": "高"}
        elif chg_pct < 0:
            return {"status": "待观察", "reason": "承载力减弱，股价微跌", "confidence": "中"}
        else:
            return {"status": "待观察", "reason": "承载力减弱但股价未跌，可能有护盘资金", "confidence": "低"}
    else:
        return {"status": "待观察", "reason": "承载力震荡，方向不明确", "confidence": "低"}


# ============================================================
# 十二、主线月令共振评分
# ============================================================

def _monthly_resonance_score(stock_wx: str, month_zhi_wx: str, policy_wx_list: list) -> dict:
    """
    月令共振评分：
      - 月令五行 与 股票行业五行 的关系
      - 政策事件五行 与 股票行业五行 的共振
    Returns: {score: 0-40, level: '主线共振'/'局部共振'/'无共振', detail}
    """
    score = 10  # 基准分
    details = []
    level = "无共振"
    resonances = []

    # 月令对股票行业的生克
    if month_zhi_wx and stock_wx:
        rel = _wuxing_rel(month_zhi_wx, stock_wx)
        if rel == "同气":
            score += 12
            details.append(f"月令{month_zhi_wx}旺 → 与股票{stock_wx}同气(月令直扶)")
            resonances.append("月令同气")
        elif rel == "相生":
            score += 9
            details.append(f"月令{month_zhi_wx} → 生 → 股票{stock_wx}(天时生扶)")
            resonances.append("月令生扶")
        elif rel == "被克":
            score -= 5
            details.append(f"月令{month_zhi_wx}克股票{stock_wx}(天时不利)")
        elif rel == "相克":
            score -= 3
            details.append(f"股票{stock_wx}克月令{month_zhi_wx}(逆势消耗)")
        else:
            details.append(f"月令{month_zhi_wx}与股票{stock_wx}关系中性")

    # 政策对股票行业的共振
    if policy_wx_list and stock_wx:
        matched = False
        for pw in policy_wx_list:
            rel = _wuxing_rel(pw, stock_wx)
            if rel in ("同气", "相生"):
                score += 8
                details.append(f"政策「{pw}」→ 共振股票「{stock_wx}」({rel})")
                resonances.append(f"政策{pw}共振")
                matched = True
        if not matched:
            for pw in policy_wx_list:
                details.append(f"政策「{pw}」与股票「{stock_wx}」无直接共振")

    # 月令与政策共振（双重加分）
    if month_zhi_wx and policy_wx_list:
        for pw in policy_wx_list:
            rel = _wuxing_rel(month_zhi_wx, pw)
            if rel in ("同气", "相生"):
                score += 5
                details.append(f"🔥 月令{month_zhi_wx}× 政策{pw}双重共振(天时地利)")
                resonances.append("天时地利共振")

    if len(resonances) >= 2:
        level = "主线共振"
    elif len(resonances) == 1:
        level = "局部共振"

    return {
        "score": max(0, min(40, score)),
        "level": level,
        "resonances": resonances,
        "detail": "；".join(details) if details else "无明显共振",
    }


# ============================================================
# 十三、地域八卦共振
# ============================================================

def _region_resonance_score(province: str, month_zhi_wx: str, policy_wx_list: list) -> dict:
    """
    地域八卦共振：省份→八卦→五行 + 月令/政策五行 → 叠加评分
    """
    region_wx = _resolve_province_bagua_wx(province)
    if not region_wx:
        return {"score": 5, "bagua": "", "region_wx": "", "detail": "地域数据未知"}

    score = 10
    details = []
    bagua = ""
    for key, gua in PROVINCE_BAGUA.items():
        if key in province:
            bagua = gua
            break

    # 地域五行 × 月令五行
    if month_zhi_wx:
        rel = _wuxing_rel(month_zhi_wx, region_wx)
        if rel in ("同气", "相生"):
            score += 6
            details.append(f"{bagua}位{region_wx}得月令{month_zhi_wx}{rel}")
        elif rel == "被克":
            score -= 3
            details.append(f"月令克{bagua}位")

    # 地域五行 × 政策五行
    if policy_wx_list:
        for pw in policy_wx_list:
            rel = _wuxing_rel(pw, region_wx)
            if rel in ("同气", "相生"):
                score += 5
                details.append(f"政策{pw}利好{bagua}位({province})")
                break

    return {
        "score": max(0, min(30, score)),
        "bagua": bagua,
        "region_wx": region_wx,
        "detail": "；".join(details) if details else f"{bagua}位{region_wx}，无特殊共振",
    }


# ============================================================
# 十四、综合评分公式 (0-100)
# ============================================================
# 承载力(35%) + 月令共振(20%) + 政策共振(15%) + 地域八卦(10%) + 资金验证(15%) + 动量(5%)

def _composite_score(capacity_score: float, monthly_res: dict, region_res: dict,
                     fund_verify: dict, chg_pct: float) -> dict:
    """
    六维综合评分 → 0-100
    """
    cap_norm = (capacity_score + 60) / 160 * 100  # [-60,100] → [0,100]
    cap_norm = max(0, min(100, cap_norm))

    monthly_norm = monthly_res["score"] / 40 * 100  # [0,40] → [0,100]
    policy_norm = monthly_norm  # 政策共振已合并在月令共振中
    region_norm = region_res["score"] / 30 * 100

    fund_scores = {"符合预期": 90, "主力撤退": 15, "骗炮嫌疑": 25, "待观察": 50}
    fund_norm = fund_scores.get(fund_verify["status"], 50)

    momentum_norm = max(0, min(100, 50 + chg_pct * 8))

    total = round(
        cap_norm * 0.35 +
        monthly_norm * 0.20 +
        policy_norm * 0.15 +
        region_norm * 0.10 +
        fund_norm * 0.15 +
        momentum_norm * 0.05,
        1,
    )

    return {
        "total": total,
        "breakdown": {
            "承载力(35%)": round(cap_norm * 0.35, 1),
            "月令共振(20%)": round(monthly_norm * 0.20, 1),
            "政策共振(15%)": round(policy_norm * 0.15, 1),
            "地域八卦(10%)": round(region_norm * 0.10, 1),
            "资金验证(15%)": round(fund_norm * 0.15, 1),
            "动量信号(5%)": round(momentum_norm * 0.05, 1),
        },
    }


# ============================================================
# 十五、主扫描函数
# ============================================================

def scan_zhuoyao(target_date_str: str = None,
                 policy_details: list = None,
                 min_composite: float = 30.0) -> dict:
    """
    玄捉妖扫描主函数

    Parameters:
        target_date_str : 目标交易日，默认2026-05-05
        policy_details  : 政策事件列表，如 ["碳中和政策加码", "芯片法案落地"]
        min_composite   : 综合评分最低门槛

    Returns:
        {
            target_date, window_dates, month_zhi_wx, policy_wx_list,
            total_scanned, excluded_count,
            results: [{...每个股票完整分析...}],
            top20: [...捉妖候选池...],
        }
    """
    import akshare as ak

    if target_date_str is None:
        target_date_str = "2026-05-05"

    print(f"\n{'='*60}")
    print(f"🐉 玄捉妖扫描系统 启动")
    print(f"   目标日: {target_date_str}")
    print(f"{'='*60}")

    # ---- 日期窗口 ----
    window_dates = _get_window_dates(target_date_str, 2, 2)
    target_gz = _get_day_ganzhi(target_date_str)
    month_zhi_wx = target_gz.get("month_wuxing", "")

    # ---- 政策事件 → 五行 ----
    if policy_details is None:
        policy_details = []
    policy_text = " ".join(_get_policy_events(policy_details))
    policy_wx_list = _resolve_policy_wuxing(policy_text)

    print(f"   扫描窗口: {window_dates[0]} ~ {window_dates[-1]}")
    print(f"   月令五行: {month_zhi_wx} (月支: {target_gz.get('month_zhi','')})")
    print(f"   政策五行: {policy_wx_list if policy_wx_list else '无'}")

    # ---- 拉取全A股实时行情 ----
    print(f"\n   ⏳ 拉取全A股实时行情...")
    df = ak.stock_zh_a_spot_em()
    print(f"   ✅ 共 {len(df)} 只")

    # ---- 逐只扫描 ----
    results = []
    excluded_count = 0
    no_ipo_count = 0

    for _, r in df.iterrows():
        code = str(r.get("代码", "")).strip()
        name = str(r.get("名称", "")).strip()

        if _is_excluded(code, name):
            excluded_count += 1
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

        # ---- 日元 ----
        riyuan = _get_riyuan(code)
        riyuan_gan = riyuan["gan"]
        riyuan_wx = riyuan["wuxing"]

        # ---- 5日承载力推演 ----
        cap_trace = _trace_5day_capacity(riyuan_gan, window_dates)
        target_day = cap_trace["days"].get(target_date_str, {})
        target_stage = target_day.get("stage", "衰")
        target_capacity = target_day.get("capacity", 0)

        # ---- 行业五行 ----
        industry_name = ""
        for col in ["行业", "所属行业", "板块"]:
            if col in r.index:
                industry_name = str(r[col]) if pd.notna(r[col]) else ""
                break
        stock_wx = _resolve_industry_wuxing(industry_name)

        # ---- 资金验证 ----
        fund_verify = _verify_fund(cap_trace["trend"], target_date_str, pct)

        # ---- 月令共振 ----
        monthly_res = _monthly_resonance_score(stock_wx, month_zhi_wx, policy_wx_list)

        # ---- 地域八卦共振 ----
        province = ""
        for col in ["省份", "地区", "地域", "所属地区"]:
            if col in r.index:
                province = str(r[col]) if pd.notna(r[col]) else ""
                break
        if not province:
            province = PROVINCE_CACHE.get(code, "")
        region_res = _region_resonance_score(province, month_zhi_wx, policy_wx_list)

        # ---- 综合评分 ----
        comp = _composite_score(target_capacity, monthly_res, region_res, fund_verify, pct)

        if comp["total"] < min_composite:
            continue

        # ---- 组装输出 ----
        _5d_stages = " → ".join(cap_trace["stages"]) if cap_trace["stages"] else ""
        _5d_caps = " → ".join(str(c) for c in cap_trace["capacities"]) if cap_trace["capacities"] else ""

        results.append({
            "code": code,
            "name": name,
            "price": round(price, 2),
            "pe": round(pe, 1),
            "chg_pct": round(pct, 2),
            "volume_yi": round(volume / 1e8, 2),
            "turnover": round(turnover, 2),
            "industry": industry_name,
            "province": province,
            # 日元
            "riyuan_gan": riyuan_gan,
            "riyuan_wx": riyuan_wx,
            "riyuan_ganzhi": riyuan["ganzhi"],
            # 行业五行
            "wuxing": stock_wx,
            # 目标日承载力
            "target_stage": target_stage,
            "target_capacity": target_capacity,
            "target_expected": target_day.get("expected_range", ""),
            # 5日窗口
            "window_5d_stages": _5d_stages,
            "window_5d_capacities": _5d_caps,
            "capacity_trend": cap_trace["trend"],
            # 资金验证
            "fund_status": fund_verify["status"],
            "fund_reason": fund_verify["reason"],
            "fund_confidence": fund_verify["confidence"],
            # 月令共振
            "monthly_level": monthly_res["level"],
            "monthly_detail": monthly_res["detail"],
            "monthly_score": round(monthly_res["score"], 1),
            # 地域八卦
            "region_bagua": region_res["bagua"],
            "region_wx": region_res["region_wx"],
            "region_detail": region_res["detail"],
            "region_score": round(region_res["score"], 1),
            # 政策共振
            "policy_wx_list": policy_wx_list,
            "policy_text": policy_text,
            # 综合
            "composite": comp["total"],
            "composite_breakdown": comp["breakdown"],
        })

    # ---- 综合排序 ----
    results.sort(key=lambda x: x["composite"], reverse=True)
    top20 = results[:20]

    # ---- 统计 ----
    diwang_count = sum(1 for r in results if r["target_stage"] == "帝旺")
    linguan_count = sum(1 for r in results if r["target_stage"] == "临官")
    fuhe_count = sum(1 for r in results if r["fund_status"] == "符合预期")
    pianpao_count = sum(1 for r in results if r["fund_status"] == "骗炮嫌疑")
    zhuxian_count = sum(1 for r in results if r["monthly_level"] == "主线共振")
    jubu_count = sum(1 for r in results if r["monthly_level"] == "局部共振")

    print(f"\n   ✅ 扫描完成")
    print(f"   合格股票: {len(results)} 只")
    print(f"   帝旺: {diwang_count} | 临官: {linguan_count}")
    print(f"   符合预期: {fuhe_count} | 骗炮嫌疑: {pianpao_count}")
    print(f"   主线共振: {zhuxian_count} | 局部共振: {jubu_count}")
    print(f"   🎯 捉妖池 Top 20 已就绪")
    print(f"{'='*60}\n")

    return {
        "target_date": target_date_str,
        "window_dates": window_dates,
        "target_ganzhi": target_gz,
        "month_zhi_wx": month_zhi_wx,
        "policy_wx_list": policy_wx_list,
        "policy_text": policy_text,
        "total_scanned": len(results),
        "excluded_count": excluded_count,
        "diwang_count": diwang_count,
        "linguan_count": linguan_count,
        "fuhe_count": fuhe_count,
        "pianpao_count": pianpao_count,
        "zhuxian_count": zhuxian_count,
        "jubu_count": jubu_count,
        "results": results,
        "top20": top20,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# 十六、快速格式化输出（控制台/文本用）
# ============================================================

def format_zhuoyao_report(data: dict) -> str:
    """格式化输出完整扫描报告（文本版）"""
    lines = []
    lines.append("=" * 70)
    lines.append("🐉  玄捉妖扫描系统 — 完整扫描报告")
    lines.append("=" * 70)
    lines.append(f"目标交易日: {data['target_date']}")
    lines.append(f"扫描窗口: {data['window_dates'][0]} ~ {data['window_dates'][-1]}")
    lines.append(f"月令五行: {data['month_zhi_wx']}")
    lines.append(f"政策事件五行: {data['policy_wx_list']}")
    lines.append(f"合格股票: {data['total_scanned']} | 排除: {data['excluded_count']}")
    lines.append(f"帝旺{data['diwang_count']} | 临官{data['linguan_count']}")
    lines.append(f"符合预期{data['fuhe_count']} | 骗炮{data['pianpao_count']}")
    lines.append(f"主线共振{data['zhuxian_count']} | 局部共振{data['jubu_count']}")
    lines.append("=" * 70)

    lines.append("\n## 🎯 捉妖候选池 TOP 20")
    lines.append("-" * 70)
    lines.append(f"{'排名':<5}{'代码':<8}{'名称':<10}{'日元':<6}{'承载力':<10}{'月令共振':<12}{'政策共振':<14}{'资金验证':<14}{'综合':<6}")
    lines.append("-" * 70)

    for i, r in enumerate(data["top20"], 1):
        lines.append(
            f"{i:<5}{r['code']:<8}{r['name']:<10}"
            f"{r['riyuan_gan']}({r['riyuan_wx']})  "
            f"{r['target_stage']}({r['target_capacity']})  "
            f"{r['monthly_level']:<10}"
            f"{';'.join(r['policy_wx_list']) if r['policy_wx_list'] else '无':<12}"
            f"{r['fund_status']:<12}"
            f"{r['composite']:<6}"
        )

    lines.append("-" * 70)
    lines.append(f"\n生成时间: {data['generated_at']}")
    lines.append("⚠️ 以上分析基于五行玄学框架，仅供研究与娱乐，不构成任何投资建议。")
    return "\n".join(lines)


def format_zhuoyao_single(r: dict) -> str:
    """格式化单个股票分析"""
    lines = []
    lines.append(f"\n{'─'*50}")
    lines.append(f"🐉 {r['name']}({r['code']})")
    lines.append(f"   日元: {r['riyuan_gan']}({r['riyuan_wx']}) | 行业五行: {r['wuxing']}")
    lines.append(f"   承载力: {r['target_stage']} (分:{r['target_capacity']}) | 预期: {r['target_expected']}")
    lines.append(f"   5日轨迹: {r['window_5d_stages']}")
    lines.append(f"   5日分值: {r['window_5d_capacities']}  | 趋势: {r['capacity_trend']}")
    lines.append(f"   资金验证: [{r['fund_confidence']}可信] {r['fund_status']} — {r['fund_reason']}")
    lines.append(f"   月令共振: {r['monthly_level']} | {r['monthly_detail']}")
    lines.append(f"   地域八卦: {r['region_bagua']}位{r['region_wx']} | {r['region_detail']}")
    lines.append(f"   综合评分: {r['composite']}/100")
    lines.append(f"   评分明细: {r['composite_breakdown']}")
    lines.append(f"{'─'*50}")
    return "\n".join(lines)


# ============================================================
# 独立运行测试
# ============================================================
if __name__ == "__main__":
    test_date = "2026-05-05"
    test_policies = [
        "碳中和政策加码",
        "芯片自主可控法案落地",
        "新型基建投资加速",
        "新能源补贴延续",
    ]
    data = scan_zhuoyao(test_date, policy_details=test_policies)
    print(format_zhuoyao_report(data))
    print("\n--- 详细展开 Top 5 ---")
    for r in data["top20"][:5]:
        print(format_zhuoyao_single(r))
