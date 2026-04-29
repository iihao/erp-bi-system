<template>
  <div class="etl-page">
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><VideoPlay /></el-icon>
            ETL 任务管理
          </span>
          <el-button type="primary" @click="runAllTasks" :loading="runningAll">
            <el-icon><VideoPlay /></el-icon>
            运行全部任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" border stripe class="task-table">
        <el-table-column prop="task_id" label="ID" width="70" />
        <el-table-column prop="task_name" label="任务名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="layer" label="分层" width="100">
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
        <el-table-column prop="last_run_at" label="上次运行" width="160" />
        <el-table-column prop="last_duration" label="耗时" width="80" />
        <el-table-column label="操作" width="200" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="runTask(row)"
              :loading="row.running"
            >
              运行
            </el-button>
            <el-button size="small" @click="viewLog(row)">
              日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 日志查看对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      :title="`运行日志 - ${currentTask?.task_name || ''}`"
      width="800px"
    >
      <div class="log-container">
        <el-table :data="logs" stripe max-height="400">
          <el-table-column prop="log_id" label="ID" width="70" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : row.status === 'running' ? '运行中' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始时间" width="160" />
          <el-table-column prop="end_time" label="结束时间" width="160" />
          <el-table-column prop="duration_seconds" label="耗时 (秒)" width="80" />
          <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
        </el-table>

        <div class="pagination">
          <el-pagination
            v-model:current-page="logPagination.page"
            v-model:page-size="logPagination.pageSize"
            :total="logPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadLogs"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Files } from '@element-plus/icons-vue'

const loading = ref(false)
const runningAll = ref(false)
const logDialogVisible = ref(false)
const currentTask = ref(null)

const tasks = ref([])
const logs = ref([])

const logPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// API 请求封装
const apiRequest = async (method, url, options = {}) => {
  const token = localStorage.getItem('token')
  const params = options.params || {}
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  })
  const config = {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  }
  delete config.params

  const requestUrl = query.toString() ? `${url}?${query.toString()}` : url

  try {
    const response = await fetch(requestUrl, config)

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || '请求失败')
    }

    const data = await response.json()
    return data
  } catch (error) {
    throw error
  }
}

const getLayerTagType = (layer) => {
  const types = { ODS: 'info', DWD: 'warning', DWS: 'success', ADS: 'danger' }
  return types[layer] || 'info'
}

const getStatusTagType = (status) => {
  const types = { success: 'success', running: 'warning', failed: 'danger', pending: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', running: '运行中', failed: '失败', pending: '等待' }
  return texts[status] || status
}

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await apiRequest('get', '/api/admin/etl/tasks')
    tasks.value = res.items.map(task => ({
      ...task,
      running: false
    }))
  } catch (error) {
    ElMessage.error(error.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 加载日志
const loadLogs = async () => {
  if (!currentTask.value) return

  try {
    const res = await apiRequest('get', `/api/admin/etl/tasks/${currentTask.value.task_id}/log`, {
      params: { page: logPagination.page, page_size: logPagination.pageSize }
    })
    logs.value = res.items
    logPagination.total = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载日志失败')
  }
}

// 运行任务
const runTask = async (task) => {
  task.running = true
  task.status = 'running'

  try {
    const result = await apiRequest('post', `/api/admin/etl/tasks/${task.task_id}/run`)

    ElMessage.success(`${task.task_name} 执行成功，耗时${result.duration}秒`)

    // 刷新任务列表
    await loadTasks()
  } catch (error) {
    ElMessage.error(`${task.task_name} 执行失败：${error.message}`)
    await loadTasks()
  }
}

// 运行全部任务
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

// 查看日志
const viewLog = (task) => {
  currentTask.value = task
  logPagination.page = 1
  logPagination.total = 0
  logDialogVisible.value = true
  loadLogs()
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.etl-page {
  padding: var(--spacing-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.log-container {
  padding: 0;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
