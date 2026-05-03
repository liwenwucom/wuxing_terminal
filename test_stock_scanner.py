# quick test for stock scanner
from stock_bazi_scanner import (
    scan_all_stocks_daily, generate_stock_top10,
    scan_stock_triple_resonance, generate_stock_diwang_detail,
    format_stock_top10_table,
)

date = "2026-05-06"
s = scan_all_stocks_daily(date)
print(f"扫描: {s['total_scanned']}只")

t = generate_stock_top10(date)
print(f"TOP10: 多头{t['bullish_count']} 空头{t['bearish_count']}")
for i, r in enumerate(t["top10"]):
    print(f"  #{i+1} {r['code']} {r['name']} {r['star']} {r['stage']} {r['composite']:.2f}")

tr = scan_stock_triple_resonance(date)
print(f"三重共振: {tr['count']}只")
for h in tr["hits"]:
    print(f"  {h['name']} {h['star']} {h['popularity_count']}次 {h['rating']}")

d = generate_stock_diwang_detail(date)
print(f"龙头推演: {len(d)}只")
for x in d:
    print(f"  {x['name']} {x['star_display']} {x['direction']}")

md = format_stock_top10_table(t)
print("\n--- Markdown Check ---")
checks = ["TOP10", "三重共振", "帝旺/临官", "免责声明"]
for c in checks:
    status = "OK" if c in md else "MISSING"
    print(f"  [{status}] {c}")
print("Done!")
