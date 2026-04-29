<template>
  <div class="visual-report-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button @click="newReport" size="small">📄 新建</el-button>
        <el-button @click="saveReport" size="small" type="primary">💾 保存</el-button>
        <el-button @click="previewReport" size="small" type="success">👁️ 预览</el-button>
        <el-button @click="exportReport" size="small" type="warning">📤 导出</el-button>
      </div>
      <div class="toolbar-center">
        <el-input v-model="reportName" placeholder="报表名称" size="small" style="width: 200px;" />
      </div>
      <div class="toolbar-right">
        <el-button @click="undo" size="small" :disabled="!canUndo">↩️ 撤销</el-button>
        <el-button @click="redo" size="small" :disabled="!canRedo">↪️ 重做</el-button>
        <el-button @click="toggleGrid" size="small">📐 网格</el-button>
      </div>
    </div>

    <div class="designer-container">
      <!-- 左侧：组件面板 -->
      <div class="left-panel">
        <el-tabs v-model="activeTab" class="component-tabs" type="border-card">
          <el-tab-pane label="📊 图表" name="charts">
            <div class="component-grid">
              <div
                v-for="chart in chartComponents"
                :key="chart.id"
                class="component-item"
                draggable
                @dragstart="onDragStart($event, chart)"
              >
                <div class="component-icon">{{ chart.icon }}</div>
                <div class="component-name">{{ chart.name }}</div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="📋 表格" name="tables">
            <div class="component-grid">
              <div
                v-for="table in tableComponents"
                :key="table.id"
                class="component-item"
                draggable
                @dragstart="onDragStart($event, table)"
              >
                <div class="component-icon">{{ table.icon }}</div>
                <div class="component-name">{{ table.name }}</div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="🔢 指标卡" name="cards">
            <div class="component-grid">
              <div
                v-for="card in cardComponents"
                :key="card.id"
                class="component-item"
                draggable
                @dragstart="onDragStart($event, card)"
              >
                <div class="component-icon">{{ card.icon }}</div>
                <div class="component-name">{{ card.name }}</div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="📁 数据集" name="datasets">
            <el-button @click="addDataset" type="primary" size="small" style="width: 100%; margin-bottom: 10px;">
              ➕ 添加数据集
            </el-button>
            <div
              v-for="ds in datasets"
              :key="ds.id"
              class="dataset-item"
              draggable
              @dragstart="onDatasetDragStart($event, ds)"
            >
              <div class="dataset-icon">📊</div>
              <div class="dataset-info">
                <div class="dataset-name">{{ ds.name }}</div>
                <div class="dataset-type">{{ ds.type }}</div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 中间：画布区域 -->
      <div class="canvas-area">
        <div class="canvas-toolbar">
          <el-button-group>
            <el-button :size="canvasZoom === 1 ? 'primary' : ''" @click="canvasZoom = 1">100%</el-button>
            <el-button :size="canvasZoom === 0.75 ? 'primary' : ''" @click="canvasZoom = 0.75">75%</el-button>
            <el-button :size="canvasZoom === 0.5 ? 'primary' : ''" @click="canvasZoom = 0.5">50%</el-button>
          </el-button-group>
        </div>
        
        <div
          class="report-canvas"
          @dragover.prevent
          @drop="onDrop"
          :style="{ zoom: canvasZoom }"
        >
          <div
            v-for="widget in widgets"
            :key="widget.id"
            class="report-widget"
            :class="{ 'selected': selectedWidget?.id === widget.id }"
            :style="{
              left: widget.x + 'px',
              top: widget.y + 'px',
              width: widget.width + 'px',
              height: widget.height + 'px'
            }"
            @click="selectWidget(widget)"
          >
            <div class="widget-header">
              <span class="widget-title">{{ widget.name }}</span>
              <div class="widget-actions">
                <el-button size="small" @click.stop="editWidget(widget)">✏️</el-button>
                <el-button size="small" @click.stop="deleteWidget(widget)">🗑️</el-button>
              </div>
            </div>
            <div class="widget-content">
              <component
                :is="getWidgetComponent(widget.type)"
                :data="widget.data"
                :config="widget.config"
                :style="{ width: '100%', height: '100%' }"
              />
            </div>
            <div
              v-if="selectedWidget?.id === widget.id"
              class="widget-resize-handle"
            >
              <div class="resize-handle resize-nw"></div>
              <div class="resize-handle resize-n"></div>
              <div class="resize-handle resize-ne"></div>
              <div class="resize-handle resize-e"></div>
              <div class="resize-handle resize-se"></div>
              <div class="resize-handle resize-s"></div>
              <div class="resize-handle resize-sw"></div>
              <div class="resize-handle resize-w"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：属性面板 -->
      <div class="right-panel">
        <el-tabs v-model="propertyTab" class="property-tabs" type="border-card">
          <el-tab-pane label="⚙️ 属性" name="properties">
            <div v-if="selectedWidget" class="property-form">
              <el-form label-position="top" size="small">
                <el-form-item label="名称">
                  <el-input v-model="selectedWidget.name" />
                </el-form-item>
                <el-form-item label="数据类型">
                  <el-select v-model="selectedWidget.dataType" style="width: 100%;">
                    <el-option label="实时数据" value="live" />
                    <el-option label="缓存数据" value="cached" />
                    <el-option label="静态数据" value="static" />
                  </el-select>
                </el-form-item>
                <el-form-item label="数据集">
                  <el-select v-model="selectedWidget.datasetId" style="width: 100%;" placeholder="选择数据集">
                    <el-option
                      v-for="ds in datasets"
                      :key="ds.id"
                      :label="ds.name"
                      :value="ds.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="维度字段">
                  <el-select v-model="selectedWidget.dimensionField" style="width: 100%;" placeholder="选择维度">
                    <el-option
                      v-for="field in getDimensionFields(selectedWidget.datasetId)"
                      :key="field"
                      :label="field"
                      :value="field"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="度量字段">
                  <el-select v-model="selectedWidget.measureField" style="width: 100%;" placeholder="选择度量" multiple>
                    <el-option
                      v-for="field in getMeasureFields(selectedWidget.datasetId)"
                      :key="field"
                      :label="field"
                      :value="field"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
            <el-empty v-else description="请选择一个组件" />
          </el-tab-pane>
          <el-tab-pane label="🎨 样式" name="style">
            <div v-if="selectedWidget" class="style-form">
              <el-form label-position="top" size="small">
                <el-form-item label="标题显示">
                  <el-switch v-model="selectedWidget.showTitle" />
                </el-form-item>
                <el-form-item label="背景颜色">
                  <el-color-picker v-model="selectedWidget.bgColor" />
                </el-form-item>
                <el-form-item label="边框颜色">
                  <el-color-picker v-model="selectedWidget.borderColor" />
                </el-form-item>
                <el-form-item label="圆角">
                  <el-slider v-model="selectedWidget.borderRadius" :min="0" :max="20" />
                </el-form-item>
                <el-form-item label="阴影">
                  <el-switch v-model="selectedWidget.showShadow" />
                </el-form-item>
              </el-form>
            </div>
            <el-empty v-else description="请选择一个组件" />
          </el-tab-pane>
          <el-tab-pane label="📊 数据" name="data">
            <div v-if="selectedWidget" class="data-preview">
              <el-table :data="widgetPreviewData" size="small" max-height="400">
                <el-table-column
                  v-for="col in widgetPreviewColumns"
                  :key="col"
                  :prop="col"
                  :label="col"
                />
              </el-table>
            </div>
            <el-empty v-else description="请选择一个组件" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 数据集配置对话框 -->
    <el-dialog v-model="datasetDialogVisible" title="添加数据集" width="600px">
      <el-form :model="newDataset" label-width="100px">
        <el-form-item label="数据集名称">
          <el-input v-model="newDataset.name" placeholder="输入数据集名称" />
        </el-form-item>
        <el-form-item label="数据来源">
          <el-select v-model="newDataset.source" style="width: 100%;">
            <el-option label="数据表" value="table" />
            <el-option label="SQL 查询" value="sql" />
            <el-option label="API 接口" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="newDataset.source === 'table'" label="选择表">
          <el-select v-model="newDataset.table" style="width: 100%;" placeholder="选择数据表">
            <el-option label="ods_room (房源表)" value="ods_room" />
            <el-option label="ods_trade (销售表)" value="ods_trade" />
            <el-option label="ods_payment (回款表)" value="ods_payment" />
            <el-option label="dwd_room_detail (房源明细)" value="dwd_room_detail" />
            <el-option label="dws_sales_payment_fact (销售回款)" value="dws_sales_payment_fact" />
            <el-option label="ads_sales_dashboard (营销驾驶舱)" value="ads_sales_dashboard" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="newDataset.source === 'sql'" label="SQL 语句">
          <el-input
            v-model="newDataset.sql"
            type="textarea"
            :rows="6"
            placeholder="输入 SQL 查询语句"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="datasetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddDataset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 状态
