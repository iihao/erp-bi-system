<template>
  <div class="ai-query-container">
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>🤖 AI 智能问数</span>
          <el-tag type="success">Qwen3.5-Plus</el-tag>
        </div>
      </template>

      <!-- 查询输入区 -->
      <div class="query-input">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题，例如：上个月销售额最高的产品是什么？"
          @keyup.enter.ctrl="handleQuery"
        />
        <el-button type="primary" @click="handleQuery" :loading="loading" class="query-btn">
          <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          智能查询
        </el-button>
      </div>

      <!-- 快捷问题 -->
      <div class="quick-questions">
        <span class="label">快捷问题：</span>
        <el-tag
          v-for="q in quickQuestions"
          :key="q"
          closable
          @click="question = q"
          class="question-tag"
        >
          {{ q }}
        </el-tag>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 查询结果 -->
      <div v-else-if="result" class="query-result">
        <el-alert
          :title="result.explanation"
          type="info"
          :closable="false"
          show-icon
          class="result-explanation"
        />

        <!-- SQL 展示 -->
        <div class="sql-section">
          <div class="section-title">
            <span>📝 生成的 SQL</span>
            <el-button size="small" @click="copySql">
              <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              复制
            </el-button>
          </div>
          <pre class="sql-code"><code>{{ result.sql }}</code></pre>
        </div>

        <!-- 数据表格 -->
        <div v-if="result.data && result.data.length > 0" class="data-section">
          <div class="section-title">
            <span>📊 查询结果 ({{ result.data.length }} 条)</span>
            <el-button size="small" @click="exportData">
              <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="7 10 12 15 17 10" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="15" x2="12" y2="3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              导出
            </el-button>
          </div>
          <el-table :data="result.data" border stripe class="result-table">
            <el-table-column
              v-for="col in result.columns"
              :key="col"
              :prop="col"
              :label="col"
            />
          </el-table>
        </div>

        <!-- 无数据提示 -->
        <el-empty v-else description="暂无数据" />
      </div>

      <!-- 初始状态 -->
      <div v-else class="empty-state">
        <el-empty description="输入问题，AI 帮您查询数据" />
        <div class="schema-info">
          <h4>可用数据表：</h4>
          <ul>
            <li><strong>products</strong> - 产品表（产品、价格、库存）</li>
            <li><strong>customers</strong> - 客户表（客户信息、行业）</li>
            <li><strong>sales_orders</strong> - 销售订单表（订单、金额）</li>
            <li><strong>sales_order_items</strong> - 订单明细表（数量、小计）</li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const question = ref('')
const loading = ref(false)
const result = ref(null)

const quickQuestions = [
  '上个月销售额最高的产品是什么？',
  '客户张三的订单有哪些？',
  '各品类的销售占比是多少？',
  '本月总销售额是多少？',
  '库存最少的 5 个产品'
]

const handleQuery = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }

  loading.value = true
  result.value = null

  try {
    const res = await api.aiQuery.execute(question.value)
    result.value = res
    ElMessage.success('查询成功')
  } catch (error) {
    ElMessage.error('查询失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const copySql = () => {
  navigator.clipboard.writeText(result.value.sql)
  ElMessage.success('SQL 已复制')
}

const exportData = () => {
  const data = JSON.stringify(result.value.data, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'query-result.json'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据已导出')
}
</script>

<style scoped>
.ai-query-container {
  padding: 24px;
  background-color: var(--bg-body);
  min-height: 100vh;
}

.query-card {
  max-width: 1200px;
  margin: 0 auto;
  border: 1px solid var(--border);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.query-input {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.query-input :deep(.el-textarea__inner) {
  border-radius: var(--radius);
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.6;
}

.query-input :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 2px rgba(44, 82, 130, 0.1);
}

.query-btn {
  min-width: 140px;
  padding: 14px 24px;
  font-weight: 500;
}

.button-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
  color: currentColor;
  stroke: currentColor;
  fill: none;
}

.quick-questions {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.label {
  font-weight: 600;
  color: var(--text-secondary);
  margin-right: 8px;
  font-size: 13px;
}

.question-tag {
  cursor: pointer;
  background-color: rgba(44, 82, 130, 0.08);
  border-color: rgba(44, 82, 130, 0.2);
  color: var(--primary);
  padding: 6px 14px;
  font-size: 13px;
  transition: all 0.3s;
}

.question-tag:hover {
  background-color: rgba(44, 82, 130, 0.15);
  border-color: var(--primary);
}

.loading-state,
.query-result,
.empty-state {
  margin-top: 20px;
}

.result-explanation {
  margin-bottom: 20px;
  border-radius: var(--radius);
}

.sql-section,
.data-section {
  margin-top: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  letter-spacing: 0.5px;
}

.sql-code {
  background: #f8fafc;
  padding: 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-primary);
}

.result-table {
  margin-top: 12px;
}

.result-table :deep(.el-table__header th) {
  background-color: #f8fafc;
  color: var(--text-secondary);
  font-weight: 600;
}

.result-table :deep(.el-table__row:hover) {
  background-color: #f0f7ff;
}

.schema-info {
  background: #f8fafc;
  padding: 20px;
  border-radius: var(--radius);
  margin-top: 20px;
  border: 1px solid var(--border-light);
}

.schema-info h4 {
  margin-bottom: 12px;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 14px;
}

.schema-info ul {
  list-style: none;
  padding-left: 0;
}

.schema-info li {
  padding: 8px 0;
  color: var(--text-secondary);
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}

.schema-info li:last-child {
  border-bottom: none;
}

.schema-info li strong {
  color: var(--primary);
  font-weight: 600;
}

/* 空状态样式 */
:deep(.el-empty__description) {
  color: var(--text-secondary);
}

:deep(.el-alert__title) {
  font-size: 14px;
}
</style>
