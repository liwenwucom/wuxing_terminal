# -*- coding: utf-8 -*-
"""
五行韭菜盘 —— 全天候后台监控守护进程
自动扫描 → 弹窗列表提醒 → 桌面通知 → 微信推送

复用现有 auto_trader 日报引擎，不做重复造轮子。
无需打开浏览器，纯后台运行，适合常开 Windows PC。

运行方式：
    python monitor.py              # 前台运行，Ctrl+C 停止
    双击 monitor_start.bat         # 一键启动
"""

import sys
import os
import time
import subprocess
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# 用户配置区 —— 改这里就行，不用动代码
# ============================================================
CONFIG = {
    # --- 分析模式 ---
    # "wuxing" = 五行离线模式（规则引擎，不消耗API）
    # "networked" = 联网模式（NewsAPI + 智谱AI，需配置环境变量）
    # "hybrid" = 混合模式（五行扫盘 + AI分析叠加上下文，推荐）
    "analysis_mode": "hybrid",

    # --- 弹窗提醒 ---
    "popup_enabled": True,          # 是否弹窗（tkinter列表窗口）
    "popup_on_diwang": True,        # 帝旺级品种触发弹窗
    "popup_on_lingguan": False,     # 临官/冠带级也弹窗
    "popup_on_news": True,          # 新闻关键词命中时弹窗
    "popup_max_items": 10,          # 弹窗最多显示几条

    # --- 桌面弹窗通知（右下角简要提醒）---
    "toast_enabled": False,         # Windows 右下角弹窗（默认关，因为有了大弹窗）

    # --- 微信推送（Server酱）---
    "wechat_enabled": False,        # 是否启用微信推送
    "wechat_sckey": "",            # Server酱 SendKey，https://sct.ftqq.com/

    # --- 日报生成 ---
    "morning_report_time": "09:00", # 早盘日报生成时间
    "market_open_check": True,      # 盘中是否定时扫描
    "check_interval_minutes": 10,   # 盘中扫描间隔（分钟）

    # --- 预警阈值 ---
    "diwang_alert": True,           # 出现帝旺级品种时提醒
    "diwang_max_items": 5,          # 帝旺品种最多提醒几个
    "lingguan_alert": False,        # 是否也提醒临官/冠带级

    # --- 期货品种额外监控 ---
    "futures_track": [
        "AU", "SC", "CU", "RB", "I",
    ],

    # --- 新闻关键词（出现即提醒）---
    "news_keywords": [
        "降准", "降息", "加息", "关税", "制裁",
        "停火", "战争", "石油暴涨", "石油暴跌", "熔断",
    ],
}

# API Key 从环境变量读取（永不硬编码）
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# ============================================================
# 基础工具
# ============================================================

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "monitor.log"
PID_FILE = BASE_DIR / "monitor.pid"
POPUP_SCRIPT = BASE_DIR / "alert_popup.py"

_GLOBAL_ALERT_ITEMS = []       # 累积的预警项（供弹窗展示）
_AI_CONTEXT = {}               # AI 分析上下文
_ALERT_LOCK = threading.Lock()


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _accumulate_alert(item: dict):
    """将预警项加入累积列表"""
    with _ALERT_LOCK:
        _GLOBAL_ALERT_ITEMS.append(item)
        if len(_GLOBAL_ALERT_ITEMS) > 50:
            _GLOBAL_ALERT_ITEMS[:] = _GLOBAL_ALERT_ITEMS[-50:]


# ============================================================
# 弹窗提醒（通过 subprocess 调用 alert_popup.py）
# ============================================================

