# -*- coding: utf-8 -*-
"""联网八字推演快速测试"""
from bazi_live_scanner import (
    generate_live_daily_report, format_live_report,
    calculate_triple_resonance, scan_daily_diwang,
)

# 用 2026-05-06 测试（用户示例的己酉日）
r = generate_live_daily_report('2026-05-06')

print("=== 天时分析 ===")
print(f"大盘承载力: {r['market_stars']} {r['market_stage']}")
print(f"四柱八字: {r['year_ganzhi']} {r['month_ganzhi']} {r['day_ganzhi']}")
print(f"年度格局: {r['annual_grade']}")

print("\n=== 各日元承载力速判 ===")
for g in ["庚", "辛", "丙", "丁", "甲", "乙", "壬", "癸", "戊", "己"]:
    if g in r['stem_capacity']:
        s = r['stem_capacity'][g]
        print(f"  {g}({s['wuxing']}): {s['stage']} {s['stars']} 预期{s['range']}")

print("\n=== 三重共振 TOP5 ===")
for x in r['top_resonance'][:5]:
    print(f"  {x['name']}({x['code']}): 总分{x['total']} [{x['resonance_level']}] 阶段:{x['stage']} 天时:{x['tianshi']} 人气:{x['pop_count']}")

print(f"\n=== 帝旺级品种 ({r['diwang_count']}只) ===")
for rep in r.get('diwang_reports', []):
    print(f"  {rep['stock_name']}({rep['stock_code']}): {rep['chang_sheng_stage']} {rep['star_display']} 择时:{rep['timing_signal']} 预期:{rep['expected_range']}")

print(f"\n=== 联网数据来源 ({len(r['data_sources'])}项) ===")
for ds in r['data_sources']:
    print(f"  {ds['category']}: {ds['source']}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
