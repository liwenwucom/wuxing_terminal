# -*- coding: utf-8 -*-
"""
2026 中国政策新闻五星结构化知识库
金木水火土五星维度编码 20 条关键经济政策
"""

from datetime import datetime

POLICY_BY_ELEMENT = {
    "金": {
        "title": "金融活水 — 降准降息 + 科创资本护航",
        "policies": [
            {
                "id": 1,
                "title": "央行降准降息",
                "desc": "降准0.5百分点，LPR降至3%，OMO降至1.4%，释放1万亿流动性",
                "direction": "利好",
                "industries": ["银行", "证券", "保险", "房地产"],
                "target_stocks": ["601398", "600036", "600030", "600048"],
                "keywords": ["降准", "降息", "LPR", "流动性", "货币宽松"],
            },
            {
                "id": 2,
                "title": "5000亿消费养老再贷款+3000亿科创再贷款",
                "desc": "科技创新债券风险分担，央行再贷款总额大幅扩充",
                "direction": "利好",
                "industries": ["半导体", "新能源", "消费"],
                "target_stocks": ["688981", "002371", "600887", "300760"],
                "keywords": ["再贷款", "科技创新", "消费", "养老"],
            },
            {
                "id": 3,
                "title": "集成电路软件产业税收优惠",
                "desc": "五部门联发落实芯片产业税收优惠清单",
                "direction": "利好",
                "industries": ["半导体", "通信"],
                "target_stocks": ["688981", "002371", "603501", "000063"],
                "keywords": ["集成电路", "芯片", "税收优惠", "软件"],
            },
            {
                "id": 4,
                "title": "科创板八条+第五套上市标准扩围",
                "desc": "上交所完善科创企业上市融资并购重组渠道",
                "direction": "利好",
                "industries": ["证券", "半导体", "医药"],
                "target_stocks": ["600030", "688981", "600276", "300760"],
                "keywords": ["科创板", "IPO", "硬科技", "上市标准"],
            },
            {
                "id": 25,
                "title": "国务院设立国家级并购基金",
                "desc": "推进十五五109项重大工程，点名六大新兴支柱产业和六大未来产业",
                "direction": "利好",
                "industries": ["证券", "军工", "半导体", "新能源"],
                "target_stocks": ["600030", "601668", "600760"],
                "keywords": ["并购基金", "央企资产证券化", "先进制造", "未来产业"],
            },
            {
                "id": 26,
                "title": "创业板并购重组改革+退市新规",
                "desc": "市值100亿以上龙头重组绿色通道；连续20日市值<5亿直接退市，壳价值归零",
                "direction": "利好",
                "industries": ["证券", "银行"],
                "target_stocks": ["600030", "300059", "601398"],
                "keywords": ["并购重组", "退市新规", "壳价值", "优质龙头"],
            },
        ],
    },
    "木": {
        "title": "产业播种 — AI智能体 + 新能源 + 乡村振兴",
        "policies": [
            {
                "id": 5,
                "title": "模数共振行动：AI赋能20个重点行业",
                "desc": "工信部国家数据局启动工业智能体工厂，覆盖钢铁汽车航空航天",
                "direction": "利好",
                "industries": ["军工", "汽车", "钢铁", "通信"],
                "target_stocks": ["600760", "600031", "600019", "600104"],
                "keywords": ["AI", "智能体", "工业互联网", "制造业"],
            },
            {
                "id": 6,
                "title": "风光新能源装机首超煤电",
                "desc": "光伏总装机首超煤电，双碳纳入地方政府刚性政绩考核",
                "direction": "利好",
                "industries": ["新能源", "电力"],
                "target_stocks": ["601012", "300274", "600438", "600905"],
                "keywords": ["光伏", "风电", "双碳", "新能源装机"],
            },
            {
                "id": 7,
                "title": "金融支持乡村全面振兴",
                "desc": "金办发33号文，加大农林牧渔数智化金融支撑",
                "direction": "利好",
                "industries": ["农业"],
                "target_stocks": ["002385", "000998", "002714"],
                "keywords": ["乡村振兴", "农业", "金融支持"],
            },
            {
                "id": 8,
                "title": "国家算力基础设施五年行动计划",
                "desc": "东数西算深入实施，算电协同写入政府工作报告",
                "direction": "利好",
                "industries": ["通信", "半导体", "电力"],
                "target_stocks": ["600941", "000063", "300308", "600900"],
                "keywords": ["算力", "东数西算", "数据中心", "算电协同"],
            },
        ],
    },
    "水": {
        "title": "流通大道 — 物流补链 + 消费活水 + 保交房",
        "policies": [
            {
                "id": 9,
                "title": "综合货运枢纽补链强链提升行动",
                "desc": "财政部交通部联合，3年覆盖30城群",
                "direction": "利好",
                "industries": ["航运", "基建"],
                "target_stocks": ["601919", "600018", "601668", "601390"],
                "keywords": ["物流", "枢纽", "交通运输", "多式联运"],
            },
            {
                "id": 10,
                "title": "因城施策去库存，保交房全面完成",
                "desc": "房地产市场在强力融资与监管协调中实现软着陆",
                "direction": "中性",
                "industries": ["房地产", "建材"],
                "target_stocks": ["600048", "000002", "600585"],
                "keywords": ["房地产", "保交房", "去库存", "楼市"],
            },
            {
                "id": 11,
                "title": "汽车以旧换新最高补贴2万",
                "desc": "报废购买新能源乘用车最高补2万，以旧换新扩至数码产品",
                "direction": "利好",
                "industries": ["汽车", "消费", "新能源"],
                "target_stocks": ["002594", "600104", "601633"],
                "keywords": ["以旧换新", "汽车补贴", "消费"],
            },
            {
                "id": 12,
                "title": "全社会物流降本增效",
                "desc": "公铁空无缝衔接，打通生产消费卡点堵点",
                "direction": "利好",
                "industries": ["航运", "基建"],
                "target_stocks": ["601919", "601390", "601668"],
                "keywords": ["物流", "降本增效", "多式联运", "供应链"],
            },
        ],
    },
    "火": {
        "title": "动能转换 — 六张网基建 + 旧城改造 + 碳金融",
        "policies": [
            {
                "id": 13,
                "title": "政治局部署六张网建设: 7万亿落地",
                "desc": "水网+新型电网+算力网+通信网+地下管网+物流网，2026年初步估算投资超7万亿",
                "direction": "利好",
                "industries": ["基建", "电力", "钢铁", "通信", "建材"],
                "target_stocks": ["601668", "601390", "600900", "600019", "600941", "000063"],
                "keywords": ["六张网", "7万亿", "基建", "超长期国债", "新基建"],
            },
            {
                "id": 14,
                "title": "住房公积金贷款利率下调0.25%",
                "desc": "金融支持住房与消费结构升级",
                "direction": "利好",
                "industries": ["房地产", "银行", "消费"],
                "target_stocks": ["600048", "601398", "600887"],
                "keywords": ["公积金", "房贷利率", "住房消费"],
            },
            {
                "id": 15,
                "title": "增存挂钩机制，城镇化告别大拆大建",
                "desc": "存量盘活为主，新增用地优先保障重大基建",
                "direction": "中性",
                "industries": ["房地产", "基建"],
                "target_stocks": ["600048", "600585", "000002"],
                "keywords": ["土地管理", "存量盘活", "城镇化"],
            },
            {
                "id": 16,
                "title": "国家低碳转型基金+碳金融顶层设计",
                "desc": "中办国办印发节能降碳意见，碳配额与绿色信贷体系构建",
                "direction": "利好",
                "industries": ["新能源", "电力", "化工"],
                "target_stocks": ["601012", "300274", "600905", "600309"],
                "keywords": ["碳金融", "低碳转型", "绿色信贷", "碳配额"],
            },
        ],
    },
    "土": {
        "title": "国家根基 — 区域协调 + 投资落地 + 民生就业",
        "policies": [
            {
                "id": 17,
                "title": "京津冀协同发展进入关键期",
                "desc": "习近平赴雄安主持座谈，把脉新时代区域协调",
                "direction": "利好",
                "industries": ["基建", "建材", "环保"],
                "target_stocks": ["601668", "601390", "600585"],
                "keywords": ["京津冀", "雄安", "区域协调", "城市群"],
            },
            {
                "id": 18,
                "title": "7550亿中央预算+1万亿超长期国债",
                "desc": "上半年基本下达完毕，十五五开局稳投资组合拳",
                "direction": "利好",
                "industries": ["基建", "钢铁", "建材"],
                "target_stocks": ["601668", "600019", "600585", "600031"],
                "keywords": ["中央预算", "国债", "投资", "十五五"],
            },
            {
                "id": 19,
                "title": "稳岗扩容保供稳价全覆盖",
                "desc": "就业提升置于十五五开局核心，保供稳价兜底民生",
                "direction": "中性",
                "industries": ["消费", "农业"],
                "target_stocks": ["600887", "000651", "002385"],
                "keywords": ["就业", "保供稳价", "民生"],
            },
            {
                "id": 20,
                "title": "智能算力突破188 EFLOPS",
                "desc": "东数西算全国调度平台接入137万PFLOPS智能算力",
                "direction": "利好",
                "industries": ["通信", "半导体"],
                "target_stocks": ["600941", "300308", "000063"],
                "keywords": ["算力", "东数西算", "AI", "数字中国"],
            },
        ],
    },
}


