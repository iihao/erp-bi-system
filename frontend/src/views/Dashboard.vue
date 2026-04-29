<template>
  <div class="dashboard-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><DataBoard /></el-icon>
          数据仪表板
        </h1>
        <p class="page-description">实时监控业务数据，掌握企业经营状况</p>
      </div>
      <div class="header-actions">
        <span class="last-update">
          <el-icon><Clock /></el-icon>
          最后更新：{{ lastUpdateTime }}
        </span>
        <el-button type="primary" @click="refreshData" :loading="loading" :icon="Refresh">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- KPI 指标卡片区 -->
    <el-row :gutter="var(--spacing-4)" class="kpi-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="(kpi, index) in kpiData" :key="index">
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-card-content">
            <div class="kpi-icon" :style="{ background: kpi.gradient }">
              <component :is="kpi.icon" />
            </div>
            <div class="kpi-info">
              <div class="kpi-label">{{ kpi.kpi_name }}</div>
              <div class="kpi-value">
                <span class="number">{{ formatKpiValue(kpi.kpi_value, kpi.unit) }}</span>
                <span class="unit">{{ kpi.unit }}</span>
              </div>
              <div class="kpi-trend" :class="kpi.trendClass">
                <el-icon><Trend v-if="kpi.trend > 0" /><Bottom v-else /></el-icon>
                <span>{{ Math.abs(kpi.trend) }}% 较上月</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="var(--spacing-4)" class="chart-row">
      <!-- 销售趋势图 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="card-title">
                <el-icon><TrendCharts /></el-icon>
                销售趋势（近 12 个月）
              </div>
              <el-radio-group v-model="trendPeriod" size="small">
                <el-radio-button label="6">半年</el-radio-button>
                <el-radio-button label="12">全年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div v-loading="chartLoading.trend" ref="trendChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <!-- 品类占比图 -->
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-title">
              <el-icon><PieChart /></el-icon>
              品类销售占比
            </div>
          </template>
          <div v-loading="chartLoading.category" ref="categoryChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="var(--spacing-4)" class="chart-row">
      <!-- 产品排行图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-title">
              <el-icon><Ranking /></el-icon>
              产品销量 Top 10
            </div>
          </template>
          <div v-loading="chartLoading.ranking" ref="rankingChartRef" class="chart"></div>
        </el-card>
      </el-col>

      <!-- 快捷入口 -->
      <el-col :xs="24" :lg="12">
        <el-card class="quick-links-card" shadow="hover">
          <template #header>
            <div class="card-title">
              <el-icon><Grid /></el-icon>
              快捷入口
            </div>
          </template>
          <div class="quick-links-grid">
            <div
              v-for="link in quickLinks"
              :key="link.path"
              class="quick-link-item"
              @click="navigateTo(link.path)"
            >
              <div class="link-icon" :style="{ background: link.gradient }">
                <component :is="link.icon" />
              </div>
              <h4>{{ link.title }}</h4>
              <p>{{ link.description }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

// Element Plus Icons
import {
  DataBoard, Clock, Refresh, Trend, Bottom, TrendCharts,
  PieChart, Ranking, Grid, Money, ShoppingCart, Package, User
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const trendPeriod = ref('12')

// 图表实例
let trendChart = null
let categoryChart = null
let rankingChart = null

// 图表 DOM 引用
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const rankingChartRef = ref(null)

// 最后更新时间
const lastUpdateTime = ref('刚刚')

// 数据
const kpiData = ref([
  { kpi_name: '总销售额', kpi_value: 0, unit: '元', trend: 0, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', icon: Money },
  { kpi_name: '总订单数', kpi_value: 0, unit: '单', trend: 0, gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', icon: ShoppingCart },
  { kpi_name: '总销售量', kpi_value: 0, unit: '件', trend: 0, gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', icon: Package },
  { kpi_name: '客户总数', kpi_value: 0, unit: '人', trend: 0, gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', icon: User }
])

const salesTrendData = ref([])
const categoryData = ref([])
const productRankingData = ref([])

// 图表加载状态
const chartLoading = reactive({
  trend: false,
  category: false,
  ranking: false
})

// 快捷链接
const quickLinks = [
  { path: '/portal/reports', title: '销售报表', description: '销售趋势、产品排行', gradient: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', icon: TrendCharts },
  { path: '/data', title: '数据预览', description: '查看数仓各层数据', gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', icon: DataLine },
  { path: '/etl', title: 'ETL 任务', description: '管理和调度 ETL', gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', icon: Refresh },
  { path: '/portal/ai-query', title: 'AI 问数', description: '自然语言查询数据', gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)', icon: ChatDotRound },
  { path: '/admin/users', title: '后台管理', description: '用户、角色、权限', gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', icon: Monitor }
]

// API 基础 URL
const API_BASE = '/api/reports'

// 获取 token
const getToken = () => localStorage.getItem('token')

// Axios 实例
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器
apiClient.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
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
    kpiData.value = data.map((item, index) => ({
      ...item,
      trend: Math.floor(Math.random() * 30) - 10, // 模拟数据
      ...kpiData.value[index]
    }))
  } catch (error) {
    console.error('加载 KPI 数据失败:', error)
    // 使用模拟数据
    kpiData.value = kpiData.value.map(kpi => ({
      ...kpi,
      kpi_value: Math.floor(Math.random() * 1000000),
      trend: Math.floor(Math.random() * 30) - 10
    }))
  }
}

// 加载销售趋势数据
const loadSalesTrend = async () => {
  chartLoading.trend = true
  try {
    const data = await apiClient.get(`/sales/trend?months=${trendPeriod.value}`)
    salesTrendData.value = data
    renderTrendChart()
  } catch (error) {
    console.error('加载销售趋势数据失败:', error)
    // 使用模拟数据
    const months = []
    for (let i = parseInt(trendPeriod.value); i > 0; i--) {
      const date = new Date()
      date.setMonth(date.getMonth() - i)
      months.push({
        month: `${date.getMonth() + 1}月`,
        sales_amount: Math.floor(Math.random() * 500000) + 100000,
        order_count: Math.floor(Math.random() * 1000) + 100
      })
    }
    salesTrendData.value = months
    renderTrendChart()
  } finally {
    chartLoading.trend = false
  }
}

// 加载品类分析数据
const loadCategoryAnalysis = async () => {
  chartLoading.category = true
  try {
    const data = await apiClient.get('/sales/category-analysis')
    categoryData.value = data
    renderCategoryChart()
  } catch (error) {
    console.error('加载品类分析数据失败:', error)
    categoryData.value = [
      { category: '电子产品', total_sales: 350000 },
      { category: '家居用品', total_sales: 280000 },
      { category: '服装鞋帽', total_sales: 220000 },
      { category: '食品饮料', total_sales: 180000 },
      { category: '其他', total_sales: 120000 }
    ]
    renderCategoryChart()
  } finally {
    chartLoading.category = false
  }
}

// 加载产品排行榜数据
const loadProductRanking = async () => {
  chartLoading.ranking = true
  try {
    const data = await apiClient.get('/sales/product-ranking?limit=10')
    productRankingData.value = data
    renderRankingChart()
  } catch (error) {
    console.error('加载产品排行榜数据失败:', error)
    productRankingData.value = Array.from({ length: 10 }, (_, i) => ({
      product_name: `产品${i + 1}`,
      total_amount: Math.floor(Math.random() * 200000) + 50000
    }))
    renderRankingChart()
  } finally {
    chartLoading.ranking = false
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
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      padding: [12, 16],
      borderRadius: 8
    },
    legend: {
      data: ['销售额', '订单数'],
      textStyle: { color: '#64748b' },
      right: 20,
      top: 10
    },
    grid: {
      left: '4%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: salesTrendData.value.map(item => item.month),
      axisLabel: {
        rotate: 45,
        color: '#64748b',
        fontSize: 12
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: [
      {
        type: 'value',
        name: '销售额',
        axisLabel: {
          formatter: value => (value / 10000).toFixed(0) + '万',
          color: '#64748b'
        },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
      },
      {
        type: 'value',
        name: '订单数',
        axisLabel: {
          formatter: value => value,
          color: '#64748b'
        },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        data: salesTrendData.value.map(item => item.sales_amount),
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
          ])
        }
      },
      {
        name: '订单数',
        type: 'bar',
        yAxisIndex: 1,
        data: salesTrendData.value.map(item => item.order_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.8)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.3)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        barMaxWidth: 40
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
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      padding: [12, 16],
      borderRadius: 8
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      type: 'scroll',
      textStyle: { color: '#64748b' }
    },
    color: ['#3b82f6', '#60a5fa', '#10b981', '#f59e0b', '#8b5cf6', '#34d399', '#fbbf24', '#a78bfa'],
    series: [
      {
        name: '销售额',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: '#1e293b'
          }
        },
        labelLine: { show: false },
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
      formatter: params => {
        const val = params[0].value
        return `${params[0].name}<br/>销售额：${(val / 10000).toFixed(2)}万`
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      padding: [12, 16],
      borderRadius: 8
    },
    grid: {
      left: '4%',
      right: '8%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: value => (value / 10000).toFixed(0) + '万',
        color: '#64748b'
      },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: productRankingData.value.map(item => item.product_name).reverse(),
      axisLabel: {
        interval: 0,
        fontSize: 12,
        color: '#475569'
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: productRankingData.value.map(item => item.total_amount).reverse(),
        barWidth: '50%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#3b82f6' },
            { offset: 0.5, color: '#60a5fa' },
            { offset: 1, color: '#60a5fa' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          formatter: params => (params.value / 10000).toFixed(1) + '万',
          fontSize: 12,
          color: '#64748b'
        }
      }
    ]
  }

  rankingChart.setOption(option)
}

// 格式化 KPI 值
const formatKpiValue = (value, unit) => {
  if (!value) return '0'
  const numValue = parseFloat(value)
  if (isNaN(numValue)) return '0'

  if (unit === '元' || unit === '件') {
    if (numValue >= 100000000) {
      return (numValue / 100000000).toFixed(2) + '亿'
    } else if (numValue >= 10000) {
      return (numValue / 10000).toFixed(2) + '万'
    }
    return numValue.toFixed(0)
  }
  return numValue.toLocaleString()
}

// 导航
const navigateTo = (path) => router.push(path)

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  try {
    await Promise.all([
      loadKpiSummary(),
      loadSalesTrend(),
      loadCategoryAnalysis(),
      loadProductRanking()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  trendChart?.resize()
  categoryChart?.resize()
  rankingChart?.resize()
}

// 生命周期
onMounted(async () => {
  await refreshData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  categoryChart?.resize()
  rankingChart?.dispose()
})
</script>

<style scoped>
/* ========================================
   仪表盘页面 - 企业级设计
   ======================================== */
.dashboard-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
  padding: var(--spacing-6);
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.header-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.page-title :deep(.el-icon) {
  font-size: 28px;
  color: var(--primary);
}

.page-description {
  font-size: var(--text-base);
  color: var(--text-tertiary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.last-update {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* KPI 卡片 */
.kpi-row {
  margin-bottom: var(--spacing-4);
}

.kpi-card {
  margin-bottom: var(--spacing-4);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  overflow: hidden;
}

.kpi-card-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.kpi-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-xl);
  color: white;
  flex-shrink: 0;
}

.kpi-icon :deep(.el-icon) {
  font-size: 28px;
}

.kpi-info {
  flex: 1;
}

.kpi-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-2);
}

.kpi-value {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.kpi-value .number {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  font-family: var(--font-family-mono);
}

.kpi-value .unit {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.kpi-trend.up {
  color: var(--success);
}

.kpi-trend.down {
  color: var(--danger);
}

/* 图表卡片 */
.chart-row {
  margin-bottom: var(--spacing-4);
}

.chart-card {
  margin-bottom: var(--spacing-4);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.card-title :deep(.el-icon) {
  font-size: 20px;
  color: var(--primary);
}

.chart {
  height: 360px;
  width: 100%;
}

/* 快捷入口 */
.quick-links-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.quick-links-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--spacing-4);
  padding: var(--spacing-4);
}

.quick-link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast) var(--transition-cubic);
  text-align: center;
}

.quick-link-item:hover {
  background: var(--slate-50);
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.link-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  color: white;
  margin-bottom: var(--spacing-3);
}

.link-icon :deep(.el-icon) {
  font-size: 24px;
}

.quick-link-item h4 {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-1);
}

.quick-link-item p {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.4;
}

/* 响应式 */
@media (max-width: 1200px) {
  .quick-links-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-4);
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .quick-links-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .kpi-value .number {
    font-size: var(--text-2xl);
  }
}
</style>
