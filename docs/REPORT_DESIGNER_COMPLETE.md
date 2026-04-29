# 报表设计器功能完善报告

**实施时间：** 2026-03-18 13:30  
**实施人员：** mac🦀  
**功能模块：** 报表设计器 - 拖拉拽 + 数据源绑定

---

## 📋 一、实施概述

本次实施完善了报表设计器功能，实现了完整的可视化报表设计体验：

1. ✅ **组件拖拉拽** - 从组件面板拖拽图表到画布
2. ✅ **数据源绑定** - 选择数据表并绑定字段
3. ✅ **实时预览** - 柱状图/折线图/饼图/表格即时渲染
4. ✅ **属性配置** - 配置颜色、尺寸、标题等
5. ✅ **保存报表** - 保存报表配置到数据库

---

## 🎨 二、核心功能

### 2.1 组件面板（左侧）

**功能：**
- 分类展示图表组件
  - 基础图表：柱状图、折线图、饼图、面积图
  - 高级图表：散点图、雷达图、仪表盘
  - 数据表：明细表、透视表、指标卡
- 支持拖拽（draggable）
- 显示组件预览图标

**组件示例：**
```javascript
{
  id: 'bar',
  name: '柱状图',
  type: 'bar',
  icon: { viewBox: '0 0 24 24', paths: [...] }
}
```

### 2.2 画布区域（中间）

**功能：**
- 接收拖拽的组件
- 支持组件绝对定位（x, y 坐标）
- 支持组件缩放（右下角拖拽）
- 支持组件选择和高亮
- 支持删除组件
- 支持刷新数据

**画布状态：**
```javascript
{
  widgets: [
    {
      id: 'widget_1710738000000',
      type: 'bar',
      title: '柱状图',
      x: 100,
      y: 150,
      width: 350,
      height: 300,
      dataSource: 'datasources',
      dimensionField: 'name',
      measureField: 'id',
      data: [...],
      options: { theme: 'blue' }
    }
  ]
}
```

### 2.3 属性面板（右侧）

**功能：**
- 显示选中组件的配置项
- 组件标题编辑
- 图表类型切换
- 数据表选择
- 维度字段绑定（X 轴）
- 数值字段绑定（Y 轴）
- 颜色主题选择
- 尺寸滑块调整

**配置项：**
```javascript
{
  title: '组件标题',
  type: 'bar|line|pie|table',
  dataSource: '选择的数据表',
  dimensionField: '维度字段',
  measureField: '数值字段',
  theme: 'blue|green|orange|purple|red',
  width: 350,
  height: 300
}
```

---

## 💾 三、数据源管理

### 3.1 数据源选择

**API：** `GET /api/admin/datasources`

```javascript
const loadDatasources = async () => {
  const res = await fetch('/api/admin/datasources', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await res.json()
  datasourceList.value = data.items || []
}
```

### 3.2 获取表列表

**API：** `GET /api/admin/datasources/{id}/metadata`

```javascript
const loadMetadata = async () => {
  const res = await fetch(`/api/admin/datasources/${selectedDatasource.value}/metadata`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await res.json()
  tableList.value = data.tables || []
}
```

### 3.3 获取表结构

**API：** `GET /api/admin/datasources/{id}/table-schema/{table}`