GLOBAL_POLICY_BY_ELEMENT = {
    "金": {
        "region": "北美与大洋洲",
        "title": "光环下的暗涌 — 美元资产与资源品核心市场",
        "policies": [
            {
                "id": "G1",
                "title": "美国GDP年化增长2.0%，CPI飙至3.5%",
                "desc": "AI投资提振经济但高物价与财政压力加剧，伯克希尔后巴菲特时代开启",
                "direction": "中性",
                "industries": ["银行", "证券", "半导体"],
                "impact_china": "美股高估值风险可能引发外资回流，间接影响A股北向资金",
                "keywords": ["美国GDP", "美联储", "通胀", "巴菲特"],
            },
            {
                "id": "G2",
                "title": "澳洲联储多次加息，通胀3.7%",
                "desc": "制造业重回扩张但中东冲突推高输入性成本",
                "direction": "中性",
                "industries": ["有色", "钢铁"],
                "impact_china": "铁矿石/锂矿进口成本上升，利好国内替代(紫金矿业/北方稀土)",
                "keywords": ["澳洲加息", "铁矿石", "RBA", "大宗商品"],
            },
        ],
    },
    "木": {
        "region": "东亚与南美",
        "title": "复苏中的生长 — 科技圈与资源型经济体",
        "policies": [
            {
                "id": "G3",
                "title": "韩国半导体出口同比+48%",
                "desc": "一季度出口额超越日本，但进口物价创金融危机以来最大涨幅",
                "direction": "利好",
                "industries": ["半导体", "通信"],
                "impact_china": "韩国半导体需求旺盛，利好上游供应链及国产替代(北方华创/长电科技)",
                "keywords": ["韩国出口", "半导体", "芯片", "三星"],
            },
            {
                "id": "G4",
                "title": "欧盟-南方共同市场贸易协定生效",
                "desc": "历时26年签署，重塑全球农产品与工业品格局",
                "direction": "利好",
                "industries": ["农业", "家电", "汽车"],
                "impact_china": "南美农产品关税降低但中国工业品竞争力仍强，关注贸易转移效应",
                "keywords": ["EU-Mercosur", "贸易协定", "南美", "农产品"],
            },
            {
                "id": "G5",
                "title": "日本工业生产连续两月下滑",
                "desc": "受中东冲突影响，泰国增速或创30年新低",
                "direction": "利空",
                "industries": ["汽车", "消费"],
                "impact_china": "泰铢贬值可能影响中国对东盟出口，日本产能受损利好中国承接替代订单",
                "keywords": ["日本工业", "泰国经济", "东盟"],
            },
        ],
    },
    "水": {
        "region": "东南亚与非洲",
        "title": "流动中的变局 — 海上枢纽与新兴市场",
        "policies": [
            {
                "id": "G6",
                "title": "中国对53个非洲建交国零关税",
                "desc": "自5月1日起全面实施，极大促进非洲对华农产品出口",
                "direction": "利好",
                "industries": ["航运", "贸易", "农业"],
                "impact_china": "中非贸易量激增，利好港口(上港集团/中远海控)及农产品加工",
                "keywords": ["零关税", "中非贸易", "非洲", "农产品"],
            },
            {
                "id": "G7",
                "title": "印尼拟对马六甲海峡收费+调整镍矿规则",
                "desc": "马来西亚能源储备告急进入应对状态",
                "direction": "利空",
                "industries": ["航运", "有色"],
                "impact_china": "海峡收费推高海运成本，镍矿出口规则调整利好国内镍相关标的",
                "keywords": ["马六甲海峡", "印尼镍矿", "马来西亚能源"],
            },
        ],
    },
    "火": {
        "region": "欧洲与中东",
        "title": "压力下的动荡 — 能源价格与地缘外溢",
        "policies": [
            {
                "id": "G8",
                "title": "欧元区滞胀风险：GDP+0.1% vs CPI+3.0%",
                "desc": "一季度GDP环比仅增0.1%，通胀率飙至三年最高",
                "direction": "利空",
                "industries": ["银行", "消费", "新能源"],
                "impact_china": "欧洲消费需求萎缩利空出口型行业，但能源转型需求利好光伏风电",
                "keywords": ["欧元区", "滞胀", "欧洲央行", "ECB"],
            },
            {
                "id": "G9",
                "title": "中东冲突持续外溢至消费品价格",
                "desc": "Dove制造商发出价格频繁小幅上涨警告，能源价格传导至全球",
                "direction": "利空",
                "industries": ["石油", "化工", "航运"],
                "impact_china": "油价上涨利好三桶油(中石油/中石化/中海油)但压制航运成本",
                "keywords": ["地缘冲突", "油价", "中东", "消费品涨价"],
            },
        ],
    },
    "土": {
        "region": "中国内地与南亚",
        "title": "定力中的空间 — 内需大国压舱石",
        "policies": [
            {
                "id": "G10",
                "title": "中国5%GDP开局+社零增速加快",
                "desc": "高于预期的一季度增速，稳定基本面为全球注入确定性",
                "direction": "利好",
                "industries": ["消费", "基建", "银行"],
                "impact_china": "内需强劲利好消费龙头+基建(伊利/中国建筑/保利)",
                "keywords": ["GDP", "社零", "内需", "中国增长"],
            },
            {
                "id": "G11",
                "title": "香港2026财政预算案: AI+金融科技重注",
                "desc": "GDP增速上调至3.2%，多年赤字后录得29亿盈余，资源集中长期产业投入",
                "direction": "利好",
                "industries": ["证券", "通信", "银行"],
                "hk_targets": ["00700", "00388", "00941"],
                "impact_china": "香港金融科技+AI投入利好港股，惠及港交所(00388)/腾讯(00700)/中移动(00941)",
                "keywords": ["香港预算案", "AI", "金融科技", "港股", "财政转盈"],
            },
            {
                "id": "G12",
                "title": "印尼PMI扩张+游客创新高",
                "desc": "短期贸易政策调整未撼基本盘，印度卢比受油价影响走弱",
                "direction": "中性",
                "industries": ["消费", "航运"],
                "impact_china": "东南亚消费升级+中印尼贸易利好消费品出海",
                "keywords": ["印尼经济", "印度卢比", "PMI", "东南亚"],
            },
        ],
    },
}


