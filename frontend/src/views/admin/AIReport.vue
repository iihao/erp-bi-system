<template>
  <div class="ai-report-chat" :class="{ dark: isDark }">
    <!-- 左侧对话列表 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <el-icon :size="20"><Document /></el-icon>
          <span v-if="!sidebarCollapsed" class="logo-text">AI 报表</span>
        </div>
        <el-button text size="small" class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>

      <el-button type="success" round @click="newReport" class="new-btn">
        <el-icon><Plus /></el-icon>
        <span v-if="!sidebarCollapsed">新报表</span>
      </el-button>

      <div class="conv-list">
        <div
          v-for="(conv, idx) in conversations"
          :key="idx"
          class="conv-item"
          :class="{ active: idx === currentConvIdx }"
          @click="switchReport(idx)"
        >
          <el-icon class="conv-icon"><ChatLineRound /></el-icon>
          <span class="conv-title" v-if="!sidebarCollapsed">{{ conv.question }}</span>
        </div>
        <div v-if="conversations.length === 0" class="empty-text">暂无报表</div>
      </div>

      <div class="stats-bar" v-if="!sidebarCollapsed">
        <div class="stat-row">
          <span class="stat-label">今日调用</span>
          <span class="stat-value">{{ stats.today_count || 0 }}/{{ stats.daily_quota || 0 }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">标准库命中</span>
          <span class="stat-value">{{ stats.standard_hits || 0 }}</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <main class="chat-main">
      <!-- 头部 -->
      <header class="chat-header">
        <div class="header-left">
          <el-button text class="menu-btn" @click="sidebarCollapsed = false" v-if="sidebarCollapsed">
            <el-icon><Menu /></el-icon>
          </el-button>
          <span class="model-badge">
            <el-tag type="info" effect="plain" size="small">{{ modelLabel }}</el-tag>
          </span>
        </div>
        <div class="header-right">
          <el-tag :type="keyTypeTagType" effect="plain" size="small">{{ keyTypeLabel }}</el-tag>
          <el-button text size="small" @click="toggleTheme" class="theme-btn" :title="isDark ? '切换亮色' : '切换暗色'">
            <el-icon><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
          <el-button text size="small" @click="clearCurrentReport">
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
            <el-icon :size="48" color="var(--accent)"><Document /></el-icon>
          </div>
          <h2>AI 智能报表</h2>
          <p>输入报表需求，AI 自动生成数据分析报表，支持标准库命中与 AI 在线生成双路径</p>
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
                <!-- 来源标识 -->
                <div class="source-tag">
                  <el-tag :type="msg.matchSource === '标准库命中' ? 'success' : 'warning'" effect="plain" size="small">
                    {{ msg.matchSource }}
                  </el-tag>
                </div>

                <!-- 思考过程 -->
                <div v-if="msg.thinking" class="thinking-panel">
                  <el-collapse v-model="msg.activeThinking">
                    <el-collapse-item name="steps" title="决策流程">
                      <ol class="thinking-list">
                        <li v-for="step in msg.thinking.decision_steps || []" :key="step">{{ step }}</li>
                      </ol>
                    </el-collapse-item>
                    <el-collapse-item name="keywords" title="关键词与匹配">
                      <div class="thinking-tags">
                        <el-tag v-for="kw in msg.thinking.keywords || []" :key="kw" size="small" effect="plain">{{ kw }}</el-tag>
                      </div>
                      <p v-if="msg.thinking.reasoning" class="thinking-reasoning">{{ msg.thinking.reasoning }}</p>
                    </el-collapse-item>
                    <el-collapse-item name="tables" title="推荐表与字段">
                      <div class="thinking-tags">
                        <el-tag v-for="t in msg.thinking.recommended_tables || []" :key="t" size="small" type="success" effect="plain">{{ t }}</el-tag>
                      </div>
                    </el-collapse-item>
                    <el-collapse-item name="profile" title="结果画像">
                      <el-descriptions :column="2" border size="small">
                        <el-descriptions-item label="行数">{{ msg.thinking.result_profile?.row_count || 0 }}</el-descriptions-item>
                        <el-descriptions-item label="列数">{{ msg.thinking.result_profile?.column_count || 0 }}</el-descriptions-item>
                        <el-descriptions-item label="主维度">{{ getFieldLabel(msg.thinking.result_profile?.dimension_field) }}</el-descriptions-item>
                        <el-descriptions-item label="核心指标">{{ getFieldLabel(msg.thinking.result_profile?.measure_field) }}</el-descriptions-item>
                      </el-descriptions>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 报表概览 KPI -->
                <div v-if="msg.cards?.length" class="kpi-grid">
                  <div v-for="(card, i) in msg.cards" :key="i" class="kpi-card">
                    <div class="kpi-label">{{ card.label }}</div>
                    <div class="kpi-value">{{ card.value }}</div>
                    <div class="kpi-sub">{{ card.sub }}</div>
                  </div>
                </div>

                <!-- 数据表格 -->
                <div v-if="msg.data?.length" class="data-panel">
                  <div class="data-header">
                    <span><el-icon :size="14"><Grid /></el-icon> 报表明细（{{ msg.data.length }} 条）</span>
                    <div class="data-actions">
                      <el-button size="small" text @click="exportMsgData(msg)">
                        <el-icon><Download /></el-icon>
                        导出
                      </el-button>
                      <el-button size="small" text @click="copyMsgSql(msg)" v-if="msg.sql">
                        <el-icon><CopyDocument /></el-icon>
                        复制 SQL
                      </el-button>
                    </div>
                  </div>
                  <el-table :data="msg.data" stripe border size="small" max-height="400" class="report-table">
                    <el-table-column
                      v-for="col in msg.columns"
                      :key="col"
                      :prop="col"
                      :label="getFieldLabel(col)"
                      min-width="120"
                      show-overflow-tooltip
                    />
                  </el-table>
                </div>

                <!-- SQL -->
                <div v-if="msg.sql" class="sql-panel">
                  <div class="sql-header">
                    <span><el-icon :size="14"><EditPen /></el-icon> 生成 SQL</span>
                    <el-button size="small" text @click="copyMsgSql(msg)">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-button>
                  </div>
                  <pre class="sql-code">{{ msg.sql }}</pre>
                </div>

                <!-- 生成说明 -->
                <div v-if="msg.explanation" class="explain-panel">
                  <p>{{ msg.explanation }}</p>
                </div>

                <div v-if="msg.role === 'assistant' && (!msg.data || msg.data.length === 0) && !msg.thinking" class="no-data">
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
            placeholder="请输入报表需求，例如：上个月各项目签约回款报表..."
            @keydown.enter.exact.prevent="sendReport"
            class="chat-input"
            resize="none"
          />
          <el-button
            type="success"
            circle
            @click="sendReport"
            :disabled="!inputMessage.trim() || loading"
            class="send-btn"
          >
            <el-icon><Top /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">
          <span>Enter 发送 · Shift+Enter 换行 · 标准库命中零 Token 消耗</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document, ChatLineRound, Delete, Plus, User, Cpu, Top,
  Fold, Expand, Menu, Grid, Download, EditPen, CopyDocument, Sunny, Moon
} from '@element-plus/icons-vue'

