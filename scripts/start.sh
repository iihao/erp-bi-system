#!/bin/bash
# ============================================================
# ERP-BI 一键启动脚本（答辩演示专用版）
# 使用前请阅读 DEMO_CHECKLIST.md
# ============================================================

set -e

# ========== 颜色输出 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; }

# ========== 项目路径 ==========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_DIR="$PROJECT_DIR/.pids"

# ========== 服务端口 ==========
BACKEND_PORT=8001
FRONTEND_PORT=9098
REDIS_PORT=6379
METABASE_PORT=3001

# ========== 前置检查 ==========
echo ""
echo "============================================"
echo -e "  ${BLUE}ERP-BI 系统启动前检查${NC}"
echo "============================================"
echo ""

ERRORS=0

# 1. 检查 Docker
info "检查 Docker 是否运行..."
if ! docker info > /dev/null 2>&1; then
    fail "Docker 未运行，请先启动 Docker Desktop"
    ERRORS=$((ERRORS + 1))
else
    ok "Docker 运行正常"
fi

# 2. 检查 Docker Compose
info "检查 Docker Compose..."
if ! docker compose version > /dev/null 2>&1 && ! docker-compose version > /dev/null 2>&1; then
    fail "Docker Compose 未安装"
    ERRORS=$((ERRORS + 1))
else
    ok "Docker Compose 可用"
fi

# 3. 检查 Node.js
info "检查 Node.js..."
if ! command -v node > /dev/null 2>&1; then
    fail "Node.js 未安装"
    ERRORS=$((ERRORS + 1))
else
    NODE_VER=$(node -v)
    ok "Node.js $NODE_VER"
fi

# 4. 检查 Python
info "检查 Python..."
if ! command -v python3 > /dev/null 2>&1; then
    fail "Python3 未安装"
    ERRORS=$((ERRORS + 1))
else
    PY_VER=$(python3 --version)
    ok "Python $PY_VER"
fi

# 5. 检查端口占用
check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t > /dev/null 2>&1; then
        local pid=$(lsof -ti :$port 2>/dev/null | head -1)
        warn "端口 $port ($name) 已被占用 (PID: $pid)，请先停止占用该端口的进程"
        ERRORS=$((ERRORS + 1))
    else
        ok "端口 $port ($name) 空闲"
    fi
}

info "检查端口占用..."
check_port $BACKEND_PORT "后端 API"
check_port $FRONTEND_PORT "前端页面"

# 6. 检查关键目录
for dir in "$BACKEND_DIR" "$FRONTEND_DIR"; do
    if [ ! -d "$dir" ]; then
        fail "目录不存在: $dir"
        ERRORS=$((ERRORS + 1))
    fi
done

# 7. 检查前端依赖
info "检查前端依赖..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    warn "前端 node_modules 不存在，将自动执行 npm install"
else
    ok "前端依赖已安装"
fi

# 8. 检查后端依赖
info "检查后端虚拟环境..."
if [ ! -d "$BACKEND_DIR/venv" ]; then
    warn "后端虚拟环境不存在，将自动创建并安装依赖"
else
    ok "后端虚拟环境存在"
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    fail "存在 $ERRORS 个错误，请先解决后再启动"
    echo ""
    exit 1
fi

# ========== 开始启动 ==========
echo ""
echo "============================================"
echo -e "  ${GREEN}所有检查通过，开始启动${NC}"
echo "============================================"
echo ""

# 创建 PID 目录
mkdir -p "$PID_DIR"

# -------------------------------------------
# [1/3] 启动基础设施（Docker）
# -------------------------------------------
echo -e "${BLUE}[1/3]${NC} 启动基础设施服务..."
cd "$PROJECT_DIR"

# 检查 Redis 和 Metabase 是否已在运行
REDIS_RUNNING=false
METABASE_RUNNING=false
if docker ps --format '{{.Names}}' | grep -q "erp-bi-redis"; then
    REDIS_RUNNING=true
    ok "Redis 容器已在运行"
fi
if docker ps --format '{{.Names}}' | grep -q "erp-bi-metabase"; then
    METABASE_RUNNING=true
    ok "Metabase 容器已在运行"
fi

# 只启动缺失的服务
NEED_START=""
if [ "$REDIS_RUNNING" = false ]; then
    NEED_START="$NEED_START redis"
fi
if [ "$METABASE_RUNNING" = false ]; then
    NEED_START="$NEED_START metabase"
