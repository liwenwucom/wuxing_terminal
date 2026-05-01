# -*- coding: utf-8 -*-
"""
五行韭菜盘 —— 全局配置模块
包含：五行映射表、节气数据、天干地支、沙雕文案库、资产标的池、上下游产业链
注释覆盖率 > 30%，方便二次修改
"""

import os
import json
import random
from datetime import datetime
from pathlib import Path

# ============================================================
# 1. 系统模式与路径
# ============================================================
SIMULATE_MODE = True  # True=模拟数据演示不联网, False=启用实时抓取
BASE_DIR = Path(__file__).parent
EVENT_LOG_PATH = BASE_DIR / "event_log.json"
CUSTOM_WUXING_YAML = BASE_DIR / "custom_wuxing.yaml"

# ============================================================
# 2. API Keys（从环境变量读取，不硬编码）
# ============================================================
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ============================================================
# 3. 五行 → 行业映射（可被 custom_wuxing.yaml 覆盖）
# ============================================================
WUXING_INDUSTRY_MAP = {
    "火": {
        "industries": ["军工", "新能源", "半导体", "能源", "煤炭", "石油", "电力", "芯片", "储能", "光伏", "汽车", "传媒"],
        "keywords": ["军工", "导弹", "战争", "冲突", "芯片", "半导体", "光伏", "新能源", "石油", "煤炭", "电力", "储能", "电池", "能源", "核能", "火箭", "汽车", "传媒", "视频", "互联网"],
        "description": "火属性行业：爆发性强，情绪驱动明显，适合短线炒作",
    },
    "金": {
        "industries": ["银行", "保险", "证券", "金融", "钢铁", "贵金属", "金属", "黄金", "家电", "通信", "有色"],
        "keywords": ["银行", "证券", "保险", "金融", "黄金", "白银", "铜", "铝", "钢铁", "稀土", "期货", "利率", "家电", "通信", "5G", "光模块"],
        "description": "金属性行业：防御性强，与货币政策高度相关",
    },
    "土": {
        "industries": ["房地产", "基建", "水泥", "建材", "工程机械", "消费"],
        "keywords": ["房地产", "基建", "水泥", "建材", "工程", "城建", "土地", "楼盘", "物业", "消费", "零售", "食品", "乳业"],
        "description": "土属性行业：周期性强，与政策刺激高度绑定",
    },
    "水": {
        "industries": ["航运", "水利", "酒类", "贸易", "物流", "港口", "渔业", "化工"],
        "keywords": ["航运", "港口", "物流", "贸易", "海运", "船舶", "水利", "白酒", "啤酒", "水运", "化工", "化学", "原料"],
        "description": "水属性行业：流动性强，受国际贸易和地缘影响大",
    },
    "木": {
        "industries": ["农业", "纺织", "医药", "生物医药", "环保", "林业", "教育"],
        "keywords": ["农业", "种业", "医药", "生物", "中药", "纺织", "服装", "环保", "教育", "林业", "棉花"],
        "description": "木属性行业：成长性强，适合中长期配置",
    },
}

# ============================================================
# 4. 期货品种 → 五行映射
# ============================================================
FUTURES_WUXING_MAP = {
    "火": {
        "contracts": ["原油", "燃料油", "沥青", "液化气", "焦炭", "焦煤", "动力煤"],
        "reason": "能源属性，燃烧即为火",
    },
    "金": {
        "contracts": ["沪金", "沪银", "沪铜", "沪铝", "沪锌", "沪镍", "沪锡", "螺纹钢", "热卷"],
        "reason": "金属属性，金曰从革",
    },
    "土": {
        "contracts": ["铁矿石", "玻璃", "橡胶", "PVC", "聚丙烯", "乙二醇", "PTA"],
        "reason": "建材化工，土爰稼穑",
    },
    "木": {
        "contracts": ["豆粕", "玉米", "棉花", "白糖", "菜油", "豆油", "棕榈油", "苹果", "红枣"],
        "reason": "农产品，木曰曲直",
    },
    "水": {
        "contracts": ["纯碱", "甲醇", "尿素", "纸浆"],
        "reason": "液体化工，水性润下",
    },
}