ELEMENT_INDUSTRY_MAP = {
    "金": ["银行", "保险", "证券", "金融", "钢铁", "家电", "通信", "有色"],
    "木": ["军工", "新能源", "医药", "农业", "环保", "汽车"],
    "水": ["航运", "酒类", "化工", "水利", "贸易", "物流"],
    "火": ["半导体", "电力", "煤炭", "石油", "传媒", "安防", "软件"],
    "土": ["房地产", "基建", "水泥", "建材", "消费", "工程机械"],
}


# ============================================================
# 期货交易所政策信号池（水洲）
# ============================================================
EXCHANGE_POLICIES = [
    {
        "id": "EX1",
        "title": "大商所期转现+生猪鸡蛋仓单规则修改征求意见",
        "desc": "未来生猪、鸡蛋仓单流转效率可能提升，有助基差点价与风险管理",
        "deadline": "2026-05-08",
        "affects": ["生猪", "鸡蛋"],
    },
    {
        "id": "EX2",
        "title": "五一休市及节后保证金调整",
        "desc": "5月1-5日休市；节后丙烯期货2607-2609保证金18%，苹果15%，红枣14%",
        "affects": ["丙烯", "苹果", "红枣"],
    },
    {
        "id": "EX3",
        "title": "广期所节后保证金恢复",
        "desc": "工业硅、多晶硅、碳酸锂、铂、钯期货保证金恢复至调整前水平",
        "affects": ["工业硅", "碳酸锂", "多晶硅"],
    },
    {
        "id": "EX4",
        "title": "5月交易交割日历提醒",
        "desc": "5/8上期所非燃料油2605最后交易日；5/22 FU2606最后交易日；5/29 2606合约最后交易日",
        "affects": ["沪铜", "沪金", "沪银", "燃料油", "螺纹钢"],
    },
    {
        "id": "EX5",
        "title": "国际地缘局势监测：美伊谈判",
        "desc": "阶段性缓和但反复风险未消除，原油、黄金期货波动率预计持续偏高",
        "affects": ["原油", "黄金", "白银"],
    },
]