const conversations = ref([])
const currentConvIdx = ref(-1)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainerRef = ref(null)
const sidebarCollapsed = ref(false)
const stats = ref({})
const keyTypeLabel = ref('未识别 / 未配置')
const keyType = ref('unknown')
const modelLabel = ref('Qwen3.6-Plus')
const isDark = ref(false)

const suggestions = [
  '生成本月各项目签约回款报表',
  '生成项目成本与费用报表',
  '生成各城市销售额报表',
  '生成应收逾期账款报表',
  '生成各项目净利润报表',
  '生成客户跟进明细报表',
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
  total_subscriptions: '认购套数', order_count: '订单数', quantity: '数量',
  bar: '柱状图', line: '折线图', pie: '饼图', table: '表格'
}

const keyTypeTagType = computed(() => {
  if (keyType.value === 'coding_plan') return 'warning'
  if (keyType.value === 'common') return 'success'
  return 'info'
})

const toggleTheme = () => {
  isDark.value = !isDark.value
  try { localStorage.setItem('ai-report-theme', isDark.value ? 'dark' : 'light') } catch {}
}

const apiRequest = async (method, url, data = {}) => {
  const token = localStorage.getItem('token')
  const config = { method: method.toUpperCase(), headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } }
  if (method.toUpperCase() !== 'GET' && Object.keys(data).length > 0) { config.body = JSON.stringify(data) }
  const response = await fetch(url, config)
  const text = await response.text()
  try { const parsed = JSON.parse(text); if (!response.ok) throw new Error(parsed.detail || parsed.message || '请求失败'); return parsed } catch (e) { if (!response.ok) throw new Error(text || '请求失败'); return text }
}

