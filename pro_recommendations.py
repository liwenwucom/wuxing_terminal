# -*- coding: utf-8 -*-
"""
2026Q2 专业股票推荐知识库
来源：国家级政策信号 + 多家券商研报共识
长持10 / 短配10 / 长回避10类 / 短回避10类
"""

LONG_HOLD = [
    {
        "code": "002594", "name": "比亚迪", "industry": "新能源",
        "logic": "全球新能源车龙头，以旧换新政策+海外扩张提速，一季度销量持续领跑",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "601138", "name": "工业富联", "industry": "通信",
        "logic": "AI基础设施景气上行，英伟达GB系列代工需求强劲，AI服务器营收占比持续提升",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "300308", "name": "中际旭创", "industry": "通信",
        "logic": "800G/1.6T光模块渗透率提升，获4家券商推荐，总市值一度突破1万亿",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "688702", "name": "盛科通信", "industry": "半导体",
        "logic": "国内稀缺以太网交换芯片标的，国产替代逻辑+AI数据中心需求爆发，4月涨幅超93%",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "600309", "name": "万华化学", "industry": "化工",
        "logic": "获15家券商买入评级，MDI价格中枢上移叠加新材料(POE、柠檬醛)量产驱动",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "603345", "name": "安井食品", "industry": "消费",
        "logic": "获5家券商联合推荐，速冻食品龙头受益餐饮复苏与预制菜渗透率提升",
        "window": "中长期(6月+)",
        "consensus": True,
    },
    {
        "code": "600150", "name": "中国船舶", "industry": "军工",
        "logic": "全球造船周期上行+船价上涨，手持订单饱满，交付确认业绩拐点",
        "window": "中长期(6月+)",
        "consensus": False,
    },
    {
        "code": "600406", "name": "国电南瑞", "industry": "电力",
        "logic": "配电网特高压投资确定性，六张网电网建设核心供应商，十五五确定性受益",
        "window": "中长期(6月+)",
        "consensus": False,
    },
    {
        "code": "002415", "name": "海康威视", "industry": "安防",
        "logic": "EBG事业群AI渗透率提升，观澜大模型赋能传统行业数字化转型，估值处近五年低位",
        "window": "中长期(6月+)",
        "consensus": False,
    },
    {
        "code": "601319", "name": "中国人保", "industry": "保险",
        "logic": "高股息防御资产，中长期资金入市+利率下降保险负债成本改善，红利资产配置价值上升",
        "window": "中长期(6月+)",
        "consensus": True,
    },
]

SHORT_TRADE = [
    {
        "code": "600988", "name": "赤峰黄金", "industry": "有色",
        "buy_trigger": "全球地缘避险升温+降息预期→金价突破前高",
        "sell_trigger": "美伊停火或美元大幅反弹，金价跌破5日线",
        "consensus": True,
    },
    {
        "code": "002840", "name": "华统股份", "industry": "消费",
        "buy_trigger": "牛周期反转确立，2026年肉牛供给缺口预计持续扩大，牛价有望加速上行",
        "sell_trigger": "牛价月度涨幅放缓或产能恢复信号显现",
        "consensus": True,
    },
    {
        "code": "601699", "name": "潞安环能", "industry": "煤炭",
        "buy_trigger": "迎峰度夏用电旺季来临+煤价季节性回升",
        "sell_trigger": "夏季补库结束或煤价走弱，跌破30日均线",
        "consensus": True,
    },
    {
        "code": "688256", "name": "寒武纪", "industry": "半导体",
        "buy_trigger": "国产AI芯片替代逻辑，十五五AI产业10万亿目标提供叙事",
        "sell_trigger": "财报不及预期或行业竞争格局恶化",
        "consensus": True,
    },
    {
        "code": "002001", "name": "新和成", "industry": "化工",
        "buy_trigger": "VE/VA价格处于历史低位，供给收缩+需求回暖，涨价预期",
        "sell_trigger": "产品价格反弹至历史中枢时部分减仓",
        "consensus": True,
    },
    {
        "code": "300308", "name": "中际旭创(短)", "industry": "通信",
        "buy_trigger": "CPO技术商业化加速+AI算力资本开支上行周期",
        "sell_trigger": "高景气高估值高拥挤三高警示，技术面过热时减仓",
        "consensus": False,
    },
    {
        "code": "600588", "name": "用友网络", "industry": "软件",
        "buy_trigger": "国产替代政策+AI加持BIP3产品升级，业绩有底部弹性",
        "sell_trigger": "年报/季报去金融化转型不及预期",
        "consensus": False,
    },
    {
        "code": "601615", "name": "明阳智能", "industry": "新能源",
        "buy_trigger": "海上风电装机提速，双碳考核硬约束下运营商加快资本开支",
        "sell_trigger": "风机招标价格连续两季度下行",
        "consensus": False,
    },
    {
        "code": "605499", "name": "东鹏饮料", "industry": "消费",
        "buy_trigger": "能量饮料赛道高景气+Q2旺季业绩催化",
        "sell_trigger": "PE 40倍以上或月度销售持续走弱",
        "consensus": False,
    },
    {
        "code": "000988", "name": "华工科技", "industry": "通信",
        "buy_trigger": "光模块放量+激光设备受益制造业景气回升",
        "sell_trigger": "CPO技术路线不确定性或业绩不达预期",
        "consensus": False,
    },
]

