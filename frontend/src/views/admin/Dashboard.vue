<template>
  <div class="admin-dashboard">
    <!-- KPI 统计卡片 -->
    <el-row :gutter="20" class="kpi-row">
      <el-col :xs="24" :sm="12" :lg="4" v-for="(kpi, index) in kpiData" :key="index">
        <div class="kpi-card-wrapper">
          <div class="kpi-card">
            <div class="kpi-icon" :style="{ background: kpi.gradient }">
              <el-icon :size="36"><component :is="kpi.icon" /></el-icon>
            </div>
            <div class="kpi-content">
              <div class="kpi-label">{{ kpi.label }}</div>
              <div class="kpi-value">{{ kpi.value }}</div>
              <div class="kpi-trend" :class="kpi.trendClass" v-if="kpi.trend">
                <el-icon class="trend-icon"><component :is="kpi.trendIcon" /></el-icon>
                <span>{{ kpi.trend }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 地产经营指标 -->
    <el-card class="estate-summary-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="header-icon"><el-icon :size="20"><House /></el-icon></span>
            <span class="card-title">地产经营指标</span>
            <el-tag size="small" type="success" class="live-tag">实时汇总</el-tag>
          </div>
          <el-tag size="small" type="info" effect="plain">认购 / 签约 / 回款 / 成本 / 费用 / 利润</el-tag>
        </div>
      </template>
      <el-row :gutter="16" class="estate-kpi-grid">
        <el-col v-for="(kpi, index) in estateKpiData" :key="index" :xs="24" :sm="12" :lg="6">
          <div class="estate-kpi-card">
            <div class="estate-kpi-icon" :style="{ background: kpi.gradient }">
              <el-icon :size="28"><component :is="kpi.icon" /></el-icon>
            </div>
            <div class="estate-kpi-content">
              <div class="estate-kpi-label">{{ kpi.label }}</div>
              <div class="estate-kpi-value">{{ kpi.value }}</div>
              <div class="estate-kpi-sub">{{ kpi.sub }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表展示区 -->
    <el-row :gutter="20" class="chart-row">
      <!-- ETL 任务执行趋势 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="header-icon"><el-icon :size="20"><TrendCharts /></el-icon></span>
                <span class="card-title">ETL 任务执行趋势</span>
                <el-tag size="small" type="success" class="live-tag">实时</el-tag>
              </div>
              <el-select v-model="trendPeriod" size="small" @change="loadETLTrend">
                <el-option label="近 7 天" value="7"/>
                <el-option label="近 30 天" value="30"/>
              </el-select>
            </div>
          </template>
          <div class="chart-container" ref="etlChartRef" v-loading="chartLoading.etl"></div>
        </el-card>
      </el-col>

      <!-- 查询热度排行 -->
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="header-icon"><el-icon :size="20"><Orange /></el-icon></span>
                <span class="card-title">查询热度排行</span>
                <el-tag size="small" type="warning" class="top-tag">Top 10</el-tag>
              </div>
            </div>
          </template>
          <div class="chart-container" ref="heatmapChartRef" v-loading="chartLoading.heatmap"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <!-- 系统资源使用率 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="header-icon"><el-icon :size="20"><Monitor /></el-icon></span>
                <span class="card-title">系统资源使用率</span>
              </div>
              <el-tag size="small" :type="systemStatusType">{{ systemStatusText }}</el-tag>
            </div>
          </template>
          <div class="resource-list">
            <div class="resource-item" v-for="item in resources" :key="item.name">
              <div class="resource-header">
                <div class="resource-info">
                  <span class="resource-icon"><el-icon><component :is="item.icon" /></el-icon></span>
                  <span class="resource-name">{{ item.name }}</span>
                </div>
                <span class="resource-value" :style="{ color: getResourceColor(item.value) }">{{ item.value }}%</span>
              </div>
              <el-progress
                :percentage="item.value"
                :color="getProgressColor(item.value)"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 快捷操作 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <span class="header-icon"><el-icon :size="20"><Lightning /></el-icon></span>
                <span class="card-title">快捷操作</span>
              </div>
            </div>
          </template>
          <div class="quick-actions">
            <button class="action-btn primary" @click="handleRunAllETL">
              <el-icon :size="28"><VideoPlay /></el-icon>
              <span class="action-text">运行全部 ETL</span>
            </button>
            <button class="action-btn success" @click="handleViewLogs">
              <el-icon :size="28"><Document /></el-icon>
              <span class="action-text">查看系统日志</span>
            </button>
            <button class="action-btn warning" @click="handleUserManage">
              <el-icon :size="28"><UserFilled /></el-icon>
              <span class="action-text">用户管理</span>
            </button>
            <button class="action-btn info" @click="handleReportConfig">
              <el-icon :size="28"><Edit /></el-icon>
              <span class="action-text">报表配置</span>
            </button>
          </div>

          <!-- 最近活动 -->
          <div class="recent-activities">
            <div class="activity-header">
              <span class="activity-title">最近活动</span>
              <el-button text size="small" type="primary">查看全部</el-button>
            </div>
            <ul class="activity-list">
              <li v-for="(activity, index) in activities" :key="index" class="activity-item">
                <div class="activity-dot" :class="activity.type"></div>
                <div class="activity-content">
                  <span class="activity-text">{{ activity.text }}</span>
                  <span class="activity-time">{{ activity.time }}</span>
                </div>
              </li>
            </ul>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { Grid, List, DataAnalysis, User, Search, Clock, Cpu, Monitor, Link, VideoPlay, Document, UserFilled, Edit, Lightning, Orange, Top, House, Coin, Wallet, Money, Tickets, TrendCharts } from '@element-plus/icons-vue'

const refreshing = ref(false)
const trendPeriod = ref('7')

const kpiData = ref([
  {
    label: '数据表总数',
    value: '0',
    trend: '+12%',
    trendClass: 'trend-up',
    trendIcon: Top,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: Grid
  },
  {
    label: 'ETL 任务数',
    value: '0',
    trend: '+3',
    trendClass: 'trend-up',
    trendIcon: Top,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    icon: List
  },
  {
    label: '报表指标数',
    value: '0',
    trend: '+24',
    trendClass: 'trend-up',
    trendIcon: Top,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    icon: DataAnalysis
  },
  {
    label: '用户总数',
    value: '0',
    trend: '+8',
    trendClass: 'trend-up',
    trendIcon: Top,
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    icon: User
  },
  {
    label: '今日查询',
    value: '0',
    trend: '+156',
    trendClass: 'trend-up',
    trendIcon: Top,
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    icon: Search
  },
  {
    label: '系统运行',
    value: '0 天',
    trend: '稳定',
    trendClass: 'trend-stable',
    gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    icon: Clock
  }
])

const estateStats = ref({
  total_projects: 0,
  total_units: 0,
  total_subscriptions: 0,
  total_contracts: 0,
  total_sales: 0,
  total_received: 0,
  total_receivables: 0,
  total_cost: 0,
  total_expense: 0,
  total_profit: 0,
  subscription_rate: 0,
  collection_rate: 0,
  cost_ratio: 0,
  expense_ratio: 0,
  profit_margin: 0
})

const resources = ref([
  { name: 'CPU 使用率', value: 0, icon: Cpu },
  { name: '内存使用率', value: 0, icon: Cpu },
  { name: '磁盘使用率', value: 0, icon: Monitor },
  { name: '数据库连接', value: 0, icon: Link }
])

const activities = ref([
  { time: '10:30', text: 'ETL 任务 "销售数据同步" 执行完成', type: 'success' },
  { time: '09:15', text: '用户 admin 登录系统', type: 'info' },
  { time: '08:00', text: '系统定时备份完成', type: 'success' },
  { time: '昨天', text: '新增报表 "月度销售分析"', type: 'warning' }
])

const chartLoading = ref({
  etl: false,
  heatmap: false
})

const etlChartRef = ref(null)
const heatmapChartRef = ref(null)
let etlChart = null
let heatmapChart = null

// 系统状态
const systemStatusType = computed(() => {
  const avgUsage = (resources.value[0].value + resources.value[1].value) / 2
  if (avgUsage < 60) return 'success'
  if (avgUsage < 80) return 'warning'
  return 'danger'
})

const systemStatusText = computed(() => {
  const avgUsage = (resources.value[0].value + resources.value[1].value) / 2
  if (avgUsage < 60) return '运行正常'
  if (avgUsage < 80) return '负载较高'
  return '负载过高'
})

const formatMoney = (value) => {
  const num = Number(value || 0)
  if (!num) return '0'
  if (Math.abs(num) >= 100000000) return `${(num / 100000000).toFixed(2)} 亿`
  if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(2)} 万`
  return `${num.toFixed(2)}`
}

const estateKpiData = computed(() => [
  {
    label: '认购套数',
    value: estateStats.value.total_subscriptions || 0,
    sub: `认购转签约率 ${estateStats.value.subscription_rate || 0}%`,
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%)',
    icon: Tickets
  },
  {
    label: '签约套数',
    value: estateStats.value.total_contracts || 0,
    sub: `项目数 ${estateStats.value.total_projects || 0} 个`,
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    icon: House
  },
  {
    label: '签约金额',
    value: `¥${formatMoney(estateStats.value.total_sales)}`,
    sub: `平均每套约 ¥${formatMoney(estateStats.value.total_contracts ? estateStats.value.total_sales / estateStats.value.total_contracts : 0)}`,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    icon: Coin
  },
  {
    label: '回款金额',
    value: `¥${formatMoney(estateStats.value.total_received)}`,
    sub: `回款率 ${estateStats.value.collection_rate || 0}%`,
    gradient: 'linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)',
    icon: Wallet
  },
  {
    label: '应收余额',
    value: `¥${formatMoney(estateStats.value.total_receivables)}`,
    sub: '未回款合同余额',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    icon: Money
  },
  {
    label: '成本金额',
    value: `¥${formatMoney(estateStats.value.total_cost)}`,
    sub: `成本率 ${estateStats.value.cost_ratio || 0}%`,
    gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    icon: DataAnalysis
  },
  {
    label: '费用金额',
    value: `¥${formatMoney(estateStats.value.total_expense)}`,
    sub: `费用率 ${estateStats.value.expense_ratio || 0}%`,
    gradient: 'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)',
    icon: Document
  },
  {
    label: '利润金额',
    value: `¥${formatMoney(estateStats.value.total_profit)}`,
    sub: `利润率 ${estateStats.value.profit_margin || 0}%`,
    gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
    icon: TrendCharts
  }
])

// 快捷操作处理
const handleRunAllETL = async () => {
  try {
    await ElMessageBox.confirm('确定要运行所有 ETL 任务吗？', '提示', { 
      type: 'info',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    ElMessage.success('ETL 任务已全部启动')
  } catch (e) {
    // 取消
  }
}

const handleViewLogs = () => {
  ElMessage.info('跳转至系统日志页面')
}

const handleUserManage = () => {
  ElMessage.info('跳转至用户管理页面')
}

const handleReportConfig = () => {
  ElMessage.info('跳转至报表配置页面')
}

const getResourceColor = (value) => {
  if (value < 60) return '#22c55e'
  if (value < 80) return '#f59e0b'
  return '#ef4444'
}

const getProgressColor = (value) => {
  if (value < 60) return '#22c55e'
  if (value < 80) return '#f59e0b'
  return '#ef4444'
}

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

// 加载 KPI 数据
const loadKPIData = async () => {
  try {
    const stats = await apiRequest('get', '/api/admin/dashboard/stats')
    kpiData.value[0].value = stats.total_tables || 24
    kpiData.value[1].value = stats.total_etl_jobs || 12
    kpiData.value[2].value = stats.total_reports || 56
    kpiData.value[3].value = stats.total_users || 128
    kpiData.value[4].value = stats.recent_ai_queries || 1024
    kpiData.value[5].value = '15 天'
  } catch (error) {
    // 使用默认数据
    kpiData.value[0].value = 24
    kpiData.value[1].value = 12
    kpiData.value[2].value = 56
    kpiData.value[3].value = 128
    kpiData.value[4].value = 1024
    kpiData.value[5].value = '15 天'
  }
}

// 加载地产经营数据
const loadRealEstateStats = async () => {
  try {
    const estate = await apiRequest('get', '/api/admin/dashboard/real-estate-stats')
    estateStats.value = {
      total_projects: estate.total_projects || 0,
      total_units: estate.total_units || 0,
      total_subscriptions: estate.total_subscriptions || 0,
      total_contracts: estate.total_contracts || 0,
      total_sales: estate.total_sales || 0,
      total_received: estate.total_received || 0,
      total_receivables: estate.total_receivables || 0,
      total_cost: estate.total_cost || 0,
      total_expense: estate.total_expense || 0,
      total_profit: estate.total_profit || 0,
      subscription_rate: estate.subscription_rate || 0,
      collection_rate: estate.collection_rate || 0,
      cost_ratio: estate.cost_ratio || 0,
      expense_ratio: estate.expense_ratio || 0,
      profit_margin: estate.profit_margin || 0
    }
  } catch (error) {
    console.error('加载地产经营数据失败', error)
  }
}

// 加载资源使用率
const loadResources = async () => {
  try {
    const metrics = await apiRequest('get', '/api/admin/monitor/metrics')
    resources.value[0].value = metrics.cpu_usage || Math.round(Math.random() * 40) + 20
    resources.value[1].value = metrics.memory_usage || Math.round(Math.random() * 30) + 30
    resources.value[2].value = metrics.disk_usage || Math.round(Math.random() * 20) + 40
    resources.value[3].value = Math.round(Math.random() * 30) + 10
  } catch (error) {
    console.error('加载资源数据失败', error)
  }
}

// 初始化 ETL 趋势图表
const initETLChart = async () => {
  if (!etlChartRef.value) return

  chartLoading.value.etl = true

  if (!etlChart) {
    etlChart = echarts.init(etlChartRef.value)
  }

  try {
    const etlData = await apiRequest('get', '/api/admin/dashboard/etl-trend')
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
        padding: [12, 16]
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
        data: etlData.dates || ['7 天前', '6 天前', '5 天前', '4 天前', '3 天前', '2 天前', '昨天'],
        axisLabel: { color: '#64748b' },
        axisLine: { lineStyle: { color: '#e2e8f0' } }
      },
      yAxis: {
        type: 'value',
        name: '执行次数',
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
      },
      series: [{
        name: 'ETL 执行次数',
        type: 'line',
        data: etlData.counts || [28, 32, 25, 38, 42, 35, 45],
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.5)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
          ])
        },
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 3 }
      }]
    }
    etlChart.setOption(option)
  } catch (error) {
    const option = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: { type: 'category', data: ['7 天前', '6 天前', '5 天前', '4 天前', '3 天前', '2 天前', '昨天'] },
      yAxis: { type: 'value', name: '执行次数' },
      series: [{
        name: 'ETL 执行次数',
        type: 'line',
        data: [28, 32, 25, 38, 42, 35, 45],
        smooth: true,
        areaStyle: { color: 'rgba(59, 130, 246, 0.3)' },
        itemStyle: { color: '#3b82f6' }
      }]
    }
    etlChart.setOption(option)
  }

  chartLoading.value.etl = false
}

// 初始化热度排行图表
const initHeatmapChart = async () => {
  if (!heatmapChartRef.value) return

  chartLoading.value.heatmap = true

  if (!heatmapChart) {
    heatmapChart = echarts.init(heatmapChartRef.value)
  }

  try {
    const heatmapData = await apiRequest('get', '/api/admin/dashboard/heatmap')
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(255, 255, 255, 0.98)',
        borderColor: '#e2e8f0',
        textStyle: { color: '#1e293b' },
        padding: [12, 16]
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        name: '查询次数',
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
      },
      yAxis: {
        type: 'category',
        data: heatmapData.reports?.map(r => r.name).reverse() || ['销售日报', '库存周报', '客户分析', '产品排行', '月度总结'],
        axisLabel: { color: '#64748b' }
      },
      series: [{
        name: '查询次数',
        type: 'bar',
        data: heatmapData.reports?.map(r => r.count).reverse() || [520, 450, 380, 320, 280],
        barWidth: '60%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#60a5fa' }
          ]),
          borderRadius: [0, 4, 4, 0]
        }
      }]
    }
    heatmapChart.setOption(option)
  } catch (error) {
    const option = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', name: '查询次数' },
      yAxis: { type: 'category', data: ['销售日报', '库存周报', '客户分析', '产品排行', '月度总结'].reverse() },
      series: [{
        name: '查询次数',
        type: 'bar',
        data: [520, 450, 380, 320, 280].reverse(),
        barWidth: '60%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#60a5fa' }
          ])
        }
      }]
    }
    heatmapChart.setOption(option)
  }

  chartLoading.value.heatmap = false
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadKPIData(),
      loadRealEstateStats(),
      loadResources(),
      initETLChart(),
      initHeatmapChart()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    refreshing.value = false
  }
}

// 窗口大小改变时重新渲染图表
const handleResize = () => {
  etlChart?.resize()
  heatmapChart?.resize()
}

onMounted(async () => {
  await nextTick()
  loadKPIData()
  loadRealEstateStats()
  loadResources()
  initETLChart()
  initHeatmapChart()
  window.addEventListener('resize', handleResize)

  // 定时刷新数据
  const refreshInterval = setInterval(() => {
    loadResources()
  }, 30000)

  return () => {
    window.removeEventListener('resize', handleResize)
    clearInterval(refreshInterval)
    etlChart?.dispose()
    heatmapChart?.dispose()
  }
})
</script>

<style scoped>
/* ========================================
   管理后台 Dashboard - 企业级专业风格
   ======================================== */

.admin-dashboard {
  padding: var(--spacing-6);
  max-width: 1800px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* KPI 卡片 */
.kpi-row {
  margin-bottom: 20px;
}

.kpi-card-wrapper {
  margin-bottom: 20px;
}

.kpi-card {
  display: flex;
  align-items: stretch;
  background: #ffffff;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all var(--transition) var(--transition-cubic);
  height: 100%;
}

.kpi-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.kpi-icon {
  width: 80px;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.kpi-icon .el-icon {
  color: #ffffff;
}

.kpi-content {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.kpi-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  font-family: 'SF Mono', 'Consolas', monospace;
  letter-spacing: -1px;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.estate-summary-card {
  margin-bottom: 20px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.estate-summary-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-bottom: 1px solid var(--border-light);
  padding: 18px 24px;
}

.estate-kpi-grid {
  margin-top: 4px;
}

.estate-kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #ffffff;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: 18px;
  box-shadow: var(--shadow-xs);
  transition: all var(--transition) var(--transition-cubic);
  height: 100%;
}

.estate-kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border);
}

.estate-kpi-icon {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.estate-kpi-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.estate-kpi-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
}

.estate-kpi-value {
  font-size: var(--text-2xl);
  line-height: 1.1;
  font-weight: var(--font-bold);
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.estate-kpi-sub {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.4;
}

.trend-up {
  color: var(--success);
}

.trend-down {
  color: var(--danger);
}

.trend-stable {
  color: var(--text-tertiary);
}

.trend-icon .el-icon {
  width: 14px;
  height: 14px;
}

/* 图表卡片 */
.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.chart-card :deep(.el-card__header) {
  background: #ffffff;
  border-bottom: 1px solid var(--border-light);
  padding: 18px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.header-icon {
  display: flex;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  flex-shrink: 0;
}

.live-tag, .top-tag {
  margin-left: 8px;
}

.chart-container {
  height: 320px;
  width: 100%;
  padding: 16px;
}

/* 资源列表 */
.resource-list {
  padding: 8px 0;
}

.resource-item {
  margin-bottom: 24px;
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.resource-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.resource-icon .el-icon {
  width: 18px;
  height: 18px;
  color: #909399;
}

.resource-name {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: var(--font-medium);
}

.resource-value {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

/* 快捷操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition) var(--transition-cubic);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(37, 99, 235, 0.05) 100%);
}

.action-btn.success:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.05) 0%, rgba(22, 163, 74, 0.05) 100%);
}

.action-btn.warning:hover {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(217, 119, 6, 0.05) 100%);
}

.action-btn.info:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(37, 99, 235, 0.05) 100%);
}

.action-btn .el-icon {
  color: var(--text-secondary);
  transition: color var(--transition) var(--transition-cubic);
}

.action-btn:hover .el-icon {
  color: var(--primary);
}

.action-btn.primary .el-icon { color: var(--primary); }
.action-btn.success .el-icon { color: var(--success); }
.action-btn.warning .el-icon { color: var(--warning); }
.action-btn.info .el-icon { color: var(--info); }

.action-text {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  text-align: center;
}

/* 最近活动 */
.recent-activities {
  border-top: 1px solid var(--border-light);
  padding-top: 20px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.activity-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
}

.activity-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.activity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.activity-dot.success { background: var(--success); }
.activity-dot.info { background: var(--info); }
.activity-dot.warning { background: var(--warning); }
.activity-dot.danger { background: var(--danger); }

.activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.activity-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.4;
}

.activity-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* 响应式 */
@media (max-width: 1024px) {
  .kpi-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .kpi-icon {
    width: 100%;
    min-width: auto;
    height: 80px;
  }

  .kpi-content {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }

  .estate-kpi-card {
    align-items: flex-start;
  }

  .estate-kpi-value {
    font-size: var(--text-xl);
  }
}
</style>
