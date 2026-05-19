<template>
  <div class="ai-query-fullscreen" :class="{ dark: isDark }">
    <!-- 主区域 -->
    <main class="chat-main">
      <!-- 头部 -->
      <header class="chat-header">
        <div class="header-left">
          <span class="source-badge">
            <el-tag :type="sourceTagType" effect="plain" size="small">{{ sourceLabel }}</el-tag>
          </span>
        </div>
        <div class="header-right">
          <el-button text size="small" @click="newConversation" class="new-btn">
            <el-icon><Plus /></el-icon>
            新对话
          </el-button>
          <el-button text size="small" @click="toggleTheme" class="theme-btn" :title="isDark ? '切换亮色' : '切换暗色'">
            <el-icon><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
          <el-button text size="small" @click="clearCurrentChat">
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainerRef">
        <!-- 欢迎屏幕 -->
        <div v-if="messages.length === 0 && !loading" class="welcome-screen">
          <div class="welcome-icon">
            <el-icon :size="48" color="var(--accent)"><ChatDotRound /></el-icon>
          </div>
          <h2>AI 智能问数</h2>
          <p>用自然语言查询业务数据，支持多表 JOIN、聚合、筛选等复杂查询</p>
          <div class="suggestion-grid">
            <div
              v-for="s in suggestions"
              :key="s"
              class="suggestion-item"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar :size="30" v-if="msg.role === 'user'" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <el-avatar :size="30" v-else class="ai-avatar">
                <el-icon><Cpu /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-text" v-if="msg.role === 'user'">{{ msg.content }}</div>

              <div v-else class="ai-response">
                <!-- 智能解读 -->
                <div v-if="msg.insight" class="ai-insight">
                  <div class="ai-insight-header">
                    <el-icon :size="14"><Lightning /></el-icon>
                    <span>结论摘要</span>
                  </div>
                  <div class="ai-insight-body">
                    <p>{{ msg.insight }}</p>
                    <div v-if="msg.highlights?.length" class="insight-bullets">
                      <div v-for="(item, i) in msg.highlights" :key="i" class="insight-bullet">
                        <span class="insight-bullet-dot"></span>
                        <span>{{ item }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 结果概览 KPI -->
                <div v-if="msg.cards?.length" class="ai-kpi-grid">
                  <div v-for="(card, i) in msg.cards" :key="i" class="ai-kpi-card">
                    <div class="ai-kpi-label">{{ card.label }}</div>
                    <div class="ai-kpi-value">{{ card.value }}</div>
                    <div class="ai-kpi-sub">{{ card.sub }}</div>
                  </div>
                </div>

                <!-- 可视化图表 -->
                <div v-if="msg.hasChart && msg.data?.length" class="ai-chart">
                  <div class="ai-chart-header">
                    <span><el-icon :size="14"><TrendCharts /></el-icon> 数据可视化</span>
                    <el-radio-group v-model="msg.chartType" size="small" @change="() => onChartTypeChange(msg)">
                      <el-radio-button label="bar">柱状图</el-radio-button>
                      <el-radio-button label="line">折线图</el-radio-button>
                      <el-radio-button label="pie">饼图</el-radio-button>
                    </el-radio-group>
                  </div>
                  <div :ref="el => setChartRef(idx, el)" class="ai-chart-container"></div>
                </div>

                <!-- 数据表格 -->
                <div v-if="msg.data?.length" class="ai-data-table">
                  <div class="ai-table-header">
                    <span><el-icon :size="14"><Grid /></el-icon> 数据明细（{{ msg.data.length }} 条）</span>
                    <el-button size="small" text @click="exportMsgData(msg)">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-button>
                  </div>
                  <el-table :data="msg.data" stripe border size="small" max-height="360" class="ai-table">
                    <el-table-column
                      v-for="col in msg.columns"
                      :key="col"
                      :prop="col"
                      :label="getFieldLabel(col)"
                      min-width="110"
                      show-overflow-tooltip
                    />
                  </el-table>
                </div>

                <!-- SQL 和 思考过程 -->
                <div v-if="msg.sql || msg.thinking" class="ai-details">
                  <el-collapse>
                    <el-collapse-item v-if="msg.sql" title="查看 SQL">
                      <pre class="sql-code">{{ msg.sql }}</pre>
                    </el-collapse-item>
                    <el-collapse-item v-if="msg.thinking" :title="msg.thinking.match_source || '思考过程'">
                      <div class="thinking-content">
                        <p v-if="msg.thinking.reasoning"><strong>推理：</strong>{{ msg.thinking.reasoning }}</p>
                        <div v-if="msg.thinking.recommended_tables?.length" class="thinking-tags">
                          <el-tag v-for="t in msg.thinking.recommended_tables" :key="t" size="small" type="success" effect="plain">{{ t }}</el-tag>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <div v-if="msg.role === 'assistant' && (!msg.data || msg.data.length === 0) && !msg.insight" class="no-data">
                  没有查询到数据，试试换个时间或换一种说法
                </div>
              </div>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="message assistant">
            <div class="message-avatar">
              <el-avatar :size="30" class="ai-avatar">
                <el-icon><Cpu /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="input-box">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 5 }"
            placeholder="请输入你的问题，例如：上个月销售额最高的产品是什么..."
            @keydown.enter.exact.prevent="sendMessage"
            class="chat-input"
            resize="none"
          />
          <el-button
            type="primary"
            circle
            @click="sendMessage"
            :disabled="!inputMessage.trim() || loading"
            class="send-btn"
          >
            <el-icon><Top /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">
          <span>Enter 发送 · Shift+Enter 换行 · 支持多表 JOIN、聚合查询</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  ChatDotRound, ChatLineRound, Delete, Plus, User, Cpu, Top,
  Lightning, TrendCharts, Download, Grid, Sunny, Moon
} from '@element-plus/icons-vue'

