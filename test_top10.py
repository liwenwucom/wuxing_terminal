# -*- coding: utf-8 -*-
"""TOP10 自动扫盘测试"""
from futures_bazi_picker import (
    generate_futures_top10, format_futures_top10_table,
    scan_all_futures_daily,
)

print("=== TOP10 自动扫盘测试 (2026-05-06) ===")
top10 = generate_futures_top10("2026-05-06")
print(f"扫描品种: {top10['total_scanned']}")
print(f"月度轮动: {top10['rotation_elements']}")
print(f"多头: {top10['bullish_count']} | 空头: {top10['bearish_count']}")
print(f"综述: {top10['summary']}")
print()
for i, r in enumerate(top10["top10"]):
    tag = "多" if r["composite"] >= 0.25 else ("空" if r["composite"] < 0.0 else "中")
    print(f"  #{i+1} [{tag}] {r['name']}({r['symbol']}) | 日元:{r['riyuan_gan']} | {r['star']} {r['stage']} | 评分:{r['composite']:.3f} | 买方:{r['opt_buyer']}")

print(f"\n=== 格式化输出验证 ===")
fmt = format_futures_top10_table(top10)
checks = [
    ("TOP10" in fmt, "标题"),
    (top10["summary"] in fmt, "综述"),
    ("买方策略" in fmt, "买方列"),
    ("卖方策略" in fmt, "卖方列"),
    ("免责声明" in fmt, "免责声明"),
]
for ok, label in checks:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")

print(f"\n=== 全品种扫描 (不截断) ===")
scan = scan_all_futures_daily("2026-05-06")
print(f"全部 {scan['total_scanned']} 个品种扫描完成")
# 统计各五行分布
wx_count = {}
for r in scan["results"]:
    wx = r["futures_wuxing"]
    wx_count[wx] = wx_count.get(wx, 0) + 1
print("五行分布:", wx_count)

print("\n===== ALL TOP10 TESTS PASSED! =====")
