<template>
  <div class="ai-report-page">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="22" class="header-icon"><Document /></el-icon>
            <span class="title">AI 智能报表</span>
            <el-tag type="success" size="small">后台审查版</el-tag>
          </div>
          <div class="header-right">
            <el-tag type="info" effect="plain" round>{{ modelLabel }}</el-tag>
            <el-tag :type="keyTypeTagType" effect="plain" round>{{ keyTypeLabel }}</el-tag>
          </div>
        </div>
      </template>

      <el-row :gutter="16" class="overview-grid">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="overview-card">
            <div class="overview-label">今日调用</div>
            <div class="overview-value">{{ stats.today_count || 0 }}</div>
            <div class="overview-tip">/ {{ stats.daily_quota || 0 }} 次配额</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="overview-card">
            <div class="overview-label">标准库命中</div>
            <div class="overview-value">{{ stats.standard_hits || 0 }}</div>
            <div class="overview-tip">命中率 {{ hitRateText }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="overview-card">
            <div class="overview-label">AI 在线生成</div>
            <div class="overview-value">{{ stats.ai_generated || 0 }}</div>
            <div class="overview-tip">详细思考过程可展开</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="overview-card">
            <div class="overview-label">平均耗时</div>
            <div class="overview-value">{{ stats.avg_time || 0 }}ms</div>
            <div class="overview-tip">执行与渲染时间</div>
          </div>
        </el-col>
      </el-row>

      <div class="query-section">
        <el-input
          v-model="question"
          type="textarea"
          :rows="4"
          placeholder="请输入报表需求，例如：上个月各项目签约回款报表"
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
          <span>快捷报表示例</span>
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
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="result" class="result-section">
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

        <div v-if="result.thinking" class="thinking-card">
          <div class="section-header">
            <span>
              <el-icon><MagicStick /></el-icon>
              思考过程
            </span>
            <el-tag :type="result.thinking.match_source === '标准库命中' ? 'success' : 'warning'" effect="plain">
              {{ result.thinking.match_source }}
            </el-tag>
          </div>

          <el-collapse v-model="thinkingActiveNames" class="thinking-collapse">
            <el-collapse-item name="overview" title="决策流程">
              <ol class="thinking-list">
                <li v-for="step in result.thinking.decision_steps || []" :key="step">{{ step }}</li>
              </ol>
            </el-collapse-item>

            <el-collapse-item name="keywords" title="关键词与匹配">
              <div class="thinking-tags">
                <el-tag v-for="kw in result.thinking.keywords || []" :key="kw" size="small" effect="plain">{{ kw }}</el-tag>
              </div>
              <div class="thinking-text">
                <p><strong>匹配来源：</strong>{{ result.thinking.match_source }}</p>
                <p v-if="result.thinking.matched_template"><strong>命中模板：</strong>{{ result.thinking.matched_template }}</p>
                <p><strong>推理说明：</strong>{{ result.thinking.reasoning }}</p>
              </div>
            </el-collapse-item>

            <el-collapse-item name="tables" title="推荐表与字段映射">
              <div class="thinking-tags">
                <el-tag v-for="table in result.thinking.recommended_tables || []" :key="table" size="small" type="success" effect="plain">
                  {{ table }}
                </el-tag>
              </div>
              <el-table :data="result.thinking.field_mapping || []" border stripe size="small" class="thinking-table">
                <el-table-column prop="field" label="字段" min-width="180" />
                <el-table-column prop="type" label="类型" width="100" />
              </el-table>
            </el-collapse-item>

            <el-collapse-item name="profile" title="结果画像">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="行数">{{ result.thinking.result_profile?.row_count || 0 }}</el-descriptions-item>
                <el-descriptions-item label="列数">{{ result.thinking.result_profile?.column_count || 0 }}</el-descriptions-item>
                <el-descriptions-item label="主维度">{{ getFieldLabel(result.thinking.result_profile?.dimension_field) }}</el-descriptions-item>
                <el-descriptions-item label="核心指标">{{ getFieldLabel(result.thinking.result_profile?.measure_field) }}</el-descriptions-item>
                <el-descriptions-item label="推荐图表">{{ getFieldLabel(result.thinking.result_profile?.chart_type) }}</el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
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
          <div class="section-header">
            <span>
              <el-icon><EditPen /></el-icon>
              生成 SQL
            </span>
          </div>
          <pre class="sql-code">{{ result.sql }}</pre>
        </div>

        <div v-if="result.explanation" class="explain-card">
          <div class="section-header">
            <span>
              <el-icon><InfoFilled /></el-icon>
              生成说明
            </span>
          </div>
          <div class="explain-content">
            <p>{{ result.explanation }}</p>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <el-empty description="输入一句话，AI 自动生成报表" />
        <div class="history-section">
          <h4>
            <el-icon><Clock /></el-icon>
            报表历史
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

    <el-alert
      title="使用须知"
      type="info"
      :closable="false"
      show-icon
      class="notice-alert"
    >
      <template #title>
        <div class="notice-content">
          <el-icon :size="16" class="notice-icon"><InfoFilled /></el-icon>
          <span>后台审查版说明：</span>
          <ul>
            <li>仅允许 SELECT 查询，保障数据安全</li>
            <li>可展开查看关键词、命中来源、推荐表和字段映射</li>
            <li>每日查询配额：{{ quotaRemaining }}/{{ dailyQuota }} 次</li>
          </ul>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document, Search, Lightning, DataAnalysis, Download, Clock, InfoFilled,
  EditPen, CopyDocument, MagicStick
} from '@element-plus/icons-vue'

