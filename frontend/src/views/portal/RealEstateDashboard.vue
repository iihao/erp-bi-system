<template>
  <div class="realestate-dashboard">
    <section class="hero-card">
      <div class="hero-copy">
        <div class="eyebrow">行业看板 / 地产经营分析</div>
        <h1>地产销售经营大屏</h1>
        <p>聚焦项目去化、销售回款和重点楼盘表现，快速掌握经营态势。</p>
      </div>
      <div class="hero-pills">
        <div class="pill">
          <span class="pill-label">平均去化率</span>
          <strong>{{ averageSellThrough }}%</strong>
        </div>
        <div class="pill">
          <span class="pill-label">回款率</span>
          <strong>{{ collectionRate }}%</strong>
        </div>
        <div class="pill">
          <span class="pill-label">重点城市</span>
          <strong>{{ kpi.total_cities || 0 }}</strong>
        </div>
      </div>
    </section>

    <el-row :gutter="20" class="kpi-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="kpi-card kpi-blue" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 21h18M5 21V7l8-4 8 4v14"/>
                <path d="M9 14h6"/>
              </svg>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">总项目数</div>
              <div class="kpi-value">{{ kpi.total_projects }}</div>
              <div class="kpi-sub">覆盖 {{ kpi.total_cities || 0 }} 个城市</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="kpi-card kpi-green" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3v18h18M7 16l4-4 4 4 5-6"/>
              </svg>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">总房源数</div>
              <div class="kpi-value">{{ kpi.total_units }}</div>
              <div class="kpi-sub">可售 {{ unitsSummary.available_units || 0 }} 套</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="kpi-card kpi-gold" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 1 1 0 7H6"/>
              </svg>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">累计销售额</div>
              <div class="kpi-value">¥{{ formatWan(kpi.total_sales) }}</div>
              <div class="kpi-sub">已签约 {{ kpi.total_contracts }} 套</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="kpi-card kpi-coral" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">已回款金额</div>
              <div class="kpi-value">¥{{ formatWan(kpi.total_received) }}</div>
              <div class="kpi-sub">回款率 {{ collectionRate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :lg="12">
        <el-card class="panel-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div>
                <div class="card-eyebrow">排名</div>
                <span class="card-title">项目去化率排名</span>
              </div>
              <el-tag type="info" effect="plain">Top {{ sellThroughRanking.length }}</el-tag>
            </div>
          </template>
          <el-table :data="sellThroughRanking" stripe class="premium-table">
            <el-table-column type="index" label="排名" width="72" />
            <el-table-column prop="project_name" label="项目名称" min-width="140" />
            <el-table-column prop="city" label="城市" width="100" />
            <el-table-column prop="sell_through_rate" label="去化率" width="160">
              <template #default="{ row }">
                <div class="rate-cell">
                  <el-progress :percentage="parseFloat(row.sell_through_rate || 0)" :color="getProgressColor(row.sell_through_rate)" :stroke-width="10" />
                  <span class="rate-text">{{ row.sell_through_rate }}%</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="panel-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div>
                <div class="card-eyebrow">成交</div>
                <span class="card-title">最近销售记录</span>
              </div>
              <el-tag type="success" effect="plain">实时更新</el-tag>
            </div>
          </template>
          <el-table :data="recentSales" stripe class="premium-table">
            <el-table-column prop="contract_code" label="合同号" width="140" />
            <el-table-column prop="customer_name" label="客户" min-width="100" />
            <el-table-column prop="project_name" label="项目" min-width="120" />
            <el-table-column prop="unit_name" label="房号" width="90" />
            <el-table-column label="金额" width="120" align="right">
              <template #default="{ row }">
                {{ formatCurrency(row.total_price) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="24">
        <el-card class="panel-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div>
                <div class="card-eyebrow">经营</div>
                <span class="card-title">项目销售业绩统计</span>
              </div>
              <el-tag type="warning" effect="plain">全量项目</el-tag>
            </div>
          </template>
          <el-table :data="projectPerformance" stripe class="premium-table">
            <el-table-column prop="project_name" label="项目名称" min-width="200" />
            <el-table-column prop="city" label="城市" width="100" />
            <el-table-column prop="total_units" label="总房源数" width="100" align="right" />
            <el-table-column prop="sold_count" label="已售数量" width="100" align="right" />
            <el-table-column prop="total_sales" label="销售金额" width="140" align="right">
              <template #default="{ row }">
                {{ formatCurrency(row.total_sales) }}
              </template>
            </el-table-column>
            <el-table-column prop="sell_through_rate" label="去化率" width="180" align="right">
              <template #default="{ row }">
                <el-progress
                  :percentage="parseFloat(row.sell_through_rate || 0)"
                  :color="getProgressColor(row.sell_through_rate)"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const kpi = ref({
  total_projects: 0,
  total_units: 0,
  total_contracts: 0,
  total_sales: 0,
  total_received: 0,
  total_receivables: 0,
  total_cities: 0
})

const unitsSummary = ref({})
const sellThroughRanking = ref([])
const recentSales = ref([])
const projectPerformance = ref([])

const collectionRate = computed(() => {
  if (!kpi.value.total_sales) return '0.0'
  return ((kpi.value.total_received / kpi.value.total_sales) * 100).toFixed(1)
})

const averageSellThrough = computed(() => {
  if (!sellThroughRanking.value.length) return '0.0'
  const total = sellThroughRanking.value.reduce((sum, item) => sum + parseFloat(item.sell_through_rate || 0), 0)
  return (total / sellThroughRanking.value.length).toFixed(1)
})

const getProgressColor = (rate) => {
  const value = parseFloat(rate || 0)
  if (value >= 80) return '#16a34a'
  if (value >= 50) return '#f59e0b'
  return '#ef4444'
}

const formatWan = (value) => {
  const num = Number(value || 0)
  if (!num) return '0'
  return (num / 10000).toFixed(0) + '万'
}

const formatCurrency = (value) => {
  const num = Number(value || 0)
  if (!num) return '¥0'
  return `¥${formatWan(num)}`
}

const loadDashboardData = async () => {
  try {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    const overviewRes = await fetch('/api/realestate/dashboard/overview', { headers })
    const overview = await overviewRes.json()
    if (overview.kpi) kpi.value = { ...kpi.value, ...overview.kpi }
    if (overview.recent_sales) recentSales.value = overview.recent_sales
    if (overview.sell_through_ranking) sellThroughRanking.value = overview.sell_through_ranking

    const unitsRes = await fetch('/api/realestate/units/summary', { headers })
    unitsSummary.value = await unitsRes.json()

    const performanceRes = await fetch('/api/realestate/sales/project-performance', { headers })
    const performance = await performanceRes.json()
    projectPerformance.value = performance.items || []
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载地产看板失败')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.realestate-dashboard {
  padding: 4px 0 12px;
  max-width: 1600px;
  margin: 0 auto;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: end;
  padding: 28px 28px 24px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.95) 0%, rgba(219, 234, 254, 0.96) 48%, rgba(191, 219, 254, 0.9) 100%);
  border: 1px solid rgba(37, 99, 235, 0.14);
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.08);
  margin-bottom: 20px;
}

.hero-copy h1 {
  margin: 6px 0 10px;
  font-size: 30px;
  line-height: 1.1;
  color: #0f172a;
}

.hero-copy p {
  margin: 0;
  color: #475569;
  font-size: 14px;
  max-width: 640px;
}

.eyebrow,
.card-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
  font-weight: 700;
}

.hero-pills {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.pill {
  min-width: 160px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.16);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.05);
}

