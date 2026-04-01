#!/bin/bash
#
# Bamboo 一键启动脚本 - 同时启动前后端开发服务器
# 功能：检测并释放端口占用，Ctrl-C / 关闭终端自动退出所有进程
#

set -e

# ─── 配置 ───
BACKEND_PORT=5001
FRONTEND_PORT=5173
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$PROJECT_DIR/venv"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ─── 子进程 PID 收集 ───
BACKEND_PID=""
FRONTEND_PID=""
CHILD_PIDS=()

cleanup() {
    echo ""
    info "正在停止所有服务..."

    # 先 kill 子进程（如果还在运行）
    for pid in "${CHILD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done

    # kill 后端
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        info "停止后端 (PID: $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi

    # kill 前端
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        info "停止前端 (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    # 等待进程退出，最多 5 秒
    local waited=0
    while [ $waited -lt 50 ]; do
        local all_dead=true
        for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                all_dead=false
                break
            fi
        done
        $all_dead && break
        sleep 0.1
        waited=$((waited + 1))
    done

    # 如果还没退出，强制 kill
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done

    ok "所有服务已停止"
    exit 0
}

# 注册退出信号处理
trap cleanup EXIT INT TERM

# ─── 端口检测与释放 ───
check_and_free_port() {
    local port=$1
    local name=$2
    local pids

    pids=$(lsof -ti :"$port" 2>/dev/null || true)

    if [ -z "$pids" ]; then
        ok "端口 $port ($name) 可用"
        return 0
    fi

    warn "端口 $port ($name) 被占用，正在释放..."
    for pid in $pids; do
        local cmd
        cmd=$(ps -p "$pid" -o command= 2>/dev/null || echo "unknown")
        warn "  终止进程 PID=$pid: $cmd"
        kill "$pid" 2>/dev/null || true
    done

    # 等待端口释放，最多 5 秒
    local waited=0
    while [ $waited -lt 50 ]; do
        if ! lsof -ti :"$port" 2>/dev/null | grep -q .; then
            ok "端口 $port 已释放"
            return 0
        fi
        sleep 0.1
        waited=$((waited + 1))
    done

    # 超时后强制 kill
    err "端口 $port 释放超时，强制终止..."
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    for pid in $pids; do
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 0.5

    if lsof -ti :"$port" 2>/dev/null | grep -q .; then
        err "无法释放端口 $port，请手动处理"
        exit 1
    fi

    ok "端口 $port 已强制释放"
}

# ─── 前置检查 ───
info "========================================="
info "  Bamboo 一键启动"
info "========================================="
echo ""

# 检查后端虚拟环境（支持 backend/venv 或项目根目录 venv）
if [ -d "$BACKEND_DIR/venv" ]; then
    VENV_DIR="$BACKEND_DIR/venv"
elif [ -d "$PROJECT_DIR/venv" ]; then
    VENV_DIR="$PROJECT_DIR/venv"
else
    err "虚拟环境不存在"
    info "请先运行: python -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# 检查前端依赖
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    warn "前端依赖未安装，正在安装..."
    (cd "$FRONTEND_DIR" && npm install)
fi

# 检查端口
info "检测端口..."
check_and_free_port $BACKEND_PORT "后端"
check_and_free_port $FRONTEND_PORT "前端"
echo ""

# ─── 启动后端 ───
info "启动后端服务 (端口: $BACKEND_PORT)..."
(
    cd "$BACKEND_DIR"
    "$VENV_DIR/bin/python3" app.py
) &
BACKEND_PID=$!

# ─── 启动前端 ───
info "启动前端服务 (端口: $FRONTEND_PORT)..."
(
    cd "$FRONTEND_DIR"
    npm run dev
) &
FRONTEND_PID=$!

echo ""
info "========================================="
ok "前后端已启动！"
info "  前端: http://localhost:$FRONTEND_PORT"
info "  后端: http://localhost:$BACKEND_PORT"
info "  按 Ctrl-C 停止所有服务"
info "========================================="
echo ""

# ─── 等待任意子进程退出 ───
# 用 wait -n 等待第一个退出的子进程（bash 4.3+）
# macOS 自带 bash 3.x 不支持 wait -n，所以用循环方式
while true; do
    # 检查后端是否还在
    if [ -n "$BACKEND_PID" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        err "后端服务异常退出"
        break
    fi
    # 检查前端是否还在
    if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        err "前端服务异常退出"
        break
    fi
    sleep 1
done

# 到达这里说明有服务异常退出，cleanup trap 会自动清理