const question = ref('')
const loading = ref(false)
const result = ref(null)
const quotaRemaining = ref(100)
const dailyQuota = ref(100)
const queryHistory = ref([])
const stats = ref({})
const thinkingActiveNames = ref(['overview', 'keywords'])
const keyTypeLabel = ref('未识别 / 未配置')
const keyType = ref('unknown')
const modelLabel = ref('Qwen3.6-Plus')
const availableModels = ref({})

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
  quantity: '数量',
  bar: '柱状图',
  line: '折线图',
  pie: '饼图',
  table: '表格'
}

const keyTypeTagType = computed(() => {
  if (keyType.value === 'coding_plan') return 'warning'
  if (keyType.value === 'common') return 'success'
  return 'info'
})

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

const getFieldLabel = (field) => {
  if (!field) return '字段'
  const key = String(field).trim()
  if (fieldLabelMap[key]) return fieldLabelMap[key]
  const lower = key.toLowerCase()
  if (fieldLabelMap[lower]) return fieldLabelMap[lower]
  return key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').trim()
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

  const title = (questionText || '').includes('报表') ? questionText : `${questionText} 报表`

  return {
    title,
    cards: cards.slice(0, 6),
    note: measureField
      ? `系统已将“${questionText}”转换为报表查询，主维度为 ${getFieldLabel(dimensionField)}，核心指标为 ${getFieldLabel(measureField)}。`
      : `系统已将“${questionText}”转换为报表查询。`
  }
}

const normalizeThinking = (thinking) => {
  if (!thinking) return null
  return {
    ...thinking,
    keywords: Array.isArray(thinking.keywords) ? thinking.keywords : [],
    decision_steps: Array.isArray(thinking.decision_steps) ? thinking.decision_steps : [],
    recommended_tables: Array.isArray(thinking.recommended_tables) ? thinking.recommended_tables : [],
    field_mapping: Array.isArray(thinking.field_mapping) ? thinking.field_mapping : [],
    result_profile: thinking.result_profile || {}
  }
}

const handleQuery = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入报表需求')
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

    const thinking = normalizeThinking(res.thinking)
    result.value = {
      sql: res.sql,
      explanation: res.explanation,
      data: res.data || [],
      columns: res.columns || [],
      summary: buildReportSummary(res.data || [], res.columns || [], question.value),
      thinking
    }

    saveQueryHistory(question.value, res.sql)
    quotaRemaining.value = Math.max(0, quotaRemaining.value - 1)
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
  a.download = `admin-ai-report-${Date.now()}.json`
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
    const quota = await apiRequest('get', '/api/admin/ai-config/stats')
    stats.value = quota || {}
    quotaRemaining.value = quota.remaining || 100
    dailyQuota.value = quota.daily_quota || quota.dailyQuota || 100
  } catch (error) {
    console.error('加载配额失败', error)
  }
}

const loadConfig = async () => {
  try {
    const config = await apiRequest('get', '/api/admin/ai-config/current')
    keyType.value = config.key_type || keyType.value
    keyTypeLabel.value = config.key_type_label || keyTypeLabel.value
    availableModels.value = config.available_models || {}
    modelLabel.value = availableModels.value[config.model]?.name || config.model || modelLabel.value
  } catch (error) {
    console.error('加载配置失败', error)
  }
}

const hitRateText = computed(() => {
  const total = Number(stats.value?.today_count || 0)
  const hits = Number(stats.value?.standard_hits || 0)
  if (!total) return '0%'
  return `${Math.round((hits / total) * 100)}%`
})

const loadAdminStats = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/ai-query/stats')
    stats.value = {
      ...stats.value,
      standard_hits: res.standard_hits || 0,
      ai_generated: res.ai_generated || 0,
      today_count: res.today_count || stats.value?.today_count || 0,
      avg_time: res.avg_time || stats.value?.avg_time || 0
    }
  } catch (error) {
    console.error('加载后台问数统计失败', error)
  }
}

onMounted(() => {
  loadConfig()
  loadQuota()
  loadAdminStats()
})
</script>

<style scoped>
.ai-report-page {
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 24%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.1), transparent 20%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
  min-height: 100%;
}

.report-card {
  max-width: 1240px;
  margin: 0 auto 20px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
}

.card-header,
.header-left,
.header-right {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  gap: 10px;
}

.header-right {
  gap: 8px;
  flex-wrap: wrap;
}

.header-icon {
  color: #2563eb;
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.overview-grid,
.query-section,
.quick-section {
  margin-bottom: 20px;
}

.overview-card {
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  padding: 14px;
  min-height: 92px;
}

.overview-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.overview-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}

.overview-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #475569;
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
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
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
.explain-card,
.thinking-card {
  background: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
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

.section-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.thinking-collapse {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.thinking-list {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  line-height: 1.8;
}

.thinking-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.thinking-text {
  display: grid;
  gap: 8px;
  color: #334155;
  font-size: 13px;
  line-height: 1.7;
}

.thinking-table {
  margin-top: 8px;
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

.explain-content p {
  margin: 0;
  line-height: 1.8;
  font-size: 14px;
  color: #334155;
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
  max-width: 1240px;
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
  .ai-report-page {
    padding: 16px;
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