.pill-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.pill strong {
  font-size: 20px;
  color: #0f172a;
}

.kpi-row,
.content-row {
  margin-bottom: 20px;
}

.kpi-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  overflow: hidden;
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.16);
}

.kpi-icon svg {
  width: 28px;
  height: 28px;
}

.kpi-blue .kpi-icon { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); }
.kpi-green .kpi-icon { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
.kpi-gold .kpi-icon { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.kpi-coral .kpi-icon { background: linear-gradient(135deg, #f97316 0%, #ef4444 100%); }

.kpi-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1;
}

.kpi-sub {
  margin-top: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.panel-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
}

.panel-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.card-title {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin-top: 2px;
}

.premium-table {
  --el-table-header-bg-color: #f8fafc;
  --el-table-border-color: rgba(148, 163, 184, 0.14);
}

.premium-table :deep(.el-table__header-wrapper th) {
  background: #f8fafc !important;
  color: #475569;
  font-weight: 700;
}

.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rate-text {
  min-width: 46px;
  font-size: 12px;
  color: #475569;
  text-align: right;
}

@media (max-width: 1024px) {
  .hero-card {
    flex-direction: column;
    align-items: start;
  }
}

@media (max-width: 768px) {
  .hero-card {
    padding: 22px 20px;
    border-radius: 18px;
  }

  .hero-copy h1 {
    font-size: 24px;
  }

  .pill {
    min-width: 140px;
  }
}
</style>
