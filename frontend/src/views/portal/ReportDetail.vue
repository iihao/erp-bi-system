<template>
  <div class="report-detail">
    <div v-loading="loading" class="report-content">
      <!-- 销售概览报表 -->
      <div v-if="reportId === 'sales-overview'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">销售概览</h2>
          <p class="report-desc">核心销售指标一览</p>
        </div>

        <el-row :gutter="20" class="kpi-row">
          <el-col :xs="24" :sm="12" :md="6" v-for="(kpi, index) in reportData.kpi" :key="index">
            <el-card class="kpi-card" shadow="hover">
              <template #header>
                <span class="kpi-title">{{ kpi.kpi_name }}</span>
              </template>
              <div class="kpi-value">
                <span class="number">{{ formatValue(kpi.kpi_value, kpi.unit) }}</span>
                <span class="unit">{{ kpi.unit }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="data-card" shadow="hover">
          <template #header>
            <span class="card-title">销售汇总</span>
          </template>
          <el-descriptions :column="2" border v-if="reportData.summary">
            <el-descriptions-item label="总销售额">{{ formatCurrency(reportData.summary.total_sales) }}</el-descriptions-item>
            <el-descriptions-item label="总订单数">{{ reportData.summary.total_orders?.toLocaleString() }} 单</el-descriptions-item>
            <el-descriptions-item label="总销售量">{{ reportData.summary.total_quantity?.toLocaleString() }} 件</el-descriptions-item>
            <el-descriptions-item label="平均订单价值">{{ formatCurrency(reportData.summary.avg_order_value) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>

      <!-- 销售趋势报表 -->
      <div v-else-if="reportId === 'sales-trend'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">销售趋势分析</h2>
          <p class="report-desc">近 12 个月销售变化趋势</p>
        </div>

        <div class="chart-options">
          <el-radio-group v-model="trendMonths" size="small" @change="loadReportData">
            <el-radio-button :label="6">近半年</el-radio-button>
            <el-radio-button :label="12">近一年</el-radio-button>
            <el-radio-button :label="18">近一年半</el-radio-button>
          </el-radio-group>
        </div>

        <el-card class="chart-card" shadow="hover">
          <div ref="trendChartRef" class="chart" style="height: 450px"></div>
        </el-card>

        <el-card class="data-card" shadow="hover" v-if="reportData.trend && reportData.trend.length > 0">
          <template #header>
            <span class="card-title">详细数据</span>
          </template>
          <el-table :data="reportData.trend" stripe style="width: 100%">
            <el-table-column prop="month" label="月份" width="120" />
            <el-table-column prop="sales_amount" label="销售额">
              <template #default="{ row }">{{ formatCurrency(row.sales_amount) }}</template>
            </el-table-column>
            <el-table-column prop="order_count" label="订单数" width="120">
              <template #default="{ row }">{{ row.order_count?.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="销售量" width="120">
              <template #default="{ row }">{{ row.quantity?.toLocaleString() }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 产品排行报表 -->
      <div v-else-if="reportId === 'product-ranking'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">产品销量排行榜</h2>
          <p class="report-desc">热销产品 Top 50</p>
        </div>

        <div class="chart-options">
          <el-radio-group v-model="rankingLimit" size="small" @change="loadReportData">
            <el-radio-button :label="10">Top 10</el-radio-button>
            <el-radio-button :label="20">Top 20</el-radio-button>
            <el-radio-button :label="50">Top 50</el-radio-button>
          </el-radio-group>
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <span class="card-title">销售额排行</span>
              </template>
              <div ref="rankingChartRef" class="chart" style="height: 400px"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card class="data-card" shadow="hover">
              <template #header>
                <span class="card-title">排行榜详情</span>
              </template>
              <el-table :data="reportData.ranking" stripe style="width: 100%" max-height="400">
                <el-table-column type="index" label="排名" width="60" align="center">
                  <template #default="{ $index }">
                    <span :class="['rank-badge', { 'top-3': $index < 3 }]">{{ $index + 1 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="product_name" label="产品名称" />
                <el-table-column prop="category" label="品类" width="100" />
                <el-table-column prop="total_amount" label="销售额" width="120">
                  <template #default="{ row }">{{ formatCurrency(row.total_amount) }}</template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 品类分析报表 -->
      <div v-else-if="reportId === 'category-analysis'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">品类分析</h2>
          <p class="report-desc">各品类销售表现分析</p>
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :lg="12">
            <el-card class="chart-card" shadow="hover">
              <template #header>
                <span class="card-title">品类销售占比</span>
              </template>
              <div ref="categoryChartRef" class="chart" style="height: 400px"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card class="data-card" shadow="hover">
              <template #header>
                <span class="card-title">品类数据详情</span>
              </template>
              <el-table :data="reportData.categories" stripe style="width: 100%" max-height="400">
                <el-table-column prop="category" label="品类" width="100" />
                <el-table-column prop="product_count" label="产品数" width="80" align="center" />
                <el-table-column prop="total_sales" label="销售额" width="120">
                  <template #default="{ row }">{{ formatCurrency(row.total_sales) }}</template>
                </el-table-column>
                <el-table-column prop="sales_ratio" label="占比">
                  <template #default="{ row }">
                    <el-progress :percentage="row.sales_ratio" :stroke-width="18" :show-text="false" />
                    <span class="ratio-text">{{ row.sales_ratio.toFixed(1) }}%</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 客户分析报表 -->
      <div v-else-if="reportId === 'customer-analysis'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">客户分析</h2>
          <p class="report-desc">客户类型、行业分布及价值分析</p>
        </div>

        <el-card class="data-card" shadow="hover">
          <template #header>
            <span class="card-title">客户分布详情</span>
          </template>
          <el-table :data="reportData.customers" stripe style="width: 100%">
            <el-table-column prop="customer_type" label="客户类型" width="120" />
            <el-table-column prop="industry" label="行业" width="100" />
            <el-table-column prop="customer_count" label="客户数" width="100" align="center" />
            <el-table-column prop="total_orders" label="订单总数" width="100" align="center" />
            <el-table-column prop="total_amount" label="销售总额" width="120">
              <template #default="{ row }">{{ formatCurrency(row.total_amount) }}</template>
            </el-table-column>
            <el-table-column prop="avg_order_value" label="客单价" width="100">
              <template #default="{ row }">{{ formatCurrency(row.avg_order_value) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 利润分析报表 -->
      <div v-else-if="reportId === 'profit-analysis'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">利润分析</h2>
          <p class="report-desc">毛利率、净利率趋势分析</p>
        </div>

        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">利润趋势</span>
          </template>
          <div ref="profitChartRef" class="chart" style="height: 400px"></div>
        </el-card>
      </div>

      <!-- 库存报表 -->
      <div v-else-if="reportId === 'inventory-report'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">库存报表</h2>
          <p class="report-desc">库存周转率、滞销商品分析</p>
        </div>

        <el-card class="data-card" shadow="hover">
          <template #header>
            <span class="card-title">库存详情</span>
          </template>
          <el-table :data="reportData.inventory" stripe style="width: 100%">
            <el-table-column prop="category" label="品类" width="120" />
            <el-table-column prop="stock_quantity" label="库存数量" width="100" align="center" />
            <el-table-column prop="stock_value" label="库存金额" width="120">
              <template #default="{ row }">{{ formatCurrency(row.stock_value) }}</template>
            </el-table-column>
            <el-table-column prop="turnover_rate" label="周转率" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.turnover_rate >= 7 ? 'success' : row.turnover_rate >= 5 ? 'warning' : 'danger'">
                  {{ row.turnover_rate }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="slow_items" label="滞销品数" width="100" align="center" />
          </el-table>
        </el-card>
      </div>

      <!-- 预测报表 -->
      <div v-else-if="reportId === 'forecast-report'" class="report-section">
        <div class="report-header">
          <h2 class="report-title">销售预测</h2>
          <p class="report-desc">基于历史数据的智能预测</p>
        </div>

        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">未来 6 个月销售预测</span>
          </template>
          <div ref="forecastChartRef" class="chart" style="height: 400px"></div>
        </el-card>
      </div>

      <!-- 未知报表 -->
      <div v-else class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p>暂无更多详情</p>
      </div>
    </div>

    <!-- 返回列表 -->
    <div class="back-action">
      <el-button @click="goBack">
        <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15,18 9,12 15,6"/>
        </svg>
        返回列表
      </el-button>
      <el-button @click="loadReportData" :loading="loading" type="primary">
        <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const reportId = ref('')
const reportData = ref({})

// 图表实例
let trendChart = null
let rankingChart = null
let categoryChart = null
let profitChart = null
let forecastChart = null

// 图表 DOM 引用
const trendChartRef = ref(null)
const rankingChartRef = ref(null)
const categoryChartRef = ref(null)
const profitChartRef = ref(null)
const forecastChartRef = ref(null)

// 参数
const trendMonths = ref(12)
const rankingLimit = ref(10)

// 格式化金额
const formatCurrency = (value) => {
  if (!value) return '¥0'
  const num = parseFloat(value)
  if (isNaN(num)) return '¥0'
  if (num >= 100000000) {
    return '¥' + (num / 100000000).toFixed(2) + '亿'
  }
  if (num >= 10000) {
    return '¥' + (num / 10000).toFixed(2) + '万'
  }
  return '¥' + num.toFixed(2)
}

// 格式化值
const formatValue = (value, unit) => {
  if (!value) return '0'
  const num = parseFloat(value)
  if (isNaN(num)) return '0'
  if (unit === '元') {
    if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
    if (num >= 10000) return (num / 10000).toFixed(2) + '万'
  }
  return num.toLocaleString()
}

// 加载报表数据
const loadReportData = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const params = new URLSearchParams({
      limit: rankingLimit.value,
      months: trendMonths.value
    })

    const response = await fetch(`/api/portal/report/${reportId.value}?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        router.push('/portal/login')
        return
      }
      if (response.status === 403) {
        ElMessage.error('您没有权限访问该报表')
        router.push('/portal/reports')
        return
      }
      throw new Error('加载数据失败')
    }

    const data = await response.json()
    reportData.value = data.data || {}

    // 渲染对应图表
    await nextTick()
    renderCharts()

  } catch (error) {
    console.error('加载报表数据失败:', error)
    ElMessage.error('加载报表数据失败')
  } finally {
    loading.value = false
  }
}

// 渲染图表
const renderCharts = () => {
  if (reportId.value === 'sales-trend') {
    renderTrendChart()
  } else if (reportId.value === 'product-ranking') {
    renderRankingChart()
  } else if (reportId.value === 'category-analysis') {
    renderCategoryChart()
  } else if (reportId.value === 'profit-analysis') {
    renderProfitChart()
  } else if (reportId.value === 'forecast-report') {
    renderForecastChart()
  }
}

// 渲染销售趋势图
const renderTrendChart = () => {
  if (!trendChartRef.value || !reportData.value.trend) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  const data = reportData.value.trend
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    legend: {
      data: ['销售额', '订单数'],
      textStyle: { color: '#64748b' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(item => item.month),
      axisLabel: { color: '#64748b' }
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
        axisLabel: { color: '#64748b' },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        data: data.map(item => item.sales_amount),
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
        name: '订单数',
        type: 'bar',
        yAxisIndex: 1,
        data: data.map(item => item.order_count),
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
}

// 渲染产品排行图
const renderRankingChart = () => {
  if (!rankingChartRef.value || !reportData.value.ranking) return

  if (!rankingChart) {
    rankingChart = echarts.init(rankingChartRef.value)
  }

  const data = reportData.value.ranking
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => `${params[0].name}<br/>销售额：${formatCurrency(params[0].value)}`,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    grid: { left: '3%', right: '10%', bottom: '3%', top: '3%', containLabel: true },
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
      data: data.map(item => item.product_name).reverse(),
      axisLabel: { color: '#64748b' }
    },
    series: [{
      name: '销售额',
      type: 'bar',
      data: data.map(item => item.total_amount).reverse(),
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
    }]
  }

  rankingChart.setOption(option)
}

// 渲染品类占比图
const renderCategoryChart = () => {
  if (!categoryChartRef.value || !reportData.value.categories) return

  if (!categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value)
  }

  const data = reportData.value.categories
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
      textStyle: { color: '#64748b' }
    },
    color: ['#2563eb', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6'],
    series: [{
      name: '销售额',
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['35%', '50%'],
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' }
      },
      data: data.map(item => ({ name: item.category, value: item.total_sales }))
    }]
  }

  categoryChart.setOption(option)
}

// 渲染利润趋势图
const renderProfitChart = () => {
  if (!profitChartRef.value || !reportData.value.profit) return

  if (!profitChart) {
    profitChart = echarts.init(profitChartRef.value)
  }

  const data = reportData.value.profit
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    legend: {
      data: ['毛利润', '净利润', '毛利率', '净利率'],
      textStyle: { color: '#64748b' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(item => item.month),
      axisLabel: { color: '#64748b' }
    },
    yAxis: [
      {
        type: 'value',
        name: '金额',
        axisLabel: {
          formatter: value => (value / 10000).toFixed(0) + '万',
          color: '#64748b'
        },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
      },
      {
        type: 'value',
        name: '比率',
        axisLabel: {
          formatter: value => value + '%',
          color: '#64748b'
        },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '毛利润',
        type: 'bar',
        data: data.map(item => item.gross_profit),
        itemStyle: { color: '#10b981' }
      },
      {
        name: '净利润',
        type: 'bar',
        data: data.map(item => item.net_profit),
        itemStyle: { color: '#2563eb' }
      },
      {
        name: '毛利率',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(item => item.gross_margin),
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 3 }
      },
      {
        name: '净利率',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(item => item.net_margin),
        itemStyle: { color: '#8b5cf6' },
        lineStyle: { width: 3 }
      }
    ]
  }

  profitChart.setOption(option)
}

// 渲染预测图
const renderForecastChart = () => {
  if (!forecastChartRef.value || !reportData.value.forecast) return

  if (!forecastChart) {
    forecastChart = echarts.init(forecastChartRef.value)
  }

  const data = reportData.value.forecast
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    legend: {
      data: ['预测销售额', '置信区间'],
      textStyle: { color: '#64748b' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(item => item.month),
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: value => (value / 10000).toFixed(0) + '万',
        color: '#64748b'
      },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    series: [
      {
        name: '预测销售额',
        type: 'line',
        smooth: true,
        data: data.map(item => item.predicted_sales),
        itemStyle: { color: '#8b5cf6' },
        lineStyle: { width: 3 },
        symbolSize: 8
      },
      {
        name: '置信区间',
        type: 'line',
        smooth: true,
        data: data.map(item => [item.confidence_interval_low, item.confidence_interval_high]),
        itemStyle: { color: '#a78bfa' },
        lineStyle: { width: 1, type: 'dashed' }
      }
    ]
  }

  forecastChart.setOption(option)
}

// 返回
const goBack = () => {
  router.back()
}

// 窗口大小变化
const handleResize = () => {
  trendChart?.resize()
  rankingChart?.resize()
  categoryChart?.resize()
  profitChart?.resize()
  forecastChart?.resize()
}

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  reportId.value = newId
  loadReportData()
}, { immediate: true })

onMounted(() => {
  reportId.value = route.params.id
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  rankingChart?.dispose()
  categoryChart?.dispose()
  profitChart?.dispose()
  forecastChart?.dispose()
})
</script>

<style scoped>
.report-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.report-content {
  min-height: calc(100vh - 200px);
}

.report-section {
  margin-bottom: 24px;
}

.report-header {
  margin-bottom: 24px;
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.report-title {
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.report-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.chart-options {
  margin-bottom: 16px;
  background: #fff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  margin-bottom: 20px;
  transition: all 0.3s;
  border: 1px solid #e2e8f0;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.kpi-card :deep(.el-card__header) {
  padding: 14px 20px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-bottom: none;
}

.kpi-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
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
  color: #2563eb;
  margin-right: 6px;
  font-family: 'SF Mono', 'Consolas', monospace;
}

.kpi-value .unit {
  font-size: 13px;
  color: #64748b;
}

.chart-card,
.data-card {
  margin-bottom: 20px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.chart-card:hover,
.data-card:hover {
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.chart-card :deep(.el-card__header),
.data-card :deep(.el-card__header) {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.chart {
  width: 100%;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f1f5f9;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
}

.rank-badge.top-3 {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #fff;
}

.ratio-text {
  font-size: 12px;
  color: #64748b;
  margin-left: 8px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 12px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #cbd5e1;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 14px;
  color: #94a3b8;
}

.back-action {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.button-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  color: currentColor;
}

/* 响应式 */
@media (max-width: 768px) {
  .report-header {
    padding: 20px;
  }

  .report-title {
    font-size: 18px;
  }
}
</style>
