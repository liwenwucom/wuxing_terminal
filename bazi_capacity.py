# -*- coding: utf-8 -*-
"""
八字十二长生承载力引擎
基于股票上市日期(IPO)推算日元 → 交易日十二长生状态 → 承载力评分 → 量价验证

核心理论：
1. 股票上市日即其"八字"，日柱天干为"日元"（本质属性）
2. 每交易日对照十二长生表（长生→帝旺→墓→绝→胎→养），得"承载力状态"
3. 状态越强（帝旺>临官>冠带>...）→承载力越强→预期涨幅越大
4. "量价齐生"验证：承载力增强+涨幅同步放大=真实资金；承载力增强+涨幅缩水=骗炮
5. 年度级别：股市主体戊土喜火，丙午年(2026)火旺=大牛市格局
"""

from lunar_python import Solar, Lunar
from datetime import datetime


TIANGAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

DIZHI_WUXING = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 十二长生表：每个天干对应12地支的状态
# 顺序索引: 0长生 1沐浴 2冠带 3临官 4帝旺 5衰 6病 7死 8墓 9绝 10胎 11养
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

# 承载力评分：帝旺最高 → 绝最弱
CAPACITY_SCORES = {
    "帝旺": 1.0, "临官": 0.85, "冠带": 0.7, "沐浴": 0.5,
    "长生": 0.4, "衰": 0.2, "病": -0.1, "死": -0.3,
    "墓": -0.4, "绝": -0.6, "胎": -0.2, "养": 0.0,
}

# 承载力对应的预期涨幅参考区间（百分比）
EXPECTED_RANGE = {
    "帝旺": (3.0, 10.0), "临官": (1.5, 5.0), "冠带": (0.5, 3.0),
    "沐浴": (0.0, 1.5), "长生": (-0.5, 1.0), "衰": (-1.0, 0.5),
    "病": (-2.0, 0.0), "死": (-3.0, -0.5), "墓": (-2.0, 0.5),
    "绝": (-5.0, -1.0), "胎": (-1.5, 1.0), "养": (-0.5, 1.5),
}

# 股市大盘主体：默认戊土（喜火生）
MARKET_RIYUAN = "戊"
MARKET_WUXING = "土"


def get_riyuan_from_ipo(ipo_date_str):
    """
    根据IPO日期推算股票的"日元"（日柱天干）
    :param ipo_date_str: 'YYYY-MM-DD'
    :return: {"gan": "壬", "zhi": "戌", "wuxing": "水", "ganzhi": "壬戌"}
    """
    try:
        y, m, d = [int(x) for x in ipo_date_str.split("-")]
        solar = Solar.fromYmd(y, m, d)
        lunar = solar.getLunar()
        ganzhi = lunar.getDayInGanZhi()
        gan = ganzhi[0]
        zhi = ganzhi[1] if len(ganzhi) >= 2 else ""
        wx = TIANGAN_WUXING.get(gan, "未知")
        return {"gan": gan, "zhi": zhi, "wuxing": wx, "ganzhi": ganzhi}
    except Exception:
        return {"gan": "戊", "zhi": "辰", "wuxing": "土", "ganzhi": "戊辰"}


def get_trade_day_info(date_str):
    """
    获取交易日的完整干支信息
    """
    y, m, d = [int(x) for x in date_str.split("-")]
    solar = Solar.fromYmd(y, m, d)
    lunar = solar.getLunar()
    return {
        "year_ganzhi": lunar.getYearInGanZhi(),
        "month_ganzhi": lunar.getMonthInGanZhi(),
        "day_ganzhi": lunar.getDayInGanZhi(),
        "day_gan": lunar.getDayGan(),
        "day_zhi": lunar.getDayZhi(),
    }


def get_chang_sheng(riyuan_gan, trade_day_zhi):
    """
    查十二长生表，返回日元在交易日的状态
    :param riyuan_gan: 股票的日元天干（如"壬"）
    :param trade_day_zhi: 交易日的地支（如"寅"）
    :return: {"stage_index": 6, "stage_name": "病", "capacity_score": -0.1}
    """
    table = CHANG_SHENG_TABLE.get(riyuan_gan, {})
    idx = table.get(trade_day_zhi)
    if idx is None:
        return {"stage_index": -1, "stage_name": "未知", "capacity_score": 0.0}
    name = STAGE_NAMES[idx]
    score = CAPACITY_SCORES.get(name, 0.0)
    return {"stage_index": idx, "stage_name": name, "capacity_score": score}