fi

if [ -n "$NEED_START" ]; then
    info "启动缺失的服务: $NEED_START"
    docker compose up -d $NEED_START 2>&1 | tail -3
    ok "基础设施服务已启动"
else
    ok "所有基础设施服务已在运行"
fi

# 等待 Redis 就绪
info "等待 Redis 就绪..."
sleep 2
if docker exec erp-bi-redis redis-cli ping > /dev/null 2>&1; then
    ok "Redis 已就绪"
else
    warn "Redis 可能尚未完全就绪，继续启动其他服务..."
fi

echo ""

# -------------------------------------------
# [2/3] 启动后端服务
# -------------------------------------------
echo -e "${BLUE}[2/3]${NC} 启动后端服务..."
cd "$BACKEND_DIR"

# 创建/激活虚拟环境
if [ ! -d "venv" ]; then
    info "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 安装依赖（使用 --quiet 减少输出）
info "安装 Python 依赖..."
./venv/bin/pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
ok "Python 依赖就绪"

# 停止旧的后端进程（使用 PID 文件，避免误杀其他进程）
if [ -f "$PID_DIR/backend.pid" ]; then
    OLD_PID=$(cat "$PID_DIR/backend.pid")
    if kill -0 "$OLD_PID" > /dev/null 2>&1; then
        info "停止旧的后端进程 (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$PID_DIR/backend.pid"
fi

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 启动后端
info "启动后端服务 (端口 $BACKEND_PORT)..."
./venv/bin/uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT \
    > "$PROJECT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PID_DIR/backend.pid"
ok "后端进程已启动 (PID: $BACKEND_PID)"

# 等待后端就绪
info "等待后端服务就绪..."
for i in $(seq 1 15); do
    if curl -sf "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        ok "后端服务已就绪 (http://localhost:$BACKEND_PORT)"
        break
    fi
    if [ $i -eq 15 ]; then
        warn "后端服务启动超时，请查看日志: $PROJECT_DIR/logs/backend.log"
    fi
    sleep 1
done

echo ""

# -------------------------------------------
# [3/3] 启动前端服务
# -------------------------------------------
echo -e "${BLUE}[3/3]${NC} 启动前端服务..."
cd "$FRONTEND_DIR"

# 安装依赖
if [ ! -d "node_modules" ]; then
    info "安装前端依赖..."
    npm install 2>&1 | tail -3
fi

# 停止旧的前端进程
if [ -f "$PID_DIR/frontend.pid" ]; then
    OLD_PID=$(cat "$PID_DIR/frontend.pid")
    if kill -0 "$OLD_PID" > /dev/null 2>&1; then
        info "停止旧的前端进程 (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$PID_DIR/frontend.pid"
fi

# 启动前端
info "启动前端服务 (端口 $FRONTEND_PORT)..."
npx vite --port $FRONTEND_PORT > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PID_DIR/frontend.pid"
ok "前端进程已启动 (PID: $FRONTEND_PID)"

# 等待前端就绪
info "等待前端服务就绪..."
for i in $(seq 1 10); do
    if curl -sf "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        ok "前端服务已就绪 (http://localhost:$FRONTEND_PORT)"
        break
    fi
    if [ $i -eq 10 ]; then
        warn "前端服务启动超时，请查看日志: $PROJECT_DIR/logs/frontend.log"
    fi
    sleep 1
done

# ========== 启动完成 ==========
echo ""
echo "============================================"
echo -e "  ${GREEN}ERP-BI 系统启动完成！${NC}"
echo "============================================"
echo ""
echo -e "${BLUE}📌 访问地址：${NC}"
echo -e "   前端界面：  ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "   后端 API：  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "   API 文档：  ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "   Metabase：  ${GREEN}http://localhost:$METABASE_PORT${NC}"
echo ""
echo -e "${BLUE}🔑 测试账号：${NC}"
echo -e "   用户名：${YELLOW}admin${NC}"
echo -e "   密码：  ${YELLOW}admin123${NC}"
echo ""
echo -e "${BLUE}📋 日志文件：${NC}"
echo -e "   后端日志：$PROJECT_DIR/logs/backend.log"
echo -e "   前端日志：$PROJECT_DIR/logs/frontend.log"
echo ""
echo -e "${BLUE}🛑 停止服务：${NC}"
echo -e "   运行：${YELLOW}./scripts/stop.sh${NC}"
echo ""
