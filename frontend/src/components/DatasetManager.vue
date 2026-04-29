<template>
  <div class="dataset-manager">
    <!-- 数据集列表 -->
    <el-card class="dataset-card">
      <template #header>
        <div class="card-header">
          <span>📊 数据集管理</span>
          <el-button type="primary" size="small" @click="showAddDataset">
            <el-icon><Plus /></el-icon>
            新建数据集
          </el-button>
        </div>
      </template>

      <el-empty v-if="datasets.length === 0" description="暂无数据集" :image-size="80">
        <el-button type="primary" @click="showAddDataset">新建数据集</el-button>
      </el-empty>

      <el-collapse v-else v-model="activeDatasets" accordion>
        <el-collapse-item
          v-for="ds in datasets"
          :key="ds.id"
          :name="ds.id"
        >
          <template #title>
            <div class="dataset-title">
              <el-icon><DataLine /></el-icon>
              <span class="dataset-name">{{ ds.name }}</span>
              <el-tag size="small" :type="ds.type === 'sql' ? 'success' : 'info'">
                {{ ds.type === 'sql' ? 'SQL 查询' : '数据表' }}
              </el-tag>
              <el-tag size="small" type="warning" v-if="ds.isDefault">默认</el-tag>
            </div>
          </template>
          
          <div class="dataset-content">
            <div class="dataset-info">
              <div class="info-row">
                <span class="label">数据集名称：</span>
                <span class="value">{{ ds.name }}</span>
              </div>
              <div class="info-row">
                <span class="label">数据类型：</span>
                <span class="value">{{ ds.type === 'sql' ? 'SQL 查询' : '数据表' }}</span>
              </div>
              <div class="info-row" v-if="ds.type === 'table'">
                <span class="label">数据表：</span>
                <span class="value">{{ ds.tableName }}</span>
              </div>
              <div class="info-row" v-if="ds.type === 'sql'">
                <span class="label">SQL 语句：</span>
                <div class="sql-content">
                  <pre>{{ ds.sql }}</pre>
                </div>
              </div>
              <div class="info-row" v-if="ds.fields && ds.fields.length > 0">
                <span class="label">字段列表（{{ ds.fields.length }}）：</span>
                <div class="field-list">
                  <el-tag
                    v-for="field in ds.fields"
                    :key="field.name"
                    size="small"
                    style="margin: 4px;"
                    :type="getFieldTypeTag(field.type)"
                  >
                    <el-icon style="vertical-align: middle; margin-right: 2px;">
                      <component :is="getFieldTypeIcon(field.type)" />
                    </el-icon>
                    {{ field.name }} ({{ field.type }})
                  </el-tag>
                </div>
              </div>
            </div>
            
            <div class="dataset-actions">
              <el-button size="small" @click="editDataset(ds)">编辑</el-button>
              <el-button size="small" @click="testDataset(ds)">测试</el-button>
              <el-button size="small" :type="ds.isDefault ? 'warning' : 'success'" @click="setDefaultDataset(ds)">
                {{ ds.isDefault ? '取消默认' : '设为默认' }}
              </el-button>
              <el-button size="small" type="danger" @click="deleteDataset(ds.id)">删除</el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 数据集编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="900px"
      :close-on-click-modal="false"
      @closed="resetDialog"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="formData.name" placeholder="例如：销售数据集" />
        </el-form-item>
        
        <el-form-item label="数据集类型" prop="type">
          <el-radio-group v-model="formData.type">
            <el-radio label="table">数据表</el-radio>
            <el-radio label="sql">SQL 查询</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="选择数据源" prop="datasourceId" v-if="formData.type === 'table'">
          <el-select
            v-model="formData.datasourceId"
            placeholder="选择数据源"
            style="width: 100%;"
            @change="onDatasourceChange"
          >
            <el-option
              v-for="ds in datasourceList"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择数据表" prop="tableName" v-if="formData.type === 'table'">
          <el-select
            v-model="formData.tableName"
            placeholder="选择数据表"
            style="width: 100%;"
            @change="loadTableFields"
          >
            <el-option
              v-for="table in tableList"
              :key="table"
              :label="table"
              :value="table"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="SQL 语句" prop="sql" v-if="formData.type === 'sql'">
          <el-input
            v-model="formData.sql"
            type="textarea"
            :rows="10"
            placeholder="输入 SQL 查询语句，例如：&#10;SELECT id, name, created_at FROM users WHERE status = 1"
            style="font-family: 'Courier New', monospace;"
          />
          <div class="form-tip">
            <el-alert
              title="SQL 查询将以只读方式执行，建议使用 SELECT 语句。系统会自动获取查询结果的字段信息。"
              type="info"
              :closable="false"
              show-icon
            />
          </div>
        </el-form-item>
        
        <el-form-item label="备注说明">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="输入数据集的备注说明"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="saving">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, DataLine } from '@element-plus/icons-vue'

// 数据
const datasets = ref([])
const activeDatasets = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建数据集')
const saving = ref(false)
const datasourceList = ref([])
const tableList = ref([])
const formRef = ref(null)

// 表单数据
const formData = ref({
  id: '',
  name: '',
  type: 'table',
  datasourceId: '',
  tableName: '',
  sql: '',
  description: '',
  fields: [],
  isDefault: false
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据集类型', trigger: 'change' }
  ],
  datasourceId: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  tableName: [
    { required: true, message: '请选择数据表', trigger: 'change' }
  ],
  sql: [
    { required: true, message: '请输入 SQL 语句', trigger: 'blur' },
    {
      pattern: /^\s*SELECT/i,
      message: 'SQL 语句必须是 SELECT 查询',
      trigger: 'blur'
    }
  ]
}