# ============================================================
# 火洲 — 政策风向敏感标的池（A-E）
# ============================================================
FIRE_SENSITIVE_TARGETS = [
    {
        "id": "A",
        "label": "六张网概念基建股",
        "trigger": "地方发改委下达重大工程批复或专项债发行超预期",
        "action": "右侧买入",
        "industries": ["基建", "建材", "钢铁"],
        "target_stocks": ["601668", "601390", "600585", "600031"],
        "risk": "基建股体量大弹性小，适合长期配置而非博弈",
    },
    {
        "id": "B",
        "label": "降准降息弹性标的",
        "trigger": "二季度降息概率上升，政治局明确用好用足宏观政策",
        "action": "提前布局",
        "industries": ["证券", "房地产", "半导体"],
        "target_stocks": ["600030", "300059", "600048", "688981"],
        "risk": "降息落地后利多出尽风险；降息延迟则配置过早受损",
    },
    {
        "id": "C",
        "label": "消费以旧换新受益股",
        "trigger": "各省省级层面发布配套实施细则",
        "action": "右侧买入",
        "industries": ["汽车", "家电", "消费"],
        "target_stocks": ["002594", "600104", "000333", "000651"],
        "risk": "补贴落地后需求释放存在前置预收和后续乏力风险",
    },
    {
        "id": "D",
        "label": "创业板并购重组概念股",
        "trigger": "板块公司重组预期+筹码结构优化",
        "action": "关注重组预期",
        "industries": ["证券", "通信", "半导体"],
        "target_stocks": ["600030", "300059", "688981"],
        "risk": "实际重组落地存巨大不确定性，须严格筛选基本面",
    },
    {
        "id": "E",
        "label": "红利防御资产",
        "trigger": "10年期国债收益率持续走低",
        "action": "配置加仓",
        "industries": ["银行", "电力", "煤炭"],
        "target_stocks": ["601398", "600900", "601088", "601319"],
        "risk": "上行空间有限，经济强复苏+利率回升时跑输成长股",
    },
]


