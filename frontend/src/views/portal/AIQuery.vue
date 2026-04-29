<template>
  <div class="ai-query-page">
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="22" class="header-icon"><ChatDotRound /></el-icon>
            <span class="title">AI 智能问数</span>
            <el-tag type="success" size="small">自然语言查询</el-tag>
          </div>
          <el-tag type="info" effect="plain" round>Qwen3.5-Plus</el-tag>
        </div>
      </template>

      <!-- 查询输入区 -->
      <div class="query-section">
        <el-input
          v-model="question"
          type="textarea"
          :rows="2"
          placeholder="例如：上个月签约回款趋势"
          @keyup.enter.ctrl="handleQuery"
          class="question-input"
        />
        <div class="query-actions">
          <el-button type="primary" @click="handleQuery" :loading="loading" size="large" round class="query-btn">
            <el-icon><Search /></el-icon>
            智能查询
          </el-button>
        </div>
      </div>

      <!-- 快捷问题 -->
      <div class="quick-section">
        <div class="quick-label">
          <el-icon><Lightning /></el-icon>
          <span>热门问题</span>
        </div>
        <div class="quick-grid">
          <el-tag
            v-for="q in quickQuestions"
            :key="q"
            @click="question = q"
            class="question-tag"
            effect="plain"
            round
          >
            {{ q }}
          </el-tag>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 查询结果 -->
      <div v-else-if="result" class="result-section">
        <!-- 智能解读 -->
        <div v-if="result.insight" class="insight-card">
          <div class="section-header">
            <span>
              <el-icon><Lightning /></el-icon>
              结论摘要
            </span>
            <el-tag type="success" effect="plain">{{ result.sourceLabel }}</el-tag>
          </div>
          <div class="insight-content">
            <p>{{ result.insight }}</p>
            <div v-if="result.profile?.highlights?.length" class="insight-bullets">
              <div v-for="(item, index) in result.profile.highlights" :key="index" class="insight-bullet">
                <span class="insight-bullet-dot"></span>
                <span>{{ item }}</span>
              </div>
            </div>
            <div v-if="result.profile?.recommendedTables?.length" class="thinking-tags">
              <el-tag
                v-for="table in result.profile.recommendedTables"
                :key="table"
                size="small"
                effect="plain"
                round
              >
                {{ table }}
              </el-tag>
            </div>
          </div>
        </div>

        <div v-if="result.profile" class="overview-card">
          <div class="section-header">
            <span>
              <el-icon><DataAnalysis /></el-icon>
              结果概览
            </span>
          </div>
          <el-row :gutter="12" class="overview-grid">
            <el-col v-for="item in result.profile.cards" :key="item.label" :xs="12" :sm="8" :md="6">
              <div class="overview-item">
                <div class="overview-label">{{ item.label }}</div>
                <div class="overview-value">{{ item.value }}</div>
                <div class="overview-sub">{{ item.sub }}</div>
              </div>
            </el-col>
          </el-row>
          <div v-if="result.profile.fieldTags?.length" class="field-tags">
            <el-tag
              v-for="field in result.profile.fieldTags"
              :key="field"
              size="small"
              effect="plain"
              round
            >
              {{ field }}
            </el-tag>
          </div>
        </div>

        <!-- 可视化图表 -->
        <div v-if="result.data && result.data.length > 0 && result.chartConfig" class="chart-card">
          <div class="section-header">
            <span>
              <el-icon><TrendCharts /></el-icon>
              数据可视化
            </span>
            <el-radio-group v-model="chartType" size="small" @change="onChartTypeChange">
              <el-radio-button label="bar">柱状图</el-radio-button>
              <el-radio-button label="line">折线图</el-radio-button>
              <el-radio-button label="pie">饼图</el-radio-button>
              <el-radio-button label="table">表格</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="chartContainer" class="chart-container" style="height: 400px;"></div>
        </div>

        <!-- 数据结果 -->
        <div v-if="result.data && result.data.length > 0" class="data-card">
          <div class="section-header">
            <span>
              <el-icon><DataAnalysis /></el-icon>
              数据明细（{{ result.data.length }} 条）
            </span>
            <el-button size="small" @click="exportData">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
          <el-table :data="result.data" stripe border class="result-table" max-height="400">
          <el-table-column
              v-for="col in result.columns"
              :key="col"
              :prop="col"
              :label="getFieldLabel(col)"
              min-width="120"
            />
          </el-table>
        </div>

        <el-collapse class="detail-collapse" v-if="result">
          <el-collapse-item title="查看查询细节" name="detail">
            <div v-if="result.thinking" class="thinking-block">
              <p><strong>命中来源：</strong>{{ result.thinking.match_source || 'AI 在线生成' }}</p>
              <p><strong>推荐表：</strong>{{ (result.thinking.recommended_tables || []).join('、') || '系统自动判断' }}</p>
              <p><strong>说明：</strong>{{ result.thinking.reasoning || result.explanation || '系统已完成问数' }}</p>
            </div>
            <pre v-if="result.sql" class="sql-code">{{ result.sql }}</pre>
          </el-collapse-item>
        </el-collapse>

        <el-empty v-if="!result.data || result.data.length === 0" description="没有查询到数据，试试换个时间或换一种说法" />
      </div>

      <!-- 初始状态 -->
      <div v-else class="empty-state">
        <el-empty description="输入问题，AI 帮您查询数据" />

        <!-- 查询历史 -->
        <div class="history-section">
          <h4>
            <el-icon><Clock /></el-icon>
            最近查询
          </h4>
          <ul class="history-list">
            <li v-for="(h, index) in queryHistory" :key="index" @click="loadHistory(h)" class="history-item">
              <span class="history-question">{{ h.question }}</span>
              <span class="history-time">{{ h.time }}</span>
            </li>
          </ul>
        </div>
      </div>
    </el-card>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  ChatDotRound, Lightning, Search, TrendCharts, DataAnalysis,
  Download, Clock
} from '@element-plus/icons-vue'

