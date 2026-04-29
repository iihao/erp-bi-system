<template>
  <div class="realestate-dashboard">
    <el-row :gutter="20" class="kpi-row">
      <!-- 核心 KPI 卡片 -->
      <el-col :span="6">
        <el-card class="kpi-card">
          <div class="kpi-content">
            <div class="kpi-icon" style="background: #409EFF;">
              <el-icon :size="32"><House /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">总项目数</div>
              <div class="kpi-value">{{ kpi.total_projects }}</div>
              <div class="kpi-sub">覆盖 {{ kpi.total_cities || 3 }} 个城市</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="kpi-card">
          <div class="kpi-content">
            <div class="kpi-icon" style="background: #67C23A;">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">总房源数</div>
              <div class="kpi-value">{{ kpi.total_units }}</div>
              <div class="kpi-sub">可售 {{ unitsSummary.available_units || 0 }} 套</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="kpi-card">
          <div class="kpi-content">
            <div class="kpi-icon" style="background: #E6A23C;">
              <el-icon :size="32"><Money /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">累计销售额</div>
              <div class="kpi-value">¥{{ (kpi.total_sales / 10000).toFixed(0) }}万</div>
              <div class="kpi-sub">已签约 {{ kpi.total_contracts }} 套</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="kpi-card">
          <div class="kpi-content">
            <div class="kpi-icon" style="background: #F56C6C;">
              <el-icon :size="32"><Briefcase /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-label">已回款金额</div>
              <div class="kpi-value">¥{{ (kpi.total_received / 10000).toFixed(0) }}万</div>
              <div class="kpi-sub">回款率 {{ collectionRate }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 去化率排名 -->
    <el-row :gutter="20" class="content-row">
      <el-col :span="12">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon :size="18"><DataAnalysis /></el-icon> 项目去化率排名</span>
            </div>
          </template>
          <el-table :data="sellThroughRanking" stripe style="width: 100%">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="project_name" label="项目名称" />
            <el-table-column prop="sell_through_rate" label="去化率" width="120">
              <template #default="{ row }">
                <el-tag :type="getRateType(row.sell_through_rate)" size="small">
                  {{ row.sell_through_rate }}%
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 最近销售记录 -->
      <el-col :span="12">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon :size="18"><Document /></el-icon> 最近销售记录</span>
            </div>
          </template>
          <el-table :data="recentSales" stripe style="width: 100%">
            <el-table-column prop="contract_code" label="合同号" width="140" />
            <el-table-column prop="customer_name" label="客户" min-width="100" />
            <el-table-column prop="project_name" label="项目" min-width="100" />
            <el-table-column prop="unit_name" label="房号" width="80" />
            <el-table-column label="金额" width="120" align="right">
              <template #default="{ row }">
                ¥{{ (row.total_price / 10000).toFixed(0) }}万
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目业绩统计 -->
    <el-row :gutter="20" class="content-row">
      <el-col :span="24">
        <el-card class="data-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon :size="18"><Histogram /></el-icon> 项目销售业绩统计</span>
            </div>
          </template>
          <el-table :data="projectPerformance" stripe style="width: 100%">
            <el-table-column prop="project_name" label="项目名称" width="200" />
            <el-table-column prop="city" label="城市" width="100" />
            <el-table-column prop="total_units" label="总房源数" align="right" />
            <el-table-column prop="sold_count" label="已售数量" align="right" />
            <el-table-column prop="total_sales" label="销售金额" align="right">
              <template #default="{ row }">
                ¥{{ (row.total_sales / 10000).toFixed(0) }}万
              </template>
            </el-table-column>
            <el-table-column prop="sell_through_rate" label="去化率" align="right">
              <template #default="{ row }">
                <el-progress 
                  :percentage="parseFloat(row.sell_through_rate || 0)" 
                  :color="getProgressColor(row.sell_through_rate)"
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
import { ElCard, ElTable, ElTableColumn, ElTag, ElProgress, ElRow, ElCol } from 'element-plus'
import { House, TrendCharts, Money, Briefcase, DataAnalysis, Document, Histogram } from '@element-plus/icons-vue'

const kpi = ref({
  total_projects: 0,
  total_units: 0,
  total_contracts: 0,
  total_sales: 0,
  total_received: 0,
  total_receivables: 0
})

const unitsSummary = ref({})
const sellThroughRanking = ref([])
const recentSales = ref([])
const projectPerformance = ref([])

const collectionRate = computed(() => {
  if (kpi.value.total_sales === 0) return 0
  return ((kpi.value.total_received / kpi.value.total_sales) * 100).toFixed(1)
})

const getRateType = (rate) => {
  if (rate >= 80) return 'success'
  if (rate >= 50) return 'warning'
  return 'info'
}

const getProgressColor = (rate) => {
  if (rate >= 80) return '#67C23A'
  if (rate >= 50) return '#E6A23C'
  return '#F56C6C'
}

const loadDashboardData = async () => {
  try {
    const token = localStorage.getItem('token')
    const headers = { 'Authorization': `Bearer ${token}` }
    
    // 加载仪表盘概览
    const overviewRes = await fetch('/api/realestate/dashboard/overview', { headers })
    const overview = await overviewRes.json()
    
    if (overview.kpi) {
      kpi.value = overview.kpi
    }
    if (overview.recent_sales) {
      recentSales.value = overview.recent_sales
    }
    if (overview.sell_through_ranking) {
      sellThroughRanking.value = overview.sell_through_ranking
    }
    
    // 加载房源汇总
    const unitsRes = await fetch('/api/realestate/units/summary', { headers })
    const units = await unitsRes.json()
    unitsSummary.value = units
    
    // 加载项目业绩
    const performanceRes = await fetch('/api/realestate/sales/project-performance', { headers })
    const performance = await performanceRes.json()
    projectPerformance.value = performance.items || []
    
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.realestate-dashboard {
  padding: 20px;
}

.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  height: 120px;
}

.kpi-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.kpi-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.kpi-icon .el-icon {
  color: white;
}

.kpi-info {
  flex: 1;
}

.kpi-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.kpi-sub {
  font-size: 12px;
  color: #909399;
}

.content-row {
  margin-bottom: 20px;
}

.data-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  background: #f5f7fa !important;
  color: #606266;
  font-weight: 600;
}
</style>
