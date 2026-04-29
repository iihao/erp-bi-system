<template>
  <div class="ai-query-simple">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap pink-bg">
          <el-icon :size="24"><ChatDotRound /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">AI 问数</h1>
          <p class="page-subtitle">自然语言查询，一键生成 SQL</p>
        </div>
      </div>
      <el-tag size="large" effect="dark" class="model-tag">
        <el-icon><Cpu /></el-icon>
        Qwen3.6-Plus
      </el-tag>
    </div>

    <!-- 查询输入 -->
    <div class="query-section">
      <div class="section-card">
        <div class="card-accent primary"></div>
        <div class="section-body">
          <el-input
            v-model="question"
            type="textarea"
            :rows="4"
            placeholder="请输入您的问题，例如：各项目去化率排名"
            @keyup.enter.ctrl="handleQuery"
            maxlength="500"
            show-word-limit
            class="question-input"
          />
          <div class="query-actions">
            <el-button type="primary" @click="handleQuery" :loading="loading" size="large">
              <el-icon><Search /></el-icon>
              立即查询
            </el-button>
            <el-button @click="showExamples = true" size="large">
              <el-icon><List /></el-icon>
              示例问题
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷问题 -->
    <div class="quick-section">
      <div class="section-card">
        <div class="card-accent warning"></div>
        <div class="section-header">
          <div class="header-left">
            <div class="header-icon-sm warning-bg">
              <el-icon :size="16"><Promotion /></el-icon>
            </div>
            <span class="section-title">热门问题</span>
          </div>
        </div>
        <div class="section-body">
          <div class="quick-grid">
            <el-tag
              v-for="q in quickQuestions"
              :key="q"
              @click="question = q"
              class="question-tag"
              effect="plain"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 查询结果 -->
    <div v-if="queryResult" class="result-section">
      <div class="section-card">
        <div class="card-accent success"></div>
        <div class="section-header">
          <div class="header-left">
            <div class="header-icon-sm success-bg">
              <el-icon :size="16"><CircleCheck /></el-icon>
            </div>
            <span class="section-title">查询结果</span>
          </div>
          <div class="result-meta">
            <el-tag size="small" :type="queryResult.matched_standard ? 'success' : 'primary'" v-if="queryResult.thinking">
              {{ queryResult.thinking.match_source || (queryResult.matched_standard ? '标准 SQL' : 'AI 生成') }}
            </el-tag>
            <span class="result-time">
              <el-icon><Timer /></el-icon>
              {{ queryResult.execution_time_ms }}ms
            </span>
          </div>
        </div>

        <div class="section-body">
          <!-- 思考过程 -->
          <el-collapse v-if="queryResult.thinking" class="thinking-collapse">
            <el-collapse-item name="thinking">
              <template #title>
                <div class="thinking-title">
                  <el-icon><Cpu /></el-icon>
                  <span>AI 思考过程</span>
                </div>
              </template>
              <div class="thinking-content">
                <div class="thinking-row" v-if="queryResult.thinking.keywords">
                  <span class="thinking-label">关键词：</span>
                  <el-tag v-for="kw in queryResult.thinking.keywords" :key="kw" size="small" type="info" class="kw-tag">{{ kw }}</el-tag>
                </div>
                <div class="thinking-row" v-if="queryResult.thinking.match_source">
                  <span class="thinking-label">匹配来源：</span>
                  <span>{{ queryResult.thinking.match_source }}</span>
                </div>
                <div class="thinking-row" v-if="queryResult.thinking.matched_template">
                  <span class="thinking-label">匹配模板：</span>
                  <span>{{ queryResult.thinking.matched_template }}</span>
                </div>
                <div class="thinking-row" v-if="queryResult.thinking.recommended_tables">
                  <span class="thinking-label">使用表：</span>
                  <el-tag v-for="t in queryResult.thinking.recommended_tables" :key="t" size="small" type="warning" class="table-tag">{{ t }}</el-tag>
                </div>
                <div class="thinking-row" v-if="queryResult.thinking.field_mapping">
                  <span class="thinking-label">字段映射：</span>
                  <el-tag v-for="f in queryResult.thinking.field_mapping" :key="f.field" size="small" :type="f.type === '维度' ? 'success' : 'primary'" class="field-tag">{{ f.field }}({{ f.type }})</el-tag>
                </div>
                <div class="thinking-row" v-if="queryResult.thinking.reasoning">
                  <span class="thinking-label">推理说明：</span>
                  <span>{{ queryResult.thinking.reasoning }}</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- SQL 语句 -->
          <div class="sql-section">
            <div class="sql-label">生成的 SQL</div>
            <pre class="sql-code">{{ queryResult.sql }}</pre>
            <el-button size="small" @click="copySql">
              <el-icon><CopyDocument /></el-icon>
              复制 SQL
            </el-button>
          </div>

          <!-- 可视化图表 -->
          <div v-if="queryResult.data && queryResult.data.length > 0" class="chart-section">
            <div class="chart-header">
              <span class="chart-label">
                <el-icon><DataBoard /></el-icon>
                数据可视化
              </span>
              <el-radio-group v-model="chartType" size="small" @change="onChartTypeChange">
                <el-radio-button label="bar">柱状图</el-radio-button>
                <el-radio-button label="line">折线图</el-radio-button>
                <el-radio-button label="pie">饼图</el-radio-button>
              </el-radio-group>
            </div>
            <div ref="chartContainer" class="chart-container"></div>
          </div>

          <!-- 数据表格 -->
          <div class="data-section" v-if="queryResult.data && queryResult.data.length > 0">
            <div class="data-label">
              <el-icon><DataBoard /></el-icon>
              数据结果（{{ queryResult.data.length }} 条）
            </div>
            <el-table :data="queryResult.data" stripe border size="default">
              <el-table-column
                v-for="col in queryResult.columns"
                :key="col"
                :prop="col"
                :label="col"
              />
            </el-table>
          </div>

          <!-- 无数据提示 -->
          <el-empty v-else-if="!queryResult.data || queryResult.data.length === 0" description="暂无数据" />
        </div>
      </div>
    </div>

    <!-- 查询历史 -->
    <div class="history-section">
      <div class="section-card">
        <div class="card-accent warning"></div>
        <div class="section-header">
          <div class="header-left">
            <div class="header-icon-sm warning-bg">
              <el-icon :size="16"><Clock /></el-icon>
            </div>
            <span class="section-title">查询历史</span>
          </div>
          <el-button size="small" @click="clearHistory">
            <el-icon><Delete /></el-icon>
            清空历史
          </el-button>
        </div>

        <div class="section-body">
          <div class="history-list">
            <div
              v-for="record in queryHistory"
              :key="record.query_id"
              class="history-item"
              @click="loadHistory(record)"
            >
              <div class="item-icon">
                <el-icon :size="16" v-if="record.status === 'success'"><SuccessFilled /></el-icon>
                <el-icon :size="16" v-else><CircleCloseFilled /></el-icon>
              </div>
              <div class="item-content">
                <div class="item-question">{{ record.question }}</div>
                <div class="item-meta">
                  <span class="item-time">{{ record.created_at }}</span>
                  <span class="item-duration">{{ record.execution_time_ms }}ms</span>
                </div>
              </div>
              <el-icon class="item-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
          <el-empty v-if="queryHistory.length === 0" description="暂无查询历史" />
        </div>
      </div>
    </div>

    <!-- 示例问题对话框 -->
    <el-dialog v-model="showExamples" title="示例问题" width="700px">
      <div class="example-grid">
        <div
          v-for="(example, idx) in quickQuestions"
          :key="idx"
          class="example-item"
          @click="selectExample(example)"
        >
          <el-icon class="example-icon"><ChatLineRound /></el-icon>
          <span>{{ example }}</span>
          <el-icon class="example-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'

