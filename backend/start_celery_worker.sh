#!/bin/bash
# Celery Worker 启动脚本

echo "🚀 启动 Celery Worker..."
echo ""

# 检查 Redis 是否运行
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis 未安装，请先安装 Redis:"
    echo "   brew install redis    # macOS"
    echo "   sudo apt install redis-server  # Ubuntu/Debian"
    exit 1
fi

# 测试 Redis 连接
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis 未运行，请启动 Redis:"
    echo "   brew services start redis    # macOS"
    echo "   sudo systemctl start redis-server  # Ubuntu/Debian"
    exit 1
fi

echo "✅ Redis 已连接"
echo ""

# 激活虚拟环境
source .venv/bin/activate

# 启动 Celery Worker
echo "📦 启动 Worker 进程..."
echo "   队列：video_processing, asr, llm"
echo "   并发数：4"
echo ""

# 启动 Worker（监听所有队列）
celery -A app.core.celery_app worker \
    --loglevel=info \
    --queues=video_processing,asr,llm \
    --concurrency=4 \
    --pool=gevent \
    --hostname=worker1@%h

# 备选方案（如果 gevent 不可用）
# celery -A app.core.celery_app worker -l info -Q video_processing,asr,llm -c 4
