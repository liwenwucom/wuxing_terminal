@echo off
chcp 65001 >nul
cd /d "C:\Users\24083\新建文件夹\wuxing_terminal"

echo ============================================
echo   五行韭菜盘 - 后台监控守护进程
echo ============================================
echo.
echo   分析模式: hybrid (五行扫盘 + AI联网分析)
echo.
echo   [联网模式需要 API Key，在下方设置]
echo   [纯五行离线: 修改 monitor.py 中 analysis_mode 为 wuxing]
echo ============================================
echo.

REM ============================================
REM  在这里填入你的 API Key（可选，不填则自动降级为纯五行模式）
REM  永久设置方法: 命令行运行 setx NEWSAPI_KEY "你的key"
REM ============================================
REM set NEWSAPI_KEY=你的NewsAPI_Key
REM set ZHIPU_API_KEY=你的智谱AI_Key

if not exist ".venv2\Scripts\python.exe" (
    echo [1/3] 创建干净虚拟环境...
    python -m venv .venv2
)

echo [2/3] 安装依赖...
call .venv2\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo.

echo [3/3] 启动后台监控...
echo   最小化本窗口即可，不要关闭
echo   按 Ctrl+C 停止
echo.
python monitor.py

pause
