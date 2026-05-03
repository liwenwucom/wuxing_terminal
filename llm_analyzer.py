# -*- coding: utf-8 -*-
"""
联网分析引擎：NewsAPI 中西新闻分离抓取 + 智谱 GLM-4-Flash 综合分析
"""

import json
import requests
from datetime import datetime

try:
    from zhipuai import ZhipuAI
    HAS_ZHIPU = True
except ImportError:
    HAS_ZHIPU = False


def _fetch_articles(news_api_key, keywords, lang, page_size=2):
    articles = []
    for kw in keywords:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": kw,
            "apiKey": news_api_key,
            "language": lang,
            "sortBy": "publishedAt",
            "pageSize": page_size,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                for a in resp.json().get("articles", []):
                    articles.append({
                        "title": a.get("title", ""),
                        "description": a.get("description") or "",
                        "source": a.get("source", {}).get("name", ""),
                        "published": (a.get("publishedAt") or "")[:10],
                    })
        except Exception as e:
            print(f"NewsAPI failed for '{kw}': {e}")

    seen = set()
    unique = []
    for art in articles:
        if art["title"] and art["title"] not in seen:
            seen.add(art["title"])
            unique.append(art)
    return unique[:10]


def fetch_economic_news(news_api_key):
    """
    返回 (china_news, global_news) 各10条
    """
    if not news_api_key:
        return [], []

    china_keywords = [
        "中国经济政策", "央行降准降息", "A股市场行情",
        "人民币汇率", "国家统计局", "财政部政策",
        "新能源汽车产业", "房地产市场调控",
        "证监会改革", "中国GDP增长",
    ]

    global_keywords = [
        "federal reserve interest rate", "global economy outlook",
        "commodity prices crude oil", "US stock market S&P 500",
        "European Central Bank inflation", "gold price",
        "emerging markets crisis", "geopolitics trade war",
        "IMF world economic", "supply chain disruption",
    ]

    china_news = _fetch_articles(news_api_key, china_keywords, "zh", page_size=2)
    global_news = _fetch_articles(news_api_key, global_keywords, "en", page_size=2)
    return china_news, global_news


def fetch_global_news(news_api_key, keywords=None, page_size=5):
    china, global_ = fetch_economic_news(news_api_key)
    return china + global_


def analyze_with_zhipu(zhipu_key, china_news, global_news, asset_type="股票"):
    """
    整合中国经济新闻 + 全球经济新闻，调用智谱 GLM-4-Flash
    asset_type: "股票" / "期货" / "期权"
    """
    if not zhipu_key or not HAS_ZHIPU:
        return {
            "sentiment": "中性",
            "confidence": 0,
            "main_drivers": [],
            "suggested_action": "缺少智谱 API Key，请在侧边栏配置",
        }

    china_text = "\n".join([f"- {n['title']}" for n in (china_news or [])[:5]])
    if not china_text.strip():
        china_text = "暂无中国经济新闻。"

    global_text = "\n".join([f"- {n['title']}" for n in (global_news or [])[:5]])
    if not global_text.strip():
        global_text = "暂无全球经济新闻。"

    prompt = f"""你是宏观经济与市场策略分析师。请基于以下中国经济新闻和全球经济新闻，对{asset_type}市场给出短期(1-5天)操作建议。

中国经济新闻（摘要）：
{china_text}

全球经济新闻（摘要）：
{global_text}

请输出JSON，不要有多余解释：
{{
    "sentiment": "看多/看空/中性",
    "confidence": 0-100的整数,
    "main_drivers": ["驱动因素1", "驱动因素2"],
    "suggested_action": "具体操作建议(例如:买入A股消费龙头/做多原油期货/买入虚值看跌期权避险)"
}}"""

    try:
        client = ZhipuAI(api_key=zhipu_key)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result = response.choices[0].message.content
        start = result.find("{")
        end = result.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(result[start:end])
        return {
            "sentiment": "中性",
            "confidence": 50,
            "main_drivers": [],
            "suggested_action": "模型返回格式异常",
        }
    except Exception as e:
        return {
            "sentiment": "中性",
            "confidence": 0,
            "main_drivers": [],
            "suggested_action": f"分析出错: {str(e)}",
        }


def generate_networked_report(news_key, zhipu_key):
    """生成完整联网分析报告（中西新闻分离 + AI综合分析）"""
    china_news, global_news = fetch_economic_news(news_key)

    if not china_news and not global_news:
        return {
            "mode": "networked",
            "error": "未能获取新闻，请检查 NewsAPI Key 或网络连接",
            "china_news": [],
            "global_news": [],
            "stocks": None,
            "futures": None,
            "options": None,
        }

    return {
        "mode": "networked",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "china_news_count": len(china_news),
        "global_news_count": len(global_news),
        "china_news": china_news,
        "global_news": global_news,
        "stocks": analyze_with_zhipu(zhipu_key, china_news, global_news, "股票"),
        "futures": analyze_with_zhipu(zhipu_key, china_news, global_news, "期货"),
        "options": analyze_with_zhipu(zhipu_key, china_news, global_news, "期权"),
    }
