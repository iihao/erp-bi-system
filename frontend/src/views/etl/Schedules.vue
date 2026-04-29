<template>
  <div class="etl-schedules">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap info-bg">
          <el-icon :size="24"><Clock /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">ETL 调度配置</h1>
          <p class="page-subtitle">配置定时任务的 Cron 计划</p>
        </div>
      </div>
    </div>

    <div class="table-card">
      <el-table :data="schedules" v-loading="loading" border stripe>
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column prop="cron_expression" label="Cron 表达式" width="160" />
        <el-table-column prop="is_enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次运行" width="170" />
        <el-table-column prop="next_run_at" label="下次运行" width="170" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="toggleEnabled(row)">
              {{ row.is_enabled ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="schedules.length === 0 && !loading" class="empty-hint">
        <el-empty description="暂无调度配置">
          <p class="hint-text">在任务管理中可为任务开启定时调度</p>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'

const loading = ref(false)
const schedules = ref([])

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

const loadSchedules = async () => {
  loading.value = true
  try {
    const res = await apiRequest('get', '/api/admin/etl/schedules')
    schedules.value = res.items || []
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
}

const toggleEnabled = async (row) => {
  try {
    await apiRequest('put', `/api/admin/etl/schedules/${row.schedule_id}`, {
      body: JSON.stringify({ is_enabled: !row.is_enabled })
    })
    ElMessage.success(`已${row.is_enabled ? '禁用' : '启用'}调度`)
    await loadSchedules()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadSchedules)
</script>

<style scoped>
.etl-schedules {
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

.empty-hint {
  padding: 40px 0;
}

.hint-text {
  color: #94a3b8;
  font-size: 13px;
}
</style>