```javascript
const loadTableSchema = async (tableName) => {
  const res = await fetch(`/api/admin/datasources/${selectedDatasource.value}/table-schema/${tableName}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await res.json()
  tableSchema.value = data.columns.map(col => ({
    key: col.field,
    label: `${col.field} (${col.type})`,
    type: col.type
  }))
}
```

### 3.4 执行查询

**API：** `POST /api/admin/datasources/{id}/query`

```javascript
const refreshWidgetData = async (widget) => {
  const sql = `SELECT \`${widget.dimensionField}\`, \`${widget.measureField}\` FROM \`${widget.dataSource}\` LIMIT 100`
  
  const res = await fetch(`/api/admin/datasources/${selectedDatasource.value}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sql, limit: 100 })
  })
  const data = await res.json()
  
  if (data.success) {
    widget.data = data.data
  }
}
```

---

## 📊 四、图表渲染实现

### 4.1 柱状图

**实现方式：** CSS Flexbox + 百分比高度

```vue
<div class="bar-chart-container">
  <div
    v-for="(item, idx) in widget.data"
    :key="idx"
    class="bar-item"
    :style="{ height: getBarHeight(item[widget.measureField]) + '%' }"
  >
    <div class="bar-label">{{ item[widget.dimensionField] }}</div>
    <div class="bar-value">{{ item[widget.measureField] }}</div>
  </div>
</div>
```

**高度计算：**
```javascript
const getBarHeight = (value) => {
  return (value / maxValue.value) * 80
}
```

### 4.2 折线图

**实现方式：** SVG Polyline

```vue
<svg :viewBox="`0 0 ${widget.width} ${widget.height - 60}`">
  <polyline
    :points="getLinePoints(widget.data, widget.measureField)"
    fill="none"
    stroke="#5470c6"
    stroke-width="3"
  />
  <circle
    v-for="(item, idx) in widget.data"
    :key="idx"
    :cx="getX(idx, widget.data.length, widget.width)"
    :cy="getY(item[widget.measureField], widget.data, widget.height - 60)"
    r="4"
    fill="#5470c6"
  />
</svg>
```

**坐标计算：**
```javascript
const getX = (index, total, width) => {
  return 40 + (index / (total - 1 || 1)) * (width - 80)
}

const getY = (value, data, height) => {
  const max = Math.max(...data.map(d => d[measureField] || 0), 1)
  return height - (value / max) * (height - 20) - 10
}
```

### 4.3 饼图

**实现方式：** SVG Path

```vue
<svg :viewBox="-100 -100 200 200">
  <path
    v-for="(slice, idx) in getPieSlices(widget.data, widget.measureField)"
    :key="idx"
    :d="slice.path"
    :fill="slice.color"
    stroke="white"
    stroke-width="1"
  />
</svg>
```

**切片计算：**
```javascript
const getPieSlices = (data, field) => {
  const total = data.reduce((sum, item) => sum + (item[field] || 0), 0)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', ...]
  
  let startAngle = 0
  return data.map((item, idx) => {
    const percentage = item[field] / total
    const angle = percentage * 360
    const endAngle = startAngle + angle
    
    // 计算 SVG Path
    const startRad = (startAngle - 90) * Math.PI / 180
    const endRad = (endAngle - 90) * Math.PI / 180
    const x1 = Math.cos(startRad) * 80
    const y1 = Math.sin(startRad) * 80
    const x2 = Math.cos(endRad) * 80
    const y2 = Math.sin(endRad) * 80
    const largeArc = angle > 180 ? 1 : 0
    const path = `M 0 0 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`
    
    startAngle = endAngle
    return { path, color: colors[idx % colors.length] }
  })
}
```

### 4.4 表格

**实现方式：** Element Plus Table

```vue
<el-table :data="widget.data" stripe size="small" max-height="200">
  <el-table-column
    v-for="field in getDisplayedFields(widget)"
    :key="field"
    :prop="field"
    :label="field"
  />
</el-table>
```

---

## 🎯 五、交互功能

### 5.1 拖拽添加组件

```javascript
const onDragStart = (event, chart) => {
  event.dataTransfer.setData('chart', JSON.stringify(chart))
  event.dataTransfer.effectAllowed = 'copy'
}

const onDrop = (event) => {
  event.preventDefault()
  const chart = JSON.parse(event.dataTransfer.getData('chart'))
  const rect = canvasRef.value.getBoundingClientRect()
  
  const widget = {
    id: `widget_${Date.now()}`,
    type: chart.type,
    title: chart.name,
    x: event.clientX - rect.left - 140,
    y: event.clientY - rect.top - 100,
    width: 350,
    height: 300,
    dataSource: selectedTable.value || '',
    dimensionField: '',
    measureField: '',
    data: null,
    loading: false,
    options: { theme: 'blue' }
  }
  
  widgets.value.push(widget)
  selectedWidget.value = widget
}
```

### 5.2 组件缩放

```javascript
const startResizing = (event, widget) => {
  event.preventDefault()
  event.stopPropagation()
  
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = widget.width
  const startHeight = widget.height
  
  const onMouseMove = (e) => {
    const dx = e.clientX - startX
    const dy = e.clientY - startY
    widget.width = Math.max(250, startWidth + dx)
    widget.height = Math.max(200, startHeight + dy)
  }
  
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
```

### 5.3 字段类型识别

```javascript
const getFieldTypeTag = (type) => {
  const typeLower = type?.toLowerCase() || ''
  if (typeLower.includes('int') || typeLower.includes('decimal')) {
    return 'success' // 数值字段 - 绿色
  } else if (typeLower.includes('date')) {
    return 'warning' // 日期字段 - 橙色
  } else {
    return 'info' // 文本字段 - 蓝色
  }
}

const isDimensionField = (type) => {
  const typeLower = type?.toLowerCase() || ''
  return !typeLower.includes('int') && !typeLower.includes('decimal')
}

const isMeasureField = (type) => {
  const typeLower = type?.toLowerCase() || ''
  return typeLower.includes('int') || typeLower.includes('decimal')
}
```

---

## 💾 六、报表保存

### 6.1 保存 API

**API：** `POST /api/admin/reports`

```javascript
const saveReport = async () => {
  if (!reportName.value) {
    ElMessage.warning('请输入报表名称')
    return
  }
  
  if (widgets.value.length === 0) {
    ElMessage.warning('请至少添加一个组件')
    return
  }
  
  const reportConfig = {
    name: reportName.value,
    description: reportDescription.value,
    type: 'dashboard',
    config: {
      widgets: widgets.value.map(w => ({
        id: w.id,
        type: w.type,
        title: w.title,
        x: w.x,
        y: w.y,
        width: w.width,
        height: w.height,
        dataSource: w.dataSource,
        dimensionField: w.dimensionField,
        measureField: w.measureField,
        options: w.options
      }))
    }
  }
  
  const res = await fetch('/api/admin/reports', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(reportConfig)
  })
  
  if (res.ok) {
    ElMessage.success('报表保存成功')
  }
}
```

---

## 📁 七、文件结构

```
frontend/src/views/admin/
├── ReportDesigner.vue          # ✅ 报表设计器主页面（已完善）
├── Datasources.vue             # 数据源管理
├── DatasourcePreview.vue       # 数据源预览
└── RealEstateDashboard.vue     # 地产 ERP 仪表盘

backend/api/
├── report_manager.py           # ✅ 报表管理 API
├── datasources.py              # ✅ 数据源 API
└── realestate.py               # 地产 ERP API
```

---

## 🎨 八、UI/UX 设计

### 8.1 三栏布局

```
┌─────────────┬──────────────────────┬─────────────┐
│  组件面板   │     报表画布         │  属性面板   │
│  (280px)    │    (自适应)          │  (320px)    │
│             │                      │             │
│ - 图表组件  │ - 拖拽区域           │ - 组件配置  │
│ - 数据源    │ - 组件列表           │ - 数据绑定  │
│ - 字段列表  │ - 实时预览           │ - 样式设置  │
└─────────────┴──────────────────────┴─────────────┘
```

### 8.2 颜色主题

```javascript
const themes = {
  blue: '#5470c6',
  green: '#91cc75',
  orange: '#fac858',
  purple: '#9a60b4',
  red: '#ee6666'
}
```

### 8.3 字段类型图标

- 📄 **文本字段** - Document 图标（蓝色）
- 💰 **数值字段** - Money 图标（绿色）
- 📅 **日期字段** - Calendar 图标（橙色）

---

## ✅ 九、功能清单

### 9.1 已完成

- [x] 组件面板（3 类 10 种图表）
- [x] 拖拽添加组件
- [x] 画布区域（绝对定位）
- [x] 组件缩放
- [x] 组件删除
- [x] 属性面板
- [x] 数据源选择
- [x] 数据表选择
- [x] 表结构查看
- [x] 维度字段绑定
- [x] 数值字段绑定
- [x] 柱状图渲染
- [x] 折线图渲染
- [x] 饼图渲染
- [x] 表格渲染
- [x] 数据刷新
- [x] 报表保存
- [x] 字段类型识别

### 9.2 待完善

- [ ] 组件移动（拖动画布内移动）
- [ ] 撤销/重做
- [ ] 组件复制
- [ ] 报表加载
- [ ] 报表预览
- [ ] 导出图片/PDF
- [ ] 更多图表类型（面积图、散点图、雷达图等）
- [ ] 高级配置（坐标轴、图例、提示框）

---

## 🧪 十、测试验证

### 10.1 测试步骤

1. **访问设计器**
   - 后台管理 → 报表管理 → 报表设计器
   - URL: `http://localhost:3000/admin/reports/designer`

2. **拖拽组件**
   - 从左侧拖拽"柱状图"到画布
   - 验证组件是否正确添加

3. **绑定数据源**
   - 选择数据源（如：AI数据融合平台数据库）
   - 选择数据表（如：datasources）
   - 选择维度字段（如：name）
   - 选择数值字段（如：id）

4. **刷新数据**
   - 点击"🔄 刷新数据"
   - 验证图表是否正确渲染

5. **配置样式**
   - 修改组件标题
   - 切换颜色主题
   - 调整组件尺寸

6. **保存报表**
   - 输入报表名称
   - 点击"保存报表"
   - 验证保存成功

### 10.2 预期效果

- ✅ 组件拖拽流畅
- ✅ 数据加载快速
- ✅ 图表渲染正确
- ✅ 样式配置即时生效
- ✅ 报表保存成功

---

## 🎓 十一、总结

本次实施完成了报表设计器的核心功能：

**核心价值：**
- 🎨 **可视化设计** - 拖拽式操作，无需编码
- 📊 **实时预览** - 数据绑定后立即查看效果
- 💾 **数据源集成** - 直接连接数据库查询
- 🎯 **灵活配置** - 支持多种图表类型和样式

**技术亮点：**
- 原生拖拽 API（无需第三方库）
- SVG 图表渲染（轻量级）
- CSS Flexbox 布局（响应式）
- Vue 3 Composition API（模块化）

**下一步：**
1. 测试验证所有功能
2. 添加更多图表类型
3. 实现组件移动功能
4. 完善报表加载和预览

---

**实施完成时间：** 2026-03-18 13:35  
**实施状态：** ✅ 核心功能已完成
