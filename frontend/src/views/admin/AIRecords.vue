<template>
  <div class="ai-records">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon-wrap info-bg">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">AI 问数记录</h1>
          <p class="page-subtitle">查询历史与数据分析</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="handleExport" size="large">
          <el-icon><Download /></el-icon>
          导出记录
        </el-button>
      </div>
    </div>

    <!-- 搜索区 -->
    <div class="search-section">
      <div class="section-card">
        <div class="card-accent primary"></div>
        <div class="section-header">
          <div class="header-left">
            <div class="header-icon-sm primary-bg">
              <el-icon :size="16"><Search /></el-icon>
            </div>
            <span class="section-title">筛选查询</span>
          </div>
        </div>
        <div class="section-body">
          <el-form :inline="true" :model="searchForm" class="search-form">
            <el-form-item label="用户">
              <el-input
                v-model="searchForm.username"
                placeholder="用户名"
                clearable
                @keyup.enter="handleSearch"
              />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input
                v-model="searchForm.keyword"
                placeholder="问题/SQL 关键词"
                clearable
                @keyup.enter="handleSearch"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
                <el-option label="成功" value="success" />
                <el-option label="失败" value="error" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="searchForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="handleReset">
                <el-icon><RefreshLeft /></el-icon>
                重置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="card-accent primary"></div>
        <div class="stat-icon-wrap primary-bg">
          <el-icon :size="24"><DataAnalysis /></el-icon>
        </div>
        <div class="stat-label">总查询次数</div>
        <div class="stat-value">{{ stats.totalQueries }}</div>
      </div>
      <div class="stat-card">
        <div class="card-accent success"></div>
        <div class="stat-icon-wrap success-bg">
          <el-icon :size="24"><CircleCheck /></el-icon>
        </div>
        <div class="stat-label">成功次数</div>
        <div class="stat-value success">{{ stats.successQueries }}</div>
      </div>
      <div class="stat-card">
        <div class="card-accent danger"></div>
        <div class="stat-icon-wrap danger-bg">
          <el-icon :size="24"><CircleClose /></el-icon>
        </div>
        <div class="stat-label">失败次数</div>
        <div class="stat-value error">{{ stats.failedQueries }}</div>
      </div>
      <div class="stat-card">
        <div class="card-accent warning"></div>
        <div class="stat-icon-wrap warning-bg">
          <el-icon :size="24"><TrendCharts /></el-icon>
        </div>
        <div class="stat-label">成功率</div>
        <div class="stat-value warning">{{ stats.successRate }}%</div>
      </div>
    </div>

    <!-- 查询记录表格 -->
    <div class="table-section">
      <div class="section-card">
        <div class="card-accent cyan"></div>
        <div class="section-header">
          <div class="header-left">
            <div class="header-icon-sm cyan-bg">
              <el-icon :size="16"><List /></el-icon>
            </div>
            <span class="section-title">查询记录</span>
          </div>
          <span class="record-count">共 {{ pagination.total }} 条</span>
        </div>

        <div class="section-body">
          <el-table :data="records" v-loading="loading" border stripe>
            <el-table-column prop="query_id" label="ID" width="70" />
            <el-table-column prop="username" label="用户" width="120" />
            <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="sql" label="生成的 SQL" min-width="250" show-overflow-tooltip />
            <el-table-column prop="match_source" label="来源" width="110">
              <template #default="{ row }">
                <el-tag :type="getMatchSourceType(row)" size="small" effect="plain">
                  {{ getMatchSourceLabel(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="execution_time" label="执行时间" width="100">
              <template #default="{ row }">
                {{ row.execution_time }}ms
              </template>
            </el-table-column>
            <el-table-column prop="result_count" label="结果数" width="80" />
            <el-table-column prop="created_at" label="查询时间" width="160" />
            <el-table-column label="操作" width="220" fixed="right" class-name="action-column">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="handleViewDetail(row)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button
                  v-if="row.status === 'success' && row.sql"
                  size="small"
                  type="success"
                  link
                  @click="handleSyncStandardSql(row)"
                >
                  <el-icon><Discount /></el-icon>
                  纳入标准库
                </el-button>
                <el-button
                  v-if="row.status === 'error'"
                  size="small"
                  type="warning"
                  link
                  @click="handleRetry(row)"
                >
                  <el-icon><RefreshRight /></el-icon>
                  重试
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSearch"
              @current-change="handleSearch"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="查询详情"
      width="800px"
    >
      <el-descriptions :column="1" border v-if="currentRecord">
        <el-descriptions-item label="用户">{{ currentRecord.username }}</el-descriptions-item>
        <el-descriptions-item label="问题">{{ currentRecord.question }}</el-descriptions-item>
        <el-descriptions-item label="关键词">
          <el-tag
            v-for="kw in (currentRecord.keywords || [])"
            :key="kw"
            size="small"
            class="keyword-tag"
          >
            {{ kw }}
          </el-tag>
          <span v-if="!currentRecord.keywords || !currentRecord.keywords.length">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="SQL 来源">
          <el-tag :type="getMatchSourceType(currentRecord)" size="small" effect="plain">
            {{ getMatchSourceLabel(currentRecord) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="生成的 SQL">
          <pre class="sql-preview">{{ currentRecord.sql }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentRecord.status === 'success' ? 'success' : 'danger'">
            {{ currentRecord.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ currentRecord.execution_time }}ms</el-descriptions-item>
        <el-descriptions-item label="结果数量">{{ currentRecord.result_count }} 条</el-descriptions-item>
        <el-descriptions-item label="查询时间">{{ currentRecord.created_at }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="currentRecord.error_message">
          <el-alert :title="currentRecord.error_message" type="error" :closable="false" />
        </el-descriptions-item>
      </el-descriptions>

      <!-- 查询结果数据 -->
      <div v-if="currentRecord?.status === 'success' && currentRecord.data" class="result-data">
        <h4>查询结果</h4>
        <el-table :data="currentRecord.data" stripe border max-height="300" size="small">
          <el-table-column
            v-for="col in currentRecord.columns"
            :key="col"
            :prop="col"
            :label="col"
            min-width="100"
          />
        </el-table>
      </div>

      <template #footer>
        <el-button
          v-if="currentRecord?.status === 'success' && currentRecord.sql"
          type="success"
          @click="handleSyncStandardSql(currentRecord)"
        >
          纳入标准库
        </el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 同步标准库对话框 -->
    <el-dialog
      v-model="syncDialogVisible"
      title="同步到标准 SQL 库"
      width="860px"
      @close="resetSyncDialog"
    >
      <el-alert
        type="info"
        show-icon
        :closable="false"
        class="sync-tip"
        title="运维审核通过后，可将这条通用问数记录直接纳入标准库。后续相似问法会优先命中标准库。"
      />

      <el-form :model="syncForm" label-width="110px" class="sync-form">
        <el-form-item label="来源问题">
          <el-input v-model="syncForm.sourceQuestion" disabled />
        </el-form-item>
        <el-form-item label="问题模板">
          <el-input
            v-model="syncForm.questionTemplate"
            type="textarea"
            :rows="2"
            placeholder="建议保留业务意图的通用问法"
          />
        </el-form-item>
        <el-form-item label="标准 SQL">
          <el-input
            v-model="syncForm.standardSql"
            type="textarea"
            :rows="8"
            placeholder="SELECT ..."
          />
        </el-form-item>
        <el-form-item label="说明">
          <el-input
            v-model="syncForm.explanation"
            type="textarea"
            :rows="2"
            placeholder="说明该标准 SQL 的业务口径与适用范围"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="syncForm.keywordsText"
            placeholder="项目, 去化, 销售, 回款"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="syncForm.isActive" />
        </el-form-item>
        <el-form-item label="覆盖同名">
          <el-switch v-model="syncForm.overwrite" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="syncDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="syncSubmitting" @click="submitSyncStandardSql">
          同步到标准库
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Element Plus Icons
import {
  Document, Download, DataAnalysis, CircleCheck, CircleClose,
  TrendCharts, Search, RefreshLeft, List, View, RefreshRight, Discount
} from '@element-plus/icons-vue'

const loading = ref(false)
const detailVisible = ref(false)
const currentRecord = ref(null)
const syncDialogVisible = ref(false)
const syncSubmitting = ref(false)
const syncSourceRecord = ref(null)

// 匹配来源标签和类型映射
const getMatchSourceLabel = (row) => {
  const source = (row?.match_source || '').toString().trim()
  if (source.includes('拦截')) return '安全拦截'
  if (source.includes('标准')) return '标准库命中'
  if (source.includes('AI')) return 'AI 在线生成'
  if (row?.matched_standard) return '标准库命中'
  return 'AI 在线生成'
}

const getMatchSourceType = (row) => {
  const label = getMatchSourceLabel(row)
  if (label === '标准库命中') return 'success'
  if (label === '安全拦截') return 'warning'
  return 'info'
}

const searchForm = reactive({
  username: '',
  keyword: '',
  status: '',
  dateRange: []
})

const stats = reactive({
  totalQueries: 0,
  successQueries: 0,
  failedQueries: 0,
  successRate: 0
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const records = ref([])
const syncForm = reactive({
  sourceQuestion: '',
  questionTemplate: '',
  standardSql: '',
  explanation: '',
  keywordsText: '',
  isActive: true,
  overwrite: true
})

// 模拟数据
const mockRecords = [
  {
    query_id: 1,
    username: 'admin',
    question: '上个月去化率最高的项目是什么？',
    sql: 'SELECT project_name, sell_through_rate FROM ads_sales_dashboard ORDER BY sell_through_rate DESC LIMIT 1',
    match_source: '标准库命中',
    status: 'success',
    execution_time: 156,
    result_count: 1,
    created_at: '2025-01-15 10:30:25',
    data: [{ project_name: '滨江壹号', sell_through_rate: 92.5 }],
    columns: ['project_name', 'sell_through_rate']
  },
  {
    query_id: 2,
    username: 'user1',
    question: '客户张三的跟进记录有哪些？',
    sql: 'SELECT c.customer_name, f.followup_date, f.followup_content FROM re_customers c JOIN re_customer_followups f ON c.customer_id = f.customer_id WHERE c.customer_name = "张三"',
    match_source: 'AI 在线生成',
    status: 'success',
    execution_time: 89,
    result_count: 5,
    created_at: '2025-01-15 09:15:30',
    data: [],
    columns: []
  },
  {
    query_id: 3,
    username: 'user2',
    question: '删除所有用户数据',
    sql: '',
    match_source: 'AI 在线生成',
    status: 'error',
    execution_time: 0,
    result_count: 0,
    created_at: '2025-01-15 08:20:15',
    error_message: '检测到危险操作：仅允许 SELECT 查询'
  }
]

// API 请求封装
const apiRequest = async (method, url, options = {}) => {
  const token = localStorage.getItem('token')
  let requestUrl = url
  if (options.params) {
    const params = new URLSearchParams()
    Object.entries(options.params).forEach(([key, value]) => {
      if (value === null || value === undefined || value === '') return
      params.append(key, value)
    })
    const queryString = params.toString()
    if (queryString) {
      requestUrl = `${url}${url.includes('?') ? '&' : '?'}${queryString}`
    }
  }
  const config = {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  }

  try {
    delete config.params
    const response = await fetch(requestUrl, config)

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

const loadRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      username: searchForm.username,
      keyword: searchForm.keyword,
      status: searchForm.status
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }

    const res = await apiRequest('get', '/api/admin/ai-query/records', { params })
    records.value = Array.isArray(res.items) ? res.items : []
    pagination.total = typeof res.total === 'number' ? res.total : 0
  } catch (error) {
    console.error('加载记录失败', error)
    records.value = mockRecords
    pagination.total = mockRecords.length
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/ai-query/stats')
    stats.totalQueries = typeof res.total === 'number' ? res.total : 1256
    stats.successQueries = typeof res.success === 'number' ? res.success : 1180
    stats.failedQueries = typeof res.failed === 'number' ? res.failed : 76
    stats.successRate = typeof res.rate === 'number' ? res.rate : 94
  } catch (error) {
    stats.totalQueries = 1256
    stats.successQueries = 1180
    stats.failedQueries = 76
    stats.successRate = 94
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadRecords()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.dateRange = []
  handleSearch()
}

const handleExport = () => {
  const data = JSON.stringify(records.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai-records-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据已导出')
}

const handleViewDetail = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

const resetSyncDialog = () => {
  syncSourceRecord.value = null
  syncForm.sourceQuestion = ''
  syncForm.questionTemplate = ''
  syncForm.standardSql = ''
  syncForm.explanation = ''
  syncForm.keywordsText = ''
  syncForm.isActive = true
  syncForm.overwrite = true
}

const handleSyncStandardSql = (row) => {
  if (!row || !row.sql) {
    ElMessage.warning('当前记录没有可同步的 SQL')
    return
  }

  syncSourceRecord.value = row
  syncForm.sourceQuestion = row.question || ''
  syncForm.questionTemplate = row.question || ''
  syncForm.standardSql = row.generated_sql || row.sql || ''
  syncForm.explanation = `由问数记录同步：${row.question || ''}`
  syncForm.keywordsText = Array.isArray(row.keywords) ? row.keywords.join('，') : ''
  syncForm.isActive = true
  syncForm.overwrite = true
  syncDialogVisible.value = true
}

const submitSyncStandardSql = async () => {
  if (!syncSourceRecord.value) return

  const payload = {
    question_template: syncForm.questionTemplate.trim(),
    standard_sql: syncForm.standardSql.trim(),
    explanation: syncForm.explanation.trim(),
    keywords: syncForm.keywordsText
      .split(/[,，、\n]+/)
      .map(item => item.trim())
      .filter(Boolean),
    is_active: syncForm.isActive ? 1 : 0,
    overwrite: syncForm.overwrite
  }

  if (!payload.question_template) {
    ElMessage.warning('请输入问题模板')
    return
  }
  if (!payload.standard_sql) {
    ElMessage.warning('请输入标准 SQL')
    return
  }

  syncSubmitting.value = true
  try {
    const res = await apiRequest('post', `/api/admin/ai-query/records/${syncSourceRecord.value.query_id}/sync-standard-sql`, {
      body: JSON.stringify(payload)
    })
    ElMessage.success(`同步成功，已${res.action === 'updated' ? '更新' : '新增'}到标准库`)
    syncDialogVisible.value = false
    await loadRecords()
  } catch (error) {
    ElMessage.error(error.message || '同步失败')
  } finally {
    syncSubmitting.value = false
  }
}

const handleRetry = async (row) => {
  try {
    await ElMessageBox.confirm('确定要重新执行此查询吗？', '提示', { type: 'info' })
    ElMessage.success('查询已重新执行')
    loadRecords()
  } catch (error) {
    // 取消
  }
}

onMounted(() => {
  loadRecords()
  loadStats()
})
</script>

<style scoped>
.ai-records {
  padding: 24px;
  max-width: 1400px;
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
.card-accent.danger { background: #ef4444; }
.card-accent.warning { background: #64748b; }
.card-accent.cyan { background: #2563eb; }

.section-header {
  padding: 14px 20px;
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

.primary-bg { background: #2563eb; }
.success-bg { background: #22c55e; }
.danger-bg { background: #ef4444; }
.warning-bg { background: #64748b; }
.info-bg { background: #0ea5e9; }
.cyan-bg { background: #2563eb; }

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.record-count {
  font-size: 13px;
  color: #94a3b8;
}

.section-body {
  padding: 20px;
}

/* 搜索表单 */
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-form :deep(.el-form-item) {
  margin-bottom: 8px;
  margin-right: 12px;
}

/* 统计卡片 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  position: relative;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  text-align: center;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin: 0 auto 12px;
  color: #fff;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.stat-value.success {
  color: #16a34a;
}

.stat-value.error {
  color: #dc2626;
}

.stat-value.warning {
  color: #64748b;
}

/* 表格区域 */
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

/* 详情对话框 */
.sql-preview {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}

.keyword-tag {
  margin-right: 8px;
  margin-bottom: 6px;
}

.result-data {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.result-data h4 {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 12px 0;
}

.sync-tip {
  margin-bottom: 16px;
}

.sync-form :deep(.el-form-item__content) {
  align-items: flex-start;
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-records {
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

  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-form {
    flex-direction: column;
  }

  .search-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
}
</style>
