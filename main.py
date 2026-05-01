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
    """渲染侧边栏：配置项"""
    with st.sidebar:
        st.header("⚙️ 配置")

        # 模式选择
        st.subheader("系统模式")
        sim_mode = st.checkbox("模拟模式（不联网）", value=SIMULATE_MODE,
                               help="开启后使用内置模拟数据，不开则尝试实时抓取")

        # API Keys
        st.subheader("API 配置（可选）")
        newsapi_key = st.text_input("NewsAPI Key", type="password",
                                    placeholder="留空则使用RSS+模拟",
                                    help="https://newsapi.org/ 免费注册")
        openai_key = st.text_input("OpenAI/DeepSeek Key", type="password",
                                   placeholder="留空则使用规则引擎",
                                   help="用于增强新闻情绪解析")

        # 资产类别开关
        st.subheader("分析范围")
        show_stocks = st.checkbox("股票分析", value=True)
        show_futures = st.checkbox("期货分析", value=True)
        show_options = st.checkbox("期权策略", value=False,
                                   help="基于股票/期货推荐生成期权策略")

        # 五行偏好
        st.subheader("五行偏好")
        preferred_wuxing = st.selectbox(
            "偏好五行方向",
            ["自动", "火", "金", "土", "水", "木"],
            help="选择你偏好的五行方向，自动则根据新闻自动判定",
        )

        # 风险偏好
        risk_level = st.radio("风险偏好", ["moderate", "aggressive"],
                              index=0,
                              help="moderate=稳健策略, aggressive=激进策略")

        # 市场选择
        market = st.selectbox("股票市场", ["A股", "美股", "港股"],
                              help="选择主要分析的市场")

        st.markdown("---")
        st.caption(f"版本: v1.0 | 模式: {'模拟' if sim_mode else '实时'}")
        st.caption("玄学有风险，梭哈需谨慎 🔮")

        return {
            "sim_mode": sim_mode,
            "newsapi_key": newsapi_key,
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
def render_daily_dashboard():
    """渲染中国版三栏日推仪表盘"""

    st.markdown("## 📊 今日自动日推 — 纯A股版")

    col_state1, col_state2, col_state3, col_state4 = st.columns(4)
    now = datetime.now()
    cache_age = get_cache_age()

    with col_state1:
        st.metric("系统状态", "运行中" if cache_age < 360 else "待刷新",
                  delta=f"缓存{cache_age:.0f}s前")
    with col_state2:
        st.metric("当前时间", now.strftime("%H:%M:%S"), delta=now.strftime("%Y-%m-%d"))
    with col_state3:
        st.metric("市场", "A股", delta="纯中国版")
    with col_state4:
        st.metric("模式", "模拟" if SIMULATE_MODE else "实时",
                  delta="联网" if not SIMULATE_MODE else "本地")

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

    # --- 气场总览 ---
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

    # ============================================================
    # 三栏：买入 | 卖出 | 回避
    # ============================================================
    st.markdown("### 📈 A股推荐 — 买入10 / 卖出10 / 回避10")
    col_buy, col_sell, col_avoid = st.columns(3)

    with col_buy:
        st.markdown("#### 🟢 买入 (10只)")
        buy_stocks = today_report.get('buy_stocks', [])
        for s in buy_stocks:
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #00cc66; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_sell:
        st.markdown("#### 🔴 卖出 (10只)")
        sell_stocks = today_report.get('sell_stocks', [])
        for s in sell_stocks:
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #ff4444; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    with col_avoid:
        st.markdown("#### ⚪ 回避 (10只)")
        avoid_stocks = today_report.get('avoid_stocks', [])
        for s in avoid_stocks:
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #999999; padding-left: 8px; margin-bottom: 8px;">
                <b>{s.get('name','')}</b> <small>{s.get('code','')}</small><br>
                <small>行业:{s.get('matched_industry','')} | PE:{s.get('pe','')} | 五行:{s.get('wuxing','')}</small><br>
                <small style="color:#888;">{s.get('direction_reason','')[:40]}</small>
                </div>
                """, unsafe_allow_html=True)

    # ============================================================
    # 期货三栏
    # ============================================================
    st.markdown("### 📉 中国期货 — 买入 / 卖出 / 回避")
    col_fbuy, col_fsell, col_favoid = st.columns(3)

    with col_fbuy:
        st.markdown("#### 🟢 买入期货")
        buy_futures = today_report.get('buy_futures', [])
        for f in buy_futures:
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
        sell_futures = today_report.get('sell_futures', [])
        for f in sell_futures:
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
        avoid_futures = today_report.get('avoid_futures', [])
        for f in avoid_futures:
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid #999999; padding-left: 8px; margin-bottom: 8px;">
                <b>{f.get('name','')}</b> <small>{f.get('exchange','')}</small><br>
                <small>{f.get('entry_signal','')[:30]}</small>
                </div>
                """, unsafe_allow_html=True)

    # ============================================================
    # 期权策略
    # ============================================================
    st.markdown("### 🎲 中国期权策略建议")
    opts = today_report.get('options_summary', {})
    if opts:
        st.info(f"**推荐策略**: {opts.get('strategy', '')}")
        targets = opts.get('suggested_targets', [])
        if targets:
            for t in targets:
                st.markdown(f"- {t}")
        st.caption(opts.get('note', ''))

    # 胜率
    winrate = today_report.get('win_rate', {})
    if winrate:
        with st.expander("🎯 玄学胜率"):
            if 'multi_period' in winrate:
                wr_cols = st.columns(3)
                for i, (label, val) in enumerate(winrate['multi_period'].items()):
                    with wr_cols[i]:
                        st.metric(label, val)
            st.caption(winrate.get('note', ''))

    # 历史
    with st.expander("📅 历史日推 (近7天)"):
        hist = load_historical_reports(days=7)
        if hist:
            for h in hist:
                rid = h.get('report_id', '')
                gen_time = h.get('generated_at', '')
                bc = len(h.get('buy_stocks', []))
                sc = len(h.get('sell_stocks', []))
                ac = len(h.get('avoid_stocks', []))
                st.markdown(f"- **{rid}** ({gen_time}): 买{bc}/卖{sc}/回避{ac} | \u4e94\u884c「{h.get('dominant_wuxing', '')}」{h.get('boost_level', '')}")
        else:
            st.caption("暂无历史报告")

    st.warning(RISK_WARNING)


# ============================================================
# 主函数
# ============================================================
def main():
    """主入口"""
    from auto_trader import generate_daily_report, load_today_report, load_historical_reports, start_auto_refresh

    load_custom_config()
    start_auto_refresh(interval_minutes=5)

    config = render_sidebar()

    tab_daily, tab_manual, tab_knowledge = st.tabs([
        "📊 自动日推(A股)", "✍️ 手动分析", "📚 知识库"
    ])

    with tab_daily:
        render_daily_dashboard()

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


if __name__ == "__main__":
    from auto_trader import start_auto_refresh
    main()
