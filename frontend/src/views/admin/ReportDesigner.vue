<template>
  <div class="report-designer-page">
    <el-container class="page-container">
      <!-- 左侧：图表组件面板 -->
      <el-aside width="280px" class="components-panel">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><DataAnalysis /></el-icon>
                图表组件
              </span>
            </div>
          </template>

          <el-tabs v-model="activeTab" class="components-tabs">
            <el-tab-pane label="基础图表" name="basic">
              <div
                v-for="chart in basicCharts"
                :key="chart.id"
                class="chart-item"
                draggable
                @dragstart="onDragStart($event, chart)"
              >
                <div class="chart-preview">
                  <div class="chart-icon">
                    <el-icon :size="20"><component :is="chart.icon" /></el-icon>
                  </div>
                  <span class="chart-name">{{ chart.name }}</span>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="高级图表" name="advanced">
              <div
                v-for="chart in advancedCharts"
                :key="chart.id"
                class="chart-item"
                draggable
                @dragstart="onDragStart($event, chart)"
              >
                <div class="chart-preview">
                  <div class="chart-icon">
                    <el-icon :size="20"><component :is="chart.icon" /></el-icon>
                  </div>
                  <span class="chart-name">{{ chart.name }}</span>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="数据表" name="table">
              <div
                v-for="chart in tableCharts"
                :key="chart.id"
                class="chart-item"
                draggable
                @dragstart="onDragStart($event, chart)"
              >
                <div class="chart-preview">
                  <div class="chart-icon">
                    <el-icon :size="20"><component :is="chart.icon" /></el-icon>
                  </div>
                  <span class="chart-name">{{ chart.name }}</span>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 数据集面板 -->
        <el-card class="panel-card" style="margin-top: 16px;">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><DataLine /></el-icon>
                数据集
              </span>
              <el-button size="small" type="primary" @click="showAddDataset" circle>
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </template>

          <el-collapse v-model="activeDatasets" accordion>
            <el-collapse-item
              v-for="ds in datasets"
              :key="ds.id"
              :name="ds.id"
            >
              <template #title>
                <div class="dataset-title">
                  <el-icon><DataLine /></el-icon>
                  <span class="dataset-name">{{ ds.name }}</span>
                  <el-tag size="small" :type="ds.type === 'sql' ? 'success' : 'info'">
                    {{ ds.type === 'sql' ? 'SQL' : '表' }}
                  </el-tag>
                </div>
              </template>
              
              <div class="dataset-content">
                <div class="dataset-info">
                  <div class="info-row">
                    <span class="label">类型：</span>
                    <span class="value">{{ ds.type === 'sql' ? 'SQL 查询' : '数据表' }}</span>
                  </div>
                  <div class="info-row" v-if="ds.type === 'table'">
                    <span class="label">表名：</span>
                    <span class="value">{{ ds.tableName }}</span>
                  </div>
                  <div class="info-row" v-if="ds.type === 'sql'">
                    <span class="label">SQL：</span>
                    <span class="value sql-preview">{{ ds.sql?.substring(0, 50) }}...</span>
                  </div>
                </div>
                
                <div class="dataset-fields" v-if="ds.fields && ds.fields.length > 0">
                  <div class="field-label">字段（{{ ds.fields.length }}）：</div>
                  <el-tag
                    v-for="field in ds.fields"
                    :key="field.name"
                    size="small"
                    style="margin: 2px;"
                  >
                    <el-icon style="vertical-align: middle; margin-right: 2px;">
                      <component :is="getFieldTypeIcon(field.type)" />
                    </el-icon>
                    {{ field.name }}
                  </el-tag>
                </div>
                
                <div class="dataset-actions">
                  <el-button size="mini" @click.stop="editDataset(ds)">编辑</el-button>
                  <el-button size="mini" type="danger" @click.stop="deleteDataset(ds.id)">删除</el-button>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
          
          <el-empty v-if="datasets.length === 0" description="暂无数据集" :image-size="60">
            <el-button type="primary" size="small" @click="showAddDataset">新建数据集</el-button>
          </el-empty>
        </el-card>

        <!-- 数据源面板 -->
        <el-card class="panel-card" style="margin-top: 16px;">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><DataLine /></el-icon>
                数据源
              </span>
            </div>
          </template>

          <el-form size="small" label-position="top">
            <el-form-item label="选择数据源">
              <el-select v-model="selectedDatasource" placeholder="请选择数据源" @change="loadMetadata" style="width: 100%;">
                <el-option
                  v-for="ds in datasourceList"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="选择数据表" v-if="tableList.length > 0">
              <el-select v-model="selectedTable" placeholder="请选择数据表" @change="loadTableSchema" style="width: 100%;">
                <el-option v-for="table in tableList" :key="table" :label="table" :value="table" />
              </el-select>
            </el-form-item>

            <el-form-item label="可用字段" v-if="tableSchema.length > 0">
              <div class="field-list">
                <el-tag
                  v-for="field in tableSchema"
                  :key="field.key"
                  size="small"
                  :type="getFieldTypeTag(field.type)"
                  style="margin: 4px;"
                  effect="plain"
                >
                  <el-icon style="vertical-align: middle; margin-right: 4px;">
                    <component :is="getFieldTypeIcon(field.type)" />
                  </el-icon>
                  {{ field.key }}
                </el-tag>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-aside>

      <!-- 中间：报表画布 -->
      <el-main class="canvas-area">
        <div class="canvas-header">
          <div class="report-controls">
            <el-button type="primary" @click="saveReport" :loading="saving">
              <el-icon><Document /></el-icon>
              保存
            </el-button>
            <el-button type="success" @click="() => saveReport(true)" :loading="saving">
              <el-icon><View /></el-icon>
              保存并发布
            </el-button>
            <el-button @click="openReportDialog">
              <el-icon><Document /></el-icon>
              打开
            </el-button>
            <el-button @click="previewReport">
              <el-icon><View /></el-icon>
              预览
            </el-button>
            <el-button @click="clearCanvas">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>

          <div class="report-info">
            <el-input v-model="reportName" placeholder="报表名称" size="default" style="width: 200px; margin-right: 12px;" />
            <el-input v-model="reportDescription" placeholder="报表描述" size="default" style="width: 300px;" />
          </div>
        </div>

        <!-- 画布容器 -->
        <div
          ref="canvasRef"
          class="canvas-container"
          @dragover="onDragOver"
          @drop="onDrop"
          @click="onCanvasClick"
        >
          <div v-if="widgets.length === 0" class="canvas-empty">
            <el-empty description="从左侧拖拽组件到画布开始设计报表" />
          </div>

          <div
            v-for="widget in widgets"
            :key="widget.id"
            class="widget"
            :class="{ active: selectedWidget?.id === widget.id }"
            :style="{ left: widget.x + 'px', top: widget.y + 'px', width: widget.width + 'px', height: widget.height + 'px' }"
            @click.stop="selectWidget(widget)"
          >
            <div class="widget-header" @mousedown="startMoving($event, widget)">
              <div class="widget-title-section">
                <el-icon class="widget-icon">
                  <Histogram v-if="widget.type === 'bar'" />
                  <TrendCharts v-else-if="widget.type === 'line'" />
                  <PieChart v-else-if="widget.type === 'pie'" />
                  <DataAnalysis v-else-if="widget.type === 'table'" />
                </el-icon>
                <span class="widget-title">{{ widget.title }}</span>
              </div>
              <div class="widget-actions">
                <el-button size="small" circle @click.stop="refreshWidgetData(widget)" title="刷新数据">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button size="small" circle @click.stop="removeWidget(widget.id)" title="删除">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <div class="widget-content">
              <div class="chart-placeholder" v-if="!widget.data && !widget.loading">
                <el-empty :description="widget.dataSource ? '点击刷新数据' : '请配置数据源'" :image-size="60" />
                <el-button v-if="widget.dataSource" type="primary" size="small" @click.stop="refreshWidgetData(widget)">加载数据</el-button>
              </div>

              <div v-else-if="widget.loading" class="chart-loading">
                <el-loading-spinner />
                <p>加载中...</p>
              </div>

              <div v-else class="chart-container">
                <!-- 柱状图 -->
                <div v-if="widget.type === 'bar'" class="bar-chart" ref="chartRefs">
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
                </div>

                <!-- 折线图 -->
                <div v-else-if="widget.type === 'line'" class="line-chart" ref="chartRefs">
                  <svg class="line-chart-svg" :viewBox="'0 0 ' + widget.width + ' ' + (widget.height - 60)">
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
                </div>

                <!-- 饼图 -->
                <div v-else-if="widget.type === 'pie'" class="pie-chart" ref="chartRefs">
                  <svg :viewBox="'-100 -100 200 200'">
                    <path
                      v-for="(slice, idx) in getPieSlices(widget.data, widget.measureField)"
                      :key="idx"
                      :d="slice.path"
                      :fill="slice.color"
                      stroke="white"
                      stroke-width="1"
                    />
                  </svg>
                </div>

                <!-- 表格 -->
                <div v-else-if="widget.type === 'table'" class="table-chart">
                  <el-table :data="widget.data" stripe size="small" max-height="200">
                    <el-table-column
                      v-for="field in getDisplayedFields(widget)"
                      :key="field"
                      :prop="field"
                      :label="field"
                    />
                  </el-table>
                </div>
              </div>
            </div>

            <!-- 调整大小手柄 -->
            <div class="widget-resizer" @mousedown="startResizing($event, widget)"></div>
          </div>
        </div>
      </el-main>

      <!-- 右侧：属性面板 -->
      <el-aside width="320px" class="properties-panel">
        <el-card class="panel-card" v-if="selectedWidget">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><EditPen /></el-icon>
                组件配置
              </span>
              <el-button size="small" @click="selectedWidget = null" circle>
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>

          <el-form size="small" label-position="top">
            <el-form-item label="组件标题">
              <el-input v-model="selectedWidget.title" placeholder="输入标题" />
            </el-form-item>

            <el-form-item label="图表类型">
              <el-select v-model="selectedWidget.type" placeholder="选择类型" @change="onChartTypeChange" style="width: 100%;">
                <el-option label="柱状图" value="bar" />
                <el-option label="折线图" value="line" />
                <el-option label="饼图" value="pie" />
                <el-option label="表格" value="table" />
              </el-select>
            </el-form-item>

            <el-divider>数据配置</el-divider>

            <el-form-item label="选择数据表">
              <el-select v-model="selectedWidget.dataSource" placeholder="选择数据表" @change="onDataSourceChange" style="width: 100%;">
                <el-option v-for="table in tableList" :key="table" :label="table" :value="table" />
              </el-select>
            </el-form-item>

            <el-form-item label="维度字段 (X 轴)" v-if="selectedWidget.dataSource && tableSchema.length > 0">
              <el-select v-model="selectedWidget.dimensionField" placeholder="选择维度字段" style="width: 100%;">
                <el-option
                  v-for="field in tableSchema.filter(f => isDimensionField(f.type))"
                  :key="field.key"
                  :label="`${field.key} (${field.type})`"
                  :value="field.key"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="数值字段 (Y 轴)" v-if="selectedWidget.dataSource && tableSchema.length > 0">
              <el-select v-model="selectedWidget.measureField" placeholder="选择数值字段" style="width: 100%;">
                <el-option
                  v-for="field in tableSchema.filter(f => isMeasureField(f.type))"
                  :key="field.key"
                  :label="`${field.key} (${field.type})`"
                  :value="field.key"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="颜色主题" v-if="selectedWidget.type !== 'table'">
              <el-select v-model="selectedWidget.options.theme" placeholder="选择主题" style="width: 100%;">
                <el-option label="蓝色" value="blue" />
                <el-option label="绿色" value="green" />
                <el-option label="橙色" value="orange" />
                <el-option label="紫色" value="purple" />
                <el-option label="红色" value="red" />
              </el-select>
            </el-form-item>

            <el-divider>样式配置</el-divider>

            <el-form-item label="宽度：{{ selectedWidget.width }}px">
              <el-slider v-model="selectedWidget.width" :min="250" :max="800" :step="10" />
            </el-form-item>

            <el-form-item label="高度：{{ selectedWidget.height }}px">
              <el-slider v-model="selectedWidget.height" :min="200" :max="600" :step="10" />
            </el-form-item>
          </el-form>

          <el-divider />

          <el-button type="primary" size="small" @click="refreshWidgetData(selectedWidget)" style="width: 100%;">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </el-card>

        <el-card class="panel-card" v-else>
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><DataAnalysis /></el-icon>
                报表统计
              </span>
            </div>
          </template>

          <div class="stats-info">
            <div class="stat-item">
              <div class="stat-number">{{ widgets.length }}</div>
              <div class="stat-label">组件数量</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ tableList.length }}</div>
              <div class="stat-label">数据表</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ tableSchema.length }}</div>
              <div class="stat-label">字段数</div>
            </div>
          </div>

          <el-divider />

          <div class="quick-tips">
            <el-alert
              title="使用提示"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                <ol style="padding-left: 20px; margin: 8px 0;">
                  <li>从左侧拖拽组件到画布</li>
                  <li>选择数据表并绑定字段</li>
                  <li>在右侧配置样式和颜色</li>
                  <li>点击刷新数据查看效果</li>
                  <li>保存报表以便后续使用</li>
                </ol>
              </template>
            </el-alert>
          </div>
        </el-card>
      </el-aside>
    </el-container>

    <!-- 报表列表对话框 -->
    <el-dialog v-model="reportListDialogVisible" title="打开报表" width="800px">
      <el-table :data="reportList" stripe border v-loading="loadingReports">
        <el-table-column prop="report_name" label="报表名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="report_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.report_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'published' ? 'success' : 'info'">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="loadReport(row)">打开</el-button>
            <el-button size="small" type="success" @click="publishReportById(row)" v-if="row.status !== 'published'">发布</el-button>
            <el-button size="small" type="danger" @click="deleteReportById(row.report_id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, DataAnalysis, DataLine, Refresh, Delete, EditPen, View, Histogram, TrendCharts, PieChart } from '@element-plus/icons-vue'

