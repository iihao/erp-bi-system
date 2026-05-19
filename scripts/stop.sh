#!/bin/bash
# ============================================================
# ERP-BI 一键停止脚本
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_DIR/.pids"

echo ""
echo "============================================"
echo -e "  ${RED}ERP-BI 系统停止${NC}"
echo "============================================"
echo ""

# 1. 停止前端
if [ -f "$PID_DIR/frontend.pid" ]; then
    PID=$(cat "$PID_DIR/frontend.pid")
    if kill -0 "$PID" > /dev/null 2>&1; then
        info "停止前端服务 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        ok "前端服务已停止"
    else
        info "前端进程不存在，跳过"
    fi
    rm -f "$PID_DIR/frontend.pid"
else
    # 兜底：如果没有 PID 文件，尝试按端口查找
    FPID=$(lsof -ti :9098 2>/dev/null | head -1)
    if [ -n "$FPID" ]; then
        info "通过端口 9098 找到前端进程 (PID: $FPID)，停止中..."
        kill "$FPID" 2>/dev/null || true
        ok "前端服务已停止"
    else
        info "前端服务未运行"
    fi
fi

# 2. 停止后端
if [ -f "$PID_DIR/backend.pid" ]; then
    PID=$(cat "$PID_DIR/backend.pid")
    if kill -0 "$PID" > /dev/null 2>&1; then
        info "停止后端服务 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        ok "后端服务已停止"
    else
        info "后端进程不存在，跳过"
    fi
    rm -f "$PID_DIR/backend.pid"
else
    # 兜底：按端口查找
    BPID=$(lsof -ti :8001 2>/dev/null | head -1)
    if [ -n "$BPID" ]; then
        info "通过端口 8001 找到后端进程 (PID: $BPID)，停止中..."
        kill "$BPID" 2>/dev/null || true
        ok "后端服务已停止"
    else
        info "后端服务未运行"
    fi
fi

# 3. 停止 Docker 容器
echo ""
info "停止 Docker 容器..."
cd "$PROJECT_DIR"
if docker compose ps --services 2>/dev/null | grep -q .; then
    docker compose stop 2>&1 | tail -5
    ok "Docker 容器已停止"
else
    info "没有运行中的容器"
fi

echo ""
echo "============================================"
echo -e "  ${GREEN}ERP-BI 系统已完全停止${NC}"
echo "============================================"
echo ""