const formatMoney = (value) => { const num = Number(value || 0); if (!num) return '0'; if (Math.abs(num) >= 100000000) return `${(num / 100000000).toFixed(2)}亿`; if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(2)}万`; return num.toFixed(2) }

const getFieldLabel = (field) => { if (!field) return '字段'; const key = String(field).trim(); if (fieldLabelMap[key]) return fieldLabelMap[key]; const lower = key.toLowerCase(); if (fieldLabelMap[lower]) return fieldLabelMap[lower]; return key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').trim() }

const buildCards = (data, columns, questionText) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) return []
  const dimField = columns.find(c => typeof data[0]?.[c] === 'string') || columns[0]
  const measureField = columns.find(c => { if (c === dimField) return false; const s = data[0]?.[c]; return s !== null && s !== undefined && !Number.isNaN(Number(s)) })
  const values = measureField ? data.map(item => Number(item[measureField]) || 0) : []
  const total = values.reduce((s, v) => s + v, 0)
  const avg = values.length ? total / values.length : 0
  const max = values.length ? Math.max(...values) : 0
  const maxItem = measureField ? data.find(item => Number(item[measureField]) === max) : null
  const cards = [
    { label: '记录数', value: data.length, sub: '报表行数' },
    { label: '字段数', value: columns.length, sub: '输出列数' },
  ]
  if (measureField) { cards.push({ label: '核心指标总计', value: formatMoney(total), sub: getFieldLabel(measureField) }); cards.push({ label: '平均值', value: formatMoney(avg), sub: getFieldLabel(measureField) }) }
  if (maxItem && measureField) cards.push({ label: '最大值', value: formatMoney(max), sub: String(maxItem[dimField] ?? '未知') })
  return cards.slice(0, 5)
}

const scrollToBottom = () => { nextTick(() => { if (messagesContainerRef.value) messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight }) }
const useSuggestion = (text) => { inputMessage.value = text; sendReport() }
const newReport = () => { currentConvIdx.value = -1; messages.value = [] }

const switchReport = (idx) => {
  if (idx === currentConvIdx.value) return
  currentConvIdx.value = idx
  const conv = conversations.value[idx]
  if (conv) { messages.value = conv.messages || []; nextTick(() => scrollToBottom()) }
}

const clearCurrentReport = () => { messages.value = []; currentConvIdx.value = -1 }

const saveConversation = () => {
  if (messages.value.length === 0) return
  const existing = conversations.value.find((c, i) => i === currentConvIdx.value)
  if (existing) { existing.messages = messages.value }
  else { conversations.value.unshift({ question: messages.value[0]?.content || '新报表', messages: [...messages.value], time: new Date().toLocaleString('zh-CN') }); currentConvIdx.value = 0 }
  if (conversations.value.length > 20) conversations.value.pop()
}

const sendReport = async () => {
  if (!inputMessage.value.trim() || loading.value) return
  const text = inputMessage.value.trim(); inputMessage.value = ''
  messages.value.push({ role: 'user', content: text }); await nextTick(); scrollToBottom()
  loading.value = true
  try {
    const res = await apiRequest('POST', '/ai-query/execute-query', { question: text, top_k: 10 })
    const thinking = res.thinking || {}
    const aiMsg = { role: 'assistant', content: '', sql: res.sql || '', explanation: res.explanation || '', data: res.data || [], columns: res.columns || [], thinking, matchSource: thinking.match_source || 'AI 在线生成', cards: buildCards(res.data, res.columns, text), activeThinking: ['steps', 'keywords'] }
    messages.value.push(aiMsg); saveConversation(); await nextTick(); scrollToBottom()
    ElMessage.success('报表生成成功')
  } catch (error) {
    messages.value.push({ role: 'assistant', content: `报表生成失败：${error.message || '未知错误'}`, isError: true })
    ElMessage.error('报表生成失败：' + (error.message || '未知错误'))
  } finally { loading.value = false; await nextTick(); scrollToBottom() }
}

const exportMsgData = (msg) => {
  if (!msg?.data) return
  const blob = new Blob([JSON.stringify(msg.data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `ai-report-${Date.now()}.json`; a.click()
  URL.revokeObjectURL(url); ElMessage.success('数据已导出')
}

const copyMsgSql = async (msg) => { if (!msg?.sql) return; await navigator.clipboard.writeText(msg.sql); ElMessage.success('SQL 已复制') }

const loadConfig = async () => { try { const config = await apiRequest('get', '/api/admin/ai-config/current'); keyType.value = config.key_type || keyType.value; keyTypeLabel.value = config.key_type_label || keyTypeLabel.value; modelLabel.value = config.available_models?.[config.model]?.name || config.model || modelLabel.value } catch (e) { console.error('加载配置失败', e) } }
const loadQuota = async () => { try { const quota = await apiRequest('get', '/api/admin/ai-config/stats'); stats.value = quota || {} } catch (e) { console.error('加载配额失败', e) } }
const loadAdminStats = async () => { try { const res = await apiRequest('get', '/api/admin/ai-query/stats'); stats.value = { ...stats.value, standard_hits: res.standard_hits || 0, ai_generated: res.ai_generated || 0, today_count: res.today_count || stats.value?.today_count || 0, avg_time: res.avg_time || stats.value?.avg_time || 0 } } catch (e) { console.error('加载统计失败', e) } }

onMounted(() => {
  try { const saved = localStorage.getItem('ai-report-theme'); if (saved === 'dark') isDark.value = true } catch {}
  loadConfig(); loadQuota(); loadAdminStats()
})
</script>

<style scoped>
.ai-report-chat {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  z-index: 10;
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-card: #ffffff;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --sidebar-bg: #f1f5f9;
  --sidebar-border: #e2e8f0;
  --sidebar-text: #334155;
  --sidebar-text-muted: #64748b;
  --sidebar-hover: #e2e8f0;
  --sidebar-active: #dcfce7;
  --msg-user-bg: #3b82f6;
  --msg-user-text: #ffffff;
  --ai-avatar-bg: #dcfce7;
  --ai-avatar-color: #22c55e;
  --typing-bg: #22c55e;
  --accent: #22c55e;
  --accent-light: #f0fdf4;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --input-focus-border: #22c55e;
  --input-focus-shadow: rgba(34, 197, 94, 0.15);
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
  --suggestion-hover-bg: #f0fdf4;
  --suggestion-hover-border: #22c55e;
  --suggestion-hover-text: #166534;
  --collapse-header-color: #64748b;
  --scrollbar-thumb: #cbd5e1;
}

.ai-report-chat.dark {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
  --border-color: #334155;
  --sidebar-bg: #1e293b;
  --sidebar-border: #334155;
  --sidebar-text: #e2e8f0;
  --sidebar-text-muted: #94a3b8;
  --sidebar-hover: #334155;
  --sidebar-active: #1e3a2f;
  --ai-avatar-bg: #1e293b;
  --ai-avatar-color: #4ade80;
  --typing-bg: #4ade80;
  --accent: #22c55e;
  --accent-light: rgba(34, 197, 94, 0.08);
  --input-bg: #1e293b;
  --input-border: #334155;
  --input-focus-border: #22c55e;
  --input-focus-shadow: rgba(34, 197, 94, 0.15);
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
  --suggestion-hover-border: #4ade80;
  --suggestion-hover-text: #f1f5f9;
  --collapse-header-color: #94a3b8;
  --scrollbar-thumb: #475569;
}

.ai-report-chat { background: var(--bg-primary); }
.chat-main { background: var(--bg-primary); }

/* 左侧栏 */
.sidebar { width: 260px; background: var(--sidebar-bg); border-right: 1px solid var(--sidebar-border); display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.25s ease, background 0.3s ease; overflow: hidden; }
.sidebar.collapsed { width: 0; border: none; }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid var(--sidebar-border); height: 52px; flex-shrink: 0; }
.logo { display: flex; align-items: center; gap: 8px; color: var(--sidebar-text); }
.logo-text { font-size: 14px; font-weight: 600; }
.toggle-btn { color: var(--sidebar-text-muted); }
.toggle-btn:hover { color: var(--sidebar-text); }
.new-btn { margin: 10px 12px; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.conv-list { flex: 1; overflow-y: auto; padding: 4px 8px; }
.conv-list::-webkit-scrollbar { width: 4px; }
.conv-list::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 4px; }

.conv-item { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.15s; font-size: 13px; white-space: nowrap; overflow: hidden; color: var(--sidebar-text); }
.conv-item:hover { background: var(--sidebar-hover); }
.conv-item.active { background: var(--sidebar-active); }
.conv-icon { flex-shrink: 0; font-size: 16px; color: var(--sidebar-text-muted); }
.conv-item.active .conv-icon { color: var(--accent); }
.conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.empty-text { text-align: center; color: var(--sidebar-text-muted); font-size: 12px; padding: 20px 0; }

.stats-bar { padding: 10px 14px; border-top: 1px solid var(--sidebar-border); flex-shrink: 0; }
.stat-row { display: flex; justify-content: space-between; font-size: 12px; color: var(--sidebar-text-muted); padding: 2px 0; }
.stat-value { color: var(--sidebar-text); font-weight: 600; }

/* 右侧主区域 */
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 0 16px; height: 52px; border-bottom: 1px solid var(--border-color); flex-shrink: 0; transition: border-color 0.3s ease; }
.header-left { display: flex; align-items: center; gap: 12px; }
.menu-btn { color: var(--text-muted); }
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

.suggestion-item { padding: 12px 14px; background: var(--suggestion-bg); border: 1px solid var(--suggestion-border); border-radius: 10px; cursor: pointer; font-size: 13px; color: var(--text-secondary); transition: all 0.15s; text-align: center; }
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
.message-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.7; word-break: break-word; }
.message.user .message-text { background: var(--msg-user-bg); color: var(--msg-user-text); border-bottom-right-radius: 4px; }

/* AI 回复 */
.ai-response { display: flex; flex-direction: column; gap: 16px; }
.source-tag { display: flex; gap: 6px; }

/* 思考面板 */
.thinking-panel { border-radius: 12px; padding: 4px 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.thinking-panel :deep(.el-collapse-item__header) { color: var(--collapse-header-color); font-size: 13px; background: transparent; }
.thinking-panel :deep(.el-collapse-item__wrap) { background: transparent; border-color: var(--border-color); }
.thinking-panel :deep(.el-collapse-item__content) { padding-bottom: 14px; }
.thinking-list { margin: 0; padding-left: 18px; color: var(--text-secondary); line-height: 1.8; font-size: 13px; }
.thinking-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.thinking-reasoning { color: var(--text-secondary); font-size: 13px; line-height: 1.7; margin: 0; }

/* KPI 卡片 */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.kpi-card { background: var(--kpi-card-bg); border: 1px solid var(--kpi-card-border); border-radius: 10px; padding: 14px; transition: background 0.3s ease, border-color 0.3s ease; }
.kpi-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; transition: color 0.3s ease; }
.kpi-value { font-size: 22px; font-weight: 700; color: var(--text-primary); transition: color 0.3s ease; }
.kpi-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; transition: color 0.3s ease; }

/* 数据面板 */
.data-panel { border-radius: 12px; padding: 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.data-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; color: var(--text-primary); font-size: 13px; font-weight: 600; }
.data-actions { display: flex; gap: 4px; }
.report-table :deep(.el-table__header th) { background: var(--table-header-bg) !important; color: var(--table-header-color) !important; border-color: var(--table-border) !important; }
.report-table :deep(.el-table__body td) { color: var(--table-cell-color) !important; border-color: var(--table-border) !important; }
.report-table :deep(.el-table__row) { background: var(--table-row-bg) !important; }
.report-table :deep(.el-table__row--striped) { background: var(--table-row-striped) !important; }

/* SQL 面板 */
.sql-panel { border-radius: 12px; padding: 14px; background: var(--bg-card); border: 1px solid var(--border-color); transition: background 0.3s ease, border-color 0.3s ease; }
.sql-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: var(--text-primary); font-size: 13px; font-weight: 600; }
.sql-code { background: var(--sql-code-bg); color: var(--sql-code-color); padding: 14px; border-radius: 8px; overflow-x: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; margin: 0; transition: background 0.3s ease, color 0.3s ease; }

/* 生成说明 */
.explain-panel { border-radius: 12px; padding: 14px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-secondary); font-size: 13px; line-height: 1.7; transition: background 0.3s ease, border-color 0.3s ease, color 0.3s ease; }
.explain-panel p { margin: 0; }

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
.input-box { display: flex; align-items: flex-end; gap: 10px; max-width: 800px; margin: 0 auto; background: var(--input-bg); border: 1px solid var(--input-border); border-radius: 14px; padding: 8px 8px 8px 14px; transition: border-color 0.15s, background 0.3s ease; }
.input-box:focus-within { border-color: var(--input-focus-border); box-shadow: 0 0 0 3px var(--input-focus-shadow); }
.chat-input { flex: 1; }
.chat-input :deep(.el-textarea__inner) { background: transparent !important; border: none !important; box-shadow: none !important; padding: 4px 0 !important; font-size: 14px; color: var(--text-primary); resize: none; }
.chat-input :deep(.el-textarea__inner)::placeholder { color: var(--text-muted); }
.send-btn { flex-shrink: 0; }
.input-hint { text-align: center; font-size: 11px; color: var(--text-muted); margin-top: 6px; }

/* 响应式 */
@media (max-width: 768px) {
  .ai-report-chat { left: 0; }
  .sidebar { position: fixed; left: 0; top: 60px; bottom: 0; z-index: 100; width: 280px; }
  .sidebar.collapsed { width: 0; }
  .suggestion-grid { grid-template-columns: repeat(2, 1fr); }
  .message-content { max-width: 92%; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
