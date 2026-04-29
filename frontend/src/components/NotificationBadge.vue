<template>
  <el-badge
    :value="unreadCount"
    :hidden="unreadCount === 0"
    :max="99"
    class="notification-badge"
    @click="handleClick"
  >
    <el-button
      :icon="icon"
      :type="type"
      :circle="circle"
      :size="size"
      :class="{ 'has-unread': unreadCount > 0 }"
    />
  </el-badge>
</template>

<script>
export default {
  name: 'NotificationBadge',
  props: {
    icon: {
      type: String,
      default: 'Bell'
    },
    type: {
      type: String,
      default: 'info'
    },
    circle: {
      type: Boolean,
      default: true
    },
    size: {
      type: String,
      default: 'default'
    },
    messageType: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      unreadCount: 0,
      pollingTimer: null
    }
  },
  mounted() {
    this.fetchUnreadCount()
    // 每 30 秒轮询一次未读消息
    this.startPolling()
  },
  beforeUnmount() {
    this.stopPolling()
  },
  methods: {
    async fetchUnreadCount() {
      try {
        const response = await this.$api.messages.getUnreadCount()
        if (response.success) {
          if (this.messageType) {
            this.unreadCount = response.data[this.messageType] || 0
          } else {
            this.unreadCount = response.data.total || 0
          }
        }
      } catch (error) {
        console.error('获取未读消息失败:', error)
      }
    },
    startPolling() {
      this.pollingTimer = setInterval(() => {
        this.fetchUnreadCount()
      }, 30000)
    },
    stopPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    },
    handleClick() {
      this.$emit('click')
      // 默认跳转到消息页面
      if (this.$router) {
        this.$router.push('/admin/messages')
      }
    },
    // 外部调用，刷新未读数
    refresh() {
      this.fetchUnreadCount()
    }
  }
}
</script>

<style scoped>
.notification-badge {
  cursor: pointer;
}

.notification-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
}

.notification-badge .has-unread {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}
</style>
