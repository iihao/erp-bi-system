<template>
  <div class="messages-page">
    <el-card class="messages-card">
      <template #header>
        <div class="card-header">
          <span class="title">消息中心</span>
          <div class="header-actions">
            <el-button
              v-if="selectedMessages.length > 0"
              type="primary"
              size="small"
              @click="batchMarkAsRead"
            >
              标记已读
            </el-button>
            <el-button
              v-if="selectedMessages.length > 0"
              type="danger"
              size="small"
              @click="batchDelete"
            >
              删除
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="markAllAsRead"
            >
              一键已读
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="showComposeDialog = true"
            >
              写信
            </el-button>
          </div>
        </div>
      </template>

      <!-- 消息类型切换 -->
      <el-tabs v-model="activeTab" @tab-change="loadMessages">
        <el-tab-pane name="all">
          <template #label>
            <span>
              全部消息
              <el-badge
                v-if="unreadStats.total_unread > 0"
                :value="unreadStats.total_unread"
                :max="99"
                class="tab-badge"
              />
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="private">
          <template #label>
            <span>
              私信
              <el-badge
                v-if="unreadStats.private_unread > 0"
                :value="unreadStats.private_unread"
                :max="99"
                class="tab-badge"
              />
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="system">
          <template #label>
            <span>
              系统通知
              <el-badge
                v-if="unreadStats.system_unread > 0"
                :value="unreadStats.system_unread"
                :max="99"
                class="tab-badge"
              />
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane name="interaction">
          <template #label>
            <span>
              互动通知
              <el-badge
                v-if="unreadStats.interaction_unread > 0"
                :value="unreadStats.interaction_unread"
                :max="99"
                class="tab-badge"
              />
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <!-- 消息列表 -->
      <div class="message-list">
        <el-empty v-if="messages.length === 0" description="暂无消息" />
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'is-read': message.is_read, 'is-selected': selectedMessages.includes(message.id) }]"
          @click="toggleSelect(message.id)"
        >
          <div class="message-avatar">
            <el-avatar
              v-if="message.message_type === 'private' && message.sender_avatar"
              :src="message.sender_avatar"
              :size="40"
            />
            <el-avatar
              v-else-if="message.message_type === 'system'"
              :size="40"
              style="background-color: #e6a23c"
            >
              <el-icon><Bell /></el-icon>
            </el-avatar>
            <el-avatar
              v-else
              :size="40"
              style="background-color: #409eff"
            >
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender-name">{{ getSenderName(message) }}</span>
              <span v-if="!message.is_read" class="unread-dot" />
              <span class="message-time">{{ formatTime(message.created_at) }}</span>
            </div>
            <div class="message-title">{{ message.title }}</div>
            <div class="message-preview">{{ truncateContent(message.content) }}</div>
            <div class="message-actions" @click.stop>
              <el-button
                v-if="!message.is_read"
                type="primary"
                link
                size="small"
                @click="markSingleAsRead(message.id)"
              >
                标记已读
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                @click="deleteSingleMessage(message.id)"
              >
                删除
              </el-button>
              <el-button
                v-if="message.message_type === 'private' && message.sender_id !== currentUserId"
                type="primary"
                link
                size="small"
                @click="replyMessage(message)"
              >
                回复
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadMessages"
        @size-change="loadMessages"
        class="pagination"
      />
    </el-card>

    <!-- 写信对话框 -->
    <el-dialog
      v-model="showComposeDialog"
      title="发送私信"
      width="500px"
      @close="resetComposeForm"
    >
      <el-form
        ref="composeFormRef"
        :model="composeForm"
        :rules="composeRules"
        label-width="80px"
      >
        <el-form-item label="收件人" prop="receiver_id">
          <el-input
            v-model="composeForm.receiver_id"
            placeholder="请输入用户 ID"
            type="number"
          />
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="composeForm.title"
            placeholder="请输入消息标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="composeForm.content"
            type="textarea"
            :rows="6"
            placeholder="请输入消息内容"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showComposeDialog = false">取消</el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending">
          发送
        </el-button>
      </template>
    </el-dialog>

    <!-- 回复对话框 -->
    <el-dialog
      v-model="showReplyDialog"
      title="回复私信"
      width="500px"
    >
      <el-form
        ref="replyFormRef"
        :model="replyForm"
        :rules="replyRules"
        label-width="80px"
      >
        <el-form-item label="收件人" prop="receiver_name">
          <el-input
            v-model="replyForm.receiver_name"
            disabled
          />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="replyForm.content"
            type="textarea"
            :rows="6"
            placeholder="请输入回复内容"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReplyDialog = false">取消</el-button>
        <el-button type="primary" @click="sendReply" :loading="sending">
          发送
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Bell, ChatDotRound } from '@element-plus/icons-vue'

