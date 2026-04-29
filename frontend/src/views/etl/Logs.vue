<template>
  <div class="etl-logs">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap info-bg">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">ETL 执行日志</h1>
          <p class="page-subtitle">查看任务执行历史和详细日志</p>
        </div>
      </div>
    </div>

    <div class="table-card">
      <el-table :data="logs" v-loading="loading" border stripe>
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column prop="task_layer" label="层级" width="80">
          <template #default="{ row }">
            <el-tag :type="getLayerType(row.task_layer)" size="small">{{ row.task_layer }}</el-tag>
          </template>
        </el-table-column>
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
            {{ row.duration_seconds ?? '-' }}s
          </template>
        </el-table-column>
        <el-table-column label="消息" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else>{{ row.message || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadLogs"
          @size-change="loadLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Document } from '@element-plus/icons-vue'

const loading = ref(false)
const logs = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

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
  const response = await fetch(url, config)
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

const getLayerType = (layer) => {
  const types = { 'ODS': 'success', 'DWD': 'primary', 'DWS': 'warning', 'ADS': 'danger' }
  return types[layer] || 'info'
}

const loadLogs = async () => {
  loading.value = true
  try {
    // Get all tasks first
    const tasksRes = await apiRequest('get', '/api/admin/etl/tasks')
    const allLogs = []
    for (const task of tasksRes.items || []) {
      try {
        const logRes = await apiRequest('get', `/api/admin/etl/tasks/${task.task_id}/log`, {
          params: { page: 1, page_size: pageSize.value }
        })
        for (const log of logRes.items || []) {
          allLogs.push(log)
        }
      } catch (e) { /* skip */ }
    }
    allLogs.sort((a, b) => b.log_id - a.log_id)
    total.value = allLogs.length
    const start = (page.value - 1) * pageSize.value
    logs.value = allLogs.slice(start, start + pageSize.value)
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.etl-logs {
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

.table-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  overflow: hidden;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.error-text {
  color: #ef4444;
}
</style>
