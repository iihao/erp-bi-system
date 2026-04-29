<template>
  <div class="etl-editor-page">
    <el-container class="page-container">
      <!-- 左侧：组件面板 -->
      <el-aside width="280px" class="components-panel">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><Tools /></el-icon>
                ETL 组件库
              </span>
            </div>
          </template>

          <el-collapse v-model="activeComponentGroup" accordion>
            <el-collapse-item title="数据源组件" name="datasource">
              <div
                v-for="comp in dataSourceComponents"
                :key="comp.id"
                class="component-item"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <el-icon class="component-icon"><DocumentChecked /></el-icon>
                <span class="component-name">{{ comp.name }}</span>
              </div>
            </el-collapse-item>

            <el-collapse-item title="转换组件" name="transform">
              <div
                v-for="comp in transformComponents"
                :key="comp.id"
                class="component-item"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <el-icon class="component-icon"><Check /></el-icon>
                <span class="component-name">{{ comp.name }}</span>
              </div>
            </el-collapse-item>

            <el-collapse-item title="目标组件" name="target">
              <div
                v-for="comp in targetComponents"
                :key="comp.id"
                class="component-item"
                draggable="true"
                @dragstart="onDragStart($event, comp)"
              >
                <el-icon class="component-icon"><Upload /></el-icon>
                <span class="component-name">{{ comp.name }}</span>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-aside>

      <!-- 中间：画布区域 -->
      <el-main class="canvas-area">
        <div class="canvas-header">
          <div class="workflow-controls">
            <el-button type="primary" @click="saveWorkflow" :loading="saving">
              <el-icon><VideoPlay /></el-icon> 保存工作流
            </el-button>
            <el-button type="success" @click="runWorkflow" :loading="running">
              <el-icon><VideoPlay /></el-icon> 运行
            </el-button>
            <el-button @click="clearCanvas">
              <el-icon><Delete /></el-icon> 清空
            </el-button>
          </div>

          <div class="workflow-info">
            <el-input v-model="workflowName" placeholder="工作流名称" style="width: 200px; margin-right: 12px;" />
            <el-select v-model="workflowLayer" placeholder="数仓层" style="width: 140px;">
              <el-option label="ODS" value="ODS" />
              <el-option label="DWD" value="DWD" />
              <el-option label="DWS" value="DWS" />
              <el-option label="ADS" value="ADS" />
            </el-select>
          </div>
        </div>

        <!-- 画布容器 -->
        <div
          ref="canvasRef"
          class="canvas-container"
          @dragover="onCanvasDragOver"
          @drop="onDrop"
          @click="onCanvasClick"
        >
          <!-- 节点 -->
          <div
            v-for="node in nodes"
            :key="node.id"
            class="node"
            :class="{ active: selectedNode?.id === node.id, dragging: draggedNode?.id === node.id }"
            :style="{ left: node.x + 'px', top: node.y + 'px' }"
            draggable="true"
            @click.stop="selectNode(node)"
            @dragstart="onNodeDragStart($event, node)"
            @dragover="onNodeDragOver($event)"
            @dragend="onNodeDragEnd"
          >
            <div class="node-header" :class="getNodeClass(node)">
              <el-icon class="node-icon-el" :size="16">
                <DocumentChecked v-if="node.type === 'dataSource'" />
                <Check v-else-if="node.type === 'transform'" />
                <Upload v-else />
              </el-icon>
              <span class="node-title">{{ node.name }}</span>
            </div>

            <div class="node-content">
              <!-- 数据源配置 -->
              <div v-if="node.type === 'dataSource'" class="node-config">
                <el-form size="small" label-position="top">
                  <el-form-item label="数据源">
                    <el-select v-model="node.config.sourceType" placeholder="选择类型" style="width: 100%">
                      <el-option label="MySQL" value="mysql" />
                      <el-option label="PostgreSQL" value="postgres" />
                      <el-option label="CSV" value="csv" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="表名">
                    <el-input v-model="node.config.tableName" placeholder="表名" />
                  </el-form-item>
                </el-form>
              </div>

              <!-- 转换配置 -->
              <div v-if="node.type === 'transform'" class="node-config">
                <el-form size="small" label-position="top">
                  <el-form-item label="类型">
                    <el-select v-model="node.config.transformType" placeholder="选择类型" style="width: 100%">
                      <el-option label="过滤" value="filter" />
                      <el-option label="聚合" value="aggregate" />
                      <el-option label="连接" value="join" />
                      <el-option label="映射" value="mapping" />
                    </el-select>
                  </el-form-item>
                  <el-form-item v-if="node.config.transformType === 'filter'" label="条件">
                    <el-input v-model="node.config.filterCondition" placeholder="WHERE 条件" />
                  </el-form-item>
                </el-form>
              </div>

              <!-- 目标配置 -->
              <div v-if="node.type === 'target'" class="node-config">
                <el-form size="small" label-position="top">
                  <el-form-item label="目标表">
                    <el-input v-model="node.config.targetTable" placeholder="表名" />
                  </el-form-item>
                  <el-form-item label="写入模式">
                    <el-select v-model="node.config.writeMode" style="width: 100%">
                      <el-option label="覆盖" value="overwrite" />
                      <el-option label="追加" value="append" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <div class="node-actions">
              <el-button size="small" type="danger" circle @click.stop="removeNode(node.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- SVG 连线层 -->
          <svg class="connections-layer" ref="svgRef">
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#909399" />
              </marker>
            </defs>
            <line
              v-for="conn in connections"
              :key="conn.id"
              :x1="getNodeCenter(conn.from).x"
              :y1="getNodeCenter(conn.from).y"
              :x2="getNodeCenter(conn.to).x"
              :y2="getNodeCenter(conn.to).y"
              stroke="#909399"
              stroke-width="2"
              marker-end="url(#arrowhead)"
            />
          </svg>
        </div>
      </el-main>

      <!-- 右侧：属性面板 -->
      <el-aside width="320px" class="properties-panel">
        <el-card class="panel-card" v-if="selectedNode">
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><Setting /></el-icon>
                节点配置
              </span>
              <el-button size="small" circle @click="selectedNode = null">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>

          <el-form size="small" label-position="top">
            <el-form-item label="节点 ID">
              <el-input :value="selectedNode.id" readonly />
            </el-form-item>
            <el-form-item label="节点名称">
              <el-input v-model="selectedNode.name" />
            </el-form-item>
            <el-form-item label="类型">
              <el-tag>{{ selectedNode.type }}</el-tag>
            </el-form-item>
            <el-form-item label="位置">
              <span>X: {{ Math.round(selectedNode.x) }}, Y: {{ Math.round(selectedNode.y) }}</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="panel-card" v-else>
          <template #header>
            <div class="panel-header">
              <span class="card-title">
                <el-icon :size="18"><InfoFilled /></el-icon>
                提示
              </span>
            </div>
          </template>
          <div class="empty-selection">
            <el-empty description="点击节点进行配置" :image-size="80" />
            <div class="help-text">
              <p>操作指南：</p>
              <ol>
                <li>从左侧拖拽组件到画布</li>
                <li>在画布上拖动节点调整位置</li>
                <li>点击节点查看配置</li>
                <li>保存并运行工作流</li>
              </ol>
            </div>
          </div>
        </el-card>
      </el-aside>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Tools, DocumentChecked, Upload, Check, Download, Delete, InfoFilled, Setting, Refresh, VideoPlay } from '@element-plus/icons-vue'

