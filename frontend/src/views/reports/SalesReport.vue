<template>
  <div class="sales-report">
    <header class="header">
      <h1>销售报表</h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading" type="primary">
          <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          刷新数据
        </el-button>
        <el-button @click="handleLogout" type="danger">
          <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          退出登录
        </el-button>
      </div>
    </header>

    <main class="content">
      <!-- KPI 卡片 -->
      <el-row :gutter="20" class="kpi-row">
        <el-col :span="6" v-for="(kpi, index) in kpiData" :key="index">
          <el-card class="kpi-card" shadow="hover">
            <template #header>
              <span class="kpi-title">{{ kpi.kpi_name }}</span>
            </template>
            <div class="kpi-value">
              <span class="number">{{ formatKpiValue(kpi.kpi_value) }}</span>
              <span class="unit">{{ kpi.unit }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" class="chart-row">
        <!-- 销售趋势图 -->
        <el-col :span="16">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">销售趋势（月度）</span>
                <el-select v-model="trendMonths" @change="loadSalesTrend" size="small" style="width: 120px">
                  <el-option label="近 6 月" :value="6" />
                  <el-option label="近 12 月" :value="12" />
                  <el-option label="近 24 月" :value="24" />
                </el-select>
              </div>
            </template>
            <div ref="trendChartRef" class="chart" style="height: 400px"></div>
          </el-card>
        </el-col>

        <!-- 品类分布 -->
        <el-col :span="8">
          <el-card class="chart-card">
            <template #header>
              <span class="card-title">品类销售分布</span>
            </template>
            <div ref="categoryChartRef" class="chart" style="height: 400px"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="chart-row">
        <!-- 产品排行榜 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">产品销量排行榜</span>
                <el-select v-model="rankingLimit" @change="loadProductRanking" size="small" style="width: 100px">
                  <el-option label="Top 5" :value="5" />
                  <el-option label="Top 10" :value="10" />
                  <el-option label="Top 20" :value="20" />
                </el-select>
              </div>
            </template>
            <div ref="rankingChartRef" class="chart" style="height: 350px"></div>
          </el-card>
        </el-col>

        <!-- 客户分析 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <span class="card-title">客户类型分析</span>
            </template>
            <div ref="customerChartRef" class="chart" style="height: 350px"></div>
          </el-card>
        </el-col>
      </el-row>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)

// 图表实例
let trendChart = null
let categoryChart = null
let rankingChart = null
let customerChart = null

// 图表 DOM 引用
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const rankingChartRef = ref(null)
const customerChartRef = ref(null)

// 数据
const kpiData = ref([])
const salesTrendData = ref([])
const categoryData = ref([])
const productRankingData = ref([])
const customerData = ref([])

// 配置
const trendMonths = ref(12)
const rankingLimit = ref(10)

// API 基础 URL - 使用相对路径，通过 Vite 代理转发
const API_BASE = '/api/reports'

// 获取 token
const getToken = () => {
  return localStorage.getItem('token')
}

// Axios 实例
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 token
apiClient.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

// 加载 KPI 数据
const loadKpiSummary = async () => {
  try {
    const data = await apiClient.get('/sales/kpi-summary')
    kpiData.value = data
  } catch (error) {
    console.error('加载 KPI 数据失败:', error)
    ElMessage.error('加载 KPI 数据失败')
  }
}

// 加载销售趋势数据
const loadSalesTrend = async () => {
  try {
    const data = await apiClient.get(`/sales/trend?months=${trendMonths.value}`)
    salesTrendData.value = data
    renderTrendChart()
  } catch (error) {
    console.error('加载销售趋势数据失败:', error)
    ElMessage.error('加载销售趋势数据失败')
  }
}

// 加载品类分析数据
const loadCategoryAnalysis = async () => {
  try {
    const data = await apiClient.get('/sales/category-analysis')
    categoryData.value = data
    renderCategoryChart()
  } catch (error) {
    console.error('加载品类分析数据失败:', error)
    ElMessage.error('加载品类分析数据失败')
  }
}

// 加载产品排行榜数据
const loadProductRanking = async () => {
  try {
    const data = await apiClient.get(`/sales/product-ranking?limit=${rankingLimit.value}`)
    productRankingData.value = data
    renderRankingChart()
  } catch (error) {
    console.error('加载产品排行榜数据失败:', error)
    ElMessage.error('加载产品排行榜数据失败')
  }
}

// 加载客户分析数据
const loadCustomerAnalysis = async () => {
  try {
    const data = await apiClient.get('/customer/analysis')
    customerData.value = data.slice(0, 8) // 只显示前 8 条
    renderCustomerChart()
  } catch (error) {
    console.error('加载客户分析数据失败:', error)
    ElMessage.error('加载客户分析数据失败')
  }
}

