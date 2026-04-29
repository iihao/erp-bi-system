<template>
  <div class="ai-config-page">
    <el-tabs v-model="activeTab" class="config-tabs">
      <!-- API 配置 -->
      <el-tab-pane label="API 配置" name="api">
        <el-card class="config-card">
          <el-form ref="formRef" :model="config" label-width="140px">
            <el-form-item label="API Key" required>
              <el-input
                v-model="config.apiKey"
                :type="showApiKey ? 'text' : 'password'"
                placeholder="请输入 DASHSCOPE_API_KEY"
                :show-password="true"
                clearable
              >
                <template #prefix>
                  <svg v-if="config.apiKey" style="width: 16px; height: 16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <circle cx="12" cy="16" r="1"/>
                    <path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                </template>
              </el-input>
              <div class="form-tip">
                <svg style="width: 14px; height: 14px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
                百炼 API 密钥，用于访问 AI 模型服务，保存后以密文存储
              </div>
            </el-form-item>

            <el-form-item label="API 地址" required>
              <el-input
                v-model="config.baseUrl"
                placeholder="https://dashscope.aliyuncs.com/api/v1"
                clearable
              />
            </el-form-item>

            <el-form-item label="模型选择" required>
              <el-select v-model="config.model" placeholder="请选择 AI 模型" style="width: 100%">
                <el-option
                  v-for="(meta, key) in availableModels"
                  :key="key"
                  :label="`${meta.name}${key === 'qwen3.6-plus' ? '（推荐）' : ''}`"
                  :value="key"
                />
              </el-select>
              <div class="form-tip">
                推荐使用 qwen3.6-plus，支持文本生成、深度思考和视觉理解，适合地产问数与图表解读
              </div>
            </el-form-item>

            <el-form-item label="模型模式">
              <el-radio-group v-model="config.modelMode">
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

            <el-form-item label="能力说明">
              <div class="capability-grid">
                <div
                  v-for="cap in currentModelCapabilities"
                  :key="cap.title"
                  class="capability-card"
                >
                  <div class="capability-title">{{ cap.title }}</div>
                  <div class="capability-desc">{{ cap.description }}</div>
                </div>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig" :loading="saving">
                <svg v-if="!saving" style="width: 16px; height: 16px; margin-right: 6px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
                  <polyline points="17,21 17,13 7,13 7,21"/>
                  <polyline points="7,3 7,8 15,8"/>
                </svg>
                保存配置
              </el-button>
              <el-button @click="handleTestConnection" :loading="testing">
                <svg v-if="!testing" style="width: 16px; height: 16px; margin-right: 6px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
                </svg>
                {{ testing ? '测试中...' : '测试连接' }}
              </el-button>
              <el-tag v-if="config.apiKey && !showApiKey" type="success" size="small" style="margin-left: 12px;">
                <svg style="width: 14px; height: 14px; margin-right: 4px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                已配置
              </el-tag>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Prompt 模板 -->
      <el-tab-pane label="Prompt 模板" name="prompt">
        <el-card class="config-card">
          <el-form ref="promptFormRef" :model="promptConfig" label-width="140px">
            <el-form-item label="系统提示词" required>
              <el-input
                v-model="promptConfig.systemPrompt"
                type="textarea"
                :rows="8"
                placeholder="系统提示词模板"
              />
              <div class="form-tip">定义 AI 助手的角色和行为准则</div>
            </el-form-item>

            <el-form-item label="用户提示词" required>
              <el-input
                v-model="promptConfig.userPrompt"
                type="textarea"
                :rows="4"
                placeholder="用户提示词模板"
              />
              <div class="form-tip">
                可用变量：{'{question}'} - 用户问题，{'{schema}'} - 表结构
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSavePrompt" :loading="saving">
                保存模板
              </el-button>
              <el-button @click="handleResetPrompt">重置默认</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 表结构映射 -->
      <el-tab-pane label="表结构映射" name="schema">
        <el-card class="config-card">
          <div class="table-header">
            <div class="table-title-group">
              <span>地产数据表配置</span>
              <el-tag type="success" effect="plain">{{ tableSummary.total }} 张表</el-tag>
              <el-tag type="info" effect="plain">{{ tableSummary.enabled }} 张启用</el-tag>
            </div>
            <div class="table-actions">
              <el-input
                v-model="schemaKeyword"
                placeholder="搜索表名/别名/描述"
                clearable
                style="width: 240px; margin-right: 12px;"
              />
              <el-button @click="handleResetEstateTables">恢复默认地产表</el-button>
              <el-button type="primary" size="small" @click="handleAddTable">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19" stroke-linecap="round"/>
                <line x1="5" y1="12" x2="19" y2="12" stroke-linecap="round"/>
              </svg>
              添加表
              </el-button>
            </div>
          </div>

          <el-table :data="filteredTableSchemas" border stripe class="schema-table">
            <el-table-column prop="table_name" label="表名" width="170" />
            <el-table-column prop="table_alias" label="中文名称" width="150" />
            <el-table-column prop="layer" label="层级" width="90" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="90" />
            <el-table-column label="字段配置" min-width="300">
              <template #default="{ row }">
                <el-tag
                  v-for="field in row.fields"
                  :key="field.name"
                  size="small"
                  class="field-tag"
                >
                  {{ field.name }}({{ field.type }})
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="描述" min-width="200" prop="description" show-overflow-tooltip />
            <el-table-column label="示例问题" min-width="220" prop="sample_question" show-overflow-tooltip />
            <el-table-column label="操作" width="150" fixed="right" class-name="action-column">
              <template #default="{ row, $index }">
                <el-button size="small" @click="handleEditTable(row, $index)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDeleteTable(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 权限配置 -->
      <el-tab-pane label="权限配置" name="permission">
        <el-card class="config-card">
          <el-form :model="permissionConfig" label-width="140px">
            <el-form-item label="查询类型限制">
              <el-checkbox-group v-model="permissionConfig.allowedTypes">
                <el-checkbox label="SELECT">SELECT (查询)</el-checkbox>
                <el-checkbox label="INSERT" disabled>INSERT (插入)</el-checkbox>
                <el-checkbox label="UPDATE" disabled>UPDATE (更新)</el-checkbox>
                <el-checkbox label="DELETE" disabled>DELETE (删除)</el-checkbox>
              </el-checkbox-group>
              <div class="form-tip">为保障安全，AI 问数仅允许 SELECT 查询</div>
            </el-form-item>

            <el-form-item label="每日查询配额">
              <el-input-number v-model="permissionConfig.dailyQuota" :min="10" :max="1000" :step="10" />
              <span class="quota-unit">次/用户/天</span>
            </el-form-item>

            <el-form-item label="敏感词过滤">
              <el-input
                v-model="permissionConfig.sensitiveWords"
                type="textarea"
                :rows="3"
                placeholder="请输入敏感词，用逗号分隔"
              />
              <div class="form-tip">包含敏感词的查询将被拒绝</div>
            </el-form-item>

            <el-form-item label="敏感表过滤">
              <el-select
                v-model="permissionConfig.sensitiveTables"
                multiple
                placeholder="请选择敏感表"
                style="width: 100%"
              >
                <el-option label="users (用户表)" value="users" />
                <el-option label="roles (角色表)" value="roles" />
                <el-option label="permissions (权限表)" value="permissions" />
                <el-option label="system_logs (系统日志)" value="system_logs" />
              </el-select>
              <div class="form-tip">AI 无法访问被标记为敏感的表</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSavePermission" :loading="saving">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 用户权限管理 -->
      <el-tab-pane label="用户权限" name="users">
        <el-card class="config-card">
          <el-table :data="userPermissions" border stripe>
            <el-table-column prop="user_id" label="用户 ID" width="80" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="role" label="角色" width="100" />
            <el-table-column label="AI 权限" width="100">
              <template #default="{ row }">
                <el-tag :type="row.ai_enabled ? 'success' : 'danger'">
                  {{ row.ai_enabled ? '已启用' : '已禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="quota" label="每日配额" width="100" />
            <el-table-column prop="used_today" label="今日已用" width="100" />
            <el-table-column label="操作" width="200" fixed="right" class-name="action-column">
              <template #default="{ row }">
                <el-button
                  size="small"
                  :type="row.ai_enabled ? 'warning' : 'success'"
                  @click="handleToggleUserAI(row)"
                >
                  {{ row.ai_enabled ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" @click="handleEditUserQuota(row)">配额</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="tableDialogVisible" :title="tableDialogMode === 'add' ? '新增表配置' : '编辑表配置'" width="760px">
      <el-form :model="tableForm" label-width="110px">
        <el-form-item label="表名">
          <el-input v-model="tableForm.table_name" placeholder="如 re_projects" />
        </el-form-item>
        <el-form-item label="中文名称">
          <el-input v-model="tableForm.table_alias" placeholder="如 项目表" />
        </el-form-item>
        <el-form-item label="层级">
          <el-select v-model="tableForm.layer" style="width: 100%">
            <el-option label="RE" value="RE" />
            <el-option label="ODS" value="ODS" />
            <el-option label="DWD" value="DWD" />
            <el-option label="DWS" value="DWS" />
            <el-option label="DIM" value="DIM" />
            <el-option label="ADS" value="ADS" />
            <el-option label="CUSTOM" value="CUSTOM" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="tableForm.priority" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="tableForm.enabled" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="tableForm.description" type="textarea" :rows="2" placeholder="表用途说明" />
        </el-form-item>
        <el-form-item label="示例问题">
          <el-input v-model="tableForm.sample_question" type="textarea" :rows="2" placeholder="如：查询上个月项目去化率最高的项目" />
        </el-form-item>
        <el-form-item label="字段 JSON">
          <el-input
            v-model="tableForm.fieldsText"
            type="textarea"
            :rows="8"
            placeholder='[{"name":"project_id","type":"INT"}]'
          />
          <div class="form-tip">支持 JSON 数组，字段会按原样保存到配置文件中</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tableDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTableSchema">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('api')
const saving = ref(false)
const testing = ref(false)
const showApiKey = ref(false)
const schemaKeyword = ref('')
const tableDialogVisible = ref(false)
const tableDialogMode = ref('add')
const editingTableIndex = ref(-1)

const config = reactive({
  apiKey: '',
  baseUrl: 'https://dashscope.aliyuncs.com/api/v1',
  model: 'qwen3.6-plus',
  modelMode: 'text'
})

const availableModels = ref({
  'qwen3.6-plus': {
    name: 'Qwen3.6 Plus',
    modes: ['text', 'deep', 'vision'],
    input: ['text', 'image'],
    context: 1000000
  },
  'qwen3.5-plus': {
    name: 'Qwen3.5 Plus',
    modes: ['text', 'vision'],
    input: ['text', 'image'],
    context: 1000000
  },
  'qwen3-max-2026-01-23': {
    name: 'Qwen3 Max 2026-01-23',
    modes: ['text', 'deep'],
    input: ['text'],
    context: 262144
  }
})

const modelModeOptions = [
  { value: 'text', label: '文本生成', tip: '适合常规 SQL 问数与报表口径生成' },
  { value: 'deep', label: '深度思考', tip: '适合复杂指标、跨表分析和口径推导' },
  { value: 'vision', label: '视觉理解', tip: '适合图片、截图、图表解读与辅助问数' }
]

const promptConfig = reactive({
  systemPrompt: `你是一个专业的 SQL 生成助手。根据数据库表结构，将用户的自然语言问题转换为 SQL 查询。

要求：
1. 只输出 SQL 语句，不要解释
2. 使用 SQLite 兼容语法
3. 如果问题不明确，生成最合理的查询
4. 限制结果数量（使用 LIMIT）
5. 只允许 SELECT 查询`,

  userPrompt: `请将以下问题转换为 SQL 查询：{question}`
})

const tableSchemas = ref([])

const permissionConfig = reactive({
  allowedTypes: ['SELECT'],
  dailyQuota: 100,
  sensitiveWords: 'DROP, DELETE, TRUNCATE, GRANT, REVOKE',
  sensitiveTables: ['users', 'roles', 'permissions', 'system_logs']
})

const userPermissions = ref([
  { user_id: 1, username: 'admin', role: '管理员', ai_enabled: true, quota: 100, used_today: 15 },
  { user_id: 2, username: 'user1', role: '普通用户', ai_enabled: true, quota: 50, used_today: 23 },
  { user_id: 3, username: 'user2', role: '普通用户', ai_enabled: false, quota: 50, used_today: 0 }
])

const tableSummary = computed(() => {
  const total = tableSchemas.value.length
  const enabled = tableSchemas.value.filter(item => item.enabled !== false).length
  const layers = [...new Set(tableSchemas.value.map(item => item.layer || 'CUSTOM'))]
  return { total, enabled, layers: layers.length }
})

const filteredTableSchemas = computed(() => {
  const keyword = schemaKeyword.value.trim().toLowerCase()
  if (!keyword) return tableSchemas.value
  return tableSchemas.value.filter(item => {
    const fields = Array.isArray(item.fields) ? item.fields : []
    return [
      item.table_name,
      item.table_alias,
      item.description,
      item.layer,
      item.sample_question,
      fields.map(field => field.name).join(' ')
    ].join(' ').toLowerCase().includes(keyword)
  })
})

const currentModelCapabilities = computed(() => {
  const model = availableModels.value[config.model] || {}
  const caps = []
  if ((model.modes || []).includes('text')) {
    caps.push({ title: '文本生成', description: '自然语言转 SQL、口径说明、报表模板生成' })
  }
  if ((model.modes || []).includes('deep')) {
    caps.push({ title: '深度思考', description: '复杂指标推导、跨表关联、口径校验' })
  }
  if ((model.modes || []).includes('vision')) {
    caps.push({ title: '视觉理解', description: '图表、截图、报表图片的辅助解析' })
  }
  return caps
})

const currentModeTip = computed(() => {
  return modelModeOptions.find(item => item.value === config.modelMode)?.tip || ''
})

const tableForm = reactive({
  table_name: '',
  table_alias: '',
  description: '',
  layer: 'RE',
  enabled: true,
  priority: 100,
  sample_question: '',
  fieldsText: '[]'
})

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
    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || '请求失败')
    }

    return result
  } catch (error) {
    throw error
  }
}

