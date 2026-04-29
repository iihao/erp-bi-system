# 代码检查和修复报告

**检查日期**: 2026-03-15
**项目名称**: AI数据融合平台

## 问题汇总和修复

### 1. 后端安全问题

#### 1.1 JWT 密钥配置问题
**文件**: `backend/api/auth.py`

**问题**: 使用了不安全的默认 JWT 密钥
```python
# 修复前
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

**修复**:
```python
# 修复后
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-at-least-32-chars")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 小时
```

#### 1.2 API 密钥硬编码
**文件**: `backend/api/ai_query.py`

**问题**: 硬编码了 DASHSCOPE_API_KEY
```python
# 修复前
self.api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-sp-33f546ba9e12486ab6b9f08b9789ea1b')
```

**修复**:
```python
# 修复后
self.api_key = os.getenv('DASHSCOPE_API_KEY')
if not self.api_key:
    logger.warning("DASHSCOPE_API_KEY 环境变量未设置，AI 问数功能将不可用")
```

### 2. 后端依赖问题

#### 2.1 requirements.txt 缺少依赖
**文件**: `backend/requirements.txt`

**问题**: 缺少必要的依赖包

**修复**: 添加以下依赖:
```
httpx==0.26.0
python-dotenv==1.0.0
psutil==5.9.7
sqlalchemy==2.0.25
```

### 3. 后端架构问题

#### 3.1 用户存储使用内存而非数据库
**文件**: `backend/main.py`

**问题**: 登录/注册功能使用内存字典而非数据库存储

**修复**: 修改为使用 SQLite 数据库:
```python
# 从数据库查询用户
users = execute_query("SELECT * FROM users WHERE username = ?", (request.username,))

# 创建 token 时使用用户 ID
access_token = create_access_token(
    data={"sub": str(user["user_id"])},
    expires_delta=timedelta(hours=24)
)

# 更新最后登录时间
execute_update("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user["user_id"],))
```

#### 3.2 数据库初始化逻辑改进
**文件**: `backend/api/database.py`

**问题**: 数据库目录可能不存在，初始化逻辑缩进混乱

**修复**:
- 添加目录创建逻辑：`os.makedirs(db_dir, exist_ok=True)`
- 修复所有 SQL 语句的缩进问题

### 4. 前端配置问题

#### 4.1 API 基础 URL 硬编码
**文件**:
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/reports/SalesReport.vue`

**问题**: 使用硬编码的 `http://localhost:8000`

**修复**:
```javascript
// 使用相对路径，通过 Vite 代理转发
const API_BASE = '/api/reports'
```

#### 4.2 登录成功后未存储用户名
**文件**: `frontend/src/views/Login.vue`

**问题**: 登录后只存储了 token，未存储用户名，导致 NavBar 显示异常

**修复**:
```javascript
localStorage.setItem('token', res.token)
localStorage.setItem('username', username.value)
```

### 5. 环境配置文件

#### 5.1 新增后端环境配置示例
**文件**: `backend/.env.example`

包含以下配置项:
- JWT 密钥配置
- 数据库配置 (SQLite/MySQL)
- 百炼 API 配置

#### 5.2 新增前端环境配置示例
**文件**: `frontend/.env.example`

包含 Vite 开发服务器配置说明

## 使用指南

### 后端启动

1. 复制环境配置文件:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置必要的环境变量:
   ```bash
   JWT_SECRET_KEY=<生成一个随机密钥>
   DASHSCOPE_API_KEY=<你的百炼 API 密钥>
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 启动服务:
   ```bash
   python main.py
   ```

### 前端启动

1. 安装依赖:
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器:
   ```bash
   npm run dev
   ```

3. 访问 `http://localhost:3000`

## 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

**注意**: 首次启动时会自动创建数据库和默认管理员账号。

## 安全建议

1. **生产环境必须修改 JWT_SECRET_KEY**，使用至少 32 个字符的随机字符串
2. **配置有效的 DASHSCOPE_API_KEY** 以启用 AI 问数功能
3. **限制 CORS 允许的来源**，修改 `backend/main.py` 中的 `allow_origins`
4. **使用 MySQL 替代 SQLite** 以获得更好的性能和并发支持
5. **启用 HTTPS** 以保护敏感数据传输

## 修复验证

所有修复已完成，建议进行以下测试:

- [ ] 用户登录/注册功能
- [ ] JWT token 生成和验证
- [ ] 数据库初始化
- [ ] API 请求代理
- [ ] AI 问数功能 (需配置 API 密钥)
- [ ] 后台管理功能
