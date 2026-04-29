<template>
  <div class="comment-form">
    <el-input
      v-model="content"
      type="textarea"
      :rows="rows"
      :placeholder="placeholder"
      :maxlength="2000"
      show-word-limit
      :disabled="loading"
      class="comment-input"
    />
    <div class="form-actions">
      <el-button
        v-if="showCancel"
        @click="handleCancel"
        :disabled="loading"
      >
        取消
      </el-button>
      <el-button
        type="primary"
        @click="handleSubmit"
        :loading="loading"
        :disabled="!content.trim()"
      >
        {{ submitText }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import commentsApi from '@/api/comments'

const { create: createComment, update: updateComment } = commentsApi

const props = defineProps({
  targetType: {
    type: String,
    required: true,
    validator: (val) => ['post', 'report'].includes(val)
  },
  targetId: {
    type: Number,
    required: true
  },
  parentId: {
    type: Number,
    default: 0
  },
  commentData: {
    type: Object,
    default: null
  },
  rows: {
    type: Number,
    default: 3
  },
  showCancel: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '写下你的评论...'
  }
})

const emit = defineEmits(['submitted', 'cancelled'])

const content = ref('')
const loading = ref(false)

const submitText = props.commentData ? '保存' : '发布'

// 监听编辑数据
watch(() => props.commentData, (newVal) => {
  if (newVal) {
    content.value = newVal.content
  } else {
    content.value = ''
  }
}, { immediate: true })

// 提交评论
const handleSubmit = async () => {
  if (!content.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  loading.value = true
  try {
    let result
    if (props.commentData) {
      // 编辑评论
      result = await updateComment(props.commentData.comment_id, {
        content: content.value.trim()
      })
    } else {
      // 创建评论
      result = await createComment({
        target_type: props.targetType,
        target_id: props.targetId,
        content: content.value.trim(),
        parent_id: props.parentId
      })
    }

    ElMessage.success(props.commentData ? '编辑成功' : '评论成功')
    emit('submitted', result.data)
    content.value = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  content.value = ''
  emit('cancelled')
}

// 暴露重置方法
const reset = () => {
  content.value = ''
}

defineExpose({ reset })
</script>

<style scoped>
.comment-form {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.comment-input {
  margin-bottom: 12px;
}

.comment-input :deep(.el-textarea__inner) {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
