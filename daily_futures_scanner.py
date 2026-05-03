# -*- coding: utf-8 -*-
"""
期货每日自动扫盘脚本 (CLI版)
—— 无需 Streamlit UI，可直接定时运行

用法:
    python daily_futures_scanner.py                       # 扫描今天
    python daily_futures_scanner.py --date 2026-05-06     # 指定日期
    python daily_futures_scanner.py --output ./reports    # 保存报告到目录
    python daily_futures_scanner.py --top 15              # 显示TOP15

输出:
    - 控制台: 美化的TOP10表格 + 各五行分布 + 综述
    - 文件:   reports/daily_futures_YYYY-MM-DD.md
"""

import sys
import os
import argparse
from datetime import datetime

try:
    from futures_bazi_picker import (
        generate_futures_top10,
        format_futures_top10_table,
        scan_all_futures_daily,
        generate_futures_bazi_report,
        scan_triple_resonance,
        generate_diwang_linguan_detail,
    )
    from futures_picker import get_main_contract
    from futures_picker import FUTURES_IPO_DATE_MAP, search_futures
    from config import RISK_WARNING
except ImportError as e:
    print(f"导入错误: {e}")
    print("请在项目根目录运行: cd wuxing_terminal && python daily_futures_scanner.py")
    sys.exit(1)


