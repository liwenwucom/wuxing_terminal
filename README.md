# 五行韭菜盘 —— 人量化玄学交易助手

基于 Streamlit 构建的 **纯A股每日自动推荐工具**，融合五行生克、节气气场、干支纪日等传统玄学体系，对 A 股及中国期货进行 **买入 / 卖出 / 回避** 三栏分类推荐，并提供期权策略建议。

> 玄学有风险，梭哈需谨慎。本工具仅供娱乐，不构成任何投资建议。

---

## 功能特点

- 每日自动生成 **30 只 A 股** 推荐：买入 10 / 卖出 10 / 回避 10
- 中国期货三栏分类：买入 / 卖出 / 回避各 5 只
- 期权策略建议（买 Call / 买 Put / 价差组合）
- 节气气场 + 天干地支实时计算
- 5 分钟新闻缓存自动刷新
- 历史日推报告存档回溯
- 纯规则引擎驱动，零 LLM 依赖也可运行

---

## 环境要求

- Python 3.8 及以上

---

## 快速启动

### 方式一：命令行

```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名

# 创建虚拟环境
python -m venv .venv2

# 激活（Windows）
.venv2\Scripts\activate
# 激活（macOS / Linux）
source .venv2/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 启动
streamlit run main.py
```

浏览器打开 `http://localhost:8501`，选择 **「自动日推(A股)」** 标签，点击 **「生成今日日推报告」**。

### 方式二：一键启动（Windows）

双击项目目录下的 **`start.bat`**，自动完成环境激活和启动。

---

## 项目结构

```
├── main.py              # Streamlit 主程序
├── auto_trader.py       # 日推引擎（30只A股 + 期货分类）
├── stock_picker.py      # 股票评分与筛选
├── futures_picker.py    # 期货品种池与方向判断
├── news_fetcher.py      # 新闻抓取与解析
├── five_elements.py     # 节气 / 干支 / 五行生克
├── backtest.py          # 历史胜率统计
├── reporter.py          # 报告整合 + 沙雕语录
├── options_picker.py    # 期权策略引擎
├── config.py            # 全局配置与股票池
├── requirements.txt     # 依赖清单
├── start.bat            # Windows 一键启动
├── .gitignore           # Git 忽略规则
└── README.md            # 本文件
```

---

## 注意事项

- 所有依赖均为 PyPI 官方正版包，无第三方仿冒/拼写错误包
- API Key 通过环境变量或侧边栏动态输入，代码中不含任何硬编码密钥
- 代码中无绝对路径，全部使用相对路径，跨机器可运行
- 如需实时行情数据，可额外安装 `akshare`（需 Python 3.10+）

---

## 开源协议

MIT License