// 图表组件定义
const basicCharts = [
  { id: 'bar', name: '柱状图', type: 'bar', icon: 'Histogram' },
  { id: 'line', name: '折线图', type: 'line', icon: 'TrendCharts' },
  { id: 'pie', name: '饼图', type: 'pie', icon: 'PieChart' },
  { id: 'area', name: '面积图', type: 'area', icon: 'ScaleToOriginal' }
]

const advancedCharts = [
  { id: 'scatter', name: '散点图', type: 'scatter', icon: 'Operation' },
  { id: 'radar', name: '雷达图', type: 'radar', icon: 'Aim' },
  { id: 'gauge', name: '仪表盘', type: 'gauge', icon: 'Timer' }
]

const tableCharts = [
  { id: 'table', name: '明细表', type: 'table', icon: 'Grid' },
  { id: 'pivot', name: '透视表', type: 'pivot', icon: 'Histogram' },
  { id: 'card', name: '指标卡', type: 'card', icon: 'DataBoard' }
]

// 状态变量
const activeTab = ref('basic')
const canvasRef = ref(null)
const selectedWidget = ref(null)
const selectedDatasource = ref(null)
const selectedTable = ref(null)
const reportName = ref('')
const reportDescription = ref('')
const saving = ref(false)
const savedReportId = ref(null)
const reportListDialogVisible = ref(false)
const reportList = ref([])
const loadingReports = ref(false)

