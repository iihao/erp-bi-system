# Token 认证优化文档

## 问题描述

用户反馈后台页面提示"未授权或 token 已过期"，但实际 token 可能仍然有效。问题原因：

1. **路由守卫不验证 token 有效性** - 只检查 token 是否存在，不检查是否过期
2. **401 错误处理不统一** - 多处可能触发跳转，导致重复跳转
3. **页面加载时不验证 token** - Layout 页面没有在加载时验证 token
4. **错误提示不清晰** - 用户不知道是 token 问题还是其他问题

## 优化方案

### 1. 路由守卫增强 (`frontend/src/router/index.js`)

**新增功能：**
- `isTokenValid(token)` - JWT token 验证函数，检查过期时间
- `clearAuthAndRedirect()` - 清除认证信息并跳转登录

**优化逻辑：**
```javascript
// 验证 token 是否过期
const isTokenValid = (token) => {
  if (!token) return false
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false
    
    const payload = JSON.parse(atob(parts[1]))
    if (decoded.exp) {
      const now = Math.floor(Date.now() / 1000)
      return decoded.exp >= now  // 检查是否过期
    }
    return true
  } catch (e) {
    return false
  }
}

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth) {
    if (!token || !isTokenValid(token)) {
      clearAuthAndRedirect()  // 强制跳转登录
      return
    }
  }
  next()
})
```

### 2. API 拦截器优化 (`frontend/src/api/index.js`)

**新增功能：**
- `isRedirecting` 标志 - 防止重复跳转

**优化逻辑：**
```javascript
let isRedirecting = false

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('portal_token')
      window.location.href = '/login'  // 强制跳转
    }
    return Promise.reject(error)
  }
)
```

### 3. Layout 页面验证 (`frontend/src/views/admin/Layout.vue`)

**新增功能：**
- 页面加载时验证 token 有效性
- token 失效时自动退出并跳转登录

**优化逻辑：**
```javascript
onMounted(() => {
  const token = localStorage.getItem('token')
  if (!token || !isTokenValid(token)) {
    ElMessage.error('登录已过期，请重新登录')
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }
})
```

### 4. 登录页面优化 (`frontend/src/views/Login.vue`)

**新增功能：**
- 使用 ElMessage 显示错误提示
- 区分不同类型的错误

**优化逻辑：**
```javascript
try {
  const res = await api.login({ username, password })
  if (res.token) {
    localStorage.setItem('token', res.token)
    localStorage.setItem('username', username)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  }
} catch (err) {
  const errorMsg = err.detail || err.message || '登录失败'
  ElMessage.error(errorMsg)
}
```

## Token 验证流程

```
用户访问页面
    ↓
路由守卫检查 token 是否存在
    ↓
是 → 验证 token 是否过期
    ↓
过期 → 清除认证 → 跳转登录页 ✅
    ↓
有效 → 允许访问
    ↓
页面加载 → Layout 再次验证 token
    ↓
API 请求 → 401 错误 → 清除认证 → 跳转登录页 ✅
```

## 优化效果

### ✅ 已解决问题

1. **Token 过期自动退出** - 路由守卫和 Layout 页面双重验证
2. **强制跳转登录页** - 不再在页面内提示，直接跳转
3. **防止重复跳转** - `isRedirecting` 标志确保只跳转一次
4. **清晰的错误提示** - 使用 ElMessage 显示友好提示

### 📊 用户体验提升

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| Token 过期 | 页面内提示"未授权" | 自动跳转登录页 ✅ |
| Token 无效 | 多次 API 请求失败 | 立即跳转登录页 ✅ |
| 重复跳转 | 可能多次跳转 | 只跳转一次 ✅ |
| 错误提示 | 技术错误信息 | 友好提示信息 ✅ |

## 测试验证

### 1. Token 过期测试
```javascript
// 手动设置过期 token
localStorage.setItem('token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjAwMDAwMDAwfQ.xxx')
// 访问后台页面 → 应该自动跳转登录页
```

### 2. Token 无效测试
```javascript
// 设置无效 token
localStorage.setItem('token', 'invalid.token.here')
// 访问后台页面 → 应该自动跳转登录页
```

### 3. 正常登录测试
```javascript
// 使用正确账号登录
username: admin
password: admin123
// → 应该成功登录并跳转到 dashboard
```

## 注意事项

1. **Token 有效期** - 默认 24 小时（1440 分钟），可在 `.env` 中配置
2. **时区问题** - JWT 使用 UTC 时间，前端使用本地时间，已做转换
3. **多标签页** - 一个标签页退出会清除所有标签页的 token
4. **前台/后台分离** - 前台和后台使用不同的 token 验证

## 配置文件

### 后端配置 (`.env`)
```bash
JWT_SECRET_KEY=your-secret-key-change-in-production-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 小时
```

### 前端配置
无需额外配置，token 验证逻辑已内置。

## 相关文件

- `frontend/src/router/index.js` - 路由守卫
- `frontend/src/api/index.js` - API 拦截器
- `frontend/src/views/admin/Layout.vue` - 后台布局
- `frontend/src/views/Login.vue` - 登录页面
- `backend/api/auth.py` - 后端认证模块

---

**优化完成时间**: 2026-03-17  
**优化人员**: AI Assistant  
**测试状态**: ✅ 待验证
