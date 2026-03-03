#!/bin/bash
# Course AI Helper - 一键停止开发环境脚本
# 使用方法：./stop-dev.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🛑 停止 Course AI Helper 开发环境"
echo "============================================================"
echo ""

# 停止前端
print_info "停止 Vite 前端..."
if [ -f "frontend/frontend.pid" ]; then
    kill $(cat frontend/frontend.pid) 2>/dev/null || true
    rm -f frontend/frontend.pid
    print_success "Vite 前端已停止"
else
    print_info "未检测到运行中的前端"
fi

# 停止后端
print_info "停止 FastAPI 后端..."
if [ -f "backend/backend.pid" ]; then
    kill $(cat backend/backend.pid) 2>/dev/null || true
    rm -f backend/backend.pid
    print_success "FastAPI 后端已停止"
else
    print_info "未检测到运行中的后端"
fi

# 停止 Celery Worker
print_info "停止 Celery Worker..."
if [ -f "backend/celery_worker.pid" ]; then
    kill $(cat backend/celery_worker.pid) 2>/dev/null || true
    rm -f backend/celery_worker.pid
    print_success "Celery Worker 已停止"
else
    print_info "未检测到运行中的 Worker"
fi

# 可选：停止 Redis（默认不停）
if [ "$1" == "--all" ]; then
    print_info "停止 Redis..."
    if command -v brew &> /dev/null; then
        brew services stop redis
    elif command -v systemctl &> /dev/null; then
        sudo systemctl stop redis-server
    fi
    print_success "Redis 已停止"
fi

echo ""
print_success "所有服务已停止"
echo ""
echo "============================================================"
