<template>
  <div class="ai-config-page">
    <el-card class="summary-card" shadow="sm">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><DataAnalysis /></el-icon>
            配置摘要
          </span>
          <div class="summary-header-actions">
            <el-tag v-if="configLoaded" type="success" effect="plain">已加载</el-tag>
            <el-tag v-else type="warning" effect="plain">未加载</el-tag>
            <el-tag :type="keyTypeTagType" effect="plain">{{ keyTypeLabel }}</el-tag>
          </div>
        </div>
      </template>

      <div class="summary-grid">
        <div v-for="item in summaryCards" :key="item.label" class="summary-item">
          <div class="summary-label">{{ item.label }}</div>
          <div class="summary-value">{{ item.value }}</div>
          <div class="summary-tip">{{ item.tip }}</div>
        </div>
      </div>

      <div class="summary-actions">
        <el-button type="primary" @click="goToLegacyConfig">打开完整配置中心</el-button>
        <el-button @click="goToAiRecords">问数记录</el-button>
        <el-button @click="goToStandardSql">标准 SQL 库</el-button>
        <el-button type="success" @click="handleTest">测试连接</el-button>
      </div>
    </el-card>

    <!-- 配置卡片 -->
    <el-row :gutter="20">
      <!-- API 配置 -->
      <el-col :span="16">
        <el-card class="config-card" shadow="sm">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon :size="18"><ChatDotRound /></el-icon>
                AI 模型配置
              </span>
              <el-tag type="success" v-if="configLoaded">已加载</el-tag>
              <el-tag type="warning" v-else>未加载</el-tag>
            </div>
          </template>

          <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px" size="default">
            <el-form-item label="API Key" prop="api_key">
              <el-input v-model="formData.api_key" type="password" show-password placeholder="请输入 DashScope API Key" clearable>
                <template #prefix>
                  <el-icon><Connection /></el-icon>
                </template>
              </el-input>
              <div class="form-tip">
                在
                <el-link type="primary" href="https://dashscope.console.aliyun.com/apiKey" target="_blank">DashScope 控制台</el-link>
                获取 API Key
              </div>
              <div class="key-meta">
                <el-tag :type="keyTypeTagType" size="small" effect="plain">{{ keyTypeLabel }}</el-tag>
                <span class="key-meta-text">推荐 Base URL：{{ recommendedBaseUrl }}</span>
              </div>
            </el-form-item>

            <el-form-item label="Base URL" prop="base_url">
              <el-input v-model="formData.base_url" placeholder="API 基础地址" />
              <div class="form-tip">
                {{ baseUrlTip }}
              </div>
            </el-form-item>

            <el-form-item label="模型" prop="model">
              <el-select v-model="formData.model" placeholder="选择 AI 模型" filterable class="full-width">
                <el-option
                  v-for="(model, key) in availableModels"
                  :key="key"
                  :label="model.name"
                  :value="key"
                >
                  <div class="model-option">
                    <span>{{ model.name }}</span>
                    <el-tag size="small" type="info">{{ key }}</el-tag>
                  </div>
                </el-option>
              </el-select>
              <div class="form-tip">
                当前模型：{{ currentModelName }}，{{ currentModelModes }}；{{ currentModelDescription }}
              </div>
            </el-form-item>

            <el-form-item label="模型模式" prop="model_mode">
              <el-radio-group v-model="formData.model_mode">
                <el-radio-button
                  v-for="mode in modelModeOptions"
                  :key="mode.value"
                  :label="mode.value"
                >
                  {{ mode.label }}
                </el-radio-button>
              </el-radio-group>
              <div class="form-tip">{{ currentModeTip }}</div>
            </el-form-item>

            <el-form-item label="每日配额" prop="daily_quota">
              <el-input-number v-model="formData.daily_quota" :min="1" :max="10000" :step="10" />
              <span class="form-tip">次/天</span>
            </el-form-item>

            <el-divider />

            <el-form-item label="敏感词" prop="sensitive_words">
              <el-input v-model="formData.sensitive_words" type="textarea" :rows="2" placeholder="用逗号分隔，例如：DROP, DELETE, TRUNCATE" />
              <div class="form-tip">
                包含这些词的 SQL 将被拦截
              </div>
            </el-form-item>

            <el-form-item label="敏感表" prop="sensitive_tables">
              <el-select v-model="formData.sensitive_tables" multiple placeholder="选择敏感表" filterable class="full-width">
                <el-option label="users (用户表)" value="users" />
                <el-option label="roles (角色表)" value="roles" />
                <el-option label="permissions (权限表)" value="permissions" />
                <el-option label="system_logs (系统日志)" value="system_logs" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmit" :loading="saving">
                <el-icon><VideoPlay /></el-icon>
                保存配置
              </el-button>
              <el-button @click="loadConfig">重置</el-button>
              <el-button type="success" @click="handleTest">
                <el-icon><Connection /></el-icon>
                测试连接
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 使用统计 -->
      <el-col :span="8">
        <el-card class="stats-card" shadow="sm">
          <template #header>
            <span class="card-title">
              <el-icon :size="18"><DataAnalysis /></el-icon>
              使用统计
            </span>
          </template>

          <div class="stats-content" v-if="stats">
            <div class="stat-item">
              <div class="stat-label">今日调用次数</div>
              <div class="stat-value">{{ stats.today_count || 0 }}</div>
              <el-progress :percentage="getPercentage(stats.today_count, stats.daily_quota)" :stroke-width="6" />
            </div>

            <div class="stat-item">
              <div class="stat-label">剩余配额</div>
              <div class="stat-value剩余">{{ stats.remaining || stats.daily_quota || 0 }}</div>
            </div>

            <div class="stat-item">
              <div class="stat-label">成功次数</div>
              <div class="stat-value success">{{ stats.success_count || 0 }}</div>
            </div>

            <div class="stat-item">
              <div class="stat-label">失败次数</div>
              <div class="stat-value danger">{{ stats.failed_count || 0 }}</div>
            </div>

            <div class="stat-item">
              <div class="stat-label">平均响应时间</div>
              <div class="stat-value">{{ stats.avg_time || 0 }}ms</div>
            </div>

            <div class="stat-item">
              <div class="stat-label">总 Token 消耗</div>
              <div class="stat-value">{{ stats.total_tokens || 0 }}</div>
            </div>
          </div>

          <el-empty v-else description="暂无统计数据" />
        </el-card>

        <el-card class="tips-card" shadow="sm" style="margin-top: 20px;">
          <template #header>
            <span class="card-title">
              <el-icon :size="18"><DataAnalysis /></el-icon>
              配置说明
            </span>
          </template>
          <div class="tips-content">
            <p>1. API Key 存储在 <code>backend/config/ai_config.json</code></p>
            <p>2. 修改配置后自动生效，无需重启</p>
            <p>3. 前端和后台共用同一套配置</p>
            <p>4. 旧版完整配置入口保留在 <code>/admin/ai-query</code></p>
            <p>5. 敏感词和敏感表用于安全拦截</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Prompt 模板配置 -->
    <el-card class="config-card" shadow="sm" style="margin-top: 20px;">
      <template #header>
        <span class="card-title">
          <el-icon :size="18"><Document /></el-icon>
          Prompt 模板配置
        </span>
      </template>

      <el-form :model="promptData" label-width="120px">
        <el-form-item label="系统 Prompt">
          <el-input v-model="promptData.system_prompt" type="textarea" :rows="6" placeholder="系统角色设定" />
        </el-form-item>

        <el-form-item label="用户 Prompt">
          <el-input v-model="promptData.user_prompt" type="textarea" :rows="3" placeholder="用户问题模板" />
          <div class="form-tip">
            使用 {'{question}'} 占位符
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="savePrompt" :loading="savingPrompt">保存模板</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, DataAnalysis, VideoPlay, Connection, Document } from '@element-plus/icons-vue'