HEADER = """
╔══════════════════════════════════════════════════════════╗
║         八字期货/期权 · 每日自动扫盘引擎 v1.0           ║
║   基于十二长生承载力 + 专业评级 + 月度轮动综合评分      ║
╚══════════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 58


def print_colored(text, color=None):
    """简单着色打印（Windows CMD 可能不支持，作为降级方案）"""
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
        "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
        "bold": "\033[1m", "reset": "\033[0m",
    }
    if color and color in colors:
        try:
            print(f"{colors[color]}{text}{colors['reset']}")
            return
        except Exception:
            pass
    print(text)


def print_top10_console(top10):
    """在控制台打印美化的TOP10表格"""
    print(f"\n{SEPARATOR}")
    print(f"  扫描日期: {top10['trade_date']}")
    print(f"  品种总数: {top10['total_scanned']}")
    print(f"  月度轮动: {' + '.join(top10['rotation_elements'])}")
    print(f"  多头品种: {top10['bullish_count']} | 空头品种: {top10['bearish_count']}")
    print(f"\n  合约选择: 基于首个合约上市日期（八字原点）推演，主力合约示例供实盘参考")
    print(SEPARATOR)

    col_widths = [5, 14, 8, 8, 16, 12, 30, 18]
    headers = ["排名", "品种", "主力合约", "日元", "承载力", "阶段定性", "期权买方策略", "期权卖方策略"]

    header_line = f"{headers[0]:^{col_widths[0]}} | {headers[1]:<{col_widths[1]}} | {headers[2]:^{col_widths[2]}} | {headers[3]:^{col_widths[3]}} | {headers[4]:^{col_widths[4]}} | {headers[5]:<{col_widths[5]}} | {headers[6]:<{col_widths[6]}} | {headers[7]:<{col_widths[7]}}"
    sep_line = "-" * len(header_line)
    print(sep_line)
    print(header_line)
    print(sep_line)

    for i, r in enumerate(top10["top10"]):
        tag = "+" if r["composite"] >= 0.25 else ("-" if r["composite"] < -0.1 else "~")
        main_ct = get_main_contract(r["symbol"])
        row = (
            f"{tag}#{i+1}".center(col_widths[0]) + " | " +
            f"{r['name']}({r['symbol']})".ljust(col_widths[1]) + " | " +
            f"{main_ct}".center(col_widths[2]) + " | " +
            f"{r['riyuan_gan']}({r['futures_wuxing']})".center(col_widths[3]) + " | " +
            f"{r['star']} {r['stage']}".center(col_widths[4]) + " | " +
            f"{r['phase_label']}".ljust(col_widths[5]) + " | " +
            f"{r['opt_buyer']}".ljust(col_widths[6]) + " | " +
            f"{r['opt_seller']}".ljust(col_widths[7])
        )
        print(row)
    print(sep_line)


def print_triple_resonance_console(triple):
    """打印三重共振扫描结果"""
    print(f"\n{SEPARATOR}")
    print("  三重共振扫描（天时 x 券商人气 x 板块政策）")
    print(f"  月度干支: {triple['month_ganzhi']} | 轮动: {'+'.join(triple['rotation_elements'])}")
    print(SEPARATOR)

    if not triple["hits"]:
        print("  当日无品种同时满足三重共振条件")
        return

    print(f"  共振品种数: {triple['count']}")
    print(f"  {'品种':<22s} | {'天时':<20s} | {'人气':>4s} | {'政策共振':<12s} | 综合评级")
    print(f"  {'-'*22}-+-{'-'*20}-+-{'-'*4}-+-{'-'*12}-+------")
    for h in triple["hits"]:
        print(f"  {h['name'] + '(' + h['symbol'] + ')':<22s} | {h['star'] + ' ' + h['stage']:<20s} | {h['popularity_count']:>4d} | {h['rotation_match'] + '利好':<12s} | {h['rating']}")


def print_wuxing_distribution(scan):
    """打印五行分布"""
    wx_count = {}
    for r in scan["results"]:
        wx = r["futures_wuxing"]
        wx_count[wx] = wx_count.get(wx, 0) + 1

    bars = {"金": "#", "木": "=", "水": "~", "火": "+", "土": "."}
    print(f"\n  五行分布:")
    for wx in ["金", "木", "水", "火", "土"]:
        count = wx_count.get(wx, 0)
        bar_char = bars.get(wx, "#")
        bar = bar_char * max(1, count)
        print(f"    {wx}: {bar} {count}个")


def print_diwang_linguan_console(details):
    """打印帝旺/临官级品种完整推演"""
    if not details:
        return
    print(f"\n{SEPARATOR}")
    print("  帝旺/临官级品种完整推演")
    print(SEPARATOR)
    for d in details:
        print(f"\n  [{d['name']} ({d['symbol']})]")
        print(f"    上市日期:  {d['ipo_date']} -> 日柱: {d['riyuan_ganzhi']} -> 日元: {d['riyuan_gan']}({d['riyuan_wuxing']})")
        print(f"    交易日干支: {d['trade_ganzhi']}")
        print(f"    承载力:     {d['chang_sheng']} ({d['star_display']})")
        print(f"    期货方向:   {d['direction']}")
        print(f"    券商推荐:   {d['popularity']}")
        print(f"    开仓条件:   {d['entry_condition']}")
        print(f"    止损建议:   {d['stop_loss']}")
        print(f"    期权策略:   {d['option_detail']}")


def generate_report_file(top10, scan, output_dir):
    """生成并保存 Markdown 报告文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    date_str = top10["trade_date"].replace("-", "")
    filename = os.path.join(output_dir, f"daily_futures_{top10['trade_date']}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 八字期货/期权每日扫盘报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**扫描日期**: {top10['trade_date']}\n\n")
        f.write(f"**品种总数**: {top10['total_scanned']}\n\n")
        f.write(f"**月度轮动五行**: {' + '.join(top10['rotation_elements'])}\n\n")

        f.write(format_futures_top10_table(top10))
        f.write("\n\n")

        f.write("## 全部品种详细评分\n\n")
        f.write("| 排名 | 品种 | 日元 | 承载力 | 评分 | 阶段定性 | 买方策略 |\n")
        f.write("|------|------|------|--------|------|----------|----------|\n")
        for i, r in enumerate(scan["results"]):
            f.write(
                f"| {i+1} | {r['name']}({r['symbol']}) | {r['riyuan_gan']}({r['futures_wuxing']}) | {r['star']} {r['stage']} | {r['composite']:.3f} | {r['phase_label']} | {r['opt_buyer']} |\n"
            )

        f.write("\n---\n\n")
        f.write(RISK_WARNING.replace("\n", "\n\n"))
        f.write("\n")

    return filename


