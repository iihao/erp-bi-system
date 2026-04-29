<template>
  <div class="ai-enhanced-query">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap purple-bg">
          <el-icon :size="24"><MagicStick /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">智能问数</h1>
          <p class="page-subtitle">AI 驱动的数据分析与可视化</p>
        </div>
      </div>
      <el-tag size="large" effect="dark" class="model-tag">
        <el-icon><Cpu /></el-icon>
        Qwen3.6-Plus
      </el-tag>
    </div>

    <el-container class="page-container">
      <!-- 左侧：历史记录和数据库结构 -->
      <el-aside width="320px" class="sidebar-panel">
        <!-- 查询历史 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="header-left">
              <div class="panel-icon-sm cyan-bg">
                <el-icon :size="14"><Clock /></el-icon>
              </div>
              <span>查询历史</span>
            </div>
            <el-button size="small" text @click="clearHistory">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>

          <el-input
            v-model="historySearch"
            placeholder="搜索历史查询..."
            size="small"
            class="history-search"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-scrollbar height="300px">
            <div
              v-for="record in filteredHistory"
              :key="record.id"
              class="history-item"
              @click="loadHistory(record)"
            >
              <div class="item-question">{{ record.question }}</div>
              <div class="item-time">{{ formatDate(record.timestamp) }}</div>
            </div>
            <el-empty v-if="filteredHistory.length === 0" description="暂无记录" :image-size="60" />
          </el-scrollbar>
        </div>

        <!-- 数据库结构 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="header-left">
              <div class="panel-icon-sm info-bg">
                <el-icon :size="14"><Collection /></el-icon>
              </div>
              <span>数据库结构</span>
            </div>
          </div>

          <el-scrollbar height="200px">
            <div class="schema-table" v-for="table in dbSchema" :key="table.name">
              <div class="table-name">
                <el-icon><Files /></el-icon>
                {{ table.name }}
              </div>
              <div class="table-fields">
                <div v-for="field in table.fields" :key="field.name" class="field-item">
                  <el-icon><Key /></el-icon>
                  <span class="field-name">{{ field.name }}</span>
                  <span class="field-type">{{ field.type }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </el-aside>

      <!-- 中间：主内容区域 -->
      <el-main class="main-content">
        <div class="query-section">
          <div class="section-card">
            <div class="card-accent purple"></div>
            <div class="section-header">
              <div class="header-left">
                <div class="header-icon-sm purple-bg">
                  <el-icon :size="16"><ChatDotRound /></el-icon>
                </div>
                <span class="section-title">AI 智能问数</span>
                <el-tag size="small" type="success" effect="dark">Qwen3.6-Plus</el-tag>
              </div>
              <el-button size="small" text @click="clearAll">
                <el-icon><RefreshLeft /></el-icon>
                重置
              </el-button>
            </div>

            <div class="section-body">
              <el-input
                v-model="currentQuestion"
                type="textarea"
                :rows="4"
                placeholder="请输入您的问题，例如：上个月去化率最高的项目是什么？"
                @keyup.enter.ctrl="handleQuery"
                maxlength="500"
                show-word-limit
              />

              <div class="quick-actions">
                <el-button-group>
                  <el-button type="primary" @click="handleQuery" :loading="loading" size="large">
                    <el-icon><Search /></el-icon>
                    AI 查询
                  </el-button>
                  <el-button @click="showAdvancedOptions = !showAdvancedOptions" size="large">
                    <el-icon><Setting /></el-icon>
                  </el-button>
                </el-button-group>

                <el-button @click="showSampleQuestions = true" type="info" plain size="large">
                  <el-icon><List /></el-icon>
                  示例问题
                </el-button>
              </div>

              <!-- 高级选项 -->
              <el-collapse-transition>
                <div v-show="showAdvancedOptions" class="advanced-options">
                  <el-form :model="advancedOptions" size="small" label-position="top">
                    <el-row :gutter="12">
                      <el-col :span="12">
                        <el-form-item label="结果数量">
                          <el-input-number v-model="advancedOptions.limit" :min="1" :max="1000" />
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item label="相似度阈值">
                          <el-slider v-model="advancedOptions.similarity" :min="0" :max="1" :step="0.1" />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-row :gutter="12">
                      <el-col :span="12">
                        <el-form-item label="查询模式">
                          <el-select v-model="advancedOptions.mode">
                            <el-option label="标准模式" value="standard" />
                            <el-option label="深度分析" value="analysis" />
                            <el-option label="图表模式" value="visualization" />
                          </el-select>
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item label="优先级">
                          <el-select v-model="advancedOptions.priority">
                            <el-option label="普通" value="normal" />
                            <el-option label="高" value="high" />
                          </el-select>
                        </el-form-item>
                      </el-col>
                    </el-row>
                  </el-form>
                </div>
              </el-collapse-transition>
            </div>
          </div>
        </div>

        <!-- 结果展示区域 -->
        <div v-if="queryResult" class="result-section">
          <div class="section-card">
            <div class="card-accent success"></div>
            <div class="section-header">
              <div class="header-left">
                <div class="header-icon-sm success-bg">
                  <el-icon :size="16"><DataAnalysis /></el-icon>
                </div>
                <span class="section-title">查询结果</span>
              </div>
              <div class="result-stats">
                <el-tag size="small" type="success">{{ queryResult.data?.length || 0 }} 条记录</el-tag>
                <el-tag size="small" type="info">耗时 {{ executionTime }}ms</el-tag>
              </div>
            </div>

            <div class="section-body">
              <!-- AI 解释 -->
              <div class="ai-explanation" v-if="queryResult.explanation">
                <el-alert
                  :title="queryResult.explanation"
                  type="info"
                  :closable="false"
                  show-icon
                />
              </div>

              <!-- 生成的 SQL -->
              <div class="sql-section">
                <div class="subsection-header">
                  <div class="header-left">
                    <el-icon><EditPen /></el-icon>
                    <span>生成的 SQL</span>
                  </div>
                  <el-button size="small" @click="copySql">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                </div>
                <pre class="sql-code">{{ queryResult.sql }}</pre>
              </div>

              <!-- 可视化结果 -->
              <div class="visualization-section" v-if="showVisualization">
                <div class="subsection-header">
                  <div class="header-left">
                    <el-icon><TrendCharts /></el-icon>
                    <span>数据可视化</span>
                  </div>
                  <el-button-group>
                    <el-button size="small" :type="chartType === 'bar' ? 'primary' : ''" @click="chartType = 'bar'">
                      柱状图
                    </el-button>
                    <el-button size="small" :type="chartType === 'line' ? 'primary' : ''" @click="chartType = 'line'">
                      折线图
                    </el-button>
                    <el-button size="small" :type="chartType === 'pie' ? 'primary' : ''" @click="chartType = 'pie'">
                      饼图
                    </el-button>
                  </el-button-group>
                </div>
                <div class="chart-container">
                  <component
                    :is="getChartComponent(chartType)"
                    :data="chartData"
                    style="width: 100%; height: 300px;"
                  />
                </div>
              </div>

              <!-- 数据表格 -->
              <div class="data-table-section">
                <div class="subsection-header">
                  <div class="header-left">
                    <el-icon><Grid /></el-icon>
                    <span>数据表格</span>
                  </div>
                  <div class="table-actions">
                    <el-button size="small" @click="exportToCsv">
                      <el-icon><Download /></el-icon>
                      导出 CSV
                    </el-button>
                    <el-button size="small" @click="exportToExcel">
                      <el-icon><Document /></el-icon>
                      导出 Excel
                    </el-button>
                  </div>
                </div>
                <el-table
                  :data="queryResult.data"
                  border
                  stripe
                  height="400"
                  style="width: 100%"
                >
                  <el-table-column
                    v-for="col in queryResult.columns"
                    :key="col"
                    :prop="col"
                    :label="col"
                    :min-width="120"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
            </div>
          </div>
        </div>

        <!-- 初始状态 -->
        <div v-else class="empty-state">
          <div class="empty-content">
            <div class="empty-icon-wrap">
              <el-icon :size="48"><ChatDotRound /></el-icon>
            </div>
            <p class="empty-text">输入问题，AI 帮您查询数据</p>
          </div>
        </div>
      </el-main>

      <!-- 右侧：AI 建议和智能辅助 -->
      <el-aside width="320px" class="assistant-panel">
        <!-- AI 建议 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="header-left">
              <div class="panel-icon-sm warning-bg">
                <el-icon :size="14"><Lightning /></el-icon>
              </div>
              <span>AI 建议</span>
            </div>
          </div>

          <div class="suggestions-list">
            <div
              v-for="suggestion in suggestions"
              :key="suggestion.id"
              class="suggestion-item"
              @click="applySuggestion(suggestion)"
            >
              <div class="suggestion-question">{{ suggestion.question }}</div>
              <div class="suggestion-description">{{ suggestion.description }}</div>
              <el-icon class="item-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <!-- 数据洞察 -->
        <div class="panel-card">
          <div class="panel-header">
            <div class="header-left">
              <div class="panel-icon-sm success-bg">
                <el-icon :size="14"><DataAnalysis /></el-icon>
              </div>
              <span>数据洞察</span>
            </div>
          </div>

          <div class="insights-content">
            <div class="insight-item">
              <div class="insight-title">数据质量评分</div>
              <el-rate v-model="dataQualityScore" disabled show-score score-template="{value} 分" />
            </div>
            <div class="insight-item">
              <div class="insight-title">查询准确性</div>
              <el-progress :percentage="accuracyPercentage" :color="accuracyColor" />
            </div>
            <div class="insight-item">
              <div class="insight-title">智能优化建议</div>
              <div class="optimization-tips">
                <el-tag v-for="tip in optimizationTips" :key="tip" type="warning" size="small" style="margin-right: 6px; margin-bottom: 6px;">
                  {{ tip }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </el-aside>
    </el-container>

    <!-- 示例问题弹窗 -->
    <el-dialog v-model="showSampleQuestions" title="示例问题" width="600px">
      <div class="sample-list">
        <div
          v-for="sample in sampleQuestions"
          :key="sample"
          class="sample-item"
          @click="selectSample(sample)"
        >
          <el-icon class="sample-icon"><ChatLineRound /></el-icon>
          <span>{{ sample }}</span>
          <el-icon class="sample-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Element Plus Icons
import {
  MagicStick, Cpu, Clock, Delete, Search, Collection, Files, Key,
  ChatDotRound, RefreshLeft, Setting, List, DataAnalysis, EditPen,
  CopyDocument, TrendCharts, Grid, Download, Document, Lightning,
  ArrowRight, ChatLineRound
} from '@element-plus/icons-vue'

// 页面状态
const currentQuestion = ref('')
const loading = ref(false)
const queryResult = ref(null)
const executionTime = ref(0)
const showAdvancedOptions = ref(false)
const showSampleQuestions = ref(false)
const showVisualization = ref(true)

// 历史记录
const historySearch = ref('')
const queryHistory = ref([
  { id: 1, question: '上个月去化率最高的项目是什么？', timestamp: new Date(Date.now() - 3600000) },
  { id: 2, question: '各项目签约金额占比情况', timestamp: new Date(Date.now() - 7200000) },
  { id: 3, question: '客户张三的跟进记录有哪些？', timestamp: new Date(Date.now() - 86400000) },
  { id: 4, question: '本月回款总额是多少？', timestamp: new Date(Date.now() - 172800000) }
])

// 高级选项
const advancedOptions = reactive({
  limit: 100,
  similarity: 0.8,
  mode: 'standard',
  priority: 'normal'
})

// 数据库结构
const dbSchema = ref([
  {
    name: 're_projects',
    fields: [
      { name: 'project_id', type: 'INT' },
      { name: 'project_code', type: 'VARCHAR' },
      { name: 'project_name', type: 'VARCHAR' },
      { name: 'city', type: 'VARCHAR' },
      { name: 'project_status', type: 'VARCHAR' }
    ]
  },
  {
    name: 're_buildings',
    fields: [
      { name: 'building_id', type: 'INT' },
      { name: 'project_id', type: 'INT' },
      { name: 'building_code', type: 'VARCHAR' },
      { name: 'building_name', type: 'VARCHAR' }
    ]
  },
  {
    name: 're_units',
    fields: [
      { name: 'unit_id', type: 'INT' },
      { name: 'building_id', type: 'INT' },
      { name: 'unit_code', type: 'VARCHAR' },
      { name: 'unit_status', type: 'VARCHAR' }
    ]
  },
  {
    name: 're_contracts',
    fields: [
      { name: 'contract_id', type: 'INT' },
      { name: 'contract_code', type: 'VARCHAR' },
      { name: 'contract_date', type: 'DATE' },
      { name: 'total_price', type: 'DECIMAL' }
    ]
  },
  {
    name: 're_payments',
    fields: [
      { name: 'payment_id', type: 'INT' },
      { name: 'payment_code', type: 'VARCHAR' },
      { name: 'payment_date', type: 'DATE' },
      { name: 'amount', type: 'DECIMAL' }
    ]
  },
  {
    name: 'ads_sales_dashboard',
    fields: [
      { name: 'project_name', type: 'VARCHAR' },
      { name: 'sold_units', type: 'INT' },
      { name: 'available_units', type: 'INT' },
      { name: 'sell_through_rate', type: 'DECIMAL' }
    ]
  }
])

// AI 建议
const suggestions = ref([
  { id: 1, question: '查询项目去化趋势', description: '按时间维度分析去化率变化' },
  { id: 2, question: '客户跟进统计', description: '按来源或意向等级统计客户跟进情况' },
  { id: 3, question: '签约金额排行', description: '统计签约金额最高的项目' },
  { id: 4, question: '回款预警查询', description: '查找回款不足或逾期的合同' }
])

// 智能分析
const dataQualityScore = ref(4.5)
const accuracyPercentage = ref(92)
const accuracyColor = computed(() => {
  if (accuracyPercentage.value >= 90) return '#67C23A'
  if (accuracyPercentage.value >= 70) return '#E6A23C'
  return '#F56C6C'
})

const optimizationTips = ref([
  '建议添加时间范围筛选',
  '考虑按维度字段分组',
  '可优化索引提升查询性能'
])

// 示例问题
const sampleQuestions = [
  '上个月去化率最高的项目是什么？',
  '客户张三的跟进记录有哪些？',
  '各项目的签约金额占比是多少？',
  '本月回款总额是多少？',
  '应收余额最少的 5 个合同',
  '最近一周的签约趋势',
  '哪个项目的退款风险最高？',
  '项目的平均单价对比'
]

// 图表相关
const chartType = ref('bar')
const chartData = ref([])

// 计算属性
const filteredHistory = computed(() => {
  if (!historySearch.value) return queryHistory.value
  return queryHistory.value.filter(record =>
    record.question.toLowerCase().includes(historySearch.value.toLowerCase())
  )
})

// 方法
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
  const response = await fetch(url, config)
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || data.message || '请求失败')
  return data
}