def show_popup(title: str, items: list, context: dict = None, summary: str = ""):
    """弹出 tkinter 列表窗口"""
    if not CONFIG["popup_enabled"]:
        return
    if not POPUP_SCRIPT.exists():
        log("弹窗脚本 alert_popup.py 不存在，跳过弹窗")
        return

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "context": context or {},
        "items": items,
        "summary": summary,
    }

    try:
        proc = subprocess.Popen(
            [sys.executable, str(POPUP_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.communicate(input=json.dumps(data, ensure_ascii=False).encode("utf-8"), timeout=1)
    except Exception as e:
        log(f"弹窗启动失败: {e}")


# --- 桌面弹窗 ---
def toast(title: str, message: str):
    if not CONFIG["toast_enabled"]:
        return
    try:
        from plyer import notification
        notification.notify(
            title=title, message=message,
            app_name="五行韭菜盘", timeout=6,
        )
    except Exception:
        pass


# --- 微信推送 ---
def wechat_push(title: str, content: str):
    sckey = CONFIG.get("wechat_sckey", "")
    if not CONFIG["wechat_enabled"] or not sckey:
        return
    try:
        import requests
        url = f"https://sctapi.ftqq.com/{sckey}.send"
        requests.post(url, data={"title": title, "desp": content}, timeout=10)
    except Exception as e:
        log(f"微信推送异常: {e}")


# ============================================================
# 核心：调用现有日报引擎 → 提取关键信息 → 弹窗
# ============================================================

def generate_and_scan() -> dict:
    log("正在生成日报（调用 auto_trader.generate_daily_report）...")
    from auto_trader import generate_daily_report
    report = generate_daily_report()
    log(f"日报生成完成: 买入{len(report.get('buy_stocks',[]))}只 "
        f"卖出{len(report.get('sell_stocks',[]))}只 "
        f"回避{len(report.get('avoid_stocks',[]))}只")
    return report


def scan_diwang_stocks(report: dict) -> list:
    results = []
    for section, label in [("buy_stocks", "买入"), ("sell_stocks", "卖出"), ("avoid_stocks", "回避")]:
        for s in report.get(section, []):
            stage = s.get("chang_sheng_name", "")
            if stage == "帝旺":
                results.append({**s, "section": label})
            elif CONFIG["lingguan_alert"] and stage in ("临官", "冠带"):
                results.append({**s, "section": label})
    return results


def build_alert_items(report: dict, networked_report: dict = None) -> list:
    """从五行报告 + AI 分析中提取弹窗条目"""
    items = []

    diwang_list = scan_diwang_stocks(report)
    for d in diwang_list:
        item = {
            "name": d.get("name", ""),
            "code": d.get("code", ""),
            "stage": d.get("chang_sheng_name", ""),
            "timing": d.get("timing_signal", "等"),
            "expected": d.get("expected_range", ""),
            "hint": f"{d.get('section','')} | {d.get('direction_reason','')[:30]}",
        }
        items.append(item)

    # 期货买入
    for f in report.get("buy_futures", [])[:3]:
        items.append({
            "name": f.get("name", ""),
            "code": "",
            "stage": "期货",
            "timing": "",
            "expected": "",
            "hint": f"买入 | {f.get('entry_signal','')[:25]}",
        })

    # AI 分析（作为独立条目）
    if networked_report:
        stocks = networked_report.get("stocks", {}) or {}
        if stocks.get("sentiment"):
            items.append({
                "name": "AI分析",
                "code": "",
                "stage": "联网",
                "timing": "",
                "expected": stocks.get("sentiment", ""),
                "hint": stocks.get("suggested_action", "")[:40],
            })

    return items[:CONFIG["popup_max_items"]]


def alert_with_popup(report: dict, networked_report: dict = None):
    """构建并弹出预警窗口"""
    items = build_alert_items(report, networked_report)

    if not items:
        log("本日无触发预警的品种")
        return

    context = {
        "ganzhi": report.get("ganzhi", ""),
        "dominant_wuxing": report.get("dominant_wuxing", ""),
        "boost_level": report.get("boost_level", ""),
    }

    if networked_report:
        stocks = networked_report.get("stocks", {}) or {}
        context["ai_sentiment"] = stocks.get("sentiment", "")

    diwang_count = sum(1 for i in items if i["stage"] == "帝旺")
    summary = f"帝旺 {diwang_count} 只 | 共 {len(items)} 条预警 | {report.get('boost_level','')}气场"

    show_popup("五行韭菜盘 · 日推预警", items, context, summary)

    # 桌面简要通知
    toast("🔮 五行韭菜盘", f"帝旺{diwang_count}只 | {report['dominant_wuxing']}气场{report['boost_level']}")

    # 微信推送
    if items:
        wx_lines = [
            f"> 干支: {report.get('ganzhi','')} | 五行: **{report.get('dominant_wuxing','')}**",
            f"> 气场: **{report.get('boost_level','')}**",
            "",
        ]
        for i in items[:5]:
            wx_lines.append(
                f"- **{i['name']}** | {i['stage']} | "
                f"择时:{i['timing']} | {i['expected']} | {i['hint']}"
            )
        wechat_push(
            f"🔮 五行韭菜盘 {datetime.now().strftime('%m/%d')}",
            "\n".join(wx_lines),
        )


# ============================================================
# 联网分析引擎（NewsAPI + 智谱 AI）
# ============================================================

def run_networked_analysis():
    if not NEWSAPI_KEY:
        log("联网分析跳过: NEWSAPI_KEY 未设置")
        return None
    if not ZHIPU_API_KEY:
        log("联网分析跳过: ZHIPU_API_KEY 未设置")
        return None

    log("正在执行联网AI分析（NewsAPI + 智谱 GLM-4-Flash）...")
    try:
        from llm_analyzer import generate_networked_report
        report = generate_networked_report(NEWSAPI_KEY, ZHIPU_API_KEY)
        if report.get("error"):
            log(f"联网分析异常: {report['error']}")
            return None
        cn = report.get("china_news_count", 0)
        gl = report.get("global_news_count", 0)
        log(f"联网分析完成: 中国经济新闻{cn}条 + 全球经济新闻{gl}条")
        return report
    except Exception as e:
        log(f"联网分析失败: {e}")
        return None


# ============================================================
# 新闻监控（RSS + 关键词）
# ============================================================

_seen_news = set()
_news_alerts = []

def check_news():
    global _news_alerts
    try:
        from news_fetcher import fetch_and_parse
        news_items = fetch_and_parse(max_items=10)
        for item in news_items:
            title = item.get("title", "")
            if not title or title in _seen_news:
                continue
            _seen_news.add(title)

            text = title + " " + item.get("content", "")
            for kw in CONFIG["news_keywords"]:
                if kw in text:
                    msg = f"新闻提醒: {title}"
                    log(msg)
                    _news_alerts.append({"title": title, "kw": kw, "time": datetime.now().strftime("%H:%M")})

                    if CONFIG["popup_on_news"] and len(_news_alerts) <= 5:
                        news_items_popup = [
                            {
                                "name": a["title"][:40],
                                "code": "",
                                "stage": "新闻",
                                "timing": a["kw"],
                                "expected": "",
                                "hint": a["time"],
                            }
                            for a in _news_alerts[-5:]
                        ]
                        show_popup("五行韭菜盘 · 新闻预警", news_items_popup, {}, "关键词命中")
                    else:
                        toast("📰 新闻预警", title)
                    break

        if len(_seen_news) > 200:
            to_remove = list(_seen_news)[:100]
            for r in to_remove:
                _seen_news.discard(r)
        if len(_news_alerts) > 50:
            _news_alerts = _news_alerts[-30:]

    except Exception as e:
        log(f"新闻监控异常: {e}")


# ============================================================
# 盘中定时扫描
# ============================================================

def is_trading_time() -> bool:
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.time()
    return (
        (t.hour == 9 and t.minute >= 30) or
        (t.hour == 10) or
        (t.hour == 11 and t.minute <= 30) or
        (t.hour == 13) or
        (t.hour == 14)
    )


def intraday_scan():
    if not CONFIG["market_open_check"]:
        return
    if not is_trading_time():
        return
    log("盘中扫描...")
    check_news()


# ============================================================
# 调度主循环
# ============================================================

def schedule_loop():
    log("监控守护进程启动")
    mode = CONFIG.get("analysis_mode", "hybrid")
    log(f"分析模式: {mode} | 弹窗={CONFIG['popup_enabled']} "
        f"微信推送={CONFIG['wechat_enabled']} "
        f"扫描间隔={CONFIG['check_interval_minutes']}分钟")
    if mode in ("networked", "hybrid"):
        log(f"NewsAPI Key: {'已配置' if NEWSAPI_KEY else '未设置（将跳过）'}")
        log(f"智谱AI Key: {'已配置' if ZHIPU_API_KEY else '未设置（将跳过）'}")

    now = datetime.now()
    target_h, target_m = map(int, CONFIG["morning_report_time"].split(":"))
    morning_target = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
    if morning_target < now:
        morning_target += timedelta(days=1)

    wait_seconds = (morning_target - now).total_seconds()
    log(f"等待 {wait_seconds / 60:.0f} 分钟到首次日报 ({CONFIG['morning_report_time']})")

    last_report_date = None
    last_intraday_check = None

    while True:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y%m%d")

            if last_report_date != today_str:
                t = now.time()
                target_t = t.replace(hour=target_h, minute=target_m, second=0)
                if t >= target_t:
                    log(f"===== 开始生成 {today_str} 日推报告 =====")
                    mode = CONFIG.get("analysis_mode", "hybrid")

                    report = None
                    networked = None

                    if mode in ("wuxing", "hybrid"):
                        try:
                            report = generate_and_scan()
                        except Exception as e:
                            log(f"五行日报生成异常: {e}")

                    if mode in ("networked", "hybrid"):
                        try:
                            networked = run_networked_analysis()
                        except Exception as e:
                            log(f"联网分析异常: {e}")

                    if report or networked:
                        alert_with_popup(report or {}, networked)

                    last_report_date = today_str
                    last_intraday_check = None

            if (CONFIG["market_open_check"] and is_trading_time() and
                (last_intraday_check is None or
                 (now - last_intraday_check).total_seconds() >= CONFIG["check_interval_minutes"] * 60)):
                intraday_scan()
                last_intraday_check = now

            time.sleep(30)

        except KeyboardInterrupt:
            log("收到停止信号，监控守护进程退出")
            break
        except Exception as e:
            log(f"主循环异常: {e}")
            time.sleep(60)


# ============================================================
# 进程管理
# ============================================================

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def is_already_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x0400, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
    except Exception:
        pass
    return False


# ============================================================
# 入口
# ============================================================

def main():
    os.chdir(str(BASE_DIR))

    if not (BASE_DIR / "auto_trader.py").exists():
        log("错误：请在 wuxing_terminal 目录下运行本脚本")
        sys.exit(1)

    if is_already_running():
        log("监控守护进程已在运行中，请勿重复启动")
        sys.exit(0)

    write_pid()

    log("=" * 40)
    log("五行韭菜盘 · 后台监控守护进程")
    log("=" * 40)

    try:
        schedule_loop()
    finally:
        remove_pid()


if __name__ == "__main__":
    main()
