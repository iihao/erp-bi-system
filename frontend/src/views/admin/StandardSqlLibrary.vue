<template>
  <div class="standard-sql-library">
    <el-card class="header-card">
      <div class="card-header">
        <div class="header-left">
          <span class="title"><el-icon :size="18"><Document /></el-icon> 标准 SQL 库</span>
          <el-tag type="success" size="small">智能匹配</el-tag>
        </div>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          新增标准 SQL
        </el-button>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <el-icon :size="32"><Files /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总记录数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">启用中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
              <el-icon :size="32"><Operation /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.usageCount }}</div>
              <div class="stat-label">总使用次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%)">
              <el-icon :size="32"><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.tokenSaved }}</div>
              <div class="stat-label">节省 Token</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keywords" placeholder="输入关键词搜索" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" stripe border v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="问题模板" min-width="200">
          <template #default="{ row }">
            <span class="question-template">{{ row.question_template }}</span>
          </template>
        </el-table-column>
        <el-table-column label="关键词" min-width="150">
          <template #default="{ row }">
            <div class="keywords-container">
              <el-tag v-for="(kw, idx) in parseKeywords(row.keywords)" :key="idx" size="small" class="keyword-tag">
                {{ kw }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="SQL 语句" min-width="250">
          <template #default="{ row }">
            <el-popover trigger="hover" placement="top" :width="400">
              <template #reference>
                <pre class="sql-preview">{{ row.standard_sql.substring(0, 50) }}...</pre>
              </template>
              <pre class="sql-full">{{ row.standard_sql }}</pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="explanation" label="说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="usage_count" label="使用次数" width="100" sortable />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteRecord(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" @close="resetDialog">
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="问题模板" prop="question_template">
          <el-input v-model="formData.question_template" type="textarea" :rows="2" placeholder="例如：查询去化率最高的项目" />
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input v-model="keywordsInput" placeholder="输入关键词，用逗号分隔" />
          <div class="form-tip">例如：项目，去化，排行</div>
        </el-form-item>
        <el-form-item label="SQL 语句" prop="standard_sql">
          <el-input v-model="formData.standard_sql" type="textarea" :rows="6" placeholder="SELECT ..." />
        </el-form-item>
        <el-form-item label="说明" prop="explanation">
          <el-input v-model="formData.explanation" type="textarea" :rows="2" placeholder="SQL 功能说明" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Plus, Search, Clock, Operation, Coin, Files } from '@element-plus/icons-vue'

const apiRequest = async (method, url, data = null) => {
  const token = localStorage.getItem('token')
  const response = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: data ? JSON.stringify(data) : null
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '请求失败')
  }
  return response.json()
}

// 统计数据
const stats = ref({
  total: 0,
  active: 0,
  usageCount: 0,
  tokenSaved: 0
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 筛选
const filterForm = reactive({
  keywords: '',
  status: null
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增标准 SQL')
const submitting = ref(false)
const formRef = ref(null)
const keywordsInput = ref('')

// 表单数据
const formData = reactive({
  id: null,
  question_template: '',
  keywords: [],
  standard_sql: '',
  explanation: '',
  is_active: 1
})

// 表单规则
const formRules = {
  question_template: [{ required: true, message: '请输入问题模板', trigger: 'blur' }],
  keywords: [{ required: true, message: '请输入关键词', trigger: 'blur' }],
  standard_sql: [{ required: true, message: '请输入 SQL 语句', trigger: 'blur' }]
}

// 解析关键词
const parseKeywords = (keywordsStr) => {
  if (!keywordsStr) return []
  try {
    return typeof keywordsStr === 'string' ? JSON.parse(keywordsStr) : keywordsStr
  } catch {
    return keywordsStr.split(',').map(k => k.trim()).filter(k => k)
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', pagination.page)
    params.append('page_size', pagination.pageSize)
    if (filterForm.keywords) params.append('keywords', filterForm.keywords)
    if (filterForm.status !== null) params.append('is_active', filterForm.status)

    const res = await apiRequest('GET', `/api/admin/standard-sql?${params}`)
    tableData.value = res.items || []
    pagination.total = res.total || 0
    stats.value = res.stats || { total: 0, active: 0, usageCount: 0, tokenSaved: 0 }
  } catch (error) {
    ElMessage.error('加载失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.keywords = ''
  filterForm.status = null
  loadData()
}

// 显示新增对话框
const showAddDialog = () => {
  dialogTitle.value = '新增标准 SQL'
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row) => {
  dialogTitle.value = '编辑标准 SQL'
  formData.id = row.id
  formData.question_template = row.question_template
  formData.standard_sql = row.standard_sql
  formData.explanation = row.explanation
  formData.is_active = row.is_active
  keywordsInput.value = parseKeywords(row.keywords).join(', ')
  dialogVisible.value = true
}

// 重置对话框
const resetDialog = () => {
  formData.id = null
  formData.question_template = ''
  formData.standard_sql = ''
  formData.explanation = ''
  formData.is_active = 1
  keywordsInput.value = ''
  formRef.value?.resetFields()
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 解析关键词
      const keywords = keywordsInput.value.split(',').map(k => k.trim()).filter(k => k)
      
      const data = {
        question_template: formData.question_template,
        keywords: keywords,
        standard_sql: formData.standard_sql,
        explanation: formData.explanation,
        is_active: formData.is_active
      }

      if (formData.id) {
        await apiRequest('PUT', `/api/admin/standard-sql/${formData.id}`, data)
        ElMessage.success('更新成功')
      } else {
        await apiRequest('POST', '/api/admin/standard-sql', data)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      loadData()
    } catch (error) {
      ElMessage.error('操作失败：' + error.message)
    } finally {
      submitting.value = false
    }
  })
}

// 切换状态
const toggleStatus = async (row) => {
  try {
    await apiRequest('PUT', `/api/admin/standard-sql/${row.id}`, {
      is_active: row.is_active ? 0 : 1
    })
    ElMessage.success('状态已更新')
    loadData()
  } catch (error) {
    ElMessage.error('操作失败：' + error.message)
  }
}

// 删除记录
const deleteRecord = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除 "${row.question_template}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await apiRequest('DELETE', `/api/admin/standard-sql/${row.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.standard-sql-library {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.header-card {
  margin-bottom: 16px;
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

.title {
  font-size: 18px;
  font-weight: 600;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon .el-icon {
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.question-template {
  font-weight: 500;
  color: #303133;
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword-tag {
  background: #ecf5ff;
  color: #409eff;
  border-color: #d9ecff;
}

.sql-preview {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #67c23a;
  background: #f0f9ff;
  padding: 8px;
  border-radius: 4px;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sql-full {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #67c23a;
  background: #f0f9ff;
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

</style>
