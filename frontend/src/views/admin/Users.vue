<template>
  <div class="users-page page-container">
    <!-- 搜索筛选区 -->
    <el-card class="search-card" shadow="sm">
      <el-form :inline="true" :model="searchForm" class="search-form" size="default">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="用户名/邮箱/姓名"
            clearable
            @keyup.enter="handleSearch"
            class="search-input"
          >
            <template #prefix>
              
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.roleId" placeholder="全部角色" clearable class="filter-select">
            <el-option
              v-for="role in roleOptions"
              :key="role.role_id"
              :label="role.role_name"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable class="filter-select">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item class="form-actions">
          <el-button type="primary" @click="handleSearch" class="btn-search">搜索</el-button>
          <el-button @click="handleReset" class="btn-reset">重置</el-button>
          <el-button type="success" @click="handleCreate" class="btn-create">新增用户</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格区 -->
    <el-card class="table-card" shadow="sm">
      <!-- 表格工具栏 -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">用户列表</span>
          <el-tag type="info" class="total-count">共 {{ pagination.total }} 条</el-tag>
        </div>
        <div class="toolbar-right">
          <el-button @click="loadUsers" :loading="loading" circle class="toolbar-btn"> </el-button>
          <el-button @click="handleExport" class="toolbar-btn">导出</el-button>
        </div>
      </div>

      <el-table
        :data="users"
        v-loading="loading"
        border
        stripe
        class="data-table"
        @selection-change="handleSelectionChange"
        :header-cell-class-name="headerCellClassName"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="user_id" label="ID" width="80" align="center" sortable />
        <el-table-column prop="username" label="用户名" width="140" sortable />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="role_name" label="角色" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info" class="role-tag">{{ row.role_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small" class="status-tag">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center" sortable />
        <el-table-column label="操作" width="320" fixed="right" align="center" class-name="action-column">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" link @click="handleEdit(row)" class="action-btn edit">编辑</el-button>
              <el-button size="small" link @click="handleResetPassword(row)" class="action-btn reset">重置密码</el-button>
              <el-button
                size="small"
                link
                :type="row.status === 1 ? 'warning' : 'success'"
                @click="handleToggleStatus(row)"
                class="action-btn toggle"
              >{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
              <el-button
                size="small"
                type="danger"
                link
                @click="handleDelete(row)"
                class="action-btn delete"
              >删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="table-pagination">
        <div class="batch-actions" v-if="selectedRows.length > 0">
          <span class="selected-count">已选择 {{ selectedRows.length }} 条记录</span>
          <el-button size="small" type="danger" @click="handleBatchDelete" class="btn-batch-delete">批量删除</el-button>
        </div>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
          class="pagination"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="560px"
      @close="handleDialogClose"
      class="form-dialog"
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="dialog-header">
          
          <span class="dialog-title">{{ isEdit ? '编辑用户' : '新增用户' }}</span>
        </div>
      </template>
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="right"
        class="user-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="isEdit"
            placeholder="请输入用户名，3-20 个字符"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码，至少 6 位"
            show-password
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱地址" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="formData.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="formData.role_id" placeholder="请选择角色" class="full-width">
            <el-option
              v-for="role in roleOptions"
              :key="role.role_id"
              :label="role.role_name"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" class="btn-submit">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="重置密码"
      width="480px"
      class="form-dialog"
      :close-on-click-modal="false"
    >
      <template #header>
        <div class="dialog-header">
          
          <span class="dialog-title">重置密码</span>
        </div>
      </template>
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="90px"
        label-position="right"
        class="password-form"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码，至少 6 位"
            show-password
          />
        </el-form-item>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          class="password-tip"
        >
          密码重置后，用户需要使用新密码重新登录
        </el-alert>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialogVisible = false" class="btn-cancel">取消</el-button>
          <el-button type="primary" @click="handleResetPasswordSubmit" :loading="submitting" class="btn-submit">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const isEdit = ref(false)
const currentUserId = ref(null)
const selectedRows = ref([])

const searchForm = reactive({
  keyword: '',
  roleId: null,
  status: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const users = ref([])
const roleOptions = ref([])

const formData = reactive({
  username: '',
  password: '',
  email: '',
  real_name: '',
  role_id: null
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const passwordForm = reactive({
  new_password: ''
})

const passwordRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
  ]
}

const formRef = ref(null)
const passwordFormRef = ref(null)

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    const res = await apiRequest('get', '/api/admin/users', { params })
    users.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error(error.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 加载角色选项
const loadRoleOptions = async () => {
  try {
    roleOptions.value = await apiRequest('get', '/api/admin/users/roles/options')
  } catch (error) {
    console.error('加载角色选项失败', error)
  }
}

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

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.roleId = null
  searchForm.status = null
  handleSearch()
}

const handleCreate = () => {
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentUserId.value = row.user_id
  formData.username = row.username
  formData.email = row.email || ''
  formData.real_name = row.real_name || ''
  formData.role_id = row.role_id
  dialogVisible.value = true
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    username: '',
    password: '',
    email: '',
    real_name: '',
    role_id: null
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await apiRequest('put', `/api/admin/users/${currentUserId.value}`, {
        body: JSON.stringify({
          email: formData.email,
          real_name: formData.real_name,
          role_id: formData.role_id
        })
      })
      ElMessage.success('用户更新成功')
    } else {
      await apiRequest('post', '/api/admin/users', {
        body: JSON.stringify(formData)
      })
      ElMessage.success('用户创建成功')
    }

    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const handleResetPassword = (row) => {
  currentUserId.value = row.user_id
  passwordForm.new_password = ''
  passwordDialogVisible.value = true
}

const handleResetPasswordSubmit = async () => {
  try {
    await passwordFormRef.value.validate()
    submitting.value = true

    await apiRequest('post', `/api/admin/users/${currentUserId.value}/reset-password`, {
      body: JSON.stringify({ new_password: passwordForm.new_password })
    })

    ElMessage.success('密码重置成功')
    passwordDialogVisible.value = false
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const handleToggleStatus = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.status === 1 ? '禁用' : '启用'}该用户吗？`,
      '提示',
      { type: 'warning' }
    )

    await apiRequest('post', `/api/admin/users/${row.user_id}/toggle-status`, {
      body: JSON.stringify({ status: row.status === 1 ? 0 : 1 })
    })

    ElMessage.success('操作成功')
    loadUsers()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？此操作不可恢复', '警告', {
      type: 'danger'
    })

    await apiRequest('delete', `/api/admin/users/${row.user_id}`)

    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个用户吗？此操作不可恢复`,
      '警告',
      { type: 'danger' }
    )

    for (const row of selectedRows.value) {
      await apiRequest('delete', `/api/admin/users/${row.user_id}`)
    }

    ElMessage.success('批量删除成功')
    selectedRows.value = []
    loadUsers()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

const headerCellClassName = () => 'table-header-cell'

onMounted(() => {
  loadUsers()
  loadRoleOptions()
})
</script>

<style scoped>
/* ========================================
   用户管理页面 - 企业级列表页样式
   ======================================== */

.page-container {
  max-width: 100%;
}

/* 搜索卡片 */
.search-card {
  margin-bottom: var(--spacing-4);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
}

.search-input {
  width: 240px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: var(--radius-lg);
}

.input-icon {
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
}

.filter-select {
  width: 160px;
}

.form-actions {
  margin-left: auto;
  display: flex;
  gap: var(--spacing-2);
}

.btn-search, .btn-reset, .btn-create {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

/* 表格卡片 */
.table-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

/* 表格工具栏 */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: var(--spacing-4);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.toolbar-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.total-count {
  font-size: var(--text-sm);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 数据表格 - 统一优化样式 */
.data-table {
  font-size: 13px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.data-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 13px;
  padding: 12px 14px;
  border-bottom: 2px solid var(--border);
}

.data-table :deep(.el-table__header th.table-header-cell) {
  background: linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%);
}

.data-table :deep(.el-table__body td) {
  padding: 10px 14px;
  color: var(--text-secondary);
  font-size: 13px;
}

.data-table :deep(.el-table__body tr:hover) {
  background-color: var(--primary-50) !important;
}

.data-table :deep(.el-table__body tr.el-table__row--striped td) {
  background: var(--slate-50);
}

.data-table :deep(.el-table__body tr.el-table__row--striped:hover td) {
  background: var(--primary-50) !important;
}

/* 修复操作列按钮显示 */
.action-column {
  padding: 8px 0;
}

.action-column .cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 标签样式 */
.role-tag, .status-tag {
  font-weight: var(--font-medium);
}

/* 操作按钮 - 修复显示问题 */
.action-buttons {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  padding: 6px 10px;
  font-size: 13px;
  height: auto;
  min-height: 28px;
}

.action-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.action-btn.edit { color: var(--primary); }
.action-btn.reset { color: var(--warning); }
.action-btn.toggle { color: var(--info); }
.action-btn.delete { color: var(--danger); }

.action-btn:hover {
  opacity: 0.8;
  transform: translateY(-1px);
}

/* 分页 */
.table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-light);
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.selected-count {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.btn-batch-delete {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

/* 分页 - 中文显示 */
.pagination {
  font-size: 13px;
}

.pagination :deep(.el-pagination__total) {
  color: var(--text-tertiary);
  font-size: 13px;
}

.pagination :deep(.el-pagination__sizes) {
  color: var(--text-secondary);
}

.pagination :deep(.el-pager li) {
  border-radius: var(--radius);
  font-weight: 500;
  font-size: 13px;
  min-width: 32px;
  height: 32px;
  line-height: 32px;
}

.pagination :deep(.el-pager li.active) {
  background: var(--primary);
  color: #ffffff;
}

.pagination :deep(.el-pager li:hover) {
  background: var(--primary-50);
  color: var(--primary);
}

.pagination :deep(.el-pagination__prev),
.pagination :deep(.el-pagination__next) {
  font-size: 13px;
}

/* 分页按钮中文 */
.pagination :deep(.el-pagination__jump) {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 对话框 */
.form-dialog :deep(.el-dialog__header) {
  padding: 0;
  border-bottom: 1px solid var(--border-light);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-5) var(--spacing-6);
}

.dialog-icon {
  width: 22px;
  height: 22px;
  color: var(--primary);
}

.dialog-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.form-dialog :deep(.el-dialog__body) {
  padding: var(--spacing-6);
}

.form-dialog :deep(.el-dialog__footer) {
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-light);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
}

.btn-cancel, .btn-submit {
  min-width: 80px;
}

/* 表单 */
.user-form, .password-form {
  padding-top: var(--spacing-4);
}

.full-width {
  width: 100%;
}

/* 密码提示 */
.password-tip {
  margin-top: var(--spacing-4);
  border-radius: var(--radius-lg);
}

/* 响应式 */
@media (max-width: 1024px) {
  .search-input {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .form-actions {
    width: 100%;
    margin-left: 0;
    flex-wrap: wrap;
  }

  .form-actions .el-button {
    flex: 1;
    min-width: 100px;
  }

  .table-toolbar {
    flex-direction: column;
    gap: var(--spacing-3);
    align-items: flex-start;
  }

  .toolbar-right {
    width: 100%;
    justify-content: flex-start;
  }

  .table-pagination {
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .batch-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
