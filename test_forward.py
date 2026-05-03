# -*- coding: utf-8 -*-
"""后续3日承载力推演测试"""
from bazi_picker import (
    get_next_n_trading_days,
    generate_forward_report,
    format_forward_report,
)

# 测试 1: 交易日推算
print("=== 测试1: 后续交易日推算 (从2026-05-06起) ===")
days = get_next_n_trading_days("2026-05-06", 3)
for i, d in enumerate(days):
    print(f"  T+{i+1}: {d}")

# 测试 2: 中际旭创 300308 的前瞻报告
print("\n=== 测试2: 中际旭创(300308) 后续3日推演 ===")
fwd = generate_forward_report("300308", "2026-05-06")
print(f"品种: {fwd['stock_name']}({fwd['stock_code']})")
print(f"日元: {fwd['riyuan_gan']}({fwd['riyuan_wuxing']})")
print(f"IPO: {fwd['ipo_date']}")

print("\n承载力变化表:")
for row in fwd["daily_rows"]:
    print(f"  {row['day_label']:12s} {row['date']}  {row['day_ganzhi']:4s}  {row['stage']:4s}  {row['star']} {row['label']}")
    print(f"  {'':12s} 量价信号: {row['threshold']}")

print("\n节奏规划:")
for a in fwd["rhythm"]["daily_actions"]:
    print(f"  {a['day_label']:12s} -> {a['action']:10s} | {a['detail'][:60]}...")
print(f"\n综合: {fwd['rhythm']['overview']}")

# 测试 3: 比亚迪
print("\n\n=== 测试3: 比亚迪(002594) 后续3日推演 ===")
fwd2 = generate_forward_report("002594", "2026-05-06")
print(f"品种: {fwd2['stock_name']}({fwd2['stock_code']})")
print(f"日元: {fwd2['riyuan_gan']}({fwd2['riyuan_wuxing']})")
for row in fwd2["daily_rows"]:
    print(f"  {row['day_label']:12s} {row['date']}  {row['stage']:4s}  {row['star']}")
for a in fwd2["rhythm"]["daily_actions"]:
    print(f"  {a['day_label']:12s} → {a['action']:10s}")

# 测试 4: 格式化输出
print("\n\n=== 测试4: Markdown 格式化验证 ===")
md = format_forward_report(fwd)
checks = [
    ("后续3日承载力推演" in md, "标题"),
    ("基础信息" in md, "基础信息段"),
    ("承载力变化表" in md, "承载力表"),
    ("节奏规划" in md, "节奏规划段"),
    (fwd["stock_name"] in md, "股票名称"),
    (fwd["riyuan_gan"] in md, "日元"),
    ("免责声明" in md, "免责声明"),
]
for ok, label in checks:
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
if all(c[0] for c in checks):
    print("  => Markdown 格式化验证通过")
else:
    print("  => Markdown 格式化验证失败")

print("\n" + "=" * 50)
print("ALL FORWARD TESTS PASSED!")
print("=" * 50)
