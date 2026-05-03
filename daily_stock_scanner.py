# -*- coding: utf-8 -*-
"""
A股每日自动扫盘脚本 (CLI版)
—— 无需 Streamlit UI，可直接定时运行

用法:
    python daily_stock_scanner.py                       # 扫描今天
    python daily_stock_scanner.py --date 2026-05-06     # 指定日期
    python daily_stock_scanner.py --output ./reports    # 保存报告到目录
    python daily_stock_scanner.py --top 15              # 显示TOP15

输出:
    - 控制台: 美化的TOP10表格 + 五行分布 + 三重共振 + 龙头推演
    - 文件:   reports/daily_stock_YYYY-MM-DD.md
"""

import sys
import os
import argparse
from datetime import datetime

try:
    from stock_bazi_scanner import (
        generate_stock_top10,
        format_stock_top10_table,
        scan_all_stocks_daily,
        scan_stock_triple_resonance,
        generate_stock_diwang_detail,
    )
    from stock_bazi_scanner import (
        STOCK_SECTOR_WUXING, _resolve_stock_name, _resolve_stock_sector,
    )
    from bazi_picker import generate_bazi_report
    from bazi_capacity import IPO_DATE_MAP
    from config import RISK_WARNING
except ImportError as e:
    print(f"Import error: {e}")
    print("Please run from project root: cd wuxing_terminal && python daily_stock_scanner.py")
    sys.exit(1)


HEADER = """
+==========================================================+
|        A股八字自动扫盘引擎 v1.0                            |
|   基于十二长生承载力 + 券商金股人气 + 政策共振              |
+==========================================================+
"""

SEPARATOR = "-" * 60


def print_top10_console(top10):
    """控制台美化打印TOP10"""
    print(f"\n{SEPARATOR}")
    print(f"  Scan Date: {top10['trade_date']}")
    print(f"  Total Stocks: {top10['total_scanned']}")
    print(f"  Monthly Rotation: {' + '.join(top10['rotation_elements'])}")
    print(f"  Bullish: {top10['bullish_count']} | Bearish: {top10['bearish_count']}")
    print(SEPARATOR)

    col_widths = [5, 16, 8, 16, 10, 16]
    headers = ["Rank", "Stock", "RiYuan", "Capacity", "Phase", "Sector"]

    hdr = f"{headers[0]:^{col_widths[0]}} | {headers[1]:<{col_widths[1]}} | {headers[2]:^{col_widths[2]}} | {headers[3]:^{col_widths[3]}} | {headers[4]:<{col_widths[4]}} | {headers[5]:<{col_widths[5]}}"
    sep_line = "-" * len(hdr)
    print(sep_line)
    print(hdr)
    print(sep_line)

    for i, r in enumerate(top10["top10"]):
        tag = "+" if r["composite"] >= 0.25 else ("-" if r["composite"] < -0.1 else "~")
        row = (
            f"{tag} #{i+1}".center(col_widths[0]) + " | " +
            f"{r['name']}({r['code']})".ljust(col_widths[1]) + " | " +
            f"{r['riyuan_gan']}({r['riyuan_wuxing']})".center(col_widths[2]) + " | " +
            f"{r['star']} {r['stage']}".center(col_widths[3]) + " | " +
            f"{r['phase_label']}".ljust(col_widths[4]) + " | " +
            f"{r['sector']}".ljust(col_widths[5])
        )
        print(row)
    print(sep_line)


def print_wuxing_distribution(scan):
    """五行分布打印"""
    wx_count = {}
    for r in scan["results"]:
        wx = r["stock_wuxing"]
        wx_count[wx] = wx_count.get(wx, 0) + 1

    bars = {"金": "#", "木": "=", "水": "~", "火": "+", "土": "."}
    print(f"\n  Five Elements Distribution:")
    for wx in ["金", "木", "水", "火", "土"]:
        count = wx_count.get(wx, 0)
        bar_char = bars.get(wx, "#")
        bar = bar_char * max(1, count)
        print(f"    {wx}: {bar} {count}")


def print_triple_resonance_console(triple):
    """三重共振打印"""
    print(f"\n{SEPARATOR}")
    print("  Triple Resonance (TianShi x Popularity x Policy)")
    print(f"  Month GZ: {triple['month_ganzhi']} | Rotation: {'+'.join(triple['rotation_elements'])}")
    print(SEPARATOR)

    if not triple["hits"]:
        print("  No stock meets all three resonance criteria today")
        return

    print(f"  Resonance Count: {triple['count']}")
    print(f"  {'Stock':<22s} | {'TianShi':<20s} | {'Pop':>4s} | {'Policy':<12s} | Rating")
    print(f"  {'-'*22}+{'-'*21}+{'-'*5}+{'-'*13}+------")
    for h in triple["hits"]:
        print(f"  {h['name'] + '(' + h['code'] + ')':<22s} | {h['star'] + ' ' + h['stage']:<20s} | {h['popularity_count']:>4d} | {h['rotation_match']:>12s} | {h['rating']}")


