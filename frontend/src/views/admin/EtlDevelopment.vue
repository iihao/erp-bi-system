<template>
  <div class="etl-development-page">
    <el-container class="dev-container">
      <!-- 左侧：表结构浏览 -->
      <el-aside width="300px" class="dev-aside">
        <el-card class="table-tree-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon :size="18"><DataAnalysis /></el-icon>
                数据表浏览
              </span>
              <el-button size="small" type="primary" @click="loadTables">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <el-input
            v-model="tableSearch"
            placeholder="搜索表名..."
            clearable
            size="small"
            class="mb-2"
          />

          <el-tree
            :data="tableTree"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            :filter-node-method="filterTable"
            @node-click="handleTableClick"
            default-expand-all
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.type === 'table'" class="node-icon"><Grid /></el-icon>
                <el-icon v-else class="node-icon"><Folder /></el-icon>
                <span :class="['node-label', data.type]">{{ node.label }}</span>
                <span v-if="data.type === 'table'" class="node-meta">{{ data.columns?.length || 0 }} 列</span>
              </span>
            </template>
          </el-tree>
        </el-card>

        <!-- 表结构详情 -->
        <el-card v-if="currentTable" class="table-detail-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon :size="18"><Files /></el-icon>
                {{ currentTable.name }}
              </span>
              <el-button size="small" @click="insertTableName">
                插入表名
              </el-button>
            </div>
          </template>

          <el-table :data="currentTable.columns" size="small" stripe>
            <el-table-column prop="name" label="列名" min-width="100" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-aside>

      <!-- 右侧：SQL 编辑器 -->
      <el-main class="dev-main">
        <el-card class="editor-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon :size="18"><Monitor /></el-icon>
                SQL 编辑器
              </span>
              <div class="header-actions">
                <el-select v-model="selectedDatabase" placeholder="选择数据库" size="default" style="width: 150px">
                  <el-option label="erp_production" value="erp_production" />
                  <el-option label="erp_ods" value="erp_ods" />
                  <el-option label="erp_dwd" value="erp_dwd" />
                  <el-option label="erp_dws" value="erp_dws" />
                  <el-option label="erp_ads" value="erp_ads" />
                </el-select>
                <el-button type="primary" @click="runQuery" :loading="running">
                  <el-icon><VideoPlay /></el-icon>
                  运行 (Ctrl+Enter)
                </el-button>
                <el-button type="success" @click="saveQuery">
                  <el-icon><Document /></el-icon>
                  保存
                </el-button>
                <el-button @click="clearEditor">清空</el-button>
              </div>
            </div>
          </template>

          <!-- SQL 编辑器 -->
          <div class="sql-editor-wrapper">
            <textarea
              ref="editorRef"
              v-model="sqlQuery"
              class="sql-editor"
              placeholder="-- 在此输入 SQL 查询&#10;SELECT * FROM table_name LIMIT 100;"
              spellcheck="false"
              @keydown.ctrl.enter.prevent="runQuery"
            ></textarea>
          </div>

          <!-- 查询结果 -->
          <div v-if="queryResult" class="query-result">
            <div class="result-header">
              <span class="card-title">
                <el-icon :size="16"><DataAnalysis /></el-icon>
                查询结果
              </span>
              <span class="result-info">
                <el-tag size="small" type="success">执行成功</el-tag>
                <span>{{ queryResult.rows?.length || 0 }} 行 · {{ queryResult.execution_time || 0 }}ms</span>
              </span>
              <div class="result-actions">
                <el-button size="small" @click="exportResult">
                  <el-icon><Download /></el-icon>
                  导出 CSV
                </el-button>
              </div>
            </div>
            <el-table
              :data="queryResult.rows"
              max-height="400"
              size="small"
              stripe
              border
            >
              <el-table-column
                v-for="col in queryResult.columns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
                show-overflow-tooltip
              />
            </el-table>
          </div>

          <!-- 错误信息 -->
          <el-alert
            v-if="queryError"
            :title="queryError"
            type="error"
            :closable="false"
            class="mt-4"
          />
        </el-card>

        <!-- 保存的查询列表 -->
        <el-card class="saved-queries-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon :size="18"><Folder /></el-icon>
                保存的查询
              </span>
              <el-button size="small" type="primary" @click="showSaveDialog = true">
                <el-icon><Plus /></el-icon>
                新建查询
              </el-button>
            </div>
          </template>

          <el-table :data="savedQueries" stripe @row-click="loadSavedQuery">
            <el-table-column prop="name" label="名称" min-width="150" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="updated_at" label="更新时间" width="160" />
            <el-table-column label="操作" width="120" fixed="right" class-name="action-column">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click.stop="deleteSavedQuery(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>

    <!-- 保存查询对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存查询"
      width="500px"
    >
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="查询名称" required>
          <el-input v-model="saveForm.name" placeholder="请输入查询名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入查询描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveQuery">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, VideoPlay, Document, Download, Plus, Grid, DataAnalysis, Monitor, Folder, Files, Connection } from '@element-plus/icons-vue'

const tableSearch = ref('')
const sqlQuery = ref('-- 在此输入 SQL 查询\nSELECT * FROM ')
const selectedDatabase = ref('erp_production')
const running = ref(false)
const queryResult = ref(null)
const queryError = ref(null)
const showSaveDialog = ref(false)
const editorRef = ref(null)

const tableTree = ref([])
const currentTable = ref(null)
const savedQueries = ref([])

const saveForm = reactive({
  name: '',
  description: ''
})