const router = useRouter()
const configLoaded = ref(false)
const saving = ref(false)
const savingPrompt = ref(false)
const formRef = ref(null)
const stats = ref(null)
const tableSchemas = ref([])
const keyType = ref('unknown')
const keyTypeLabel = ref('未识别 / 未配置')

const formData = reactive({
  api_key: '',
  base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  model: 'qwen3.6-plus',
  model_mode: 'text',
  daily_quota: 100,
  sensitive_words: '',
  sensitive_tables: []
})

const promptData = reactive({
  system_prompt: '',
  user_prompt: ''
})

const availableModels = ref({})
const modelModeOptions = [
  { value: 'text', label: '文本生成', tip: '适合常规 SQL 问数与报表口径生成' },
  { value: 'deep', label: '深度思考', tip: '适合复杂指标、跨表分析和口径推导' },
  { value: 'vision', label: '视觉理解', tip: '适合图片、截图、图表解读与辅助问数' }
]

const detectKeyType = (apiKey) => {
  const key = (apiKey || '').trim()
  if (!key || key === 'sk-****') return 'unknown'
  if (key.startsWith('sk-sp-')) return 'coding_plan'
  if (key.startsWith('sk-')) return 'common'
  return 'unknown'
}

const getKeyTypeLabel = (type) => {
  const map = {
    coding_plan: 'Coding Plan 专属 Key',
    common: '通用百炼 Key',
    unknown: '未识别 / 未配置'
  }
  return map[type] || '未识别 / 未配置'
}

