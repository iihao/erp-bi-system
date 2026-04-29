<template>
  <div class="report-designer-pro">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button @click="$router.back()" size="small">← 返回</el-button>
        <el-divider direction="vertical" />
        <el-input 
          v-model="reportName" 
          placeholder="报表名称" 
          size="small"
          style="width: 200px"
        />
        <el-input 
          v-model="reportDescription" 
          placeholder="报表描述" 
          size="small"
          style="width: 300px"
        />
      </div>
      
      <div class="toolbar-center">
        <el-button-group>
          <el-button size="small" @click="undo" :disabled="!canUndo">↶ 撤销</el-button>
          <el-button size="small" @click="redo" :disabled="!canRedo">↷ 重做</el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-button-group>
          <el-button size="small" @click="alignLeft">左对齐</el-button>
          <el-button size="small" @click="alignCenter">居中</el-button>
          <el-button size="small" @click="alignRight">右对齐</el-button>
        </el-button-group>
      </div>
      
      <div class="toolbar-right">
        <el-button @click="previewReport" size="small">
          <el-icon><View /></el-icon> 预览
        </el-button>
        <el-button type="primary" @click="saveReport('draft')" :loading="saving" size="small">
          <el-icon><VideoPlay /></el-icon> 保存
        </el-button>
        <el-button type="success" @click="saveReport('published')" :loading="saving" size="small">
          <el-icon><Top /></el-icon> 发布
        </el-button>
      </div>
    </div>

    <div class="designer-container">
      <!-- 左侧面板：数据集 + 组件 -->
      <div class="left-panel">
        <el-tabs v-model="leftActiveTab" class="panel-tabs">
          <el-tab-pane label="数据集" name="dataset">
            <div class="dataset-panel">
              <el-button type="primary" size="small" @click="showAddDataset" style="width: 100%; margin-bottom: 12px;">
                <el-icon><Plus /></el-icon> 新建数据集
              </el-button>
              
              <div class="dataset-list">
                <div 
                  v-for="ds in datasets" 
                  :key="ds.id"
                  class="dataset-item"
                  :class="{ active: selectedDataset?.id === ds.id }"
                  @click="selectDataset(ds)"
                >
                  <div class="dataset-header">
                    <span class="dataset-name">{{ ds.name }}</span>
                    <el-button size="small" @click.stop="editDataset(ds)" circle>
                      <el-icon><Edit /></el-icon>
                    </el-button>
                  </div>
                  <div class="dataset-info">
                    <el-tag size="small" type="info">{{ ds.tableName }}</el-tag>
                    <span class="field-count">{{ ds.fields?.length || 0 }} 个字段</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="组件" name="components">
            <div class="components-panel">
              <el-tabs v-model="componentTab" size="small">
                <el-tab-pane label="图表" name="chart">
                  <div class="component-grid">
                    <div
                      v-for="chart in chartComponents"
                      :key="chart.type"
                      class="component-item"
                      draggable
                      @dragstart="onDragStart($event, chart)"
                    >
                      <div class="component-icon">
                        <el-icon :size="28"><component :is="chart.icon" /></el-icon>
                      </div>
                      <span class="component-name">{{ chart.name }}</span>
                    </div>
                  </div>
                </el-tab-pane>
                <el-tab-pane label="表格" name="table">
                  <div class="component-grid">
                    <div
                      v-for="table in tableComponents"
                      :key="table.type"
                      class="component-item"
                      draggable
                      @dragstart="onDragStart($event, table)"
                    >
                      <div class="component-icon">
                        <el-icon :size="28"><component :is="table.icon" /></el-icon>
                      </div>
                      <span class="component-name">{{ table.name }}</span>
                    </div>
                  </div>
                </el-tab-pane>
                <el-tab-pane label="控件" name="control">
                  <div class="component-grid">
                    <div
                      v-for="control in controlComponents"
                      :key="control.type"
                      class="component-item"
                      draggable
                      @dragstart="onDragStart($event, control)"
                    >
                      <div class="component-icon">
                        <el-icon :size="28"><component :is="control.icon" /></el-icon>
                      </div>
                      <span class="component-name">{{ control.name }}</span>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 中间：画布区域 -->
      <div class="canvas-wrapper">
        <div class="canvas-toolbar">
          <el-button-group>
            <el-button size="small" @click="zoomOut" :disabled="zoom <= 50">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button size="small" disabled>{{ zoom }}%</el-button>
            <el-button size="small" @click="zoomIn" :disabled="zoom >= 200">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-button-group>
          <el-button-group>
            <el-button size="small" @click="fitCanvas">适应屏幕</el-button>
            <el-button size="small" @click="resetCanvas">重置</el-button>
          </el-button-group>
        </div>
        
        <div class="canvas-container" ref="canvasContainer">
          <div 
            class="report-canvas"
            :style="{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }"
            @dragover="onDragOver"
            @drop="onDrop"
            @click="onCanvasClick"
          >
            <!-- 网格背景 -->
            <div class="canvas-grid"></div>
            
            <!-- 报表组件 -->
            <div
              v-for="widget in widgets"
              :key="widget.id"
              class="report-widget"
              :class="{ active: selectedWidget?.id === widget.id }"
              :style="{
                left: widget.x + 'px',
                top: widget.y + 'px',
                width: widget.width + 'px',
                height: widget.height + 'px',
                zIndex: widget.zIndex
              }"
              @click.stop="selectWidget(widget)"
            >
              <!-- 组件内容 -->
              <div class="widget-body">
                <div v-if="widget.type === 'table'" class="table-widget">
                  <el-table :data="widget.data || []" size="small" max-height="200">
                    <el-table-column
                      v-for="field in widget.displayFields"
                      :key="field"
                      :prop="field"
                      :label="field"
                    />
                  </el-table>
                </div>
                
                <div v-else-if="widget.type === 'bar'" class="chart-widget">
                  <!-- 柱状图渲染 -->
                  <div class="bar-chart">
                    <div
                      v-for="(item, idx) in (widget.data || [])"
                      :key="idx"
                      class="bar-item"
                      :style="{ height: getBarHeight(item[widget.measureField]) + '%' }"
                    >
                      <div class="bar-value">{{ item[widget.measureField] }}</div>
                      <div class="bar-label">{{ item[widget.dimensionField] }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 组件操作栏 -->
              <div class="widget-toolbar" v-show="selectedWidget?.id === widget.id">
                <el-button size="small" @click.stop="editWidget(widget)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" @click.stop="duplicateWidget(widget)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button size="small" type="danger" @click.stop="removeWidget(widget.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧面板：属性配置 -->
      <div class="right-panel">
        <el-tabs v-model="rightActiveTab" class="panel-tabs">
          <el-tab-pane label="数据" name="data">
            <div class="properties-panel" v-if="selectedWidget">
              <el-form size="small" label-position="top">
                <el-form-item label="绑定数据集">
                  <el-select v-model="selectedWidget.datasetId" placeholder="选择数据集" @change="onDatasetChange" style="width: 100%">
                    <el-option
                      v-for="ds in datasets"
                      :key="ds.id"
                      :label="ds.name"
                      :value="ds.id"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="维度字段" v-if="selectedWidget.datasetId">
                  <el-select v-model="selectedWidget.dimensionField" placeholder="选择维度字段" style="width: 100%">
                    <el-option
                      v-for="field in getDimensionFields(selectedWidget.datasetId)"
                      :key="field.name"
                      :label="`${field.name} (${field.type})`"
                      :value="field.name"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="度量字段" v-if="selectedWidget.datasetId">
                  <el-select v-model="selectedWidget.measureField" placeholder="选择度量字段" style="width: 100%">
                    <el-option
                      v-for="field in getMeasureFields(selectedWidget.datasetId)"
                      :key="field.name"
                      :label="`${field.name} (${field.type})`"
                      :value="field.name"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="显示字段">
                  <el-transfer
                    v-model="selectedWidget.displayFields"
                    :data="getAllFields(selectedWidget.datasetId)"
                    :titles="['可选字段', '已选字段']"
                    filterable
                  />
                </el-form-item>
              </el-form>
            </div>
            <div v-else class="empty-panel">
              <el-empty description="请选择组件" :image-size="80" />
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="样式" name="style">
            <div class="properties-panel" v-if="selectedWidget">
              <el-form size="small" label-position="top">
                <el-form-item label="标题">
                  <el-input v-model="selectedWidget.title" placeholder="组件标题" />
                </el-form-item>
                
                <el-form-item label="颜色主题">
                  <el-select v-model="selectedWidget.theme" placeholder="选择主题" style="width: 100%">
                    <el-option label="蓝色" value="blue" />
                    <el-option label="绿色" value="green" />
                    <el-option label="橙色" value="orange" />
                    <el-option label="紫色" value="purple" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="宽度：{{ selectedWidget.width }}px">
                  <el-slider v-model="selectedWidget.width" :min="200" :max="1200" :step="10" />
                </el-form-item>
                
                <el-form-item label="高度：{{ selectedWidget.height }}px">
                  <el-slider v-model="selectedWidget.height" :min="150" :max="800" :step="10" />
                </el-form-item>
                
                <el-form-item label="圆角">
                  <el-slider v-model="selectedWidget.borderRadius" :min="0" :max="20" />
                </el-form-item>
                
                <el-form-item label="阴影">
                  <el-switch v-model="selectedWidget.shadow" />
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="高级" name="advanced">
            <div class="properties-panel" v-if="selectedWidget">
              <el-form size="small" label-position="top">
                <el-form-item label="条件格式">
                  <el-button size="small" @click="showConditionalFormat">
                    <el-icon><Plus /></el-icon> 添加规则
                  </el-button>
                </el-form-item>
                
                <el-form-item label="数据刷新">
                  <el-select v-model="selectedWidget.refreshInterval" placeholder="刷新频率" style="width: 100%">
                    <el-option label="不刷新" :value="0" />
                    <el-option label="30 秒" :value="30000" />
                    <el-option label="1 分钟" :value="60000" />
                    <el-option label="5 分钟" :value="300000" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="钻取配置">
                  <el-button size="small" @click="showDrillDown">
                    <el-icon><Edit /></el-icon> 配置钻取
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 新建数据集对话框 -->
    <el-dialog v-model="datasetDialogVisible" title="新建数据集" width="800px">
      <el-form :model="datasetForm" label-width="120px">
        <el-form-item label="数据集名称">
          <el-input v-model="datasetForm.name" placeholder="例如：销售数据集" />
        </el-form-item>
        <el-form-item label="数据源">
          <el-select v-model="datasetForm.datasourceId" placeholder="选择数据源" style="width: 100%">
            <el-option
              v-for="ds in datasourceList"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据表">
          <el-select v-model="datasetForm.tableName" placeholder="选择数据表" style="width: 100%">
            <el-option v-for="table in tableList" :key="table" :label="table" :value="table" />
          </el-select>
        </el-form-item>
        <el-form-item label="筛选条件">
          <el-input
            v-model="datasetForm.filter"
            type="textarea"
            placeholder="WHERE 条件，例如：status = 'active'"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="datasetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createDataset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, VideoPlay, Top, FolderChecked, Edit, Refresh, CopyDocument, Delete, ZoomIn, ZoomOut, ScaleToOriginal, Plus } from '@element-plus/icons-vue'

// 状态管理
const leftActiveTab = ref('dataset')
const rightActiveTab = ref('data')
const componentTab = ref('chart')
const reportName = ref('')
const reportDescription = ref('')
const saving = ref(false)
const zoom = ref(100)

// 数据集管理
const datasets = ref([])
const selectedDataset = ref(null)
const datasetDialogVisible = ref(false)
const datasetForm = ref({
  name: '',
  datasourceId: '',
  tableName: '',
  filter: ''
})

// 组件定义
const chartComponents = [
  { type: 'bar', name: '柱状图', icon: 'Histogram' },
  { type: 'line', name: '折线图', icon: 'TrendCharts' },
  { type: 'pie', name: '饼图', icon: 'PieChart' },
  { type: 'area', name: '面积图', icon: 'ScaleToOriginal' },
  { type: 'scatter', name: '散点图', icon: 'Operation' },
  { type: 'radar', name: '雷达图', icon: 'Aim' }
]

const tableComponents = [
  { type: 'table', name: '明细表', icon: 'Grid' },
  { type: 'pivot', name: '透视表', icon: 'Histogram' },
  { type: 'cross', name: '交叉表', icon: 'Plus' }
]

const controlComponents = [
  { type: 'input', name: '输入框', icon: 'EditPen' },
  { type: 'select', name: '下拉框', icon: 'ArrowDown' },
  { type: 'date', name: '日期选择', icon: 'Calendar' },
  { type: 'button', name: '按钮', icon: 'Pointer' }
]

// 画布组件
const widgets = ref([])
const selectedWidget = ref(null)
const selectedDatasource = ref(null)
const datasourceList = ref([])
const tableList = ref([])

// 撤销重做
const history = ref([])
const historyIndex = ref(-1)

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

// 拖拽开始
const onDragStart = (event, component) => {
  event.dataTransfer.setData('component', JSON.stringify(component))
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
  const component = JSON.parse(event.dataTransfer.getData('component'))
  const rect = event.currentTarget.getBoundingClientRect()
  
  const widget = {
    id: `widget_${Date.now()}`,
    type: component.type,
    title: component.name,
    x: (event.clientX - rect.left - 100) * (100 / zoom.value),
    y: (event.clientY - rect.top - 50) * (100 / zoom.value),
    width: 400,
    height: 300,
    zIndex: widgets.value.length + 1,
    datasetId: selectedDataset.value?.id || null,
    dimensionField: '',
    measureField: '',
    displayFields: [],
    data: null,
    theme: 'blue',
    borderRadius: 4,
    shadow: true
  }
  
  widgets.value.push(widget)
  selectWidget(widget)
  pushHistory()
  ElMessage.success(`已添加${component.name}`)
}

// 选择组件
const selectWidget = (widget) => {
  selectedWidget.value = widget
}

// 画布点击
const onCanvasClick = () => {
  selectedWidget.value = null
}

// 删除组件
const removeWidget = (id) => {
  ElMessageBox.confirm('确定删除该组件？', '提示', { type: 'warning' })
    .then(() => {
      const idx = widgets.value.findIndex(w => w.id === id)
      if (idx > -1) {
        widgets.value.splice(idx, 1)
        if (selectedWidget.value?.id === id) {
          selectedWidget.value = null
        }
        pushHistory()
        ElMessage.success('删除成功')
      }
    })
}

// 复制组件
const duplicateWidget = (widget) => {
  const newWidget = {
    ...JSON.parse(JSON.stringify(widget)),
    id: `widget_${Date.now()}`,
    x: widget.x + 20,
    y: widget.y + 20,
    zIndex: widgets.value.length + 1
  }
  widgets.value.push(newWidget)
  selectWidget(newWidget)
  pushHistory()
  ElMessage.success('已复制组件')
}

// 编辑组件
const editWidget = (widget) => {
  ElMessage.info('编辑功能开发中')
}

// 数据集操作
const showAddDataset = () => {
  datasetForm.value = {
    name: '',
    datasourceId: '',
    tableName: '',
    filter: ''
  }
  datasetDialogVisible.value = true
}

const editDataset = (ds) => {
  datasetForm.value = { ...ds }
  datasetDialogVisible.value = true
}

const selectDataset = (ds) => {
  selectedDataset.value = ds
}

const createDataset = async () => {
  // TODO: 调用 API 创建数据集
  datasets.value.push({
    id: `dataset_${Date.now()}`,
    ...datasetForm.value,
    fields: []
  })
  datasetDialogVisible.value = false
  ElMessage.success('数据集创建成功')
}

// 字段获取
const getDimensionFields = (datasetId) => {
  const ds = datasets.value.find(d => d.id === datasetId)
  return ds?.fields?.filter(f => f.type !== 'number') || []
}

const getMeasureFields = (datasetId) => {
  const ds = datasets.value.find(d => d.id === datasetId)
  return ds?.fields?.filter(f => f.type === 'number') || []
}

const getAllFields = (datasetId) => {
  const ds = datasets.value.find(d => d.id === datasetId)
  return ds?.fields?.map(f => ({ key: f.name, label: f.name })) || []
}

// 数据集变化
const onDatasetChange = () => {
  if (selectedWidget.value?.datasetId) {
    const ds = datasets.value.find(d => d.id === selectedWidget.value.datasetId)
    if (ds) {
      // 加载数据集字段
    }
  }
}

// 图表渲染辅助
const getBarHeight = (value) => {
  if (!selectedWidget.value?.data) return 0
  const max = Math.max(...selectedWidget.value.data.map(d => d[selectedWidget.value.measureField] || 0), 1)
  return (value / max) * 80
}

// 撤销重做
const pushHistory = () => {
  history.value = history.value.slice(0, historyIndex.value + 1)
  history.value.push(JSON.stringify(widgets.value))
  historyIndex.value++
}

const undo = () => {
  if (canUndo.value) {
    historyIndex.value--
    widgets.value = JSON.parse(history.value[historyIndex.value])
  }
}

const redo = () => {
  if (canRedo.value) {
    historyIndex.value++
    widgets.value = JSON.parse(history.value[historyIndex.value])
  }
}

// 对齐
const alignLeft = () => {
  ElMessage.info('左对齐功能开发中')
}

const alignCenter = () => {
  ElMessage.info('居中对齐功能开发中')
}

const alignRight = () => {
  ElMessage.info('右对齐功能开发中')
}

// 缩放
const zoomIn = () => {
  zoom.value = Math.min(200, zoom.value + 10)
}

const zoomOut = () => {
  zoom.value = Math.max(50, zoom.value - 10)
}

const fitCanvas = () => {
  zoom.value = 100
}

const resetCanvas = () => {
  widgets.value = []
  zoom.value = 100
}

// 保存报表
const saveReport = async (status) => {
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
      type: 'report',
      status: status,
      config: {
        widgets: widgets.value.map(w => ({
          id: w.id,
          type: w.type,
          title: w.title,
          x: w.x,
          y: w.y,
          width: w.width,
          height: w.height,
          datasetId: w.datasetId,
          dimensionField: w.dimensionField,
          measureField: w.measureField,
          displayFields: w.displayFields,
          theme: w.theme,
          borderRadius: w.borderRadius,
          shadow: w.shadow
        })),
        datasets: datasets.value
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
      ElMessage.success(status === 'published' ? '报表已发布' : '报表已保存')
    } else {
      const error = await res.json()
      ElMessage.error(error.detail || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败：' + error.message)
  } finally {
    saving.value = false
  }
}

// 预览报表
const previewReport = () => {
  ElMessage.success('预览功能开发中')
}

// 条件格式
const showConditionalFormat = () => {
  ElMessage.info('条件格式功能开发中')
}

// 钻取配置
const showDrillDown = () => {
  ElMessage.info('钻取配置功能开发中')
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
  } catch (error) {
    console.error('加载数据源失败', error)
  }
}

// 初始化
onMounted(() => {
  loadDatasources()
  pushHistory()
})

// 键盘快捷键
const handleKeyDown = (e) => {
  // Delete 删除
  if (e.key === 'Delete' && selectedWidget.value) {
    removeWidget(selectedWidget.value.id)
  }
  
  // Ctrl/Cmd + S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveReport('draft')
  }
  
  // Ctrl/Cmd + Z 撤销
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
    e.preventDefault()
    undo()
  }
  
  // Ctrl/Cmd + Shift + Z 重做
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') {
    e.preventDefault()
    redo()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.report-designer-pro {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 工具栏 */
.toolbar {
  height: 50px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 设计器容器 */
.designer-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边面板 */
.left-panel,
.right-panel {
  width: 320px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.right-panel {
  border-right: none;
  border-left: 1px solid #e4e7ed;
}

.panel-tabs {
  flex: 1;
  overflow: hidden;
}

.panel-tabs :deep(.el-tabs__content) {
  height: calc(100% - 55px);
  overflow-y: auto;
  padding: 12px;
}

/* 数据集面板 */
.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dataset-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.dataset-item:hover {
  border-color: #409EFF;
  background: #ecf5ff;
}

.dataset-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dataset-name {
  font-weight: 600;
  font-size: 14px;
}

.dataset-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

/* 组件面板 */
.component-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s;
}

.component-item:hover {
  border-color: #409EFF;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.component-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  color: #409EFF;
}

.component-name {
  font-size: 12px;
  text-align: center;
}

/* 画布区域 */
.canvas-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f2f5;
}

.canvas-toolbar {
  height: 40px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.canvas-container {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.report-canvas {
  position: relative;
  width: 1200px;
  height: 1600px;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(64, 158, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
}

/* 报表组件 */
.report-widget {
  position: absolute;
  background: #fff;
  border: 2px solid transparent;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.report-widget.active {
  border-color: #409EFF;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.widget-body {
  height: 100%;
  padding: 12px;
  overflow: hidden;
}

.widget-toolbar {
  position: absolute;
  top: -36px;
  right: 0;
  display: flex;
  gap: 4px;
  background: #fff;
  padding: 4px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 属性面板 */
.properties-panel {
  padding: 12px;
}

.empty-panel {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

/* 图表组件 */
.table-widget {
  height: 100%;
  overflow: auto;
}

.chart-widget {
  height: 100%;
}

.bar-chart {
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
  min-height: 20px;
}

.bar-value {
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  padding: 2px 6px;
  margin-bottom: 4px;
}

.bar-label {
  font-size: 11px;
  color: #606266;
  transform: rotate(-45deg);
  transform-origin: top center;
}
</style>