const question = ref('')
const loading = ref(false)
const result = ref(null)
const quotaRemaining = ref(100)
const dailyQuota = ref(100)
const chartType = ref('bar')
const chartContainer = ref(null)
let chartInstance = null

const quickQuestions = [
  '各项目去化率排名',
  '本月回款总额及环比',
  '客户跟进记录最多的前 10 位',
  '各项目销售目标达成率',
  '购买金额最高的客户',
  '各项目的房源状态分布',
  '本月退款金额统计',
  '集团现金流分析',
  '各项目成本与预算差异',
  '各户型面积均价排名',
  '应收逾期账款明细',
  '各项目净利润率',
  '认购转化率统计',
  '各月回款趋势',
  '各城市销售额排名'
]

const queryHistory = ref([])

// API 请求封装
const apiRequest = async (method, url, data = {}) => {
  const token = localStorage.getItem('token')
  const config = {
    method: method.toUpperCase(),
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  if (method.toUpperCase() !== 'GET' && Object.keys(data).length > 0) {
    config.body = JSON.stringify(data)
  }

  try {
    const response = await fetch(url, config)
    const text = await response.text()

    try {
      const parsed = JSON.parse(text)
      if (!response.ok) {
        throw new Error(parsed.detail || parsed.message || '请求失败')
      }
      return parsed
    } catch (parseError) {
      if (!response.ok) {
        throw new Error(text || '请求失败')
      }
      return text
    }
  } catch (error) {
    throw error
  }
}

const handleQuery = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  if (quotaRemaining.value <= 0) {
    ElMessage.warning('今日查询配额已用完，请明天再来')
    return
  }

  loading.value = true
  result.value = null

  try {
    const res = await apiRequest('POST', '/ai-query/execute-query', {
      question: question.value,
      top_k: 10
    })

    result.value = {
      sql: res.sql,
      explanation: res.explanation,
      data: res.data,
      columns: res.columns,
      insight: generateInsight(res.data, res.columns, question.value),
      chartConfig: res.data && res.data.length > 0 ? { enabled: true } : null,
      thinking: res.thinking || null,
      profile: buildResultProfile(res.data, res.columns, res.thinking, res.explanation, question.value),
      sourceLabel: getSourceLabel(res.thinking)
    }

    if (res.chart_type && res.data && res.data.length > 0) {
      chartType.value = res.chart_type
    }

    saveQueryHistory(question.value, res.sql)
    quotaRemaining.value--

    if (res.data && res.data.length > 0) {
      await nextTick()
      renderChart(res.data, res.columns)
    }

    ElMessage.success('查询成功')
  } catch (error) {
    ElMessage.error('查询失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const exportData = () => {
  const data = JSON.stringify(result.value.data, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai-query-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据已导出')
}

const saveQueryHistory = (question, sql) => {
  const history = {
    question: question,
    sql: sql,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  queryHistory.value.unshift(history)
  if (queryHistory.value.length > 10) {
    queryHistory.value.pop()
  }
}

const loadHistory = (history) => {
  question.value = history.question
}

// 渲染图表
const renderChart = (data, columns) => {
  if (!chartContainer.value || !data || data.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartContainer.value)

  const { xAxis, series, yAxisData } = analyzeChartData(data, columns)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLabel: {
        interval: 0,
        rotate: 30,
        fontSize: 11
      },
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: yAxisData,
    series: series
  }

  chartInstance.setOption(option)

  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

// 图表颜色
const chartColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']

const fieldLabelMap = {
  month: '月份',
  date: '日期',
  day: '日期',
  year: '年份',
  project_name: '项目名称',
  project: '项目',
  project_id: '项目ID',
  building_name: '楼栋名称',
  building_id: '楼栋ID',
  unit_name: '房源名称',
  unit_id: '房源ID',
  customer_name: '客户名称',
  customer_id: '客户ID',
  city: '城市',
  province: '省份',
  category: '分类',
  name: '名称',
  status: '状态',
  count: '数量',
  total_count: '总数量',
  total_sales: '签约金额',
  sales_amount: '签约金额',
  total_amount: '总金额',
  amount: '金额',
  received_amount: '回款金额',
  total_received: '回款金额',
  receivables: '应收余额',
  total_receivables: '应收余额',
  total_cost: '成本金额',
  cost_amount: '成本金额',
  total_expense: '费用金额',
  fee_amount: '费用金额',
  profit: '利润',
  total_profit: '利润金额',
  profit_margin: '利润率',
  collection_rate: '回款率',
  subscription_rate: '认购转签约率',
  sell_through_rate: '去化率',
  contract_count: '签约套数',
  total_units: '房源总数',
  total_contracts: '签约套数',
  total_subscriptions: '认购套数',
  order_count: '订单数',
  quantity: '数量'
}

const getFieldLabel = (field) => {
  if (!field) return '字段'
  const key = String(field).trim()
  if (fieldLabelMap[key]) return fieldLabelMap[key]
  const lower = key.toLowerCase()
  if (fieldLabelMap[lower]) return fieldLabelMap[lower]
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim()
}

// 分析图表数据
const analyzeChartData = (data, columns) => {
  if (!data || data.length === 0 || !columns || columns.length < 2) {
    return { xAxis: [], series: [], yAxisData: { type: 'value' } }
  }

  let dimensionField = columns.find(c => {
    const sample = data[0]?.[c]
    return sample !== null && sample !== undefined && typeof sample === 'string' && String(sample).length < 30
  }) || columns[0]

  const xAxis = data.map(item => String(item[dimensionField] ?? ''))

  const measureFields = columns.filter(c => {
    if (c === dimensionField) return false
    const sample = data[0]?.[c]
    return sample !== null && sample !== undefined && !isNaN(Number(sample))
  })

  // 柱状图/折线图
  const series = measureFields.slice(0, 3).map((field, idx) => ({
    name: getFieldLabel(field),
    type: chartType.value,
    data: data.map(item => Number(item[field]) || 0),
    itemStyle: {
      color: chartColors[idx % chartColors.length]
    },
    label: {
      show: chartType.value !== 'pie' && data.length <= 15,
      position: 'top',
      fontSize: 10,
      formatter: (p) => {
        const v = p.value
        if (Math.abs(v) >= 10000) return (v / 10000).toFixed(1) + '万'
        return v
      }
    }
  }))

  // 饼图特殊处理
  if (chartType.value === 'pie') {
    const mainField = measureFields[0] || columns[1]
    series.length = 0
    series.push({
      name: getFieldLabel(mainField),
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {c} ({d}%)',
        fontSize: 11
      },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold' }
      },
      data: data.map((item, index) => ({
        name: String(item[dimensionField]),
        value: Number(item[mainField]) || 0,
        itemStyle: { color: chartColors[index % chartColors.length] }
      }))
    })
  }

  const yAxisData = {
    type: 'value',
    axisLabel: {
      formatter: (v) => {
        if (Math.abs(v) >= 10000) return (v / 10000).toFixed(0) + '万'
        return v
      }
    }
  }

  return { xAxis, series, yAxisData }
}

// 图表类型切换
const onChartTypeChange = () => {
  if (result.value?.data && result.value?.columns) {
    renderChart(result.value.data, result.value.columns)
  }
}

// 生成智能解读
const generateInsight = (data, columns, question) => {
  if (!data || data.length === 0 || !columns || columns.length < 2) {
    return '暂无数据可分析'
  }

  const dimensionField = columns[0]
  const measureField = columns[1]

  const values = data.map(item => Number(item[measureField]) || 0)
  const total = values.reduce((sum, val) => sum + val, 0)
  const avg = total / values.length
  const max = Math.max(...values)
  const min = Math.min(...values)
  const maxItem = data.find(item => Number(item[measureField]) === max)
  const minItem = data.find(item => Number(item[measureField]) === min)

  const questionLower = question.toLowerCase()

  if (questionLower.includes('最高') || questionLower.includes('最大')) {
    return `查询结果显示，${maxItem ? maxItem[dimensionField] : '该项'}的${getFieldLabel(measureField)}最高，达到${max}。${data.length}个数据项的${getFieldLabel(measureField)}总计为${total}，平均值为${avg.toFixed(2)}。`
  }

  if (questionLower.includes('最低') || questionLower.includes('最小')) {
    return `查询结果显示，${minItem ? minItem[dimensionField] : '该项'}的${getFieldLabel(measureField)}最低，为${min}。${data.length}个数据项的${getFieldLabel(measureField)}总计为${total}，平均值为${avg.toFixed(2)}。`
  }

  if (questionLower.includes('占比') || questionLower.includes('比例')) {
    const percentages = data.map(item => {
      const value = Number(item[measureField]) || 0
      const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
      return `${item[dimensionField]}：${percentage}%`
    }).join('，')
    return `各项目的占比情况如下：${percentages}。总计：${total}。`
  }

  if (questionLower.includes('总额') || questionLower.includes('总计') || questionLower.includes('多少')) {
    return `查询结果显示，${getFieldLabel(measureField)}总计为${total}。共有${data.length}条记录，平均值为${avg.toFixed(2)}。其中最高值为${max}（${maxItem ? maxItem[dimensionField] : '未知'}），最低值为${min}（${minItem ? minItem[dimensionField] : '未知'}）。`
  }

  return `查询共返回${data.length}条数据。${getFieldLabel(measureField)}的总计为${total}，平均值为${avg.toFixed(2)}。最高值为${max}（${maxItem ? maxItem[dimensionField] : '未知'}），最低值为${min}（${minItem ? minItem[dimensionField] : '未知'}）。`
}

const formatBigNumber = (value) => {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0'
  if (Math.abs(num) >= 100000000) return `${(num / 100000000).toFixed(2)}亿`
  if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(2)}万`
  return num.toFixed(2)
}

const getSourceLabel = (thinking) => {
  const source = thinking?.match_source || ''
  if (String(source).includes('标准库')) return '标准库命中'
  if (String(source).includes('拦截')) return '安全拦截'
  return 'AI 在线生成'
}

const buildResultProfile = (data, columns, thinking, explanation, questionText) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) return null

  const dimensionField = columns.find(col => {
    const sample = data[0]?.[col]
    return sample !== null && sample !== undefined && typeof sample === 'string'
  }) || columns[0]

  const numericFields = columns.filter(col => {
    if (col === dimensionField) return false
    return data.some(item => item[col] !== null && item[col] !== undefined && !Number.isNaN(Number(item[col])))
  })

  const primaryField = numericFields[0] || columns.find(col => col !== dimensionField) || columns[0]
  const values = primaryField ? data.map(item => Number(item[primaryField]) || 0) : []
  const total = values.reduce((sum, val) => sum + val, 0)
  const avg = values.length ? total / values.length : 0
  const max = values.length ? Math.max(...values) : 0
  const min = values.length ? Math.min(...values) : 0
  const maxItem = primaryField ? data.find(item => Number(item[primaryField]) === max) : null
  const minItem = primaryField ? data.find(item => Number(item[primaryField]) === min) : null

  const cards = [
    { label: '记录数', value: data.length, sub: '返回行数' },
    { label: '字段数', value: columns.length, sub: '输出列数' },
    { label: '数值字段', value: numericFields.length, sub: '可统计指标' }
  ]

  if (primaryField) {
    cards.push(
      { label: '核心指标总计', value: formatBigNumber(total), sub: getFieldLabel(primaryField) },
      { label: '平均值', value: formatBigNumber(avg), sub: getFieldLabel(primaryField) }
    )
  }

  if (maxItem) {
    cards.push({ label: '最大值', value: formatBigNumber(max), sub: String(maxItem[dimensionField] ?? '未知') })
  }

  const highlights = []
  if (primaryField && data.length > 0) {
    highlights.push(`主指标「${getFieldLabel(primaryField)}」合计 ${formatBigNumber(total)}，平均 ${formatBigNumber(avg)}`)
    if (maxItem) {
      highlights.push(`最高值来自「${String(maxItem[dimensionField] ?? '未知')}」`)
    }
    if (minItem) {
      highlights.push(`最低值来自「${String(minItem[dimensionField] ?? '未知')}」`)
    }
  }

  if (thinking?.recommended_tables?.length) {
    highlights.push(`优先使用：${thinking.recommended_tables.slice(0, 3).join('、')}`)
  }

  if (thinking?.reasoning) {
    highlights.push(thinking.reasoning)
  } else if (explanation) {
    highlights.push(String(explanation).slice(0, 100))
  }

  return {
    cards: cards.slice(0, 6),
    highlights: highlights.slice(0, 4),
    recommendedTables: thinking?.recommended_tables || [],
    fieldTags: columns.slice(0, 8).map(getFieldLabel)
  }
}

// 加载用户配额
const loadQuota = async () => {
  try {
    const quota = await apiRequest('get', '/api/portal/ai-query/quota')
    quotaRemaining.value = quota.remaining || 100
    dailyQuota.value = quota.daily || 100
  } catch (error) {
    console.error('加载配额失败', error)
  }
}

onMounted(() => {
  loadQuota()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.ai-query-page {
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 24%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.1), transparent 20%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  min-height: 100%;
}

.query-card {
  max-width: 1000px;
  margin: 0 auto 20px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(240px, 0.8fr);
  gap: 16px;
  padding: 18px;
  margin-bottom: 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(14, 165, 233, 0.06));
  border: 1px solid rgba(59, 130, 246, 0.12);
}

.hero-copy h2 {
  margin: 6px 0 8px;
  font-size: 22px;
  line-height: 1.25;
  color: #0f172a;
}

.hero-copy p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: #475569;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
}

.hero-stats {
  display: grid;
  gap: 10px;
}

.hero-stat {
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.hero-stat-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.hero-stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.helper-panel {
  margin-bottom: 20px;
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.helper-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
}

.helper-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.helper-item {
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.helper-item-title {
  font-size: 12px;
  font-weight: 600;
  color: #2563eb;
  margin-bottom: 4px;
}

.helper-item-desc {
  font-size: 13px;
  color: #334155;
  line-height: 1.6;
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
}

.header-icon {
  color: #2563eb;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.query-section {
  margin-bottom: 20px;
}

.question-input {
  margin-bottom: 12px;
}

.question-input :deep(.el-textarea__inner) {
  border-radius: 14px;
  padding: 16px 18px;
  font-size: 14px;
  line-height: 1.6;
  border-color: rgba(148, 163, 184, 0.22);
}

.query-actions {
  display: flex;
  justify-content: flex-end;
}

.query-btn {
  padding: 12px 32px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  box-shadow: 0 10px 22px rgba(37, 99, 235, 0.18);
}

.quick-section {
  margin-bottom: 20px;
}

.quick-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #475569;
  font-size: 14px;
  margin-bottom: 10px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.question-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 12px;
  transition: all 0.3s;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-tag:hover {
  background-color: rgba(37, 99, 235, 0.08);
  border-color: #2563eb;
  color: #2563eb;
}

.loading-state,
.result-section,
.empty-state {
  margin-top: 20px;
}

.sql-card,
.data-card,
.chart-card,
.insight-card,
.detail-collapse {
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
}

.insight-card {
  background: linear-gradient(135deg, #1d4ed8 0%, #0f766e 100%);
  color: white;
  border: none;
}

.insight-content p {
  margin: 0;
  line-height: 1.8;
  font-size: 14px;
}

.insight-bullets {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.insight-bullet {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.insight-bullet-dot {
  width: 6px;
  height: 6px;
  margin-top: 7px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.9;
  flex: 0 0 auto;
}

.overview-card {
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
}

.overview-grid {
  margin-top: 8px;
}

.overview-item {
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  padding: 14px;
  min-height: 96px;
}

.overview-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.overview-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
  margin-bottom: 4px;
}

.overview-sub {
  font-size: 12px;
  color: #475569;
}

.field-tags,
.thinking-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.chart-card {
  background: #fff;
}

.chart-container {
  width: 100%;
  margin-top: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #0f172a;
  font-size: 14px;
}

.sql-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
}

.thinking-block {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
  color: #334155;
  font-size: 13px;
  line-height: 1.7;
}

.result-table {
  margin-top: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.result-table :deep(.el-table__header th) {
  background-color: #f1f5f9;
  color: #475569;
  font-weight: 600;
}

.history-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.history-section h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 12px 0;
}

.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  margin-bottom: 8px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.history-question {
  color: #475569;
  font-size: 13px;
}

.history-time {
  color: #94a3b8;
  font-size: 12px;
}

.notice-alert {
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 8px;
}

.notice-content {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.notice-content span {
  font-weight: 600;
}

.notice-icon {
  margin-top: 2px;
}

.notice-content ul {
  margin: 0 0 0 8px;
  padding-left: 16px;
}

.notice-content li {
  color: #64748b;
  font-size: 13px;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .ai-query-page {
    padding: 16px;
  }

  .hero-panel,
  .helper-grid {
    grid-template-columns: 1fr;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .query-btn {
    width: 100%;
    justify-content: center;
  }

  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
