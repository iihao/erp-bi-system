#!/bin/bash
# ============================================================
# AI数据融合平台启动脚本
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "============================================"
echo "  AI数据融合平台启动"
echo "============================================"

# 1. 启动数据库和中间件 (Docker Compose)
echo ""
echo "[1/4] 启动数据库、中间件和 BI 服务..."
cd "$PROJECT_DIR"
docker-compose up -d mysql redis metabase

# 等待 MySQL 启动
echo "等待 MySQL 启动..."
sleep 10

# 检查 MySQL 是否就绪
until docker exec erp-bi-mysql mysqladmin ping -h localhost -uroot -proot123 > /dev/null 2>&1; do
    echo "等待 MySQL 就绪..."
    sleep 2
done
echo "MySQL 已就绪!"

# 2. 初始化数据库 (如果未初始化)
echo ""
echo "[2/4] 检查数据库初始化状态..."
DB_CHECK=$(docker exec erp-bi-mysql mysql -uroot -proot123 -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'erp_source'" 2>/dev/null | tail -1)
if [ "$DB_CHECK" -lt 10 ]; then
    echo "初始化数据库..."
    docker exec -i erp-bi-mysql mysql -uroot -proot123 < "$PROJECT_DIR/init_scripts/erp_init.sql"
    echo "数据库初始化完成!"
else
    echo "数据库已初始化，跳过..."
fi

# 3. 启动后端服务
echo ""
echo "[3/4] 启动后端服务..."
cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 安装依赖
echo "安装 Python 依赖..."
./venv/bin/pip install -r requirements.txt -q

# 启动后端
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

nohup ./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 3

# 检查后端是否启动
if curl -s http://localhost:8000/health > /dev/null; then
    echo "后端服务已启动 (http://localhost:8000)"
else
    echo "警告：后端服务可能未正常启动，请检查 /tmp/backend.log"
fi

# 4. 启动前端服务
echo ""
echo "[4/4] 启动前端服务..."
cd "$FRONTEND_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端
pkill -f "vite" 2>/dev/null || true
sleep 1

nohup npm run dev > /tmp/frontend.log 2>&1 &
sleep 3

# 检查前端是否启动
if curl -s http://localhost:3000 > /dev/null; then
    echo "前端服务已启动 (http://localhost:3000)"
else
    echo "警告：前端服务可能未正常启动，请检查 /tmp/frontend.log"
fi

# 完成
echo ""
echo "============================================"
echo "  AI数据融合平台启动完成!"
echo "============================================"
echo ""
echo "访问地址:"
echo "  - 前端界面：http://localhost:3000"
echo "  - 后端 API:  http://localhost:8000"
echo "  - API 文档：http://localhost:8000/docs"
echo "  - Metabase BI: http://localhost:3001"
echo ""
echo "测试账号:"
echo "  - 用户名：admin"
echo "  - 密码：admin123"
echo ""
echo "停止服务:"
echo "  ./scripts/stop.sh"
echo ""
