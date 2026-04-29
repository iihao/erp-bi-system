<template>
  <div class="reports-page">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="报表名称/描述"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.reportType" placeholder="全部类型" clearable>
            <el-option label="图表" value="chart" />
            <el-option label="表格" value="table" />
            <el-option label="KPI 指标" value="kpi" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
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
          <el-button type="success" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增报表
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="reports" v-loading="loading" border stripe>
        <el-table-column prop="report_id" label="ID" width="70" />
        <el-table-column prop="report_name" label="报表名称" width="180" />
        <el-table-column prop="report_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.report_type)">
              {{ getTypeLabel(row.report_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column prop="published_at" label="发布时间" width="160" />
        <el-table-column label="操作" width="280" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              :type="row.status === 'published' ? 'warning' : 'success'"
              @click="handleTogglePublish(row)"
            >
              {{ row.status === 'published' ? '取消发布' : '发布' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑报表' : '新增报表'"
      width="700px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="报表名称" prop="report_name">
              <el-input v-model="formData.report_name" placeholder="请输入报表名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报表类型" prop="report_type">
              <el-select v-model="formData.report_type" placeholder="请选择类型" style="width: 100%">
                <el-option label="图表" value="chart" />
                <el-option label="表格" value="table" />
                <el-option label="KPI 指标" value="kpi" />
                <el-option label="仪表板" value="dashboard" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="报表描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入报表描述"
          />
        </el-form-item>
        <el-form-item label="SQL 查询" prop="sql_query">
          <el-input
            v-model="formData.sql_query"
            type="textarea"
            :rows="6"
            placeholder="请输入 SQL 查询语句"
            style="font-family: monospace;"
          />
        </el-form-item>
        <el-form-item label="图表配置" prop="config_json">
          <el-input
            v-model="configJsonStr"
            type="textarea"
            :rows="4"
            placeholder="请输入 JSON 格式的图表配置"
            style="font-family: monospace;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, RefreshLeft, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentReportId = ref(null)

const searchForm = reactive({
  keyword: '',
  reportType: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const reports = ref([])

const formData = reactive({
  report_name: '',
  report_type: '',
  description: '',
  sql_query: '',
  config_json: null
})

const configJsonStr = ref('')

const formRules = {
  report_name: [{ required: true, message: '请输入报表名称', trigger: 'blur' }],
  report_type: [{ required: true, message: '请选择报表类型', trigger: 'change' }]
}

const formRef = ref(null)

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

  try {
    const response = await fetch(url, config)

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

// 加载报表列表
const loadReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const res = await apiRequest('get', '/api/admin/reports', { params })
    reports.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载报表列表失败')
  } finally {
    loading.value = false
  }
}

const getTypeTagType = (type) => {
  const types = { chart: 'primary', table: 'success', kpi: 'warning', dashboard: 'info' }
  return types[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = { chart: '图表', table: '表格', kpi: 'KPI 指标', dashboard: '仪表板' }
  return labels[type] || type
}

const getStatusTagType = (status) => {
  const types = { draft: 'info', published: 'success', archived: 'warning' }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = { draft: '草稿', published: '已发布', archived: '已归档' }
  return labels[status] || status
}

const handleSearch = () => {
  pagination.page = 1
  loadReports()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.reportType = ''
  searchForm.status = ''
  handleSearch()
}

const handleCreate = () => {
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentReportId.value = row.report_id
  formData.report_name = row.report_name
  formData.report_type = row.report_type
  formData.description = row.description || ''
  formData.sql_query = row.sql_query || ''
  formData.config_json = row.config_json
  configJsonStr.value = row.config_json ? JSON.stringify(row.config_json, null, 2) : ''
  dialogVisible.value = true
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    report_name: '',
    report_type: '',
    description: '',
    sql_query: '',
    config_json: null
  })
  configJsonStr.value = ''
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    // 解析配置 JSON
    let configJson = null
    if (configJsonStr.value) {
      try {
        configJson = JSON.parse(configJsonStr.value)
      } catch (e) {
        throw new Error('图表配置 JSON 格式不正确')
      }
    }

    const body = {
      report_name: formData.report_name,
      report_type: formData.report_type,
      description: formData.description,
      sql_query: formData.sql_query,
      config_json: configJson
    }

    if (isEdit.value) {
      await apiRequest('put', `/admin/reports/${currentReportId.value}`, { body: JSON.stringify(body) })
      ElMessage.success('报表更新成功')
    } else {
      await apiRequest('post', '/api/admin/reports', { body: JSON.stringify(body) })
      ElMessage.success('报表创建成功')
    }

    dialogVisible.value = false
    loadReports()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const handleTogglePublish = async (row) => {
  try {
    const action = row.status === 'published' ? '取消发布' : '发布'
    await ElMessageBox.confirm(`确定要${action}该报表吗？`, '提示', { type: 'warning' })

    const endpoint = row.status === 'published' ? 'unpublish' : 'publish'
    await apiRequest('post', `/admin/reports/${row.report_id}/${endpoint}`)

    ElMessage.success(`${action}成功`)
    loadReports()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该报表吗？此操作不可恢复', '警告', {
      type: 'danger'
    })

    await apiRequest('delete', `/admin/reports/${row.report_id}`)

    ElMessage.success('报表删除成功')
    loadReports()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports-page {
  padding: var(--spacing-6);
}

.search-card {
  margin-bottom: 16px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
}

.table-card {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
