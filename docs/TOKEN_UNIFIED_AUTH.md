# Token 统一认证实施报告

**实施时间：** 2026-03-18  
**实施人员：** mac🦀  
**功能模块：** 认证授权 - Token 统一管理

---

## 📋 一、实施概述

本次实施统一了门户和后台的 Token 认证机制：

1. ✅ **Token 共用** - 门户和后台使用同一个 `token`
2. ✅ **统一验证** - 路由守卫统一检查 token 有效性
3. ✅ **强制跳转** - Token 失效时强制跳转到登录页
4. ✅ **API 拦截** - 401 错误自动清除 token 并跳转

---

## 🔧 二、修改内容

### 2.1 路由守卫统一

**文件：** `frontend/src/router/index.js`

```javascript
router.beforeEach((to, from, next) => {
  // 统一使用 token 进行认证（门户和后台共用）
  const token = localStorage.getItem('token')

  // 检查是否需要认证（门户和后台都需要）
  const requiresAuth = to.meta.requiresAuth || to.meta.requiresPortalAuth

  if (requiresAuth) {
    if (!token || !isTokenValid(token)) {
      console.warn('[路由守卫] Token 失效，强制跳转登录页')
      clearAuthAndRedirect()
      return
    }
  }

  // 如果已登录且访问登录页，重定向到前台门户
  if (to.path === '/login' && token && isTokenValid(token)) {
    next('/portal')
    return
  }

  next()
})
```

### 2.2 API 拦截器统一

**文件：** `frontend/src/api/index.js`

```javascript
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true
      // Token 失效，清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('portal_token')
      // 强制跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error.response?.data || error)
  }
)
```

### 2.3 门户页面 Token 统一

**修改的文件：**
- `views/portal/AIQuery.vue`
- `views/portal/Dashboard.vue`
- `views/portal/Layout.vue`
- `views/portal/Login.vue`
- `views/portal/ReportDetail.vue`
- `views/portal/ReportPortal.vue`
- `views/portal/Reports.vue`

**修改内容：**
```javascript
// 修改前
const token = localStorage.getItem('portal_token')

// 修改后
const token = localStorage.getItem('token')
```

---

## 🔑 三、Token 存储

### 3.1 存储键名

| 键名 | 用途 | 说明 |
|------|------|------|
| `token` | ✅ 主 Token | 门户和后台共用 |
| `username` | ✅ 用户名 | 显示用 |
| `portal_token` | ❌ 已废弃 | 不再使用 |

### 3.2 Token 格式

```javascript
// JWT Token 结构
{
  "sub": "1",           // 用户 ID
  "exp": 1773886301,    // 过期时间（Unix 时间戳）
  // ... 其他 claims
}

// Token 有效期：24 小时
```

---

## 🔒 四、认证流程

### 4.1 登录流程

```
用户登录
  ↓
POST /api/auth/login
  ↓
返回 token
  ↓
保存到 localStorage.token
  ↓
跳转到 /portal
```

### 4.2 访问控制流程

```
访问页面
  ↓
路由守卫检查
  ↓
需要认证？
  ├─ 是 → 检查 token
  │      ├─ 有效 → 允许访问
  │      └─ 失效 → 清除 token → 跳转 /login
  └─ 否 → 允许访问
```

### 4.3 Token 失效处理

**场景 1：路由守卫检测**
```javascript
if (!token || !isTokenValid(token)) {
  clearAuthAndRedirect()  // 清除存储 + 跳转登录
}
```

**场景 2：API 请求 401**
```javascript
if (error.response?.status === 401) {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  window.location.href = '/login'
}
```

**场景 3：页面内检查**
```javascript
const checkToken = () => {
  const token = localStorage.getItem('token')
  if (!token || !isTokenValid(token)) {
    router.push('/login')
  }
}
```

---

## 📁 五、修改的文件

### 前端文件

| 文件 | 修改内容 |
|------|---------|
| `src/router/index.js` | 统一路由守卫逻辑 |
| `src/api/index.js` | 已存在，无需修改 |
| `src/views/portal/*.vue` | 替换 portal_token 为 token |

### 后端文件

无需修改，后端已统一使用 `/api/auth/login` 接口。

---

## ✅ 六、验证测试

### 6.1 登录测试

1. 访问 http://localhost:3000/login
2. 输入账号：admin / admin123
3. 登录成功
4. 检查 localStorage：
   - ✅ `token` 存在
   - ❌ `portal_token` 不存在

### 6.2 访问控制测试

**测试 1：未登录访问后台**
```
1. 清除 localStorage
2. 访问 /admin/datasources
3. 预期：自动跳转到 /login
```

**测试 2：未登录访问门户**
```
1. 清除 localStorage
2. 访问 /portal/dashboard
3. 预期：自动跳转到 /login
```

**测试 3：Token 过期**
```
1. 修改 localStorage.token 的过期时间为过去
2. 访问任意需要认证的页面
3. 预期：自动跳转到 /login
```

**测试 4：API 返回 401**
```
1. 使用过期的 token 调用 API
2. 后端返回 401
3. 预期：自动跳转到 /login
```

---

## 🎯 七、安全特性

### 7.1 Token 验证

```javascript
const isTokenValid = (token) => {
  if (!token) return false
  
  // 验证 JWT 格式
  const parts = token.split('.')
  if (parts.length !== 3) return false
  
  // 解码并检查过期时间
  const payload = JSON.parse(atob(parts[1]))
  if (payload.exp && payload.exp < Date.now() / 1000) {
    return false
  }
  
  return true
}
```

### 7.2 防止死循环

```javascript
// 防止重复跳转
let isRedirecting = false

if (error.response?.status === 401 && !isRedirecting) {
  isRedirecting = true
  // 跳转逻辑
}
```

### 7.3 强制跳转

```javascript
// 使用 window.location 而不是 router.push
// 避免路由守卫死循环
window.location.href = '/login'
```

---

## 🎓 八、总结

**实施效果：**
- ✅ 门户和后台 Token 统一管理
- ✅ Token 失效自动跳转登录
- ✅ API 401 错误自动处理
- ✅ 所有页面统一使用 `token`

**安全提升：**
- 🔒 Token 过期自动清除
- 🔒 401 错误强制跳转
- 🔒 防止路由守卫死循环
- 🔒 统一的认证流程

**下一步：**
1. 添加 Token 刷新机制
2. 实现记住登录功能
3. 添加多设备登录控制
4. 实现 Token 黑名单

---

**实施完成时间：** 2026-03-18 22:20  
**实施状态：** ✅ 已完成
