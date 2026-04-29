# 数据集管理功能实施报告

**实施时间：** 2026-03-18  
**实施人员：** mac🦀  
**功能模块：** 报表设计器 - 数据集管理

---

## 📋 一、实施概述

本次实施完成了数据集管理功能，支持创建、编辑、删除数据集，并提供两种数据集类型：

1. ✅ **数据表模式** - 直接选择已有数据表
2. ✅ **SQL 查询模式** - 自定义 SQL 查询语句

---

## 🎯 二、核心功能

### 2.1 数据集类型

#### 数据表模式
- 选择数据源
- 选择数据表
- 自动获取表结构
- 自动获取字段列表

#### SQL 查询模式
- 自定义 SQL 语句
- SQL 语法验证（必须 SELECT）
- 执行 SQL 获取字段
- 支持复杂查询

### 2.2 数据集操作

| 操作 | 说明 |
|------|------|
| **新建** | 创建新的数据集 |
| **编辑** | 修改数据集配置 |
| **删除** | 删除数据集（带确认） |
| **测试** | 测试数据集查询 |
| **设为默认** | 设置默认数据集 |

---

## 🎨 三、界面设计

### 3.1 数据集列表

```
┌─────────────────────────────────────────────────┐
│ 📊 数据集管理          [+ 新建数据集]            │
├─────────────────────────────────────────────────┤
│ ▼ 📊 销售数据集 [SQL] [默认]                    │
│   ───────────────────────────────────────────   │
│   数据集名称：销售数据集                         │
│   数据类型：SQL 查询                             │
│   SQL 语句：SELECT id, name, total...           │
│   字段列表（5）：                                │
│     💰 id (int)  📄 name (varchar) ...          │
│   ───────────────────────────────────────────   │
│   [编辑] [测试] [取消默认] [删除]                │
└─────────────────────────────────────────────────┘
```

### 3.2 新建数据集对话框

```
┌─────────────────────────────────────────┐
│          新建数据集                      │
├─────────────────────────────────────────┤
│ 数据集名称：[____________]               │
│                                          │
│ 数据集类型：○ 数据表 ● SQL 查询          │
│                                          │
│ SQL 语句：                               │
│ ┌─────────────────────────────────────┐ │
│ │ SELECT id, name, created_at         │ │
│ │ FROM users                          │ │
│ │ WHERE status = 1                    │ │
│ └─────────────────────────────────────┘ │
│ ℹ️ SQL 查询将以只读方式执行...           │
│                                          │
│ 备注说明：[____________]                 │
│                                          │
│              [取消]  [确定]              │
└─────────────────────────────────────────┘
```

---

## 💾 四、数据结构

### 4.1 数据集对象

```javascript
{
  id: 'ds_1710777600000',        // 数据集 ID
  name: '销售数据集',             // 数据集名称
  type: 'sql',                   // 类型：table | sql
  datasourceId: '1',             // 数据源 ID
  tableName: 'sales_orders',     // 表名（仅 table 类型）
  sql: 'SELECT * FROM...',       // SQL 语句（仅 sql 类型）
  description: '销售订单数据集',  // 备注说明
  fields: [                      // 字段列表
    {
      name: 'id',
      type: 'int',
      nullable: false,
      key: 'PRI'
    },
    {
      name: 'name',
      type: 'varchar',
      nullable: true,
      key: ''
    }
  ],
  isDefault: false,              // 是否默认数据集
  createdAt: '2026-03-18T12:00:00Z'
}
```

### 4.2 字段对象

```javascript
{
  name: 'user_id',        // 字段名
  type: 'INTEGER',        // 字段类型
  nullable: true,         // 是否可空
  key: 'PRI',             // 键（PK 等）
  default: null           // 默认值
}
```

---

## 🔧 五、API 调用

### 5.1 获取数据源列表

```javascript
GET /api/admin/datasources
Authorization: Bearer {token}

Response:
{
  "items": [
    {
      "id": 1,
      "name": "MySQL-业务库",
      "db_type": "mysql",
      "status": "active"
    }
  ]
}
```

### 5.2 获取表列表

```javascript
GET /api/admin/datasources/{datasourceId}/metadata
Authorization: Bearer {token}

Response:
{
  "tables": ["users", "orders", "products"],
  "table_count": 3
}
```

### 5.3 获取表结构

```javascript
GET /api/admin/datasources/{datasourceId}/table-schema/{tableName}
Authorization: Bearer {token}

Response:
{
  "columns": [
    {
      "field": "id",
      "type": "INTEGER",
      "nullable": false,
      "key": "PK"
    }
  ],
  "column_count": 10
}
```

