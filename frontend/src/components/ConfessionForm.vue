<template>
  <div class="confession-form">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            发布树洞
          </span>
          <el-tag type="warning" size="small">匿名发布</el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
      >
        <el-form-item label="标题（可选）" prop="title">
          <el-input
            v-model="form.title"
            placeholder="给心事加个标题吧~"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            maxlength="2000"
            show-word-limit
            placeholder="在这里写下你的心事、吐槽、秘密...（匿名发布，不会显示你的身份信息）"
          />
        </el-form-item>

        <el-form-item>
          <div class="form-actions">
            <el-alert
              title="温馨提示"
              type="info"
              :closable="false"
              show-icon
              class="tips-alert"
            >
              <template #default>
                <ul class="tips-list">
                  <li>发布后不会显示你的身份信息</li>
                  <li>请遵守社区规范，文明发言</li>
                  <li>不要发布广告、色情、暴力等不当内容</li>
                </ul>
              </template>
            </el-alert>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 19l7-7 3 3-7 7-3-3z" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 2l7.586 7.586" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="11" cy="11" r="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              发布
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import treeholeApi from '@/api/treehole'

const emit = defineEmits(['submitted'])

const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  title: '',
  content: ''
})

const rules = {
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 1, max: 2000, message: '内容长度请在 1-2000 字之间', trigger: 'blur' }
  ]
}

// 提交发布
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const result = await treeholeApi.create({
        title: form.title || null,
        content: form.content
      })

      if (result.success) {
        ElMessage.success('发布成功')
        // 清空表单
        form.title = ''
        form.content = ''
        // 通知父组件
        emit('submitted', result.data)
      }
    } catch (error) {
      console.error('发布失败:', error)
      const message = error.detail?.message || error.message || '发布失败'
      ElMessage.error(message)
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  form.title = ''
  form.content = ''
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 暴露方法给父组件
defineExpose({
  resetForm
})
</script>

<style scoped>
.confession-form {
  margin-bottom: 24px;
}

.form-card {
  border-radius: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.icon {
  width: 20px;
  height: 20px;
  color: #6366f1;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  width: 100%;
}

.tips-alert {
  flex: 1;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.8;
}

.tips-list li {
  color: #64748b;
}

.el-button {
  flex-shrink: 0;
  min-width: 100px;
}

.btn-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  vertical-align: middle;
}
</style>