def get_capacity_report(stock_name, stock_code, ipo_date_str, trade_date_str):
    """
    生成单只股票的承载力完整报告
    """
    riyuan = get_riyuan_from_ipo(ipo_date_str)
    trade_info = get_trade_day_info(trade_date_str)
    chang_sheng = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])

    # 预期涨幅区间
    stage = chang_sheng["stage_name"]
    exp_range = EXPECTED_RANGE.get(stage, (-1.0, 1.0))

    # 生克关系
    gan_wx = riyuan["wuxing"]
    zhi_wx = DIZHI_WUXING.get(trade_info["day_zhi"], "未知")
    sheng_ke = _analyze_sheng_ke(gan_wx, zhi_wx)

    return {
        "stock_name": stock_name,
        "stock_code": stock_code,
        "ipo_date": ipo_date_str,
        "riyuan": riyuan,
        "trade_date": trade_date_str,
        "trade_info": trade_info,
        "chang_sheng": chang_sheng,
        "expected_range": exp_range,
        "sheng_ke": sheng_ke,
        "capacity_score": chang_sheng["capacity_score"],
    }


def get_capacity_score_for_scoring(stock_code, ipo_date_map, trade_date_str=None):
    """
    为股票评分系统提供的标准化承载力因子 (范围 -0.6 ~ 1.0)
    """
    trade_date_str = trade_date_str or datetime.now().strftime("%Y-%m-%d")
    ipo = ipo_date_map.get(stock_code, "1990-01-01")
    riyuan = get_riyuan_from_ipo(ipo)
    trade_info = get_trade_day_info(trade_date_str)
    chang_sheng = get_chang_sheng(riyuan["gan"], trade_info["day_zhi"])
    return chang_sheng["capacity_score"]


def verify_price_volume(prev_capacity_score, curr_capacity_score,
                        prev_return_pct, curr_return_pct):
    """
    "量价齐生"验证法
    :return: {"signal": "...", "verdict": "符合预期"/"骗炮风险"/"短线透支"}
    """
    capacity_up = curr_capacity_score > prev_capacity_score
    capacity_down = curr_capacity_score < prev_capacity_score
    return_up = curr_return_pct > prev_return_pct

    if capacity_up and return_up:
        return {"signal": "量价齐生", "verdict": "真实资金流入，符合预期", "score_mod": 0.3}
    elif capacity_up and not return_up:
        return {"signal": "量升价缩", "verdict": "承载力增强但涨幅不跟上，警惕骗炮", "score_mod": -0.2}
    elif capacity_down and return_up:
        return {"signal": "量缩价升", "verdict": "承载力下降但涨幅逆势，短线透支易回调", "score_mod": -0.1}
    elif capacity_down and not return_up:
        return {"signal": "量价齐缩", "verdict": "承载力下降+涨幅同步走弱，趋势偏空", "score_mod": -0.3}
    else:
        return {"signal": "持平", "verdict": "承载力持平，方向不明", "score_mod": 0.0}


def get_market_annual_assessment(year_ganzhi=None):
    """
    年度级别判断：股市(戊土)喜火生
    2026=丙午(火旺)→大牛市格局
    """
    if year_ganzhi is None:
        now = datetime.now()
        s = Solar.fromYmd(now.year, now.month, now.day)
        year_ganzhi = s.getLunar().getYearInGanZhi()

    gan = year_ganzhi[0]
    zhi = year_ganzhi[1]
    gan_wx = TIANGAN_WUXING.get(gan, "未知")
    zhi_wx = DIZHI_WUXING.get(zhi, "未知")

    # 戊土喜火生，忌金泄
    grade = "中性"
    if gan_wx == "火" and zhi_wx == "火":
        grade = "大旺（火年火月，戊土得双火生，预期牛市）"
    elif gan_wx == "火":
        grade = "偏旺（天干火生土，地支无克则佳）"
    elif gan_wx == "金" and zhi_wx == "金":
        grade = "偏弱（金旺泄土气，火被金克无法生土）"
    elif gan_wx == "水":
        grade = "偏弱（水旺耗火，土被水淹）"

    return {
        "year_ganzhi": year_ganzhi,
        "gan_wuxing": gan_wx,
        "zhi_wuxing": zhi_wx,
        "grade": grade,
        "explanation": f"股市戊土喜火。{gan_wx}年干{'生土' if gan_wx=='火' else '平凡' if gan_wx=='土' else '泄土' if gan_wx=='金' else '耗土' if gan_wx=='水' else ''}",
    }


