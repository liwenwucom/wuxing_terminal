"""端到端测试：纯中国版 买入10/卖出10/回避10"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from auto_trader import generate_daily_report
from news_fetcher import fetch_and_parse

report = generate_daily_report()
print(f"报告ID: {report['report_id']}")
print(f"生成时间: {report['generated_at']}")
print(f"市场: {report['market']}")
print(f"五行: {report['dominant_wuxing']} | 气场: {report['boost_level']}")
print(f"情绪: {report['market_sentiment']}")
print()

buy = report['buy_stocks']
sell = report['sell_stocks']
avoid = report['avoid_stocks']
print(f"=== 买入 ({len(buy)}只) ===")
for s in buy[:5]:
    print(f"  {s['name']} {s['code']} | {s['matched_industry']} | PE:{s['pe']} | 五行:{s['wuxing']} | {s['direction_reason'][:30]}")

print(f"\n=== 卖出 ({len(sell)}只) ===")
for s in sell[:5]:
    print(f"  {s['name']} {s['code']} | {s['matched_industry']} | PE:{s['pe']} | 五行:{s['wuxing']} | {s['direction_reason'][:30]}")

print(f"\n=== 回避 ({len(avoid)}只) ===")
for s in avoid[:5]:
    print(f"  {s['name']} {s['code']} | {s['matched_industry']} | PE:{s['pe']} | 五行:{s['wuxing']} | {s['direction_reason'][:30]}")

print(f"\n=== 期货 ===")
bf = report['buy_futures']
sf = report['sell_futures']
af = report['avoid_futures']
print(f"买入期货: {len(bf)}只")
for f in bf[:2]:
    pa = f.get('price_analysis', {})
    print(f"  {f['name']} | 入场:{f['entry_signal'][:20]} | 止损:{pa.get('stop_loss','')[:20]}")
print(f"卖出期货: {len(sf)}只")
for f in sf[:2]:
    pa = f.get('price_analysis', {})
    print(f"  {f['name']} | 入场:{f['entry_signal'][:20]} | 止损:{pa.get('stop_loss','')[:20]}")
print(f"回避期货: {len(af)}只")

print(f"\n=== 期权 ===")
opts = report.get('options_summary', {})
print(f"策略: {opts.get('strategy','')}")
for t in opts.get('suggested_targets', []):
    print(f"  {t}")

sandiao = report['sandiao']
print(f"\n沙雕: {sandiao[:50]}")

all_codes = [s['code'] for s in buy + sell + avoid]
assert len(all_codes) == len(set(all_codes)), "ERROR: 发现重复股票!"
assert len(buy) == 10, f"买入应为10只，实际{len(buy)}"
assert len(sell) == 10, f"卖出应为10只，实际{len(sell)}"
assert len(avoid) == 10, f"回避应为10只，实际{len(avoid)}"

print(f"\nAll tests PASSED!")
print(f"Total: 股票{report['stock_count']}只(买{len(buy)}/卖{len(sell)}/回避{len(avoid)}) + 期货{report['futures_count']}只 + 期权策略")
