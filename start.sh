#!/bin/bash

echo "======================================="
echo "  Bamboo AI 工作流系统"
echo "======================================="
echo ""

# 检查并启动后端
if [ -d "backend" ]; then
    echo "Starting backend server..."

    # 进入后端目录
    cd backend

    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "[ERROR] Virtual environment not found, creating..."
        python -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 检查.env文件
    if [ ! -f ".env" ]; then
        echo "[ERROR] .env file not found, please configure:"
        echo "   1. Copy environment variable example file"
        echo "   2. Edit backend/.env, add your DEEPSEEK_API_KEY"
        deactivate
        exit 1
    fi

    # 安装依赖并启动
    pip install -r requirements.txt -q
    python app.py
else
    echo "[ERROR] backend directory not found"
    exit 1
fi
