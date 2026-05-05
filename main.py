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
from stock_classifier import (
    classify_stocks, scan_and_classify,
    format_classification_report,
)
from cheap_pick_scanner import scan_cheap_picks, format_report as format_cheap_report
from zhuoyao_scanner import (
    scan_zhuoyao, format_zhuoyao_report, format_zhuoyao_single,
    CAPACITY_SCORES as ZY_CAPACITY_SCORES, EXPECTED_RANGE as ZY_EXPECTED_RANGE,
    STAGE_NAMES as ZY_STAGE_NAMES,
    TIANGAN_WUXING as ZY_TIANGAN_WUXING,
)
from zhuoyao_futures_scanner import (
    scan_futures_zhuoyao, format_futures_zhuoyao_report,
    format_futures_single,
    CAPACITY_SCORES as ZYF_CAPACITY_SCORES,
    FUTURES_EXPECTED_RANGE as ZYF_EXPECTED_RANGE,
    PHYSICAL_WUXING as ZYF_PHYSICAL_WUXING,
)

from chen_nanpeng_scanner import (
    scan_chen_nanpeng, format_chen_nanpeng_report,
    format_single_stock as format_cn_single,
    CHENNANPENG_INDUSTRY_WUXING,
)

from chen_nanpeng_futures_scanner import (
    scan_chen_nanpeng_futures, format_cn_futures_report,
    format_futures_single_cn,
    CN_FUTURES_WUXING_PHYSICAL,
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
# 智能分类辅助渲染
# ============================================================

def _render_classify_group(group: dict, prefix: str):
    """渲染一个板块的买入/卖出/观望三栏"""
    col_buy, col_sell, col_hold = st.columns(3)

    with col_buy:
        st.markdown("#### 🟢 买入（推荐）")
        for item in group.get("buy", []):
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #00cc66; padding-left: 8px; margin-bottom: 10px;">
                <b>{item['name']}</b> <small>{item['code']}</small><br>
                <small>行业: {item['sector']} | 五行: {item['wuxing']}</small><br>
                <small>日元: {item['riyuan']} | 长生: {item['stage']} | 择时: {item['timing']}</small><br>
                <small>预期: {item['expected_range']} | 评分: {item['total_score']}</small><br>
                <small style="color:#888;">{item['direction_reason'][:40]}</small>
                </div>
                """, unsafe_allow_html=True)
        if not group.get("buy"):
            st.caption("暂无")

    with col_sell:
        st.markdown("#### 🔴 卖出（回避）")
        for item in group.get("sell", []):
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #ff4444; padding-left: 8px; margin-bottom: 10px;">
                <b>{item['name']}</b> <small>{item['code']}</small><br>
                <small>行业: {item['sector']} | 五行: {item['wuxing']}</small><br>
                <small>日元: {item['riyuan']} | 长生: {item['stage']} | 择时: {item['timing']}</small><br>
                <small>预期: {item['expected_range']} | 评分: {item['total_score']}</small><br>
                <small style="color:#888;">{item['direction_reason'][:40]}</small>
                </div>
                """, unsafe_allow_html=True)
        if not group.get("sell"):
            st.caption("暂无")

    with col_hold:
        st.markdown("#### ⚪ 观望/中性")
        for item in group.get("hold", []):
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #999999; padding-left: 8px; margin-bottom: 10px;">
                <b>{item['name']}</b> <small>{item['code']}</small><br>
                <small>行业: {item['sector']} | 五行: {item['wuxing']}</small><br>
                <small>日元: {item['riyuan']} | 长生: {item['stage']} | 择时: {item['timing']}</small><br>
                <small>预期: {item['expected_range']} | 评分: {item['total_score']}</small><br>
                <small style="color:#888;">{item['direction_reason'][:40]}</small>
                </div>
                """, unsafe_allow_html=True)
        if not group.get("hold"):
            st.caption("暂无")


# ============================================================
# 主函数
# ============================================================
def main():
    """主入口"""

    load_custom_config()
    start_auto_refresh(interval_minutes=5)

    config = render_sidebar()

    tab_daily, tab_manual, tab_knowledge, tab_bazi, tab_live, tab_futures, tab_stock_scan, tab_classify, tab_options, tab_zhuoyao, tab_zhuoyao_futures, tab_chen_nanpeng, tab_cn_futures = st.tabs([
        "📊 自动日推(A股)", "✍️ 手动分析", "📚 知识库", "🧧 八字选股",
        "🌐 联网推演", "📈 期货全量", "🔎 A股全量扫盘", "🧠 智能分类", "🎯 期权策略",
        "🐉 玄捉妖扫描", "🐉 玄捉妖·期货", "⏳ 陈南鹏·五行择时", "⏳ 陈南鹏·期货择时",
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
        st.markdown("## 📈 期货全量（全部58个品种）")
        st.caption("上期所/能源中心/大商所/郑商所/广期所/中金所 → 全部品种 → 五行属性 → 保证金 → 合约信息")

        from futures_picker import CHINA_FUTURES_POOL, FUTURES_IPO_DATE_MAP

        # ═══════════════════════════════════════
        # 全量期货展示（可折叠）
        # ═══════════════════════════════════════
        with st.expander("📋 全部58个期货品种一览（展开查看）", expanded=False):
            all_futures = []
            for exchange, products in CHINA_FUTURES_POOL.items():
                for p in products:
                    symbol = p["symbol"]
                    ipo = FUTURES_IPO_DATE_MAP.get(symbol, "未知")
                    all_futures.append({
                        "交易所": exchange,
                        "品种": p["name"],
                        "代码": symbol,
                        "五行": p["wuxing"],
                        "合约单位": p["unit"],
                        "保证金参考": p["margin"],
                        "上市日期": ipo,
                    })
            st.dataframe(pd.DataFrame(all_futures), use_container_width=True, hide_index=True)
            st.caption("共 58 个期货品种，全部五行属性已标注")

        st.markdown("---")

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
        st.markdown("## 🔎 A股全量扫盘（全市场4500+只）")
        st.caption("akshare实时行情 × IPO日期→日元 × 十二长生承载力 × 政策分 × 机构信号 | 排除ST/科创板/港股")

        stock_date = st.date_input(
            "📅 目标交易日", value=datetime.now(),
            key="stock_scan_date",
        )
        stock_date_str = stock_date.strftime("%Y-%m-%d")

        col_s1, col_s2 = st.columns([1, 3])
        with col_s1:
            run_full_scan = st.button(
                "⚡ 全市场扫盘", type="primary",
                use_container_width=True,
                help="扫描全部A股（排除688/ST/港股），计算八字承载力+政策+机构评分"
            )
        with col_s2:
            if "full_market_result" in st.session_state:
                fr = st.session_state["full_market_result"]
                st.caption(f"上次扫描: {fr.get('total_scanned',0)}只 | 买{fr.get('buy_count',0)} 卖{fr.get('sell_count',0)} 观{fr.get('hold_count',0)}")
            else:
                st.caption("首次使用请点击扫描（约需10-30秒拉取全市场数据）")

        if run_full_scan:
            with st.spinner(f"正在拉取全A股实时数据 + 八字推演 ({stock_date_str}) ..."):
                try:
                    from full_market_scanner import scan_full_market
                    result = scan_full_market(stock_date_str)
                    st.session_state["full_market_result"] = result
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")

        market_data = st.session_state.get("full_market_result")
        if market_data:
            results = market_data.get("results", [])

            # 统计
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("扫描总数", market_data["total_scanned"])
            with c2:
                st.metric("🟢 买入", market_data["buy_count"])
            with c3:
                st.metric("🔴 卖出", market_data["sell_count"])
            with c4:
                st.metric("⚪ 观望", market_data["hold_count"])
            with c5:
                st.metric("日支", market_data.get("day_zhi", ""))

            # 筛选器
            st.markdown("---")
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                wx_filter = st.multiselect(
                    "五行", ["金", "木", "水", "火", "土"],
                    key="wx_filter", placeholder="全部五行"
                )
            with col_f2:
                stage_filter = st.multiselect(
                    "承载力",
                    ["帝旺", "临官", "冠带", "沐浴", "长生", "衰", "病", "死", "墓", "绝"],
                    key="stage_filter", placeholder="全部阶段"
                )
            with col_f3:
                label_filter = st.multiselect(
                    "买卖标签",
                    ["买入", "卖出", "观望"],
                    key="label_filter", placeholder="全部"
                )
            with col_f4:
                search_term = st.text_input("🔍 搜索（代码/名称）", key="stock_search")

            # 筛选
            filtered = results
            if wx_filter:
                filtered = [r for r in filtered if r["wuxing"] in wx_filter]
            if stage_filter:
                filtered = [r for r in filtered if r["stage"] in stage_filter]
            if label_filter:
                filtered = [r for r in filtered if r["label"] in label_filter]
            if search_term:
                filtered = [r for r in filtered if search_term.upper() in r["code"] or search_term in r["name"]]

            st.caption(f"显示 {len(filtered)} / {len(results)} 只")

            # 分页
            page_size = st.select_slider("每页", options=[50, 100, 200, 500, 1000], value=100)
            total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
            page = st.number_input("页码", 1, total_pages, 1, key="stock_page")
            start = (page - 1) * page_size
            page_data = filtered[start:start + page_size]

            # 数据表
            table_data = []
            for r in page_data:
                cap_label = r["capacity_label"]
                cap_icon = {"强": "🔥", "中": "✅", "弱": "❄️"}.get(cap_label, "")
                table_data.append({
                    "代码": r["code"],
                    "名称": r["name"],
                    "股价": r["price"],
                    "PE": r["pe"],
                    "涨跌%": r["chg_pct"],
                    "成交亿": r["volume_yi"],
                    "五行": r["wuxing"],
                    "日元": r["riyuan_gan"],
                    "长生": r["stage"],
                    "承载力": f"{cap_icon}{r['capacity']}",
                    "预期": r["expected_range"],
                    "政策分": r["policy_score"],
                    "机构分": r["inst_score"],
                    "综合": r["composite"],
                    "标签": r["label"],
                })

            st.dataframe(
                pd.DataFrame(table_data),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "代码": st.column_config.TextColumn(width="small"),
                    "名称": st.column_config.TextColumn(width="small"),
                    "股价": st.column_config.NumberColumn(format="%.2f"),
                    "标签": st.column_config.TextColumn(width="small"),
                },
            )

            # 承载力速查表
            with st.expander("📋 承载力评分速查", expanded=False):
                cap_ref = []
                for stage in ["帝旺", "临官", "冠带", "沐浴", "长生", "养", "衰", "胎", "病", "死", "墓", "绝"]:
                    cap_ref.append({
                        "长生阶段": stage,
                        "承载力分": CAPACITY_SCORES.get(stage, 0),
                        "预期区间": EXPECTED_RANGE.get(stage, ""),
                        "等级": "强" if CAPACITY_SCORES.get(stage, 0) >= 70 else ("中" if CAPACITY_SCORES.get(stage, 0) >= 40 else "弱"),
                    })
                st.dataframe(pd.DataFrame(cap_ref), use_container_width=True, hide_index=True)

            st.warning(RISK_WARNING)
        else:
            st.info(
                "👆 点击「全市场扫盘」开始。\n\n"
                "系统将：\n"
                "1. akshare 拉取全A股实时行情（4500+只）\n"
                "2. 自动查询IPO日期 → 计算日元天干\n"
                "3. 十二长生承载力推演\n"
                "4. 行业→五行 + 政策关键词 + 机构信号 → 综合评分\n"
                "5. 排除：688科创板 / ST / 港股 / 退市风险\n\n"
                "首扫约需10-30秒，后续有筛选器可按五行/承载力/买卖标签过滤"
            )

        st.markdown("---")
        st.warning(
            "⚠️ **免责声明**：本推演基于八字五行和十二长生理论，仅为传统文化视角的沙盘演练，"
            "不构成任何形式的投资建议。股市有风险，所有标的均为方法论演示，不构成买入推荐。"
            "投资者须根据自身风险承受能力独立决策，并设置硬性止损。入市须谨慎，盈亏自负。"
        )


    _render_extra_tabs(tab_options, tab_zhuoyao, tab_zhuoyao_futures, tab_chen_nanpeng, tab_cn_futures)

    with tab_classify:
        st.markdown("## 🧠 科创板 / A股 智能分类")

        scan_mode = st.radio(
            "扫描模式",
            ["五行承载力分类", "低价潜力扫盘（股价<30元）"],
            horizontal=True,
            key="classify_mode",
        )

        if scan_mode == "五行承载力分类":
            _render_wuxing_classify()
        else:
            _render_cheap_pick_scan()


# ============================================================
# 五行承载力分类标签页内容
# ============================================================
def _render_wuxing_classify():
    st.caption("基于十二长生承载力 + 预期涨幅 + 政策信号，自动分为买入/卖出/观望三栏")

    classify_date = st.date_input(
        "📅 目标交易日", value=datetime.now(),
        key="classify_date",
    )
    classify_date_str = classify_date.strftime("%Y-%m-%d")

    col_c1, col_c2 = st.columns([1, 3])
    with col_c1:
        run_classify = st.button("⚡ 一键扫描并分类", type="primary", use_container_width=True)
    with col_c2:
        if run_classify:
            st.caption("正在扫描全部收录股票并分类...")
        else:
            st.caption("扫描所有收录的A股+科创板股票，自动按买入/卖出/观望分类")

    if run_classify:
        with st.spinner(f"正在扫描并分类 ({classify_date_str}) ..."):
            try:
                class_result = scan_and_classify(classify_date_str)
                st.session_state["classify_result"] = class_result
                st.rerun()
            except Exception as e:
                st.error(f"扫描分类出错: {e}")

    class_result = st.session_state.get("classify_result")
    if class_result:
        if class_result.get("excluded"):
            exc_names = ", ".join(
                f"{e.get('name','')}({e.get('code','')})" for e in class_result["excluded"]
            )
            st.warning(f"⚠️ 已排除非A股品种: {exc_names}")

        st.markdown("---")
        st.markdown("## 🛡️ 科创板（688开头）")
        kc = class_result.get("kechuang", {})
        st.metric("科创板总数", kc.get("total", 0))
        _render_classify_group(kc, "kechuang")

        st.markdown("---")
        st.markdown("## 📊 A股（非科创板）")
        ash = class_result.get("ashares", {})
        st.metric("A股总数", ash.get("total", 0))
        _render_classify_group(ash, "ashares")

        with st.expander("📋 完整分类报告（文本）"):
            st.code(format_classification_report(class_result), language="markdown")

        st.warning(RISK_WARNING)
    else:
        st.info(
            "👆 点击「一键扫描并分类」开始。\n\n"
            "系统将：\n"
            "1. 扫描全部收录的 A股 + 科创板股票\n"
            "2. 计算每只的十二长生承载力 + 预期涨幅 + 政策信号\n"
            "3. 自动分离科创板/A股\n"
            "4. 按 买入/卖出/观望 三类输出，每类最多10只"
        )


# ============================================================
# 低价潜力扫盘标签页内容
# ============================================================
def _render_cheap_pick_scan():
    st.caption("🔍 全市场实时数据 → 股价 < 30元 → PE估值 → 科创板/A股自动分离")

    col_b1, col_b2 = st.columns([1, 3])
    with col_b1:
        run_cheap = st.button("⚡ 一键扫盘（全市场）", type="primary", use_container_width=True)
    with col_b2:
        st.caption("akshare实时拉取全A股行情，筛选股价<30元且PE合理的潜力股")

    if run_cheap:
        with st.spinner("正在拉取全市场实时数据并筛选..."):
            try:
                cheap_result = scan_cheap_picks()
                st.session_state["cheap_result"] = cheap_result
            except Exception as e:
                st.error(f"扫描出错: {e}")

    cheap_result = st.session_state.get("cheap_result")
    if cheap_result:
        st.markdown("---")
        st.markdown("## 🛡️ 科创板 低价潜力股")
        st.metric("科创板符合条件", cheap_result.get("kechuang_total", 0))

        col_a, col_b = st.columns(2)

        with col_a:
            kc = cheap_result.get("kechuang", [])
            if kc:
                for i, s in enumerate(kc, 1):
                    st.markdown(f"""
                    <div style="border-left: 4px solid #00cc66; padding-left: 8px; margin-bottom: 8px;">
                    <b>{i}. {s['name']}</b> <small>{s['code']}</small><br>
                    <small>💰 {s['price']}元 | PE: {s['pe']} | 涨跌: {s['chg_pct']}% | 成交: {s['volume_yi']}亿</small><br>
                    <small>⭐ 评分: {s['score']} | {s['reason']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("暂无符合条件")

        with col_b:
            st.markdown("## 📊 A股 低价潜力股")
            st.metric("A股符合条件", cheap_result.get("ashares_total", 0))

            ash = cheap_result.get("ashares", [])
            if ash:
                for i, s in enumerate(ash, 1):
                    st.markdown(f"""
                    <div style="border-left: 4px solid #ff9900; padding-left: 8px; margin-bottom: 8px;">
                    <b>{i}. {s['name']}</b> <small>{s['code']}</small><br>
                    <small>💰 {s['price']}元 | PE: {s['pe']} | 涨跌: {s['chg_pct']}% | 成交: {s['volume_yi']}亿</small><br>
                    <small>⭐ 评分: {s['score']} | {s['reason']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("暂无符合条件")

        with st.expander("📋 完整报告"):
            st.code(format_cheap_report(cheap_result), language="markdown")

        st.warning(RISK_WARNING)
    else:
        st.info(
            "👆 点击「一键扫盘」开始。\n\n"
            "系统将：\n"
            "1. 通过 akshare 实时拉取全 A 股行情\n"
            "2. 过滤：股价 < 30元 | 日成交 > 2000万 | 排除 ST\n"
            "3. 按 价格+PE+活跃度 综合评分\n"
            "4. 科创板/A股 自动分离，每板最多10只"
        )


# ============================================================
# 期权 + 玄捉妖 + 玄捉妖·期货 + 陈南鹏五行择时 + 陈南鹏期货择时 标签页（每次脚本执行都必须渲染）
# ============================================================
def _render_extra_tabs(tab_options, tab_zhuoyao, tab_zhuoyao_futures, tab_chen_nanpeng, tab_cn_futures):
    with tab_options:
        st.markdown("## 🎯 期权全量展示（所有中国场内期权产品）")
        st.caption("ETF期权 ❘ 股指期权 ❘ 商品期权 → 全部产品 → 五行属性 → 承载力 → 策略建议")

        from options_picker import OPTION_STRATEGIES, PRO_OPTION_STRATEGIES, STOP_LOSS_DISCIPLINE

        # ═══════════════════════════════════════
        # 一、ETF期权（股票期权）
        # ═══════════════════════════════════════
        st.markdown("---")
        st.markdown("### 📊 ETF期权（上交所/深交所）")
        etf_options = [
            {"标的": "上证50ETF", "代码": "510050", "交易所": "上交所", "五行": "金", "类型": "ETF期权"},
            {"标的": "沪深300ETF", "代码": "510300/159919", "交易所": "上交所/深交所", "五行": "土", "类型": "ETF期权"},
            {"标的": "中证500ETF", "代码": "510500/159922", "交易所": "上交所/深交所", "五行": "火", "类型": "ETF期权"},
            {"标的": "创业板ETF", "代码": "159915", "交易所": "深交所", "五行": "火", "类型": "ETF期权"},
            {"标的": "科创50ETF", "代码": "588000", "交易所": "上交所", "五行": "君", "类型": "ETF期权"},
            {"标的": "深证100ETF", "代码": "159901", "交易所": "深交所", "五行": "土", "类型": "ETF期权"},
            {"标的": "中证1000ETF", "代码": "512100/159845", "交易所": "上交所/深交所", "五行": "水", "类型": "ETF期权"},
        ]
        st.dataframe(pd.DataFrame(etf_options), use_container_width=True, hide_index=True)

        # ═══════════════════════════════════════
        # 二、股指期权
        # ═══════════════════════════════════════
        st.markdown("---")
        st.markdown("### 📈 股指期权（中金所）")
        idx_options = [
            {"标的": "沪深300股指期权", "代码": "IO", "交易所": "中金所", "五行": "土", "合约乘数": "100元/点", "类型": "股指期权"},
            {"标的": "中证1000股指期权", "代码": "MO", "交易所": "中金所", "五行": "水", "合约乘数": "200元/点", "类型": "股指期权"},
            {"标的": "上证50股指期权", "代码": "HO", "交易所": "中金所", "五行": "金", "合约乘数": "100元/点", "类型": "股指期权"},
        ]
        st.dataframe(pd.DataFrame(idx_options), use_container_width=True, hide_index=True)

        # ═══════════════════════════════════════
        # 三、商品期权（各期货交易所）
        # ═══════════════════════════════════════
        st.markdown("---")
        st.markdown("### 🛢️ 商品期权（全部品种）")

        commodity_options = [
            # 上期所
            {"品种": "黄金期权", "代码": "AU", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "铜期权", "代码": "CU", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "铝期权", "代码": "AL", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "锌期权", "代码": "ZN", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "天然橡胶期权", "代码": "RU", "交易所": "上期所", "五行": "木", "类型": "商品期权"},
            {"品种": "白银期权", "代码": "AG", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "螺纹钢期权", "代码": "RB", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "丁二烯橡胶期权", "代码": "BR", "交易所": "上期所", "五行": "木", "类型": "商品期权"},
            {"品种": "镍期权", "代码": "NI", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "锡期权", "代码": "SN", "交易所": "上期所", "五行": "金", "类型": "商品期权"},
            {"品种": "氧化铝期权", "代码": "AO", "交易所": "上期所", "五行": "土", "类型": "商品期权"},
            # 能源中心
            {"品种": "原油期权", "代码": "SC", "交易所": "能源中心", "五行": "火", "类型": "商品期权"},
            # 大商所
            {"品种": "豆粕期权", "代码": "M", "交易所": "大商所", "五行": "木", "类型": "商品期权"},
            {"品种": "玉米期权", "代码": "C", "交易所": "大商所", "五行": "木", "类型": "商品期权"},
            {"品种": "铁矿石期权", "代码": "I", "交易所": "大商所", "五行": "土", "类型": "商品期权"},
            {"品种": "液化气期权", "代码": "PG", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            {"品种": "聚丙烯期权", "代码": "PP", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            {"品种": "聚乙烯期权", "代码": "L", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            {"品种": "棕榈油期权", "代码": "P", "交易所": "大商所", "五行": "木", "类型": "商品期权"},
            {"品种": "苯乙烯期权", "代码": "EB", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            {"品种": "乙二醇期权", "代码": "EG", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            {"品种": "生猪期权", "代码": "LH", "交易所": "大商所", "五行": "水", "类型": "商品期权"},
            {"品种": "鸡蛋期权", "代码": "JD", "交易所": "大商所", "五行": "木", "类型": "商品期权"},
            {"品种": "原木期权", "代码": "LG", "交易所": "大商所", "五行": "木", "类型": "商品期权"},
            {"品种": "焦煤期权", "代码": "JM", "交易所": "大商所", "五行": "火", "类型": "商品期权"},
            # 郑商所
            {"品种": "棉花期权", "代码": "CF", "交易所": "郑商所", "五行": "木", "类型": "商品期权"},
            {"品种": "白糖期权", "代码": "SR", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "PTA期权", "代码": "TA", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "甲醇期权", "代码": "MA", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "菜籽粕期权", "代码": "RM", "交易所": "郑商所", "五行": "木", "类型": "商品期权"},
            {"品种": "动力煤期权", "代码": "ZC", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "纯碱期权", "代码": "SA", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "烧碱期权", "代码": "SH", "交易所": "郑商所", "五行": "水", "类型": "商品期权"},
            {"品种": "尿素期权", "代码": "UR", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "锰硅期权", "代码": "SM", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "硅铁期权", "代码": "SF", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "苹果期权", "代码": "AP", "交易所": "郑商所", "五行": "木", "类型": "商品期权"},
            {"品种": "花生期权", "代码": "PK", "交易所": "郑商所", "五行": "木", "类型": "商品期权"},
            {"品种": "短纤期权", "代码": "PF", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "玻璃期权", "代码": "FG", "交易所": "郑商所", "五行": "土", "类型": "商品期权"},
            {"品种": "对二甲苯期权", "代码": "PX", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "红枣期权", "代码": "CJ", "交易所": "郑商所", "五行": "火", "类型": "商品期权"},
            {"品种": "菜籽油期权", "代码": "OI", "交易所": "郑商所", "五行": "木", "类型": "商品期权"},
            # 广期所
            {"品种": "碳酸锂期权", "代码": "LC", "交易所": "广期所", "五行": "金", "类型": "商品期权"},
            {"品种": "工业硅期权", "代码": "SI", "交易所": "广期所", "五行": "土", "类型": "商品期权"},
        ]
        st.dataframe(pd.DataFrame(commodity_options), use_container_width=True, hide_index=True)
        st.caption(f"共 {len(commodity_options)} 个商品期权品种 | 覆盖上期所/能源中心/大商所/郑商所/广期所")

        # ═══════════════════════════════════════
        # 四、五行气场 → 期权策略
        # ═══════════════════════════════════════
        st.markdown("---")
        st.markdown("### 🌈 五行气场 → 期权策略建议")
        opt_strat = []
        for level, config in OPTION_STRATEGIES.items():
            opt_strat.append({
                "气场": level,
                "进取策略": config["aggressive"],
                "稳健策略": config["moderate"],
                "逻辑": config["description"],
            })
        st.dataframe(pd.DataFrame(opt_strat), use_container_width=True, hide_index=True)

        # ═══════════════════════════════════════
        # 五、专业策略池
        # ═══════════════════════════════════════
        with st.expander("🧩 专业期权策略池（O1~O6 六大策略详情）"):
            for ps in PRO_OPTION_STRATEGIES:
                st.markdown(f"""
                ### {ps['id']} {ps['tool']}
                - **适用**: {ps['scenario']}
                - **目的**: {ps['purpose']}
                - **建议**: {ps['recommendation']}
                ---
                """)

        # ═══════════════════════════════════════
        # 六、止损纪律
        # ═══════════════════════════════════════
        with st.expander("⚠️ 止损纪律"):
            for k, v in STOP_LOSS_DISCIPLINE.items():
                st.markdown(f"- **{k}**: {v}")

        st.warning(RISK_WARNING)


    with tab_zhuoyao:
        st.markdown("## 🐉 玄捉妖扫描系统")
        st.caption("融合五行玄学 + 实时行情 + 政策事件共振 | 5日窗口承载力推演 | 资金验证 | 地域八卦 | 捉妖池 Top 20")

        # ---- 系统状态 ----
        col_z1, col_z2, col_z3 = st.columns(3)
        with col_z1:
            zy_date = st.date_input(
                "📅 目标交易日",
                value=datetime(2026, 5, 5),
                key="zy_target_date",
                help="默认2026-05-05（巳月火旺日）"
            )
        with col_z2:
            zy_min_score = st.slider(
                "综合评分门槛",
                0.0, 100.0, 30.0, 5.0,
                key="zy_min_score",
                help="低于此分数的股票不显示"
            )
        with col_z3:
            st.markdown("")
            st.markdown("")

        # ---- 政策事件输入 ----
        st.markdown("### 📰 政策事件输入")
        col_pe1, col_pe2 = st.columns([3, 1])
        with col_pe1:
            policy_input = st.text_area(
                "输入近期重大政策/事件（每行一条）",
                value=st.session_state.get("zy_policy_template", ""),
                placeholder="碳中和政策加码\n芯片自主可控法案落地\n新型基建投资加速\n新能源补贴延续\n军工订单增长",
                height=120,
                key="zy_textarea",
                help="用回车分隔，每行一个政策事件。关键词会自动映射到五行。"
            )
            if st.session_state.get("zy_policy_template"):
                st.session_state["zy_policy_template"] = ""
        with col_pe2:
            st.caption("💡 **预设模板**")
            if st.button("🔥 火系政策", key="zy_fire", use_container_width=True):
                st.session_state["zy_policy_template"] = "碳中和政策加码\n新能源补贴延续\n芯片自主可控法案落地\n低空经济开放\n算力基建加速"
                st.rerun()
            if st.button("🛡️ 全系政策", key="zy_all", use_container_width=True):
                st.session_state["zy_policy_template"] = "碳中和政策加码\n芯片自主可控法案落地\n新型基建投资加速\n新能源补贴延续\n房地产调控放松\n军工订单增长\n医药集采缓和\n水利工程开工"
                st.rerun()
            if st.button("🧹 清空", key="zy_clear", use_container_width=True):
                st.session_state["zy_policy_template"] = ""
                st.rerun()

            # 五行映射速查
            with st.expander("📋 政策关键词→五行速查"):
                policy_wx_map = {
                    "🔥 火": "碳中和 能源转型 新能源 光伏 风电 芯片 半导体 集成电路 人工智能 大模型 算力 低空经济 航天 卫星 储能 特高压 数据要素 数字经济 游戏 传媒",
                    "💎 金": "贸易战 关税 制裁 一带一路 出海 设备更新 国防预算 军民融合 汽车 机器人 机床 家电 反倾销 出口管制",
                    "🏗️ 土": "基建投资 房地产调控 新型城镇化 城中村改造 保障房 城市更新 老旧小区改造 土地政策 消费刺激 水泥",
                    "💧 水": "水利工程 南水北调 航运政策 港口建设 海洋经济 环保督察 数字货币 跨境电商 物流 供热水务",
                    "🌿 木": "乡村振兴 农业补贴 种业振兴 医保谈判 集采 医药创新 教育改革 减税降费 以旧换新 纺织",
                }
                for wx_label, keywords in policy_wx_map.items():
                    st.markdown(f"**{wx_label}**: {keywords}")

        # ---- 扫描按钮 ----
        st.markdown("---")
        col_run1, col_run2 = st.columns([1, 3])
        with col_run1:
            run_zy = st.button("🔮 玄捉妖·全市场扫描", type="primary", use_container_width=True)
        with col_run2:
            if "zy_data" in st.session_state:
                d = st.session_state["zy_data"]
                st.caption(
                    f"上次扫描: {d.get('total_scanned', 0)}只合格 "
                    f"| 帝旺{d.get('diwang_count', 0)} | 符合预期{d.get('fuhe_count', 0)} "
                    f"| 主线共振{d.get('zhuxian_count', 0)} | 捉妖池Top20已就绪"
                )
            else:
                st.caption("首次使用请点击扫描（约需15-45秒，拉取全A股4500+只实时数据 + 八字推演）")

        if run_zy:
            date_str = zy_date.strftime("%Y-%m-%d")
            policy_list = [line.strip() for line in policy_input.split("\n") if line.strip()]

            with st.spinner(f"🐉 玄捉妖正在扫描全市场 ({date_str}) ...\n\n"
                            f"• 拉取全A股实时行情\n"
                            f"• IPO日期→日元天干\n"
                            f"• 5日窗口十二长生承载力推演\n"
                            f"• 资金验证（量价齐升/骗炮）\n"
                            f"• 月令+政策+地域八卦共振\n"
                            f"• 六维综合评分排序"):
                try:
                    data = scan_zhuoyao(date_str, policy_details=policy_list, min_composite=zy_min_score)
                    st.session_state["zy_data"] = data
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")
                    st.info("请确认: 1) akshare 已安装 (`pip install akshare`)  2) lunar-python 已安装  3) 网络连接正常")

        # ---- 展示结果 ----
        zy_data = st.session_state.get("zy_data")
        if zy_data:
            st.markdown("---")

            # ----- 天时概览卡片 -----
            st.markdown("### 🌤️ 天时四方概览")
            tgz = zy_data.get("target_ganzhi", {})
            wd = zy_data.get("window_dates", [])

            tc1, tc2, tc3, tc4, tc5 = st.columns(5)
            with tc1:
                st.metric("目标日", zy_data["target_date"])
            with tc2:
                st.metric("四柱", f"{tgz.get('year_ganzhi','')} {tgz.get('month_ganzhi','')} {tgz.get('day_ganzhi','')}")
            with tc3:
                st.metric("月令气场", f"{zy_data['month_zhi_wx'] or '?'}旺")
            with tc4:
                st.metric("政策五行", "、".join(zy_data["policy_wx_list"]) if zy_data["policy_wx_list"] else "无输入")
            with tc5:
                st.metric("窗口范围", f"{wd[0] if wd else '?'} ~ {wd[-1] if wd else '?'}")

            # 月令与政策五行关系
            mwx = zy_data.get("month_zhi_wx", "")
            pwl = zy_data.get("policy_wx_list", [])
            if mwx and pwl:
                sheng_list = [pw for pw in pwl if {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}.get(mwx) == pw or pw == mwx]
                if sheng_list:
                    st.success(f"🔥 月令{mwx} × 政策{'、'.join(sheng_list)} → 天时地利共振，{mwx}系板块优先关注")
                else:
                    st.info(f"月令{mwx} 与当前政策匪集五行不完全共振，市场可能结构性分化")

            # ----- 扫描统计 -----
            st.markdown("---")
            st.markdown("### 📊 扫描统计")
            sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
            with sc1:
                st.metric("合格股票", zy_data["total_scanned"])
            with sc2:
                st.metric("🔥 帝旺级", zy_data["diwang_count"])
            with sc3:
                st.metric("✅ 符合预期", zy_data["fuhe_count"])
            with sc4:
                st.metric("⚠️ 骗炮嫌疑", zy_data["pianpao_count"])
            with sc5:
                st.metric("⭐ 主线共振", zy_data["zhuxian_count"])
            with sc6:
                st.metric("局部共振", zy_data["jubu_count"])

            # ----- 5日承载力速判表 -----
            with st.expander("📐 5日窗口十二长生速判（各日元每日承载力）", expanded=False):
                stems_order = ["庚", "辛", "丙", "丁", "甲", "乙", "壬", "癸", "戊", "己"]
                cap_matrix = {}
                for gan in stems_order:
                    row = {}
                    for date_str in zy_data.get("window_dates", []):
                        from zhuoyao_scanner import _get_day_ganzhi, _get_stage, CAPACITY_SCORES as CS
                        gz = _get_day_ganzhi(date_str)
                        day_zhi = gz.get("day_zhi", "")
                        if day_zhi:
                            stage = _get_stage(gan, day_zhi)
                            cap = CS.get(stage, 0)
                            icon = "🔥" if cap >= 70 else ("✅" if cap >= 40 else "❄️" if cap < 0 else "·")
                            row[date_str] = f"{icon}{stage}({cap})"
                        else:
                            row[date_str] = "—"
                    cap_matrix[f"{gan}({ZY_TIANGAN_WUXING.get(gan,'')})"] = row

                st.dataframe(pd.DataFrame(cap_matrix).T, use_container_width=True)
                st.caption("🔥=强(≥70分) ✅=中(40-69) ·=弱(0-39) ❄️=极弱(<0)")

            # ----- 捉妖池 Top 20 -----
            st.markdown("---")
            st.markdown("## 🎯 捉妖候选池 TOP 20")
            st.caption("六维综合评分降序排列：承载力(35%) + 月令(20%) + 政策(15%) + 地域八卦(10%) + 资金验证(15%) + 动量(5%)")

            top20 = zy_data.get("top20", [])
            if top20:
                # 筛选器
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    zy_wx_f = st.multiselect("行业五行", ["金", "木", "水", "火", "土"], key="zy_wx_filter", placeholder="全部")
                with col_f2:
                    zy_stage_f = st.multiselect("承载力", ZY_STAGE_NAMES, key="zy_stage_filter", placeholder="全部")
                with col_f3:
                    zy_fund_f = st.multiselect("资金验证", ["符合预期", "待观察", "骗炮嫌疑", "主力撤退"], key="zy_fund_filter", placeholder="全部")
                with col_f4:
                    zy_search = st.text_input("🔍 搜索", key="zy_search", placeholder="代码/名称")

                top20_f = top20
                if zy_wx_f:
                    top20_f = [r for r in top20_f if r["wuxing"] in zy_wx_f]
                if zy_stage_f:
                    top20_f = [r for r in top20_f if r["target_stage"] in zy_stage_f]
                if zy_fund_f:
                    top20_f = [r for r in top20_f if r["fund_status"] in zy_fund_f]
                if zy_search:
                    top20_f = [r for r in top20_f if zy_search.upper() in r["code"] or zy_search in r["name"]]

                # 主表格
                t20_data = []
                for i, r in enumerate(top20_f, 1):
                    cap_icon = "🔥" if r["target_capacity"] >= 70 else ("✅" if r["target_capacity"] >= 40 else "❄️")
                    fund_icon = {"符合预期": "🚀", "主力撤退": "💨", "骗炮嫌疑": "⚠️", "待观察": "⏳"}.get(r["fund_status"], "⏳")
                    ml_icon = {"主线共振": "⭐", "局部共振": "◎", "无共振": "·"}.get(r["monthly_level"], "·")
                    t20_data.append({
                        "#": i,
                        "代码": r["code"],
                        "名称": r["name"],
                        "股价": r["price"],
                        "涨跌%": r["chg_pct"],
                        "日元": f"{r['riyuan_gan']}({r['riyuan_wx']})",
                        "行业五行": r["wuxing"],
                        "承载力": f"{cap_icon} {r['target_stage']}({r['target_capacity']})",
                        "5日趋势": r["capacity_trend"],
                        "资金验证": f"{fund_icon} {r['fund_status']}",
                        "月令共振": f"{ml_icon} {r['monthly_level']}",
                        "地域": f"{r['region_bagua']}位{r['region_wx']}" if r.get("region_bagua") else "—",
                        "综合": r["composite"],
                    })
                st.dataframe(
                    pd.DataFrame(t20_data),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "#": st.column_config.NumberColumn(width="small"),
                        "代码": st.column_config.TextColumn(width="small"),
                        "名称": st.column_config.TextColumn(width="small"),
                        "综合": st.column_config.NumberColumn(width="small"),
                    },
                )

                # ----- 个骨深度展开 -----
                st.markdown("---")
                st.markdown("### 🔍 个骨深度推演")
                st.caption("点击展开查看完整的六维评分细节")

                top20_show = top20_f[:20]
                cols_per_row = 2
                for group_start in range(0, len(top20_show), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for col_i, (stock_i, stock_col) in enumerate(zip(range(group_start, min(group_start + cols_per_row, len(top20_show))), row_cols)):
                        idx = col_i + group_start
                        if idx >= len(top20_show):
                            break
                        r = top20[idx]
                        with stock_col:
                            cap_level = "🔥🔥🔥 极强" if r["target_stage"] == "帝旺" else (
                                "★★ 偏强" if r["target_stage"] in ("临官", "冠带") else
                                "· 中性" if r["target_stage"] in ("沐浴", "长生", "衰", "养", "胎") else
                                "⚠ 偏弱"
                            )
                            fund_badge = {"符合预期": "🟢", "待观察": "🟡", "骗炮嫌疑": "🟠", "主力撤退": "🔴"}.get(r["fund_status"], "⚪")

                            with st.expander(
                                f"{fund_badge} {r['name']}({r['code']}) — {r['target_stage']} | {r['composite']}分",
                                expanded=False,
                            ):
                                st.markdown(f"""
**基础信息**
- 代码: {r['code']} | 名称: {r['name']}
- 股价: {r['price']}元 | PE: {r['pe']} | 涨跌: {r['chg_pct']}%
- 成交额: {r['volume_yi']}亿 | 换手率: {r['turnover']}%

**八字日元**
- IPO日元: {r['riyuan_gan']}({r['riyuan_wx']}) | 日柱: {r['riyuan_ganzhi']}
- 行业五行: {r['wuxing']} | 行业: {r['industry']}

**承载力推演**
- 目标日状态: **{r['target_stage']}** ({r['target_capacity']}分) → {cap_level}
- 预期区间: {r['target_expected']}
- 5日轨迹: {r['window_5d_stages']}
- 5日分值: {r['window_5d_capacities']}
- 承载力趋势: {r['capacity_trend']}

**资金验证**
- [{r['fund_confidence']}可信] {r['fund_status']}
- 判定理由: {r['fund_reason']}

**主线共振**
- 月令评级: {r['monthly_level']} (得分: {r['monthly_score']}/40)
- 共振详情: {r['monthly_detail']}

**地域八卦**
- 地域: {r['province'] or '未知'}
- 八卦位: {r['region_bagua'] or '—'} | 方位五行: {r['region_wx'] or '—'}
- 地域共振: {r['region_detail']} (得分: {r['region_score']}/30)

**综合评分: {r['composite']}/100**
""")
                                bd = r.get("composite_breakdown", {})
                                if bd:
                                    bd_str = "\n".join(f"- {k}: {v}" for k, v in bd.items())
                                    st.markdown(f"**评分明细**:\n{bd_str}")
                                st.caption("—" * 30)

                # 文本报告
                with st.expander("📋 纯文本完整报告（可复制）"):
                    st.code(format_zhuoyao_report(zy_data), language="text")
            else:
                st.warning("没有股票通过综合评分门槛筛选。尝试降低门槛分数。")

            st.warning(RISK_WARNING)

        else:
            st.info(
                "🐉 **玄捉妖扫描系统** —— 使用说明\n\n"
                "1. **选择目标交易日**（默认2026-05-05，巳月火旺）\n"
                "2. **输入政策事件**（每行一条，系统自动映射五行）—— 也可用快捷模板按钮\n"
                "3. **点击扫描**（约需15-45秒）\n\n"
                "系统将自动完成：\n"
                "- 📡 **akshare** 拉取全A股4500+实时行情\n"
                "- 🏗️ **IPO日期 → 日元天干**（股票八字排盘）\n"
                "- 🧮 **5日窗口十二长生承载力推演**（T-2 ~ T+2）\n"
                "- 🕵️ **资金验证**：量价齐升=符合预期 / 承载力增但股价滞涨=骗炮嫌疑\n"
                "- 🌐 **主线共振评分**：月令气场 × 政策五行 × 行业五行 × 地域八卦\n"
                "- 📊 **六维综合评分**(0-100) → 捉妖候选池 Top 20\n\n"
                "---\n"
                "### 🔑 核心逻辑\n"
                "| 维度 | 权重 | 说明 |\n"
                "|------|------|------|\n"
                "| 承载力 | 35% | 日元在目标日的十二长生状态 |\n"
                "| 月令共振 | 20% | 月令五行 vs 股票行业五行 |\n"
                "| 政策共振 | 15% | 政策事件五行 → 股票五行共振 |\n"
                "| 地域八卦 | 10% | 省份→八卦方位→五行共振 |\n"
                "| 资金验证 | 15% | 承载力趋势 × 股价涨跌 = 量价验证 |\n"
                "| 动量信号 | 5% | 当日涨跌幅映射 |\n\n"
                "---\n"
                "### 📋 五行行业映射速查\n"
                "| 五行 | 行业 |\n"
                "|------|------|\n"
                "| 🔥 火 | 军工/新能源/半导体/芯片/电力/煤炭/石油/化工/储能 |\n"
                "| 💎 金 | 银行/保险/证券/钢铁/有色金属/汽车/机械/家电 |\n"
                "| 🏗️ 土 | 房地产/基建/水泥/建材/工程机械/消费/农业 |\n"
                "| 💧 水 | 航运/水利/酒类/贸易/物流/渔业/环保/医药 |\n"
                "| 🌿 木 | 农业/纺织/医药/生物医药/教育/林业/食品/旅游 |\n\n"
                "---\n"
                "### 🗺️ 地域—八卦—五行映射\n"
                "| 方位 | 八卦 | 五行 | 省份 |\n"
                "|------|------|------|------|\n"
                "| 东方 | 震 | 木 | 上海、浙江、江苏、安徽 |\n"
                "| 东南 | 巽 | 木 | 福建 |\n"
                "| 南方 | 离 | 火 | 广东、广西、海南、湖南、湖北、江西 |\n"
                "| 西南 | 坤 | 土 | 四川、重庆、云南、贵州、西藏、河南 |\n"
                "| 东北 | 艮 | 土 | 山东 |\n"
                "| 西方 | 兑 | 金 | 陕西、甘肃、青海 |\n"
                "| 西北 | 乾 | 金 | 宁夏、新疆 |\n"
                "| 北方 | 坎 | 水 | 北京、天津、河北、山西、内蒙古、东北三省 |\n"
            )


    with tab_zhuoyao_futures:
        st.markdown("## 🐉 玄捉妖·期货")
        st.caption( "融合五行玄学 + 实时期货数据 + 政策事件共振 | 本气纯真翻倍 | 多空方向判定 | 捉妖池 Top 15")

        # ---- 系统状态 ----
        col_fz1, col_fz2, col_fz3 = st.columns(3)
        with col_fz1:
            fz_date = st.date_input(
                "📅 目标交易日",
                value=datetime(2026, 5, 5),
                key="fz_target_date",
                help="默认2026-05-05（巳月火旺日）",
            )
        with col_fz2:
            fz_min_score = st.slider(
                "综合评分门槛", 0.0, 100.0, 20.0, 5.0, key="fz_min_score",
            )
        with col_fz3:
            st.markdown("")
            st.markdown("")

        # ---- 政策事件输入 ----
        st.markdown("### 📰 政策/地缘事件输入")
        col_fz_e1, col_fz_e2 = st.columns([3, 1])
        with col_fz_e1:
            fz_policy = st.text_area(
                "输入近期重大政策/地缘事件（每行一条）",
                value=st.session_state.get("fz_policy_template", ""),
                placeholder="中东地缘冲突持续升级\n美联储降息预期升温\n川渝基建投资加大\n全球贸易争端加剧\nOPEC减产延期",
                height=120, key="fz_textarea",
                help="用回车分隔。关键词：中东/OPEC/贸易战/关税/基建/降息/减排/汇率..."
            )
            if st.session_state.get("fz_policy_template"):
                st.session_state["fz_policy_template"] = ""
        with col_fz_e2:
            st.caption("💡 **预设模板**")
            if st.button("🛢️ 能源危机", key="fz_energy", use_container_width=True):
                st.session_state["fz_policy_template"] = "中东地缘冲突持续升级\nOPEC宣布减产延期\n天然气供应紧张\n冬季能源需求激增"
                st.rerun()
            if st.button("📉 宏观衰退", key="fz_macro", use_container_width=True):
                st.session_state["fz_policy_template"] = "美联储降息预期升温\n全球贸易争端加剧\n中国基建投资加大\n央行购金量创新高"
                st.rerun()
            if st.button("🌾 农产危机", key="fz_crop", use_container_width=True):
                st.session_state["fz_policy_template"] = "全球气候异常乾旱频发\n大豆玉米产区受灾\n农产品价格飙升\n粮食安全政策加码"
                st.rerun()
            if st.button("🧹 清空", key="fz_clear", use_container_width=True):
                st.session_state["fz_policy_template"] = ""
                st.rerun()
            with st.expander("📋 政策关键词→五行速查"):
                st.markdown("""
**🔥 火**: 中东 地缘冲突 OPEC 产油国 导弹 空袭 石油 天然气 能源 碳中和 减排  
**💎 金**: 贸易战 关税 制裁 美联储 降息 加息 汇率 黄金 央行购金 反倾销  
**🏗️ 土**: 基建 放水 城镇化 房地产 城中村 乾旱 气候 农产品 大豆 玉米  
**💧 水**: 航运 物流 港口 海运 水运 环保 水利  
""")

        st.markdown("---")
        col_fr1, col_fr2 = st.columns([1, 3])
        with col_fr1:
            run_fz = st.button("🔮 玄捉妖·期货扫描", type="primary", use_container_width=True)
        with col_fr2:
            if "fz_data" in st.session_state:
                fd = st.session_state["fz_data"]
                st.caption(f"上次扫描: {fd.get('total_scanned',0)}个品种 | "
                           f"帝旺{fd.get('diwang_count',0)} | 本气纯真{fd.get('benqi_count',0)} | "
                           f"月令主线{fd.get('monthly_main_count',0)} | 捉妖池Top15已就绪")
            else:
                st.caption("首次使用请点击扫描（拉取六大交易所64个期货品种实时数据 + 八字推演）")

        if run_fz:
            fz_date_str = fz_date.strftime("%Y-%m-%d")
            fz_policy_list = [line.strip() for line in fz_policy.split("\n") if line.strip()]
            with st.spinner(f"🐉 玄捉妖·期货正在扫描全市场 ({fz_date_str}) ...\n\n"
                            "• 拉取六大交易所实时期货数据\n"
                            "• IPO日期→日元天干+实物五行映射\n"
                            "• 十二长生承载力推演 + 本气纯真翻倍\n"
                            "• 月令共振 + 政策事件五行映射\n"
                            "• 多空方向判定 + 资金验证\n"
                            "• 五维综合评分排序"):
                try:
                    fd = scan_futures_zhuoyao(fz_date_str, policy_details=fz_policy_list, min_composite=fz_min_score)
                    st.session_state["fz_data"] = fd
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")
                    st.info("请确认: 1) akshare已安装  2) lunar-python已安装  3) 网络正常")

        fz_data = st.session_state.get("fz_data")
        if fz_data:
            st.markdown("---")

            # ----- 天时卡片 -----
            st.markdown("### 🌤️ 天时气场")
            tgz2 = fz_data.get("target_ganzhi", {})
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            with fc1: st.metric("目标日", fz_data["target_date"])
            with fc2: st.metric("四柱", f"{tgz2.get('year_ganzhi','')} {tgz2.get('month_ganzhi','')} {tgz2.get('day_ganzhi','')}")
            with fc3: st.metric("月令气场", f"{fz_data['month_zhi_wx'] or '?'}月当令")
            with fc4: st.metric("日支", fz_data.get("day_zhi", "?"))
            with fc5: st.metric("政策五行", "、".join(fz_data["policy_wx_list"]) if fz_data["policy_wx_list"] else "无")

            mwx2 = fz_data.get("month_zhi_wx", "")
            if mwx2:
                month_advice = {
                    "木": "🌿 木月: 棉花、白糖、纸浆、橡胶 为首选多头",
                    "火": "🔥 火月: 焦煤焦炭·原油·天然气 为首选多头，贵金属偏多",
                    "金": "💎 金月: 黄金白银·有色金属 为首选多头",
                    "水": "💧 水月: 原油化工·航运指数 为首选多头",
                    "土": "🏗️ 土月: 大豆玉米豆粕·玻璃·股指 为首选多头",
                }
                st.info(month_advice.get(mwx2, ""))

            # ----- 关键统计 ----
            st.markdown("---\n### 📊 扫描统计")
            fs1, fs2, fs3, fs4, fs5, fs6 = st.columns(6)
            with fs1: st.metric("合格品种", fz_data["total_scanned"])
            with fs2: st.metric("🔥 帝旺级", fz_data["diwang_count"])
            with fs3: st.metric("⭐ 本气纯真", fz_data["benqi_count"])
            with fs4: st.metric("月令主线", fz_data["monthly_main_count"])
            with fs5: st.metric("📈 偏多", fz_data["long_count"])
            with fs6: st.metric("🚫 强制风控", fz_data["blocked_count"])

            # ----- 承载力速判表 -----
            with st.expander("📐 各类日元在今日的十二长生承载力速判表", expanded=False):
                from zhuoyao_futures_scanner import _get_stage, CAPACITY_SCORES as CS2
                stems = ["庚", "辛", "丙", "丁", "甲", "乙", "壬", "癸", "戊", "己"]
                quick_data = {}
                day_zhi2 = fz_data.get("day_zhi", "")
                for gan in stems:
                    stage2 = _get_stage(gan, day_zhi2)
                    cap2 = CS2.get(stage2, 0)
                    icon2 = "🔥" if cap2 >= 70 else ("✅" if cap2 >= 40 else "❄️" if cap2 < 0 else "·")
                    quick_data[f"{gan}({ZY_TIANGAN_WUXING.get(gan,'')})"] = f"{icon2} {stage2}({cap2})"
                st.dataframe(pd.DataFrame(list(quick_data.items()), columns=["日元", "今日承载力"]), use_container_width=True, hide_index=True)

            # ----- 捉妖池 Top 15 -----
            st.markdown("---\n## 🎯 期货捉妖候选池 TOP 15")
            st.caption("五维综合评分: 承载力(30%) + 月令共振(20%) + 事件共振(15%) + 多空验证(25%) + 动量(10%)")

            top15 = fz_data.get("top15", [])
            if top15:
                col_ff1, col_ff2, col_ff3, col_ff4 = st.columns(4)
                with col_ff1:
                    fz_wx_f = st.multiselect("实物五行", ["金","木","水","火","土"], key="fz_wx_filter", placeholder="全部")
                with col_ff2:
                    fz_stage_f = st.multiselect("承载力", ZY_STAGE_NAMES, key="fz_stage_filter", placeholder="全部")
                with col_ff3:
                    fz_dir_f = st.multiselect("方向", ["只多","偏多","多空皆可","偏空","只空","观望"], key="fz_dir_filter", placeholder="全部")
                with col_ff4:
                    fz_search = st.text_input("🔍 搜索", key="fz_search", placeholder="品种名称/代码")

                top15_f = top15
                if fz_wx_f:
                    top15_f = [r for r in top15_f if r["phys_wx"] in fz_wx_f]
                if fz_stage_f:
                    top15_f = [r for r in top15_f if r["stage"] in fz_stage_f]
                if fz_dir_f:
                    top15_f = [r for r in top15_f if r["direction"] in fz_dir_f]
                if fz_search:
                    top15_f = [r for r in top15_f if fz_search.upper() in r["symbol"] or fz_search in r["name"]]

                f15_data = []
                for i, r in enumerate(top15_f, 1):
                    bc = "⭐纯真" if r["is_benqi"] else "—"
                    mc = "✅主线" if r["monthly_main"] else "—"
                    dir_icon = {"只多":"📈🚀","偏多":"📈","多空皆可":"⚖️","偏空":"📉","只空":"📉💨","观望":"⏸️"}.get(r["direction"],"⏳")
                    rc_icon = "⛔" if "强制风控" in r["risk_control"] else "✅"
                    f15_data.append({
                        "#": i, "品种": r["name"], "代码": r["symbol"],
                        "实物五行": r["phys_wx"],
                        "日元": f"{r['riyuan_gan']}({r['riyuan_wx']})",
                        "承载力": f"{r['stage']}({r['capacity']})",
                        "本气纯真": bc, "月令主线": mc,
                        "方向": f"{dir_icon} {r['direction']}",
                        "资金": r["fund_signal"],
                        "风控": f"{rc_icon} {r['risk_control'][:4]}",
                        "综合": r["composite"],
                    })
                st.dataframe(pd.DataFrame(f15_data), use_container_width=True, hide_index=True)

                # ----- 品种展开 ----
                st.markdown("---\n### 🔍 个品深度推演")
                st.caption("点击展开查看完整五维评分与交易参数")
                for group_s in range(0, min(len(top15_f), 15), 2):
                    row_c = st.columns(2)
                    for ci, (gbi, gcol) in enumerate(zip(range(group_s, min(group_s+2, len(top15_f))), row_c)):
                        gi = group_s + ci
                        if gi >= len(top15_f): break
                        r = top15_f[gi]
                        with gcol:
                            bc_tag = "⭐ 本气纯真·承载力翻倍!" if r["is_benqi"] else ""
                            mc_tag = "✅ 月令主线共振!" if r["monthly_main"] else ""
                            tags = " ".join(filter(None, [bc_tag, mc_tag]))
                            d_icon_map = {"只多":"🚀","偏多":"📈","多空皆可":"⚖️","偏空":"📉","只空":"💨","观望":"⏸️"}
                            with st.expander(f"{d_icon_map.get(r['direction'],'⏳')} {r['name']}({r['symbol']}) — {r['direction']} | {r['composite']}分", expanded=False):
                                st.markdown(f"""
**{tags}**

**基础信息**
- 品种: {r['name']}({r['symbol']}) | 交易所: {r['exchange']}
- 合约: {r['unit']} | 保证金: {r['margin']}
- {'实时: ' + str(r['price']) + '元  |  涨跌: ' + str(r['chg_pct']) + '%' if r['chg_pct'] else '价格: 模拟数据'}

**八字日元 + 实物五行**
- IPO日元: {r['riyuan_gan']}({r['riyuan_wx']}) | 日柱: {r['riyuan_ganzhi']}
- 实物五行: {r['phys_wx']} | 同气纯真: {'✅' if r['is_benqi'] else '❌'}

**承载力推演**
- 状态: **{r['stage']}** ({r['capacity']}分)
- 预期: {r['expected']}

**月令共振** (得分: {r['monthly_score']}/30)
- {r['monthly_detail']}

**事件共振** (得分: {r['event_score']}/30)
- {r['event_detail']}

**地域八卦共振**
- {r['region_detail']}

**多空方向**: {r['direction']} | 资金信号: {r['fund_signal']}
- 判定: {r['direction_reason']}

**交易参数**
- 关键分水岭: {r['watershed']}
- 有效期: {r['valid_days']}
- 风控状态: {r['risk_control']}

**综合评分: {r['composite']}/100**
""")
                                bd = r.get("composite_breakdown", {})
                                if bd:
                                    st.markdown("**评分明细**")
                                    for k, v in bd.items():
                                        st.text(f"{k}: {v}")
                                st.caption("—" * 40)

                with st.expander("📋 纯文本完整报告（可复制）"):
                    st.code(format_futures_zhuoyao_report(fz_data), language="text")
            else:
                st.warning("没有品种通过门槛，尝试降低评分门槛。")

            st.warning(RISK_WARNING)

        else:
            st.info(
                "🐉 **玄捉妖·期货** —— 使用说明\n\n"
                "1. **选择交易日**（默认2026-05-05，巳月火旺）\n"
                "2. **输入政策/地缘事件**（每行一条）→ 快捷模板可选\n"
                "3. **点击扫描**（拉取6大交易所64个期货品种 + 八字推演）\n\n"
                "系统完成：\n"
                "- 📡 **akshare**拉取六大交易所主力合约实时价格\n"
                "- 🏗️ **品种出厂**：IPO日→日元天干 + 实物属性硬性五行二次映射\n"
                "- ⭐ **本气纯真**：日元五行==实物五行→承载力翻倍（如乙木日元+白糖/棉花=纯真）\n"
                "- 🧮 **承载力**：十二长生推演（帝旺>临官>冠带>衰>沐浴>长生）\n"
                "- 🌐 **月令共振 + 事件共振**：月令气场 × 政策关键词→五行 × 品种五行\n"
                "- 🧭 **多空方向**：承载力+价格涨跌→只多/只空/多空皆可/骗炮\n"
                "- 🚫 **强制风控**：死/墓/绝→禁止开新仓\n"
                "- 📊 **综合评分**(0-100)→捉妖池Top15\n\n"
                "---\n### 关键规则\n"
                "| 规则 | 说明 |\n"
                "|------|------|\n"
                "| 帝旺/临官 | 当日允许高仓位主力方向 |\n"
                "| 死/墓/绝 | 强制风控禁止开新仓 |\n"
                "| 本气纯真 | 日元与实物同气时承载力翻倍 |\n"
                "| 多空核验 | 承载力增强+价格齐升=真实做多 |\n"
                "| 多单骗炮 | 承载力强但价格下跌=资金未入场 |\n"
                "| 空头衰竭 | 承载力绝但跌势放缓=可能反转 |\n"
            )


    with tab_chen_nanpeng:
        st.markdown("## ⏳ 陈南鹏·五行择时系统")
        st.caption("遵循陈南鹏《仁者无敌》五行理论 | 流年干支定基调 | 流月轮动选板块 | 名称偏旁+代码数字+量价筛个股")

        col_cn1, col_cn2 = st.columns([1, 2])
        with col_cn1:
            cn_date = st.date_input(
                "📅 目标交易日",
                value=datetime(2026, 5, 5),
                key="cn_target_date",
                help="默认2026-05-05（丙午年巳月）"
            )
        with col_cn2:
            st.markdown("")
            cn_year = st.text_input("🧧 手动指定年柱（留空则自动推算）", placeholder="如: 丙午", key="cn_year_manual")

        with st.expander("📐 陈南鹏行业五行对照表（原版版图）", expanded=False):
            cna, cnb, cnc, cnd, cne = st.columns(5)
            with cna: st.markdown("**💧 水**: " + "、".join(CHENNANPENG_INDUSTRY_WUXING["水"]))
            with cnb: st.markdown("**🌿 木**: " + "、".join(CHENNANPENG_INDUSTRY_WUXING["木"]))
            cnc, cnd, cne = st.columns(3)
            with cnc: st.markdown("**🔥 火**: " + "、".join(CHENNANPENG_INDUSTRY_WUXING["火"]))
            with cnd: st.markdown("**🏗️ 土**(回避): " + "、".join(CHENNANPENG_INDUSTRY_WUXING["土"]))
            with cne: st.markdown("**💎 金**(泄气): " + "、".join(CHENNANPENG_INDUSTRY_WUXING["金"]))

        st.markdown("---")
        col_cn_run1, col_cn_run2 = st.columns([1, 3])
        with col_cn_run1:
            run_cn = st.button("🔮 陈南鹏·五行择时扫描", type="primary", use_container_width=True)
        with col_cn_run2:
            if "cn_data" in st.session_state:
                cd = st.session_state["cn_data"]
                st.caption(
                    f"上次扫描: {cd.get('total_scanned',0)}只合格 "
                    f"| 年柱{cd.get('year_ganzhi','')} "
                    f"| 得令{', '.join(cd.get('year_analysis',{}).get('de_ling',[]))} "
                    f"| 回避{cd.get('avoid_count',0)}只 | 关注{cd.get('focus_count',0)}只"
                )
            else:
                st.caption("首次使用请点击扫描（拉取全A股实时行情 + 陈南鹏五层五行推演）")

        if run_cn:
            date_str = cn_date.strftime("%Y-%m-%d")
            year_str_val = cn_year.strip() if cn_year else None

            with st.spinner(f"⏳ 陈南鹏五行择时系统正在分析 ({date_str}) ...\n\n"
                            f"• 第一层: 流年{year_str_val or '自动推演'}干支定全局基调\n"
                            f"• 第二层: 五行→行业映射（陈南鹏原版版图）\n"
                            f"• 第三层: 流月轮动筛选逐月热点\n"
                            f"• 第四层: 个股名称偏旁+代码数字+量价匹配\n"
                            f"• 第五层: 生成回避清单"):
                try:
                    data = scan_chen_nanpeng(date_str, year_str=year_str_val)
                    st.session_state["cn_data"] = data
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")
                    st.info("请确认: 1) akshare 已安装  2) lunar-python 已安装  3) 网络连接正常")

        cn_data = st.session_state.get("cn_data")
        if cn_data:
            st.markdown("---")

            ya = cn_data["year_analysis"]
            mo = cn_data["month_overlay"]

            st.markdown("### 🌤️ 第一层：流年五行基调")
            col_a1, col_a2, col_a3, col_a4 = st.columns(4)
            with col_a1: st.metric("年柱", cn_data["year_ganzhi"])
            with col_a2: st.metric("关系", ya.get("relation", ""))
            with col_a3:
                dl = ", ".join(ya.get("de_ling", []))
                st.metric("⭐ 得令", dl or "—")
            with col_a4:
                sk = ", ".join(ya.get("shou_ke", []))
                st.metric("⛔ 受克", sk or "—")

            st.markdown(f"> {ya.get('analysis', '')}")

            st.markdown("### 📅 第三层：流月轮动")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1: st.metric("农历月份", f"第{cn_data['lunar_month']}月")
            with col_m2: st.metric("月支", f"{mo.get('month_zhi','')}({mo.get('month_wuxing','')})")
            with col_m3:
                tag = "✅ 扶旺" if mo.get("supports_year") else ("⚠️ 对冲" if mo.get("opposes_year") else "· 中性")
                st.metric("月令态度", tag)

            st.info(mo.get("analysis", ""))

            st.markdown(f"#### ✅ 本月看好行业 Top 3")
            for ti in cn_data["top_industries"][:3]:
                if ti:
                    st.markdown(f"- **{ti}**")

            if cn_data["avoid_industries"]:
                st.markdown(f"#### ⛔ 本月回避行业")
                for ai in cn_data["avoid_industries"][:5]:
                    st.markdown(f"- ~~{ai}~~")

            st.markdown("---")
            st.markdown("## 🎯 个股候选池 TOP 10")
            st.caption("评分维度: 五行得令(40分) + 代码干支数(12分) + 名称偏旁 + 换手率 + 量比 → 100分")

            candidates = cn_data["candidates"][:10]
            if candidates:
                cn_table = []
                for i, c in enumerate(candidates, 1):
                    icon = { "关注": "⭐", "可轻仓试多": "👀", "回避": "⛔" }.get(c["action"], "·")
                    cn_table.append({
                        "#": i, "名称": c["name"], "代码": c["code"],
                        "五行": c["stock_wx"],
                        "换手%": c["hsl"], "量比": c["amount"],
                        "评分": c["score"], "操作": f"{icon} {c['action']}",
                        "理由": ", ".join(c["reasons"][:2]),
                    })
                st.dataframe(pd.DataFrame(cn_table), use_container_width=True, hide_index=True)

                st.markdown("---\n### 🔍 个股详情推演")
                for group_s in range(0, min(len(candidates), 10), 2):
                    row_c = st.columns(2)
                    for ci in range(2):
                        gi = group_s + ci
                        if gi >= len(candidates):
                            break
                        c = candidates[gi]
                        with row_c[ci]:
                            icon = { "关注": "⭐", "可轻仓试多": "👀", "回避": "⛔" }.get(c["action"], "·")
                            with st.expander(f"{icon} {c['name']}({c['code']}) — {c['action']} | {c['score']}分"):
                                st.text(format_cn_single(c, ya))

                with st.expander("📋 纯文本完整报告"):
                    st.code(format_chen_nanpeng_report(cn_data), language="text")
            else:
                st.warning("没有个股通过综合评分门槛。")

            st.warning(RISK_WARNING)

        else:
            st.info(
                "⏳ **陈南鹏·五行择时** —— 使用说明\n\n"
                "1. **选择交易日**（默认2026-05-05，丙午年巳月）\n"
                "2. 可选手动指定年柱（如: 壬寅、丙午、甲辰）\n"
                "3. **点击扫描**\n\n"
                "系统完成：\n"
                "- **第一层**：流年干支分析 → 得令/受克/被泄五行定性\n"
                "- **第二层**：陈南鹏原版五行→行业映射\n"
                "- **第三层**：流月地支×年令 → 本月热点板块预判\n"
                "- **第四层**：个股名称偏旁+代码数字+换手率+量比筛选\n"
                "- **第五层**：受克五行行业自动入回避清单\n\n"
                "---\n### 陈南鹏核心逻辑\n"
                "| 规则 | 含义 |\n"
                "|------|------|\n"
                "| 干生支/支生干 | 生与被生五行皆旺（吉）|\n"
                "| 干克支/支克干 | 受克五行需回避（凶）|\n"
                "| 生得令者 | 泄气走弱须谨慎 |\n"
                "| 名称偏旁 | 水氵雨/木艹林/火日光电/土石山/金钅铁 |\n"
                "| 代码数字 | 含年干数(甲1乙2...)或年支数(子1丑2...)→加分 |\n"
            )


    with tab_cn_futures:
        st.markdown("## ⏳ 陈南鹏·五行期货择时系统")
        st.caption("遵循陈南鹏《仁者无敌》五行理论 × 期货双向交易 | 量价验证 | 杠杆风控")

        col_cnf1, col_cnf2, col_cnf3 = st.columns([1, 1, 1])
        with col_cnf1:
            cnf_date = st.date_input(
                "📅 目标交易日",
                value=datetime(2026, 5, 5),
                key="cnf_target_date",
                help="默认2026-05-05"
            )
        with col_cnf2:
            cnf_year = st.text_input("🧧 手动年柱", placeholder="如: 丙午", key="cnf_year_manual")
        with col_cnf3:
            cnf_events = st.text_area(
                "📰 宏观事件（可选）",
                placeholder="中东地缘冲突持续\nOPEC减产延期\n美联储降息预期",
                height=120, key="cnf_events",
            )

        with st.expander("📐 陈南鹏期货品种五行对照表", expanded=False):
            for wx_label in ["水", "木", "火", "土", "金"]:
                items = CN_FUTURES_WUXING_PHYSICAL.get(wx_label, [])
                names = "、".join([f"{it['name']}({it['symbol']})" for it in items])
                icons = {"水": "💧", "木": "🌿", "火": "🔥", "土": "🏗️", "金": "💎"}
                bias = {"水": "偏多", "木": "偏多", "火": "偏多", "土": "偏空(被克)", "金": "偏空(泄气)"}
                st.caption(f"{icons.get(wx_label,'')} **{wx_label}** ({bias.get(wx_label,'')}): {names}")

        st.markdown("---")
        col_cnf_run1, col_cnf_run2 = st.columns([1, 3])
        with col_cnf_run1:
            run_cnf = st.button("🔮 陈南鹏·期货择时扫描", type="primary", use_container_width=True, key="cnf_run")
        with col_cnf_run2:
            if "cnf_data" in st.session_state:
                cd = st.session_state["cnf_data"]
                st.caption(
                    f"上次: 做多{cd.get('long_count',0)}只 | 做空{cd.get('short_count',0)}只 "
                    f"| 年柱{cd.get('year_ganzhi','')} | 得令{', '.join(cd.get('de_ling',[]))}"
                )

        if run_cnf:
            date_str = cnf_date.strftime("%Y-%m-%d")
            year_str_val = cnf_year.strip() if cnf_year else None

            with st.spinner(f"⏳ 陈南鹏期货择时系统分析中 ({date_str}) ...\n\n"
                            f"• 第一层: 流年干支定五行强弱\n"
                            f"• 第二层: 五行→期货品种物理映射\n"
                            f"• 第三层: 月令×年令双重叠加\n"
                            f"• 第四层: 持仓量验证+15%仓位上限+2%止损\n"
                            f"• 第五层: 宏观事件方向确认"):
                try:
                    data = scan_chen_nanpeng_futures(date_str, year_str=year_str_val, events_text=cnf_events)
                    st.session_state["cnf_data"] = data
                    st.rerun()
                except Exception as e:
                    st.error(f"扫描出错: {e}")
                    st.info("请确认: 1) akshare已安装  2) lunar-python已安装  3) 网络正常")

        cnf_data = st.session_state.get("cnf_data")
        if cnf_data:
            st.markdown("---")
            ya = cnf_data["year_analysis"]
            mo = cnf_data["month_overlay"]

            st.markdown("### 🌤️ 第一层：流年五行")
            col_cnf_a1, col_cnf_a2, col_cnf_a3, col_cnf_a4 = st.columns(4)
            with col_cnf_a1: st.metric("年柱", cnf_data["year_ganzhi"])
            with col_cnf_a2: st.metric("关系", ya.get("relation", ""))
            with col_cnf_a3: st.metric("⭐ 得令", ", ".join(cnf_data["de_ling"]))
            with col_cnf_a4: st.metric("⛔ 受克", ", ".join(cnf_data["shou_ke"]))
            st.info(f"> 全年方向：{'/'.join(cnf_data['de_ling'])}品种偏多，{'/'.join(cnf_data['shou_ke'])}品种偏空")

            st.markdown("### 📅 第三层：流月叠加")
            st.info(mo["analysis"])

            st.markdown("---")
            col_cnf_long, col_cnf_short = st.columns(2)

            with col_cnf_long:
                st.markdown("### 🟢 做多品种 TOP 5")
                if cnf_data["long_top5"]:
                    lt = []
                    for i, c in enumerate(cnf_data["long_top5"], 1):
                        lt.append({
                            "#": i, "品种": c["name"], "五行": c["wuxing"],
                            "评分": c["score"], "涨跌%": c["chg_pct"],
                            "仓位": c["verify"]["position_weight"],
                            "止损": c["stop_loss"],
                        })
                    st.dataframe(pd.DataFrame(lt), use_container_width=True, hide_index=True)
                else:
                    st.caption("无符合条件品种")

            with col_cnf_short:
                st.markdown("### 🔴 做空品种 TOP 5")
                if cnf_data["short_top5"]:
                    st2 = []
                    for i, c in enumerate(cnf_data["short_top5"], 1):
                        st2.append({
                            "#": i, "品种": c["name"], "五行": c["wuxing"],
                            "评分": c["score"], "涨跌%": c["chg_pct"],
                            "仓位": c["verify"]["position_weight"],
                        })
                    st.dataframe(pd.DataFrame(st2), use_container_width=True, hide_index=True)
                else:
                    st.caption("无符合条件品种")

            if cnf_data["neutral"]:
                st.markdown("### ⚪ 中性/观望品种")
                nt = []
                for c in cnf_data["neutral"][:5]:
                    nt.append({"品种": c["name"], "五行": c["wuxing"], "评分": c["score"]})
                st.dataframe(pd.DataFrame(nt), use_container_width=True, hide_index=True)

            if cnf_data["event_note"]:
                st.markdown(f"### 📰 事件修正\n{cnf_data['event_note']}")

            st.markdown("---\n### 🔍 品种详情")
            for group_s in range(0, 5):
                row_c = st.columns(2)
                for ci in range(2):
                    gi = group_s * 2 + ci
                    cand = None
                    all_cands = cnf_data["long_top5"] + cnf_data["short_top5"]
                    if gi < len(all_cands):
                        cand = all_cands[gi]
                    if cand:
                        with row_c[ci]:
                            dir_icon = "🟢" if cand["direction"] in ("做多", "偏多") else "🔴"
                            with st.expander(f"{dir_icon} {cand['name']}({cand['symbol']}) — {cand['direction']} | {cand['score']}分"):
                                st.text(format_futures_single_cn(cand, ya))

            with st.expander("📋 纯文本完整报告"):
                st.code(format_cn_futures_report(cnf_data), language="text")

            st.warning(RISK_WARNING)

        else:
            st.info(
                "⏳ **陈南鹏·期货择时** —— 与股票择时对照使用\n\n"
                "1. 选择交易日 + 可选手动指定年柱\n"
                "2. 可选输入宏观事件进行方向修正\n"
                "3. 点击扫描\n\n"
                "系统完成：\n"
                "- **第一层**：流年干支定五行强弱→全年多空基调\n"
                "- **第二层**：65+品种物理属性→五行映射\n"
                "- **第三层**：月令年令双重叠加→最强多/空品种\n"
                "- **第四层**：持仓量验证+≤15%单品种仓位+2%硬止损\n"
                "- **第五层**：宏观事件方向确认/冲突提示\n\n"
                "---\n### 与股票择时的关键区别\n"
                "| 维度 | 股票择时 | 期货择时 |\n"
                "|------|---------|----------|\n"
                "| 方向 | 只能做多+回避 | 双向交易（多空皆可获利）|\n"
                "| 风控 | 换手率+均线 | 持仓量+杠杆仓位上限+硬止损 |\n"
                "| 标的匹配 | 名称偏旁+代码数字 | 品种物理属性→五行 |\n"
                "| 事件修正 | 政策关键词→五行 | 地缘/宏观→方向确认/冲突 |\n"
            )


if __name__ == "__main__":
    from auto_trader import start_auto_refresh
    main()
