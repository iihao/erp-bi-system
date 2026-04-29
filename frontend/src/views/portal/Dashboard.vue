<template>
  <div class="portal-dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1 class="welcome-title">欢迎使用 地产经营门户</h1>
      <p class="welcome-subtitle">聚焦认购、签约、回款、成本、费用与利润，快速掌握经营态势</p>
    </div>

    <!-- 地产核心指标 -->
    <el-row :gutter="20" class="kpi-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="(kpi, index) in estateCoreKpiData" :key="index">
        <el-card class="kpi-card" shadow="hover">
          <template #header>
            <span class="kpi-title">{{ kpi.kpi_name }}</span>
          </template>
          <div class="kpi-value">
            <span class="number">{{ formatKpiValue(kpi.kpi_value, kpi.unit) }}</span>
            <span class="unit">{{ kpi.unit }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 地产经营指标 -->
    <el-card class="estate-summary-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">地产经营指标</span>
          <el-tag type="success" effect="plain">实时汇总</el-tag>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col v-for="(item, index) in estateKpiData" :key="index" :xs="24" :sm="12" :lg="6">
          <div class="estate-kpi-item">
            <div class="estate-kpi-icon" :style="{ background: item.gradient }">
              <el-icon :size="24"><component :is="item.icon" /></el-icon>
            </div>
            <div class="estate-kpi-body">
              <div class="estate-kpi-label">{{ item.label }}</div>
              <div class="estate-kpi-value">{{ item.value }}</div>
              <div class="estate-kpi-sub">{{ item.sub }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 签约回款趋势图 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">签约回款趋势（近 6 个月）</span>
            </div>
          </template>
          <div v-loading="chartLoading.trend" ref="trendChartRef" class="chart" style="height: 350px"></div>
        </el-card>
      </el-col>

      <!-- 回款结构图 -->
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">回款结构占比</span>
          </template>
          <div v-loading="chartLoading.category" ref="categoryChartRef" class="chart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <!-- 项目销售排行图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">项目销售排行 Top 5</span>
            </div>
          </template>
          <div v-loading="chartLoading.ranking" ref="rankingChartRef" class="chart" style="height: 320px"></div>
        </el-card>
      </el-col>

      <!-- 快捷入口 -->
      <el-col :xs="24" :lg="12">
        <el-card class="quick-links-card" shadow="hover">
          <template #header>
            <span class="card-title">快捷入口</span>
          </template>
          <div class="quick-links-container">
            <div class="quick-link-item" @click="navigateTo('/portal/reports')">
              <div class="link-icon-wrapper blue">
                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
              </div>
              <h3>全部报表</h3>
              <p>查看您可访问的所有报表</p>
            </div>
            <div class="quick-link-item" @click="navigateTo('/portal/realestate')">
              <div class="link-icon-wrapper green">
                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v18h18" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18 17V9" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M13 17V5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M8 17v-3" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3>地产看板</h3>
              <p>项目、房源、签约、回款全景</p>
            </div>
            <div class="quick-link-item" @click="navigateTo('/portal/ai-query')">
              <div class="link-icon-wrapper orange">
                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                </svg>
              </div>
              <h3>AI 问数</h3>
              <p>快速提问地产经营数据</p>
            </div>
            <div class="quick-link-item" @click="navigateTo('/portal/report-portal')">
              <div class="link-icon-wrapper blue">
                <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 21h18M5 21V7l8-4 8 4v14"/>
                  <path d="M9 14h6"/>
                </svg>
              </div>
              <h3>报表中心</h3>
              <p>浏览已发布的经营报表</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 刷新按钮 -->
    <div class="refresh-action">
      <el-button @click="refreshData" :loading="loading" type="primary" circle>
        <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Tickets, House, Coin, Wallet, Money, DataAnalysis, Document, TrendCharts, HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)

// 图表实例
let trendChart = null
let categoryChart = null
let rankingChart = null

// 图表 DOM 引用
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const rankingChartRef = ref(null)

// 数据
const realEstateSummary = ref({})
const realEstateTrendData = ref([])
const realEstateRankingData = ref([])
const realEstatePaymentData = ref([])

// 图表加载状态
const chartLoading = ref({
  trend: false,
  category: false,
  ranking: false
})

// API 基础 URL
const API_BASE = '/api/portal'

// 获取 token
const getToken = () => {
  return localStorage.getItem('token')
}

// 加载仪表板概览数据
const loadOverview = async () => {
  loading.value = true
  try {
    const token = getToken()
    const response = await fetch(`${API_BASE}/overview`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        router.push('/portal/login')
        return
      }
      throw new Error('加载数据失败')
    }

    const data = await response.json()

    realEstateSummary.value = data.real_estate_summary || {}

    realEstateTrendData.value = data.real_estate_trend || []
    renderTrendChart()

    realEstatePaymentData.value = data.real_estate_payment_structure || []
    renderCategoryChart()

    realEstateRankingData.value = data.real_estate_ranking || []
    renderRankingChart()

  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const formatMoney = (value) => {
  const num = Number(value || 0)
  if (!num) return '0'
  if (Math.abs(num) >= 100000000) return `${(num / 100000000).toFixed(2)}亿`
  if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(2)}万`
  return num.toFixed(2)
}

const estateKpiData = computed(() => {
  const summary = realEstateSummary.value || {}
  return [
    {
      label: '认购套数',
      value: summary.total_subscriptions || 0,
      sub: `认购转签约率 ${summary.subscription_rate || 0}%`,
      gradient: 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
      icon: Tickets
    },
    {
      label: '签约套数',
      value: summary.total_contracts || 0,
      sub: `项目数 ${summary.total_projects || 0} 个`,
      gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      icon: House
    },
    {
      label: '签约金额',
      value: `¥${formatMoney(summary.total_sales)}`,
      sub: `回款率 ${summary.collection_rate || 0}%`,
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
      icon: Coin
    },
    {
      label: '回款金额',
      value: `¥${formatMoney(summary.total_received)}`,
      sub: `应收余额 ¥${formatMoney(summary.total_receivables)}`,
      gradient: 'linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)',
      icon: Wallet
    },
    {
      label: '成本金额',
      value: `¥${formatMoney(summary.total_cost)}`,
      sub: `成本率 ${summary.cost_ratio || 0}%`,
      gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
      icon: DataAnalysis
    },
    {
      label: '费用金额',
      value: `¥${formatMoney(summary.total_expense)}`,
      sub: `费用率 ${summary.expense_ratio || 0}%`,
      gradient: 'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)',
      icon: Document
    },
    {
      label: '利润金额',
      value: `¥${formatMoney(summary.total_profit)}`,
      sub: `利润率 ${summary.profit_margin || 0}%`,
      gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
      icon: TrendCharts
    },
    {
      label: '房源总数',
      value: summary.total_units || 0,
      sub: '覆盖全部项目',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
      icon: HomeFilled
    }
  ]
})

const estateCoreKpiData = computed(() => {
  const summary = realEstateSummary.value || {}
  return [
    {
      kpi_name: '认购套数',
      kpi_value: summary.total_subscriptions || 0,
      unit: '套'
    },
    {
      kpi_name: '签约套数',
      kpi_value: summary.total_contracts || 0,
      unit: '套'
    },
    {
      kpi_name: '签约金额',
      kpi_value: summary.total_sales || 0,
      unit: '元'
    },
    {
      kpi_name: '回款金额',
      kpi_value: summary.total_received || 0,
      unit: '元'
    }
  ]
})

// 渲染签约回款趋势图
const renderTrendChart = () => {
  const dataSource = realEstateTrendData.value
  if (!trendChartRef.value || dataSource.length === 0) return

  chartLoading.value.trend = true

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      formatter: params => {
        const lines = [params[0].axisValue]
        params.forEach(item => {
          lines.push(`${item.marker}${item.seriesName}：¥${formatMoney(item.value)}`)
        })
        return lines.join('<br/>')
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dataSource.map(item => item.month),
      axisLabel: { color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      name: '金额',
      axisLabel: {
        formatter: value => (value / 10000).toFixed(0) + '万',
        color: '#64748b'
      },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    series: [
      {
        name: '签约金额',
        type: 'line',
        smooth: true,
        data: dataSource.map(item => item.sales_amount),
        itemStyle: { color: '#2563eb' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37, 99, 235, 0.4)' },
            { offset: 1, color: 'rgba(37, 99, 235, 0.05)' }
          ])
        }
      },
      {
        name: '回款金额',
        type: 'bar',
        data: dataSource.map(item => item.received_amount || 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.8)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.3)' }
          ])
        },
        barMaxWidth: 35
      }
    ]
  }

  trendChart.setOption(option)
  chartLoading.value.trend = false
}

// 渲染回款结构图
const renderCategoryChart = () => {
  const dataSource = realEstatePaymentData.value
  if (!categoryChartRef.value || dataSource.length === 0) return

  chartLoading.value.category = true

  if (!categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      type: 'scroll',
      textStyle: { color: '#64748b' }
    },
    color: ['#2563eb', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
    series: [
      {
        name: '回款结构',
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
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        labelLine: { show: false },
        data: dataSource.map(item => ({
          name: item.name || item.category,
          value: item.value || item.total_sales
        }))
      }
    ]
  }

  categoryChart.setOption(option)
  chartLoading.value.category = false
}

// 渲染项目销售排行图
const renderRankingChart = () => {
  const dataSource = realEstateRankingData.value
  if (!rankingChartRef.value || dataSource.length === 0) return

  chartLoading.value.ranking = true

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
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    grid: {
      left: '3%',
      right: '10%',
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
      data: dataSource.map(item => item.project_name || item.product_name).reverse(),
      axisLabel: {
        interval: 0,
        fontSize: 12,
        color: '#64748b'
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    series: [
      {
        name: '销售额',
        type: 'bar',
        data: dataSource.map(item => item.total_sales || item.total_amount).reverse(),
        barWidth: '60%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2563eb' },
            { offset: 1, color: '#3b82f6' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          formatter: params => (params.value / 10000).toFixed(1) + '万',
          fontSize: 11,
          color: '#64748b'
        }
      }
    ]
  }

  rankingChart.setOption(option)
  chartLoading.value.ranking = false
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
  return numValue.toFixed(0)
}

// 导航
const navigateTo = (path) => {
  router.push(path)
}

// 刷新数据
const refreshData = async () => {
  await loadOverview()
  ElMessage.success('数据刷新成功')
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  trendChart?.resize()
  categoryChart?.resize()
  rankingChart?.resize()
}

// 生命周期
onMounted(async () => {
  await loadOverview()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  categoryChart?.dispose()
  rankingChart?.dispose()
})
</script>

<style scoped>
.portal-dashboard {
  max-width: 1600px;
  margin: 0 auto;
  position: relative;
}

.welcome-section {
  margin-bottom: 24px;
  padding: 28px 28px 30px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.96) 0%, rgba(219, 234, 254, 0.98) 52%, rgba(191, 219, 254, 0.94) 100%);
  color: #fff;
  box-shadow: 0 16px 32px rgba(37, 99, 235, 0.1);
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.welcome-section::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 28%),
    radial-gradient(circle at bottom left, rgba(96, 165, 250, 0.1), transparent 26%);
  pointer-events: none;
}

.welcome-title {
  position: relative;
  z-index: 1;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  position: relative;
  z-index: 1;
  font-size: 14px;
  color: #475569;
  margin: 0;
}

.estate-summary-card {
  margin-bottom: 20px;
  border-radius: 20px;
  border: 1px solid #dbeafe;
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08);
}

.estate-kpi-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 16px;
  min-height: 112px;
}

.estate-kpi-icon {
  width: 52px;
  height: 52px;
  min-width: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}

.estate-kpi-body {
  min-width: 0;
}

.estate-kpi-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.estate-kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
  margin-bottom: 4px;
}

.estate-kpi-sub {
  font-size: 12px;
  color: #475569;
}

.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
}

.kpi-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.12);
  border-color: rgba(37, 99, 235, 0.28);
}

.kpi-card :deep(.el-card__header) {
  padding: 14px 20px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-bottom: none;
}

.kpi-title {
  font-size: 13px;
  color: #1d4ed8;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.kpi-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  padding: 24px 0;
}

.kpi-value .number {
  font-size: 32px;
  font-weight: 700;
  color: #0f172a;
  margin-right: 6px;
  font-family: 'SF Mono', 'Consolas', monospace;
}

.kpi-value .unit {
  font-size: 13px;
  color: #64748b;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  transition: all 0.3s ease;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
}

.chart-card:hover {
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.1);
}

.chart-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
}

.chart {
  width: 100%;
}

.quick-links-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  height: 100%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
}

.quick-links-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.quick-links-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 12px;
}

.quick-link-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 130px;
}

.quick-link-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 26px rgba(37, 99, 235, 0.12);
  border-color: rgba(37, 99, 235, 0.25);
  background: #fff;
}

.link-icon-wrapper {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.link-icon-wrapper.blue {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.link-icon-wrapper.green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.link-icon-wrapper.orange {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.quick-link-item:hover .link-icon-wrapper {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.link-icon {
  width: 22px;
  height: 22px;
  color: #ffffff;
}

.quick-link-item h3 {
  font-size: 14px;
  color: #1e293b;
  margin: 0 0 6px 0;
  font-weight: 600;
  white-space: nowrap;
}

.quick-link-item p {
  font-size: 11px;
  color: #64748b;
  margin: 0;
  text-align: center;
  line-height: 1.3;
}

.refresh-action {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

.button-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  color: currentColor;
}

/* 响应式 */
@media (max-width: 900px) {
  .quick-links-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .quick-links-container {
    grid-template-columns: 1fr;
  }

  .kpi-value .number {
    font-size: 26px;
  }

  .welcome-section {
    padding: 22px 20px;
    border-radius: 18px;
  }
}
</style>
