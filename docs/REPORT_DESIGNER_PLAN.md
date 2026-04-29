# 报表设计器功能完善方案

## 📋 一、功能概述

实现可视化的报表设计器，支持：
1. ✅ **组件拖拉拽** - 从组件面板拖拽图表到画布
2. ✅ **数据源绑定** - 选择数据表并绑定字段
3. ✅ **属性配置** - 配置图表类型、颜色、尺寸等
4. ✅ **实时预览** - 查看图表渲染效果
5. ✅ **保存报表** - 保存报表配置到数据库

---

## 🎨 二、核心功能实现

### 2.1 组件面板（左侧）

**功能：**
- 分类展示图表组件（基础图表、高级图表、表格）
- 支持拖拽（draggable）
- 显示组件预览图标

**组件列表：**
```javascript
const basicCharts = [
  { id: 'bar', name: '柱状图', type: 'bar' },
  { id: 'line', name: '折线图', type: 'line' },
  { id: 'pie', name: '饼图', type: 'pie' },
  { id: 'area', name: '面积图', type: 'area' }
]

const advancedCharts = [
  { id: 'scatter', name: '散点图', type: 'scatter' },
  { id: 'radar', name: '雷达图', type: 'radar' },
  { id: 'gauge', name: '仪表盘', type: 'gauge' }
]

const tableCharts = [
  { id: 'table', name: '明细表', type: 'table' },
  { id: 'pivot', name: '透视表', type: 'pivot' },
  { id: 'card', name: '指标卡', type: 'card' }
]
```

### 2.2 画布区域（中间）

**功能：**
- 接收拖拽的组件
- 支持组件移动（position absolute）
- 支持组件缩放（resize）
- 支持组件选择和高亮
- 支持删除组件

**拖拽事件处理：**
```javascript
// 开始拖拽
const onDragStart = (event, chart) => {
  event.dataTransfer.setData('chart', JSON.stringify(chart))
  event.dataTransfer.effectAllowed = 'copy'
}

// 拖拽经过
const onDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

// 放下组件
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
    width: 300,
    height: 250,
    dataSource: '',
    dimensionField: '',
    measureField: '',
    data: null,
    options: {
      theme: 'blue'
    }
  }
  
  widgets.value.push(widget)
  selectedWidget.value = widget
}
```

### 2.3 属性面板（右侧）

**功能：**
- 显示选中组件的配置项
- 数据源选择
- 维度字段和数值字段绑定
- 颜色和主题配置
- 尺寸调整

**配置项：**
```javascript
{
  title: '组件标题',
  dataSource: '选择数据表',
  dimensionField: '维度字段（X 轴）',
  measureField: '数值字段（Y 轴）',
  theme: '颜色主题',
  height: '图表高度'
}
```

---

## 💾 三、数据源管理

### 3.1 获取数据表列表

**API：** `GET /api/admin/datasources/{id}/metadata`

```javascript
const loadTableList = async () => {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/admin/datasources/1/metadata', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await res.json()
  tableList.value = data.tables || []
}
```

### 3.2 获取表结构

**API：** `GET /api/admin/datasources/{id}/table-schema/{table}`

```javascript
const loadTableSchema = async (tableName) => {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/admin/datasources/1/table-schema/${tableName}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await res.json()
  
  // 转换为字段选项
  tableSchema.value = data.columns.map(col => ({
    key: col.field,
    label: `${col.field} (${col.type})`,
    type: col.type
  }))
}
```

### 3.3 执行查询获取数据

**API：** `POST /api/admin/datasources/{id}/query`

```javascript
const loadWidgetData = async () => {
  if (!selectedWidget.value.dataSource) return
  
  const sql = `SELECT ${selectedWidget.value.dimensionField}, ${selectedWidget.value.measureField} FROM \`${selectedWidget.value.dataSource}\` LIMIT 100`
  
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/admin/datasources/1/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sql })
  })
  const data = await res.json()
  
  if (data.success) {
    selectedWidget.value.data = data.data
  }
}
```

---

## 🎯 四、图表渲染

### 4.1 使用 ECharts 渲染

**安装依赖：**
```bash
npm install echarts vue-echarts
```

**柱状图组件：**
```vue
<template>
  <v-chart class="chart" :option="chartOption" />
</template>

<script setup>
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const props = defineProps(['data', 'options'])