# ============================================================
# 5. 股票推荐池（示例，按行业分组）
# ============================================================
STOCK_POOL = {
    "A股": {
        "军工": [
            {"name": "中航沈飞", "code": "600760", "pe": 45.2, "pb": 6.8, "market_cap": "1200亿", "reason": "战斗机总装龙头"},
            {"name": "航发动力", "code": "600893", "pe": 55.0, "pb": 4.5, "market_cap": "980亿", "reason": "航空发动机唯一上市平台"},
            {"name": "中国船舶", "code": "600150", "pe": 38.5, "pb": 2.9, "market_cap": "1500亿", "reason": "船舶制造龙头"},
            {"name": "中国重工", "code": "601989", "pe": 42.0, "pb": 2.1, "market_cap": "1100亿", "reason": "海军装备龙头"},
            {"name": "中航光电", "code": "002179", "pe": 30.0, "pb": 4.5, "market_cap": "600亿", "reason": "军工连接器龙头"},
        ],
        "新能源": [
            {"name": "宁德时代", "code": "300750", "pe": 22.3, "pb": 4.1, "market_cap": "7800亿", "reason": "动力电池全球龙头"},
            {"name": "隆基绿能", "code": "601012", "pe": 14.5, "pb": 2.2, "market_cap": "1800亿", "reason": "光伏一体化龙头"},
            {"name": "比亚迪", "code": "002594", "pe": 25.8, "pb": 4.6, "market_cap": "6500亿", "reason": "新能源车+电池双轮驱动"},
            {"name": "阳光电源", "code": "300274", "pe": 18.0, "pb": 4.2, "market_cap": "1400亿", "reason": "逆变器+储能龙头"},
            {"name": "通威股份", "code": "600438", "pe": 10.0, "pb": 1.8, "market_cap": "1200亿", "reason": "硅料+电池片双龙头"},
        ],
        "银行": [
            {"name": "工商银行", "code": "601398", "pe": 5.2, "pb": 0.58, "market_cap": "1.8万亿", "reason": "宇宙行，股息率超5%"},
            {"name": "招商银行", "code": "600036", "pe": 6.8, "pb": 0.95, "market_cap": "8200亿", "reason": "零售银行标杆"},
            {"name": "建设银行", "code": "601939", "pe": 5.0, "pb": 0.55, "market_cap": "1.5万亿", "reason": "基建贷款主力"},
            {"name": "农业银行", "code": "601288", "pe": 5.0, "pb": 0.52, "market_cap": "1.3万亿", "reason": "三农金融龙头"},
        ],
        "证券": [
            {"name": "中信证券", "code": "600030", "pe": 15.2, "pb": 1.3, "market_cap": "3100亿", "reason": "券商龙头"},
            {"name": "东方财富", "code": "300059", "pe": 28.0, "pb": 4.0, "market_cap": "2800亿", "reason": "互联网券商龙头"},
            {"name": "华泰证券", "code": "601688", "pe": 12.0, "pb": 0.95, "market_cap": "1600亿", "reason": "综合券商"},
        ],
        "房地产": [
            {"name": "保利发展", "code": "600048", "pe": 8.5, "pb": 0.65, "market_cap": "1200亿", "reason": "央企地产龙头"},
            {"name": "万科A", "code": "000002", "pe": 10.0, "pb": 0.55, "market_cap": "1100亿", "reason": "地产龙头"},
        ],
        "基建": [
            {"name": "中国建筑", "code": "601668", "pe": 4.8, "pb": 0.55, "market_cap": "2200亿", "reason": "基建龙头"},
            {"name": "海螺水泥", "code": "600585", "pe": 10.2, "pb": 0.95, "market_cap": "1400亿", "reason": "水泥龙头"},
            {"name": "三一重工", "code": "600031", "pe": 15.0, "pb": 1.8, "market_cap": "1500亿", "reason": "工程机械龙头"},
            {"name": "中国中铁", "code": "601390", "pe": 5.5, "pb": 0.58, "market_cap": "1600亿", "reason": "铁路基建龙头"},
        ],
        "航运": [
            {"name": "中远海控", "code": "601919", "pe": 5.5, "pb": 0.8, "market_cap": "1800亿", "reason": "集装箱航运龙头"},
            {"name": "上港集团", "code": "600018", "pe": 12.0, "pb": 1.2, "market_cap": "1200亿", "reason": "全球最大集装箱港"},
        ],
        "医药": [
            {"name": "恒瑞医药", "code": "600276", "pe": 55.0, "pb": 6.2, "market_cap": "2800亿", "reason": "创新药龙头"},
            {"name": "片仔癀", "code": "600436", "pe": 45.0, "pb": 12.0, "market_cap": "1500亿", "reason": "中药国宝级标的"},
            {"name": "药明康德", "code": "603259", "pe": 20.0, "pb": 2.8, "market_cap": "1400亿", "reason": "CXO龙头"},
            {"name": "迈瑞医疗", "code": "300760", "pe": 30.0, "pb": 8.0, "market_cap": "3200亿", "reason": "医疗器械龙头"},
        ],
        "农业": [
            {"name": "大北农", "code": "002385", "pe": 30.5, "pb": 2.8, "market_cap": "320亿", "reason": "农业科技龙头"},
            {"name": "隆平高科", "code": "000998", "pe": 35.0, "pb": 3.2, "market_cap": "280亿", "reason": "种业龙头"},
            {"name": "牧原股份", "code": "002714", "pe": 15.0, "pb": 2.5, "market_cap": "2200亿", "reason": "生猪养殖龙头"},
        ],
        "半导体": [
            {"name": "中芯国际", "code": "688981", "pe": 40.0, "pb": 2.5, "market_cap": "3800亿", "reason": "芯片制造龙头"},
            {"name": "北方华创", "code": "002371", "pe": 35.0, "pb": 6.5, "market_cap": "1800亿", "reason": "半导体设备龙头"},
            {"name": "韦尔股份", "code": "603501", "pe": 38.0, "pb": 5.0, "market_cap": "1200亿", "reason": "CIS芯片龙头"},
            {"name": "长电科技", "code": "600584", "pe": 22.0, "pb": 2.0, "market_cap": "500亿", "reason": "封测龙头"},
        ],
        "酒类": [
            {"name": "贵州茅台", "code": "600519", "pe": 28.0, "pb": 8.5, "market_cap": "2.1万亿", "reason": "白酒绝对龙头"},
            {"name": "五粮液", "code": "000858", "pe": 20.0, "pb": 4.5, "market_cap": "5500亿", "reason": "浓香白酒龙头"},
        ],
        "煤炭": [
            {"name": "中国神华", "code": "601088", "pe": 9.0, "pb": 1.2, "market_cap": "6000亿", "reason": "煤电运一体化龙头"},
            {"name": "陕西煤业", "code": "601225", "pe": 7.0, "pb": 1.5, "market_cap": "1800亿", "reason": "优质动力煤龙头"},
        ],
        "电力": [
            {"name": "长江电力", "code": "600900", "pe": 20.0, "pb": 2.8, "market_cap": "5000亿", "reason": "水电龙头，股息稳定"},
            {"name": "华能国际", "code": "600011", "pe": 15.0, "pb": 1.2, "market_cap": "1000亿", "reason": "火电龙头"},
            {"name": "三峡能源", "code": "600905", "pe": 22.0, "pb": 2.0, "market_cap": "1500亿", "reason": "风电光伏运营龙头"},
        ],
        "钢铁": [
            {"name": "宝钢股份", "code": "600019", "pe": 12.0, "pb": 0.7, "market_cap": "1500亿", "reason": "钢铁龙头"},
            {"name": "中信特钢", "code": "000708", "pe": 14.0, "pb": 2.0, "market_cap": "800亿", "reason": "特钢龙头"},
        ],
        "汽车": [
            {"name": "上汽集团", "code": "600104", "pe": 10.0, "pb": 0.7, "market_cap": "1800亿", "reason": "汽车制造龙头"},
            {"name": "长城汽车", "code": "601633", "pe": 18.0, "pb": 2.5, "market_cap": "2000亿", "reason": "SUV+皮卡龙头"},
        ],
        "家电": [
            {"name": "美的集团", "code": "000333", "pe": 13.0, "pb": 2.5, "market_cap": "4500亿", "reason": "家电龙头"},
            {"name": "格力电器", "code": "000651", "pe": 8.0, "pb": 1.8, "market_cap": "2000亿", "reason": "空调龙头"},
        ],
        "石油": [
            {"name": "中国石油", "code": "601857", "pe": 10.0, "pb": 0.8, "market_cap": "1.5万亿", "reason": "油气龙头"},
            {"name": "中国石化", "code": "600028", "pe": 12.0, "pb": 0.75, "market_cap": "7000亿", "reason": "炼化龙头"},
        ],
        "通信": [
            {"name": "中兴通讯", "code": "000063", "pe": 16.0, "pb": 2.0, "market_cap": "1300亿", "reason": "5G设备龙头"},
            {"name": "中国移动", "code": "600941", "pe": 12.0, "pb": 1.2, "market_cap": "1.2万亿", "reason": "电信运营商龙头"},
            {"name": "中际旭创", "code": "300308", "pe": 35.0, "pb": 6.0, "market_cap": "800亿", "reason": "光模块龙头"},
        ],
        "消费": [
            {"name": "伊利股份", "code": "600887", "pe": 18.0, "pb": 3.0, "market_cap": "1800亿", "reason": "乳制品龙头"},
            {"name": "海天味业", "code": "603288", "pe": 40.0, "pb": 10.0, "market_cap": "2500亿", "reason": "调味品龙头"},
            {"name": "中国中免", "code": "601888", "pe": 25.0, "pb": 3.5, "market_cap": "1600亿", "reason": "免税龙头"},
        ],
        "传媒": [
            {"name": "分众传媒", "code": "002027", "pe": 20.0, "pb": 5.0, "market_cap": "900亿", "reason": "电梯媒体龙头"},
            {"name": "芒果超媒", "code": "300413", "pe": 28.0, "pb": 3.0, "market_cap": "500亿", "reason": "视频平台龙头"},
        ],
        "保险": [
            {"name": "中国平安", "code": "601318", "pe": 9.0, "pb": 0.9, "market_cap": "8000亿", "reason": "综合金融龙头"},
            {"name": "中国人寿", "code": "601628", "pe": 15.0, "pb": 1.5, "market_cap": "6000亿", "reason": "寿险龙头"},
        ],
        "化工": [
            {"name": "万华化学", "code": "600309", "pe": 16.0, "pb": 3.0, "market_cap": "2500亿", "reason": "MDI全球龙头"},
            {"name": "恒力石化", "code": "600346", "pe": 12.0, "pb": 1.5, "market_cap": "1000亿", "reason": "炼化一体化龙头"},
        ],
        "有色": [
            {"name": "紫金矿业", "code": "601899", "pe": 15.0, "pb": 2.5, "market_cap": "3500亿", "reason": "铜金矿龙头"},
            {"name": "北方稀土", "code": "600111", "pe": 30.0, "pb": 5.0, "market_cap": "800亿", "reason": "稀土龙头"},
        ],
    },
    "美股": {
        "科技": [
            {"name": "NVIDIA", "code": "NVDA", "pe": 42.0, "pb": 45.0, "market_cap": "$2.2T", "reason": "AI芯片之王"},
            {"name": "Microsoft", "code": "MSFT", "pe": 35.0, "pb": 12.0, "market_cap": "$3.1T", "reason": "AI+云服务龙头"},
            {"name": "Apple", "code": "AAPL", "pe": 30.0, "pb": 40.0, "market_cap": "$3.0T", "reason": "消费电子+服务生态"},
        ],
        "能源": [
            {"name": "Exxon Mobil", "code": "XOM", "pe": 12.0, "pb": 2.0, "market_cap": "$450B", "reason": "全球能源巨头"},
            {"name": "Chevron", "code": "CVX", "pe": 13.0, "pb": 1.8, "market_cap": "$280B", "reason": "综合能源龙头"},
        ],
        "金融": [
            {"name": "JPMorgan", "code": "JPM", "pe": 11.0, "pb": 1.7, "market_cap": "$500B", "reason": "全球最大银行"},
            {"name": "Goldman Sachs", "code": "GS", "pe": 14.0, "pb": 1.4, "market_cap": "$150B", "reason": "顶级投行"},
        ],
        "半导体": [
            {"name": "AMD", "code": "AMD", "pe": 50.0, "pb": 5.0, "market_cap": "$250B", "reason": "CPU+GPU双龙头"},
            {"name": "TSMC", "code": "TSM", "pe": 18.0, "pb": 5.5, "market_cap": "$600B", "reason": "全球晶圆代工霸主"},
        ],
        "医药": [
            {"name": "Pfizer", "code": "PFE", "pe": 20.0, "pb": 1.8, "market_cap": "$160B", "reason": "全球医药巨头"},
        ],
        "军工": [
            {"name": "Lockheed Martin", "code": "LMT", "pe": 16.0, "pb": 8.0, "market_cap": "$110B", "reason": "全球军工龙头"},
            {"name": "RTX Corp", "code": "RTX", "pe": 19.0, "pb": 2.3, "market_cap": "$140B", "reason": "导弹系统+航空发动机"},
        ],
        "消费": [
            {"name": "Coca-Cola", "code": "KO", "pe": 25.0, "pb": 11.0, "market_cap": "$270B", "reason": "消费品防御标的"},
        ],
    },
    "港股": {
        "科技": [
            {"name": "腾讯控股", "code": "00700", "pe": 18.0, "pb": 3.5, "market_cap": "3.5万亿港元", "reason": "互联网龙头"},
            {"name": "阿里巴巴", "code": "09988", "pe": 12.0, "pb": 1.5, "market_cap": "1.5万亿港元", "reason": "电商+云服务"},
            {"name": "美团", "code": "03690", "pe": 25.0, "pb": 4.0, "market_cap": "8000亿港元", "reason": "本地生活龙头"},
        ],
        "金融": [
            {"name": "友邦保险", "code": "01299", "pe": 15.0, "pb": 2.0, "market_cap": "7000亿港元", "reason": "亚洲保险龙头"},
            {"name": "汇丰控股", "code": "00005", "pe": 7.0, "pb": 0.8, "market_cap": "1.2万亿港元", "reason": "全球银行巨头"},
        ],
        "能源": [
            {"name": "中海油", "code": "00883", "pe": 5.0, "pb": 0.9, "market_cap": "6000亿港元", "reason": "油气开采龙头"},
        ],
        "医药": [
            {"name": "药明生物", "code": "02269", "pe": 30.0, "pb": 3.5, "market_cap": "1200亿港元", "reason": "生物药CDMO龙头"},
        ],
        "消费": [
            {"name": "安踏体育", "code": "02020", "pe": 22.0, "pb": 5.0, "market_cap": "2500亿港元", "reason": "国产运动品牌龙头"},
        ],
    },
}