# ============================================================
# 土洲 — 中长期赛道红利池（Z1-Z5）
# ============================================================
EARTH_LONG_TRACKS = [
    {
        "id": "Z1",
        "label": "人工智能/智能制造",
        "driver": "十五五AI产业规模超10万亿，八部委AI+制造专项行动",
        "window": "2026-2030",
        "industries": ["半导体", "通信", "安防", "软件"],
        "target_stocks": ["002415", "601138", "300308", "688256"],
    },
    {
        "id": "Z2",
        "label": "六大新兴支柱产业",
        "driver": "到2030年产值扩大到10万亿以上，政策红利持续释放",
        "window": "2026-2030",
        "industries": ["新能源", "医药", "军工", "通信"],
        "target_stocks": ["600406", "601615", "300308", "600760"],
    },
    {
        "id": "Z3",
        "label": "新能源/电力运营",
        "driver": "双碳考核硬约束+风光装机步步高+六网电网建设推动",
        "window": "2026-2028",
        "industries": ["电力", "新能源", "基建"],
        "target_stocks": ["600406", "601615", "600900", "600905"],
    },
    {
        "id": "Z4",
        "label": "银发经济/医疗服务",
        "driver": "老龄化加速+服务消费与养老再贷款落地，消费医疗市场扩容",
        "window": "长期",
        "industries": ["医药", "消费", "保险"],
        "target_stocks": ["600276", "300760", "601319"],
    },
    {
        "id": "Z5",
        "label": "军工/卫星互联网",
        "driver": "十五五国防现代化投入+商业航天牌照审批加速+地缘风险催化",
        "window": "2026-2030",
        "industries": ["军工", "通信", "半导体"],
        "target_stocks": ["600760", "600150", "000063"],
    },
]