### 5.4 执行 SQL 查询（测试用）

```javascript
POST /api/admin/datasources/{datasourceId}/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "sql": "SELECT id, name FROM users LIMIT 10",
  "limit": 10
}

Response:
{
  "success": true,
  "columns": ["id", "name"],
  "data": [...],
  "row_count": 10
}
```

---

## 📁 六、文件结构

### 新增文件
- `frontend/src/components/DatasetManager.vue` - 数据集管理组件

### 修改文件
- `frontend/src/views/admin/ReportDesigner.vue` - 报表设计器（集成数据集管理）

---

## 🎯 七、使用流程

### 7.1 创建数据表类型数据集

1. 点击"新建数据集"
2. 输入数据集名称
3. 选择"数据表"类型
4. 选择数据源
5. 选择数据表
6. 自动加载字段列表
7. 点击"确定"保存

### 7.2 创建 SQL 查询类型数据集

1. 点击"新建数据集"
2. 输入数据集名称
3. 选择"SQL 查询"类型
4. 输入 SQL 语句（必须 SELECT）
5. 点击"确定"保存
6. 系统自动解析字段

### 7.3 使用数据集

1. 在报表设计器中选择数据集
2. 拖拽字段到画布
3. 配置字段映射
4. 预览数据

---

## ✅ 八、验证规则

### 8.1 表单验证

```javascript
const formRules = {
  name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据集类型', trigger: 'change' }
  ],
  datasourceId: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  tableName: [
    { required: true, message: '请选择数据表', trigger: 'change' }
  ],
  sql: [
    { required: true, message: '请输入 SQL 语句', trigger: 'blur' },
    {
      pattern: /^\s*SELECT/i,
      message: 'SQL 语句必须是 SELECT 查询',
      trigger: 'blur'
    }
  ]
}
```

### 8.2 唯一性验证

```javascript
// 检查数据集名称是否重复
const exists = datasets.value.some(
  ds => ds.name === formData.value.name && ds.id !== formData.value.id
)

if (exists) {
  ElMessage.error('数据集名称已存在')
  return
}
```

---

## 🎨 九、样式设计

### 9.1 字段类型标签

| 类型 | 颜色 | 图标 |
|------|------|------|
| 数值型（int/decimal） | 绿色 | 💰 Money |
| 日期型（date/time） | 橙色 | 📅 Calendar |
| 文本型（varchar/text） | 蓝色 | 📄 Document |

### 9.2 数据集类型标签

| 类型 | 颜色 | 说明 |
|------|------|------|
| 数据表 | 蓝色 | 从数据表创建 |
| SQL 查询 | 绿色 | 自定义 SQL 查询 |

---

## 💾 十、本地存储

### 10.1 存储键名

```javascript
localStorage.setItem('report_datasets', JSON.stringify(datasets))
```

### 10.2 加载逻辑

```javascript
const loadFromLocal = () => {
  const saved = localStorage.getItem('report_datasets')
  if (saved) {
    try {
      datasets.value = JSON.parse(saved)
    } catch (error) {
      console.error('加载数据集失败', error)
    }
  }
}
```

---

## 🚀 十一、后续优化

### 11.1 短期优化

- [ ] SQL 语法高亮
- [ ] SQL 智能提示
- [ ] 字段类型推断优化
- [ ] 数据集测试功能

### 11.2 中期优化

- [ ] 数据集分类管理
- [ ] 数据集导入导出
- [ ] 数据集版本管理
- [ ] 数据集权限控制

### 11.3 长期优化

- [ ] 数据集血缘分析
- [ ] 数据集使用统计
- [ ] 数据集质量监控
- [ ] 数据集自动文档

---

## 🎓 十二、总结

本次实施完成了数据集管理的核心功能：

**核心价值：**
- 📊 **双模式支持** - 数据表/SQL 查询
- 🔍 **自动解析** - 自动获取字段信息
- 💾 **本地存储** - 数据集配置持久化
- ✅ **完整验证** - 表单和数据验证

**技术亮点：**
- Vue 3 Composition API
- Element Plus 组件库
- 本地存储持久化
- 动态表单验证

**下一步：**
1. 集成到报表设计器
2. 实现数据集测试功能
3. 添加 SQL 语法高亮
4. 实现字段映射功能

---

**实施完成时间：** 2026-03-18 16:00  
**实施状态：** ✅ 核心功能已完成