# ============================================================
# 6. 上下游产业链映射
# ============================================================
SUPPLY_CHAIN = {
    "军工": {
        "upstream": ["特种钢材(抚顺特钢)", "高温合金(钢研高纳)", "碳纤维(光威复材)", "电子元器件(振华科技)"],
        "midstream": ["零部件加工", "分系统集成", "总装制造"],
        "downstream": ["国防装备", "航空航天", "船舶制造", "军贸出口"],
    },
    "新能源": {
        "upstream": ["锂矿(天齐锂业)", "钴矿(华友钴业)", "硅料(通威股份)", "稀土(北方稀土)"],
        "midstream": ["电池制造(宁德时代)", "组件生产(隆基绿能)", "逆变器(阳光电源)"],
        "downstream": ["新能源车(比亚迪)", "光伏电站", "储能系统", "充电桩"],
    },
    "半导体": {
        "upstream": ["硅片(沪硅产业)", "光刻胶(晶瑞电材)", "电子气体(华特气体)", "靶材(江丰电子)"],
        "midstream": ["芯片设计(韦尔股份)", "晶圆制造(中芯国际)", "封装测试(长电科技)"],
        "downstream": ["消费电子", "汽车电子", "AI算力", "通信设备"],
    },
    "房地产": {
        "upstream": ["土地开发", "水泥(海螺水泥)", "钢铁(宝钢股份)", "工程机械(三一重工)"],
        "midstream": ["房地产开发", "建筑工程", "装饰装修"],
        "downstream": ["物业管理", "家居消费", "家电(美的集团)", "商业运营"],
    },
    "航运": {
        "upstream": ["造船(中国船舶)", "集装箱制造(中集集团)", "燃油供应"],
        "midstream": ["集装箱航运(中远海控)", "油运(中远海能)", "干散货运输"],
        "downstream": ["港口(上港集团)", "物流仓储", "外贸企业", "跨境电商"],
    },
    "医药": {
        "upstream": ["原料药(华海药业)", "中间体", "研发服务(药明康德)", "医疗器械零部件"],
        "midstream": ["创新药研发(恒瑞医药)", "仿制药生产", "中药加工(片仔癀)", "疫苗生产"],
        "downstream": ["医院", "药店连锁", "医保支付", "健康管理"],
    },
}