const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: props.data?.map(item => item[props.dimensionField]) || []
  },
  yAxis: { type: 'value' },
  series: [{
    type: 'bar',
    data: props.data?.map(item => item[props.measureField]) || [],
    itemStyle: { color: props.options?.theme === 'blue' ? '#5470c6' : '#91cc75' }
  }]
}))
</script>
```

---

## 💾 五、报表保存

### 5.1 保存报表配置

**API：** `POST /api/admin/reports`

```javascript
const saveReport = async () => {
  if (!reportName.value) {
    ElMessage.warning('请输入报表名称')
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
  
  const token = localStorage.getItem('token')
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

## 🔧 六、增强功能

### 6.1 组件移动

```javascript
const startMoving = (widget, event) => {
  const startX = event.clientX
  const startY = event.clientY
  const startWidgetX = widget.x
  const startWidgetY = widget.y
  
  const onMouseMove = (e) => {
    const dx = e.clientX - startX
    const dy = e.clientY - startY
    widget.x = startWidgetX + dx
    widget.y = startWidgetY + dy
  }
  
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
```

### 6.2 组件缩放

```javascript
const startResizing = (widget, event) => {
  const startX = event.clientX
  const startY = event.clientY
  const startWidth = widget.width
  const startHeight = widget.height
  
  const onMouseMove = (e) => {
    const dx = e.clientX - startX
    const dy = e.clientY - startY
    widget.width = Math.max(200, startWidth + dx)
    widget.height = Math.max(150, startHeight + dy)
  }
  
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
```

### 6.3 字段类型识别

```javascript
const getFieldDataType = (fieldName) => {
  const field = tableSchema.value.find(f => f.key === fieldName)
  if (!field) return 'unknown'
  
  const type = field.type.toLowerCase()
  if (type.includes('int') || type.includes('decimal') || type.includes('float')) {
    return 'numeric'
  } else if (type.includes('date') || type.includes('time')) {
    return 'date'
  } else {
    return 'string'
  }
}

// 自动推荐维度字段和数值字段
const autoRecommendFields = () => {
  const dimensionFields = tableSchema.value.filter(f => 
    getFieldDataType(f.key) === 'string' || getFieldDataType(f.key) === 'date'
  )
  const measureFields = tableSchema.value.filter(f => 
    getFieldDataType(f.key) === 'numeric'
  )
  
  return {
    dimensions: dimensionFields,
    measures: measureFields
  }
}
```

---

## 📁 七、文件结构

```
frontend/src/views/admin/
├── ReportDesigner.vue          # 报表设计器主页面
├── ReportDesigner/
│   ├── components/
│   │   ├── ChartPanel.vue     # 组件面板
│   │   ├── Canvas.vue         # 画布区域
│   │   ├── PropertiesPanel.vue # 属性面板
│   │   └── Charts/
│   │       ├── BarChart.vue   # 柱状图
│   │       ├── LineChart.vue  # 折线图
│   │       ├── PieChart.vue   # 饼图
│   │       └── ...
│   └── composables/
│       ├── useDragDrop.js     # 拖拽逻辑
│       ├── useDataSource.js   # 数据源管理
│       └── useChartRender.js  # 图表渲染
```

---

## ✅ 八、实现步骤

### 阶段 1：基础框架（已完成）
- [x] 三栏布局（组件面板、画布、属性面板）
- [x] 组件列表展示
- [x] 基础拖拽功能

### 阶段 2：数据源绑定（进行中）
- [ ] 获取数据表列表
- [ ] 获取表结构
- [ ] 字段选择器
- [ ] SQL 查询生成

### 阶段 3：图表渲染
- [ ] 集成 ECharts
- [ ] 实现柱状图/折线图/饼图
- [ ] 实时数据更新

### 阶段 4：交互增强
- [ ] 组件移动
- [ ] 组件缩放
- [ ] 组件复制/删除
- [ ] 撤销/重做

### 阶段 5：保存加载
- [ ] 保存报表配置
- [ ] 加载已保存报表
- [ ] 报表预览
- [ ] 报表分享

---

## 🎯 九、核心 API

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/admin/datasources/{id}/metadata` | GET | 获取表列表 |
| `/api/admin/datasources/{id}/table-schema/{table}` | GET | 获取表结构 |
| `/api/admin/datasources/{id}/query` | POST | 执行 SQL 查询 |
| `/api/admin/reports` | POST | 保存报表 |
| `/api/admin/reports/{id}` | GET | 获取报表详情 |
| `/api/admin/reports/{id}` | PUT | 更新报表 |
| `/api/admin/reports/{id}` | DELETE | 删除报表 |

---

## 🎨 十、UI/UX 设计

### 10.1 拖拽反馈
- 拖拽时显示组件预览
- 画布显示放置区域高亮
- 放下时动画效果

### 10.2 组件选择
- 选中组件显示蓝色边框
- 显示调整大小的控制点
- 显示移动手柄

### 10.3 数据绑定
- 字段类型图标（数字/文本/日期）
- 智能推荐字段
- 字段搜索过滤

---

**实施时间：** 2026-03-18  
**状态：** 🚧 开发中
