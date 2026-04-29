<template>
  <div class="etl-task-container">
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>📦 ETL 任务管理</span>
          <el-button type="primary" @click="runAllTasks" :loading="running">
            <svg class="button-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            运行全部任务
          </el-button>
        </div>
      </template>

      <!-- 任务列表 -->
      <el-table :data="tasks" border stripe class="task-table">
        <el-table-column prop="name" label="任务名称" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="layer" label="数仓分层" width="100">
          <template #default="{ row }">
            <el-tag :type="getLayerTagType(row.layer)">{{ row.layer }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastRun" label="上次运行" width="180" />
        <el-table-column prop="duration" label="耗时" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="runTask(row)"
              :loading="row.running"
            >
              运行
            </el-button>
            <el-button
              size="small"
              @click="viewLog(row)"
            >
              日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 运行日志 -->
      <div v-if="showLog" class="log-section">
        <el-card class="log-card">
          <template #header>
            <div class="log-header">
              <span>📋 运行日志 - {{ currentTask?.name }}</span>
              <el-button size="small" @click="showLog = false">关闭</el-button>
            </div>
          </template>
          <pre class="log-content">{{ logContent }}</pre>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const running = ref(false)
const showLog = ref(false)
const currentTask = ref(null)
const logContent = ref('')

const tasks = reactive([
  {
    id: 1,
    name: 'ODS 数据抽取',
    description: '从 MySQL 业务库抽取原始数据到 ODS 层',
    layer: 'ODS',
    status: 'success',
    lastRun: '2026-03-14 10:30:00',
    duration: '2.3s',
    running: false,
    script: 'ods_extract.py'
  },
  {
    id: 2,
    name: 'DWD 数据清洗',
    description: '清洗和标准化 ODS 层数据',
    layer: 'DWD',
    status: 'success',
    lastRun: '2026-03-14 10:31:00',
    duration: '3.1s',
    running: false,
    script: 'dwd_clean.py'
  },
  {
    id: 3,
    name: 'DWS 数据聚合',
    description: '轻度聚合生成汇总数据',
    layer: 'DWS',
    status: 'pending',
    lastRun: '-',
    duration: '-',
    running: false,
    script: 'dws_aggregate.py'
  },
  {
    id: 4,
    name: 'ADS 报表生成',
    description: '生成面向应用的报表指标',
    layer: 'ADS',
    status: 'pending',
    lastRun: '-',
    duration: '-',
    running: false,
    script: 'ads_report.py'
  }
])

const getLayerTagType = (layer) => {
  const types = {
    'ODS': 'info',
    'DWD': 'warning',
    'DWS': 'success',
    'ADS': 'danger'
  }
  return types[layer] || 'info'
}

const getStatusTagType = (status) => {
  const types = {
    'success': 'success',
    'running': 'warning',
    'failed': 'danger',
    'pending': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'success': '成功',
    'running': '运行中',
    'failed': '失败',
    'pending': '等待'
  }
  return texts[status] || status
}

const runTask = async (task) => {
  task.running = true
  task.status = 'running'
  
  logContent.value = `[${new Date().toLocaleString()}] 开始执行任务：${task.name}\n`
  showLog.value = true
  currentTask.value = task

  try {
    // 模拟任务执行
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    logContent.value += `[${new Date().toLocaleString()}] 连接数据库...\n`
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    logContent.value += `[${new Date().toLocaleString()}] 执行 ${task.script}...\n`
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    logContent.value += `[${new Date().toLocaleString()}] 任务执行成功!\n`
    
    task.status = 'success'
    task.lastRun = new Date().toLocaleString()
    task.duration = (Math.random() * 3 + 1).toFixed(1) + 's'
    
    ElMessage.success(`${task.name} 执行成功`)
  } catch (error) {
    task.status = 'failed'
    logContent.value += `[${new Date().toLocaleString()}] 任务执行失败：${error.message}\n`
    ElMessage.error(`${task.name} 执行失败`)
  } finally {
    task.running = false
  }
}

const runAllTasks = async () => {
  running.value = true
  
  for (const task of tasks) {
    if (!task.running) {
      await runTask(task)
    }
  }
  
  running.value = false
  ElMessage.success('全部任务执行完成')
}

const viewLog = (task) => {
  currentTask.value = task
  logContent.value = `[${task.lastRun}] 查看 ${task.name} 的运行日志...\n`
  logContent.value += `脚本：${task.script}\n`
  logContent.value += `耗时：${task.duration}\n`
  logContent.value += `状态：${getStatusText(task.status)}\n`
  showLog.value = true
}
</script>

<style scoped>
.etl-task-container {
  padding: 24px;
  background-color: var(--bg-body);
  min-height: 100vh;
}

.task-card {
  max-width: 1400px;
  margin: 0 auto;
  border: 1px solid var(--border);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.task-table {
  margin-top: 10px;
}

.task-table :deep(.el-table__header th) {
  background-color: #f8fafc;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 13px;
}

.task-table :deep(.el-table__row:hover) {
  background-color: #f0f7ff;
}

.task-table :deep(.el-table__cell) {
  padding: 12px 16px;
  font-size: 13px;
}

.log-section {
  margin-top: 20px;
}

.log-card {
  border: 1px solid var(--border);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-header span {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.log-content {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: var(--radius);
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  border: 1px solid var(--border);
}

/* 标签样式优化 */
:deep(.el-tag) {
  font-weight: 500;
  padding: 4px 12px;
}

:deep(.el-tag--info) {
  background-color: rgba(66, 153, 225, 0.1);
  border-color: rgba(66, 153, 225, 0.3);
  color: var(--primary-light);
}

:deep(.el-tag--warning) {
  background-color: rgba(214, 158, 46, 0.1);
  border-color: rgba(214, 158, 46, 0.3);
  color: var(--warning);
}

:deep(.el-tag--success) {
  background-color: rgba(56, 161, 105, 0.1);
  border-color: rgba(56, 161, 105, 0.3);
  color: var(--success);
}

:deep(.el-tag--danger) {
  background-color: rgba(229, 62, 62, 0.1);
  border-color: rgba(229, 62, 62, 0.3);
  color: var(--danger);
}

.button-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
  color: currentColor;
  stroke: currentColor;
  fill: none;
}
</style>
