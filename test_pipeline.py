from news_fetcher import parse_news
from five_elements import analyze_wuxing_boost
from stock_picker import pick_stocks
from futures_picker import pick_futures
from backtest import calculate_win_rate
from reporter import build_report

test_news = [
    '央行宣布降准0.5个百分点，释放长期资金约1万亿元。基建、房地产板块受益。',
    '美国对华半导体出口管制加码，涉及AI芯片。国产替代概念受关注。',
    '红海局势紧张，全球航运价格暴涨，中远海控盈利预期大幅上调。',
]

print("| 五行 | 气场 | 操作建议 | 评分 | 沙雕点评 |")
print("|------|------|----------|------|----------|")

for text in test_news:
    parsed = parse_news({'title': '', 'content': text})
    boost = analyze_wuxing_boost(parsed['wuxing'])
    stocks = pick_stocks(parsed['industries'], parsed['wuxing'], 'A股')
    futures = pick_futures(parsed['wuxing'], boost['boost_level'])
    winrate = calculate_win_rate(parsed['wuxing'], parsed['event_type'])
    report = build_report(parsed, boost, stocks, futures, None, winrate)

    wuxing = report['wuxing']
    boost_lv = report['boost_level']
    action = report['action']
    score = report['total_score']
    sandiao = report['sandiao_stock'][:25]

    print(f"| {wuxing:4s} | {boost_lv:4s} | {action:12s} | {score:.3f} | {sandiao}... |")

print()
print("All 3 pipelines passed!")
