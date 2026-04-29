<template>
  <div class="smart-report-page">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="22" class="header-icon"><Document /></el-icon>
            <span class="title">AI 智能报表</span>
            <el-tag type="success" size="small">自然语言生成报表</el-tag>
          </div>
          <el-tag type="info" effect="plain" round>一键生成</el-tag>
        </div>
      </template>

      <div class="query-section">
        <el-input
          v-model="question"
          type="textarea"
          :rows="2"
          placeholder="例如：上个月各项目签约回款报表"
          @keyup.enter.ctrl="handleQuery"
          class="question-input"
        />
        <div class="query-actions">
          <el-button type="primary" @click="handleQuery" :loading="loading" size="large" round class="query-btn">
            <el-icon><Search /></el-icon>
            生成报表
          </el-button>
        </div>
      </div>

      <div class="quick-section">
        <div class="quick-label">
          <el-icon><Lightning /></el-icon>
          <span>报表示例</span>
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

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="result" class="result-section">
        <div v-if="result.profile" class="summary-card">
          <div class="section-header">
            <span>
              <el-icon><DataAnalysis /></el-icon>
              结果概览
            </span>
            <el-tag type="success" effect="plain">{{ result.sourceLabel }}</el-tag>
          </div>
          <el-row :gutter="12" class="summary-grid">
            <el-col v-for="item in result.profile.cards" :key="item.label" :xs="12" :sm="12" :md="8" :lg="6">
              <div class="summary-item">
                <div class="summary-label">{{ item.label }}</div>
                <div class="summary-value">{{ item.value }}</div>
                <div class="summary-sub">{{ item.sub }}</div>
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
          <div v-if="result.profile.highlights?.length" class="summary-note-list">
            <div v-for="(item, index) in result.profile.highlights" :key="index" class="summary-note-item">
              <span class="summary-note-dot"></span>
              <span>{{ item }}</span>
            </div>
          </div>
        </div>

        <div v-if="result.summary" class="summary-card">
          <div class="section-header">
            <span>
              <el-icon><DataAnalysis /></el-icon>
              报表概览
            </span>
            <el-tag type="success" effect="plain">纯报表输出</el-tag>
          </div>
          <el-row :gutter="12" class="summary-grid">
            <el-col v-for="item in result.summary.cards" :key="item.label" :xs="24" :sm="12" :md="8" :lg="6">
              <div class="summary-item">
                <div class="summary-label">{{ item.label }}</div>
                <div class="summary-value">{{ item.value }}</div>
                <div class="summary-sub">{{ item.sub }}</div>
              </div>
            </el-col>
          </el-row>
          <div class="summary-note">{{ result.summary.note }}</div>
        </div>

        <div v-if="result.data && result.data.length > 0" class="data-card">
          <div class="section-header">
            <span>
              <el-icon><Document /></el-icon>
              报表明细（{{ result.data.length }} 条）
            </span>
            <div class="section-actions">
              <el-button size="small" @click="exportData">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button size="small" @click="copySql">
                <el-icon><CopyDocument /></el-icon>
                复制 SQL
              </el-button>
            </div>
          </div>

          <div class="report-table-wrap">
            <el-table
              :data="result.data"
              stripe
              border
              class="result-table"
              max-height="420"
            >
            <el-table-column
                v-for="col in result.columns"
                :key="col"
                :prop="col"
                :label="getFieldLabel(col)"
                min-width="120"
                show-overflow-tooltip
              />
            </el-table>
          </div>
        </div>

        <div v-if="result.sql" class="sql-card">
          <el-collapse>
            <el-collapse-item title="查看生成细节" name="sql">
              <div v-if="result.explanation" class="explain-content">
                <p>{{ result.explanation }}</p>
              </div>
              <div v-if="result.thinking?.recommended_tables?.length" class="thinking-tags">
                <el-tag
                  v-for="table in result.thinking.recommended_tables"
                  :key="table"
                  size="small"
                  effect="plain"
                  round
                >
                  {{ table }}
                </el-tag>
              </div>
              <pre class="sql-code">{{ result.sql }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>

        <el-empty v-else description="暂无数据" />
      </div>

      <div v-else class="empty-state">
        <el-empty description="输入一句话生成报表" />

        <div class="history-section">
          <h4>
            <el-icon><Clock /></el-icon>
            我的报表历史
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
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document, Search, Lightning, DataAnalysis, Download, Clock, CopyDocument
} from '@element-plus/icons-vue'

