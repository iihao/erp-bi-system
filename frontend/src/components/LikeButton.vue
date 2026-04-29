<template>
  <div class="like-component">
    <el-button
      :type="buttonType"
      :class="['like-btn', { 'liked': isLiked }]"
      :loading="loading"
      :disabled="disabled"
      @click="toggleLike"
      circle
    >
      <template #icon>
        <svg class="like-icon" viewBox="0 0 24 24" :class="{ 'icon-liked': isLiked }" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </template>
      <span class="like-count" v-if="showCount">{{ count }}</span>
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps({
  // 目标类型：post, comment, report
  targetType: {
    type: String,
    required: true,
    validator: (value) => ['post', 'comment', 'report'].includes(value)
  },
  // 目标 ID
  targetId: {
    type: [Number, String],
    required: true
  },
  // 初始点赞数
  initialCount: {
    type: Number,
    default: 0
  },
  // 是否已点赞
  initialLiked: {
    type: Boolean,
    default: false
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

const emit = defineEmits(['like-change', 'count-change'])

const loading = ref(false)
const count = ref(props.initialCount)
const isLiked = ref(props.initialLiked)

const buttonType = computed(() => {
  return isLiked.value ? 'danger' : 'info'
})

// 监听初始值变化
watch(() => props.initialCount, (newVal) => {
  count.value = newVal
})

watch(() => props.initialLiked, (newVal) => {
  isLiked.value = newVal
})

// 切换点赞状态
const toggleLike = async () => {
  if (loading.value || disabled.value) return

  loading.value = true

  try {
    if (isLiked.value) {
      // 取消点赞
      await api.likes.unlike(props.targetType, props.targetId)
      count.value--
      isLiked.value = false
      ElMessage.success('已取消点赞')
    } else {
      // 点赞
      await api.likes.like({
        target_type: props.targetType,
        target_id: parseInt(props.targetId)
      })
      count.value++
      isLiked.value = true
      ElMessage.success('点赞成功')
    }

    // 触发自定义事件
    emit('like-change', {
      targetType: props.targetType,
      targetId: props.targetId,
      isLiked: isLiked.value,
      count: count.value
    })
    emit('count-change', count.value)

  } catch (error) {
    console.error('点赞操作失败:', error)
    const message = error.detail?.message || error.message || '操作失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 刷新点赞状态
const refreshStatus = async () => {
  try {
    const result = await api.likes.getStatus({
      target_type: props.targetType,
      target_id: props.targetId
    })
    count.value = result.count
    isLiked.value = result.user_liked
  } catch (error) {
    console.error('获取点赞状态失败:', error)
  }
}

// 暴露方法给父组件
defineExpose({
  refreshStatus
})
</script>

<style scoped>
.like-component {
  display: inline-block;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-radius: 20px;
  padding: 6px 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.like-btn:hover {
  transform: scale(1.05);
}

.like-btn.liked {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-color: #dc2626;
  color: #ffffff;
}

.like-btn.liked:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  border-color: #b91c1c;
}

.like-icon {
  width: 18px;
  height: 18px;
  transition: all 0.3s ease;
  color: currentColor;
}

.like-btn:not(.liked) .like-icon {
  color: #9ca3af;
}

.like-btn.liked .like-icon {
  color: #ffffff;
  animation: heartBeat 0.5s ease-in-out;
}

@keyframes heartBeat {
  0% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.3);
  }
  50% {
    transform: scale(0.9);
  }
  75% {
    transform: scale(1.15);
  }
  100% {
    transform: scale(1);
  }
}

.like-count {
  font-size: 14px;
  font-weight: 500;
  min-width: 20px;
  text-align: center;
}

.like-btn.liked .like-count {
  color: #ffffff;
}

.like-btn:not(.liked) .like-count {
  color: #6b7280;
}

/* 小尺寸 */
.like-btn.small {
  padding: 4px 8px;
  border-radius: 16px;
}

.like-btn.small .like-icon {
  width: 14px;
  height: 14px;
}

.like-btn.small .like-count {
  font-size: 12px;
}

/* 大尺寸 */
.like-btn.large {
  padding: 8px 16px;
  border-radius: 24px;
}

.like-btn.large .like-icon {
  width: 22px;
  height: 22px;
}

.like-btn.large .like-count {
  font-size: 16px;
}
</style>