// Element Plus Icons
import {
  ChatDotRound, Cpu, Search, List, CircleCheck, Timer,
  CopyDocument, DataBoard, Clock, Delete, SuccessFilled,
  CircleCloseFilled, ArrowRight, ChatLineRound, Promotion
} from '@element-plus/icons-vue'

// 状态
const question = ref('')
const loading = ref(false)
const queryResult = ref(null)
const queryHistory = ref([])
const showExamples = ref(false)
const chartType = ref('bar')
const chartContainer = ref(null)
let chartInstance = null

// 图表颜色
const chartColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']

// 快捷问题
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

// API 请求
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
  const response = await fetch(url, config)
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || '请求失败')
  return data
}

// 查询
const handleQuery = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  loading.value = true
  try {
    const result = await apiRequest('post', '/ai-query/execute-query', {
      body: JSON.stringify({
        question: question.value,
        top_k: 10
      })
    })

    queryResult.value = result

    // 如果后端推荐了图表类型，使用推荐
    if (result.chart_type && result.data && result.data.length > 0) {
      chartType.value = result.chart_type
    }

    ElMessage.success(`查询成功，耗时 ${result.execution_time_ms}ms`)

    // 添加到历史
    loadHistoryList()

    // 渲染图表
    if (result.data && result.data.length > 0) {
      await nextTick()
      renderChart(result.data, result.columns)
    }

  } catch (error) {
    console.error('查询失败', error)
    ElMessage.error('查询失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载历史
const loadHistoryList = async () => {
  try {
    const res = await apiRequest('get', '/api/ai-query/logs?limit=20')
    queryHistory.value = res.data || []
  } catch (error) {
    console.error('加载历史失败', error)
  }
}

// 选择历史
const loadHistory = (row) => {
  question.value = row.question
}

// 清空历史
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定清空查询历史吗？', '提示', { type: 'warning' })
    queryHistory.value = []
    ElMessage.success('历史已清空')
  } catch {
    // 取消
  }
}

