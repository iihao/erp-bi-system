# 答辩演示操作指南

> 版本：2026-05-10 | 预计准备时间：5 分钟

## 🚀 一键启动

```bash
cd /Users/huangqiang/projects/erp-bi-system
./scripts/start.sh
```

启动后等待所有服务就绪，确认看到绿色的 "ERP-BI 系统启动完成！" 提示。

## 📌 服务地址

| 服务 | 地址 | 用途 |
|------|------|------|
| 前端界面 | http://localhost:9098 | 主演示页面 |
| 后端 API | http://localhost:8001 | 后端接口 |
| API 文档 | http://localhost:8001/docs | Swagger 接口文档 |
| Metabase | http://localhost:3001 | BI 自助分析 |

## 🔑 测试账号

- **用户名：** `admin`
- **密码：** `admin123`

## 🛑 停止服务

```bash
./scripts/stop.sh
```

## ⚠️ 常见问题排查

### 1. 端口被占用

如果启动时提示端口 8001 或 9098 被占用：

```bash
# 查看占用 8001 端口的进程
lsof -i :8001
# 查看占用 9098 端口的进程
lsof -i :9098

# 杀掉占用端口的进程（替换 PID 为实际进程号）
kill -9 <PID>
```

### 2. Docker 未运行

确保 Docker Desktop 已启动：
- Mac: 打开 Docker Desktop 应用，等待鲸鱼图标变为正常运行状态
- 确认 `docker ps` 命令能正常执行

### 3. 后端启动失败

```bash
# 查看后端日志
cat logs/backend.log

# 手动启动后端排查
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 4. 前端启动失败

```bash
# 查看前端日志
cat logs/frontend.log

# 手动启动前端排查
cd frontend
npm run dev
```

### 5. Redis/Metabase 容器问题

```bash
# 查看容器状态
docker ps | grep erp-bi

# 重启容器
docker compose restart redis metabase
```

## 📋 演示前检查清单

- [ ] Docker Desktop 已启动且正常运行
- [ ] 执行 `./scripts/start.sh` 无报错
- [ ] 浏览器能打开 http://localhost:9098
- [ ] 能用 admin/admin123 登录成功
- [ ] 仪表板页面数据正常加载
- [ ] AI 智能问数功能可用（需要网络连接调用百炼 API）
- [ ] Metabase 页面 http://localhost:3001 能正常访问
- [ ] 关闭所有可能占用端口 8001/9098 的其他程序
- [ ] 确认电脑网络稳定（AI 功能需要联网）

## 💡 演示建议

1. **提前 5-10 分钟启动**，确保所有服务都已就绪
2. **打开 2 个浏览器标签页**：一个前端页面 + 一个 Metabase
3. **准备好 2-3 个 AI 问数示例**，提前测试确保可用
4. **如果 AI 功能出现问题**，可以先展示自研前端报表和 Metabase
5. **演示期间不要关闭终端窗口**

## 🔧 手动启动（备用方案）

如果一键脚本出现问题，可以分步手动启动：

```bash
# 终端 1：启动 Docker 基础设施
cd /Users/huangqiang/projects/erp-bi-system
docker compose up -d redis metabase

# 终端 2：启动后端
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001

# 终端 3：启动前端
cd frontend
npm run dev
```