def print_diwang_detail_console(details):
    """龙头推演打印"""
    if not details:
        return
    print(f"\n{SEPARATOR}")
    print("  DiWang / LinGuan Level Detail")
    print(SEPARATOR)
    for d in details:
        print(f"\n  [{d['name']} ({d['code']})]")
        print(f"    Sector:       {d['sector']}")
        print(f"    IPO Date:     {d['ipo_date']} -> Day Pillar: {d['riyuan_ganzhi']} -> RiYuan: {d['riyuan_gan']}({d['riyuan_wuxing']})")
        print(f"    Trade Day GZ: {d['trade_ganzhi']}")
        print(f"    Capacity:     {d['chang_sheng']} ({d['star_display']})")
        print(f"    Direction:    {d['direction']}")
        print(f"    Popularity:   {d['popularity_detail']}")
        print(f"    Entry Signal: {d['entry_condition']}")
        print(f"    Stop Loss:    {d['stop_loss']}")
        print(f"    Strategy:     {d['strategy']}")


def generate_report_file(top10, scan, output_dir):
    """生成 Markdown 报告并保存"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = os.path.join(output_dir, f"daily_stock_{top10['trade_date']}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# A股八字每日扫盘报告\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Scan Date**: {top10['trade_date']}\n\n")
        f.write(f"**Total Stocks**: {top10['total_scanned']}\n\n")
        f.write(f"**Monthly Rotation**: {' + '.join(top10['rotation_elements'])}\n\n")

        f.write(format_stock_top10_table(top10))
        f.write("\n\n")

        f.write("## Full Ranking\n\n")
        f.write("| Rank | Stock | Code | RiYuan | Capacity | Score | Phase | Sector |\n")
        f.write("|------|-------|------|--------|----------|-------|-------|--------|\n")
        for i, r in enumerate(scan["results"]):
            f.write(
                f"| {i+1} | {r['name']} | {r['code']} | {r['riyuan_gan']}({r['riyuan_wuxing']}) | {r['star']} {r['stage']} | {r['composite']:.3f} | {r['phase_label']} | {r['sector']} |\n"
            )

        f.write("\n---\n\n")
        f.write(RISK_WARNING.replace("\n", "\n\n"))
        f.write("\n")

    return filename


def main():
    parser = argparse.ArgumentParser(
        description="A股八字每日自动扫盘脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python daily_stock_scanner.py                        # Scan today
  python daily_stock_scanner.py --date 2026-05-06      # Specific date
  python daily_stock_scanner.py --output ./reports     # Save report
  python daily_stock_scanner.py --top 15               # TOP15
  python daily_stock_scanner.py --code 002594          # Single stock analysis
        """,
    )
    parser.add_argument("--date", type=str, default=None, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--output", "-o", type=str, default="./reports", help="Output dir")
    parser.add_argument("--top", type=int, default=10, help="Show TOP N stocks")
    parser.add_argument("--code", "-c", type=str, default=None, help="Single stock analysis")
    parser.add_argument("--no-save", action="store_true", help="No file save, console only")
    parser.add_argument("--list", action="store_true", help="List all supported stocks")

    args = parser.parse_args()

    if args.list:
        print("\nSupported Stocks:\n")
        for code, ipo in sorted(IPO_DATE_MAP.items()):
            name = _resolve_stock_name(code)
            sector = _resolve_stock_sector(code)
            print(f"  {code}  {name:<12s}  {sector:<20s}  IPO: {ipo}")
        print(f"\nTotal: {len(IPO_DATE_MAP)} stocks\n")
        return

    print(HEADER)

    trade_date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.code:
        codes = [c.strip() for c in args.code.split(",")]
        for code in codes:
            if code not in IPO_DATE_MAP:
                print(f"  Not found: {code}")
                continue
            print(f"\n{'='*60}")
            print(f"  Single Analysis: {_resolve_stock_name(code)} ({code})")
            print(f"{'='*60}")
            try:
                report = generate_bazi_report(code, trade_date_str)
                print(f"  RiYuan: {report['riyuan_gan']}({report['riyuan_wuxing']})")
                print(f"  Capacity: {report['star_display']} {report['chang_sheng_stage']}")
                print(f"  Expected: {report['expected_range']}")
                print(f"  Timing: {report['action']}")
                print(f"  Conclusion: {report['conclusion']}")
            except Exception as e:
                print(f"  Error: {e}")
        return

    print(f"\n  [1/3] Scanning all stocks ({trade_date_str}) ...")

    try:
        scan = scan_all_stocks_daily(trade_date_str)
        print(f"  [2/3] Scan complete, {scan['total_scanned']} stocks")
    except Exception as e:
        print(f"\n  Scan failed: {e}")
        sys.exit(1)

    print(f"  [3/3] Scoring and ranking ...")

    top10 = generate_stock_top10(trade_date_str)
    if args.top != 10:
        top10["top10"] = scan["results"][:args.top]

    print(f"\n  {top10['summary']}")

    print_top10_console(top10)
    print_wuxing_distribution(scan)

    triple = scan_stock_triple_resonance(trade_date_str)
    print_triple_resonance_console(triple)

    details = generate_stock_diwang_detail(trade_date_str)
    print_diwang_detail_console(details)

    if not args.no_save:
        try:
            filename = generate_report_file(top10, scan, args.output)
            print(f"\n  [OK] Report saved: {filename}")
        except Exception as e:
            print(f"\n  [WARN] Save failed: {e}")

    print(f"\n{SEPARATOR}")
    print("  Scan Complete!")
    print(f"{SEPARATOR}\n")

    print("  Disclaimer: Based on BaZi Twelve Growth Stages theory,")
    print("  for traditional culture perspective sandbox exercise only.")
    print("  NOT investment advice. Trade at your own risk.")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    main()