# ============================================================
# 7. 节气数据
# ============================================================
SOLAR_TERMS = {
    "立春": {"month": 2, "dominant": "木", "secondary": "水", "phase": "木旺", "day_approx": 4},
    "雨水": {"month": 2, "dominant": "木", "secondary": "水", "phase": "木旺", "day_approx": 19},
    "惊蛰": {"month": 3, "dominant": "木", "secondary": "火", "phase": "木旺火生", "day_approx": 5},
    "春分": {"month": 3, "dominant": "木", "secondary": "火", "phase": "木旺火生", "day_approx": 20},
    "清明": {"month": 4, "dominant": "木", "secondary": "火", "phase": "木旺火生", "day_approx": 5},
    "谷雨": {"month": 4, "dominant": "木", "secondary": "火", "phase": "木旺火生", "day_approx": 20},
    "立夏": {"month": 5, "dominant": "火", "secondary": "木", "phase": "火旺", "day_approx": 5},
    "小满": {"month": 5, "dominant": "火", "secondary": "木", "phase": "火旺", "day_approx": 21},
    "芒种": {"month": 6, "dominant": "火", "secondary": "土", "phase": "火旺土生", "day_approx": 5},
    "夏至": {"month": 6, "dominant": "火", "secondary": "土", "phase": "火旺土生", "day_approx": 21},
    "小暑": {"month": 7, "dominant": "火", "secondary": "土", "phase": "火旺土生", "day_approx": 7},
    "大暑": {"month": 7, "dominant": "火", "secondary": "土", "phase": "火旺土生", "day_approx": 22},
    "立秋": {"month": 8, "dominant": "金", "secondary": "土", "phase": "金旺", "day_approx": 7},
    "处暑": {"month": 8, "dominant": "金", "secondary": "土", "phase": "金旺", "day_approx": 23},
    "白露": {"month": 9, "dominant": "金", "secondary": "水", "phase": "金旺水生", "day_approx": 7},
    "秋分": {"month": 9, "dominant": "金", "secondary": "水", "phase": "金旺水生", "day_approx": 23},
    "寒露": {"month": 10, "dominant": "金", "secondary": "水", "phase": "金旺水生", "day_approx": 8},
    "霜降": {"month": 10, "dominant": "金", "secondary": "水", "phase": "金旺水生", "day_approx": 23},
    "立冬": {"month": 11, "dominant": "水", "secondary": "金", "phase": "水旺", "day_approx": 7},
    "小雪": {"month": 11, "dominant": "水", "secondary": "金", "phase": "水旺", "day_approx": 22},
    "大雪": {"month": 12, "dominant": "水", "secondary": "木", "phase": "水旺木生", "day_approx": 7},
    "冬至": {"month": 12, "dominant": "水", "secondary": "木", "phase": "水旺木生", "day_approx": 21},
    "小寒": {"month": 1, "dominant": "水", "secondary": "木", "phase": "水旺木生", "day_approx": 5},
    "大寒": {"month": 1, "dominant": "水", "secondary": "木", "phase": "水旺木生", "day_approx": 20},
}

