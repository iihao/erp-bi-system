<template>
  <div class="etl-tasks">
    <!-- Page header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap info-bg">
          <el-icon :size="24"><Connection /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">ETL 任务管理</h1>
          <p class="page-subtitle">数据仓库 ODS→DWD→DWS→ADS 数据流转</p>
        </div>
      </div>
      <el-button type="primary" @click="runAllTasks" :loading="runningAll" size="large">
        <el-icon><VideoPlay /></el-icon>
        运行全部
      </el-button>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-label">任务总数</div>
        <div class="stat-value">{{ tasks.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日成功</div>
        <div class="stat-value success">{{ stats.todaySuccess }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日失败</div>
        <div class="stat-value error">{{ stats.todayFailed }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">成功率</div>
        <div class="stat-value warning">{{ stats.successRate }}%</div>
      </div>
    </div>

    <!-- Task table -->
    <div class="table-card">
      <el-table :data="tasks" v-loading="loading" border stripe>
        <el-table-column prop="task_id" label="ID" width="70" />
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column prop="layer" label="层级" width="100">
          <template #default="{ row }">
            <el-tag :type="getLayerType(row.layer)">{{ row.layer }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'info'" size="small">
              {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : '等待' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最后执行" width="180" />
        <el-table-column prop="last_duration" label="耗时" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="runTask(row)" :loading="row.running">
              <el-icon><VideoPlay /></el-icon>
              执行
            </el-button>
            <el-button size="small" type="primary" link @click="viewLog(row)">
              <el-icon><Document /></el-icon>
              日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Log dialog -->
    <el-dialog v-model="logVisible" title="执行日志" width="700px">
      <el-table :data="logs" stripe v-loading="logLoading">
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
              {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : '运行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="170" />
        <el-table-column prop="end_time" label="结束时间" width="170" />
        <el-table-column prop="duration_seconds" label="耗时" width="80">
          <template #default="{ row }">
            {{ row.duration_seconds }}s
          </template>
        </el-table-column>
        <el-table-column label="消息" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.message || row.error_message || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, VideoPlay, Document } from '@element-plus/icons-vue'

const loading = ref(false)
const runningAll = ref(false)
const logVisible = ref(false)
const logLoading = ref(false)
const currentTask = ref(null)
const logs = ref([])

const tasks = ref([])
const stats = reactive({
  todaySuccess: 0,
  todayFailed: 0,
  successRate: 0
})

const apiRequest = async (method, url, options = {}) => {
  const token = localStorage.getItem('token')
  const config = {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  }

  if (config.params) {
    const qs = new URLSearchParams(config.params).toString()
    url = `${url}?${qs}`
    delete config.params
  }

  const response = await fetch(url, config)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text)
  }
  return response.json()
}

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await apiRequest('get', '/api/admin/etl/tasks')
    tasks.value = (res.items || []).map(t => ({ ...t, running: false }))
  } catch (e) {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/etl/stats')
    stats.todaySuccess = res.todaySuccess || 0
    stats.todayFailed = res.todayFailed || 0
    stats.successRate = res.successRate || 0
  } catch (e) {
    // ignore
  }
}

const getLayerType = (layer) => {
  const types = { 'ODS': 'success', 'DWD': 'primary', 'DWS': 'warning', 'ADS': 'danger' }
  return types[layer] || 'info'
}

const runTask = async (task) => {
  task.running = true
  try {
    const res = await apiRequest('post', `/api/admin/etl/tasks/${task.task_id}/run`)
    ElMessage.success(`${task.task_name} 执行成功，影响 ${res.affected_rows} 行`)
    await loadTasks()
    await loadStats()
  } catch (e) {
    const msg = e.message ? JSON.parse(e.message) : {}
    ElMessage.error(`执行失败：${msg.detail || msg.message || '未知错误'}`)
    await loadTasks()
  } finally {
    task.running = false
  }
}

const runAllTasks = async () => {
  runningAll.value = true
  for (const task of tasks.value) {
    if (!task.running) {
      await runTask(task)
    }
  }
  runningAll.value = false
  ElMessage.success('全部任务执行完成')
}

const viewLog = async (task) => {
  currentTask.value = task
  logVisible.value = true
  logLoading.value = true
  try {
    const res = await apiRequest('get', `/api/admin/etl/tasks/${task.task_id}/log`, {
      params: { page: 1, page_size: 50 }
    })
    logs.value = res.items || []
  } catch (e) {
    logs.value = []
  } finally {
    logLoading.value = false
  }
}

onMounted(() => {
  loadTasks()
  loadStats()
})
</script>

<style scoped>
.etl-tasks {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 12px;
  padding: 20px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-wrap {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  color: #fff;
}

.header-text .page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.header-text .page-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.stat-value.success { color: #16a34a; }
.stat-value.error { color: #dc2626; }
.stat-value.warning { color: #64748b; }

.table-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

@media (max-width: 768px) {
  .etl-tasks { padding: 16px; }
  .page-header { flex-direction: column; gap: 16px; }
  .stats-section { grid-template-columns: repeat(2, 1fr); }
}
</style>
