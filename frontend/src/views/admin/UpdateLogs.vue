<template>
  <div class="update-logs-page">
    <!-- 搜索筛选区 -->
    <el-card class="search-card" shadow="sm">
      <el-form :inline="true" :model="searchForm" class="search-form" size="default">
        <el-form-item label="分类">
          <el-select v-model="searchForm.category" placeholder="全部分类" clearable class="filter-select">
            <el-option label="新功能" value="feature" />
            <el-option label="修复" value="fix" />
            <el-option label="优化" value="optimize" />
            <el-option label="安全" value="security" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索标题或内容"
            clearable
            @keyup.enter="handleSearch"
            class="search-input"
          />
        </el-form-item>
        <el-form-item class="form-actions">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新增日志
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row" v-if="stats">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">总记录数</div>
            <div class="stat-value">{{ stats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">新功能</div>
            <div class="stat-value feature">{{ stats.by_category.feature || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">修复</div>
            <div class="stat-value fix">{{ stats.by_category.fix || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">优化</div>
            <div class="stat-value optimize">{{ stats.by_category.optimize || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格区 -->
    <el-card class="table-card" shadow="sm">
      <el-table
        :data="logs"
        v-loading="loading"
        border
        stripe
        class="data-table"
        row-key="id"
      >
        <el-table-column prop="version" label="版本" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="分类" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getCategoryTagType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人员" width="120" align="center" />
        <el-table-column prop="created_at" label="更新时间" width="170" align="center" />
        <el-table-column label="操作" width="180" align="center" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" link @click="handleView(row)">
                查看
              </el-button>
              <el-button size="small" type="warning" link @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button size="small" type="danger" link @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="table-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          class="pagination"
        />
      </div>
    </el-card>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="showViewDialog" title="更新详情" width="800px" destroy-on-close>
      <div v-if="currentLog" class="log-detail">
        <div class="detail-header">
          <div class="header-row">
            <el-tag size="large">{{ currentLog.version }}</el-tag>
            <el-tag size="large" :type="getCategoryTagType(currentLog.category)">
              {{ getCategoryLabel(currentLog.category) }}
            </el-tag>
          </div>
          <div class="header-meta">
            <span><el-icon><User /></el-icon> {{ currentLog.operator }}</span>
            <span><el-icon><Calendar /></el-icon> {{ currentLog.created_at }}</span>
          </div>
        </div>
        
        <el-divider />
        
        <div class="detail-content">
          <h3>{{ currentLog.title }}</h3>
          <p class="detail-description">{{ currentLog.description }}</p>
          
          <div class="detail-body" v-html="formatContent(currentLog.content)"></div>
          
          <div v-if="currentLog.files_changed?.length" class="detail-files">
            <h4><el-icon><Folder /></el-icon> 修改文件</h4>
            <ul>
              <li v-for="(file, idx) in currentLog.files_changed" :key="idx">{{ file }}</li>
            </ul>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="editMode === 'create' ? '新增日志' : '编辑日志'" width="700px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="80px" size="default">
        <el-form-item label="版本号" prop="version">
          <el-input v-model="formData.version" placeholder="例如：1.0.0" />
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="简短描述更新内容" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="一句话概述" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="formData.category" placeholder="请选择分类">
            <el-option label="新功能" value="feature" />
            <el-option label="修复" value="fix" />
            <el-option label="优化" value="optimize" />
            <el-option label="安全" value="security" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="详情" prop="content">
          <el-input v-model="formData.content" type="textarea" :rows="8" placeholder="支持 Markdown 格式" />
        </el-form-item>
        <el-form-item label="修改文件">
          <el-input v-model="filesInput" type="textarea" :rows="3" placeholder="每行一个文件路径" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Calendar, Folder, Search, Plus, Document } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const logs = ref([])
const stats = ref(null)
const showViewDialog = ref(false)
const showEditDialog = ref(false)
const showCreateDialog = ref(false)
const editMode = ref('create')
const currentLog = ref(null)
const formRef = ref(null)
const filesInput = ref('')

const searchForm = reactive({
  category: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formData = reactive({
  id: null,
  version: '',
  title: '',
  description: '',
  category: '',
  content: '',
  files_changed: []
})

const formRules = {
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content: [{ required: true, message: '请输入更新内容', trigger: 'blur' }]
}

// 分类标签映射
const categoryMap = {
  feature: { label: '新功能', type: 'success' },
  fix: { label: '修复', type: 'danger' },
  optimize: { label: '优化', type: 'warning' },
  security: { label: '安全', type: 'info' },
  other: { label: '其他', type: 'info' }
}

const getCategoryLabel = (category) => categoryMap[category]?.label || category
const getCategoryTagType = (category) => categoryMap[category]?.type || 'info'

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

// 加载日志列表
const loadLogs = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: pagination.page,
      page_size: pagination.pageSize,
      ...(searchForm.category && { category: searchForm.category }),
      ...(searchForm.keyword && { keyword: searchForm.keyword })
    })
    const res = await apiRequest('get', `/api/admin/update-logs?${params}`)
    logs.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 加载统计
const loadStats = async () => {
  try {
    stats.value = await apiRequest('get', '/api/admin/update-logs/stats/category')
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadLogs()
}

// 重置
const handleReset = () => {
  searchForm.category = ''
  searchForm.keyword = ''
  handleSearch()
}

// 分页
const handlePageChange = (page) => {
  pagination.page = page
  loadLogs()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  loadLogs()
}

// 查看
const handleView = (row) => {
  currentLog.value = row
  showViewDialog.value = true
}

// 编辑
const handleEdit = (row) => {
  editMode.value = 'edit'
  formData.id = row.id
  formData.version = row.version
  formData.title = row.title
  formData.description = row.description
  formData.category = row.category
  formData.content = row.content
  formData.files_changed = row.files_changed || []
  filesInput.value = (row.files_changed || []).join('\n')
  showEditDialog.value = true
}

// 新增
const handleCreate = () => {
  editMode.value = 'create'
  Object.assign(formData, {
    id: null,
    version: '',
    title: '',
    description: '',
    category: '',
    content: '',
    files_changed: []
  })
  filesInput.value = ''
  showEditDialog.value = true
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该日志？', '提示', { type: 'warning' })
    await apiRequest('delete', `/api/admin/update-logs/${row.id}`)
    ElMessage.success('删除成功')
    loadLogs()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message || '删除失败')
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      submitting.value = true
      formData.files_changed = filesInput.value.split('\n').filter(f => f.trim())
      const url = editMode.value === 'create' 
        ? '/api/admin/update-logs' 
        : `/api/admin/update-logs/${formData.id}`
      const method = editMode.value === 'create' ? 'post' : 'put'
      await apiRequest(method, url, { body: JSON.stringify(formData) })
      ElMessage.success(editMode.value === 'create' ? '创建成功' : '更新成功')
      showEditDialog.value = false
      loadLogs()
      loadStats()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 格式化内容
const formatContent = (content) => {
  if (!content) return ''
  return content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h4>$1</h4>')
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .join('\n')
}

// 监听新增对话框
watch(showCreateDialog, (val) => {
  if (val) handleCreate()
})

onMounted(() => {
  loadLogs()
  loadStats()
})
</script>

<style scoped>
.update-logs-page {
  padding: var(--spacing-6);
}

.stats-row {
  margin: 16px 0;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 8px 0;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
}

.stat-value.feature { color: #10b981; }
.stat-value.fix { color: #ef4444; }
.stat-value.optimize { color: #f59e0b; }

.log-detail .detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-meta {
  color: #64748b;
  font-size: 13px;
}

.header-meta span {
  margin-left: 16px;
}

.detail-content h3 {
  font-size: 18px;
  margin: 0 0 12px 0;
  color: #1e293b;
}

.detail-description {
  color: #64748b;
  margin-bottom: 20px;
}

.detail-body {
  line-height: 1.8;
  color: #334155;
}

.detail-body h3 {
  font-size: 16px;
  margin: 16px 0 8px 0;
}

.detail-body li {
  margin-left: 20px;
  color: #475569;
}

.detail-files {
  margin-top: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.detail-files h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #475569;
}

.detail-files ul {
  margin: 0;
  padding-left: 20px;
}

.detail-files li {
  font-family: monospace;
  font-size: 12px;
  color: #64748b;
  margin: 4px 0;
}
</style>