# ============================================================
# 月度行业五行轮动表（2026.05 — 2026.12）
# 基于丙午年火旺→生戊土股市的逻辑，按月干支推演板块轮动
# ============================================================
MONTHLY_ROTATION = [
    {
        "month": 5, "label": "巳月(金火双旺)", "ganzhi": "己巳", "solar_term": "立夏后",
        "elements": ["火", "金"],
        "bullish_industries": ["军工", "半导体", "电力", "通信", "有色", "贵金属"],
        "logic": "火旺生金(贵金属/有色)；巳火本气丙合辛金→丙辛合水(财水)，主题催化",
        "target_stocks": ["688256", "300308", "601138", "600988", "601899", "600150", "002594"],
    },
    {
        "month": 6, "label": "午月(纯粹炎火)", "ganzhi": "庚午", "solar_term": "芒种后",
        "elements": ["火"],
        "bullish_industries": ["半导体", "消费", "煤炭", "石油", "传媒", "家电"],
        "logic": "火主线上资本流+高温季节性用电需求，618电商大促催化消费",
        "target_stocks": ["688256", "605499", "601699", "603345", "000651", "000333"],
    },
    {
        "month": 7, "label": "未月(土火相生)", "ganzhi": "辛未", "solar_term": "小暑后",
        "elements": ["土", "火"],
        "bullish_industries": ["水利", "农业", "基建", "建材", "粮食安全"],
        "logic": "未为西南坤卦→藏粮于地/水利基建方向触发，土火相生利好中字头基建",
        "target_stocks": ["601668", "601390", "600585", "600031", "002007", "002714"],
    },
    {
        "month": 8, "label": "申月(金水进气)", "ganzhi": "壬申", "solar_term": "立秋后",
        "elements": ["金", "水"],
        "bullish_industries": ["汽车", "煤炭", "证券", "航运", "港口"],
        "logic": "立秋主力调仓火转金水—金(金融/贵金属/军工)+水(港口/出海贸易)秋季起爆剂",
        "target_stocks": ["002594", "601699", "600030", "601688", "601919", "600018"],
    },
    {
        "month": 9, "label": "酉月(纯金旺极)", "ganzhi": "癸酉", "solar_term": "白露后",
        "elements": ["金"],
        "bullish_industries": ["贵金属", "军工", "安防", "银行", "保险"],
        "logic": "癸水金生为财，酉金助庚金制造业，金气最旺月份",
        "target_stocks": ["600988", "601899", "600030", "600036", "601318", "600150"],
    },
    {
        "month": 10, "label": "戌月(火土相生)", "ganzhi": "丙戌", "solar_term": "寒露后",
        "elements": ["火", "土"],
        "bullish_industries": ["煤炭", "房地产", "基建", "水泥"],
        "logic": "戌为火库，丙戌上为火/下乾为天→火天大有·煤炭大涨，地产松绑预期",
        "target_stocks": ["601699", "600048", "601668", "600585", "600031"],
    },
    {
        "month": 11, "label": "亥月(冬水充足)", "ganzhi": "丁亥", "solar_term": "立冬后",
        "elements": ["水"],
        "bullish_industries": ["航运", "造船", "贸易", "酒类", "物流"],
        "logic": "丁火落地海峡概念/水旺利出海贸易，年末跨年金气行情",
        "target_stocks": ["601919", "600018", "000858", "600519", "600309"],
    },
    {
        "month": 12, "label": "子月(土水相济)", "ganzhi": "戊子", "solar_term": "大雪后",
        "elements": ["水", "土"],
        "bullish_industries": ["航运", "消费", "物流", "农业", "酒类"],
        "logic": "火转水—水为财(流动性)转向末端跨年行情，年末消费旺季",
        "target_stocks": ["601919", "600018", "601888", "000333", "000858", "600519"],
    },
]


# ============================================================
# 政策联动推演规则
# ============================================================
POLICY_INTERACTION = [
    {
        "scenario": "降准降息落地",
        "triggers": ["央行降准", "LPR下调", "OMO降息"],
        "bullish": ["证券", "半导体", "通信"],
        "bearish": ["银行"],
        "target_stocks": ["600030", "300059", "688981", "300308"],
        "description": "券商、成长科技(AI+半导体)、红利三条线受正向催化",
    },
    {
        "scenario": "美伊冲突再度升级",
        "triggers": ["中东冲突", "美伊谈判破裂", "地缘升温"],
        "bullish": ["有色", "石油"],
        "bearish": ["航运", "航空"],
        "target_stocks": ["600988", "601899", "601857"],
        "description": "黄金S1、原油F3获短期脉冲利好，科创成长股短期承压但中期逻辑不改",
    },
    {
        "scenario": "专项债发行提速+六张网配套资金下达",
        "triggers": ["专项债", "六张网", "财政支出加速"],
        "bullish": ["基建", "建材", "钢铁"],
        "bearish": [],
        "target_stocks": ["601668", "601390", "600585", "600031"],
        "description": "基建股右侧机会，螺纹钢期货空头逻辑若基建需求超预期则阶段性削弱",
    },
]


def get_policy_score(stock_industry, stock_wuxing, dominant_wuxing):
    """
    基于中国+全球策略知识库计算政策驱动力分数
    """
    score = 0.0
    matched_policies = []

    all_policy_sets = [("china", POLICY_BY_ELEMENT), ("global", GLOBAL_POLICY_BY_ELEMENT)]

    for source, policy_set in all_policy_sets:
        for element, section in policy_set.items():
            for policy in section.get("policies", []):
                if stock_industry in policy.get("industries", []):
                    weight = 1.0 if policy["direction"] == "利好" else 0.3

                    if element == dominant_wuxing:
                        weight *= 1.5
                    elif stock_wuxing == dominant_wuxing:
                        weight *= 1.2

                    score += weight
                    matched_policies.append(f"[{source}] {policy['title']}")

    return min(score, 10.0), matched_policies[:3]


