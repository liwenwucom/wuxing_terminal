"""端到端测试：日推引擎"""
from auto_trader import generate_daily_report, pick_10_stocks_daily
from futures_picker import pick_futures_daily_report
from news_fetcher import fetch_and_parse

news = fetch_and_parse(max_items=20)
print(f"抓取新闻: {len(news)} 条")
for n in news[:3]:
    regions = set(n.get('region', '').split(',')) if isinstance(n.get('region'), str) else {n.get('region', '')}
    print(f"  [{n.get('source','')}] {n.get('title','')[:40]} | 五行:{n.get('wuxing','')} | 区域:{regions}")

print()

stock_report = pick_10_stocks_daily(news)
print(f"=== 股票推荐 ({stock_report['total_picks']}只) ===")
print(f"主导五行: {stock_report['dominant_wuxing']}")
print(f"气场: {stock_report['boost_level']}")
for s in stock_report['stocks'][:3]:
    print(f"  {s.get('action_icon','')} {s.get('action','')} | {s.get('name','')} {s.get('code','')} | {s.get('matched_industry','')}")

print()

futures_report = pick_futures_daily_report(news)
print(f"=== 期货推荐 ({futures_report['total_count']}只) ===")
for f in futures_report['futures'][:3]:
    p = f.get('price_analysis', {})
    print(f"  {f.get('direction','')} | {f.get('name','')} ({f.get('exchange','')})")
    print(f"    入场: {f.get('entry_signal','')}")
    print(f"    止损: {p.get('stop_loss','')}")
    print(f"    目标: {p.get('target','')}")

print()

print("=== 完整日推报告 ===")
report = generate_daily_report()
print(f"报告ID: {report['report_id']}")
print(f"生成时间: {report['generated_at']}")
print(f"股票: {report['stock_count']}只 | 期货: {report['futures_count']}只")
print(f"沙雕: {report.get('sandiao','')[:40]}")
print(f"\n{report['risk_warning'][:50]}...")
print("\nAll tests PASSED!")
