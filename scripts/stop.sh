#!/bin/bash
# ============================================================
# AI数据融合平台停止脚本
# ============================================================

set -e

echo "============================================"
echo "  AI数据融合平台停止"
echo "============================================"

# 停止前端服务
echo ""
echo "[1/3] 停止前端服务..."
pkill -f "vite" 2>/dev/null || echo "前端服务未运行"
echo "前端服务已停止"

# 停止后端服务
echo ""
echo "[2/3] 停止后端服务..."
pkill -f "uvicorn main:app" 2>/dev/null || echo "后端服务未运行"
echo "后端服务已停止"

# 停止 Docker 容器
echo ""
echo "[3/3] 停止 Docker 容器..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
docker-compose down
echo "Docker 容器已停止"

echo ""
echo "============================================"
echo "  AI数据融合平台已完全停止"
echo "============================================"