const currentConvId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainerRef = ref(null)
const quotaRemaining = ref(100)
const dailyQuota = ref(100)
const sourceLabel = ref('AI 智能问数')
const sourceTagType = ref('success')
const isDark = ref(false)

const chartInstances = reactive({})
const chartRefs = reactive({})
const setChartRef = (idx, el) => { if (el) chartRefs[idx] = el }

const suggestions = [
  '本月各项目签约回款情况',
  '上月销售额最高的产品 TOP5',
  '近 30 天销售趋势',
  '客户购买金额排行',
  '各城市销售额分布',
  '本月回款率统计',
]

const fieldLabelMap = {
  month: '月份', date: '日期', day: '日期', year: '年份',
  project_name: '项目名称', project: '项目', project_id: '项目ID',
  building_name: '楼栋名称', building_id: '楼栋ID',
  unit_name: '房源名称', unit_id: '房源ID',
  customer_name: '客户名称', customer_id: '客户ID',
  city: '城市', province: '省份', category: '分类',
  name: '名称', status: '状态', count: '数量',
  total_count: '总数量', total_sales: '签约金额', sales_amount: '签约金额',
  total_amount: '总金额', amount: '金额', received_amount: '回款金额',
  total_received: '回款金额', receivables: '应收余额', total_receivables: '应收余额',
  total_cost: '成本金额', cost_amount: '成本金额',
  total_expense: '费用金额', fee_amount: '费用金额',
  profit: '利润', total_profit: '利润金额', profit_margin: '利润率',
  collection_rate: '回款率', subscription_rate: '认购转签约率',
  sell_through_rate: '去化率', contract_count: '签约套数',
  total_units: '房源总数', total_contracts: '签约套数',
  total_subscriptions: '认购套数', order_count: '订单数', quantity: '数量'
}

const chartColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']

const toggleTheme = () => {
  isDark.value = !isDark.value
  try { localStorage.setItem('ai-query-theme', isDark.value ? 'dark' : 'light') } catch {}
  // 重新渲染图表适配主题
  setTimeout(() => {
    Object.values(chartInstances).forEach(c => {
      if (c) c.resize()
    })
  }, 100)
}

const apiRequest = async (method, url, data = {}) => {
  const token = localStorage.getItem('token')
  const config = {
    method: method.toUpperCase(),
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
  }
  if (method.toUpperCase() !== 'GET' && Object.keys(data).length > 0) {
    config.body = JSON.stringify(data)
  }
  const response = await fetch(url, config)
  const text = await response.text()
  try {
    const parsed = JSON.parse(text)
    if (!response.ok) throw new Error(parsed.detail || parsed.message || '请求失败')
    return parsed
  } catch (e) {
    if (!response.ok) throw new Error(text || '请求失败')
    return text
  }
}

