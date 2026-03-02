#!/bin/bash

# Course AI Helper - 一键启动脚本
# 自动启动后端和前端服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查 Python
check_python() {
    print_info "检查 Python 环境..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python 3.10+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 版本：$PYTHON_VERSION"
}

# 检查 Node.js
check_node() {
    print_info "检查 Node.js 环境..."
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    print_success "Node.js 版本：$NODE_VERSION"
}

# 初始化后端
init_backend() {
    print_info "初始化后端..."
    cd "$SCRIPT_DIR/backend"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d ".venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv .venv
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 安装依赖
    if [ ! -f ".venv/.deps_installed" ]; then
        print_info "安装 Python 依赖..."
        pip install -q -r requirements.txt
        touch .venv/.deps_installed
        print_success "依赖安装完成"
    else
        print_success "依赖已安装"
    fi
    
    # 创建数据目录
    mkdir -p data/{videos,subtitles,summaries,embeddings,chroma}
    
    cd "$SCRIPT_DIR"
}

# 初始化前端
init_frontend() {
    print_info "初始化前端..."
    cd "$SCRIPT_DIR/frontend"
    
    # 安装依赖（如果未安装）
    if [ ! -d "node_modules" ]; then
        print_info "安装前端依赖（这可能需要几分钟）..."
        npm install --silent
        print_success "前端依赖安装完成"
    else
        print_success "前端依赖已安装"
    fi
    
    cd "$SCRIPT_DIR"
}

# 启动后端
start_backend() {
    print_info "启动后端服务..."
    cd "$SCRIPT_DIR/backend"
    source .venv/bin/activate
    
    # 检查端口是否被占用
    if command -v lsof &> /dev/null; then
        PID=$(lsof -ti:8000 2>/dev/null)
        if [ ! -z "$PID" ]; then
            print_warning "端口 8000 被占用 (PID: $PID)，清理中..."
            kill -9 $PID 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # 启动后端（后台运行）
    nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    # 等待后端启动
    sleep 3
    
    # 检查后端是否正常启动
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "后端服务已启动 (PID: $BACKEND_PID)"
        print_success "API 文档：http://localhost:8000/docs"
    else
        print_error "后端启动失败，查看日志：logs/backend.log"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
}

# 启动前端
start_frontend() {
    print_info "启动前端服务..."
    cd "$SCRIPT_DIR/frontend"
    
    # 启动前端（后台运行）
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    # 等待前端启动
    sleep 5
    
    # 检查前端是否正常启动
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "前端服务已启动 (PID: $FRONTEND_PID)"
        print_success "前端地址：http://localhost:3000"
    else
        print_warning "前端可能还在启动中，查看日志：logs/frontend.log"
    fi
    
    cd "$SCRIPT_DIR"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    
    # 停止后端
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            print_success "后端服务已停止 (PID: $PID)"
        fi
        rm logs/backend.pid
    fi
    
    # 停止前端
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            print_success "前端服务已停止 (PID: $PID)"
        fi
        rm logs/frontend.pid
    fi
    
    # 清理残留进程
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    print_success "所有服务已停止"
}

# 显示服务状态
show_status() {
    print_info "服务状态:"
    
    # 后端状态
    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_success "后端：运行中 (PID: $PID)"
        else
            print_error "后端：已停止"
        fi
    else
        print_warning "后端：未启动"
    fi
    
    # 前端状态
    if [ -f "logs/frontend.pid" ]; then
        PID=$(cat logs/frontend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_success "前端：运行中 (PID: $PID)"
        else
            print_error "前端：已停止"
        fi
    else
        print_warning "前端：未启动"
    fi
    
    # 访问地址
    echo ""
    print_info "访问地址:"
    echo "  后端 API:   http://localhost:8000"
    echo "  API 文档：  http://localhost:8000/docs"
    echo "  前端界面：http://localhost:3000"
}

# 查看日志
view_logs() {
    if [ ! -d "logs" ]; then
        print_error "日志目录不存在"
        exit 1
    fi
    
    echo "选择要查看的日志:"
    echo "1) 后端日志"
    echo "2) 前端日志"
    echo "3) 全部日志"
    read -p "> " choice
    
    case $choice in
        1)
            tail -f logs/backend.log
            ;;
        2)
            tail -f logs/frontend.log
            ;;
        3)
            tail -f logs/*.log
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
}

# 主菜单
show_menu() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║   Course AI Helper - 启动管理器        ║"
    echo "╠════════════════════════════════════════╣"
    echo "║  1) 启动所有服务                       ║"
    echo "║  2) 仅启动后端                         ║"
    echo "║  3) 仅启动前端                         ║"
    echo "║  4) 停止所有服务                       ║"
    echo "║  5) 查看服务状态                       ║"
    echo "║  6) 查看日志                           ║"
    echo "║  7) 重启所有服务                       ║"
    echo "║  0) 退出                               ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
}

# 主函数
main() {
    # 创建日志目录
    mkdir -p logs
    
    # 如果提供了命令行参数，直接执行
    if [ $# -gt 0 ]; then
        case $1 in
            start)
                check_python
                check_node
                init_backend
                init_frontend
                start_backend
                start_frontend
                show_status
                ;;
            stop)
                stop_services
                ;;
            restart)
                stop_services
                sleep 2
                start_backend
                start_frontend
                ;;
            status)
                show_status
                ;;
            logs)
                view_logs
                ;;
            *)
                print_error "未知命令：$1"
                echo "可用命令：start, stop, restart, status, logs"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # 交互式菜单
    while true; do
        show_menu
        read -p "请选择操作 [0-7]: " choice
        
        case $choice in
            1)
                check_python
                check_node
                init_backend
                init_frontend
                start_backend
                start_frontend
                show_status
                ;;
            2)
                check_python
                init_backend
                start_backend
                ;;
            3)
                check_node
                init_frontend
                start_frontend
                ;;
            4)
                stop_services
                ;;
            5)
                show_status
                ;;
            6)
                view_logs
                ;;
            7)
                stop_services
                sleep 2
                start_backend
                start_frontend
                show_status
                ;;
            0)
                print_info "退出"
                exit 0
                ;;
            *)
                print_error "无效选择，请输入 0-7"
                ;;
        esac
    done
}

# 运行主函数
main "$@"
