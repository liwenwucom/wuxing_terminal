# -*- coding: utf-8 -*-
"""
五行韭菜盘 —— Streamlit 主入口
全球宏观玄学交易助手
运行：streamlit run main.py
"""

import sys
import os
from datetime import datetime

import streamlit as st
import pandas as pd

# 页面配置
st.set_page_config(
    page_title="五行韭菜盘 | 玄学交易助手",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 导入本地模块
# ============================================================
from config import (
    SIMULATE_MODE, RISK_WARNING,
    WUXING_INDUSTRY_MAP, FUTURES_WUXING_MAP,
    load_custom_config,
)
from five_elements import (
    get_current_solar_term, get_ganzhi_info,
    analyze_wuxing_boost, get_wuxing_market_color,
)
from news_fetcher import fetch_and_parse, parse_news, force_refresh, get_cache_age
from stock_picker import pick_stocks
from futures_picker import pick_futures
from options_picker import pick_options
from backtest import calculate_win_rate, record_event
from reporter import build_report
from auto_trader import generate_daily_report, load_today_report, load_historical_reports, start_auto_refresh
from llm_analyzer import generate_networked_report, fetch_global_news
from bazi_picker import (
    generate_bazi_report, format_bazi_report,
    generate_forward_report, format_forward_report,
)
from bazi_live_scanner import (
    generate_live_daily_report, format_live_report,
    get_popularity_info, GOLD_STOCK_POPULARITY_2026_05,
    BROKER_GOLD_POOL_2026_05, DATA_SOURCES,
)
from futures_bazi_picker import (
    generate_futures_bazi_report, format_futures_bazi_report,
    generate_futures_forward_report, format_futures_forward_report,
    FUTURES_CAPACITY_STAR_MAP,
    get_monthly_futures_direction,
    FUTURES_DATA_SOURCES_REFERENCE,
    generate_futures_top10, format_futures_top10_table,
)
from futures_picker import (
    FUTURES_IPO_DATE_MAP, FUTURES_BAZI_BASE, CHINA_FUTURES_POOL,
    OPTION_BUYER_SELLER_MATRIX, search_futures,
    get_main_contract,
)
from stock_bazi_scanner import (
    generate_stock_top10, format_stock_top10_table,
    scan_all_stocks_daily, scan_stock_triple_resonance,
    generate_stock_diwang_detail, STOCK_SECTOR_WUXING,
    _resolve_stock_name, _resolve_stock_sector,
    _resolve_stock_wuxing, STOCK_CAPACITY_STAR_MAP,
)


def _futures_name_for_ui(symbol):
    for exchange, contracts in CHINA_FUTURES_POOL.items():
        for c in contracts:
            if c["symbol"] == symbol:
                return f"({c['name']})"
    return ""


# ============================================================
# 标题与气场展示
# ============================================================
def render_header():
    """渲染页面顶部：标题+五行气场"""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("🔮 五行韭菜盘")
        st.caption("全球宏观玄学交易助手 —— 让每一棵韭菜都有信仰")

    term = get_current_solar_term()
    ganzhi = get_ganzhi_info()

    with col2:
        wuxing_color = get_wuxing_market_color(term["dominant_wuxing"])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                    border-radius: 12px; padding: 16px; text-align: center;
                    border: 1px solid {wuxing_color};">
            <div style="font-size: 14px; color: #aaa;">当前节气</div>
            <div style="font-size: 28px; font-weight: bold; color: {wuxing_color};">
                {term['name']}
            </div>
            <div style="font-size: 14px; color: #ccc;">{term['phase']}</div>
            <div style="font-size: 12px; color: #888;">主导五行：{term['dominant_wuxing']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                    border-radius: 12px; padding: 16px; text-align: center;
                    border: 1px solid #666;">
            <div style="font-size: 14px; color: #aaa;">今日干支</div>
            <div style="font-size: 28px; font-weight: bold; color: #e0c068;">
                {ganzhi.get('day_ganzhi', '')}
            </div>
            <div style="font-size: 14px; color: #ccc;">
                日五行：{ganzhi.get('day_wuxing', '')}
            </div>
            <div style="font-size: 12px; color: #888;">
                {ganzhi.get('year_ganzhi', '')}年
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")


# ============================================================
# 侧边栏配置
# ============================================================
def render_sidebar():
    """渲染侧边栏：配置项（API Key 持久化在 session_state）"""
    with st.sidebar:
        st.header("⚙️ 配置")

        st.subheader("系统模式")
        system_mode = st.radio(
            "分析模式",
            ["五行模式", "联网模式"],
            index=0,
            help="五行模式=玄学算卦(离线)；联网模式=NewsAPI新闻+智谱AI分析(需API Key)",
        )

        if system_mode == "联网模式":
            newsapi_key = st.text_input(
                "NewsAPI Key", type="password",
                value=st.session_state.get("newsapi_key", ""),
                placeholder="https://newsapi.org/ 免费注册",
                help="联网模式必需",
            )
            zhipu_key = st.text_input(
                "智谱 AI Key", type="password",
                value=st.session_state.get("zhipu_key", ""),
                placeholder="https://open.bigmodel.cn/ 免费注册",
                help="GLM-4-Flash 免费2000万tokens/月",
            )
            st.session_state["newsapi_key"] = newsapi_key
            st.session_state["zhipu_key"] = zhipu_key
            openai_key = ""
            sim_mode = False
        else:
            newsapi_key = st.session_state.get("newsapi_key", "")
            zhipu_key = st.session_state.get("zhipu_key", "")
            openai_key = st.text_input(
                "OpenAI/DeepSeek Key", type="password",
                placeholder="留空则使用规则引擎",
                help="用于增强五行模式的新闻情绪解析",
            )
            sim_mode = st.checkbox(
                "模拟模式（不联网）", value=SIMULATE_MODE,
                help="开启后使用内置模拟数据",
            )

        st.markdown("---")

        show_stocks = st.checkbox("股票分析", value=True)
        show_futures = st.checkbox("期货分析", value=True)
        show_options = st.checkbox("期权策略", value=True,
                                   help="基于股票/期货推荐生成期权策略")

        risk_level = st.radio("风险偏好", ["moderate", "aggressive"],
                              index=0,
                              help="moderate=稳健策略, aggressive=激进策略")

        market = st.selectbox("股票市场", ["A股", "美股", "港股"],
                              help="五行模式生效")

        preferred_wuxing = st.selectbox(
            "偏好五行", ["自动", "火", "金", "土", "水", "木"],
            help="五行模式生效",
        )

        st.markdown("---")
        st.caption(f"v3.0 | 当前: {system_mode}")
        st.caption("玄学有风险，梭哈需谨慎")

        return {
            "system_mode": system_mode,
            "sim_mode": sim_mode,
            "newsapi_key": newsapi_key,
            "zhipu_key": zhipu_key,
            "openai_key": openai_key,
            "show_stocks": show_stocks,
            "show_futures": show_futures,
            "show_options": show_options,
            "preferred_wuxing": preferred_wuxing,
            "risk_level": risk_level,
            "market": market,
        }


# ============================================================
# 新闻输入区域
# ============================================================
def render_news_input():
    """渲染新闻输入区域：手动输入 或 自动抓取"""
    st.subheader("📰 新闻输入")

    tab1, tab2 = st.tabs(["手动输入", "自动抓取"])

    with tab1:
        news_text = st.text_area(
            "输入新闻内容（标题+正文）",
            height=120,
            placeholder="例如：中东地缘冲突持续升级，国际油价突破90美元/桶，能源和军工板块受到提振...",
            key="manual_news",
        )
        return {"mode": "manual", "text": news_text}

    with tab2:
        col1, col2 = st.columns([1, 3])
        with col1:
            fetch_btn = st.button("🔄 自动抓取最新新闻", type="primary", use_container_width=True)
        with col2:
            st.caption("将自动从财联社/RSS抓取最新财经要闻并逐条分析")

        if fetch_btn:
            with st.spinner("正在抓取新闻..."):
                return {"mode": "auto", "fetch": True}

        return {"mode": "auto", "fetch": False}


# ============================================================
# 分析卡片渲染
# ============================================================
def render_analysis_card(report: dict):
    """渲染单个分析结果卡片"""

    boost_level = report.get("boost_level", "中性")
    wuxing = report.get("wuxing", "")

    # 五行对应的emoji和颜色
    wuxing_icons = {"火": "🔥", "金": "💎", "土": "🏗️", "水": "💧", "木": "🌿"}
    icon = wuxing_icons.get(wuxing, "🔮")

    # --- 第一行：核心判定 ---
    st.markdown(f"### {icon} {report.get('news_summary', '')[:60]}...")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("五行属性", f"{icon} {wuxing}")
    with col2:
        delta_str = f"{report.get('sentiment_score', 0):+.1f}"
        st.metric("情绪评分", delta_str,
                  delta="利好" if report.get('sentiment_score', 0) > 0 else "利空")
    with col3:
        boost = report.get("boost_level", "")
        boost_delta = "↑" if boost in ("增强", "当令") else "↓" if "削弱" in boost else "→"
        st.metric("五行气场", boost, delta=boost_delta)
    with col4:
        score = report.get("total_score", 0)
        st.metric("综合评分", f"{score:.2%}" if score <= 1 else f"{score:.3f}")
    with col5:
        action = report.get("action", "")
        st.metric("操作建议", action)

    # --- 沙雕点评 ---
    sandiao = report.get("sandiao_stock", "")
    if sandiao:
        st.info(f"💬 **沙雕点评**：{sandiao}")

    # --- 胜率 ---
    winrate = report.get("win_rate", {})
    if winrate and "multi_period" in winrate:
        st.markdown("#### 🎯 玄学胜率（模拟回测）")
        periods = winrate["multi_period"]
        wr_cols = st.columns(3)
        for i, (label, val) in enumerate(periods.items()):
            with wr_cols[i]:
                st.metric(label, val)
        st.caption(winrate.get("note", ""))

    # --- 逻辑推导 ---
    with st.expander("📖 逻辑推导 & 节气分析", expanded=False):
        st.markdown(f"**节气判断**：{report.get('term_name', '')} | {report.get('term_phase', '')}")
        st.markdown(f"**干支**：{report.get('ganzhi', '')}")
        st.markdown(f"**增强/削弱**：{report.get('boost_detail', '')}")
        st.markdown(f"**股票逻辑**：{report.get('stock_logic', '')}")
        if report.get("futures_logic"):
            st.markdown(f"**期货逻辑**：{report.get('futures_logic', '')}")
        if report.get("options_logic"):
            st.markdown(f"**期权逻辑**：{report.get('options_logic', '')}")

    # --- 推荐股票 ---
    stocks = report.get("stocks", [])
    if stocks:
        st.markdown("#### 📈 推荐股票")
        stock_data = []
        for s in stocks:
            stock_data.append({
                "名称": s.get("name", ""),
                "代码": s.get("code", ""),
                "行业": s.get("matched_industry", ""),
                "PE": s.get("pe", s.get("realtime_pe", "N/A")),
                "PB": s.get("pb", s.get("realtime_pb", "N/A")),
                "市值": s.get("market_cap", "N/A"),
                "推荐理由": s.get("reason", ""),
            })
        st.dataframe(pd.DataFrame(stock_data), use_container_width=True, hide_index=True)

        # 上下游展开
        for s in stocks:
            chain = s.get("supply_chain", {})
            if chain and chain.get("upstream"):
                with st.expander(f"🔗 上下游：{s.get('name', '')} ({s.get('matched_industry', '')})"):
                    st.markdown(f"**上游**：{'、'.join(chain.get('upstream', []))}")
                    st.markdown(f"**中游**：{'、'.join(chain.get('midstream', []))}")
                    st.markdown(f"**下游**：{'、'.join(chain.get('downstream', []))}")

    # --- 推荐期货 ---
    futures = report.get("futures", [])
    if futures:
        st.markdown("#### 📉 推荐期货")
        fut_data = []
        for f in futures:
            fut_data.append({
                "品种": f.get("name", ""),
                "合约代码": f.get("symbol", ""),
                "方向": f.get("direction", ""),
                "基差": f.get("basis", ""),
                "持仓": f.get("open_interest", ""),
            })
        st.dataframe(pd.DataFrame(fut_data), use_container_width=True, hide_index=True)

    # --- 推荐期权策略 ---
    options = report.get("options", [])
    if options:
        st.markdown("#### 🎲 期权策略")
        st.info(f"**策略**：{report.get('options_logic', '')}")
        opt_data = []
        for o in options:
            opt_data.append({
                "标的": o.get("underlying", ""),
                "策略": o.get("strategy", ""),
                "IV": o.get("iv_estimate", ""),
                "建议月份": o.get("suggested_month", ""),
            })
        st.dataframe(pd.DataFrame(opt_data), use_container_width=True, hide_index=True)

    # --- 风险提示 ---
    risks = report.get("risks", [])
    if risks:
        with st.expander("⚠️ 风险提示", expanded=len(risks) > 1):
            for r in risks:
                st.warning(r)

    # --- 底部免责 ---
    st.caption(report.get("slogan", ""))

    st.markdown("---")


# ============================================================
# 主分析流水线
# ============================================================
def run_analysis(news_text: str, config: dict) -> dict:
    """执行完整分析流水线"""

    # 1. 新闻解析
    parsed = parse_news({"title": "", "content": news_text})

    # 2. 五行算卦
    boost = analyze_wuxing_boost(parsed["wuxing"])

    # 3. 股票推荐
    market = config.get("market", "A股")
    stock_result = pick_stocks(parsed["industries"], parsed["wuxing"], market)

    # 4. 期货推荐
    futures_result = None
    if config.get("show_futures"):
        futures_result = pick_futures(parsed["wuxing"], boost["boost_level"])

    # 5. 期权策略
    options_result = None
    if config.get("show_options"):
        stocks_for_options = stock_result.get("stocks", [])
        options_result = pick_options(
            boost["boost_level"],
            stocks_for_options,
            config.get("risk_level", "moderate"),
        )

    # 6. 胜率
    winrate = calculate_win_rate(
        parsed["wuxing"],
        parsed["event_type"],
    )

    # 7. 整合报告
    report = build_report(
        parsed, boost, stock_result,
        futures_result, options_result, winrate,
    )

    # 8. 记录事件
    record_event(news_text, report)

    return report


def run_batch_analysis(news_items: list, config: dict):
    """批量分析多条新闻"""
    for i, item in enumerate(news_items):
        text = item.get("content", "") or item.get("title", "")
        if not text:
            continue
        st.markdown(f"## 分析 #{i+1}: {item.get('title', '')[:40]}...")
        with st.spinner(f"正在算第{i+1}卦..."):
            report = run_analysis(text, config)
            render_analysis_card(report)

    st.warning(RISK_WARNING)


# ============================================================
# 自动日推仪表盘
# ============================================================
def render_daily_dashboard(config=None):
    """双模式日推仪表盘：五行模式 / 联网模式"""

    system_mode = config.get("system_mode", "五行模式") if config else "五行模式"
    now = datetime.now()
    cache_age = get_cache_age()

    if system_mode == "联网模式":
        _render_networked_dashboard(config, now, cache_age)
    else:
        _render_wuxing_dashboard(config, now, cache_age)


def _render_networked_dashboard(config, now, cache_age):
    """联网模式：中西新闻分离 + 智谱 AI 综合分析"""
    st.markdown("## 🌐 今日自动日推 — 全球宏观联网版")

    col_state1, col_state2, col_state3, col_state4 = st.columns(4)
    with col_state1:
        st.metric("系统状态", "运行中" if cache_age < 360 else "待刷新",
                  delta=f"缓存{cache_age:.0f}s前")
    with col_state2:
        st.metric("当前时间", now.strftime("%H:%M:%S"), delta=now.strftime("%Y-%m-%d"))
    with col_state3:
        st.metric("市场", "全球", delta="NewsAPI + ZhipuAI")
    with col_state4:
        st.metric("模式", "联网-AI分析", delta="GLM-4-Flash")

    st.markdown("---")

    news_key = config.get("newsapi_key", "")
    zhipu_key = config.get("zhipu_key", "")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🌍 抓取中西新闻并AI分析", type="primary", use_container_width=True):
            if not news_key:
                st.error("请先在侧边栏输入 NewsAPI Key")
            elif not zhipu_key:
                st.error("请先在侧边栏输入智谱 AI Key")
            else:
                with st.spinner("抓取中国经济新闻 + 全球经济新闻 → 调用智谱AI综合分析 → 生成策略..."):
                    networked_report = generate_networked_report(news_key, zhipu_key)

                    if networked_report.get("error"):
                        st.warning(networked_report["error"])
                    else:
                        st.session_state["networked_report"] = networked_report
                        cn = networked_report.get('china_news_count', 0)
                        gl = networked_report.get('global_news_count', 0)
                        st.success(f"分析完成！中国经济新闻 {cn}条 + 全球经济新闻 {gl}条")
                        st.rerun()

    with col_btn2:
        if st.button("🔄 重新分析", use_container_width=True):
            if "networked_report" in st.session_state:
                del st.session_state["networked_report"]
            st.rerun()

    networked_report = st.session_state.get("networked_report")

    if not networked_report:
        st.info("点击「抓取中西新闻并AI分析」按钮，获取中国经济+全球经济双视角AI交易策略。")
        st.markdown("---")
        st.caption("需要: NewsAPI Key + 智谱 API Key")
        return

    st.markdown("---")

    china_news = networked_report.get("china_news", [])
    global_news = networked_report.get("global_news", [])

    col_cn, col_gl = st.columns(2)
    with col_cn:
        st.markdown(f"#### 🇨🇳 中国经济新闻 ({len(china_news)}条)")
        if china_news:
            for i, n in enumerate(china_news):
                st.markdown(f"**{i+1}.** {n['title']}<br><small>{n['source']} | {n.get('published','')}</small>",
                            unsafe_allow_html=True)
        else:
            st.caption("未抓取到中国经济新闻")

    with col_gl:
        st.markdown(f"#### 🌍 全球经济新闻 ({len(global_news)}条)")
        if global_news:
            for i, n in enumerate(global_news):
                st.markdown(f"**{i+1}.** {n['title']}<br><small>{n['source']} | {n.get('published','')}</small>",
                            unsafe_allow_html=True)
        else:
            st.caption("未抓取到全球经济新闻")

    st.markdown("---")
    st.markdown("### 🧠 智谱 GLM-4-Flash 双视角综合分析")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📊 股票市场")
        stock = networked_report.get("stocks", {})
        if stock:
            sentiment = stock.get("sentiment", "N/A")
            conf = stock.get("confidence", 0)
            sentiment_color = "#00cc66" if "看多" in str(sentiment) else ("#ff4444" if "看空" in str(sentiment) else "#999")
            st.markdown(f"""
            <div style="border-left: 4px solid {sentiment_color}; padding: 0 12px;">
            <h4 style="margin:0;color:{sentiment_color}">{sentiment}</h4>
            <p>置信度: <b>{conf}%</b></p>
            <p>{stock.get('suggested_action', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            for d in stock.get("main_drivers", []):
                st.caption(f"• {d}")

    with col2:
        st.markdown("#### 📉 期货市场")
        futures = networked_report.get("futures", {})
        if futures:
            sentiment = futures.get("sentiment", "N/A")
            conf = futures.get("confidence", 0)
            sentiment_color = "#00cc66" if "看多" in str(sentiment) else ("#ff4444" if "看空" in str(sentiment) else "#999")
            st.markdown(f"""
            <div style="border-left: 4px solid {sentiment_color}; padding: 0 12px;">
            <h4 style="margin:0;color:{sentiment_color}">{sentiment}</h4>
            <p>置信度: <b>{conf}%</b></p>
            <p>{futures.get('suggested_action', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            for d in futures.get("main_drivers", []):
                st.caption(f"• {d}")

    with col3:
        st.markdown("#### 🎲 期权策略")
        options = networked_report.get("options", {})
        if options:
            sentiment = options.get("sentiment", "N/A")
            conf = options.get("confidence", 0)
            sentiment_color = "#00cc66" if "看多" in str(sentiment) else ("#ff4444" if "看空" in str(sentiment) else "#999")
            st.markdown(f"""
            <div style="border-left: 4px solid {sentiment_color}; padding: 0 12px;">
            <h4 style="margin:0;color:{sentiment_color}">{sentiment}</h4>
            <p>置信度: <b>{conf}%</b></p>
            <p>{options.get('suggested_action', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            for d in options.get("main_drivers", []):
                st.caption(f"• {d}")

    st.markdown("---")
    st.caption(f"分析时间: {networked_report.get('generated_at', '')} | 模型: GLM-4-Flash | 双视角: 中国经济 + 全球经济")
    st.warning(RISK_WARNING)


def _render_wuxing_dashboard(config, now, cache_age):
    """五行模式：玄学算卦，30只A股三栏"""
    st.markdown("## 📊 今日自动日推 — 五行A股版")

    col_state1, col_state2, col_state3, col_state4 = st.columns(4)
    with col_state1:
        st.metric("系统状态", "运行中" if cache_age < 360 else "待刷新",
                  delta=f"缓存{cache_age:.0f}s前")
    with col_state2:
        st.metric("当前时间", now.strftime("%H:%M:%S"), delta=now.strftime("%Y-%m-%d"))
    with col_state3:
        st.metric("市场", "A股", delta="纯中国版")
    with col_state4:
        st.metric("模式", "五行算卦", delta="离线")

    st.markdown("---")

    today_report = load_today_report()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 生成今日日推报告", type="primary", use_container_width=True):
            with st.spinner("抓取中国新闻 → 五行算卦 → 筛选A股标的..."):
                today_report = generate_daily_report()
                st.success(f"报告已生成！股票 {today_report['stock_count']}只 | 期货 {today_report['futures_count']}只")
                st.rerun()

    with col_btn2:
        if st.button("🔄 强制刷新新闻(5分钟)", use_container_width=True):
            force_refresh()
            st.success("新闻缓存已刷新")
            st.rerun()

    if not today_report:
        st.info("今日日推报告尚未生成，请点击上方按钮生成。")
        return

    st.markdown("---")

    cols = st.columns(5)
    with cols[0]:
        st.metric("主导五行", today_report['dominant_wuxing'])
    with cols[1]:
        st.metric("五行气场", today_report['boost_level'])
    with cols[2]:
        st.metric("市场情绪", f"{today_report.get('market_sentiment', 0):.2f}")
    with cols[3]:
        term = today_report.get('term', {})
        st.metric("节气", f"{term.get('name', '')} {term.get('phase', '')}")
    with cols[4]:
        st.metric("干支日", today_report.get('ganzhi', ''))

    sandiao = today_report.get('sandiao', '')
    if sandiao:
        st.info(f"💬 {sandiao}")

    policy_boost = today_report.get('policy_boost_level', '')
    policy_summary = today_report.get('policy_summary', '')
    global_summary = today_report.get('global_summary', '')
    global_impact = today_report.get('global_impact', [])
    if policy_summary:
        with st.expander(f"🏛️ 政策面气场: {policy_boost} (点击展开策略要点)"):
            st.markdown("**国内政策**")
            st.markdown(policy_summary)
            if global_summary:
                st.markdown("---")
                st.markdown("**全球五大洲经济**")
                st.markdown(global_summary)
            if global_impact:
                st.markdown("---")
                st.markdown("**对华影响**")
                for imp in global_impact[:5]:
                    st.caption(f"> {imp}")

    st.markdown("### 📈 A股推荐 — 买入10 / 卖出10 / 回避10")
    col_buy, col_sell, col_avoid = st.columns(3)

    with col_buy:
        st.markdown("#### 🟢 买入 (10只)")
        for s in today_report.get('buy_stocks', []):
            signal_icon = {"追": "🔥", "等": "⏳", "撤": "🛑"}.get(s.get('timing_signal',''), '')
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #00cc66; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small>
                <small style="color:#ff9900;">{s.get('star_display','')} {signal_icon}{s.get('timing_signal','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small>日元:{s.get('riyuan_gan','')} | 长生:{s.get('chang_sheng_name','')} | 预期:{s.get('expected_range','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_sell:
        st.markdown("#### 🔴 卖出 (10只)")
        for s in today_report.get('sell_stocks', []):
            signal_icon = {"追": "🔥", "等": "⏳", "撤": "🛑"}.get(s.get('timing_signal',''), '')
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #ff4444; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small>
                <small style="color:#ff9900;">{s.get('star_display','')} {signal_icon}{s.get('timing_signal','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small>日元:{s.get('riyuan_gan','')} | 长生:{s.get('chang_sheng_name','')} | 预期:{s.get('expected_range','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_avoid:
        st.markdown("#### ⚪ 回避 (10只)")
        for s in today_report.get('avoid_stocks', []):
            signal_icon = {"追": "🔥", "等": "⏳", "撤": "🛑"}.get(s.get('timing_signal',''), '')
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #999999; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small>
                <small style="color:#ff9900;">{s.get('star_display','')} {signal_icon}{s.get('timing_signal','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small>日元:{s.get('riyuan_gan','')} | 长生:{s.get('chang_sheng_name','')} | 预期:{s.get('expected_range','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("### 📉 中国期货 — 买入 / 卖出 / 回避")
    col_fbuy, col_fsell, col_favoid = st.columns(3)

    with col_fbuy:
        st.markdown("#### 🟢 买入期货")
        for f in today_report.get('buy_futures', []):
            pa = f.get('price_analysis', {})
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #00cc66; padding-left: 8px; margin-bottom: 8px;">
                <b>{f.get('name','')}</b> <small>{f.get('exchange','')}</small><br>
                <small>入场: {f.get('entry_signal','')[:25]}</small><br>
                <small>止损: {pa.get('stop_loss','')[:20]} | 目标: {pa.get('target','')[:20]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_fsell:
        st.markdown("#### 🔴 卖出期货")
        for f in today_report.get('sell_futures', []):
            pa = f.get('price_analysis', {})
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #ff4444; padding-left: 8px; margin-bottom: 8px;">
                <b>{f.get('name','')}</b> <small>{f.get('exchange','')}</small><br>
                <small>入场: {f.get('entry_signal','')[:25]}</small><br>
                <small>止损: {pa.get('stop_loss','')[:20]} | 目标: {pa.get('target','')[:20]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_favoid:
        st.markdown("#### ⚪ 回避期货")
        for f in today_report.get('avoid_futures', []):
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #999999; padding-left: 8px; margin-bottom: 8px;">
                <b>{f.get('name','')}</b> <small>{f.get('exchange','')}</small><br>
                <small>{f.get('entry_signal','')[:30]}</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("### 🎲 中国期权策略建议")
    opts = today_report.get('options_summary', {})
    if opts:
        st.info(f"**推荐策略**: {opts.get('strategy', '')}")
        for t in opts.get('suggested_targets', []):
            st.markdown(f"- {t}")
        st.caption(opts.get('note', ''))

    timing_summary = today_report.get('timing_summary', '')
    may_events = today_report.get('may_events', '')
    if timing_summary:
        with st.expander("⏱️ 五行择时推荐（追/等/撤）", expanded=True):
            st.markdown(timing_summary)
            st.caption("追=承载力强+天时生助 | 等=承载力中+方向不明 | 撤=承载力弱+天时相克")
    if may_events:
        with st.expander("📅 5月宏观事件日历"):
            st.code(may_events, language=None)

    stock_count = today_report.get('stock_count', 0)
    winrate = today_report.get('win_rate', {})
    if winrate:
        with st.expander("🎯 玄学胜率"):
            if 'multi_period' in winrate:
                wr_cols = st.columns(3)
                for i, (label, val) in enumerate(winrate['multi_period'].items()):
                    with wr_cols[i]:
                        st.metric(label, val)
            st.caption(winrate.get('note', ''))

    with st.expander("📅 历史日推 (近7天)"):
        hist = load_historical_reports(days=7)
        if hist:
            for h in hist:
                rid = h.get('report_id', '')
                gen_time = h.get('generated_at', '')
                bc = len(h.get('buy_stocks', []))
                sc = len(h.get('sell_stocks', []))
                ac = len(h.get('avoid_stocks', []))
                st.markdown(f"- **{rid}** ({gen_time}): 买{bc}/卖{sc}/回避{ac} | 五行「{h.get('dominant_wuxing', '')}」{h.get('boost_level', '')}")
        else:
            st.caption("暂无历史报告")

    st.warning(RISK_WARNING)


# ============================================================
# 主函数
# ============================================================
def main():
    """主入口"""

    load_custom_config()
    start_auto_refresh(interval_minutes=5)

    config = render_sidebar()

    tab_daily, tab_manual, tab_knowledge, tab_bazi, tab_live, tab_futures, tab_stock_scan = st.tabs([
        "📊 自动日推(A股)", "✍️ 手动分析", "📚 知识库", "🧧 八字选股", "🌐 联网推演", "📈 期货/期权推演", "🔎 A股扫盘"
    ])

    with tab_daily:
        render_daily_dashboard(config)

    with tab_manual:
        render_header()
        news_input = render_news_input()

        if news_input["mode"] == "auto" and news_input.get("fetch"):
            with st.spinner("正在抓取并解析新闻..."):
                news_items = fetch_and_parse(max_items=5)
                run_batch_analysis(news_items, config)

        elif news_input["mode"] == "manual" and news_input.get("text"):
            news_text = news_input["text"].strip()
            if len(news_text) < 10:
                st.warning("请输入至少10个字以上的新闻内容~")
            else:
                if st.button("🔮 算一卦", type="primary", use_container_width=True):
                    with st.spinner("五行算卦中，请稍候..."):
                        report = run_analysis(news_text, config)
                        render_analysis_card(report)
                        st.warning(RISK_WARNING)
        else:
            st.info("输入新闻内容或切换到自动抓取模式开始分析。")

    with tab_knowledge:
        st.markdown("## 📚 五行行业映射速查表")
        col_tabs = st.columns(5)
        for i, (wx, info) in enumerate(WUXING_INDUSTRY_MAP.items()):
            with col_tabs[i % 5]:
                st.markdown(f"### {['🔥','💎','🏗️','💧','🌿'][i]} {wx}")
                st.caption(info["description"])
                for ind in info["industries"]:
                    st.markdown(f"- {ind}")

        st.markdown("---")
        st.markdown("## 📊 中国期货品种五行映射")
        f_cols = st.columns(5)
        for i, (wx, info) in enumerate(FUTURES_WUXING_MAP.items()):
            with f_cols[i % 5]:
                st.markdown(f"### {['🔥','💎','🏗️','💧','🌿'][i]} {wx}")
                st.caption(info["reason"])
                for c in info["contracts"]:
                    st.markdown(f"- {c}")

        st.markdown("---")
        st.markdown("## 📋 提示词库")

        with st.expander("🔍 为什么A股八字操盘系统不做期货功能？（完整分析提示词）", expanded=False):
            st.caption("复制以下内容发送给 AI，从账户体系、数据基础、监管合规等角度深度分析")

            prompt_text = """# 角色设定
你是一位熟悉中国金融市场的产品经理，同时了解证券、期货交易规则以及量化/玄学派交易软件的开发逻辑。

# 任务
用户发现某款名为"A股八字自动操盘"的软件（功能包括：根据上市日期排八字、十二长生承载力推演、买入卖出信号提示）只有股票模块，完全没有期货和期权功能。请从以下角度，详细分析为什么这类软件普遍**不做期货功能**：

1. **账户与资金体系差异**（证券账户 vs 期货账户，保证金制度，证券三方存管 vs 期货银期转账）
2. **合约生命周期差异**（股票无限期 vs 期货有到期日、移仓换月；"八字原点"如何定义？连续合约 vs 具体合约的八字矛盾）
3. **数据获取难度**（所有A股上市日期公开易得；期货每个品种、每个合约的上市日期分散、历史数据不完整）
4. **监管与合规风险**（证监会2015年以后对"玄学预测"类软件的警示；期货监管更严厉，杠杆产品搭配"占卜"信号容易引发纠纷）
5. **用户群体与产品定位**（八字炒股主要吸引散户；期货用户更专业，对玄学接受度低，更看重基本面/技术面）
6. **开发成本与收益**（增加期货模块需要额外对接期货公司、仿真交易系统、风控模块，投入产出比低）

# 输出要求
- 分点论述，每一点先说核心原因，再展开解释
- 语言平实、专业，不带情绪
- 最后一个自然段给出"结论"：如果非要给八字系统添加期货功能，需要解决哪三个最低门槛问题

# 附加说明
请基于中国内地金融市场实际情况回答，可引用公开规则（如《期货交易管理条例》、交易所合约挂牌规则等），无需编造。"""

            st.code(prompt_text, language="text")
            st.caption("使用方式：完整复制上述内容 → 发送给支持联网的 AI → 获得结构化分析报告")

    with tab_bazi:
        st.markdown("## 🧧 八字选股助手")
        st.caption("基于 IPO 日元 × 交易日地支 → 十二长生承载力 → 追/等/撤决策")

        col1, col2 = st.columns([2, 1])
        with col1:
            code_input = st.text_input(
                "股票代码", placeholder="002594 / 600519 / 300308 ...",
                help="输入6位A股代码，回车生成报告"
            )
        with col2:
            date_input = st.date_input(
                "目标交易日", value=datetime.now(),
                help="默认今天，可手动选择"
            )

        prev_return = st.text_input("前一日涨跌幅%（可选，用于量价验证）", placeholder="-0.5")

        if code_input.strip():
            code = code_input.strip()
            date_str = date_input.strftime("%Y-%m-%d")
            prev_pct = None
            if prev_return.strip():
                try:
                    prev_pct = float(prev_return.strip())
                except ValueError:
                    st.warning("涨跌幅格式无效，已忽略")

            with st.spinner("排盘中..."):
                try:
                    report = generate_bazi_report(code, trade_date_str=date_str, prev_return_pct=prev_pct)
                    st.success(f"✅ 报告已生成 — {report['stock_name']}")

                    # 快速摘要卡片
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.metric("承载力", f"{report['star_display']} {report['chang_sheng_stage']}")
                    with m_col2:
                        s = report['timing_signal']
                        st.metric("择时信号", f"{'🔥' if s=='追' else '⏳' if s=='等' else '🛑'} {s}")
                    with m_col3:
                        st.metric("预期区间", report['expected_range'])

                    # 完整报告
                    with st.expander("📋 完整推演报告", expanded=True):
                        st.markdown(format_bazi_report(report))

                    # 十二长生速查
                    with st.expander("📐 该日元十二长生速查"):
                        st.code(report["stem_table"], language=None)

                    st.markdown("---")
                    st.markdown("### ⏭️ 后续3日承载力节奏推演")
                    with st.spinner("正在推算后续3个交易日..."):
                        try:
                            fwd = generate_forward_report(code, trade_date_str=date_str)
                            st.markdown(format_forward_report(fwd))
                        except Exception as fe:
                            st.warning(f"前瞻推演暂时不可用: {fe}")

                except Exception as e:
                    st.error(f"排盘失败: {e}")
                    st.info("请确认股票代码正确 — 系统已收录 55 只A股 IPO 日期")
        else:
            st.info("👆 输入股票代码开始八字推演")
            st.markdown("---")
            st.markdown("### 🧮 十二长生承载力速判表（5天干×12地支）")
            stems = [
                ("甲木", {"子": "沐", "丑": "冠", "寅": "临", "卯": "旺", "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "绝", "酉": "胎", "戌": "养", "亥": "长"}),
                ("丙火", {"子": "胎", "丑": "养", "寅": "长", "卯": "沐", "辰": "冠", "巳": "临", "午": "旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝"}),
                ("戊土", {"子": "旺", "丑": "冠", "寅": "病", "卯": "死", "辰": "墓", "巳": "临", "午": "旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝"}),
                ("庚金", {"子": "死", "丑": "墓", "寅": "绝", "卯": "胎", "辰": "养", "巳": "长", "午": "沐", "未": "冠", "申": "临", "酉": "旺", "戌": "衰", "亥": "病"}),
                ("壬水", {"子": "旺", "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "绝", "午": "胎", "未": "养", "申": "长", "酉": "沐", "戌": "冠", "亥": "临"}),
            ]
            branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            table_data = {}
            for stem_name, stem_map in stems:
                row = {}
                for b in branches:
                    v = stem_map.get(b, "?")
                    style = ""
                    if v == "旺":
                        style = "⭐"
                    elif v in ("临", "冠"):
                        style = "★"
                    elif v == "沐":
                        style = "·"
                    row[b] = f"{style}{v}" if style else v
                table_data[stem_name] = row
            df = pd.DataFrame(table_data).T
            df.index.name = "日元"
            st.dataframe(df, use_container_width=True)
            st.caption("⭐帝旺 ★临官/冠带 ·沐浴  其他:长/冠(冠带)/衰/病/死/墓/绝/胎/养")

    with tab_live:
        st.markdown("## 🌐 联网版八字选股推演")
        st.caption("天时分析 → 帝旺扫描 → 券商金股交叉 → 三重共振日报")

        col_date1, col_date2 = st.columns([1, 3])
        with col_date1:
            live_date = st.date_input(
                "选择推演日期", value=datetime.now(),
                key="live_date",
                help="默认今天，可手动选择（如5月6日等）"
            )
        with col_date2:
            st.markdown("")
            st.markdown("")
            gen_btn = st.button("🔮 生成联网推演日报", type="primary", use_container_width=True)

        if gen_btn:
            date_str = live_date.strftime("%Y-%m-%d")
            with st.spinner(f"正在联网推演 {date_str} ..."):
                try:
                    live_report = generate_live_daily_report(trade_date_str=date_str)
                    st.session_state["live_report"] = live_report
                    st.success(f"✅ 推演完成！帝旺级品种 {live_report['diwang_count']} 只 | 共振排名 {len(live_report['top_resonance'])} 只")
                    st.rerun()
                except Exception as e:
                    st.error(f"推演出错: {e}")

        live_report = st.session_state.get("live_report")

        # 如果已有报告，展示
        if live_report:
            trade_date = live_report["trade_date"]
            day_ganzhi = live_report["day_ganzhi"]

            st.markdown("---")
            st.markdown("## 一、当日天时分析")

            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                st.metric("公历日期", trade_date)
                st.metric("四柱八字", f"{live_report['year_ganzhi']} {live_report['month_ganzhi']} {day_ganzhi}")
            with t_col2:
                st.metric("日柱干支", f"{day_ganzhi}（{live_report['day_gan']}{live_report['day_wuxing']}日干）")
                st.metric("年度格局", live_report["annual_grade"])
            with t_col3:
                m_stars = live_report["market_stars"]
                m_stage = live_report["market_stage"]
                st.metric("大盘戊土承载力", f"{m_stars} {m_stage}")
                st.metric("大盘预期区间", live_report["market_range"])

            st.markdown(live_report["market_note"])

            st.markdown("---")
            st.markdown("## 二、各日元当日承载力速判")

            stem_data = []
            gan_order = ["庚", "辛", "丙", "丁", "甲", "乙", "壬", "癸", "戊", "己"]
            for gan in gan_order:
                if gan in live_report["stem_capacity"]:
                    sc = live_report["stem_capacity"][gan]
                    signal = "🔥🔥🔥 当日最强" if sc["stage"] == "帝旺" else (
                        "★★ 偏强" if sc["stage"] in ("临官", "冠带") else
                        "· 一般" if sc["stage"] in ("沐浴", "长生", "衰", "养") else
                        "⚠ 偏弱"
                    )
                    stem_data.append({
                        "日元": f"{gan}({sc['wuxing']})",
                        "十二长生": sc["stage"],
                        "星级": sc["stars"],
                        "信号": signal,
                        "预期区间": sc["range"],
                    })
            st.dataframe(pd.DataFrame(stem_data), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("## 三、三重共振扫描（天时×券商人气×板块政策）")

            top_r = live_report.get("top_resonance", [])
            if top_r:
                res_data = []
                for r in top_r[:12]:
                    emoji = "🔴" if r["resonance_level"] == "三重共振" else ("🟡" if r["resonance_level"] == "双重共振" else "⚪")
                    res_data.append({
                        "排名": len(res_data) + 1,
                        "品种": f"{r['name']}({r['code']})",
                        "阶段": r["stage"],
                        "天时": r["tianshi"],
                        "人气(次)": r["pop_count"],
                        "政策": r["policy"],
                        "总分": r["total"],
                        "共振": f"{emoji} {r['resonance_level']}",
                    })
                st.dataframe(pd.DataFrame(res_data), use_container_width=True, hide_index=True)
            else:
                st.info("暂无三重共振级别品种")

            st.markdown("---")
            st.markdown("## 四、帝旺级品种完整推演")

            diwang_reps = live_report.get("diwang_reports", [])
            if diwang_reps:
                for rep in diwang_reps:
                    with st.expander(f"📋 {rep['stock_name']} ({rep['stock_code']}) — {rep['star_display']} {rep['chang_sheng_stage']}", expanded=False):
                        st.markdown(format_bazi_report(rep))
            else:
                st.info("当日无帝旺级品种")

            st.markdown("---")
            st.markdown("## 五、本月券商金股人气榜")

            pop_items = sorted(GOLD_STOCK_POPULARITY_2026_05.items(), key=lambda x: x[1]["count"], reverse=True)
            pop_data = []
            for code, info in pop_items:
                pop_data.append({
                    "名称": info["name"],
                    "代码": code,
                    "推荐次数": f"{'⭐' * min(info['count'], 5)} {info['count']}",
                })
            st.dataframe(pd.DataFrame(pop_data), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("## 📎 联网数据来源")
            for ds in live_report.get("data_sources", DATA_SOURCES):
                st.markdown(f"- **{ds['category']}**: {ds['source']} ({ds['purpose']})")

            st.markdown("---")
            st.warning(
                "⚠️ **免责声明**：本系统所有「帝旺」「买入」「追」等表述均是基于公开信息的五行框架推演练习，"
                "绝不构成任何形式的证券投资建议或收益承诺。期货和期权交易风险极高，可能造成超过本金投入的亏损。"
                "市场风险莫测，投资须怀敬畏之心。"
            )
        else:
            st.info("👆 选择推演日期，点击「生成联网推演日报」开始。系统将自动：\n\n"
                    "1. 分析当日天时（四柱八字+大盘戊土承载力）\n"
                    "2. 扫描全部收录股票的帝旺/临官状态\n"
                    "3. 交叉匹配16家券商5月金股人气\n"
                    "4. 计算三重共振评分\n"
                    "5. 生成帝旺级品种完整推演报告")

            st.markdown("---")
            with st.expander("📋 5月券商金股池预览"):
                for b in BROKER_GOLD_POOL_2026_05:
                    st.markdown(f"**{b['broker']}** ({b['date']})")
                    st.caption("、".join(b["picks"]))
                    st.markdown("")


    with tab_futures:
        st.markdown("## 📈 八字期货/期权推演")
        st.caption("输入品种代码或中文名 → 自动查上市日期 → 排八字定五行 → 承载力推演 → 策略输出")

        # 日期选择器（全局共用）
        fut_date = st.date_input(
            "📅 目标交易日", value=datetime.now(),
            key="futures_date_global",
        )
        date_str = fut_date.strftime("%Y-%m-%d")

        # ═══════════════════════════════════════
        # 自动扫盘区（一键选出TOP10）
        # ═══════════════════════════════════════
        col_auto1, col_auto2 = st.columns([1, 3])
        with col_auto1:
            run_top10 = st.button("⚡ 自动扫盘 TOP10", type="primary", use_container_width=True,
                                  help="扫描全部46个期货品种，按承载力+专业评级+月度轮动评分，选出TOP10并自动匹配期权策略")
        with col_auto2:
            if run_top10:
                st.caption("正在扫描全部期货品种...")
            else:
                st.caption("一键自动扫描全部期货品种，生成TOP10推荐表+期权策略匹配")

        if run_top10:
            with st.spinner(f"正在扫描全部期货品种 ({date_str}) ..."):
                try:
                    top10 = generate_futures_top10(date_str)
                    st.session_state["futures_top10"] = top10
                    st.success(f"✅ 扫描完成！共 {top10['total_scanned']} 个品种，多头 {top10['bullish_count']} 个，空头 {top10['bearish_count']} 个")
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")

        top10 = st.session_state.get("futures_top10")
        if top10:
            st.markdown("---")
            st.markdown(format_futures_top10_table(top10))

            # 可展开详细数据
            with st.expander("📊 TOP10 详细数据表"):
                t10_data = []
                for r in top10["top10"]:
                    t10_data.append({
                        "品种": f"{r['name']}({r['symbol']})",
                        "主力合约": get_main_contract(r["symbol"]),
                        "上市日期(首个)": r["ipo_date"],
                        "日元": r["riyuan_gan"],
                        "期货五行": r["futures_wuxing"],
                        "承载力": f"{r['star']} {r['stage']}",
                        "阶段": r["phase_label"],
                        "承载力分": r["capacity"],
                        "专业评级": r["pro_direction"],
                        "综合评分": r["composite"],
                        "买方策略": r["opt_buyer"],
                        "卖方策略": r["opt_seller"],
                    })
                st.dataframe(pd.DataFrame(t10_data), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.caption("👇 下方可手动输入品种做单品种深度推演")

        # ═══════════════════════════════════════
        # 手动输入区
        # ═══════════════════════════════════════

        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            fut_input = st.text_input(
                "🔍 输入品种代码或名称",
                placeholder="如: AU / 黄金 / SC / 原油 / RB / 螺纹钢 ...",
                key="futures_input",
                help="支持代码(AU/SC/RB...)、中文名(黄金/原油/螺纹钢...)、拼音模糊搜索"
            )
            selected_symbol = None
            selected_info = None
            if fut_input:
                matches = search_futures(fut_input.strip())
                if matches:
                    if len(matches) == 1:
                        selected_info = matches[0]
                        selected_symbol = matches[0]["symbol"]
                        st.caption(f"✅ 匹配: {selected_info['name']} ({selected_info['symbol']}) | 五行: {selected_info['wuxing']} | {selected_info['exchange']}")
                    else:
                        st.caption(f"🔍 找到 {len(matches)} 个匹配，请精确输入:")
                        for m in matches[:5]:
                            st.caption(f"  → {m['symbol']} — {m['name']} [{m['wuxing']}]")
                else:
                    st.caption("❓ 未匹配到品种，请检查输入")

        # 快速输入示例按钮
        if not fut_input:
            st.caption("💡 快速输入示例：")
            cols_quick = st.columns(8)
            quick_inputs = ["AU", "SC", "RB", "I", "CU", "黄金", "原油", "螺纹"]
            for i, qi in enumerate(quick_inputs):
                with cols_quick[i]:
                    if st.button(qi, key=f"quick_{qi}", use_container_width=True):
                        st.session_state["futures_input"] = qi
                        st.rerun()

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            run_fut = st.button("📅 单日推演", type="primary", use_container_width=True,
                                disabled=not selected_symbol)
        with col_btn2:
            run_fwd = st.button("⏭️ 后续3日推演", type="secondary", use_container_width=True,
                                disabled=not selected_symbol)
        with col_btn3:
            if selected_info:
                st.caption(f"当前选中: {selected_info['name']}({selected_info['symbol']}) | {selected_info['wuxing']}")
            else:
                st.caption("👆 先输入品种代码或名称")

        if run_fut:
            with st.spinner(f"正在推演 {selected_symbol} ..."):
                try:
                    frep = generate_futures_bazi_report(selected_symbol, date_str)
                    st.session_state["futures_report"] = frep
                    st.success(f"✅ {frep['name']} 承载力: {frep['star_display']} {frep['chang_sheng_stage']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"推演出错: {e}")

        if run_fwd:
            with st.spinner(f"正在推算后续3日承载力..."):
                try:
                    fwdrep = generate_futures_forward_report(selected_symbol, date_str, 3)
                    st.session_state["futures_forward"] = fwdrep
                    st.success(f"✅ 已推算T+0至T+3 共4日承载力")
                    st.rerun()
                except Exception as e:
                    st.error(f"推演出错: {e}")

        frep = st.session_state.get("futures_report")
        fwdrep = st.session_state.get("futures_forward")

        if frep:
            st.markdown("---")
            st.markdown("## 📊 期货推演")
            st.caption("方向 + 开仓条件 + 止损")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("品种", f"{frep['name']} ({frep['symbol']})")
            with c2:
                st.metric("日元", f"{frep['riyuan_gan']}({frep['riyuan_wuxing']})")
            with c3:
                st.metric("承载力", f"{frep['star_display']} {frep['chang_sheng_stage']}")
            with c4:
                action_map = {"追": "🔥 追", "等": "⏳ 等", "撤": "🛑 撤"}
                st.metric("择时", action_map.get(frep['action'], frep['action']))

            with st.expander("📋 期货完整推演报告", expanded=True):
                # 只显示期货核心段：基础信息+承载力+期货策略+结论
                fr = frep
                st.markdown(f"""
### 一、基础信息
- 品种：{fr['name']} ({fr['symbol']})
- 上市日期：{fr['ipo_date']}
- 日元五行：{fr['riyuan_gan']}({fr['riyuan_wuxing']}) | 日柱：{fr['riyuan_ganzhi']}
- 品种五行归类：{fr['futures_wuxing']}
- 目标交易日：{fr['trade_date']}

### 二、当日承载力
- 时间八字：{fr['year_ganzhi']} {fr['month_ganzhi']} {fr['day_ganzhi']}
- {fr['riyuan_gan']}({fr['riyuan_wuxing']}) x {fr['day_zhi']}日支 = **{fr['chang_sheng_stage']}**
- 承载力等级：{fr['star_display']} {fr['star_label']}
- 理论预期方向：{fr['expected_range']}
- 量价验证信号：{fr['verify_signal']}

### 三、期货策略
- **方向**：{'做多' if fr['action']=='追' else ('做空/震荡' if fr['action']=='撤' else '观望/震荡')}
- **开仓条件**：{fr['verify_signal']}
- **止损建议**：突破前高/前低的2%或关键支撑/压力位，按自身风险承受能力设定

### 四、综合结论
> {fr['conclusion']}
""")
                st.caption("—" * 40)
                st.warning(
                    "⚠️ **免责声明**：本推演基于八字十二长生理论，仅为传统文化视角的沙盘演练，不构成任何投资建议。"
                    "期货交易风险极高，可能造成超过本金投入的亏损，严禁使用借贷资金。"
                )

            # 期权策略段——独立展示
            st.markdown("---")
            st.markdown("## 🎯 期权策略矩阵")
            st.caption("基于承载力等级自动匹配买/卖策略")
            if frep["option_bs"]:
                bs = frep["option_bs"]
                ocol1, ocol2 = st.columns(2)
                with ocol1:
                    st.info(f"**买方首推**\n\n{bs['buyer_strategy']}")
                    st.caption(bs["logic"])
                with ocol2:
                    st.warning(f"**卖方策略**\n\n{bs['seller_strategy']}")
                    st.caption(f"风险: {bs['risk_note']}")
            if frep["option_strategies"]:
                with st.expander("📋 期权详细策略"):
                    for s in frep["option_strategies"]:
                        st.markdown(f"- **{s['strategy']}**: {s['detail']}")
                        st.caption(f"  ⚠ {s['risk_note']}")

        if fwdrep:
            st.markdown("---")
            st.markdown("### ⏭️ 后续承载力变化表")
            fwd_data = []
            for row in fwdrep["daily_rows"]:
                fwd_data.append({
                    "交易日": row["day_label"],
                    "日期": row["date"],
                    "日柱": row["day_ganzhi"],
                    "十二长生": row["stage"],
                    "承载力": f"{row['star']} {row['label']}",
                    "预期方向": row["expected"],
                    "期权买方": row["opt_buyer"],
                    "期权卖方": row["opt_seller"],
                })
            st.dataframe(pd.DataFrame(fwd_data), use_container_width=True, hide_index=True)

            st.markdown("### 离场/加仓节奏规划")
            rhythm_data = []
            for a in fwdrep["rhythm"]["daily_actions"]:
                emoji = "🔥" if "加仓" in a["action"] else ("⏳" if "持有" in a["action"] else "🛑")
                rhythm_data.append({
                    "交易日": a["day_label"],
                    "日期": a["date"],
                    "承载力": a["stage"],
                    "操作": f"{emoji} {a['action']}",
                    "详细理由": a["detail"],
                })
            st.dataframe(pd.DataFrame(rhythm_data), use_container_width=True, hide_index=True)
            st.info(f"💡 综合节奏建议：{fwdrep['rhythm']['overview']}")

        # 初始状态提示
        if not frep and not fwdrep and not selected_symbol:
            st.info(
                "👆 **输入品种代码或名称**，系统将自动完成：\n\n"
                "1. 🔍 联网/本地匹配期货品种\n"
                "2. 📅 查上市日期 → 排八字 → 定日元五行\n"
                "3. 🧮 计算目标交易日的十二长生承载力（帝旺/临官/冠带/.../死/墓）\n"
                "4. 📊 输出期货策略（方向 + 开仓条件 + 止损）\n"
                "5. 🎯 独立输出期权买/卖策略矩阵\n\n"
                "支持输入示例：`AU` `黄金` `SC` `原油` `RB` `螺纹钢`"
            )
        elif not frep and not fwdrep and selected_symbol:
            st.success(f"✅ 已识别: {selected_info['name']} ({selected_info['symbol']}) | 五行: {selected_info['wuxing']} | 点击上方按钮开始推演")

        st.markdown("---")
        st.markdown("### 📋 期货期权策略速查表")

        tab_opt1, tab_opt2 = st.tabs(["期权买/卖矩阵", "月度轮动方向"])

        with tab_opt1:
            opt_matrix_data = []
            for m in OPTION_BUYER_SELLER_MATRIX:
                opt_matrix_data.append({
                    "承载力": m["level"],
                    "适用阶段": "、".join(m["stages"]),
                    "买方策略": m["buyer_strategy"],
                    "卖方策略": m["seller_strategy"],
                })
            st.dataframe(pd.DataFrame(opt_matrix_data), use_container_width=True, hide_index=True)

        with tab_opt2:
            try:
                md = get_monthly_futures_direction(date_str)
                md_data = []
                for elem, info in md["directions"].items():
                    md_data.append({
                        "五行": elem,
                        "方向": info["direction"],
                        "品种": "、".join(info["picks"][:6]),
                        "逻辑": info["note"],
                    })
                st.dataframe(pd.DataFrame(md_data), use_container_width=True, hide_index=True)
            except Exception:
                st.caption("月度轮动数据加载中...")

        st.markdown("---")
        st.warning(
            "⚠️ **期货/期权免责声明**：本推演基于八字十二长生理论，仅为传统文化视角的沙盘演练，"
            "不构成任何形式的投资建议。期货和期权交易风险极高，可能造成超过本金投入的亏损，"
            "严禁使用借贷资金或生活必用资金参与。必须设置硬性止损线（单笔亏损≤账户总值2-5%）。"
        )

        with st.expander("📡 联网数据来源集成参考"):
            ds_data = []
            for ds in FUTURES_DATA_SOURCES_REFERENCE:
                ds_data.append({
                    "数据类别": ds["category"],
                    "联网搜索建议": ds["search_suggestion"],
                    "用途": ds["purpose"],
                })
            st.dataframe(pd.DataFrame(ds_data), use_container_width=True, hide_index=True)

    with tab_stock_scan:
        st.markdown("## 🔎 A股八字自动扫盘")
        st.caption("基于67只核心标的的十二长生承载力 + 券商金股人气 + 月度轮动政策共振，一键生成TOP10榜单")

        stock_date = st.date_input(
            "📅 目标交易日", value=datetime.now(),
            key="stock_scan_date",
        )
        stock_date_str = stock_date.strftime("%Y-%m-%d")

        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            run_stock_top10 = st.button("⚡ 自动扫盘 TOP10", type="primary", use_container_width=True,
                                        help="扫描全部67只核心标的，按承载力+券商人气+政策共振评分，选出TOP10")
        with col_s2:
            if run_stock_top10:
                st.caption("正在扫描全部A股核心标的...")
            else:
                st.caption("一键自动扫描全部收录A股，生成TOP10推荐表+三重共振+龙头推演")

        if run_stock_top10:
            with st.spinner(f"正在扫描全部A股标的 ({stock_date_str}) ..."):
                try:
                    stock_top10 = generate_stock_top10(stock_date_str)
                    st.session_state["stock_top10"] = stock_top10
                    st.success(f"✅ 扫描完成！共 {stock_top10['total_scanned']} 只标的，多头 {stock_top10['bullish_count']} 只，空头 {stock_top10['bearish_count']} 只")
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")

        stock_top10_data = st.session_state.get("stock_top10")
        if stock_top10_data:
            st.markdown("---")
            st.markdown(format_stock_top10_table(stock_top10_data))

            with st.expander("📊 TOP10 详细数据表"):
                t10s = []
                for r in stock_top10_data["top10"]:
                    t10s.append({
                        "股票": f"{r['name']}({r['code']})",
                        "板块": r["sector"],
                        "日元": r["riyuan_gan"],
                        "行业五行": r["stock_wuxing"],
                        "承载力": f"{r['star']} {r['stage']}",
                        "阶段": r["phase_label"],
                        "承载力分": r["capacity"],
                        "综合评分": r["composite"],
                        "量价信号": r["verify_signal"],
                    })
                st.dataframe(pd.DataFrame(t10s), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.caption("💡 下方可选具体标的做深度推演")

        # 手动选股深度推演
        st.markdown("---")
        st.markdown("### 🔍 个股深度推演")
        col_ss1, col_ss2 = st.columns([2, 1])
        with col_ss1:
            stock_codes = list(STOCK_SECTOR_WUXING.keys())
            stock_options = [f"{c} {STOCK_SECTOR_WUXING[c]['name']} ({STOCK_SECTOR_WUXING[c]['sector']})" for c in stock_codes]
            selected_stock_idx = st.selectbox(
                "选择标的",
                range(len(stock_codes)),
                format_func=lambda i: stock_options[i],
                key="stock_detail_select",
            )
            sel_code = stock_codes[selected_stock_idx]
        with col_ss2:
            st.caption(f"五行: {_resolve_stock_wuxing(sel_code)} | 板块: {_resolve_stock_sector(sel_code)}")

        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            if st.button("🔮 单日推演", type="primary", use_container_width=True, key="stock_single_run"):
                with st.spinner("推演中..."):
                    try:
                        rep = generate_bazi_report(sel_code, stock_date_str)
                        st.session_state["stock_single_report"] = rep
                        st.rerun()
                    except Exception as e:
                        st.error(f"推演出错: {e}")
        with col_sb2:
            if st.button("⏭️ 后续3日推演", use_container_width=True, key="stock_forward_run"):
                with st.spinner("推演中..."):
                    try:
                        fwd = generate_forward_report(sel_code, stock_date_str, 3)
                        st.session_state["stock_forward_report"] = fwd
                        st.rerun()
                    except Exception as e:
                        st.error(f"推演出错: {e}")

        srep = st.session_state.get("stock_single_report")
        if srep:
            st.markdown("---")
            st.markdown("## 📊 单日推演")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("标的", f"{srep['name']} ({srep['code']})")
            with c2:
                st.metric("日元", f"{srep['riyuan_gan']}({srep['riyuan_wuxing']})")
            with c3:
                st.metric("承载力", f"{srep['star_display']} {srep['chang_sheng_stage']}")
            with c4:
                action_map = {"追": "🔥 追", "等": "⏳ 等", "撤": "🛑 撤"}
                st.metric("择时", action_map.get(srep['action'], srep['action']))
            with st.expander("📋 完整推演报告", expanded=True):
                st.markdown(format_bazi_report(srep))

        sfwd = st.session_state.get("stock_forward_report")
        if sfwd:
            st.markdown("---")
            st.markdown(format_forward_report(sfwd))

        if not srep and not sfwd:
            st.info(
                "👆 **选择一只标的**，点击「单日推演」或「后续3日推演」获取详细分析。\n\n"
                "推演内容：上市日期排八字 → 当日十二长生承载力 → 预期方向 → 量价验证 → 择时（追/等/撤）"
            )

        st.markdown("---")
        st.markdown("### 📋 股票承载力速查")
        cap_data = []
        for stage, (star, label, verify) in STOCK_CAPACITY_STAR_MAP.items():
            cap_data.append({
                "承载力": stage,
                "星级": star,
                "等级": label,
                "量价验证信号": verify,
            })
        st.dataframe(pd.DataFrame(cap_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.warning(
            "⚠️ **免责声明**：本推演基于八字五行和十二长生理论，仅为传统文化视角的沙盘演练，"
            "不构成任何形式的投资建议。股市有风险，所有标的均为方法论演示，不构成买入推荐。"
            "投资者须根据自身风险承受能力独立决策，并设置硬性止损。入市须谨慎，盈亏自负。"
        )


if __name__ == "__main__":
    from auto_trader import start_auto_refresh
    main()