def get_element_policy_weight():
    """
    返回五行维度上当前政策面的综合权重
    """
    weights = {}
    for element, section in POLICY_BY_ELEMENT.items():
        count = sum(1 for p in section.get("policies", []) if p["direction"] == "利好")
        weights[element] = count / len(section.get("policies", []))
    return weights


def get_policy_driven_stocks(dominant_wuxing, top_n=15):
    """
    返回政策面最受益的股票列表
    """
    all_stocks = set()
    result = []

    for element, section in POLICY_BY_ELEMENT.items():
        if element == dominant_wuxing:
            for policy in section.get("policies", []):
                if policy["direction"] == "利好":
                    for code in policy.get("target_stocks", []):
                        if code not in all_stocks:
                            all_stocks.add(code)
                            result.append({
                                "code": code,
                                "policy": policy["title"],
                                "element": element,
                                "industry": policy.get("industries", [None])[0],
                            })

    for element, section in POLICY_BY_ELEMENT.items():
        if element != dominant_wuxing:
            for policy in section.get("policies", []):
                if policy["direction"] == "利好":
                    for code in policy.get("target_stocks", []):
                        if code not in all_stocks:
                            all_stocks.add(code)
                            result.append({
                                "code": code,
                                "policy": policy["title"],
                                "element": element,
                                "industry": policy.get("industries", [None])[0],
                            })

    return result[:top_n]


def generate_policy_summary():
    """生成五行政策面概述"""
    lines = []
    for element in ["金", "木", "水", "火", "土"]:
        section = POLICY_BY_ELEMENT.get(element, {})
        headlines = [p["title"] for p in section.get("policies", []) if p["direction"] == "利好"]
        if headlines:
            lines.append(f"【{element}·{section.get('title', '')}】{' | '.join(headlines[:2])}")
    return "\n".join(lines)


def get_boost_level_from_policy(dominant_wuxing):
    """
    从中国+全球政策面计算五行气场等级

    综合中国政策和全球政策：
    >=80% → 旺相
    >=50% → 平和
    <40%  → 削弱
    """
    all_policies = []
    for policy_set in [POLICY_BY_ELEMENT, GLOBAL_POLICY_BY_ELEMENT]:
        section = policy_set.get(dominant_wuxing, {})
        all_policies.extend(section.get("policies", []))

    if not all_policies:
        return "平和"

    bullish_count = sum(1 for p in all_policies if p["direction"] == "利好")
    ratio = bullish_count / len(all_policies)

    if ratio >= 0.80:
        return "旺相"
    elif ratio >= 0.50:
        return "平和"
    else:
        return "削弱"


def get_global_impact(element=None):
    """获取全球政策对中国市场的影响分析"""
    impacts = []
    source = GLOBAL_POLICY_BY_ELEMENT
    elements = [element] if element else ["金", "木", "水", "火", "土"]

    for el in elements:
        section = source.get(el, {})
        region = section.get("region", "")
        for policy in section.get("policies", []):
            impact = policy.get("impact_china", "")
            if impact:
                impacts.append(f"【{el}·{region}】{policy['title']} → {impact}")

    return impacts[:8]


def generate_global_summary():
    """生成全球五大洲经济概述"""
    lines = []
    for element in ["金", "木", "水", "火", "土"]:
        section = GLOBAL_POLICY_BY_ELEMENT.get(element, {})
        region = section.get("region", "")
        title = section.get("title", "")
        headlines = [p["title"] for p in section.get("policies", [])]
        if headlines:
            lines.append(f"【{element}·{region}】{title} | {' | '.join(headlines)}")
    return "\n".join(lines)


def get_exchange_alerts():
    """获取期货交易所政策提醒"""
    return EXCHANGE_POLICIES


def get_fire_sensitive_targets():
    """获取火洲政策敏感标的"""
    return FIRE_SENSITIVE_TARGETS


def get_earth_long_tracks():
    """获取土洲中长期赛道"""
    return EARTH_LONG_TRACKS


def get_policy_interaction(trigger_keywords=None):
    """获取政策联动推演规则"""
    if not trigger_keywords:
        return POLICY_INTERACTION
    matched = []
    for rule in POLICY_INTERACTION:
        for kw in trigger_keywords:
            if kw in rule.get("triggers", []):
                matched.append(rule)
                break
    return matched


