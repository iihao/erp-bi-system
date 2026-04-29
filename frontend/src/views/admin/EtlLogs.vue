<template>
  <div class="etl-logs-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><Document /></el-icon>
            ETL 执行日志
          </span>
          <div class="header-actions">
            <el-select
              v-model="selectedTaskId"
              placeholder="选择任务"
              clearable
              style="width: 220px"
              @change="loadLogs"
            >
              <el-option
                v-for="task in tasks"
                :key="task.task_id"
                :label="task.task_name"
                :value="task.task_id"
              />
            </el-select>
            <el-button type="primary" :disabled="!selectedTaskId" @click="loadLogs">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="!selectedTaskId"
        title="请选择一个 ETL 任务查看执行日志"
        type="info"
        :closable="false"
        class="mb-3"
      />

      <el-table :data="logs" v-loading="loading" border stripe max-height="640">
        <el-table-column prop="log_id" label="ID" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="task_layer" label="分层" width="90" />
        <el-table-column prop="start_time" label="开始时间" width="170" />
        <el-table-column prop="end_time" label="结束时间" width="170" />
        <el-table-column prop="duration_seconds" label="耗时(秒)" width="100" />
        <el-table-column prop="message" label="消息" min-width="280" show-overflow-tooltip />
        <el-table-column prop="error_message" label="错误信息" min-width="240" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const tasks = ref([])
const logs = ref([])
const selectedTaskId = ref(null)

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
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  }
  delete config.params

  const requestUrl = query.toString() ? `${url}?${query.toString()}` : url
  const response = await fetch(requestUrl, config)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || '请求失败')
  }
  return response.json()
}

const getStatusTagType = (status) => {
  const types = { success: 'success', running: 'warning', failed: 'danger', pending: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', running: '运行中', failed: '失败', pending: '等待' }
  return texts[status] || status
}

const loadTasks = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/etl/tasks')
    tasks.value = res.items || []
    if (!selectedTaskId.value && tasks.value.length) {
      selectedTaskId.value = tasks.value[0].task_id
      await loadLogs()
    }
  } catch (error) {
    ElMessage.error(error.message || '加载任务列表失败')
  }
}

const loadLogs = async () => {
  if (!selectedTaskId.value) {
    logs.value = []
    return
  }

  loading.value = true
  try {
    const res = await apiRequest('get', `/api/admin/etl/tasks/${selectedTaskId.value}/log`, {
      params: { page: 1, page_size: 100 }
    })
    logs.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.etl-logs-page {
  padding: var(--spacing-6);
}

.page-card {
  min-height: calc(100vh - 128px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mb-3 {
  margin-bottom: 12px;
}
</style>