// 组件数据
const dataSourceComponents = [
  { id: 'mysql-source', name: 'MySQL 数据源', type: 'dataSource' },
  { id: 'postgres-source', name: 'PostgreSQL 数据源', type: 'dataSource' },
  { id: 'csv-source', name: 'CSV 文件', type: 'dataSource' }
]

const transformComponents = [
  { id: 'filter', name: '数据过滤', type: 'transform' },
  { id: 'aggregate', name: '数据聚合', type: 'transform' },
  { id: 'join', name: '数据连接', type: 'transform' },
  { id: 'mapping', name: '字段映射', type: 'transform' }
]

const targetComponents = [
  { id: 'mysql-target', name: 'MySQL 目标', type: 'target' },
  { id: 'csv-target', name: 'CSV 输出', type: 'target' }
]

const activeComponentGroup = ref('datasource')
const workflowName = ref('新建工作流')
const workflowLayer = ref('ODS')
const saving = ref(false)
const running = ref(false)
const currentWorkflowId = ref(null)

// 画布
const canvasRef = ref(null)
const svgRef = ref(null)

// 数据
const nodes = ref([])
const connections = ref([])
const selectedNode = ref(null)

// 拖拽状态
let dragData = null
let draggedNode = null
let dragOffset = { x: 0, y: 0 }
let isDraggingNode = false

