# AI数据融合平台 - 测试验证指南

## 一、启动说明

### 1. 启动后端服务
```bash
cd backend
source venv/bin/activate  # 或使用 venv\Scripts\activate (Windows)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

## 二、测试用户账号

系统预定义三种角色，使用相同的登录接口：

| 角色 | 用户名 | 密码 | 权限说明 |
|------|--------|------|----------|
| 超级管理员 | admin | admin123 | 可访问所有报表 |
| 数据分析师 | analyst | analyst123 | 可访问基础报表 + 分析报表 |
| 普通用户 | user | user123 | 仅可访问基础报表 |

## 三、测试步骤

### 步骤 1: 访问前台登录页
- 访问 `http://localhost:5173/portal/login`
- 验证页面显示商务风格的登录界面
- 点击「返回后台管理」可跳转到后台登录页

### 步骤 2: 使用不同角色登录
分别使用上述三种账号登录，验证：
- 登录成功跳转到仪表板
- 右上角显示用户名和角色标签

### 步骤 3: 验证权限控制

#### 普通用户 (user) 可访问：
- [x] 销售概览
- [x] 销售趋势
- [x] 产品排行
- [x] 品类分析

#### 数据分析师 (analyst) 额外可访问：
- [x] 客户分析
- [x] 利润分析
- [x] 库存报表

#### 超级管理员 (admin) 额外可访问：
- [x] 预测报表

### 步骤 4: 验证报表功能

1. **仪表板** (`/portal`)
   - 显示 4 个 KPI 卡片
   - 销售趋势图（近 6 个月）
   - 品类占比饼图
   - 产品排行 Top 5
   - 快捷入口

2. **报表列表** (`/portal/reports`)
   - 按分类筛选（全部/基础/分析/高级）
   - 仅显示用户有权限的报表
   - 点击卡片进入详情页

3. **报表详情** (`/portal/report/:id`)
   - 销售趋势：支持切换 近半年/近一年/近一年半
   - 产品排行：支持切换 Top 10/20/50
   - 品类分析：饼图 + 表格展示
   - 客户分析：详细数据表格
   - 利润分析：利润趋势图表
   - 库存报表：库存周转率表格
   - 预测报表：未来 6 个月预测

### 步骤 5: 验证响应式
- 调整浏览器窗口大小
- 在移动端视图下测试侧边栏折叠功能

## 四、API 端点测试

使用 curl 或 Postman 测试 API：

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}'

# 2. 获取报表列表（替换为实际 token）
curl http://localhost:8000/api/portal/reports \
  -H "Authorization: Bearer <token>"

# 3. 获取 KPI 指标
curl http://localhost:8000/api/portal/kpi \
  -H "Authorization: Bearer <token>"

# 4. 获取销售趋势
curl "http://localhost:8000/api/portal/sales-trend?months=12" \
  -H "Authorization: Bearer <token>"

# 5. 获取产品排行
curl "http://localhost:8000/api/portal/product-ranking?limit=10" \
  -H "Authorization: Bearer <token>"

# 6. 获取品类分析
curl http://localhost:8000/api/portal/category-analysis \
  -H "Authorization: Bearer <token>"

# 7. 获取单个报表数据
curl http://localhost:8000/api/portal/report/sales-overview \
  -H "Authorization: Bearer <token>"

# 8. 获取前台概览
curl http://localhost:8000/api/portal/overview \
  -H "Authorization: Bearer <token>"
```

## 五、权限验证测试

### 测试无权限访问
使用普通用户 token 访问受限报表：
```bash
# 应返回 403 Forbidden
curl http://localhost:8000/api/portal/report/forecast-report \
  -H "Authorization: Bearer <user_token>"
```

### 测试无认证访问
不带 token 访问：
```bash
# 应返回 401 Unauthorized
curl http://localhost:8000/api/portal/reports
```

## 六、预期结果

1. **登录功能**: 三种角色均可成功登录
2. **权限隔离**: 普通用户无法访问分析/高级报表
3. **数据展示**: 所有图表正常渲染，数据正确显示
4. **响应式**: 移动端适配正常
5. **路由守卫**: 未登录自动跳转到登录页

## 七、常见问题排查

### 问题 1: 登录失败
- 检查后端服务是否启动
- 确认数据库连接正常
- 检查用户表是否有测试数据

### 问题 2: 图表不显示
- 检查 echarts 是否正确安装：`npm list echarts`
- 检查浏览器控制台是否有报错
- 确认 DOM 元素已渲染

### 问题 3: 401/403 错误
- 确认 token 是否有效
- 检查用户角色权限配置
- 验证路由守卫逻辑

## 八、创建测试数据

如果数据库为空，执行以下 SQL 创建测试用户：

```sql
-- 插入测试用户 (密码均为 123456 的 SHA256 哈希)
INSERT INTO users (username, password_hash, email, real_name, role_id, status) VALUES
('admin', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'admin@example.com', '系统管理员', 1, 1),
('analyst', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'analyst@example.com', '数据分析师', 2, 1),
('user', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'user@example.com', '普通用户', 3, 1);
```

注意：请确保 roles 表中存在对应的角色记录。