// API 请求封装
const apiRequest = async (method, url, options = {}) => {
  const token = localStorage.getItem('token')
  const params = options.params || {}
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value)
    }
  })
  const config = {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...options
  }
  delete config.params

  const requestUrl = query.toString() ? `${url}?${query.toString()}` : url

  try {
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

// 监听搜索
watch(tableSearch, (val) => {
  // 树过滤逻辑在模板中处理
})

const filterTable = (value, data) => {
  if (!value) return true
  return data.name && data.name.toLowerCase().includes(value.toLowerCase())
}

// 加载表结构
const loadTables = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/etl/dev/tables')
    const tableNames = res.tables || []
    const children = []

    for (const name of tableNames) {
      try {
        const schema = await apiRequest('get', `/api/admin/etl/dev/tables/${encodeURIComponent(name)}/schema`)
        children.push({
          id: name,
          name,
          type: 'table',
          columns: schema.columns || []
        })
      } catch (schemaError) {
        children.push({
          id: name,
          name,
          type: 'table',
          columns: []
        })
      }
    }

    tableTree.value = [
      {
        id: 'tables-root',
        name: '数据库表',
        type: 'schema',
        children
      }
    ]
  } catch (error) {
    console.error('加载表结构失败', error)
    tableTree.value = []
  }
}

// 处理表点击
const handleTableClick = (data) => {
  if (data.type === 'table') {
    currentTable.value = data
  }
}

// 插入表名到编辑器
const insertTableName = () => {
  if (currentTable.value) {
    sqlQuery.value += currentTable.value.name + ' '
  }
}

// 运行查询
const runQuery = async () => {
  if (!sqlQuery.value.trim()) {
    ElMessage.warning('请输入 SQL 查询')
    return
  }

  running.value = true
  queryError.value = null
  queryResult.value = null

  try {
    const startTime = Date.now()
    const res = await apiRequest('post', '/api/admin/etl/dev/sql/execute', {
      body: JSON.stringify({
        sql: sqlQuery.value,
        limit: 200
      })
    })

    queryResult.value = {
      columns: res.columns || [],
      rows: res.data || [],
      execution_time: Math.round((res.execute_time || ((Date.now() - startTime) / 1000)) * 1000)
    }

    ElMessage.success('查询执行成功')
  } catch (error) {
    queryError.value = error.message || '查询执行失败'
    ElMessage.error(queryError.value)
  } finally {
    running.value = false
  }
}

// 清空编辑器
const clearEditor = () => {
  sqlQuery.value = ''
  queryResult.value = null
  queryError.value = null
}

// 保存查询
const confirmSaveQuery = async () => {
  if (!saveForm.name.trim()) {
    ElMessage.warning('请输入查询名称')
    return
  }

  try {
    await apiRequest('post', '/api/admin/etl/dev/scripts', {
      body: JSON.stringify({
        script_name: saveForm.name,
        description: saveForm.description,
        script_type: 'sql',
        content: sqlQuery.value
      })
    })

    ElMessage.success('查询保存成功')
    showSaveDialog.value = false
    saveForm.name = ''
    saveForm.description = ''
    loadSavedQueries()
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 加载保存的查询
const loadSavedQueries = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/etl/dev/scripts')
    savedQueries.value = (res.items || []).map(item => ({
      id: item.script_id,
      name: item.script_name,
      description: item.description,
      sql: item.content,
      updated_at: item.updated_at || item.created_at
    }))
  } catch (error) {
    console.error('加载保存的查询失败', error)
  }
}

// 加载保存的查询到编辑器
const loadSavedQuery = (row) => {
  sqlQuery.value = row.sql
  ElMessage.success('查询已加载到编辑器')
}

// 删除保存的查询
const deleteSavedQuery = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除查询"${row.name}"吗？`, '提示', { type: 'warning' })
    await apiRequest('delete', `/api/admin/etl/dev/scripts/${row.id}`)
    ElMessage.success('删除成功')
    loadSavedQueries()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

// 导出结果
const exportResult = () => {
  if (!queryResult.value || !queryResult.value.rows) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  const rows = queryResult.value.rows
  const columns = queryResult.value.columns
  const csv = [
    columns.join(','),
    ...rows.map(row => columns.map(col => row[col]).join(','))
  ].join('\n')

  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `query_result_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success('数据已导出')
}

onMounted(() => {
  loadTables()
  loadSavedQueries()
})
</script>

<style scoped>
.etl-development-page {
  padding: 0;
  height: calc(100vh - 128px);
}

.dev-container {
  height: 100%;
}

.dev-aside {
  background: #f8fafc;
  padding: 16px;
  overflow-y: auto;
}

.dev-main {
  padding: 16px;
  background: #f1f5f9;
  overflow-y: auto;
}

.mb-2 {
  margin-bottom: 12px;
}

.mt-4 {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 表树样式 */
.table-tree-card {
  margin-bottom: 16px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.node-icon {
  width: 16px;
  height: 16px;
  color: #64748b;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  font-size: 13px;
}

.node-label.table {
  color: #3b82f6;
}

.node-label.schema {
  color: #64748b;
  font-weight: 500;
}

.node-meta {
  font-size: 11px;
  color: #94a3b8;
  margin-left: auto;
}

/* SQL 编辑器样式 */
.sql-editor-wrapper {
  background: #1e293b;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.sql-editor {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  background: #1e293b;
  color: #e2e8f0;
  border: none;
  outline: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
}

.sql-editor::placeholder {
  color: #64748b;
}

/* 查询结果样式 */
.query-result {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.result-header .card-title {
  font-size: 14px;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #64748b;
}

.result-actions {
  display: flex;
  gap: 8px;
}

/* 保存的查询样式 */
.saved-queries-card {
  margin-top: 16px;
}
</style>