# 节气日期列表（按顺序）
SOLAR_TERM_DATES = [
    ("小寒", 1, 5), ("大寒", 1, 20),
    ("立春", 2, 4), ("雨水", 2, 19),
    ("惊蛰", 3, 5), ("春分", 3, 20),
    ("清明", 4, 5), ("谷雨", 4, 20),
    ("立夏", 5, 5), ("小满", 5, 21),
    ("芒种", 6, 5), ("夏至", 6, 21),
    ("小暑", 7, 7), ("大暑", 7, 22),
    ("立秋", 8, 7), ("处暑", 8, 23),
    ("白露", 9, 7), ("秋分", 9, 23),
    ("寒露", 10, 8), ("霜降", 10, 23),
    ("立冬", 11, 7), ("小雪", 11, 22),
    ("大雪", 12, 7), ("冬至", 12, 21),
]

# 五行生克
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天干地支列表
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
TIANGAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
DIZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

# ============================================================
# 8. 沙雕文案库
# ============================================================
SHADIAO_QUOTES = {
    "增强": {
        "stock": [
            "这票要逆天，马斯克都拦不住 🚀",
            "老天爷赏饭吃，此时不冲更待何时 💰",
            "五行加持，韭菜也能变镰刀 ⚔️",
            "天时地利人和，满仓就是干 🔥",
        ],
        "futures": [
            "多头的号角已经吹响，空头准备哭 🎺",
            "这行情，杠杆拉到顶，赢了会所嫩模 🏎️",
            "趋势来了，猪都能飞，何况你是人 🐷✈️",
        ],
        "options": [
            "买Call！买Call！买Call！重要的事说三遍 📢",
            "捡钱行情，不买期权等于白活 💎",
        ],
    },
    "当令": {
        "stock": [
            "主场作战，稳如老狗 🐕",
            "五行当令，坐等抬轿 🛋️",
            "时机正好，别人恐惧我贪婪 😎",
        ],
        "futures": [
            "顺大势，逆小势，这波稳了 🧘",
            "趋势是你的朋友，五行是你的靠山 🏔️",
        ],
        "options": [
            "卖方策略，稳稳收租 🏠",
            "波动率适中，卖跨式躺赚 💤",
        ],
    },
    "削弱": {
        "stock": [
            "今日不宜开仓，宜吃瓜 🍉",
            "别碰！这个方向是送人头 ⚠️",
            "多头进去，骨灰出来 💀",
            "忍住！管住手比啥都强 ✋",
        ],
        "futures": [
            "空头磨刀霍霍，多头痛不欲生 😭",
            "这行情，做多就是给市场送钱 💸",
            "反向操作？你确定你不是反向指标？🤡",
        ],
        "options": [
            "买Put！买Put！买入熊市价差 🐻",
            "保护性Put，守住本金就是胜利 🛡️",
        ],
    },
    "中性": {
        "stock": [
            "AI也懵了，你看着办 🤷",
            "这局面，连算命的都摇头 🔮",
            "观望也是一种操作，而且是高级操作 🧐",
        ],
        "futures": [
            "方向不明，宜小仓试水 🏊",
            "多看少动，留得青山在 🌲",
        ],
        "options": [
            "蝶式价差，不管涨跌都能赚（一点点）🦋",
            "铁鹰策略，适合这种磨人行情 🦅",
        ],
    },
}