const formatBigNumber = (value) => {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0'
  if (Math.abs(num) >= 100000000) return `${(num / 100000000).toFixed(2)}亿`
  if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(2)}万`
  return num.toFixed(2)
}

const getFieldLabel = (field) => {
  if (!field) return '字段'
  const key = String(field).trim()
  if (fieldLabelMap[key]) return fieldLabelMap[key]
  const lower = key.toLowerCase()
  if (fieldLabelMap[lower]) return fieldLabelMap[lower]
  return key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').trim()
}

const getSourceLabel = (thinking) => {
  const source = thinking?.match_source || ''
  if (String(source).includes('标准库')) return { label: '标准库命中', type: 'success' }
  if (String(source).includes('拦截')) return { label: '安全拦截', type: 'danger' }
  return { label: 'AI 在线生成', type: 'warning' }
}

const generateInsight = (data, columns, question) => {
  if (!data || data.length === 0 || !columns || columns.length < 2) return null
  const dimField = columns[0], measureField = columns[1]
  const values = data.map(item => Number(item[measureField]) || 0)
  const total = values.reduce((s, v) => s + v, 0)
  const avg = total / values.length
  const max = Math.max(...values), min = Math.min(...values)
  const maxItem = data.find(item => Number(item[measureField]) === max)
  const minItem = data.find(item => Number(item[measureField]) === min)
  const q = question.toLowerCase()

  let insight = ''
  if (q.includes('最高') || q.includes('最大')) insight = `${maxItem?.[dimField] ?? '该项'}的${getFieldLabel(measureField)}最高，达到 ${formatBigNumber(max)}。`
  else if (q.includes('最低') || q.includes('最小')) insight = `${minItem?.[dimField] ?? '该项'}的${getFieldLabel(measureField)}最低，为 ${formatBigNumber(min)}。`
  else insight = `共返回 ${data.length} 条数据，${getFieldLabel(measureField)}总计 ${formatBigNumber(total)}，平均 ${formatBigNumber(avg)}。`

  const highlights = [
    `最高值：${formatBigNumber(max)}（${maxItem?.[dimField] ?? '未知'}）`,
    `最低值：${formatBigNumber(min)}（${minItem?.[dimField] ?? '未知'}）`
  ]
  return { insight, highlights }
}

const buildCards = (data, columns) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) return []
  const dimField = columns.find(c => typeof data[0]?.[c] === 'string') || columns[0]
  const numFields = columns.filter(c => c !== dimField && data.some(item => !Number.isNaN(Number(item[c]))))
  const primaryField = numFields[0] || columns.find(c => c !== dimField) || columns[0]
  const values = primaryField ? data.map(item => Number(item[primaryField]) || 0) : []
  const total = values.reduce((s, v) => s + v, 0)
  const avg = values.length ? total / values.length : 0
  const max = values.length ? Math.max(...values) : 0
  const maxItem = primaryField ? data.find(item => Number(item[primaryField]) === max) : null
  const cards = [
    { label: '记录数', value: data.length, sub: '返回行数' },
    { label: '字段数', value: columns.length, sub: '输出列数' },
  ]
  if (primaryField) cards.push({ label: '总计', value: formatBigNumber(total), sub: getFieldLabel(primaryField) })
  if (primaryField) cards.push({ label: '平均值', value: formatBigNumber(avg), sub: getFieldLabel(primaryField) })
  if (maxItem) cards.push({ label: '最大值', value: formatBigNumber(max), sub: String(maxItem[dimField] ?? '未知') })
  return cards.slice(0, 5)
}


const scrollToBottom = () => {
  nextTick(() => { if (messagesContainerRef.value) messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight })
}

const useSuggestion = (text) => { inputMessage.value = text; sendMessage() }
// 用 localStorage 持久化最后一次对话，刷新页面自动恢复
const saveLastConversation = () => {
  try {
    localStorage.setItem('ai-query-last-conv', JSON.stringify({
      messages: messages.value,
      convId: currentConvId.value
    }))
  } catch {}
}

const loadLastConversation = () => {
  try {
    const saved = localStorage.getItem('ai-query-last-conv')
    if (saved) {
      const data = JSON.parse(saved)
      messages.value = data.messages || []
      currentConvId.value = data.convId || null
      // 恢复图表
      nextTick(() => {
        messages.value.forEach((m, idx) => {
          if (m.role === 'assistant' && m.data?.length && chartRefs[idx]) {
            setTimeout(() => renderChartForMsg(m, chartRefs[idx]), 100)
          }
        })
      })
    }
  } catch {}
}

const clearLastConversation = () => {
  try { localStorage.removeItem('ai-query-last-conv') } catch {}
}

const newConversation = () => {
  currentConvId.value = null
  messages.value = []
  clearLastConversation()
  Object.keys(chartInstances).forEach(k => { chartInstances[k]?.dispose(); delete chartInstances[k] })
}

const clearCurrentChat = () => { messages.value = []; currentConvId.value = null; clearLastConversation(); Object.keys(chartInstances).forEach(k => { chartInstances[k]?.dispose(); delete chartInstances[k] }) }


const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return
  const text = inputMessage.value.trim(); inputMessage.value = ''
  messages.value.push({ role: 'user', content: text }); await nextTick(); scrollToBottom()
  loading.value = true

  try {
    const res = await apiRequest('POST', '/ai-query/execute-query', { question: text, top_k: 10 })
    const srcInfo = getSourceLabel(res.thinking); sourceLabel.value = srcInfo.label; sourceTagType.value = srcInfo.type
    const aiMsg = { role: 'assistant', content: '', sql: res.sql, data: res.data || [], columns: res.columns || [], thinking: res.thinking || null, chartType: res.chart_type || 'bar', hasChart: res.data && res.data.length > 0 }
    const insightData = generateInsight(res.data, res.columns, text)
    if (insightData) { aiMsg.insight = insightData.insight; aiMsg.highlights = insightData.highlights }
    aiMsg.cards = buildCards(res.data, res.columns)
    messages.value.push(aiMsg); quotaRemaining.value = Math.max(0, quotaRemaining.value - 1)
    await nextTick(); scrollToBottom()
    const lastIdx = messages.value.length - 1
    if (aiMsg.data?.length && chartRefs[lastIdx]) setTimeout(() => renderChartForMsg(aiMsg, chartRefs[lastIdx]), 100)

    // 保存到 localStorage
    saveLastConversation()

    ElMessage.success('查询成功')
  } catch (error) {
    messages.value.push({ role: 'assistant', content: `查询失败：${error.message || '未知错误'}`, isError: true })
    ElMessage.error('查询失败：' + (error.message || '未知错误'))
  } finally { loading.value = false; await nextTick(); scrollToBottom() }
}

const analyzeChartData = (data, columns, chartType) => {
  if (!data || data.length === 0 || !columns || columns.length < 2) return { xAxis: [], series: [], yAxisData: { type: 'value' } }
  const dimField = columns.find(c => { const s = data[0]?.[c]; return s !== null && s !== undefined && typeof s === 'string' && String(s).length < 30 }) || columns[0]
  const xAxis = data.map(item => String(item[dimField] ?? ''))
  const measureFields = columns.filter(c => { if (c === dimField) return false; const s = data[0]?.[c]; return s !== null && s !== undefined && !Number.isNaN(Number(s)) })
  const series = measureFields.slice(0, 3).map((field, idx) => ({
    name: getFieldLabel(field), type: chartType, data: data.map(item => Number(item[field]) || 0),
    itemStyle: { color: chartColors[idx % chartColors.length] },
    label: { show: chartType !== 'pie' && data.length <= 15, position: 'top', fontSize: 10, formatter: (p) => Math.abs(p.value) >= 10000 ? (p.value / 10000).toFixed(1) + '万' : p.value }
  }))
  if (chartType === 'pie') {
    const mainField = measureFields[0] || columns[1]; series.length = 0
    series.push({ name: getFieldLabel(mainField), type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: true, itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }, label: { show: true, formatter: '{b}: {c} ({d}%)', fontSize: 11 }, emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } }, data: data.map((item, i) => ({ name: String(item[dimField]), value: Number(item[mainField]) || 0, itemStyle: { color: chartColors[i % chartColors.length] } })) })
  }
  return { xAxis, series, yAxisData: { type: 'value', axisLabel: { formatter: (v) => Math.abs(v) >= 10000 ? (v / 10000).toFixed(0) + '万' : v } } }
}

const renderChartForMsg = (msg, container) => {
  if (!container || !msg.data?.length) return
  const key = messages.value.indexOf(msg)
  if (chartInstances[key]) chartInstances[key].dispose()
  const chart = echarts.init(container)
  chartInstances[key] = chart
  const { xAxis, series, yAxisData } = analyzeChartData(msg.data, msg.columns, msg.chartType)
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: series.map(s => s.name), bottom: 10, textStyle: { color: isDark.value ? '#94a3b8' : '#64748b' } },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: xAxis, axisLabel: { interval: 0, rotate: 30, fontSize: 11, color: isDark.value ? '#94a3b8' : '#64748b' }, axisTick: { alignWithLabel: true }, axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#e2e8f0' } } },
    yAxis: { ...yAxisData, axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#e2e8f0' } }, splitLine: { lineStyle: { color: isDark.value ? '#1e293b' : '#f1f5f9' } } },
    series
  })
}

const onChartTypeChange = (msg) => {
  const idx = messages.value.indexOf(msg)
  if (chartInstances[idx]) chartInstances[idx].dispose()
  if (chartRefs[idx] && msg.data?.length) setTimeout(() => renderChartForMsg(msg, chartRefs[idx]), 50)
}

const exportMsgData = (msg) => {
  if (!msg?.data) return
  const blob = new Blob([JSON.stringify(msg.data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `ai-query-${Date.now()}.json`; a.click()
  URL.revokeObjectURL(url); ElMessage.success('数据已导出')
}

const loadQuota = async () => {
  try { const quota = await apiRequest('get', '/api/portal/ai-query/quota'); quotaRemaining.value = quota.remaining || 100; dailyQuota.value = quota.daily || 100 } catch (e) { console.error('加载配额失败', e) }
}

const handleResize = () => { Object.values(chartInstances).forEach(c => c?.resize()) }

onMounted(() => {
  try { const saved = localStorage.getItem('ai-query-theme'); if (saved === 'dark') isDark.value = true } catch {}
  loadQuota(); loadLastConversation(); window.addEventListener('resize', handleResize)
})
onUnmounted(() => { Object.values(chartInstances).forEach(c => c?.dispose()); window.removeEventListener('resize', handleResize) })
</script>

<style scoped>
.ai-query-fullscreen {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 10;
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-card: #ffffff;
  --bg-code: #1e293b;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --border-hover: #cbd5e1;
  --sidebar-bg: #f1f5f9;
  --sidebar-border: #e2e8f0;
  --sidebar-text: #334155;
  --sidebar-text-muted: #64748b;
  --sidebar-hover: #e2e8f0;
  --sidebar-active: #dbeafe;
  --msg-user-bg: #3b82f6;
  --msg-user-text: #ffffff;
  --ai-avatar-bg: #dbeafe;
  --ai-avatar-color: #2563eb;
  --typing-bg: #2563eb;
  --accent: #3b82f6;
  --accent-light: #eff6ff;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --input-focus-border: #3b82f6;
  --input-focus-shadow: rgba(59, 130, 246, 0.15);
  --table-header-bg: #f8fafc;
  --table-header-color: #475569;
  --table-row-bg: #ffffff;
  --table-row-striped: #f8fafc;
  --table-cell-color: #0f172a;
  --table-border: #e2e8f0;
  --kpi-card-bg: #f8fafc;
  --kpi-card-border: #e2e8f0;
  --sql-code-bg: #1e293b;
  --sql-code-color: #e2e8f0;
  --welcome-text-primary: #0f172a;
  --welcome-text-secondary: #64748b;
  --suggestion-bg: #ffffff;
  --suggestion-border: #e2e8f0;
  --suggestion-hover-bg: #eff6ff;
  --suggestion-hover-border: #3b82f6;
  --suggestion-hover-text: #1e40af;
  --collapse-header-color: #64748b;
  --scrollbar-thumb: #cbd5e1;
}

.ai-query-fullscreen.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --bg-code: #0f172a;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
  --border-color: #334155;
  --border-hover: #475569;
  --sidebar-bg: #1e293b;
  --sidebar-border: #334155;
  --sidebar-text: #e2e8f0;
  --sidebar-text-muted: #94a3b8;
  --sidebar-hover: #334155;
  --sidebar-active: #1e3a5f;
  --ai-avatar-bg: #1e293b;
  --ai-avatar-color: #60a5fa;
  --typing-bg: #60a5fa;
  --accent: #3b82f6;
  --accent-light: rgba(59, 130, 246, 0.1);
  --input-bg: #1e293b;
  --input-border: #334155;
  --input-focus-border: #3b82f6;
  --input-focus-shadow: rgba(59, 130, 246, 0.15);
  --table-header-bg: #0f172a;
  --table-header-color: #94a3b8;
  --table-row-bg: #1e293b;
  --table-row-striped: rgba(30, 41, 59, 0.6);
  --table-cell-color: #e2e8f0;
  --table-border: #334155;
  --kpi-card-bg: #1e293b;
  --kpi-card-border: #334155;
  --sql-code-bg: #0f172a;
  --sql-code-color: #e2e8f0;
  --welcome-text-primary: #f1f5f9;
  --welcome-text-secondary: #94a3b8;
  --suggestion-bg: #1e293b;
  --suggestion-border: #334155;
  --suggestion-hover-bg: #334155;
  --suggestion-hover-border: #60a5fa;
  --suggestion-hover-text: #f1f5f9;
  --collapse-header-color: #94a3b8;
  --scrollbar-thumb: #475569;
}

/* 全局背景 */
.ai-query-fullscreen { background: var(--bg-primary); }
.chat-main { background: var(--bg-primary); }

/* 主区域 */
.chat-main { display: flex; flex-direction: column; height: 100%; min-width: 0; }

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: border-color 0.3s ease;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.header-right .el-button { color: var(--text-secondary); }
.theme-btn:hover { color: var(--accent) !important; }

/* 消息区域 */
.messages-container { flex: 1; overflow-y: auto; padding: 16px 0; }
.messages-container::-webkit-scrollbar { width: 6px; }
.messages-container::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 4px; }

/* 欢迎屏幕 */
.welcome-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; }
.welcome-icon { margin-bottom: 16px; }
.welcome-screen h2 { font-size: 26px; color: var(--welcome-text-primary); margin: 0 0 8px; font-weight: 700; transition: color 0.3s ease; }
.welcome-screen p { color: var(--welcome-text-secondary); font-size: 14px; margin: 0 0 32px; max-width: 480px; transition: color 0.3s ease; }

.suggestion-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 600px; width: 100%; }

.suggestion-item {
  padding: 12px 14px;
  background: var(--suggestion-bg);
  border: 1px solid var(--suggestion-border);
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s;
  text-align: center;
}

.suggestion-item:hover { background: var(--suggestion-hover-bg); color: var(--suggestion-hover-text); border-color: var(--suggestion-hover-border); }

/* 消息列表 */
.message-list { max-width: 800px; margin: 0 auto; padding: 0 16px; display: flex; flex-direction: column; gap: 24px; }

.message { display: flex; gap: 12px; }
.message.user { flex-direction: row-reverse; }
.message-avatar { flex-shrink: 0; margin-top: 2px; }

.user-avatar { background: var(--msg-user-bg) !important; color: var(--msg-user-text) !important; }
.ai-avatar { background: var(--ai-avatar-bg) !important; color: var(--ai-avatar-color) !important; border: 1px solid var(--border-color); transition: background 0.3s ease, color 0.3s ease, border-color 0.3s ease; }

.message-content { max-width: 85%; min-width: 0; }
.message-role { font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; transition: color 0.3s ease; }
.message.user .message-role { text-align: right; }

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message.user .message-text { background: var(--msg-user-bg); color: var(--msg-user-text); border-bottom-right-radius: 4px; }

/* AI 回复 */
.ai-response { display: flex; flex-direction: column; gap: 16px; }

.ai-insight { border-radius: 12px; overflow: hidden; background: var(--accent-light); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.ai-insight-header { display: flex; align-items: center; gap: 6px; padding: 10px 14px; background: var(--accent); border-bottom: 1px solid transparent; color: #fff; font-size: 13px; font-weight: 600; }
.ai-insight-body { padding: 14px; color: var(--text-primary); font-size: 14px; line-height: 1.7; transition: color 0.3s ease; }
.ai-insight-body p { margin: 0 0 10px; }

.insight-bullets { display: flex; flex-direction: column; gap: 6px; }
.insight-bullet { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--text-secondary); }
.insight-bullet-dot { width: 6px; height: 6px; margin-top: 7px; border-radius: 50%; background: var(--accent); flex: 0 0 auto; }

/* KPI 卡片 */
.ai-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.ai-kpi-card { background: var(--kpi-card-bg); border: 1px solid var(--kpi-card-border); border-radius: 10px; padding: 14px; transition: background 0.3s ease, border-color 0.3s ease; }
.ai-kpi-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; transition: color 0.3s ease; }
.ai-kpi-value { font-size: 22px; font-weight: 700; color: var(--text-primary); transition: color 0.3s ease; }
.ai-kpi-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; transition: color 0.3s ease; }

/* 图表 */
.ai-chart { border-radius: 12px; padding: 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.ai-chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; color: var(--text-primary); font-size: 13px; font-weight: 600; gap: 8px; }
.ai-chart-container { width: 100%; height: 360px; }

/* 数据表格 */
.ai-data-table { border-radius: 12px; padding: 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.ai-table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; color: var(--text-primary); font-size: 13px; font-weight: 600; }

.ai-table :deep(.el-table__header th) { background: var(--table-header-bg) !important; color: var(--table-header-color) !important; border-color: var(--table-border) !important; }
.ai-table :deep(.el-table__body td) { color: var(--table-cell-color) !important; border-color: var(--table-border) !important; }
.ai-table :deep(.el-table__row) { background: var(--table-row-bg) !important; }
.ai-table :deep(.el-table__row--striped) { background: var(--table-row-striped) !important; }

/* 详情折叠 */
.ai-details { border-radius: 12px; padding: 4px 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.ai-details :deep(.el-collapse-item__header) { color: var(--collapse-header-color); font-size: 12px; background: transparent; }
.ai-details :deep(.el-collapse-item__wrap) { background: transparent; border-color: var(--border-color); }
.ai-details :deep(.el-collapse-item__content) { padding-bottom: 14px; }

.sql-code { background: var(--sql-code-bg); color: var(--sql-code-color); padding: 14px; border-radius: 8px; overflow-x: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; margin: 0; transition: background 0.3s ease, color 0.3s ease; }

.thinking-content { display: flex; flex-direction: column; gap: 8px; color: var(--text-secondary); font-size: 13px; line-height: 1.6; }
.thinking-content p { margin: 0; }
.thinking-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.no-data { color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px; }

/* 加载动画 */
.typing-indicator { display: flex; gap: 4px; padding: 14px 18px; }
.typing-indicator span { width: 8px; height: 8px; border-radius: 50%; background: var(--typing-bg); animation: typing 1.2s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* 输入区 */
.input-area { padding: 12px 16px 16px; flex-shrink: 0; }

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 800px;
  margin: 0 auto;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 14px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.15s, background 0.3s ease;
}

.input-box:focus-within { border-color: var(--input-focus-border); box-shadow: 0 0 0 3px var(--input-focus-shadow); }

.chat-input { flex: 1; }
.chat-input :deep(.el-textarea__inner) { background: transparent !important; border: none !important; box-shadow: none !important; padding: 4px 0 !important; font-size: 14px; color: var(--text-primary); resize: none; }
.chat-input :deep(.el-textarea__inner)::placeholder { color: var(--text-muted); }
.send-btn { flex-shrink: 0; }

.input-hint { text-align: center; font-size: 11px; color: var(--text-muted); margin-top: 6px; }

/* 响应式 */
@media (max-width: 768px) {
  .suggestion-grid { grid-template-columns: repeat(2, 1fr); }
  .message-content { max-width: 92%; }
  .ai-kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