// 数据集管理
const datasets = ref([])
const datasetDialogVisible = ref(false)
const currentDataset = ref({
  id: '',
  name: '',
  type: 'table', // table | sql
  datasourceId: '',
  tableName: '',
  sql: '',
  fields: []
})

// 数据
const datasourceList = ref([])
const tableList = ref([])
const tableSchema = ref([])
const widgets = ref([])
const chartRefs = ref([])

// 拖拽开始
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
    width: 350,
    height: 300,
    dataSource: selectedTable.value || '',
    dimensionField: '',
    measureField: '',
    data: null,
    loading: false,
    options: {
      theme: 'blue'
    }
  }
  
  widgets.value.push(widget)
  selectedWidget.value = widget
  ElMessage.success(`已添加${chart.name}组件`)
}

// 画布点击
const onCanvasClick = () => {
  selectedWidget.value = null
}

// 选择组件
const selectWidget = (widget) => {
  selectedWidget.value = widget
}

// 删除组件
const removeWidget = (id) => {
  ElMessageBox.confirm('确定要删除该组件吗？', '提示', {
    type: 'warning'
  }).then(() => {
    const idx = widgets.value.findIndex(w => w.id === id)
    if (idx > -1) {
      widgets.value.splice(idx, 1)
      if (selectedWidget.value?.id === id) {
        selectedWidget.value = null
      }
      ElMessage.success('删除成功')
    }
  })
}

