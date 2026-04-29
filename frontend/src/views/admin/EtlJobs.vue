<template>
  <div class="etl-jobs-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">总任务数</div>
            <div class="stat-value">{{ stats.totalJobs }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">今日成功</div>
            <div class="stat-value success">{{ stats.todaySuccess }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">今日失败</div>
            <div class="stat-value error">{{ stats.todayFailed }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-label">成功率</div>
            <div class="stat-value">{{ stats.successRate }}%</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 作业列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon :size="18"><Grid /></el-icon>
            作业定义
          </span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增作业
          </el-button>
        </div>
      </template>

      <el-table :data="jobs" v-loading="loading" border stripe>
        <el-table-column prop="task_id" label="ID" width="70" />
        <el-table-column prop="task_name" label="任务名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="layer" label="分层" width="100">
          <template #default="{ row }">
            <el-tag :type="getLayerTagType(row.layer)">{{ row.layer }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="script_path" label="脚本路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="schedule" label="调度配置" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.schedule_enabled" type="success" size="small">
              {{ row.schedule_cron }}
            </el-tag>
            <el-tag v-else type="info" size="small">未启用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次运行" width="160" />
        <el-table-column label="操作" width="280" fixed="right" class-name="action-column">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="runTask(row)" :loading="row.running">
              运行
            </el-button>
            <el-button size="small" @click="handleSchedule(row)">调度</el-button>
            <el-button size="small" @click="viewLog(row)">日志</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑作业对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑作业' : '新增作业'"
      width="700px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="formData.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="数据分层" prop="layer">
          <el-select v-model="formData.layer" placeholder="请选择数据分层">
            <el-option label="ODS (原始数据层)" value="ODS" />
            <el-option label="DWD (明细数据层)" value="DWD" />
            <el-option label="DWS (汇总数据层)" value="DWS" />
            <el-option label="ADS (应用数据层)" value="ADS" />
          </el-select>
        </el-form-item>
        <el-form-item label="脚本路径" prop="script_path">
          <el-input v-model="formData.script_path" placeholder="例如：etl/ods_extract.py" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        <el-form-item label="启用调度">
          <el-switch v-model="formData.schedule_enabled" />
        </el-form-item>
        <el-form-item label="Cron 表达式" v-if="formData.schedule_enabled">
          <el-input v-model="formData.schedule_cron" placeholder="例如：0 2 * * * (每天 2 点)" />
          <div class="form-tip">常用示例：0 2 * * * (每天 2 点) | 0 */30 * * * (每 30 分钟)</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 调度配置对话框 -->
    <el-dialog
      v-model="scheduleDialogVisible"
      title="调度配置"
      width="500px"
    >
      <el-form :model="scheduleForm" label-width="100px">
        <el-form-item label="启用调度">
          <el-switch v-model="scheduleForm.enabled" />
        </el-form-item>
        <el-form-item label="Cron 表达式" v-if="scheduleForm.enabled">
          <el-input v-model="scheduleForm.cron" placeholder="0 2 * * *" />
          <div class="form-tip">
            <strong>示例：</strong><br>
            <code>0 2 * * *</code> - 每天 2:00 执行<br>
            <code>0 */30 * * *</code> - 每 30 分钟执行<br>
            <code>0 9 * * 1-5</code> - 工作日 9:00 执行
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSchedule" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 日志查看对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      title="运行日志"
      width="900px"
    >
      <el-table :data="logs" stripe max-height="500">
        <el-table-column prop="log_id" label="ID" width="70" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : row.status === 'running' ? '运行中' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160" />
        <el-table-column prop="end_time" label="结束时间" width="160" />
        <el-table-column prop="duration_seconds" label="耗时 (秒)" width="80" />
        <el-table-column prop="message" label="消息" min-width="250" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Grid } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const logDialogVisible = ref(false)
const isEdit = ref(false)
const currentJob = ref(null)

const stats = reactive({
  totalJobs: 0,
  todaySuccess: 0,
  todayFailed: 0,
  successRate: 0
})

const jobs = ref([])
const logs = ref([])

const formData = reactive({
  task_id: null,
  task_name: '',
  layer: 'ODS',
  script_path: '',
  description: '',
  schedule_enabled: false,
  schedule_cron: ''
})

const scheduleForm = reactive({
  enabled: false,
  cron: ''
})

const formRules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  layer: [{ required: true, message: '请选择数据分层', trigger: 'change' }],
  script_path: [{ required: true, message: '请输入脚本路径', trigger: 'blur' }]
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

const getLayerTagType = (layer) => {
  const types = { ODS: 'info', DWD: 'warning', DWS: 'success', ADS: 'danger' }
  return types[layer] || 'info'
}

const getStatusTagType = (status) => {
  const types = { success: 'success', running: 'warning', failed: 'danger', pending: 'info' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { success: '成功', running: '运行中', failed: '失败', pending: '等待' }
  return texts[status] || status
}

// 加载任务列表
const loadJobs = async () => {
  loading.value = true
  try {
    const res = await apiRequest('get', '/api/admin/etl/tasks')
    jobs.value = (res.items || []).map(task => ({
      ...task,
      running: false
    }))
    stats.totalJobs = res.total ?? jobs.value.length
  } catch (error) {
    ElMessage.error(error.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const res = await apiRequest('get', '/api/admin/etl/stats')
    stats.todaySuccess = res.todaySuccess ?? res.today_success ?? 0
    stats.todayFailed = res.todayFailed ?? res.today_failed ?? 0
    stats.successRate = res.successRate ?? res.success_rate ?? 0
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

// 加载日志
const loadLogs = async () => {
  if (!currentJob.value) return

  try {
    const res = await apiRequest('get', `/api/admin/etl/tasks/${currentJob.value.task_id}/log`, {
      params: { page: 1, page_size: 50 }
    })
    logs.value = res.items || []
  } catch (error) {
    ElMessage.error(error.message || '加载日志失败')
  }
}

const handleCreate = () => {
  isEdit.value = false
  Object.assign(formData, {
    task_id: null,
    task_name: '',
    layer: 'ODS',
    script_path: '',
    description: '',
    schedule_enabled: false,
    schedule_cron: ''
  })
  dialogVisible.value = true
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await apiRequest('put', `/api/admin/etl/tasks/${formData.task_id}`, {
        body: JSON.stringify(formData)
      })
      ElMessage.success('作业更新成功')
    } else {
      await apiRequest('post', '/api/admin/etl/tasks', {
        body: JSON.stringify(formData)
      })
      ElMessage.success('作业创建成功')
    }

    dialogVisible.value = false
    loadJobs()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const runTask = async (task) => {
  task.running = true
  task.status = 'running'

  try {
    const result = await apiRequest('post', `/api/admin/etl/tasks/${task.task_id}/run`)

    ElMessage.success(`${task.task_name} 执行成功，耗时${result.duration}秒`)

    await loadJobs()
    loadStats()
  } catch (error) {
    ElMessage.error(`${task.task_name} 执行失败：${error.message}`)
    await loadJobs()
  } finally {
    task.running = false
  }
}

const handleSchedule = (row) => {
  currentJob.value = row
  scheduleForm.enabled = row.schedule_enabled || false
  scheduleForm.cron = row.schedule_cron || ''
  scheduleDialogVisible.value = true
}

const handleSaveSchedule = async () => {
  try {
    submitting.value = true
    await apiRequest('put', `/api/admin/etl/tasks/${currentJob.value.task_id}/schedule`, {
      body: JSON.stringify({
        schedule_enabled: scheduleForm.enabled,
        schedule_cron: scheduleForm.cron
      })
    })

    ElMessage.success('调度配置保存成功')
    scheduleDialogVisible.value = false
    loadJobs()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

const viewLog = (row) => {
  currentJob.value = row
  logDialogVisible.value = true
  loadLogs()
}

onMounted(() => {
  loadJobs()
  loadStats()
})
</script>

<style scoped>
.etl-jobs-page {
  padding: var(--spacing-6);
}

.mb-4 {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px 0;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.stat-value.success {
  color: #16a34a;
}

.stat-value.error {
  color: #dc2626;
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
  margin-top: 8px;
  line-height: 1.5;
}

.form-tip code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
}
</style>