LONG_AVOID = [
    {"direction": "地产开发商(民企)", "reason": "保交房与化存量背景下房地产投资持续下行，行业利润空间持续收窄", "since": "2025Q4"},
    {"direction": "传统燃油整车", "reason": "新能源渗透率提升+价格战盈利挤压+自主品牌份额提升，合资燃油车利润萎缩", "since": "长期"},
    {"direction": "教培(学科类)", "reason": "双减监管框架持续收紧，资本化路径受阻，政策方向无根本性逆转", "since": "长期"},
    {"direction": "仿制药无创新能力", "reason": "集采常态化+医保控费，普通仿制药利润空间持续压缩，创新门槛高昂", "since": "长期"},
    {"direction": "餐饮加盟连锁(低壁垒)", "reason": "消费分级背景下同质化竞争+租金人工成本上涨+平台抽成侵蚀，净利润率极薄", "since": "长期"},
    {"direction": "低端纺织制造", "reason": "东南亚竞争+国内人工环保成本上升+外贸订单流失，性价比逻辑被挑战", "since": "长期"},
    {"direction": "纯组件光伏(无上游)", "reason": "主材产能严重过剩+价格战激烈+技术迭代颠覆加速，低毛利甚至亏损是常态", "since": "长期"},
    {"direction": "城投平台非标融资", "reason": "地方化债严监管下融资类业务持续萎缩，信用分层加剧，尾部城投风险暴露", "since": "长期"},
    {"direction": "传统纯连锁百货", "reason": "线上渗透率攀升+购物中心体验分流+百货业态转型困难，坪效客流量双降", "since": "长期"},
    {"direction": "高估值小市值科技概念", "reason": "注册制+退市新规壳价值归零，连20日市值<5亿即退市，炒小炒差时代终结", "since": "2026新规"},
]

SHORT_AVOID = [
    {"direction": "*ST股票", "reason": "退市风险集中，应退尽退优胜劣汰成铁律", "window": "2026全年"},
    {"direction": "光模块(高位追涨)", "reason": "高景气高估值高拥挤三高状态，对交易能力要求越来越高", "window": "2026年5-6月"},
    {"direction": "光伏组件股", "reason": "一季报产能过剩矛盾消化中，供需未根本改善，短期缺乏涨价动力", "window": "2026年5-6月"},
    {"direction": "电商代运营", "reason": "短视频直播算法红利消退+平台抽成上涨+流量成本攀升，业绩承压", "window": "2026年5-8月"},
    {"direction": "电子烟概念股", "reason": "国内外监管收紧方向明确，税收和渠道政策不确定性高", "window": "2026年5-9月"},
    {"direction": "上市未满一年新股(科创板)", "reason": "解禁潮涌出(5-7月小非解禁高峰)+次新股流动性折价", "window": "2026年5-7月"},
    {"direction": "创投VC/PE概念股", "reason": "注册制IPO退出节奏放缓+二级市场估值中枢下移，退出收益率收窄", "window": "2026年5-12月"},
    {"direction": "部分白酒二线品牌(酒鬼酒/舍得等)", "reason": "商务宴请恢复慢于预期+渠道去库存压力+二三线品牌溢价能力下降", "window": "2026年5-8月"},
    {"direction": "数字货币概念股(无实质业务)", "reason": "炒作情绪退潮+全球加密监管收紧+国内无实质业务支撑，回调压力大", "window": "2026全年"},
    {"direction": "传统航空股(三大航)", "reason": "国际航线恢复不及预期+油价高位震荡+汇率波动财务成本重，业绩修复缓慢", "window": "2026年5-9月"},
]


def is_in_long_hold(code):
    return any(s["code"] == code for s in LONG_HOLD)


def is_in_short_trade(code):
    return any(s["code"] == code for s in SHORT_TRADE)


def is_in_avoid_direction(industry):
    for a in LONG_AVOID:
        if a["direction"] in industry:
            return True, a["reason"]
    return False, ""


def get_consensus_bonus(code):
    """共识度加分：券商同推+多机构认同"""
    for s in LONG_HOLD:
        if s["code"] == code and s["consensus"]:
            return 1.5
    for s in SHORT_TRADE:
        if s["code"] == code and s["consensus"]:
            return 1.0
    return 0.0


def get_pro_recommendation(code):
    """返回股票的机构推荐标签"""
    for s in LONG_HOLD:
        if s["code"] == code:
            return {"type": "long_hold", "label": "核心成长股", "logic": s["logic"],
                    "consensus": s["consensus"]}
    for s in SHORT_TRADE:
        if s["code"] == code:
            return {"type": "short_trade", "label": "弹性交易股",
                    "buy_trigger": s["buy_trigger"], "sell_trigger": s["sell_trigger"],
                    "consensus": s["consensus"]}
    return None


def get_long_avoid_list():
    return [a["direction"] for a in LONG_AVOID]


def get_short_avoid_list():
    return [s["direction"] for s in SHORT_AVOID]