// 加载数据源列表
const loadDatasources = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/admin/datasources', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    datasourceList.value = data.items || []
    
    if (datasourceList.value.length > 0 && !formData.value.datasourceId) {
      formData.value.datasourceId = datasourceList.value[0].id
    }
  } catch (error) {
    console.error('加载数据源失败', error)
  }
}

// 加载表列表
const loadTableList = async (datasourceId) => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${datasourceId}/metadata`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      tableList.value = data.tables || []
    } else {
      ElMessage.error(data.detail || '加载表列表失败')
    }
  } catch (error) {
    ElMessage.error('加载表列表失败')
  }
}

// 加载表字段
const loadTableFields = async () => {
  if (!formData.value.datasourceId || !formData.value.tableName) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/admin/datasources/${formData.value.datasourceId}/table-schema/${formData.value.tableName}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (res.ok) {
      formData.value.fields = data.columns || []
      ElMessage.success(`加载 ${data.columns.length} 个字段`)
    }
  } catch (error) {
    console.error('加载表字段失败', error)
  }
}

// 数据源变化
const onDatasourceChange = (datasourceId) => {
  tableList.value = []
  formData.value.tableName = ''
  formData.value.fields = []
  loadTableList(datasourceId)
}

// 显示新增对话框
const showAddDataset = () => {
  dialogTitle.value = '新建数据集'
  formData.value = {
    id: '',
    name: '',
    type: 'table',
    datasourceId: datasourceList.value[0]?.id || '',
    tableName: '',
    sql: '',
    description: '',
    fields: [],
    isDefault: false
  }
  dialogVisible.value = true
  loadDatasources()
}

// 编辑数据集
const editDataset = (ds) => {
  dialogTitle.value = '编辑数据集'
  formData.value = { ...ds }
  dialogVisible.value = true
  
  if (ds.type === 'table' && ds.datasourceId) {
    loadTableList(ds.datasourceId)
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    
    saving.value = true
    
    // 验证数据集名称唯一性
    const exists = datasets.value.some(
      ds => ds.name === formData.value.name && ds.id !== formData.value.id
    )
    
    if (exists) {
      ElMessage.error('数据集名称已存在')
      return
    }
    
    if (formData.value.id) {
      // 更新
      const index = datasets.value.findIndex(ds => ds.id === formData.value.id)
      if (index > -1) {
        datasets.value[index] = { ...formData.value }
      }
      ElMessage.success('更新成功')
    } else {
      // 新增
      const newDataset = {
        ...formData.value,
        id: `ds_${Date.now()}`,
        createdAt: new Date().toISOString()
      }
      datasets.value.push(newDataset)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    saveToLocal()
  } catch (error) {
    if (error !== false) { // 排除表单验证失败
      console.error('保存数据集失败', error)
    }
  } finally {
    saving.value = false
  }
}

// 删除数据集
const deleteDataset = (id) => {
  ElMessageBox.confirm('确定要删除该数据集吗？', '提示', {
    type: 'warning'
  }).then(() => {
    const index = datasets.value.findIndex(ds => ds.id === id)
    if (index > -1) {
      datasets.value.splice(index, 1)
      ElMessage.success('删除成功')
      saveToLocal()
    }
  })
}

// 设为默认数据集
const setDefaultDataset = (ds) => {
  datasets.value.forEach(d => {
    d.isDefault = (d.id === ds.id)
  })
  ElMessage.success('已设为默认数据集')
  saveToLocal()
}

// 测试数据集
const testDataset = async (ds) => {
  ElMessage.info('测试功能开发中...')
  // TODO: 实现数据集测试功能
}

// 重置对话框
const resetDialog = () => {
  formRef.value?.resetFields()
  formData.value = {
    id: '',
    name: '',
    type: 'table',
    datasourceId: '',
    tableName: '',
    sql: '',
    description: '',
    fields: [],
    isDefault: false
  }
}

// 保存到本地存储
const saveToLocal = () => {
  localStorage.setItem('report_datasets', JSON.stringify(datasets.value))
}

// 从本地存储加载
const loadFromLocal = () => {
  const saved = localStorage.getItem('report_datasets')
  if (saved) {
    try {
      datasets.value = JSON.parse(saved)
    } catch (error) {
      console.error('加载数据集失败', error)
    }
  }
}

// 获取字段类型标签
const getFieldTypeTag = (type) => {
  const typeLower = (type || '').toLowerCase()
  if (typeLower.includes('int') || typeLower.includes('decimal') || typeLower.includes('float')) {
    return 'success'
  } else if (typeLower.includes('date')) {
    return 'warning'
  } else {
    return 'info'
  }
}

// 获取字段类型图标
const getFieldTypeIcon = (type) => {
  const typeLower = (type || '').toLowerCase()
  if (typeLower.includes('int') || typeLower.includes('decimal') || typeLower.includes('float')) {
    return 'Money'
  } else if (typeLower.includes('date')) {
    return 'Calendar'
  } else {
    return 'Document'
  }
}

onMounted(() => {
  loadFromLocal()
  loadDatasources()
})
</script>

<style scoped>
.dataset-manager {
  padding: 20px;
}

.dataset-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dataset-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.dataset-name {
  font-weight: 600;
  font-size: 14px;
}

.dataset-content {
  padding: 12px;
}

.dataset-info {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  margin-bottom: 12px;
  line-height: 1.5;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  width: 100px;
  color: #909399;
  flex-shrink: 0;
}

.value {
  color: #303133;
  flex: 1;
}

.sql-content {
  flex: 1;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
}

.sql-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.field-list {
  display: flex;
  flex-wrap: wrap;
  margin-top: 8px;
}

.dataset-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.form-tip {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
