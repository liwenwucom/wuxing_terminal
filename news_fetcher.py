# -*- coding: utf-8 -*-
"""
全球新闻抓取与解析引擎 v2.0
- 每5分钟自动刷新缓存
- 全球源：Reuters, Bloomberg, CNBC, MarketWatch, Investing.com
- 中国源：财联社, 东方财富, 同花顺, 新浪财经
- 解析：行业、五行属性、情绪评分、影响市场、国家/地区标签
"""

import re
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta

from config import (
    SIMULATE_MODE, SIMULATED_NEWS, NEWSAPI_KEY,
    find_wuxing_by_keywords, classify_event,
    WUXING_INDUSTRY_MAP, EVENT_PATTERNS,
)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ============================================================
# 全球新闻缓存（5分钟过期）
# ============================================================
_NEWS_CACHE = {"data": [], "last_fetch": 0, "lock": threading.Lock()}
_CACHE_TTL = 300  # 5分钟 = 300秒

GLOBAL_NEWS_SOURCES = {
    "Reuters": "https://www.reuters.com/world/rss",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories",
    "Investing": "https://www.investing.com/rss/news.rss",
    "Bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "YahooFinance": "https://finance.yahoo.com/news/rssindex",
}

CHINA_NEWS_SOURCES = {
    "财联社": "https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=8.4.6",
    "东方财富": "https://np-listapi.eastmoney.com/comm/web/getNewsList",
    "新浪财经": "https://feedx.net/rss/sinafinance.xml",
}


# ============================================================
# 事件→国家/地区映射（辅助全球分析）
# ============================================================
REGION_PATTERNS = {
    "美国": ["美联储", "Fed", "华尔街", "Wall Street", "NASDAQ", "NYSE", "白宫", "White House"],
    "中国": ["央行", "发改委", "国务院", "证监会", "人民币", "沪深", "A股"],
    "欧洲": ["ECB", "欧洲央行", "欧盟", "EU", "欧元区", "Eurozone", "德国", "法国"],
    "中东": ["OPEC", "沙特", "伊朗", "以色列", "中东", "红海", "波斯湾"],
    "日本": ["日本央行", "BOJ", "日经", "Nikkei", "日元"],
    "新兴市场": ["印度", "巴西", "俄罗斯", "东南亚", "越南"],
}

# ============================================================
# 全局事件关键词（英文）
# ============================================================
GLOBAL_EVENT_PATTERNS = {
    "geopolitical": {
        "keywords": ["war", "conflict", "missile", "military", "sanction", "border", "invasion", "tension"],
        "sentiment": -0.5, "wuxing": "火",
    },
    "monetary": {
        "keywords": ["rate hike", "rate cut", "interest rate", "fed", "ecb", "inflation", "cpi", "ppi", "tightening", "easing", "qe"],
        "sentiment": 0.3, "wuxing": "土",
    },
    "energy": {
        "keywords": ["oil price", "crude", "opec", "natural gas", "energy crisis", "barrel", "brent", "wti"],
        "sentiment": 0.5, "wuxing": "火",
    },
    "tech_sanction": {
        "keywords": ["chip ban", "semiconductor", "export control", "ai regulation", "technology ban", "nvidia", "tsmc"],
        "sentiment": -0.2, "wuxing": "火",
    },
    "supply_chain": {
        "keywords": ["supply chain", "shortage", "logistics", "shipping cost", "container", "freight", "port congestion"],
        "sentiment": -0.2, "wuxing": "水",
    },
    "commodity": {
        "keywords": ["gold price", "copper", "iron ore", "steel", "metal", "commodity rally", "silver", "lithium"],
        "sentiment": 0.3, "wuxing": "金",
    },
    "earnings": {
        "keywords": ["earnings", "revenue", "profit", "beat estimate", "miss estimate", "guidance", "quarterly result"],
        "sentiment": 0.2, "wuxing": "",
    },
}


def _is_cache_valid() -> bool:
    """检查缓存是否在5分钟内有效"""
    return (time.time() - _NEWS_CACHE["last_fetch"]) < _CACHE_TTL