const activeTab = ref('charts')
const propertyTab = ref('properties')
const reportName = ref('未命名报表')
const canvasZoom = ref(1)
const selectedWidget = ref(null)
const widgets = ref([])
const datasets = ref([])
const datasetDialogVisible = ref(false)
const newDataset = reactive({ name: '', source: 'table', table: '', sql: '' })
const canUndo = ref(false)
const canRedo = ref(false)

// 图表组件
const chartComponents = [
  { id: 'bar', name: '柱状图', icon: '📊', type: 'bar' },
  { id: 'line', name: '折线图', icon: '📈', type: 'line' },
  { id: 'pie', name: '饼图', icon: '🥧', type: 'pie' },
  { id: 'area', name: '面积图', icon: '📉', type: 'area' },
  { id: 'scatter', name: '散点图', icon: '⚬', type: 'scatter' },
  { id: 'radar', name: '雷达图', icon: '🕸️', type: 'radar' },
  { id: 'funnel', name: '漏斗图', icon: '🌪️', type: 'funnel' },
  { id: 'gauge', name: '仪表盘', icon: '⏱️', type: 'gauge' }
]

// 表格组件
const tableComponents = [
  { id: 'simple-table', name: '简单表格', icon: '📋', type: 'simple-table' },
  { id: 'pivot-table', name: '透视表', icon: '🔀', type: 'pivot-table' },
  { id: 'cross-table', name: '交叉表', icon: '➕', type: 'cross-table' }
]

