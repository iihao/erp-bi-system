<template>
  <div class="confession-item">
    <div class="confession-header">
      <div class="user-info">
        <el-avatar
          :src="displayAvatar || defaultAvatar"
          :size="40"
          shape="circle"
          class="user-avatar"
        >
          <span class="avatar-text">{{ avatarText }}</span>
        </el-avatar>
        <div class="user-details">
          <span class="username">{{ confession.display_username }}</span>
          <span class="post-time">{{ formatTime(confession.created_at) }}</span>
        </div>
      </div>
      <div class="actions">
        <!-- 删除按钮（仅自己可见） -->
        <el-button
          v-if="showDelete"
          type="danger"
          size="small"
          text
          @click="handleDelete"
        >
          删除
        </el-button>
      </div>
    </div>

    <div class="confession-content">
      <h4 class="confession-title" v-if="confession.title">
        {{ confession.title }}
      </h4>
      <p class="confession-text">{{ confession.content }}</p>
    </div>

    <div class="confession-footer">
      <LikeButton
        :targetType="'post'"
        :targetId="confession.post_id"
        :initialCount="confession.like_count"
        :initialLiked="confession.user_liked"
        :showCount="true"
        size="small"
      />

      <span class="stat-item" @click="handleComment">
        <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ confession.comment_count }}
      </span>

      <span class="stat-item">
        <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ confession.view_count }}
      </span>
    </div>

    <!-- 评论区 -->
    <div v-if="showComments" class="comments-section">
      <CommentList
        :targetType="'post'"
        :targetId="confession.post_id"
        @close="showComments = false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import LikeButton from '@/components/LikeButton.vue'
import CommentList from '@/components/CommentList.vue'
import treeholeApi from '@/api/treehole'

const props = defineProps({
  confession: {
    type: Object,
    required: true
  },
  showDelete: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['deleted', 'comment'])

const defaultAvatar = 'https://ui-avatars.com/api/?name=Anonymous&background=6366f1&color=fff'
const showComments = ref(false)

const displayAvatar = computed(() => props.confession.display_avatar)

const avatarText = computed(() => {
  const name = props.confession.display_username || '匿名'
  return name.charAt(0).toUpperCase()
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

  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  if (diff < month) return `${Math.floor(diff / day)}天前`
  if (diff < year) return `${Math.floor(diff / month)}个月前`
  return `${Math.floor(diff / year)}年前`
}

// 删除树洞
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这条树洞吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const result = await treeholeApi.delete(props.confession.post_id)

    if (result.success) {
      ElMessage.success('删除成功')
      emit('deleted', props.confession.post_id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      const message = error.detail?.message || error.message || '删除失败'
      ElMessage.error(message)
    }
  }
}

// 查看评论
const handleComment = () => {
  showComments.value = !showComments.value
  emit('comment', props.confession)
}
</script>

<style scoped>
.confession-item {
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  transition: all 0.3s;
}

.confession-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: #6366f1;
}

.confession-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
}

.avatar-text {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.username {
  font-weight: 600;
  color: #1e293b;
  font-size: 15px;
}

.post-time {
  font-size: 13px;
  color: #94a3b8;
}

.confession-content {
  margin-bottom: 16px;
}

.confession-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.confession-text {
  font-size: 15px;
  color: #475569;
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.confession-footer {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  transition: color 0.2s;
}

.stat-item:hover {
  color: #6366f1;
}

.stat-icon {
  width: 18px;
  height: 18px;
  color: #94a3b8;
}

.stat-item:hover .stat-icon {
  color: #6366f1;
}

.comments-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}
</style>