// 清空画布
const clearCanvas = () => {
  ElMessageBox.confirm('确定要清空画布吗？', '警告', {
    type: 'warning',
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    widgets.value = []
    selectedWidget.value = null
    ElMessage.success('画布已清空')
  })
}

// 移动组件
const startMoving = (event, widget) => {
  event.preventDefault()
  event.stopPropagation()
  
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

// 调整大小
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

// 加载数据源列表
const loadDatasources = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/admin/datasources', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    datasourceList.value = data.items || []
    
    // 默认选择第一个
    if (datasourceList.value.length > 0) {
      selectedDatasource.value = datasourceList.value[0].id
      loadMetadata()
    }
  } catch (error) {
    console.error('加载数据源失败', error)
  }
}

// 加载元数据（表列表）
const loadMetadata = async () => {
  if (!selectedDatasource.value) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${selectedDatasource.value}/metadata`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      tableList.value = data.tables || []
      ElMessage.success(`加载 ${tableList.value.length} 个表`)
    } else {
      ElMessage.error(data.detail || '加载元数据失败')
    }
  } catch (error) {
    ElMessage.error('加载元数据失败')
  }
}

// 加载表结构
const loadTableSchema = async (tableName) => {
  if (!tableName) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${selectedDatasource.value}/table-schema/${tableName}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      tableSchema.value = data.columns || []
      
      // 如果当前选中的组件数据源为空，自动填充
      if (selectedWidget.value && !selectedWidget.value.dataSource) {
        selectedWidget.value.dataSource = tableName
      }
    }
  } catch (error) {
    console.error('加载表结构失败', error)
  }
}

// 获取字段类型标签
const getFieldTypeTag = (type) => {
  const typeLower = type?.toLowerCase() || ''
  if (typeLower.includes('int') || typeLower.includes('decimal') || typeLower.includes('float') || typeLower.includes('number')) {
    return 'success'
  } else if (typeLower.includes('date') || typeLower.includes('time')) {
    return 'warning'
  } else {
    return 'info'
  }
}

// 获取字段类型图标
const getFieldTypeIcon = (type) => {
  const typeLower = type?.toLowerCase() || ''
  if (typeLower.includes('int') || typeLower.includes('decimal') || typeLower.includes('float')) {
    return 'Money'
  } else if (typeLower.includes('date')) {
    return 'Calendar'
  } else {
    return 'Document'
  }
}

// 判断是否为维度字段
const isDimensionField = (type) => {
  const typeLower = type?.toLowerCase() || ''
  return !typeLower.includes('int') && !typeLower.includes('decimal') && !typeLower.includes('float')
}

// 判断是否为数值字段
const isMeasureField = (type) => {
  const typeLower = type?.toLowerCase() || ''
  return typeLower.includes('int') || typeLower.includes('decimal') || typeLower.includes('float')
}

// 数据源变化
const onDataSourceChange = () => {
  if (selectedWidget.value?.dataSource) {
    loadTableSchema(selectedWidget.value.dataSource)
  }
}

// 图表类型变化
const onChartTypeChange = () => {
  ElMessage.success('图表类型已切换')
}

// 刷新组件数据
const refreshWidgetData = async (widget) => {
  if (!widget.dataSource || !widget.dimensionField || !widget.measureField) {
    ElMessage.warning('请先配置数据源和字段')
    return
  }
  
  widget.loading = true
  
  try {
    const token = localStorage.getItem('token')
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
      ElMessage.success('数据加载成功')
    } else {
      ElMessage.error(data.error || '查询失败')
    }
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  } finally {
    widget.loading = false
  }
}

// 柱状图高度计算
const maxValue = computed(() => {
  if (!selectedWidget.value?.data) return 100
  const values = selectedWidget.value.data.map(item => item[selectedWidget.value.measureField] || 0)
  return Math.max(...values, 1)
})

const getBarHeight = (value) => {
  return (value / maxValue.value) * 80
}

// 折线图坐标计算
const getX = (index, total, width) => {
  return 40 + (index / (total - 1 || 1)) * (width - 80)
}

const getY = (value, data, height) => {
  const max = Math.max(...data.map(d => d[selectedWidget.value?.measureField] || 0), 1)
  return height - (value / max) * (height - 20) - 10
}

const getLinePoints = (data, field) => {
  if (!data || data.length === 0) return ''
  const width = selectedWidget.value?.width || 350
  const height = (selectedWidget.value?.height || 300) - 60
  return data.map((item, idx) => {
    const x = getX(idx, data.length, width)
    const y = getY(item[field], data, height)
    return `${x},${y}`
  }).join(' ')
}

// 饼图切片计算
const getPieSlices = (data, field) => {
  if (!data || data.length === 0) return []
  
  const total = data.reduce((sum, item) => sum + (item[field] || 0), 0)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
  
  let startAngle = 0
  return data.map((item, idx) => {
    const value = item[field] || 0
    const percentage = value / total
    const angle = percentage * 360
    const endAngle = startAngle + angle
    
    const startRad = (startAngle - 90) * Math.PI / 180
    const endRad = (endAngle - 90) * Math.PI / 180
    
    const x1 = Math.cos(startRad) * 80
    const y1 = Math.sin(startRad) * 80
    const x2 = Math.cos(endRad) * 80
    const y2 = Math.sin(endRad) * 80
    
    const largeArc = angle > 180 ? 1 : 0
    
    const path = `M 0 0 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`
    
    startAngle = endAngle
    
    return {
      path,
      color: colors[idx % colors.length]
    }
  })
}

// 表格显示字段
const getDisplayedFields = (widget) => {
  if (!widget.data || widget.data.length === 0) return []
  return Object.keys(widget.data[0])
}

// 保存报表
const saveReport = async (publish = false) => {
  if (!reportName.value) {
    ElMessage.warning('请输入报表名称')
    return
  }
  
  if (widgets.value.length === 0) {
    ElMessage.warning('请至少添加一个组件')
    return
  }
  
  saving.value = true
  
  try {
    const token = localStorage.getItem('token')
    const reportConfig = {
      name: reportName.value,
      description: reportDescription.value,
      type: 'dashboard',
      status: publish ? 'published' : 'draft',
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
      const result = await res.json()
      if (publish) {
        ElMessage.success('报表已保存并发布到门户')
        // 更新已保存报表的 ID
        savedReportId.value = result.id
      } else {
        ElMessage.success('报表保存成功')
        savedReportId.value = result.id
      }
    } else {
      const error = await res.json()
      ElMessage.error(error.detail || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  } finally {
    saving.value = false
  }
}

// 发布报表到门户
const publishReport = async () => {
  if (!savedReportId.value) {
    ElMessage.warning('请先保存报表')
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/reports/${savedReportId.value}/publish`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (res.ok) {
      ElMessage.success('报表已发布到门户')
    } else {
      const error = await res.json()
      ElMessage.error(error.detail || '发布失败')
    }
  } catch (error) {
    ElMessage.error('发布失败：' + error.message)
  }
}