const handleQuery = async () => {
  if (!currentQuestion.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  loading.value = true
  const startTime = Date.now()

  try {
    const result = await apiRequest('post', '/api/ai-query/execute-query', {
      body: JSON.stringify({
        question: currentQuestion.value,
        top_k: advancedOptions.limit
      })
    })

    executionTime.value = Date.now() - startTime

    queryResult.value = {
      sql: result.sql || '',
      explanation: result.explanation || 'SQL 生成成功',
      data: result.data || [],
      columns: result.columns || []
    }

    if (result.data && result.data.length > 0) {
      chartData.value = result.data.map(item => {
        const chartItem = {}
        for (const key in item) {
          chartItem[key] = item[key]
        }
        return chartItem
      })
    }

    addToHistory(currentQuestion.value)

    ElMessage.success(`查询成功，耗时 ${executionTime.value}ms`)

  } catch (error) {
    console.error('AI 查询失败', error)
    ElMessage.error('查询失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const addToHistory = (question) => {
  queryHistory.value.unshift({
    id: Date.now(),
    question,
    timestamp: new Date()
  })

  if (queryHistory.value.length > 50) {
    queryHistory.value = queryHistory.value.slice(0, 50)
  }
}

const loadHistory = (record) => {
  currentQuestion.value = record.question
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？', '确认清空', {
      type: 'warning'
    })
    queryHistory.value = []
    ElMessage.success('历史记录已清空')
  } catch {
    // 用户取消
  }
}