// 指标卡组件
const cardComponents = [
  { id: 'kpi-card', name: 'KPI 指标卡', icon: '🎯', type: 'kpi-card' },
  { id: 'number-card', name: '数字卡片', icon: '🔢', type: 'number-card' },
  { id: 'trend-card', name: '趋势卡片', icon: '📊', type: 'trend-card' }
]

// 拖拽开始
const onDragStart = (event, component) => {
  event.dataTransfer.setData('component', JSON.stringify(component))
}

const onDatasetDragStart = (event, dataset) => {
  event.dataTransfer.setData('dataset', JSON.stringify(dataset))
}

// 放置
const onDrop = (event) => {
  const componentData = event.dataTransfer.getData('component')
  const datasetData = event.dataTransfer.getData('dataset')
  
  if (componentData) {
    const component = JSON.parse(componentData)
    const rect = event.currentTarget.getBoundingClientRect()
    const widget = {
      id: `widget-${Date.now()}`,
      name: component.name,
      type: component.type,
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      width: 400,
      height: 300,
      showTitle: true,
      bgColor: '#ffffff',
      borderColor: '#e2e8f0',
      borderRadius: 8,
      showShadow: true,
      dataType: 'live',
      datasetId: '',
      dimensionField: '',
      measureField: [],
      config: {},
      data: null
    }
    widgets.value.push(widget)
    selectWidget(widget)
    ElMessage.success(`已添加 ${component.name}`)
  }
}

// 选择组件
const selectWidget = (widget) => {
  selectedWidget.value = widget
  loadWidgetData(widget)
}

// 获取组件类型
const getWidgetComponent = (type) => {
  const components = {
    'bar': 'BarChart',
    'line': 'LineChart',
    'pie': 'PieChart',
    'area': 'AreaChart',
    'scatter': 'ScatterChart',
    'radar': 'RadarChart',
    'funnel': 'FunnelChart',
    'gauge': 'GaugeChart',
    'simple-table': 'SimpleTable',
    'pivot-table': 'PivotTable',
    'cross-table': 'CrossTable',
    'kpi-card': 'KPICard',
    'number-card': 'NumberCard',
    'trend-card': 'TrendCard'
  }
  return components[type] || 'div'
}

// 加载组件数据
const loadWidgetData = (widget) => {
  // 模拟数据加载
  widget.data = generateMockData(widget.type)
}

// 生成模拟数据
const generateMockData = (type) => {
  if (type === 'bar' || type === 'line') {
    return {
      categories: ['1 月', '2 月', '3 月', '4 月', '5 月', '6 月'],
      series: [
        { name: '销售额', data: [120, 132, 101, 134, 90, 230] },
        { name: '回款额', data: [220, 182, 191, 234, 290, 330] }
      ]
    }
  } else if (type === 'pie') {
    return [
      { name: '可售', value: 40 },
      { name: '已签约', value: 35 },
      { name: '已交付', value: 25 }
    ]
  } else if (type === 'kpi-card') {
    return { value: 1234567, unit: '元', label: '总销售额', trend: '+12.5%' }
  }
  return {}
}

