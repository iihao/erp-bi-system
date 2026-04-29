<template>
  <div class="comment-item" :class="{ 'reply-item': isReply }">
    <div class="comment-avatar">
      <el-avatar
        :src="comment.avatar_url || '/default-avatar.png'"
        :size="40"
        shape="circle"
      />
    </div>
    <div class="comment-content">
      <div class="comment-header">
        <span class="username">{{ comment.username }}</span>
        <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
        <span v-if="comment.updated_at !== comment.created_at" class="edited-tag">
          (已编辑)
        </span>
      </div>
      <div class="comment-text">{{ comment.content }}</div>
      <div class="comment-actions">
        <el-button
          link
          type="primary"
          size="small"
          @click="handleReply"
          :disabled="isEditing"
        >
          回复
        </el-button>
        <el-button
          link
          type="primary"
          size="small"
          @click="handleLike"
          :disabled="isEditing"
        >
          <el-icon v-if="comment.user_liked"><StarFilled /></el-icon>
          <el-icon v-else><Star /></el-icon>
          {{ comment.like_count }}
        </el-button>
        <template v-if="canEdit">
          <el-button
            link
            type="primary"
            size="small"
            @click="handleEdit"
            :disabled="isEditing"
          >
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除这条评论吗？"
            @confirm="handleDelete"
          >
            <template #reference>
              <el-button
                link
                type="danger"
                size="small"
                :disabled="isEditing"
              >
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
        <span v-if="comment.reply_count > 0" class="reply-count">
          {{ comment.reply_count }} 条回复
        </span>
      </div>

      <!-- 编辑表单 -->
      <div v-if="isEditing" class="edit-form">
        <CommentForm
          :target-type="targetType"
          :target-id="targetId"
          :comment-data="comment"
          :show-cancel="true"
          @submitted="onEditComplete"
          @cancelled="isEditing = false"
        />
      </div>

      <!-- 回复表单 -->
      <div v-if="showReplyForm" class="reply-form">
        <CommentForm
          :target-type="targetType"
          :target-id="targetId"
          :parent-id="comment.comment_id"
          :rows="2"
          :show-cancel="true"
          :placeholder="`回复 @${comment.username}...`"
          @submitted="onReplyComplete"
          @cancelled="showReplyForm = false"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import commentsApi from '@/api/comments'
import CommentForm from './CommentForm.vue'

const { like: likeComment, unlike: unlikeComment, delete: deleteComment } = commentsApi

const props = defineProps({
  comment: {
    type: Object,
    required: true
  },
  targetType: {
    type: String,
    required: true
  },
  targetId: {
    type: Number,
    required: true
  },
  currentUserId: {
    type: Number,
    default: null
  },
  isReply: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['reply', 'edit', 'delete', 'like'])

const isEditing = ref(false)
const showReplyForm = ref(false)

// 判断是否可以编辑/删除
const canEdit = computed(() => {
  return props.currentUserId && props.currentUserId === props.comment.user_id
})

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day
  const year = 12 * month

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < month) {
    return `${Math.floor(diff / day)}天前`
  } else if (diff < year) {
    return `${Math.floor(diff / month)}个月前`
  } else {
    return `${Math.floor(diff / year)}年前`
  }
}

// 回复
const handleReply = () => {
  showReplyForm.value = true
}

// 点赞
const handleLike = async () => {
  try {
    if (props.comment.user_liked) {
      await unlikeComment(props.comment.comment_id)
    } else {
      await likeComment(props.comment.comment_id)
    }
    emit('like', props.comment.comment_id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail?.message || '操作失败')
  }
}

// 编辑
const handleEdit = () => {
  isEditing.value = true
}

// 编辑完成
const onEditComplete = (updatedComment) => {
  isEditing.value = false
  emit('edit', updatedComment)
}

// 回复完成
const onReplyComplete = (newReply) => {
  showReplyForm.value = false
  emit('reply', newReply)
}

// 删除
const handleDelete = async () => {
  try {
    await deleteComment(props.comment.comment_id)
    ElMessage.success('删除成功')
    emit('delete', props.comment.comment_id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail?.message || '删除失败')
  }
}
</script>

<style scoped>
.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.reply-item {
  background: #fafafa;
  border-radius: 4px;
  margin-top: 8px;
}

.comment-avatar {
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.username {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.comment-time {
  color: #999;
  font-size: 12px;
}

.edited-tag {
  color: #999;
  font-size: 12px;
  font-style: italic;
}

.comment-text {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  word-break: break-word;
}

.comment-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.reply-count {
  color: #409eff;
  font-size: 12px;
  cursor: pointer;
  margin-left: 8px;
}

.reply-count:hover {
  text-decoration: underline;
}

.edit-form,
.reply-form {
  margin-top: 12px;
}
</style>
