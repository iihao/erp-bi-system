<template>
  <div class="etl-schedules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><Timer /></el-icon>
            ETL 调度配置
          </span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增调度
          </el-button>
        </div>
      </template>

      <el-table :data="schedules" v-loading="loading" border stripe>
        <el-table-column prop="schedule_id" label="ID" width="80" />
        <el-table-column prop="task_name" label="任务名称" width="180" />
        <el-table-column prop="cron_expression" label="Cron 表达式" width="150">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.cron_expression }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'danger'">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次运行" width="160" />
        <el-table-column prop="next_run_at" label="下次运行" width="160" />
        <el-table-column label="操作" width="180" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑调度' : '新增调度'"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="任务名称" prop="task_name">
          <el-select v-model="formData.task_name" placeholder="请选择任务" style="width: 100%">
            <el-option label="ODS 数据抽取" value="ODS 数据抽取" />
            <el-option label="DWD 数据清洗" value="DWD 数据清洗" />
            <el-option label="DWS 数据聚合" value="DWS 数据聚合" />
            <el-option label="ADS 报表生成" value="ADS 报表生成" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron 表达式" prop="cron_expression">
          <el-input v-model="formData.cron_expression" placeholder="例如：0 2 * * *" />
          <div class="form-tip">每天凌晨 2 点执行：0 2 * * *</div>
        </el-form-item>
        <el-form-item label="是否启用" prop="is_enabled">
          <el-switch v-model="formData.is_enabled" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Timer, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentScheduleId = ref(null)

const schedules = ref([])

const formData = reactive({
  task_name: '',
  cron_expression: '',
  is_enabled: true
})

const formRules = {
  task_name: [{ required: true, message: '请选择任务', trigger: 'change' }],
  cron_expression: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }]
}

const formRef = ref(null)

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

// 加载调度列表
const loadSchedules = async () => {
  loading.value = true
  try {
    const res = await apiRequest('get', '/api/admin/etl/schedules')
    schedules.value = res.items
  } catch (error) {
    ElMessage.error(error.message || '加载调度列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentScheduleId.value = row.schedule_id
  formData.task_name = row.task_name
  formData.cron_expression = row.cron_expression
  formData.is_enabled = row.is_enabled
  dialogVisible.value = true
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    task_name: '',
    cron_expression: '',
    is_enabled: true
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await apiRequest('put', `/api/admin/etl/schedules/${currentScheduleId.value}`, {
        body: JSON.stringify({
          cron_expression: formData.cron_expression,
          is_enabled: formData.is_enabled
        })
      })
      ElMessage.success('调度配置更新成功')
    } else {
      await apiRequest('post', '/api/admin/etl/schedules', {
        body: JSON.stringify(formData)
      })
      ElMessage.success('调度配置创建成功')
    }

    dialogVisible.value = false
    loadSchedules()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该调度配置吗？', '警告', {
      type: 'danger'
    })

    await apiRequest('delete', `/api/admin/etl/schedules/${row.schedule_id}`)

    ElMessage.success('调度配置删除成功')
    loadSchedules()
  } catch (error) {
    if (error.message && !error.message.includes('取消')) {
      ElMessage.error(error.message)
    }
  }
}

onMounted(() => {
  loadSchedules()
})
</script>

<style scoped>
.etl-schedules-page {
  padding: var(--spacing-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #1e293b;
}

.form-tip {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}
</style>