// 渲染销售趋势图
const renderTrendChart = () => {
  if (!trendChartRef.value) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1a202c' }
    },
    legend: {
      data: ['销售额', '订单数'],
      textStyle: { color: '#4a5568' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: salesTrendData.value.map(item => item.month),
      axisLabel: { color: '#4a5568' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: [
      {
        type: 'value',
        name: '销售额 (元)',
        axisLabel: {
          formatter: value => (value / 10000).toFixed(0) + '万',
          color: '#4a5568'
        },
        splitLine: { lineStyle: { color: '#f7fafc', type: 'dashed' } }
      },
      {
        type: 'value',
        name: '订单数',
        axisLabel: {
          formatter: value => value + '单',
          color: '#4a5568'
        },
        splitLine: { lineStyle: { color: '#f7fafc', type: 'dashed' } }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        data: salesTrendData.value.map(item => item.sales_amount),
        itemStyle: { color: '#2c5282' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(44, 82, 130, 0.5)' },
            { offset: 1, color: 'rgba(44, 82, 130, 0.05)' }
          ])
        }
      },
      {
        name: '订单数',
        type: 'bar',
        yAxisIndex: 1,
        data: salesTrendData.value.map(item => item.order_count),
        itemStyle: { color: '#38a169' }
      }
    ]
  }

  trendChart.setOption(option)
}

// 渲染品类分布图
const renderCategoryChart = () => {
  if (!categoryChartRef.value) return

  if (!categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1a202c' }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#4a5568' }
    },
    color: ['#2c5282', '#4299e1', '#38a169', '#d69e2e', '#3182ce', '#68d391', '#f6ad55', '#a0aec0'],
    series: [
      {
        name: '销售额',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: categoryData.value.map(item => ({
          name: item.category,
          value: item.total_sales
        }))
      }
    ]
  }

  categoryChart.setOption(option)
}

// 渲染产品排行榜图
const renderRankingChart = () => {
  if (!rankingChartRef.value) return

  if (!rankingChart) {
    rankingChart = echarts.init(rankingChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1a202c' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '销售额 (元)',
      axisLabel: {
        formatter: value => (value / 10000).toFixed(0) + '万',
        color: '#4a5568'
      },
      splitLine: { lineStyle: { color: '#f7fafc', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: productRankingData.value.map(item => item.product_name).reverse(),
      axisLabel: {
        interval: 0,
        fontSize: 12,
        color: '#4a5568'
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: productRankingData.value.map(item => item.total_amount).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2c5282' },
            { offset: 0.5, color: '#4299e1' },
            { offset: 1, color: '#4299e1' }
          ])
        },
        label: {
          show: true,
          position: 'right',
          formatter: params => {
            const value = params.value
            return (value / 10000).toFixed(1) + '万'
          },
          color: '#4a5568'
        }
      }
    ]
  }

  rankingChart.setOption(option)
}

// 渲染客户分析图
const renderCustomerChart = () => {
  if (!customerChartRef.value) return

  if (!customerChart) {
    customerChart = echarts.init(customerChartRef.value)
  }

  // 按客户类型聚合
  const typeMap = {}
  customerData.value.forEach(item => {
    if (!typeMap[item.customer_type]) {
      typeMap[item.customer_type] = 0
    }
    typeMap[item.customer_type] += item.total_amount
  })

  const data = Object.entries(typeMap).map(([name, value]) => ({ name, value }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 元',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1a202c' }
    },
    legend: {
      top: '5%',
      left: 'center',
      textStyle: { color: '#4a5568' }
    },
    color: ['#2c5282', '#4299e1', '#38a169', '#d69e2e', '#3182ce'],
    series: [
      {
        name: '销售额',
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['50%', '60%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          formatter: '{b}\n{d}%'
        },
        data: data
      }
    ]
  }

  customerChart.setOption(option)
}

// 格式化 KPI 值
const formatKpiValue = (value) => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万'
  }
  return value.toFixed(0)
}

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadKpiSummary(),
      loadSalesTrend(),
      loadCategoryAnalysis(),
      loadProductRanking(),
      loadCustomerAnalysis()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  trendChart?.resize()
  categoryChart?.resize()
  rankingChart?.resize()
  customerChart?.resize()
}

// 生命周期
onMounted(async () => {
  await refreshData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  categoryChart?.dispose()
  rankingChart?.dispose()
  customerChart?.dispose()
})
</script>

<style scoped>
.sales-report {
  min-height: 100vh;
  background-color: var(--bg-body);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: var(--bg-header);
  box-shadow: var(--shadow-sm);
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

.header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
  font-weight: 600;
  letter-spacing: 1px;
}

.header-actions {
  display: flex;
  gap: 12px;
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

.content {
  padding: 0 24px 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  margin-bottom: 20px;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.kpi-card :deep(.el-card__header) {
  padding: 14px 20px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-bottom: none;
}

.kpi-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.kpi-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  padding: 28px 0;
}

.kpi-value .number {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary);
  margin-right: 8px;
  font-family: 'SF Mono', 'Consolas', monospace;
}

.kpi-value .unit {
  font-size: 14px;
  color: var(--text-secondary);
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
  border: 1px solid var(--border);
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: var(--shadow-md);
}

.chart-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.chart {
  width: 100%;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }

  .content {
    padding: 0 12px 16px;
  }

  .kpi-value .number {
    font-size: 28px;
  }

  .header h1 {
    font-size: 20px;
  }
}
</style>