def fetch_global_news(max_items: int = 20) -> list:
    """主入口：全球新闻抓取（带5分钟缓存）"""
    with _NEWS_CACHE["lock"]:
        if _NEWS_CACHE["data"] and _is_cache_valid():
            return _NEWS_CACHE["data"][:max_items]

    if SIMULATE_MODE:
        result = SIMULATED_NEWS[:max_items]
        _NEWS_CACHE["data"] = result
        _NEWS_CACHE["last_fetch"] = time.time()
        return result

    all_news = []

    # 全球英文源
    en_news = fetch_global_rss(max_items=max_items)
    all_news.extend(en_news)

    # 中国中文源
    cn_news = fetch_china_news(max_items=max_items)
    all_news.extend(cn_news)

    # API源
    if NEWSAPI_KEY:
        api_news = fetch_newsapi(max_items=max_items)
        all_news.extend(api_news)

    if not all_news:
        all_news = SIMULATED_NEWS[:max_items]

    # 去重
    seen = set()
    deduped = []
    for n in all_news:
        key = hashlib.md5((n.get("title", "") + n.get("content", "")[:50]).encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            deduped.append(n)

    _NEWS_CACHE["data"] = deduped
    _NEWS_CACHE["last_fetch"] = time.time()
    return deduped[:max_items]


def fetch_global_rss(max_items: int = 15) -> list:
    """抓取全球英文RSS源"""
    if not HAS_FEEDPARSER:
        return []
    items = []
    for source_name, url in GLOBAL_NEWS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                items.append({
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", entry.get("description", "")),
                    "source": source_name,
                    "region": detect_region(entry.get("title", "")),
                    "published": entry.get("published", ""),
                })
        except Exception:
            continue
    return items


def fetch_china_news(max_items: int = 15) -> list:
    """抓取中国财经新闻"""
    items = []

    # 财联社API
    try:
        if HAS_REQUESTS:
            resp = requests.get(
                "https://www.cls.cn/api/sw",
                params={"app": "CailianpressWeb", "os": "web", "sv": "8.4.6"},
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.cls.cn/"},
                timeout=10,
            )
            data = resp.json()
            for item in data.get("data", {}).get("roll_data", [])[:max_items]:
                items.append({
                    "title": item.get("title", ""),
                    "content": item.get("brief", item.get("title", "")),
                    "source": "财联社",
                    "region": "中国",
                    "published": item.get("ctime", ""),
                })
    except Exception:
        pass

    # 东方财富
    try:
        if HAS_REQUESTS and items:
            resp = requests.get(
                "https://np-listapi.eastmoney.com/comm/web/getNewsList",
                params={"client": "web", "biz": "web_news", "columnCode": "yw", "pageIndex": 1, "pageSize": 10},
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.eastmoney.com/"},
                timeout=10,
            )
            data = resp.json()
            for item in data.get("data", {}).get("list", [])[:max_items]:
                items.append({
                    "title": item.get("title", ""),
                    "content": item.get("digest", item.get("title", "")),
                    "source": "东方财富",
                    "region": "中国",
                    "published": item.get("showTime", ""),
                })
    except Exception:
        pass

    return items


def fetch_newsapi(max_items: int = 10) -> list:
    """从 NewsAPI 抓取全球新闻"""
    if not HAS_REQUESTS or not NEWSAPI_KEY:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "stock OR oil OR gold OR semiconductor OR bank OR real estate OR shipping OR technology OR war OR central bank OR commodity OR futures",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_items,
            "apiKey": NEWSAPI_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if data.get("status") != "ok":
            return []
        items = []
        for article in data.get("articles", []):
            items.append({
                "title": article.get("title", ""),
                "content": article.get("description", "") or article.get("title", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "region": detect_region(article.get("title", "")),
                "published": article.get("publishedAt", ""),
            })
        return items
    except Exception:
        return []


def detect_region(text: str) -> str:
    """自动检测新闻归属地区"""
    for region, keywords in REGION_PATTERNS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                return region
    return "全球"


def parse_news(news_item: dict) -> dict:
    """解析单条新闻：行业、五行、情绪、事件类型、区域标签"""
    title = news_item.get("title", "")
    content = news_item.get("content", "")
    combined_text = f"{title} {content}".lower()

    # 中文事件分类
    event_info = classify_event(f"{title} {content}")

    # 英文全球事件分类
    global_event = classify_global_event(combined_text)
    if global_event and not event_info.get("wuxing"):
        event_info = global_event

    # 五行关键词匹配
    wuxing_hits = find_wuxing_by_keywords(f"{title} {content}")

    # 确定主五行
    main_wuxing = event_info.get("wuxing", "")
    if not main_wuxing and wuxing_hits:
        main_wuxing = max(wuxing_hits, key=lambda k: len(wuxing_hits[k]))

    # 确定行业
    industries = set()
    if main_wuxing and main_wuxing in WUXING_INDUSTRY_MAP:
        industries.update(WUXING_INDUSTRY_MAP[main_wuxing]["industries"])
    for w in wuxing_hits:
        if w in WUXING_INDUSTRY_MAP:
            industries.update(WUXING_INDUSTRY_MAP[w]["industries"])

    # 情绪评分
    sentiment = event_info.get("sentiment", 0.0)
    if sentiment == 0.0:
        sentiment = analyze_sentiment_global(combined_text)

    return {
        "title": title,
        "content": content[:200],
        "source": news_item.get("source", "未知"),
        "region": news_item.get("region", detect_region(title)),
        "published": news_item.get("published", ""),
        "event_type": event_info.get("event_type", "其他"),
        "wuxing": main_wuxing or "未匹配",
        "industries": sorted(industries),
        "sentiment_score": round(sentiment, 2),
        "wuxing_detail": {w: matched for w, matched in wuxing_hits.items()} if wuxing_hits else {},
    }


def classify_global_event(text: str) -> dict:
    """英文全球事件分类"""
    text_lower = text.lower()
    for event_type, config in GLOBAL_EVENT_PATTERNS.items():
        for kw in config["keywords"]:
            if kw in text_lower:
                return {
                    "event_type": event_type,
                    "sentiment": config["sentiment"],
                    "wuxing": config["wuxing"],
                }
    return {}


def analyze_sentiment_global(text: str) -> float:
    """中英双语情绪分析"""
    bullish_cn = ["暴涨", "大涨", "利好", "增长", "突破", "创新高", "超预期", "降准", "降息", "宽松", "涨价", "供不应求", "走强", "反弹"]
    bearish_cn = ["暴跌", "大跌", "利空", "下滑", "下降", "制裁", "风险", "危机", "减产", "停产", "亏损", "加息", "紧缩", "通胀", "恐慌"]
    bullish_en = ["surge", "rally", "bullish", "beat", "upgrade", "outperform", "record high", "boost", "stimulus", "recovery"]
    bearish_en = ["plunge", "crash", "bearish", "downgrade", "underperform", "recession", "crisis", "default", "sell-off", "panic"]

    score = 0
    for kw in bullish_cn + bullish_en:
        if kw.lower() in text.lower():
            score += 1
    for kw in bearish_cn + bearish_en:
        if kw.lower() in text.lower():
            score -= 1

    if score >= 3:
        return 1.0
    elif score >= 1:
        return 0.6
    elif score <= -3:
        return -1.0
    elif score <= -1:
        return -0.5
    return 0.0


def fetch_and_parse(max_items: int = 20) -> list:
    """一站式：全球抓取 + 解析"""
    raw_news = fetch_global_news(max_items=max_items)
    parsed = []
    for item in raw_news:
        if "error" in item:
            continue
        parsed.append(parse_news(item))
    return parsed if parsed else [parse_news(n) for n in SIMULATED_NEWS[:max_items]]


def get_cache_age() -> float:
    """获取缓存年龄（秒）"""
    return time.time() - _NEWS_CACHE["last_fetch"]


def force_refresh():
    """强制刷新新闻缓存"""
    with _NEWS_CACHE["lock"]:
        _NEWS_CACHE["last_fetch"] = 0
        _NEWS_CACHE["data"] = []


# 别名兼容
fetch_news = fetch_global_news