const getRecommendedBaseUrl = (type) => {
  return type === 'coding_plan'
    ? 'https://coding.dashscope.aliyuncs.com/v1'
    : 'https://dashscope.aliyuncs.com/compatible-mode/v1'
}

const recommendedBaseUrl = computed(() => getRecommendedBaseUrl(keyType.value))

const keyTypeTagType = computed(() => {
  if (keyType.value === 'coding_plan') return 'warning'
  if (keyType.value === 'common') return 'success'
  return 'info'
})

const baseUrlTip = computed(() => {
  if (keyType.value === 'coding_plan') {
    return '检测到 Coding Plan Key，建议使用 https://coding.dashscope.aliyuncs.com/v1'
  }
  if (keyType.value === 'common') {
    return '检测到通用百炼 Key，建议使用 https://dashscope.aliyuncs.com/compatible-mode/v1'
  }
  return '未识别到 Key 类型，保存后后端会自动按 Key 类型选择推荐地址'
})
const currentModeTip = computed(() => modelModeOptions.find((item) => item.value === formData.model_mode)?.tip || '')

const currentModelInfo = computed(() => availableModels.value[formData.model] || availableModels.value['qwen3.6-plus'] || {})
const currentModelName = computed(() => currentModelInfo.value.name || formData.model || '未选择')
const currentModelModes = computed(() => {
  const modes = currentModelInfo.value.modes || []
  const labels = modes.map((mode) => modelModeOptions.find((item) => item.value === mode)?.label || mode)
  return labels.length ? labels.join(' / ') : '暂无能力说明'
})
const currentModelDescription = computed(() => currentModelInfo.value.description || '暂无模型说明')
const modelModeLabel = computed(() => modelModeOptions.find((item) => item.value === (formData.model_mode || 'text'))?.label || '文本生成')
const sensitiveWordsCount = computed(() => {
  return (formData.sensitive_words || '')
    .split(/[,，\n]/)
    .map(item => item.trim())
    .filter(Boolean).length
})
const tableSummary = computed(() => {
  const total = tableSchemas.value.length
  const enabled = tableSchemas.value.filter(item => item.enabled !== false).length
  const layers = new Set(tableSchemas.value.map(item => item.layer || 'CUSTOM'))
  return { total, enabled, layers: layers.size }
})
const summaryCards = computed(() => [
  {
    label: 'Key 类型',
    value: keyTypeLabel.value,
    tip: `推荐地址：${recommendedBaseUrl.value}`
  },
  {
    label: '当前模型',
    value: currentModelName.value,
    tip: `${formData.model} · ${modelModeLabel.value}`
  },
  {
    label: '模型能力',
    value: currentModelModes.value,
    tip: currentModelDescription.value
  },
  {
    label: '表配置',
    value: `${tableSummary.value.enabled}/${tableSummary.value.total}`,
    tip: `${tableSummary.value.layers} 个层级已纳入配置`
  },
  {
    label: '使用配额',
    value: stats.value ? `${stats.value.today_count || 0}/${stats.value.daily_quota || formData.daily_quota}` : `${formData.daily_quota}`,
    tip: `剩余 ${stats.value?.remaining ?? formData.daily_quota} 次/天`
  },
  {
    label: '安全规则',
    value: `${sensitiveWordsCount.value} 词 / ${formData.sensitive_tables.length} 表`,
    tip: '敏感词与敏感表会拦截危险查询'
  }
])

const goToLegacyConfig = () => {
  router.push('/admin/ai-query')
}

const goToAiRecords = () => {
  router.push('/admin/ai-records')
}

const goToStandardSql = () => {
  router.push('/admin/standard-sql')
}

