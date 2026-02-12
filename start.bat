@echo off
chcp 65001 >nul
echo =======================================
echo   Bamboo AI 工作流系统
echo ======================================
echo.

REM 检查 backend 目录
if not exist "backend" (
    echo [ERROR] backend directory not found
    exit /b 1
)

echo Starting backend server...
cd backend

REM 检查虚拟环境
if not exist "venv" (
    echo [ERROR] Virtual environment not found, creating...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查 .env 文件
if not exist ".env" (
    echo [ERROR] backend\.env file not found, please configure:
    echo    1. Copy environment variable example file
    echo    2. Edit backend\.env, add your DEEPSEEK_API_KEY
    deactivate
    exit /b 1
)

REM 安装依赖并启动
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting server on http://localhost:5001
echo Press Ctrl+C to stop
python app.py
