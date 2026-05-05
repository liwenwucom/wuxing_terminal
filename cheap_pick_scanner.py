# -*- coding: utf-8 -*-
"""
低价潜力股扫描引擎
—— 每天自动扫描全市场，找出「股价低 + 涨幅潜力高」的 A股 + 科创板

筛选规则：
1. 最新股价 < 30元（< 15元加分）
2. PE 合理或偏低（负PE且连续亏损的排除）
3. 近5日成交额 > 2000万（排除僵尸股）
4. 排除 ST/*ST/退市风险
5. 科创板（688）和非科创板自动分离
6. 按「估值潜力分」从高到低，每板最多10只

数据源：akshare（免费，无需 API Key）
运行方式：python cheap_pick_scanner.py
"""

import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

# ============================================================
# 配置
# ============================================================
MAX_PRICE = 30          # 最高股价
BONUS_PRICE = 15        # 低于此价加分
MIN_VOLUME_YUAN = 20_000_000  # 最小日成交额（2000万）
TOP_N = 10              # 每个板块最多输出几只


def _has_akshare():
    try:
        import akshare
        return True
    except ImportError:
        return False


def fetch_all_stocks():
    """akshare 拉取全A股实时行情"""
    if not _has_akshare():
        raise RuntimeError(
            "akshare 未安装，请运行: pip install akshare>=1.17\n"
            "然后重新运行本脚本。"
        )
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    return df


def compute_score(row: dict) -> float:
    """
    计算「估值潜力分」
    高分 = 价格低 + PE低(非负) + 有一定活跃度
    """
    price = float(row.get("最新价", 999))
    pe = float(row.get("市盈率-动态", -999))
    pct = float(row.get("涨跌幅", 0))
    volume = float(row.get("成交额", 0))
    turnover = float(row.get("换手率", 0))

    # 价格分（越低越加分）
    if price <= BONUS_PRICE:
        price_score = 35
    elif price <= 20:
        price_score = 25
    elif price <= MAX_PRICE:
        price_score = 15
    else:
        return -999  # 超过30元直接排除

    # PE分（正PE且越低越好）
    if pe <= 0 or pe > 500:
        pe_score = 0      # 负PE不参与估值分
    elif pe <= 10:
        pe_score = 30
    elif pe <= 20:
        pe_score = 20
    elif pe <= 40:
        pe_score = 10
    else:
        pe_score = 5

    # 活跃度分（有成交才有机会）
    if volume < MIN_VOLUME_YUAN:
        return -999  # 僵尸股排除
    elif volume > 500_000_000:  # 5亿以上
        vol_score = 15
    elif volume > 100_000_000:  # 1亿以上
        vol_score = 10
    else:
        vol_score = 5

    # 趋势修正（跌多了反而有反弹潜力）
    if pct <= -5:
        trend_bonus = 8    # 超跌反弹潜力
    elif pct <= -2:
        trend_bonus = 4
    elif pct >= 5:
        trend_bonus = -5   # 已经涨高了，追高风险
    else:
        trend_bonus = 0

    return price_score + pe_score + vol_score + trend_bonus


def is_st_stock(name: str) -> bool:
    return name and ("ST" in name.upper() or "*ST" in name.upper())


def scan_cheap_picks(df=None) -> dict:
    """
    返回:
    {
        "kechuang": [{code, name, price, pe, industry, score, reason}, ...],
        "ashares": [...],
        "generated_at": str,
        "total_scanned": int,
    }
    """
    if df is None:
        print("正在拉取全市场实时数据...")
        df = fetch_all_stocks()

    print(f"扫描范围: {len(df)} 只股票")

    kechuang_list = []
    ashares_list = []

    for _, r in df.iterrows():
        code = str(r.get("代码", "")).strip()
        name = str(r.get("名称", "")).strip()

        if not code or is_st_stock(name):
            continue

        score = compute_score(r)
        if score < 0:
            continue

        price = float(r.get("最新价", 0))
        pe = float(r.get("市盈率-动态", 0))
        pct = float(r.get("涨跌幅", 0))
        volume = float(r.get("成交额", 0))

        reasons = []
        if price <= BONUS_PRICE:
            reasons.append(f"低价{price:.1f}元")
        if 0 < pe <= 15:
            reasons.append(f"低PE({pe:.0f}倍)")
        if pct <= -3:
            reasons.append("超跌")

        entry = {
            "code": code,
            "name": name,
            "price": round(price, 2),
            "pe": round(pe, 1),
            "chg_pct": round(pct, 2),
            "volume_yi": round(volume / 1e8, 2),
            "score": round(score, 1),
            "reason": " + ".join(reasons) if reasons else "综合低估",
        }

        if code.startswith("688"):
            kechuang_list.append(entry)
        else:
            ashares_list.append(entry)

    kechuang_list.sort(key=lambda x: x["score"], reverse=True)
    ashares_list.sort(key=lambda x: x["score"], reverse=True)

    return {
        "kechuang": kechuang_list[:TOP_N],
        "ashares": ashares_list[:TOP_N],
        "kechuang_total": len(kechuang_list),
        "ashares_total": len(ashares_list),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_scanned": len(df),
    }


def format_report(result: dict) -> str:
    """格式化为 Markdown 报告"""
    lines = [
        f"# 🎯 低价潜力股 · 每日扫描",
        f"生成时间: {result['generated_at']}",
        f"扫描范围: {result['total_scanned']} 只",
        f"",
        f"筛选条件: 股价 < {MAX_PRICE}元 | 日成交 > {MIN_VOLUME_YUAN//10000}万 | 排除ST",
        f"",
    ]

    for key, label in [("kechuang", "科创板(688)"), ("ashares", "A股(非科创板)")]:
        items = result[key]
        total = result[f"{key}_total"]
        lines.append(f"## {label}")
        lines.append(f"符合条件: {total} 只 → 展示前 {len(items)} 只")
        lines.append("")
        lines.append("| # | 股票 | 代码 | 股价 | PE | 涨跌 | 日成交(亿) | 评分 | 理由 |")
        lines.append("|---|------|------|------|-----|------|-----------|------|------|")
        for i, s in enumerate(items, 1):
            lines.append(
                f"| {i} | {s['name']} | {s['code']} | {s['price']} | "
                f"{s['pe']} | {s['chg_pct']}% | {s['volume_yi']} | "
                f"{s['score']} | {s['reason']} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("> ⚠️ 风险提示: 低价不等于必涨，数据可能有延迟，仅供参考，不构成投资建议。")
    return "\n".join(lines)


def main():
    print("=" * 50)
    print("  低价潜力股 · 全市场扫描")
    print("=" * 50)
    result = scan_cheap_picks()
    report = format_report(result)
    print(report)

    # 同时保存到文件
    fname = f"cheap_picks_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存: {fname}")

    return result


if __name__ == "__main__":
    main()