def main():
    parser = argparse.ArgumentParser(
        description="八字期货/期权每日自动扫盘脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python daily_futures_scanner.py                        # 扫描今天
  python daily_futures_scanner.py --date 2026-05-06      # 指定日期
  python daily_futures_scanner.py --output ./reports     # 保存报告
  python daily_futures_scanner.py --top 15               # TOP15
  python daily_futures_scanner.py --symbol AU            # 单独分析黄金
        """,
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="目标交易日 (YYYY-MM-DD)，默认今天"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="./reports",
        help="报告输出目录 (默认 ./reports)"
    )
    parser.add_argument(
        "--top", type=int, default=10,
        help="显示TOP N品种 (默认 10)"
    )
    parser.add_argument(
        "--symbol", "-s", type=str, default=None,
        help="单独分析指定品种 (如 AU / 黄金 / SC), 多个用逗号分隔"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="不保存报告文件，仅控制台输出"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="列出所有支持的期货品种"
    )

    args = parser.parse_args()

    if args.list:
        print("\n支持的期货品种:\n")
        for sym, ipo in sorted(FUTURES_IPO_DATE_MAP.items()):
            print(f"  {sym:6s}  上市: {ipo}")
        print(f"\n共 {len(FUTURES_IPO_DATE_MAP)} 个品种\n")
        return

    print(HEADER)

    trade_date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.symbol:
        symbols = [s.strip() for s in args.symbol.split(",")]
        for sym in symbols:
            matches = search_futures(sym)
            if matches:
                info = matches[0]
                print(f"\n{'='*58}")
                print(f"  单独分析: {info['name']} ({info['symbol']})")
                print(f"{'='*58}")
                report = generate_futures_bazi_report(info["symbol"], trade_date_str)
                print(f"  日元: {report['riyuan_gan']}({report['riyuan_wuxing']})")
                print(f"  承载力: {report['star_display']} {report['chang_sheng_stage']}")
                print(f"  预期: {report['expected_range']}")
                print(f"  择时: {report['action']}")
                print(f"  买方: {report['option_bs']['buyer_strategy'] if report['option_bs'] else '-'}")
                print(f"  卖方: {report['option_bs']['seller_strategy'] if report['option_bs'] else '-'}")
                print(f"  结论: {report['conclusion']}")
            else:
                print(f"  未找到品种: {sym}")
        return

    print(f"\n  [1/3] 正在扫描全部期货品种 ({trade_date_str}) ...")

    try:
        scan = scan_all_futures_daily(trade_date_str)
        print(f"  [2/3] 扫描完成, 共 {scan['total_scanned']} 个品种")
    except Exception as e:
        print_colored(f"\n  扫描失败: {e}", "red")
        sys.exit(1)

    print(f"  [3/3] 正在评分排序并匹配期权策略 ...")

    top10 = generate_futures_top10(trade_date_str)
    if args.top != 10:
        top10["top10"] = scan["results"][:args.top]

    print("\n")
    print_colored(f"  {top10['summary']}", "bold")

    print_top10_console(top10)
    print_wuxing_distribution(scan)

    triple = scan_triple_resonance(trade_date_str)
    print_triple_resonance_console(triple)

    details = generate_diwang_linguan_detail(trade_date_str)
    print_diwang_linguan_console(details)

    if not args.no_save:
        try:
            filename = generate_report_file(top10, scan, args.output)
            print(f"\n  [OK] 报告已保存: {filename}")
        except Exception as e:
            print(f"\n  [WARN] 报告保存失败: {e}")

    print(f"\n{SEPARATOR}")
    print_colored("  推演完成！", "green")
    print(f"{SEPARATOR}\n")

    print("  免责声明: 本报告基于八字十二长生理论框架推演，")
    print("  仅为传统文化视角的沙盘演练，不构成任何投资建议。")
    print("  期货/期权交易风险极高，可能亏损超过本金。")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    main()