const handleSaveConfig = async () => {
  if (!config.apiKey || !config.apiKey.trim()) {
    ElMessage.warning('请输入 API Key')
    return
  }
  saving.value = true
  try {
    await apiRequest('POST', '/api/admin/ai-config/api', {
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      model: config.model,
      modelMode: config.modelMode,
      available_models: availableModels.value
    })
    ElMessage.success('API 配置保存成功！')
    // 保存成功后，显示截断的 Key
    const maskedKey = config.apiKey.includes('****')
      ? config.apiKey
      : config.apiKey.substring(0, 8) + '****'
    config.apiKey = maskedKey
    showApiKey.value = true
  } catch (error) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleTestConnection = async () => {
  // 检查是否是密文显示
  const isMasked = config.apiKey && config.apiKey.includes('****')
  
  if (!config.apiKey || !config.apiKey.trim()) {
    ElMessage.warning('请先输入或保存 API Key')
    return
  }
  
  // 如果是密文，提示用户后端会使用保存的 Key 测试
  if (isMasked) {
    ElMessage.info({
      message: '使用已保存的 API Key 进行测试...',
      duration: 2000
    })
  }
  
  testing.value = true
  try {
    const res = await apiRequest('GET', '/api/admin/ai-config/test')
    if (res.status === 'success') {
      ElMessage.success({
        message: `API 连接正常！模型：${res.model || 'qwen3.6-plus'} / 模式：${res.model_mode || config.modelMode}`,
        duration: 3000
      })
    } else {
      ElMessage.warning({
        message: '警告：' + (res.message || 'API 连接异常'),
        duration: 3000
      })
    }
  } catch (error) {
    ElMessage.error({
      message: '连接测试失败：' + (error.message || '无法连接到 API 服务'),
      duration: 3000
    })
  } finally {
    testing.value = false
  }
}

const handleSavePrompt = async () => {
  saving.value = true
  try {
    await apiRequest('POST', '/api/admin/ai-config/prompt', {
      system_prompt: promptConfig.systemPrompt,
      user_prompt: promptConfig.userPrompt
    })
    ElMessage.success('Prompt 模板保存成功')
  } catch (error) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleResetPrompt = () => {
  promptConfig.systemPrompt = `你是一个专业的 SQL 生成助手。根据数据库表结构，将用户的自然语言问题转换为 SQL 查询。

要求：
1. 只输出 SQL 语句，不要解释
2. 使用 SQLite 兼容语法
3. 如果问题不明确，生成最合理的查询
4. 限制结果数量（使用 LIMIT）
5. 只允许 SELECT 查询`
  promptConfig.userPrompt = `请将以下问题转换为 SQL 查询：{question}`
  ElMessage.success('已重置为默认模板')
}

const openTableDialog = (row = null, index = -1) => {
  tableDialogMode.value = row ? 'edit' : 'add'
  editingTableIndex.value = index
  tableForm.table_name = row?.table_name || ''
  tableForm.table_alias = row?.table_alias || ''
  tableForm.description = row?.description || ''
  tableForm.layer = row?.layer || 'RE'
  tableForm.enabled = row?.enabled !== false
  tableForm.priority = row?.priority ?? 100
  tableForm.sample_question = row?.sample_question || ''
  tableForm.fieldsText = JSON.stringify(row?.fields || [], null, 2)
  tableDialogVisible.value = true
}

const handleAddTable = () => {
  openTableDialog()
}

const handleEditTable = (row, index) => {
  openTableDialog(row, index)
}

const handleDeleteTable = (row) => {
  ElMessageBox.confirm(`确定要删除表 ${row.table_name} 的配置吗？`, '警告', {
    type: 'warning'
  }).then(() => {
    return apiRequest('DELETE', `/api/admin/ai-config/schema/${row.table_name}`)
  }).then(async () => {
    await loadConfig()
    ElMessage.success('删除成功')
  }).catch(() => {})
}

const handleSaveTableSchema = async () => {
  if (!tableForm.table_name.trim()) {
    ElMessage.warning('请输入表名')
    return
  }

  let fields = []
  try {
    fields = JSON.parse(tableForm.fieldsText || '[]')
    if (!Array.isArray(fields)) {
      throw new Error('字段必须是数组')
    }
  } catch (error) {
    ElMessage.error('字段 JSON 格式错误：' + (error.message || '无法解析'))
    return
  }

  saving.value = true
  try {
    await apiRequest('POST', '/api/admin/ai-config/schema', {
      table_name: tableForm.table_name.trim(),
      table_alias: tableForm.table_alias.trim(),
      description: tableForm.description.trim(),
      layer: tableForm.layer,
      enabled: tableForm.enabled,
      priority: tableForm.priority,
      sample_question: tableForm.sample_question.trim(),
      fields
    })
    await loadConfig()
    tableDialogVisible.value = false
    ElMessage.success('表配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleResetEstateTables = async () => {
  try {
    await ElMessageBox.confirm('确定恢复默认地产表配置吗？当前修改将被覆盖。', '提示', { type: 'warning' })
    await loadConfig()
    ElMessage.success('已恢复默认地产表配置')
  } catch {
    // 取消
  }
}

const handleSavePermission = async () => {
  saving.value = true
  try {
    await apiRequest('POST', '/api/admin/ai-config/permission', {
      allowed_types: permissionConfig.allowedTypes,
      daily_quota: permissionConfig.dailyQuota,
      sensitive_words: permissionConfig.sensitiveWords,
      sensitive_tables: permissionConfig.sensitiveTables
    })
    ElMessage.success('权限配置保存成功')
  } catch (error) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const handleToggleUserAI = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.ai_enabled ? '禁用' : '启用'}该用户的 AI 问数权限吗？`,
      '提示',
      { type: 'info' }
    )
    row.ai_enabled = !row.ai_enabled
    ElMessage.success('权限更新成功')
  } catch (error) {
    // 取消
  }
}

const handleEditUserQuota = (row) => {
  ElMessageBox.prompt('设置每日配额', '编辑配额', {
    inputValue: row.quota.toString(),
    inputPattern: /^\d+$/,
    inputErrorMessage: '请输入有效数字'
  }).then(({ value }) => {
    row.quota = parseInt(value)
    ElMessage.success('配额更新成功')
  }).catch(() => {})
}

// 加载配置
const loadConfig = async () => {
  try {
    const res = await apiRequest('GET', '/api/admin/ai-config/current')
    config.apiKey = res.api_key_configured ? 'sk-****' : ''
    showApiKey.value = Boolean(res.api_key_configured)
    config.baseUrl = res.base_url || config.baseUrl
    config.model = res.model || config.model
    config.modelMode = res.model_mode || config.modelMode
    availableModels.value = res.available_models || availableModels.value
    
    if (res.system_prompt) {
      promptConfig.systemPrompt = res.system_prompt
    }
    if (res.user_prompt) {
      promptConfig.userPrompt = res.user_prompt
    }
    if (res.daily_quota) {
      permissionConfig.dailyQuota = res.daily_quota
    }
    if (res.sensitive_words) {
      permissionConfig.sensitiveWords = res.sensitive_words
    }
    if (res.sensitive_tables) {
      permissionConfig.sensitiveTables = res.sensitive_tables
    }
    tableSchemas.value = res.table_schemas && res.table_schemas.length > 0 ? res.table_schemas : tableSchemas.value
    console.log('配置加载成功:', {
      api_key: res.api_key ? '已配置 (' + res.api_key.substring(0, 8) + '****)' : '未配置',
      base_url: config.baseUrl,
      model: config.model,
      model_mode: config.modelMode
    })
  } catch (error) {
    console.error('加载配置失败', error)
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.ai-config-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.config-tabs {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.config-card {
  border: none;
  box-shadow: none;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.table-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.table-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.table-header span {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  width: 100%;
}

.capability-card {
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 14px 16px;
}

.capability-title {
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 6px;
}

.capability-desc {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.btn-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
  color: currentColor;
  stroke: currentColor;
  fill: none;
}

.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  line-height: 1.5;
}

.quota-unit {
  margin-left: 12px;
  color: #64748b;
  font-size: 13px;
}

.schema-table {
  margin-top: 16px;
}

.field-tag {
  margin-right: 6px;
  margin-bottom: 4px;
  background-color: #f1f5f9;
  color: #475569;
  border-color: #e2e8f0;
}

.model-capability-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
}
</style>
