<template>
  <div class="follow-component">
    <el-button
      :type="buttonType"
      :class="['follow-btn', { 'following': isFollowing }]"
      :loading="loading"
      :disabled="disabled"
      @click="toggleFollow"
      :plain="!isFollowing"
    >
      <template #icon>
        <svg class="follow-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
      </template>
      {{ isFollowing ? '已关注' : '关注' }}
      <span class="follower-count" v-if="showCount">{{ followerCount }}</span>
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps({
  // 目标用户 ID
  userId: {
    type: [Number, String],
    required: true
  },
  // 初始是否已关注
  initialFollowing: {
    type: Boolean,
    default: false
  },
  // 初始粉丝数
  initialFollowerCount: {
    type: Number,
    default: 0
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 显示计数
  showCount: {
    type: Boolean,
    default: true
  },
  // 按钮大小
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  }
})

const emit = defineEmits(['follow-change', 'count-change'])

const loading = ref(false)
const isFollowing = ref(props.initialFollowing)
const followerCount = ref(props.initialFollowerCount)

const buttonType = computed(() => {
  return isFollowing.value ? 'success' : 'primary'
})

// 监听初始值变化
watch(() => props.initialFollowing, (newVal) => {
  isFollowing.value = newVal
})

watch(() => props.initialFollowerCount, (newVal) => {
  followerCount.value = newVal
})

// 切换关注状态
const toggleFollow = async () => {
  if (loading.value || disabled.value) return

  loading.value = true

  try {
    if (isFollowing.value) {
      // 取消关注
      await api.follows.unfollow(parseInt(props.userId))
      followerCount.value--
      isFollowing.value = false
      ElMessage.success('已取消关注')
    } else {
      // 关注
      await api.follows.follow({
        followed_id: parseInt(props.userId)
      })
      followerCount.value++
      isFollowing.value = true
      ElMessage.success('关注成功')
    }

    // 触发自定义事件
    emit('follow-change', {
      userId: props.userId,
      isFollowing: isFollowing.value,
      followerCount: followerCount.value
    })
    emit('count-change', followerCount.value)

  } catch (error) {
    console.error('关注操作失败:', error)
    const message = error.detail?.message || error.message || '操作失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 刷新关注状态
const refreshStatus = async () => {
  try {
    const result = await api.follows.getStatus(parseInt(props.userId))
    if (result.success) {
      followerCount.value = result.data.follower_count
      isFollowing.value = result.data.is_following
    }
  } catch (error) {
    console.error('获取关注状态失败:', error)
  }
}

// 暴露方法给父组件
defineExpose({
  refreshStatus
})
</script>

<style scoped>
.follow-component {
  display: inline-block;
}

.follow-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 20px;
  padding: 8px 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.follow-btn:hover {
  transform: scale(1.05);
}

.follow-btn.following {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: #16a34a;
  color: #ffffff;
}

.follow-btn.following:hover {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  border-color: #15803d;
}

.follow-icon {
  width: 18px;
  height: 18px;
  transition: all 0.3s ease;
  color: currentColor;
}

.follow-btn:not(.following) .follow-icon {
  color: #3b82f6;
}

.follow-btn.following .follow-icon {
  color: #ffffff;
  animation: followPulse 0.5s ease-in-out;
}

@keyframes followPulse {
  0% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.2);
  }
  50% {
    transform: scale(0.9);
  }
  75% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.follower-count {
  font-size: 14px;
  font-weight: 500;
  min-width: 20px;
  text-align: center;
  margin-left: 4px;
}

.follow-btn.following .follower-count {
  color: #ffffff;
}

.follow-btn:not(.following) .follower-count {
  color: #6b7280;
}

/* 小尺寸 */
.follow-btn.small {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
}

.follow-btn.small .follow-icon {
  width: 14px;
  height: 14px;
}

.follow-btn.small .follower-count {
  font-size: 12px;
}

/* 大尺寸 */
.follow-btn.large {
  padding: 10px 20px;
  border-radius: 24px;
  font-size: 16px;
}

.follow-btn.large .follow-icon {
  width: 22px;
  height: 22px;
}

.follow-btn.large .follower-count {
  font-size: 16px;
}
</style>