GENERAL_SLOGANS = [
    "玄学有风险，梭哈需谨慎，本工具仅供娱乐 🎰",
    "以上分析基于玄学，如有雷同纯属巧合 🔮",
    "五行韭菜盘，让每一棵韭菜都有信仰 🌱",
    "亏了别找我，赚了记得请我喝奶茶 🧋",
]

# ============================================================
# 9. 风险提示（必须显示）
# ============================================================
RISK_WARNING = "⚠️ 玄学有风险，梭哈需谨慎。本工具仅供娱乐，不构成任何投资建议。投资有风险，入市需谨慎。根据历史回测，本金最大回撤可能超过20%，请严格控制仓位，100%保本无法保证。"

# ============================================================
# 10. 模拟新闻数据（SIMULATE_MODE=True时使用）
# ============================================================
SIMULATED_NEWS = [
    {
        "title": "中东地缘冲突持续升级 国际油价突破90美元",
        "content": "中东地区地缘冲突持续升级，国际油价突破90美元/桶。分析人士指出，如果局势进一步恶化，全球能源供应链将面临重大冲击。受此影响，煤炭、石油板块集体走强。军工板块也受到提振。",
        "source": "财联社",
        "published": "2024-04-15 08:30:00",
    },
    {
        "title": "央行宣布降准0.5个百分点 释放长期资金约1万亿",
        "content": "中国人民银行宣布下调金融机构存款准备金率0.5个百分点，释放长期资金约1万亿元。市场人士认为，此举将有效降低企业融资成本，对基建、房地产板块形成利好。",
        "source": "央行官网",
        "published": "2024-04-15 09:00:00",
    },
    {
        "title": "红海局势持续紧张 全球航运价格暴涨",
        "content": "受红海局势影响，全球航运价格持续暴涨，集装箱运价指数创年内新高。中远海控、招商轮船等航运企业盈利预期大幅上调。港口吞吐量增加带动相关港口股走强。",
        "source": "财联社",
        "published": "2024-04-15 10:00:00",
    },
    {
        "title": "美国对华半导体出口管制再度加码",
        "content": "美国政府宣布对华半导体出口管制再度加码，涉及AI芯片、光刻机等关键领域。市场分析认为，此举将加速中国半导体自主可控进程，利好国产替代概念。中芯国际、北方华创等标的关注度提升。",
        "source": "路透社",
        "published": "2024-04-15 11:00:00",
    },
    {
        "title": "全国多地出台房地产松绑政策",
        "content": "近期全国多个城市出台房地产松绑政策，包括降低首付比例、放宽限购等。分析指出，政策底已经出现，房地产市场有望企稳回升。保利发展、万科A等地产龙头估值处于历史低位。",
        "source": "证券时报",
        "published": "2024-04-15 12:00:00",
    },
]

