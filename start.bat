@echo off
chcp 65001 >nul
cd /d "C:\Users\24083\新建文件夹\wuxing_terminal"

echo ============================================
echo   五行韭菜盘 - 一键启动
echo ============================================
echo.

if not exist ".venv2\Scripts\python.exe" (
    echo [1/3] 创建干净虚拟环境...
    python -m venv .venv2
)

echo [2/3] 安装依赖...
call .venv2\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo.

echo [3/3] 启动 Streamlit...
echo.
streamlit run main.py

pause