// 生成 ID
const generateId = () => `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

// 获取节点样式
const getNodeClass = (node) => {
  const classes = { dataSource: 'datasource', transform: 'transform', target: 'target' }
  return classes[node.type] || ''
}

// 获取默认配置
const getDefaultConfig = (type) => {
  const configs = {
    dataSource: { sourceType: '', tableName: '', queryCondition: '' },
    transform: { transformType: '', filterCondition: '', aggregateFields: '', joinCondition: '', fieldMapping: '' },
    target: { targetTable: '', writeMode: 'overwrite' }
  }
  return configs[type] || {}
}

// 获取节点中心点
const getNodeCenter = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  return { x: node.x + 120, y: node.y + 40 }
}

// 从面板拖拽开始
const onDragStart = (event, component) => {
  dragData = { ...component }
  event.dataTransfer.setData('text/plain', component.id)
  event.dataTransfer.effectAllowed = 'copy'
}

// 画布拖拽经过
const onCanvasDragOver = (event) => {
  event.preventDefault()
  if (isDraggingNode && draggedNode) {
    const rect = canvasRef.value.getBoundingClientRect()
    draggedNode.x = event.clientX - rect.left - dragOffset.x
    draggedNode.y = event.clientY - rect.top - dragOffset.y
  } else {
    event.dataTransfer.dropEffect = 'copy'
  }
}

// 放置到画布
const onDrop = (event) => {
  event.preventDefault()
  if (!dragData) return

  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left - 100
  const y = event.clientY - rect.top - 40

  const newNode = {
    id: generateId(),
    name: dragData.name,
    type: dragData.type,
    x,
    y,
    description: '',
    config: getDefaultConfig(dragData.type)
  }

  nodes.value.push(newNode)
  ElMessage.success(`已添加 ${dragData.name} 节点`)
  dragData = null
}

// 节点拖拽开始
const onNodeDragStart = (event, node) => {
  if (event.target.closest('.node-actions') || event.target.closest('.el-form')) return
  draggedNode = node
  isDraggingNode = true
  const rect = event.currentTarget.getBoundingClientRect()
  dragOffset.x = event.clientX - rect.left
  dragOffset.y = event.clientY - rect.top
  event.dataTransfer.effectAllowed = 'move'
  event.stopPropagation()
}

// 节点拖拽经过
const onNodeDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

// 节点拖拽结束
const onNodeDragEnd = () => {
  isDraggingNode = false
  draggedNode = null
}

// 选择节点
const selectNode = (node) => {
  selectedNode.value = node
}

// 移除节点
const removeNode = (nodeId) => {
  ElMessageBox.confirm('确定删除这个节点？', '确认删除', { type: 'warning' }).then(() => {
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    connections.value = connections.value.filter(c => c.from !== nodeId && c.to !== nodeId)
    if (selectedNode.value?.id === nodeId) {
      selectedNode.value = null
    }
    ElMessage.success('已删除')
  }).catch(() => {})
}

// 画布点击
const onCanvasClick = () => {
  selectedNode.value = null
}

// 清空画布
const clearCanvas = () => {
  ElMessageBox.confirm('确定清空画布？', '确认清空', { type: 'warning' }).then(() => {
    nodes.value = []
    connections.value = []
    selectedNode.value = null
    currentWorkflowId.value = null
    ElMessage.success('已清空')
  }).catch(() => {})
}

// 保存工作流
const saveWorkflow = async () => {
  if (nodes.value.length === 0) {
    ElMessage.warning('请先添加节点')
    return
  }

  saving.value = true
  try {
    const token = localStorage.getItem('token')
    const workflow = {
      name: workflowName.value,
      description: `${workflowName.value} 工作流`,
      layer: workflowLayer.value,
      nodes: nodes.value,
      connections: connections.value
    }

    const url = currentWorkflowId.value
      ? `/api/admin/etl-editor/workflows/${currentWorkflowId.value}`
      : '/api/admin/etl-editor/workflows'

    const response = await fetch(url, {
      method: currentWorkflowId.value ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(workflow)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '保存失败')
    }

    const result = await response.json()
    currentWorkflowId.value = result.workflow_id
    ElMessage.success(`工作流已保存 (ID: ${result.workflow_id})`)
    return result
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
    return null
  } finally {
    saving.value = false
  }
}

// 运行工作流
const runWorkflow = async () => {
  if (nodes.value.length === 0) {
    ElMessage.warning('请先添加节点')
    return
  }

  if (!currentWorkflowId.value) {
    const saved = await saveWorkflow()
    if (!saved) {
      return
    }
  }

  running.value = true
  try {
    const token = localStorage.getItem('token')

    const response = await fetch(`/api/admin/etl-editor/workflows/${currentWorkflowId.value}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        workflow_id: currentWorkflowId.value,
        variables: {
          nodes: nodes.value,
          connections: connections.value
        }
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '保存失败')
    }

    const result = await response.json()
    ElMessage.success(`工作流运行成功 (执行 ID: ${result.execution_id})`)
  } catch (error) {
    ElMessage.error('运行失败：' + error.message)
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.etl-editor-page {
  height: 100vh;
  background: #f8fafc;
}

.page-container {
  height: 100%;
}

.components-panel,
.properties-panel {
  background: #f8fafc;
  padding: 16px;
}

.canvas-area {
  background: #f1f5f9;
  padding: 16px;
  position: relative;
}

.panel-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  height: 100%;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1e293b;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
}