// 打开报表列表对话框
const openReportDialog = async () => {
  reportListDialogVisible.value = true
  loadingReports.value = true
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/admin/reports', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    reportList.value = data.items || []
  } catch (error) {
    ElMessage.error('加载报表列表失败')
  } finally {
    loadingReports.value = false
  }
}

// 加载报表
const loadReport = (report) => {
  if (report.config && report.config.widgets) {
    widgets.value = report.config.widgets.map(w => ({
      ...w,
      data: null,
      loading: false
    }))
    reportName.value = report.name
    reportDescription.value = report.description || ''
    savedReportId.value = report.report_id
    reportListDialogVisible.value = false
    ElMessage.success('报表已加载')
  }
}

// 发布报表（从列表）
const publishReportById = async (report) => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/reports/${report.report_id}/publish`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (res.ok) {
      ElMessage.success('报表已发布')
      openReportDialog() // 刷新列表
    } else {
      const error = await res.json()
      ElMessage.error(error.detail || '发布失败')
    }
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

// 删除报表（从列表）
const deleteReportById = async (reportId) => {
  ElMessageBox.confirm('确定要删除该报表吗？', '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/admin/reports/${reportId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (res.ok) {
        ElMessage.success('删除成功')
        openReportDialog() // 刷新列表
      } else {
        const error = await res.json()
        ElMessage.error(error.detail || '删除失败')
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 预览报表
const previewReport = () => {
  if (widgets.value.length === 0) {
    ElMessage.warning('请先添加组件')
    return
  }
  ElMessage.success('报表预览功能开发中')
}

// 初始化
const init = async () => {
  await loadDatasources()
}

init()
</script>

<style scoped>
.report-designer-page {
  padding: 0;
  height: 100vh;
  overflow: hidden;
}

.page-container {
  height: 100vh;
}

.components-panel,
.properties-panel {
  background: #f5f7fa;
  padding: 16px;
  overflow-y: auto;
}

.panel-card {
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.components-tabs {
  margin-top: 8px;
}

.chart-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s;
}

.chart-item:hover {
  border-color: #409EFF;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.chart-preview {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409EFF;
}

.chart-name {
  font-size: 13px;
  font-weight: 500;
}

.field-list {
  display: flex;
  flex-wrap: wrap;
}

.canvas-area {
  background: #fff;
  padding: 0;
  overflow: hidden;
}

.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.report-controls {
  display: flex;
  gap: 12px;
}

.report-info {
  display: flex;
  align-items: center;
}

.canvas-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 80px);
  overflow: auto;
  background: #f0f2f5;
}

.canvas-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.widget {
  position: absolute;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.widget.active {
  border-color: #409EFF;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
  border-radius: 4px 4px 0 0;
}

.widget-title-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.widget-icon {
  width: 16px;
  height: 16px;
  color: #606266;
}

.widget-title {
  font-size: 13px;
  font-weight: 600;
}

.widget-actions {
  display: flex;
  gap: 4px;
}

.widget-content {
  padding: 12px;
  height: calc(100% - 50px);
  overflow: hidden;
}

.chart-placeholder,
.chart-loading {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.widget-resizer {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: se-resize;
  background: linear-gradient(135deg, transparent 50%, #409EFF 50%);
  border-radius: 0 0 4px 0;
}

.stats-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.quick-tips {
  margin-top: 16px;
}

/* 柱状图样式 */
.bar-chart {
  width: 100%;
  height: 100%;
}

.bar-chart-container {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 100%;
  padding: 20px 10px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
  margin: 0 4px;
  background: linear-gradient(to top, #5470c6, #91cc75);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  min-height: 20px;
}

.bar-item:hover {
  opacity: 0.8;
}

.bar-label {
  font-size: 11px;
  color: #606266;
  margin-top: 4px;
  transform: rotate(-45deg);
  transform-origin: top center;
}

.bar-value {
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  padding: 2px 6px;
  margin-bottom: 4px;
}

/* 折线图样式 */
.line-chart {
  width: 100%;
  height: 100%;
}

.line-chart-svg {
  width: 100%;
  height: 100%;
}

/* 饼图样式 */
.pie-chart {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pie-chart svg {
  width: 200px;
  height: 200px;
}

/* 表格样式 */
.table-chart {
  width: 100%;
  height: 100%;
  overflow: auto;
}
</style>
