#!/bin/bash
# Course AI Helper - 一键启动开发环境脚本
# 使用方法：./start-dev.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🎬 Course AI Helper - 一键启动开发环境"
echo "============================================================"
echo ""

# 步骤 1: 检查 Git
print_info "步骤 1/7: 检查 Git..."
if ! command -v git &> /dev/null; then
    print_error "Git 未安装，请先安装 Git"
    exit 1
fi
print_success "Git 已安装"

# 步骤 2: 拉取最新代码
print_info "步骤 2/7: 拉取最新代码..."
if [ -d ".git" ]; then
    print_info "检测到已有 Git 仓库，执行 git pull..."
    git pull origin main
    print_success "代码已更新"
else
    print_warning "当前目录不是 Git 仓库，跳过 pull"
fi

# 步骤 3: 检查并安装 Python 依赖
print_info "步骤 3/7: 检查 Python 依赖..."
if [ ! -d "backend/.venv" ]; then
    print_info "创建 Python 虚拟环境..."
    cd backend
    python3 -m venv .venv
    cd ..
    print_success "虚拟环境已创建"
fi

print_info "安装/更新 Python 依赖..."
cd backend
source .venv/bin/activate
pip install -q -r requirements.txt
cd ..
print_success "Python 依赖已安装"

# 步骤 4: 检查并安装 Node 依赖
print_info "步骤 4/7: 检查 Node 依赖..."
if [ ! -d "frontend/node_modules" ]; then
    print_info "安装 Node 依赖（首次运行可能需要几分钟）..."
    cd frontend
    npm install
    print_success "Node 依赖已安装"
    cd ..
else
    print_info "Node 依赖已存在，跳过安装"
fi

# 步骤 5: 检查并启动 Redis
print_info "步骤 5/7: 检查 Redis..."
if ! command -v redis-cli &> /dev/null; then
    print_error "Redis 未安装，请先安装 Redis:"
    echo "   macOS: brew install redis"
    echo "   Ubuntu/Debian: sudo apt install redis-server"
    exit 1
fi

if ! redis-cli ping &> /dev/null; then
    print_info "Redis 未运行，尝试启动..."
    if command -v brew &> /dev/null; then
        brew services start redis
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start redis-server
    else
        print_error "无法自动启动 Redis，请手动启动"
        exit 1
    fi
    sleep 2
fi

if redis-cli ping &> /dev/null; then
    print_success "Redis 已启动并连接成功"
else
    print_error "Redis 连接失败"
    exit 1
fi

# 步骤 6: 启动 Celery Worker
print_info "步骤 6/7: 启动 Celery Worker..."
cd backend
if [ -f "celery_worker.pid" ]; then
    OLD_PID=$(cat celery_worker.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        print_info "检测到已运行的 Worker，先停止..."
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
    rm -f celery_worker.pid
fi

print_info "启动 Celery Worker（后台运行）..."
nohup celery -A app.core.celery_app worker \
    --loglevel=warning \
    --queues=video_processing,asr,llm \
    --concurrency=4 \
    --detach \
    --pidfile=celery_worker.pid \
    > logs/celery_worker.log 2>&1 &

echo $! > celery_worker.pid
sleep 3

if [ -f "celery_worker.pid" ] && ps -p $(cat celery_worker.pid) > /dev/null 2>&1; then
    print_success "Celery Worker 已启动 (PID: $(cat celery_worker.pid))"
else
    print_warning "Celery Worker 启动失败，查看日志：logs/celery_worker.log"
fi
cd ..

# 步骤 7: 启动 FastAPI 后端
print_info "步骤 7/7: 启动 FastAPI 后端..."
cd backend
if [ -f "backend.pid" ]; then
    OLD_PID=$(cat backend.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        print_info "检测到已运行的后端，先停止..."
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
fi

print_info "启动 FastAPI 后端（后台运行）..."
nohup python3 main.py > logs/backend.log 2>&1 &
echo $! > backend.pid
sleep 3

if [ -f "backend.pid" ] && ps -p $(cat backend.pid) > /dev/null 2>&1; then
    print_success "FastAPI 后端已启动 (PID: $(cat backend.pid))"
else
    print_error "FastAPI 后端启动失败，查看日志：logs/backend.log"
    exit 1
fi
cd ..

# 启动前端
print_info "启动 Vite 前端开发服务器..."
cd frontend
if [ -f "frontend.pid" ]; then
    OLD_PID=$(cat frontend.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        print_info "检测到已运行的前端，先停止..."
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
fi

nohup npm run dev > ../logs/frontend.log 2>&1 &
echo $! > frontend.pid
sleep 3

if [ -f "frontend.pid" ] && ps -p $(cat frontend.pid) > /dev/null 2>&1; then
    print_success "Vite 前端已启动 (PID: $(cat frontend.pid))"
else
    print_error "Vite 前端启动失败，查看日志：logs/frontend.log"
    exit 1
fi
cd ..

# 完成
echo ""
echo "============================================================"
echo "✅ 启动完成！"
echo "============================================================"
echo ""
echo "📱 访问地址:"
echo "   前端：http://localhost:3000"
echo "   API 文档：http://localhost:8000/docs"
echo "   后端健康检查：http://localhost:8000/health"
echo ""
echo "📊 服务状态:"
echo "   ✅ Redis: 运行中"
if [ -f "backend/celery_worker.pid" ]; then
    echo "   ✅ Celery Worker: 运行中 (PID: $(cat backend/celery_worker.pid))"
else
    echo "   ⚠️  Celery Worker: 未运行"
fi
if [ -f "backend/backend.pid" ]; then
    echo "   ✅ FastAPI 后端：运行中 (PID: $(cat backend/backend.pid))"
else
    echo "   ⚠️  FastAPI 后端：未运行"
fi
if [ -f "frontend/frontend.pid" ]; then
    echo "   ✅ Vite 前端：运行中 (PID: $(cat frontend/frontend.pid))"
else
    echo "   ⚠️  Vite 前端：未运行"
fi
echo ""
echo "📝 日志文件:"
echo "   后端：backend/logs/backend.log"
echo "   前端：logs/frontend.log"
echo "   Celery: backend/logs/celery_worker.log"
echo ""
echo "🛑 停止服务:"
echo "   ./stop-dev.sh"
echo ""
echo "============================================================"