.component-item:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.component-icon {
  width: 16px;
  height: 16px;
  color: #3b82f6;
  flex-shrink: 0;
}

.node-icon-el {
  font-size: 16px;
  flex-shrink: 0;
}

.component-name {
  font-size: 13px;
  color: #1e293b;
}

.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 8px;
}

.workflow-controls {
  display: flex;
  gap: 8px;
}

.canvas-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 220px);
  background:
    radial-gradient(circle, #cbd5e1 1px, transparent 1px);
  background-size: 20px 20px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.node {
  position: absolute;
  width: 240px;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  transition: box-shadow 0.2s;
  z-index: 10;
}

.node.active {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.node.dragging {
  opacity: 0.8;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 6px 6px 0 0;
  font-weight: 500;
}

.node-header.datasource {
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  color: #1e40af;
}

.node-header.transform {
  background: linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%);
  color: #166534;
}

.node-header.target {
  background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
  color: #92400e;
}

.node-icon-el {
  font-size: 16px;
  flex-shrink: 0;
  color: currentColor;
}

.node-title {
  font-size: 13px;
  flex: 1;
}

.node-content {
  padding: 12px;
}

.node-config {
  max-height: 200px;
  overflow-y: auto;
}

.node-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 8px 12px;
  border-top: 1px solid #e2e8f0;
}

.connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.empty-selection {
  text-align: center;
  padding: 40px 20px;
}

.help-text {
  margin-top: 16px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.8;
  text-align: left;
}

.help-text ol {
  padding-left: 20px;
  margin: 8px 0 0 0;
}

.help-text li {
  margin-bottom: 4px;
}
</style>
