<template>
  <div class="etl-monitor">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap info-bg">
          <el-icon :size="24"><TrendCharts /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">ETL 监控</h1>
          <p class="page-subtitle">数据仓库各层数据量及执行状态</p>
        </div>
      </div>
      <el-button type="primary" @click="loadData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- Table stats -->
    <div class="stats-grid">
      <div class="stat-card" v-for="s in tableStats" :key="s.name">
        <div class="stat-name">{{ s.name }}</div>
        <div class="stat-layer-tag">
          <el-tag :type="getLayerType(s.layer)" size="small">{{ s.layer }}</el-tag>
        </div>
        <div class="stat-count">{{ s.count }}</div>
        <div class="stat-label">条记录</div>
      </div>
    </div>

    <!-- ETL stats -->
    <div class="etl-stats-card">
      <el-descriptions title="ETL 统计" :column="3" border>
        <el-descriptions-item label="任务总数">{{ etlStats.totalJobs }}</el-descriptions-item>
        <el-descriptions-item label="今日成功">
          <el-tag type="success" size="small">{{ etlStats.todaySuccess }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="今日失败">
          <el-tag type="danger" size="small">{{ etlStats.todayFailed }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { TrendCharts, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const tableStats = ref([])
const etlStats = reactive({ totalJobs: 0, todaySuccess: 0, todayFailed: 0 })

const apiRequest = async (method, url, options = {}) => {
  const token = localStorage.getItem('token')
  const response = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json()
}

const getLayerType = (layer) => {
  const types = { 'ODS': 'success', 'DWD': 'primary', 'DWS': 'warning', 'ADS': 'danger' }
  return types[layer] || 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    // Get ETL stats
    const statsRes = await apiRequest('get', '/api/admin/etl/stats')
    etlStats.totalJobs = statsRes.totalJobs || 0
    etlStats.todaySuccess = statsRes.todaySuccess || 0
    etlStats.todayFailed = statsRes.todayFailed || 0

    // Get table row counts via schema API
    const schemaRes = await apiRequest('get', '/ai-query/schema')
    const keyTables = [
      { name: 'ods_room', layer: 'ODS', label: 'ODS 房源' },
      { name: 'ods_contract', layer: 'ODS', label: 'ODS 合同' },
      { name: 'dwd_room_detail', layer: 'DWD', label: 'DWD 房间明细' },
      { name: 'dwd_trade_detail', layer: 'DWD', label: 'DWD 交易明细' },
      { name: 'dws_sales_payment_fact', layer: 'DWS', label: 'DWS 销售回款' },
      { name: 'ads_sales_dashboard', layer: 'ADS', label: 'ADS 销售仪表盘' },
      { name: 'ads_finance_dashboard', layer: 'ADS', label: 'ADS 财务仪表盘' },
      { name: 'ads_szl_dashboard', layer: 'ADS', label: 'ADS 损益仪表盘' },
    ]
    tableStats.value = keyTables
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.etl-monitor {
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

.stats-grid {
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

.stat-name {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 4px;
}

.stat-layer-tag {
  margin-bottom: 8px;
}

.stat-count {
  font-size: 36px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 13px;
  color: #94a3b8;
}

.etl-stats-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