# ============================================================
# 11. 事件类型分类
# ============================================================
EVENT_PATTERNS = {
    "地缘冲突": {"keywords": ["冲突", "战争", "导弹", "开火", "军队", "边境", "军事"], "sentiment": -0.5, "wuxing": "火"},
    "货币政策": {"keywords": ["降准", "降息", "加息", "利率", "MLF", "LPR", "准备金", "宽松", "紧缩"], "sentiment": 0.4, "wuxing": "土"},
    "能源供应": {"keywords": ["油价", "石油", "天然气", "煤炭价格", "能源危机", "减产", "OPEC"], "sentiment": 0.5, "wuxing": "火"},
    "贸易制裁": {"keywords": ["制裁", "关税", "禁运", "贸易战", "实体清单", "出口管制"], "sentiment": -0.3, "wuxing": "金"},
    "科技管制": {"keywords": ["芯片", "半导体", "光刻机", "AI限制", "技术封锁"], "sentiment": -0.2, "wuxing": "火"},
    "房地产政策": {"keywords": ["房地产", "限购", "首付", "房贷", "楼市", "房价"], "sentiment": 0.3, "wuxing": "土"},
    "航运危机": {"keywords": ["航运", "集装箱", "运价", "港口拥堵", "苏伊士", "巴拿马"], "sentiment": 0.2, "wuxing": "水"},
}