watch(
  () => formData.api_key,
  (value) => {
    const detectedType = detectKeyType(value)
    if (detectedType === 'unknown') return
    keyType.value = detectedType
    keyTypeLabel.value = getKeyTypeLabel(detectedType)
    if (!formData.base_url || formData.base_url.includes('/api/v1') || formData.base_url.includes('coding.dashscope')) {
      formData.base_url = getRecommendedBaseUrl(detectedType)
    }
  }
)

const formRules = {
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  model: [{ required: true, message: '请选择模型', trigger: 'change' }]
}

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

// 加载配置
const loadConfig = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/ai-config/config')
    formData.api_key = res.api_key || ''
    formData.base_url = res.base_url || 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    formData.model = res.model || 'qwen3.6-plus'
    formData.model_mode = res.model_mode || 'text'
    formData.daily_quota = res.daily_quota || 100
    formData.sensitive_words = res.sensitive_words || ''
    formData.sensitive_tables = res.sensitive_tables || []
    tableSchemas.value = res.table_schemas || []
    promptData.system_prompt = res.system_prompt || ''
    promptData.user_prompt = res.user_prompt || ''
    availableModels.value = res.available_models || {}
    keyType.value = res.key_type || detectKeyType(res.api_key)
    keyTypeLabel.value = res.key_type_label || getKeyTypeLabel(keyType.value)
    configLoaded.value = true
  } catch (error) {
    ElMessage.error('加载配置失败：' + error.message)
  }
}

// 加载统计
const loadStats = async () => {
  try {
    stats.value = await apiRequest('get', '/api/admin/ai-config/stats')
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 保存配置
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      saving.value = true
      const detectedType = detectKeyType(formData.api_key)
      if (detectedType !== 'unknown') {
        keyType.value = detectedType
        keyTypeLabel.value = getKeyTypeLabel(detectedType)
        const recommendedUrl = getRecommendedBaseUrl(detectedType)
        if (!formData.base_url || formData.base_url.includes('/api/v1') || formData.base_url.includes('coding.dashscope')) {
          formData.base_url = recommendedUrl
        }
      }
      // 构建完整的配置对象
      const configData = {
        api_key: formData.api_key,
        base_url: formData.base_url,
        model: formData.model,
        model_mode: formData.model_mode,
        daily_quota: formData.daily_quota,
        sensitive_words: formData.sensitive_words,
        sensitive_tables: formData.sensitive_tables
      }
      await apiRequest('post', '/api/admin/ai-config/api', {
        body: JSON.stringify(configData)
      })
      ElMessage.success('配置保存成功')
      loadConfig()  // 重新加载配置
      loadStats()
    } catch (error) {
      ElMessage.error('保存失败：' + error.message)
    } finally {
      saving.value = false
    }
  })
}

// 保存 Prompt
const savePrompt = async () => {
  try {
    savingPrompt.value = true
    await apiRequest('post', '/api/admin/ai-config/prompt', {
      body: JSON.stringify(promptData)
    })
    ElMessage.success('Prompt 模板保存成功')
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  } finally {
    savingPrompt.value = false
  }
}

// 测试连接
const handleTest = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/ai-config/test')
    keyType.value = res.key_type || keyType.value
    keyTypeLabel.value = res.key_type_label || keyTypeLabel.value
    if (res.base_url_suggested && (!formData.base_url || formData.base_url.includes('/api/v1'))) {
      formData.base_url = res.base_url_suggested
    }
    const statusMap = {
      success: '成功',
      warning: '警告',
      error: '失败'
    }
    const icon = statusMap[res.status] || '失败'
    ElMessage.success(`${icon}：${res.message || '测试完成'}`)
  } catch (error) {
    ElMessage.error('连接测试失败：' + error.message)
  }
}

const getPercentage = (value, total) => {
  if (!total) return 0
  return Math.min(100, Math.round((value / total) * 100))
}

onMounted(() => {
  loadConfig()
  loadStats()
})
</script>

<style scoped>
.ai-config-page {
  padding: var(--spacing-6);
}

.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.full-width {
  width: 100%;
}

.form-tip {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.key-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.key-meta-text {
  font-size: 12px;
  color: #475569;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.summary-item {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  min-height: 96px;
}

.summary-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.4;
}

.summary-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
}

.summary-actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.form-tip code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.stat-value.success { color: #10b981; }
.stat-value.danger { color: #ef4444; }
.stat-value.剩余 { color: #3b82f6; }

.tips-content p {
  font-size: 13px;
  color: #475569;
  line-height: 1.8;
  margin: 8px 0;
}

.tips-content code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}
</style>
