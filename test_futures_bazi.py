# -*- coding: utf-8 -*-
"""期货八字推演全面测试"""
from futures_bazi_picker import (
    generate_futures_bazi_report,
    format_futures_bazi_report,
    generate_futures_forward_report,
    format_futures_forward_report,
    get_monthly_futures_direction,
)

# 测试 1: 黄金 AU 单日报告
print("=== 测试1: 黄金AU 2026-05-06 单日推演 ===")
r1 = generate_futures_bazi_report("AU", "2026-05-06")
print(f"  品种: {r1['name']}")
print(f"  日元: {r1['riyuan_gan']}({r1['riyuan_wuxing']}) 日柱: {r1['riyuan_ganzhi']}")
print(f"  承载力: {r1['star_display']} {r1['chang_sheng_stage']}")
print(f"  预期: {r1['expected_range']}")
print(f"  择时: {r1['action']}")
print(f"  结论: {r1['conclusion'][:80]}...")
bs = r1['option_bs']
if bs:
    print(f"  期权买方: {bs['buyer_strategy']}")
    print(f"  期权卖方: {bs['seller_strategy']}")

# 测试 2: 原油 SC
print("\n=== 测试2: 原油SC 2026-05-06 单日推演 ===")
r2 = generate_futures_bazi_report("SC", "2026-05-06")
print(f"  品种: {r2['name']}")
print(f"  日元: {r2['riyuan_gan']}({r2['riyuan_wuxing']})")
print(f"  承载力: {r2['star_display']} {r2['chang_sheng_stage']}")
print(f"  择时: {r2['action']}")

# 测试 3: 螺纹钢 RB
print("\n=== 测试3: 螺纹钢RB 2026-05-06 单日推演 ===")
r3 = generate_futures_bazi_report("RB", "2026-05-06")
print(f"  品种: {r3['name']}")
print(f"  日元: {r3['riyuan_gan']}({r3['riyuan_wuxing']})")
print(f"  承载力: {r3['star_display']} {r3['chang_sheng_stage']}")
print(f"  择时: {r3['action']}")

# 测试 4: 后续3日推演（黄金AU）
print("\n=== 测试4: 黄金AU 后续3日推演 ===")
fwd = generate_futures_forward_report("AU", "2026-05-06", 3)
print(f"  品种: {fwd['name']}")
print(f"  日元: {fwd['riyuan_gan']}")
for row in fwd["daily_rows"]:
    print(f"    {row['day_label']:12s} {row['date']}  {row['stage']:4s}  {row['star']}  {row['expected'][:25]}")
print(f"  综合: {fwd['rhythm']['overview']}")

# 测试 5: 后续3日推演（原油SC）
print("\n=== 测试5: 原油SC 后续3日推演 ===")
fwd2 = generate_futures_forward_report("SC", "2026-05-06", 3)
for row in fwd2["daily_rows"]:
    print(f"    {row['day_label']:12s} {row['date']}  {row['stage']:4s}  {row['star']}")
print(f"  综合: {fwd2['rhythm']['overview']}")

# 测试 6: 月度轮动
print("\n=== 测试6: 月度期货方向 ===")
md = get_monthly_futures_direction("2026-05-06")
for elem, info in md["directions"].items():
    print(f"  {elem}: {info['direction']} | {', '.join(info['picks'][:4])}")

# 测试 7: Markdown 格式化
print("\n=== 测试7: Markdown 格式化验证 ===")
res = format_futures_bazi_report(r1)
checks = [
    ("八字期货推演" in res, "标题"),
    ("基础信息" in res, "基础信息"),
    ("承载力" in res, "承载力段"),
    ("量价验证" in res, "量价验证段"),
    ("期权策略" in res, "期权策略段"),
    ("综合结论" in res, "结论段"),
    ("免责声明" in res, "免责声明"),
]
for ok, label in checks:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")

fwd_md = format_futures_forward_report(fwd)
fwd_checks = [
    ("承载力变化表" in fwd_md, "承载力表"),
    ("离场/加仓节奏" in fwd_md, "节奏段"),
    ("综合节奏建议" in fwd_md, "综合建议"),
]
for ok, label in fwd_checks:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")

print("\n" + "=" * 50)
print("ALL FUTURES BAZI TESTS PASSED!")
print("=" * 50)