const copySql = () => {
  navigator.clipboard.writeText(queryResult.value.sql)
  ElMessage.success('SQL 已复制到剪贴板')
}

const exportToCsv = () => {
  if (!queryResult.value?.data) {
    ElMessage.warning('没有数据可导出')
    return
  }

  const headers = queryResult.value.columns.join(',')
  const rows = queryResult.value.data.map(row =>
    queryResult.value.columns.map(col =>
      `"${String(row[col]).replace(/"/g, '""')}"`
    ).join(',')
  )

  const csvContent = ['\ufeff' + [headers, ...rows].join('\n')]
  const blob = new Blob(csvContent, { type: 'text/csv;charset=utf-8' })

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `query_result_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('数据已导出为 CSV')
}

const exportToExcel = () => {
  ElMessage.info('Excel 导出功能即将推出...')
}

const clearAll = () => {
  currentQuestion.value = ''
  queryResult.value = null
  executionTime.value = 0
}

const selectSample = (sample) => {
  currentQuestion.value = sample
  showSampleQuestions.value = false
}

const applySuggestion = (suggestion) => {
  currentQuestion.value = suggestion.question
  ElMessage.success('已填入建议问题')
}

const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getChartComponent = (type) => {
  return {
    name: 'ChartComponent',
    props: ['data'],
    template: `
      <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #f8fafc; border-radius: 8px;">
        <div style="text-align: center;">
          <div style="font-size: 14px; margin-bottom: 10px; color: #94a3b8; font-weight: 600; letter-spacing: 2px;">CHART</div>
          <div style="font-size: 14px; font-weight: 500; color: #475569;">${type === 'bar' ? '柱状图' : type === 'line' ? '折线图' : '饼图'}</div>
          <div v-if="data" style="margin-top: 8px; font-size: 12px; color: #94a3b8;">{{ data.length }} 条数据</div>
        </div>
      </div>
    `
  }
}
</script>

<style scoped>
.ai-enhanced-query {
  height: calc(100vh - 128px);
  background: #f8fafc;
  display: flex;
  flex-direction: column;
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
  margin: 16px;
  flex-shrink: 0;
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

/* 页面容器 */
.page-container {
  height: calc(100% - 100px);
  flex: 1;
}

/* 侧边栏和助手面板 */
.sidebar-panel,
.assistant-panel {
  background: #f8fafc;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.main-content {
  padding: 16px;
  background: #f1f5f9;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 面板卡片 */
.panel-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.panel-header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.panel-header .header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}

.panel-icon-sm {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #fff;
}

.cyan-bg { background: #0ea5e9; }
.info-bg { background: #0ea5e9; }
.warning-bg { background: #64748b; }
.success-bg { background: #22c55e; }
.purple-bg { background: #2563eb; }
.pink-bg { background: rgba(255, 255, 255, 0.15); }

.primary-bg { background: #2563eb; }

/* 历史搜索 */
.history-search {
  margin: 12px 12px 8px;
  width: calc(100% - 24px);
}

/* 历史项 */
.history-item {
  padding: 10px 12px;
  margin: 0 8px 8px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.history-item:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.item-question {
  font-size: 13px;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-time {
  font-size: 11px;
  color: #94a3b8;
}

/* 数据库结构 */
.schema-table {
  margin: 0 12px 12px;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.table-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: #3b82f6;
  font-size: 13px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
  font-size: 12px;
  color: #64748b;
  padding-left: 8px;
}

.field-item .el-icon {
  color: #cbd5e1;
  width: 12px;
}

.field-name {
  color: #1e293b;
  font-weight: 500;
}

.field-type {
  color: #94a3b8;
  font-family: monospace;
  font-size: 11px;
}

/* 主内容卡片 */
.section-card {
  position: relative;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

.card-accent.purple { background: #2563eb; }
.card-accent.success { background: #22c55e; }

.section-header {
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.section-header .header-left {
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

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.result-stats {
  display: flex;
  gap: 8px;
}

.section-body {
  padding: 20px;
}

/* 查询输入区域 */
.quick-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  gap: 8px;
}

.advanced-options {
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

/* 结果区域 */
.result-section {
  flex-shrink: 0;
}

.ai-explanation {
  margin-bottom: 16px;
}

.sql-section,
.visualization-section,
.data-table-section {
  margin-top: 16px;
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.subsection-header .header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
}

.sql-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 0;
}

.chart-container {
  height: 300px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.table-actions {
  display: flex;
  gap: 8px;
}

/* 空状态 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 400px;
}

.empty-content {
  text-align: center;
}

.empty-icon-wrap {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  color: #cbd5e1;
  margin: 0 auto 16px;
}

.empty-text {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

/* AI 建议列表 */
.suggestions-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  position: relative;
}

.suggestion-item:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.suggestion-question {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  margin-bottom: 4px;
}

.suggestion-description {
  font-size: 12px;
  color: #94a3b8;
}

.item-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #cbd5e1;
  transition: all 0.2s;
}

.suggestion-item:hover .item-arrow {
  color: #3b82f6;
  transform: translateY(-50%) translateX(2px);
}

/* 数据洞察 */
.insights-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.insight-item {
  margin-bottom: 4px;
}

.insight-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  font-size: 13px;
}

.optimization-tips {
  margin-top: 8px;
}

/* 示例问题列表 */
.sample-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sample-item {
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

.sample-item:hover {
  background: #f1f5f9;
  border-color: #3b82f6;
  color: #2563eb;
}

.sample-icon {
  color: #94a3b8;
  flex-shrink: 0;
}

.sample-item:hover .sample-icon {
  color: #2563eb;
}

.sample-arrow {
  margin-left: auto;
  color: #cbd5e1;
  transition: all 0.2s;
}

.sample-item:hover .sample-arrow {
  color: #2563eb;
  transform: translateX(2px);
}

/* 响应式 */
@media (max-width: 1200px) {
  .sidebar-panel,
  .assistant-panel {
    display: none;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    margin: 8px;
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
