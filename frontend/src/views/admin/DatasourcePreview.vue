<template>
  <div class="datasource-preview">
    <el-card class="header-card">
      <div class="card-header">
        <div class="header-left">
          <el-button circle @click="$router.back()">
            <el-icon><Back /></el-icon>
          </el-button>
          <div class="title-section">
            <span class="title"><el-icon :size="18"><DataAnalysis /></el-icon> 数据源预览：{{ datasource.name }}</span>
            <el-tag :type="datasource.status === 'active' ? 'success' : 'info'">
              {{ datasource.status === 'active' ? '已激活' : '未激活' }}
            </el-tag>
            <el-tag type="warning">{{ datasource.db_type }}</el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button @click="refreshMetadata"><el-icon><Refresh /></el-icon> 刷新</el-button>
          <el-button type="primary" @click="showQueryEditor = !showQueryEditor">
            <el-icon><EditPen /></el-icon> SQL 查询
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- SQL 查询编辑器 -->
    <el-card v-if="showQueryEditor" class="query-editor-card">
      <div class="query-editor">
        <div class="editor-header">
          <span><el-icon><EditPen /></el-icon> SQL 查询编辑器</span>
          <el-button type="primary" size="small" @click="executeQuery" :loading="executing">
            <el-icon><VideoPlay /></el-icon> 执行
          </el-button>
        </div>
        <el-input
          v-model="sqlQuery"
          type="textarea"
          :rows="6"
          placeholder="输入 SELECT 查询语句，例如：SELECT * FROM table_name"
          class="sql-input"
        />
        <div class="query-tips">
          <el-alert
            title="只支持 SELECT 查询语句，查询结果最多返回 100 条"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-card>

    <!-- 查询结果 -->
    <el-card v-if="queryResult" class="result-card">
      <template #header>
        <div class="result-header">
          <span><el-icon><DataAnalysis /></el-icon> 查询结果</span>
          <div class="result-info">
            <el-tag size="small">共 {{ queryResult.row_count }} 条</el-tag>
            <el-tag size="small" type="success">耗时 {{ queryResult.execution_time_ms }}ms</el-tag>
          </div>
        </div>
      </template>
      <el-table :data="queryResult.data" stripe border max-height="400">
        <el-table-column
          v-for="col in queryResult.columns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="120"
        />
      </el-table>
    </el-card>

    <!-- 元数据加载状态 -->
    <el-card v-loading="loading" class="metadata-card">
      <template #header>
        <div class="metadata-header">
          <span><el-icon><FolderChecked /></el-icon> 表列表（{{ metadata.table_count }} 个表）</span>
        </div>
      </template>

      <!-- 表列表 -->
      <div class="table-list">
        <el-collapse v-model="activeTables" accordion>
          <el-collapse-item
            v-for="table in metadata.tables"
            :key="table"
            :name="table"
            @click="loadTableSchema(table)"
          >
            <template #title>
              <div class="table-title">
                <el-icon><Document /></el-icon>
                <span>{{ table }}</span>
              </div>
            </template>
            
            <!-- 表结构 -->
            <div v-if="tableSchemas[table]" class="table-schema">
              <el-table :data="tableSchemas[table]" stripe size="small">
                <el-table-column prop="field" label="字段" width="150" />
                <el-table-column prop="type" label="类型" width="120">
                  <template #default="{ row }">
                    <el-tag size="small" type="info">{{ row.type }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="nullable" label="可空" width="60" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.nullable" size="small" type="success">是</el-tag>
                    <el-tag v-else size="small">否</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="key" label="键" width="60" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.key === 'PRI'" size="small" type="warning">PK</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="default" label="默认值" />
              </el-table>
              
              <div class="table-actions">
                <el-button size="small" @click="previewTableData(table)">
                  <el-icon><View /></el-icon> 预览数据
                </el-button>
                <el-button size="small" @click="copyQuery(table)">
                  <el-icon><CopyDocument /></el-icon> 复制查询
                </el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Back, Refresh, EditPen, VideoPlay, DataAnalysis, FolderChecked, View, CopyDocument } from '@element-plus/icons-vue'
import { ElCard, ElTable, ElTableColumn, ElTag, ElButton, ElInput, ElAlert, ElCollapse, ElCollapseItem } from 'element-plus'

const route = useRoute()
const datasourceId = route.params.id

const datasource = ref({
  name: '',
  db_type: '',
  status: 'inactive'
})

const loading = ref(false)
const metadata = reactive({
  tables: [],
  table_count: 0
})

const tableSchemas = ref({})
const activeTables = ref('')

const showQueryEditor = ref(false)
const sqlQuery = ref('')
const executing = ref(false)
const queryResult = ref(null)

// 加载数据源详情
const loadDatasource = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${datasourceId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    datasource.value = data
  } catch (error) {
    ElMessage.error('加载数据源失败')
  }
}

// 加载元数据
const loadMetadata = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${datasourceId}/metadata`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      metadata.tables = data.tables || []
      metadata.table_count = data.table_count || 0
      ElMessage.success(`加载 ${metadata.table_count} 个表`)
    } else {
      ElMessage.error(data.detail || '加载元数据失败')
    }
  } catch (error) {
    ElMessage.error('加载元数据失败')
  } finally {
    loading.value = false
  }
}

// 加载表结构
const loadTableSchema = async (tableName) => {
  if (tableSchemas.value[tableName]) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${datasourceId}/table-schema/${tableName}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      tableSchemas.value[tableName] = data.columns || []
    }
  } catch (error) {
    ElMessage.error('加载表结构失败')
  }
}

// 预览表数据
const previewTableData = (tableName) => {
  sqlQuery.value = `SELECT * FROM \`${tableName}\` LIMIT 100`
  showQueryEditor.value = true
  executeQuery()
}

// 复制查询语句
const copyQuery = (tableName) => {
  const query = `SELECT * FROM \`${tableName}\` LIMIT 100`
  navigator.clipboard.writeText(query)
  ElMessage.success('已复制查询语句')
}

// 执行查询
const executeQuery = async () => {
  if (!sqlQuery.value.trim()) {
    ElMessage.warning('请输入 SQL 查询语句')
    return
  }
  
  executing.value = true
  queryResult.value = null
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${datasourceId}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sql: sqlQuery.value,
        limit: 100
      })
    })
    const data = await res.json()
    
    if (data.success) {
      queryResult.value = data
      ElMessage.success(`查询成功，返回 ${data.row_count} 条记录`)
    } else {
      ElMessage.error(data.error || '查询失败')
    }
  } catch (error) {
    ElMessage.error('查询失败')
  } finally {
    executing.value = false
  }
}

// 刷新元数据
const refreshMetadata = () => {
  tableSchemas.value = {}
  loadMetadata()
  ElMessage.success('元数据已刷新')
}

onMounted(() => {
  loadDatasource()
  loadMetadata()
})
</script>

<style scoped>
.datasource-preview {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.query-editor-card {
  margin-bottom: 20px;
}

.query-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.sql-input {
  font-family: 'Courier New', monospace;
}

.query-tips {
  max-width: 400px;
}

.result-card {
  margin-bottom: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-info {
  display: flex;
  gap: 8px;
}

.metadata-card {
  min-height: 400px;
}

.metadata-header {
  font-weight: 600;
}

.table-list {
  max-height: 600px;
  overflow-y: auto;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.table-schema {
  padding: 12px;
}

.table-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

:deep(.el-collapse-item__header) {
  font-weight: 500;
  background: #f5f7fa;
}

:deep(.el-table) {
  font-size: 13px;
}
</style>