def _analyze_sheng_ke(gan_wx, zhi_wx):
    """简化的五行生克分析"""
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    if gan_wx == zhi_wx:
        return "日元与日支同五行，气场平稳"
    elif sheng.get(gan_wx) == zhi_wx:
        return f"日元{gan_wx}生地支{zhi_wx}→泄气，承载力偏弱"
    elif sheng.get(zhi_wx) == gan_wx:
        return f"地支{zhi_wx}生日元{gan_wx}→得生，承载力增强"
    elif ke.get(gan_wx) == zhi_wx:
        return f"日元{gan_wx}克地支{zhi_wx}→主动但耗力"
    elif ke.get(zhi_wx) == gan_wx:
        return f"地支{zhi_wx}克日元{gan_wx}→受克，承载力被压制"
    return "关系复杂"


IPO_DATE_MAP = {
    "600519": "2001-08-27",  # 贵州茅台 → 壬水
    "000858": "1998-04-27",  # 五粮液
    "002594": "2011-06-30",  # 比亚迪
    "300750": "2018-06-11",  # 宁德时代
    "601398": "2006-10-27",  # 工商银行
    "600036": "2002-04-09",  # 招商银行
    "601939": "2007-09-25",  # 建设银行
    "601288": "2010-07-15",  # 农业银行
    "600030": "2003-01-06",  # 中信证券
    "300059": "2010-03-19",  # 东方财富
    "601688": "2010-02-26",  # 华泰证券
    "601318": "2007-03-01",  # 中国平安
    "601628": "2007-01-09",  # 中国人寿
    "601319": "2018-11-16",  # 中国人保
    "601138": "2018-06-08",  # 工业富联
    "300308": "2017-07-14",  # 中际旭创
    "000063": "1997-11-18",  # 中兴通讯
    "600941": "2022-01-05",  # 中国移动
    "600309": "2001-01-05",  # 万华化学
    "002001": "2004-06-25",  # 新和成
    "002415": "2010-05-28",  # 海康威视
    "600988": "2004-04-14",  # 赤峰黄金（借壳上市或大致）
    "688256": "2020-07-20",  # 寒武纪
    "601899": "2008-04-25",  # 紫金矿业
    "600150": "1998-05-20",  # 中国船舶
    "601668": "2009-07-29",  # 中国建筑
    "601390": "2007-12-03",  # 中国中铁
    "600585": "2002-02-07",  # 海螺水泥
    "600031": "2003-07-03",  # 三一重工
    "600406": "2003-10-16",  # 国电南瑞
    "600900": "2003-11-18",  # 长江电力
    "601088": "2007-10-09",  # 中国神华
    "601699": "2006-09-22",  # 潞安环能
    "601857": "2007-11-05",  # 中国石油
    "002840": "2017-01-10",  # 华统股份
    "603345": "2017-02-22",  # 安井食品
    "600588": "2001-05-18",  # 用友网络
    "601615": "2019-01-22",  # 明阳智能
    "605499": "2021-05-27",  # 东鹏饮料
    "000988": "2000-06-08",  # 华工科技
    "688702": "2023-09-14",  # 盛科通信
    "600048": "2006-07-31",  # 保利发展
    "600438": "2004-03-02",  # 通威股份
    "300274": "2011-11-02",  # 阳光电源
    "600276": "2000-10-18",  # 恒瑞医药
    "002714": "2014-01-28",  # 牧原股份
    "300760": "2018-10-16",  # 迈瑞医疗
    "601012": "2012-04-11",  # 隆基绿能
    "688981": "2023-05-10",  # 中芯国际(A)
    "002371": "2010-03-16",  # 北方华创
    "603501": "2017-05-04",  # 韦尔股份
    "600584": "2003-06-03",  # 长电科技
    "600887": "1996-03-12",  # 伊利股份
    "603288": "2014-02-11",  # 海天味业
    "601888": "2009-10-15",  # 中国中免
    "600346": "2010-02-09",  # 恒力石化（借壳）
    "000651": "1996-11-18",  # 格力电器
    "000333": "2013-09-18",  # 美的集团
    "601919": "2007-06-26",  # 中远海控
    "600018": "2006-10-26",  # 上港集团
    "600760": "1996-10-11",  # 中航沈飞
    "600893": "1996-04-11",  # 航发动力
    "002007": "2004-06-25",  # 华兰生物
    "601899": "2008-04-25",  # 紫金矿业
    "600111": "1997-09-24",  # 北方稀土
    "600019": "2000-12-12",  # 宝钢股份
    "601225": "2014-01-28",  # 陕西煤业
    "600905": "2021-06-22",  # 三峡能源
    "600011": "2001-12-06",  # 华能国际
}