export default {
  name: 'MessagesPage',
  components: {
    Bell,
    ChatDotRound
  },
  data() {
    return {
      activeTab: 'all',
      messages: [],
      currentPage: 1,
      pageSize: 20,
      total: 0,
      selectedMessages: [],
      unreadStats: {
        total_unread: 0,
        private_unread: 0,
        system_unread: 0,
        interaction_unread: 0
      },
      showComposeDialog: false,
      showReplyDialog: false,
      sending: false,
      composeForm: {
        receiver_id: '',
        title: '',
        content: ''
      },
      composeRules: {
        receiver_id: [
          { required: true, message: '请输入收件人 ID', trigger: 'blur' }
        ],
        title: [
          { required: true, message: '请输入消息标题', trigger: 'blur' },
          { max: 200, message: '标题不能超过 200 字', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入消息内容', trigger: 'blur' },
          { max: 5000, message: '内容不能超过 5000 字', trigger: 'blur' }
        ]
      },
      replyForm: {
        receiver_id: '',
        receiver_name: '',
        title: '回复：',
        content: ''
      },
      replyRules: {
        content: [
          { required: true, message: '请输入回复内容', trigger: 'blur' }
        ]
      },
      currentUserId: null
    }
  },
  mounted() {
    this.currentUserId = parseInt(localStorage.getItem('user_id') || '0')
    this.loadMessages()
    this.loadUnreadStats()
  },
  methods: {
    async loadMessages() {
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize
        }
        if (this.activeTab !== 'all') {
          params.message_type = this.activeTab
        }

        const response = await this.$api.messages.getList(params)
        if (response.success) {
          this.messages = response.data.list
          this.total = response.data.total
          if (response.data.unread_stats) {
            this.unreadStats = response.data.unread_stats
          }
        }
      } catch (error) {
        this.$message.error('加载消息失败：' + (error.message || '未知错误'))
      }
    },
    async loadUnreadStats() {
      try {
        const response = await this.$api.messages.getUnreadCount()
        if (response.success) {
          this.unreadStats = {
            total_unread: response.data.total || 0,
            private_unread: response.data.private || 0,
            system_unread: response.data.system || 0,
            interaction_unread: response.data.interaction || 0
          }
        }
      } catch (error) {
        console.error('获取未读统计失败:', error)
      }
    },
    getSenderName(message) {
      if (message.message_type === 'system') {
        return '系统通知'
      }
      if (message.message_type === 'interaction') {
        const typeMap = {
          like: '点赞通知',
          comment: '评论通知',
          follow: '关注通知'
        }
        return typeMap[message.source_type] || '互动通知'
      }
      return message.sender_name || `用户${message.sender_id}`
    },
    truncateContent(content, length = 100) {
      if (!content) return ''
      if (content.length <= length) return content
      return content.substring(0, length) + '...'
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      const date = new Date(timeStr)
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      if (hours < 24) return `${hours}小时前`
      if (days < 30) return `${days}天前`

      return date.toLocaleDateString('zh-CN')
    },
    toggleSelect(messageId) {
      const index = this.selectedMessages.indexOf(messageId)
      if (index > -1) {
        this.selectedMessages.splice(index, 1)
      } else {
        this.selectedMessages.push(messageId)
      }
    },
    async markSingleAsRead(messageId) {
      try {
        await this.$api.messages.markAsRead([messageId])
        this.$message.success('标记成功')
        this.loadMessages()
        this.loadUnreadStats()
      } catch (error) {
        this.$message.error('标记失败：' + (error.message || '未知错误'))
      }
    },
    async deleteSingleMessage(messageId) {
      this.$confirm('确定要删除这条消息吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await this.$api.messages.delete([messageId])
          this.$message.success('删除成功')
          this.loadMessages()
        } catch (error) {
          this.$message.error('删除失败：' + (error.message || '未知错误'))
        }
      }).catch(() => {})
    },
    async batchMarkAsRead() {
      if (this.selectedMessages.length === 0) {
        this.$message.warning('请选择要标记的消息')
        return
      }
      try {
        await this.$api.messages.markAsRead(this.selectedMessages)
        this.$message.success('标记成功')
        this.selectedMessages = []
        this.loadMessages()
        this.loadUnreadStats()
      } catch (error) {
        this.$message.error('标记失败：' + (error.message || '未知错误'))
      }
    },
    async batchDelete() {
      if (this.selectedMessages.length === 0) {
        this.$message.warning('请选择要删除的消息')
        return
      }
      this.$confirm(`确定要删除选中的 ${this.selectedMessages.length} 条消息吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await this.$api.messages.delete(this.selectedMessages)
          this.$message.success('删除成功')
          this.selectedMessages = []
          this.loadMessages()
        } catch (error) {
          this.$message.error('删除失败：' + (error.message || '未知错误'))
        }
      }).catch(() => {})
    },
    async markAllAsRead() {
      const messageType = this.activeTab === 'all' ? null : this.activeTab
      try {
        await this.$api.messages.readAll(messageType)
        this.$message.success('操作成功')
        this.loadMessages()
        this.loadUnreadStats()
      } catch (error) {
        this.$message.error('操作失败：' + (error.message || '未知错误'))
      }
    },
    replyMessage(message) {
      this.replyForm = {
        receiver_id: message.sender_id,
        receiver_name: message.sender_name || `用户${message.sender_id}`,
        title: `回复：${message.title}`,
        content: ''
      }
      this.showReplyDialog = true
    },
    resetComposeForm() {
      this.composeForm = {
        receiver_id: '',
        title: '',
        content: ''
      }
      if (this.$refs.composeFormRef) {
        this.$refs.composeFormRef.clearValidate()
      }
    },
    async sendMessage() {
      if (!this.$refs.composeFormRef) return

      await this.$refs.composeFormRef.validate(async (valid) => {
        if (!valid) return

        this.sending = true
        try {
          await this.$api.messages.send({
            receiver_id: parseInt(this.composeForm.receiver_id),
            title: this.composeForm.title,
            content: this.composeForm.content
          })
          this.$message.success('发送成功')
          this.showComposeDialog = false
          this.resetComposeForm()
          this.loadMessages()
          this.loadUnreadStats()
        } catch (error) {
          this.$message.error('发送失败：' + (error.message || error.detail?.message || '未知错误'))
        } finally {
          this.sending = false
        }
      })
    },
    async sendReply() {
      if (!this.$refs.replyFormRef) return

      await this.$refs.replyFormRef.validate(async (valid) => {
        if (!valid) return

        this.sending = true
        try {
          await this.$api.messages.send({
            receiver_id: parseInt(this.replyForm.receiver_id),
            title: this.replyForm.title,
            content: this.replyForm.content
          })
          this.$message.success('回复成功')
          this.showReplyDialog = false
          this.loadMessages()
        } catch (error) {
          this.$message.error('回复失败：' + (error.message || error.detail?.message || '未知错误'))
        } finally {
          this.sending = false
        }
      })
    }
  }
}
</script>

<style scoped>
.messages-page {
  padding: 20px;
}

.messages-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.tab-badge {
  margin-left: 8px;
}

.message-list {
  margin-top: 10px;
}

.message-item {
  display: flex;
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.message-item:hover {
  background-color: #f5f7fa;
}

.message-item.is-selected {
  background-color: #ecf5ff;
}

.message-item:not(.is-read) {
  background-color: #fff9f0;
}

.message-item:not(.is-read):hover {
  background-color: #fff3e0;
}

.message-avatar {
  margin-right: 15px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.sender-name {
  font-weight: 500;
  color: #303133;
  margin-right: 10px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background-color: #f56c6c;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.message-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
}

.message-preview {
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>
