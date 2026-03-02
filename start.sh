#!/bin/bash

# Course AI Helper - 快速启动脚本

set -e

echo "🚀 Course AI Helper - 启动脚本"
echo "================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python 版本：$python_version"

# 创建虚拟环境（如果不存在）
if [ ! -d "backend/.venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv backend/.venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source backend/.venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
cd backend
pip install -q -r requirements.txt
cd ..

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/{videos,subtitles,summaries,embeddings,chroma}

# 复制环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置 API Key 等参数"
fi

# 启动后端服务
echo ""
echo "🚀 启动后端服务..."
echo "📍 API 文档：http://localhost:8000/docs"
echo "📍 健康检查：http://localhost:8000/health"
echo ""

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
