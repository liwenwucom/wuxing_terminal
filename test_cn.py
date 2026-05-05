import sys
sys.path.insert(0, r"c:\Users\24083\新建文件夹\wuxing_terminal")
from chen_nanpeng_scanner import analyze_year_pillar, check_name_wuxing, check_code_number
import json

print("--- 2026 ---")
r = analyze_year_pillar("丙午")
d = {k: v for k, v in r.items() if k != "analysis"}
print(json.dumps(d, ensure_ascii=False, indent=2))
print("解读:", r["analysis"])

print()
print("--- 2022 ---")
r2 = analyze_year_pillar("壬寅")
d2 = {k: v for k, v in r2.items() if k != "analysis"}
print(json.dumps(d2, ensure_ascii=False, indent=2))
print("解读:", r2["analysis"])

print()
print("--- name radicals ---")
print("贵州茅台:", check_name_wuxing("贵州茅台"))
print("中国平安:", check_name_wuxing("中国平安"))
print("比亚迪:", check_name_wuxing("比亚迪"))
print("农业银行:", check_name_wuxing("农业银行"))

print()
print("--- code number ---")
print("600519 壬寅:", check_code_number("600519", "壬", "寅"))
print("000333 丙午:", check_code_number("000333", "丙", "午"))
print("600036 壬寅:", check_code_number("600036", "壬", "寅"))