def get_sensitive_bonus(stock_code):
    """股票在火洲敏感标的中的加分"""
    for target in FIRE_SENSITIVE_TARGETS:
        if stock_code in target.get("target_stocks", []):
            return 0.8
    return 0.0


def get_long_track_bonus(stock_code):
    """股票在土洲中长期赛道中的加分"""
    for track in EARTH_LONG_TRACKS:
        if stock_code in track.get("target_stocks", []):
            return 0.6
    return 0.0


def get_futures_policy_boost(futures_name):
    """期货是否受交易所政策直接影响"""
    for policy in EXCHANGE_POLICIES:
        for affected in policy.get("affects", []):
            if affected in futures_name:
                return policy
    return None


def summarize_fire_sensitive() -> str:
    """生成火洲敏感标的一览"""
    lines = ["【火洲·政策风向敏感标的】"]
    for t in FIRE_SENSITIVE_TARGETS:
        lines.append(f"  {t['id']}. {t['label']}: {t['action']}({t['risk'][:25]})")
    return "\n".join(lines)


def summarize_earth_tracks() -> str:
    """生成土洲中长期赛道一览"""
    lines = ["【土洲·中长期赛道红利】"]
    for t in EARTH_LONG_TRACKS:
        lines.append(f"  {t['id']}. {t['label']}: {t['driver'][:35]}")
    return "\n".join(lines)


# ============================================================
# 附录一：五大洲×金木水火土政策引用索引
# ============================================================
POLICY_REFERENCE_INDEX = {
    "金": {
        "theme": "融通 — 金融资源配置与监管",
        "sources": [
            "两会十五五109项重大工程+7万亿投资",
            "创业板改革4月意见",
            "退市新规（连续20日市值<5亿直接终止上市）",
            "政治局会议定调精准有效实施更加积极的财政政策",
        ],
    },
    "木": {
        "theme": "生长 — 产业增长极",
        "sources": [
            "AI产业规模10万亿目标",
            "六大支柱产业目标（智能机器人/商业航天/新材料/生物制造等）",
            "模数共振行动：AI赋能20个重点行业",
        ],
    },
    "水": {
        "theme": "流通 — 消费与流通",
        "sources": [
            "商贸政策组合（以旧换新+消费补贴）",
            "两会与政府工作报告",
            "六张网落地窗口（物流网/水网）",
        ],
    },
    "火": {
        "theme": "转换 — 动能转换",
        "sources": [
            "政治局会议更加积极的财政政策+适度宽松货币政策",
            "货币政策前瞻性增强（预计降息10BP/降准25-50BP）",
            "碳金融顶层设计+低碳转型基金",
        ],
    },
    "土": {
        "theme": "根基 — 长期国策",
        "sources": [
            "十五五开局元年，长期产业规划主线",
            "AI/制造/新能源/军工赛道中长期红利",
            "7550亿中央预算+1万亿超长期国债",
        ],
    },
}

APRIL_PERFORMANCE = {
    "688702": {"name": "盛科通信-U", "return_4m": "+93%", "close": 322.16, "note": "以太网交换芯片稀缺标的"},
    "300308": {"name": "中际旭创", "return_4m": "+50%", "close": 857.50, "note": "市值一度破万亿，获4家券商推荐"},
    "603345": {"name": "安井食品", "return_4m": "N/A", "close": None, "note": "获5家券商推荐（全市场最多）"},
}


def get_monthly_rotation(month=None):
    """获取当前月份的行业轮动信号"""
    if month is None:
        month = datetime.now().month
    for entry in MONTHLY_ROTATION:
        if entry["month"] == month:
            return entry
    return MONTHLY_ROTATION[0]


def get_rotation_bonus(stock_code):
    """股票在当月轮动重点池中的加分"""
    entry = get_monthly_rotation()
    if entry and stock_code in entry.get("target_stocks", []):
        return 0.5
    return 0.0


def summarize_monthly_rotation() -> str:
    """生成月度轮动一览"""
    entry = get_monthly_rotation()
    if not entry:
        return "【月度轮动】暂无数据"
    lines = [
        f"【{entry['month']}月·{entry['label']}】行业五行轮动",
        f"  主导元素: {'+'.join(entry['elements'])}",
        f"  看好行业: {' | '.join(entry['bullish_industries'])}",
        f"  核心逻辑: {entry['logic']}",
    ]
    return "\n".join(lines)
