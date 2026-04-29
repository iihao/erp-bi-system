<template>
  <div class="monitor-page">
    <!-- 系统信息卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon cpu">
              <el-icon :size="32"><Cpu /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">CPU 使用率</div>
              <div class="metric-value">{{ metrics.cpu_usage }}%</div>
            </div>
          </div>
          <el-progress :percentage="metrics.cpu_usage" :color="getMetricColor(metrics.cpu_usage)" />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon memory">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">内存使用率</div>
              <div class="metric-value">{{ metrics.memory_usage }}%</div>
              <div class="metric-detail">
                {{ metrics.memory_used }}GB / {{ metrics.memory_total !== undefined ? metrics.memory_total + 'GB' : '' }}
              </div>
            </div>
          </div>
          <el-progress :percentage="metrics.memory_usage" :color="getMetricColor(metrics.memory_usage)" />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon disk">
              <el-icon :size="32"><Monitor /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">磁盘使用率</div>
              <div class="metric-value">{{ metrics.disk_usage }}%</div>
              <div class="metric-detail">
                {{ metrics.disk_used }}GB / {{ metrics.disk_total !== undefined ? metrics.disk_total + 'GB' : '' }}
              </div>
            </div>
          </div>
          <el-progress :percentage="metrics.disk_usage" :color="getMetricColor(metrics.disk_usage)" />
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon network">
              <el-icon :size="32"><Coin /></el-icon>
            </div>
            <div class="metric-info">
              <div class="metric-label">网络流量</div>
              <div class="metric-value">
                <span class="upload">↑{{ metrics.network_sent }}MB</span>
                <span class="download">↓{{ metrics.network_recv }}MB</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息详情 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">
            <el-icon :size="18"><Cpu /></el-icon>
            系统信息
          </span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="主机名">{{ systemInfo.hostname }}</el-descriptions-item>
            <el-descriptions-item label="操作系统">{{ systemInfo.os_name }} {{ systemInfo.os_version }}</el-descriptions-item>
            <el-descriptions-item label="平台架构">{{ systemInfo.platform }}</el-descriptions-item>
            <el-descriptions-item label="CPU 核心数">{{ systemInfo.cpu_count }} 核</el-descriptions-item>
            <el-descriptions-item label="处理器">{{ systemInfo.processor }}</el-descriptions-item>
            <el-descriptions-item label="Python 版本">{{ systemInfo.python_version }}</el-descriptions-item>
            <el-descriptions-item label="运行时间">{{ systemInfo.uptime }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">
            <el-icon :size="18"><Connection /></el-icon>
            服务状态
          </span>
          </template>
          <el-table :data="services" stripe>
            <el-table-column prop="service_name" label="服务名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'running' ? 'success' : row.status === 'error' ? 'danger' : 'warning'">
                  {{ row.status === 'running' ? '运行中' : row.status === 'error' ? '错误' : '停止' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="port" label="端口" width="80" />
            <el-table-column prop="message" label="状态说明" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统日志 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><Document /></el-icon>
            系统日志
          </span>
          <div class="header-actions">
            <el-select v-model="logLevel" placeholder="日志级别" clearable style="width: 120px" @change="loadLogs">
              <el-option label="DEBUG" value="DEBUG" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-input
              v-model="logKeyword"
              placeholder="搜索日志..."
              clearable
              style="width: 200px; margin-left: 10px"
              @keyup.enter="loadLogs"
            />
            <el-button type="primary" @click="loadLogs" style="margin-left: 10px">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" v-loading="logsLoading" stripe max-height="400">
        <el-table-column prop="log_id" label="ID" width="70" />
        <el-table-column prop="log_level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getLogLevelType(row.log_level)" size="small">{{ row.log_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="160" />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="logPagination.page"
          v-model:page-size="logPagination.pageSize"
          :total="logPagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Cpu, Connection, Coin, Refresh, Document } from '@element-plus/icons-vue'

const metrics = reactive({
  cpu_usage: 0,
  memory_usage: 0,
  memory_used: 0,
  memory_available: 0,
  disk_usage: 0,
  disk_used: 0,
  disk_free: 0,
  network_sent: 0,
  network_recv: 0
})

const systemInfo = reactive({
  hostname: '',
  os_name: '',
  os_version: '',
  platform: '',
  architecture: '',
  processor: '',
  cpu_count: 0,
  memory_total: 0,
  disk_total: 0,
  python_version: '',
  uptime: ''
})

const services = ref([])
const logs = ref([])
const logsLoading = ref(false)
const logLevel = ref('')
const logKeyword = ref('')

const logPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// API 请求封装
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

  try {
    const response = await fetch(url, config)

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

const getMetricColor = (value) => {
  if (value < 60) return '#67c23a'
  if (value < 80) return '#e6a23c'
  return '#f56c6c'
}

const getLogLevelType = (level) => {
  const types = { DEBUG: 'info', INFO: 'success', WARNING: 'warning', ERROR: 'danger' }
  return types[level] || 'info'
}

// 加载系统指标
const loadMetrics = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/monitor/metrics')
    Object.assign(metrics, res)
  } catch (error) {
    console.error('加载指标失败', error)
  }
}

// 加载系统信息
const loadSystemInfo = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/monitor/system')
    Object.assign(systemInfo, res)
  } catch (error) {
    console.error('加载系统信息失败', error)
  }
}

// 加载服务状态
const loadServices = async () => {
  try {
    services.value = await apiRequest('get', '/api/admin/monitor/services')
  } catch (error) {
    console.error('加载服务状态失败', error)
  }
}

// 加载日志
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const params = {
      page: logPagination.page,
      page_size: logPagination.pageSize,
      level: logLevel || undefined,
      keyword: logKeyword || undefined
    }
    const res = await apiRequest('get', '/api/admin/monitor/logs', { params })
    logs.value = res.items
    logPagination.total = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 定时刷新指标
let metricsInterval = null
onMounted(() => {
  loadMetrics()
  loadSystemInfo()
  loadServices()
  loadLogs()

  // 每 10 秒刷新一次指标
  metricsInterval = setInterval(() => {
    loadMetrics()
    loadServices()
  }, 10000)
})

// 清理定时器
onUnmounted(() => {
  if (metricsInterval) {
    clearInterval(metricsInterval)
  }
})
</script>

<style scoped>
.monitor-page {
  padding: var(--spacing-6);
}

.mb-4 {
  margin-bottom: 20px;
}

.metric-card {
  text-align: center;
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.metric-icon.cpu {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-icon.memory {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-icon.disk {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-icon.network {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-info {
  text-align: left;
  flex: 1;
}

.metric-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.metric-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.upload {
  color: #67c23a;
  font-size: 14px;
  margin-right: 12px;
}

.download {
  color: #409eff;
  font-size: 14px;
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

.header-actions {
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