const question = ref('')
const loading = ref(false)
const result = ref(null)
const quotaRemaining = ref(100)
const dailyQuota = ref(100)
const queryHistory = ref([])

const quickQuestions = [
  '生成本月各项目签约回款报表',
  '生成项目成本与费用报表',
  '生成各项目去化率排行报表',
  '生成本月认购转签约报表',
  '生成各城市销售额报表',
  '生成应收逾期账款报表',
  '生成各项目净利润报表',
  '生成客户跟进明细报表'
]

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

const formatMoney = (value) => {
  const num = Number(value || 0)
  if (!num) return '0'
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

const buildReportProfile = (data, columns, thinking, explanation, questionText) => {
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
  const maxItem = primaryField ? data.find(item => Number(item[primaryField]) === max) : null

  const cards = [
    { label: '记录数', value: data.length, sub: '报表行数' },
    { label: '字段数', value: columns.length, sub: '输出列数' },
    { label: '数值字段', value: numericFields.length, sub: '可统计指标' }
  ]

  if (primaryField) {
    cards.push(
      { label: '核心指标总计', value: formatMoney(total), sub: getFieldLabel(primaryField) },
      { label: '平均值', value: formatMoney(avg), sub: getFieldLabel(primaryField) }
    )
  }

  if (maxItem) {
    cards.push({ label: '最大值', value: formatMoney(max), sub: String(maxItem[dimensionField] ?? '未知') })
  }

  const highlights = []
  if (primaryField && data.length > 0) {
    highlights.push(`主维度：${getFieldLabel(dimensionField)}，主指标：${getFieldLabel(primaryField)}`)
    highlights.push(`合计 ${formatMoney(total)}，平均 ${formatMoney(avg)}`)
    if (maxItem) {
      highlights.push(`峰值出现在「${String(maxItem[dimensionField] ?? '未知')}」`)
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
    fieldTags: columns.slice(0, 8).map(getFieldLabel)
  }
}

const buildReportSummary = (data, columns, questionText) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) return null

  const dimensionField = columns.find(col => {
    const sample = data[0]?.[col]
    return sample !== null && sample !== undefined && typeof sample === 'string'
  }) || columns[0]

  const measureField = columns.find(col => {
    const sample = data[0]?.[col]
    return sample !== null && sample !== undefined && !Number.isNaN(Number(sample)) && col !== dimensionField
  })

  const values = measureField ? data.map(item => Number(item[measureField]) || 0) : []
  const total = values.reduce((sum, val) => sum + val, 0)
  const avg = values.length ? total / values.length : 0
  const max = values.length ? Math.max(...values) : 0
  const min = values.length ? Math.min(...values) : 0
  const maxItem = measureField ? data.find(item => Number(item[measureField]) === max) : null
  const minItem = measureField ? data.find(item => Number(item[measureField]) === min) : null

  const cards = [
    { label: '记录数', value: data.length, sub: '报表行数' },
    { label: '字段数', value: columns.length, sub: '输出列数' }
  ]

  if (measureField) {
    cards.push(
      { label: '核心指标总计', value: formatMoney(total), sub: getFieldLabel(measureField) },
      { label: '平均值', value: formatMoney(avg), sub: getFieldLabel(measureField) }
    )
    if (maxItem) {
      cards.push({ label: '最大值', value: formatMoney(max), sub: String(maxItem[dimensionField] ?? '未知') })
    }
    if (minItem) {
      cards.push({ label: '最小值', value: formatMoney(min), sub: String(minItem[dimensionField] ?? '未知') })
    }
  }

  const lowerQuestion = (questionText || '').toLowerCase()
  const title = lowerQuestion.includes('报表') ? questionText : `${questionText} 报表`

  return {
    title,
    cards: cards.slice(0, 6),
    highlights: [
      `共返回 ${data.length} 条记录`,
      `主维度：${getFieldLabel(dimensionField)}`,
      measureField ? `核心指标：${getFieldLabel(measureField)}` : '已完成报表生成'
    ],
    fieldTags: columns.slice(0, 8).map(getFieldLabel),
    note: measureField
      ? `系统已将“${questionText}”转换为报表查询，主维度为 ${getFieldLabel(dimensionField)}，核心指标为 ${getFieldLabel(measureField)}。`
      : `系统已将“${questionText}”转换为报表查询。`
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
      data: res.data || [],
      columns: res.columns || [],
      summary: buildReportSummary(res.data || [], res.columns || [], question.value),
      thinking: res.thinking || null,
      profile: buildReportProfile(res.data || [], res.columns || [], res.thinking, res.explanation, question.value),
      sourceLabel: getSourceLabel(res.thinking)
    }

    saveQueryHistory(question.value, res.sql)
    quotaRemaining.value--
    ElMessage.success('报表生成成功')
  } catch (error) {
    ElMessage.error('报表生成失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const exportData = () => {
  if (!result.value?.data) return
  const data = JSON.stringify(result.value.data, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai-report-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据已导出')
}

const copySql = async () => {
  if (!result.value?.sql) return
  await navigator.clipboard.writeText(result.value.sql)
  ElMessage.success('SQL 已复制')
}

const saveQueryHistory = (questionText, sql) => {
  queryHistory.value.unshift({
    question: questionText,
    sql,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  if (queryHistory.value.length > 10) {
    queryHistory.value.pop()
  }
}

const loadHistory = (history) => {
  question.value = history.question
}

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

onUnmounted(() => {})
</script>

<style scoped>
.smart-report-page {
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 24%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.1), transparent 20%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  min-height: 100%;
}

.report-card {
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
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(37, 99, 235, 0.06));
  border: 1px solid rgba(14, 165, 233, 0.12);
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
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
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
  color: #0f766e;
  margin-bottom: 4px;
}

.helper-item-desc {
  font-size: 13px;
  color: #334155;
  line-height: 1.6;
}

.card-header,
.header-left {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
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

.query-section,
.quick-section {
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
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 8px;
}

.question-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 12px;
  transition: all 0.3s;
  text-align: center;
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

.summary-card,
.data-card,
.sql-card,
.explain-card {
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
}

.section-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-grid {
  margin-top: 8px;
}

.summary-item {
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  padding: 14px;
  min-height: 100px;
}

.summary-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
  margin-bottom: 4px;
}

.summary-sub {
  font-size: 12px;
  color: #475569;
}

.summary-note {
  margin-top: 12px;
  font-size: 13px;
  color: #475569;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}

.summary-note-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.summary-note-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #334155;
}

.summary-note-dot {
  width: 6px;
  height: 6px;
  margin-top: 7px;
  border-radius: 50%;
  background: #2563eb;
  flex: 0 0 auto;
}

.field-tags,
.thinking-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.explain-content p {
  margin: 0;
  line-height: 1.8;
  font-size: 14px;
  color: #334155;
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

.report-table-wrap {
  overflow: auto;
  border-radius: 12px;
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

.sql-code {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 12px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.explain-content {
  margin-bottom: 12px;
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
  border-radius: 14px;
}

.notice-content {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.notice-content ul {
  margin: 0;
  padding-left: 18px;
}

@media (max-width: 768px) {
  .smart-report-page {
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