# ============================================================
# 12. 辅助函数
# ============================================================
def get_sandiao_quote(boost_level: str, asset_type: str = "stock") -> str:
    """根据增强/当令/削弱/中性 + 资产类型，随机返回一条沙雕文案"""
    quotes = SHADIAO_QUOTES.get(boost_level, SHADIAO_QUOTES["中性"])
    asset_quotes = quotes.get(asset_type, quotes.get("stock", ["🤷"]))
    return random.choice(asset_quotes)

def get_random_slogan() -> str:
    """随机返回一条系统标语"""
    return random.choice(GENERAL_SLOGANS)

def find_wuxing_by_keywords(text: str) -> dict:
    """在文本中搜索五行相关关键词"""
    result = {}
    for wuxing, info in WUXING_INDUSTRY_MAP.items():
        matched = [kw for kw in info["keywords"] if kw in text]
        if matched:
            result[wuxing] = matched
    return result

def classify_event(text: str) -> dict:
    """根据关键词分类事件类型，返回(事件类型, 情绪, 五行)"""
    for event_type, config in EVENT_PATTERNS.items():
        for kw in config["keywords"]:
            if kw in text:
                return {
                    "event_type": event_type,
                    "sentiment": config["sentiment"],
                    "wuxing": config["wuxing"],
                }
    return {"event_type": "其他", "sentiment": 0.0, "wuxing": ""}

def load_custom_config():
    """加载用户自定义五行配置（YAML），若存在则覆盖默认映射"""
    import yaml
    if CUSTOM_WUXING_YAML.exists():
        with open(CUSTOM_WUXING_YAML, "r", encoding="utf-8") as f:
            custom = yaml.safe_load(f)
            if custom:
                if "industries" in custom:
                    WUXING_INDUSTRY_MAP.update(custom["industries"])
                if "futures" in custom:
                    FUTURES_WUXING_MAP.update(custom["futures"])
                return True
    return False

def save_event_log(entry: dict):
    """保存事件记录到 event_log.json"""
    log = []
    if EVENT_LOG_PATH.exists():
        with open(EVENT_LOG_PATH, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []
    log.append(entry)
    with open(EVENT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def load_event_log() -> list:
    """加载事件记录"""
    if not EVENT_LOG_PATH.exists():
        return []
    with open(EVENT_LOG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