// 获取维度字段
const getDimensionFields = (datasetId) => {
  return ['日期', '项目', '楼栋', '房型', '状态']
}

// 获取度量字段
const getMeasureFields = (datasetId) => {
  return ['销售额', '回款额', '面积', '单价', '数量']
}

// 添加数据集
const addDataset = () => {
  datasetDialogVisible.value = true
}

const confirmAddDataset = () => {
  if (!newDataset.name) {
    ElMessage.warning('请输入数据集名称')
    return
  }
  datasets.value.push({
    id: `dataset-${Date.now()}`,
    name: newDataset.name,
    type: newDataset.source === 'sql' ? 'SQL' : '表',
    source: newDataset.source,
    table: newDataset.table,
    sql: newDataset.sql
  })
  datasetDialogVisible.value = false
  ElMessage.success('数据集添加成功')
}

// 工具栏操作
const newReport = () => {
  ElMessageBox.confirm('确定要新建报表吗？未保存的内容将丢失', '提示', {
    type: 'warning'
  }).then(() => {
    widgets.value = []
    reportName.value = '未命名报表'
    ElMessage.success('已新建报表')
  })
}

const saveReport = () => {
  ElMessage.success('报表保存成功')
}

const previewReport = () => {
  ElMessage.info('预览功能开发中')
}

const exportReport = () => {
  ElMessage.info('导出功能开发中')
}

const undo = () => {
  ElMessage.info('撤销功能开发中')
}

const redo = () => {
  ElMessage.info('重做功能开发中')
}

const toggleGrid = () => {
  ElMessage.info('网格功能开发中')
}

const editWidget = (widget) => {
  ElMessage.info(`编辑 ${widget.name}`)
}

const deleteWidget = (widget) => {
  ElMessageBox.confirm(`确定要删除 ${widget.name} 吗？`, '提示', {
    type: 'warning'
  }).then(() => {
    widgets.value = widgets.value.filter(w => w.id !== widget.id)
    selectedWidget.value = null
    ElMessage.success('已删除')
  })
}

// 计算属性
const widgetPreviewData = computed(() => {
  if (!selectedWidget.value) return []
  return selectedWidget.value.data?.series || []
})

const widgetPreviewColumns = computed(() => {
  if (!selectedWidget.value) return []
  return ['name', 'data']
})
</script>

<style scoped>
.visual-report-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
}

.designer-toolbar {
  height: 50px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.toolbar-left, .toolbar-right {
  display: flex;
  gap: 8px;
}

.designer-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 260px;
  background: white;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
}

.right-panel {
  width: 300px;
  background: white;
  border-left: 1px solid #e2e8f0;
  overflow-y: auto;
}

.canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8fafc;
}

.canvas-toolbar {
  padding: 10px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  text-align: center;
}

.report-canvas {
  flex: 1;
  position: relative;
  overflow: auto;
  background-image:
    linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 10px;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}

.component-item:hover {
  background: #e0f2fe;
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.component-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.component-name {
  font-size: 12px;
  color: #475569;
  text-align: center;
}

.dataset-item {
  display: flex;
  align-items: center;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: grab;
}

.dataset-icon {
  font-size: 20px;
  margin-right: 10px;
}

.dataset-info {
  flex: 1;
}

.dataset-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}

.dataset-type {
  font-size: 11px;
  color: #64748b;
}

.report-widget {
  position: absolute;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.report-widget.selected {
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.widget-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.widget-actions {
  display: flex;
  gap: 4px;
}

.widget-content {
  height: calc(100% - 40px);
  padding: 10px;
}

.widget-resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
  pointer-events: auto;
}

.resize-nw { top: -4px; left: -4px; cursor: nw-resize; }
.resize-n { top: -4px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.resize-ne { top: -4px; right: -4px; cursor: ne-resize; }
.resize-e { right: -4px; top: 50%; transform: translateY(-50%); cursor: e-resize; }
.resize-se { bottom: -4px; right: -4px; cursor: se-resize; }
.resize-s { bottom: -4px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.resize-sw { bottom: -4px; left: -4px; cursor: sw-resize; }
.resize-w { left: -4px; top: 50%; transform: translateY(-50%); cursor: w-resize; }

.property-form, .style-form {
  padding: 10px;
}

.data-preview {
  padding: 10px;
}
</style>
