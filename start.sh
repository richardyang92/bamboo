#!/bin/bash

echo "🚀 启动 AI 智能绘图工作流 Web 服务器..."
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行："
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在，请先配置："
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件，添加你的 ZHIPUAI_API_KEY"
    exit 1
fi

# 激活虚拟环境并启动服务器
source venv/bin/activate
python app.py