// 复制 SQL
const copySql = () => {
  if (queryResult.value?.sql) {
    navigator.clipboard.writeText(queryResult.value.sql)
    ElMessage.success('SQL 已复制')
  }
}

// 选择示例
const selectExample = (example) => {
  question.value = example
  showExamples.value = false
}

// 图表类型切换
const onChartTypeChange = () => {
  if (queryResult.value?.data && queryResult.value?.columns) {
    renderChart(queryResult.value.data, queryResult.value.columns)
  }
}

// 渲染图表
const renderChart = (data, columns) => {
  if (!chartContainer.value || !data || data.length === 0) return
  if (chartInstance) { chartInstance.dispose() }
  chartInstance = echarts.init(chartContainer.value)

  const { xAxis, series, yAxisData } = analyzeChartData(data, columns)

  const option = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: series.map(s => s.name), bottom: 10 },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: xAxis, axisLabel: { interval: 0, rotate: 30, fontSize: 11 } },
    yAxis: yAxisData,
    series
  }
  chartInstance.setOption(option)
  window.addEventListener('resize', () => { chartInstance?.resize() })
}

// 分析图表数据
const analyzeChartData = (data, columns) => {
  if (!data || data.length === 0 || !columns || columns.length < 2) {
    return { xAxis: [], series: [], yAxisData: { type: 'value' } }
  }

  let dimensionField = columns.find(c => {
    const sample = data[0]?.[c]
    return sample !== null && typeof sample === 'string' && String(sample).length < 30
  }) || columns[0]

  const xAxis = data.map(item => String(item[dimensionField] ?? ''))

  const measureFields = columns.filter(c => {
    if (c === dimensionField) return false
    const sample = data[0]?.[c]
    return sample !== null && !isNaN(Number(sample))
  })

  const series = measureFields.slice(0, 3).map((field, idx) => ({
    name: field,
    type: chartType.value,
    data: data.map(item => Number(item[field]) || 0),
    itemStyle: { color: chartColors[idx % chartColors.length] },
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

  if (chartType.value === 'pie') {
    const mainField = measureFields[0] || columns[1]
    series.length = 0
    series.push({
      name: mainField, type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c} ({d}%)', fontSize: 11 },
      emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
      data: data.map((item, i) => ({
        name: String(item[dimensionField]),
        value: Number(item[mainField]) || 0,
        itemStyle: { color: chartColors[i % chartColors.length] }
      }))
    })
  }

  const yAxisData = {
    type: 'value',
    axisLabel: { formatter: (v) => Math.abs(v) >= 10000 ? (v / 10000).toFixed(0) + '万' : v }
  }
  return { xAxis, series, yAxisData }
}

onUnmounted(() => {
  if (chartInstance) { chartInstance.dispose() }
})

onMounted(() => {
  loadHistoryList()
})
</script>

<style scoped>
.ai-query-simple {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 12px;
  padding: 20px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-wrap {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  color: #fff;
}

.header-text .page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.header-text .page-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.model-tag {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 卡片通用样式 */
.section-card {
  position: relative;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.section-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.card-accent.primary { background: #2563eb; }
.card-accent.success { background: #22c55e; }
.card-accent.warning { background: #64748b; }

.section-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon-sm {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
}

.success-bg { background: #22c55e; }
.warning-bg { background: #64748b; }
.pink-bg { background: rgba(255, 255, 255, 0.15); }

.primary-bg { background: #2563eb; }

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #64748b;
}

.section-body {
  padding: 20px;
}

/* 查询输入 */
.question-input {
  margin-bottom: 16px;
}

.question-input :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.6;
  border-radius: 8px;
}

.query-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 快捷问题 */
.quick-section {
  margin-bottom: 4px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.question-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 12px;
  border-radius: 8px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s;
}

.question-tag:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #3b82f6;
}

/* 思考过程 */
.thinking-collapse {
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.thinking-collapse :deep(.el-collapse-item__header) {
  padding: 0 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
  border-radius: 8px;
}

.thinking-collapse :deep(.el-collapse-item__wrap) {
  border: none;
}

.thinking-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}

.thinking-content {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.thinking-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
}

.thinking-label {
  font-weight: 600;
  color: #64748b;
  min-width: 70px;
  flex-shrink: 0;
}

.kw-tag, .table-tag, .field-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

/* 图表区域 */
.chart-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.chart-container {
  width: 100%;
  height: 350px;
}

/* SQL 区域 */
.sql-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.sql-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
  font-weight: 500;
}

.sql-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  margin: 0 0 12px 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 数据区域 */
.data-section {
  margin-top: 16px;
}

.data-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 12px;
}

/* 历史列表 */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.item-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0fdf4;
  color: #22c55e;
}

.history-item .item-icon {
  background: #fef2f2;
  color: #ef4444;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-question {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.item-time {
  font-size: 12px;
  color: #94a3b8;
}

.item-duration {
  font-size: 12px;
  color: #94a3b8;
}

.item-arrow {
  color: #cbd5e1;
  transition: all 0.2s;
}

.history-item:hover .item-arrow {
  color: #3b82f6;
  transform: translateX(2px);
}

/* 示例列表 */
.example-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #334155;
}

.example-item:hover {
  background: #f1f5f9;
  border-color: #3b82f6;
  color: #3b82f6;
}

.example-icon {
  color: #94a3b8;
  flex-shrink: 0;
}

.example-item:hover .example-icon {
  color: #3b82f6;
}

.example-arrow {
  margin-left: auto;
  color: #cbd5e1;
  transition: all 0.2s;
}

.example-item:hover .example-arrow {
  color: #3b82f6;
  transform: translateX(2px);
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-query-simple {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
  }

  .header-icon-wrap {
    width: 44px;
    height: 44px;
  }

  .header-text .page-title {
    font-size: 20px;
  }
}
</style>
