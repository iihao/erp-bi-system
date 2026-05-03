<template>
  <div class="ai-chat-fullscreen">
    <!-- 左侧对话列表 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <el-icon :size="22"><ChatDotRound /></el-icon>
          <span v-if="!sidebarCollapsed" class="logo-text">AI 对话</span>
        </div>
        <el-button
          text size="small"
          class="toggle-btn"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>

      <el-button type="primary" round @click="newConversation" class="new-conv-btn">
        <el-icon><Plus /></el-icon>
        <span v-if="!sidebarCollapsed">新对话</span>
      </el-button>

      <div class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: conv.id === currentConvId }"
          @click="switchConversation(conv.id)"
        >
          <el-icon class="conv-icon"><ChatLineRound /></el-icon>
          <span class="conv-title" v-if="!sidebarCollapsed">{{ conv.title }}</span>
          <el-button
            v-if="!sidebarCollapsed"
            text size="small"
            class="del-btn"
            @click.stop="deleteConversation(conv.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div v-if="conversations.length === 0" class="empty-text">暂无对话</div>
      </div>
    </aside>

    <!-- 右侧聊天区域 -->
    <main class="chat-main">
      <!-- 头部 -->
      <header class="chat-header">
        <div class="header-left">
          <el-button text class="mobile-menu-btn" @click="sidebarCollapsed = false" v-if="isMobile && sidebarCollapsed">
            <el-icon><Menu /></el-icon>
          </el-button>
          <span class="model-label">
            <el-icon><Cpu /></el-icon>
            <el-select v-model="selectedModel" size="small" class="model-select" @change="onModelChange">
              <el-option
                v-for="meta in modelList"
                :key="meta.key"
                :label="meta.label"
                :value="meta.key"
              />
            </el-select>
          </span>
        </div>
        <div class="header-right">
          <el-button text size="small" @click="clearCurrentChat">
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <!-- 欢迎屏幕 -->
        <div v-if="messages.length === 0 && !streaming" class="welcome-screen">
          <div class="welcome-icon">
            <el-icon :size="56" color="#60a5fa"><ChatDotRound /></el-icon>
          </div>
          <h2>有什么可以帮你的？</h2>
          <p>输入问题，AI 帮你解答</p>
          <div class="suggestion-grid">
            <div
              v-for="s in suggestions"
              :key="s"
              class="suggestion-item"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar :size="32" v-if="msg.role === 'user'">
                <el-icon><User /></el-icon>
              </el-avatar>
              <el-avatar :size="32" v-else class="ai-avatar">
                <el-icon><Cpu /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
              <div class="message-text" v-if="msg.role === 'user'">{{ msg.content }}</div>
              <div class="message-text markdown" v-else v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>

          <!-- 流式输出 -->
          <div v-if="streaming" class="message assistant streaming">
            <div class="message-avatar">
              <el-avatar :size="32" class="ai-avatar">
                <el-icon><Cpu /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-role">AI</div>
              <div class="message-text markdown" v-html="renderMarkdown(streamContent)"></div>
              <span class="typing-cursor"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="input-box">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="输入你的问题..."
            @keydown.enter.exact.prevent="sendMessage"
            class="chat-input"
            resize="none"
          />
          <el-button
            type="primary"
            circle
            @click="sendMessage"
            :disabled="!inputMessage.trim() || streaming"
            class="send-btn"
          >
            <el-icon><Top /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">
          <span>Enter 发送 · Shift+Enter 换行</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, ChatLineRound, Delete, ChatDotRound,
  User, Cpu, Top, Fold, Expand, Menu
} from '@element-plus/icons-vue'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

const conversations = ref([])
const currentConvId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const streaming = ref(false)
const streamContent = ref('')
const messagesContainer = ref(null)
const selectedModel = ref('')
const modelList = ref([])
const sidebarCollapsed = ref(false)
const isMobile = ref(false)

const suggestions = [
  '解释一下什么是 RESTful API',
  '帮我写一个 Python 快速排序',
  '什么是微服务架构',
  '如何做数据库设计',
  '解释 Git rebase 的用法',
  '什么是 Docker 容器化',
]

const renderMarkdown = (content) => {
  if (!content) return ''
  try { return marked.parse(content) } catch { return content }
}

const loadModels = async () => {
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch('/api/admin/ai-config/current', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    if (data.available_models) {
      modelList.value = Object.entries(data.available_models).map(([key, meta]) => ({
        key, label: meta.name || key,
      }))
      selectedModel.value = data.model || modelList.value[0]?.key || ''
    }
  } catch (e) {
    console.warn('加载模型列表失败', e)
  }
}

const loadConversations = async () => {
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch('/ai-chat/conversations', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    conversations.value = data.data || []
  } catch (e) {
    console.warn('加载对话列表失败', e)
  }
}

const switchConversation = async (convId) => {
  if (convId === currentConvId.value) return
  currentConvId.value = convId
  messages.value = []
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch(`/ai-chat/conversations/${convId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    messages.value = data.messages || []
    await nextTick()
    scrollToBottom()
  } catch (e) {
    ElMessage.error('加载对话失败')
  }
}

const newConversation = () => {
  currentConvId.value = null
  messages.value = []
}

const deleteConversation = async (convId) => {
  try {
    await ElMessageBox.confirm('确定删除该对话吗？', '提示', { type: 'warning' })
    const token = localStorage.getItem('token')
    await fetch(`/ai-chat/conversations/${convId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (currentConvId.value === convId) {
      currentConvId.value = null
      messages.value = []
    }
    await loadConversations()
    ElMessage.success('已删除')
  } catch (e) {
    // 取消
  }
}

const clearCurrentChat = () => {
  messages.value = []
  currentConvId.value = null
}

const useSuggestion = (text) => {
  inputMessage.value = text
  sendMessage()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || streaming.value) return

  const text = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({ role: 'user', content: text })
  await nextTick()
  scrollToBottom()

  streaming.value = true
  streamContent.value = ''

  try {
    const token = localStorage.getItem('token')
    const resp = await fetch('/ai-chat/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        conversation_id: currentConvId.value,
        message: text,
        model: selectedModel.value,
      }),
    })

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      throw new Error(errData.detail || errData.error?.message || '请求失败')
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event:')) continue
        if (line.startsWith('data:')) {
          const dataStr = line.slice(5).trim()
          if (!dataStr) continue
          try {
            const data = JSON.parse(dataStr)
            if (data.content !== undefined) {
              streamContent.value += data.content
              await nextTick()
              scrollToBottom()
            }
            if (data.id && data.is_new) {
              currentConvId.value = data.id
              await loadConversations()
            }
          } catch {
            // 忽略
          }
        }
      }
    }

    if (streamContent.value) {
      messages.value.push({ role: 'assistant', content: streamContent.value })
    }
    await loadConversations()
  } catch (error) {
    ElMessage.error('AI 回复失败：' + error.message)
  } finally {
    streaming.value = false
    streamContent.value = ''
  }
}

const onModelChange = () => {
  if (messages.value.length > 0) newConversation()
}

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadConversations()
  loadModels()
})
</script>

<style scoped>
.ai-chat-fullscreen {
  position: fixed;
  top: 60px;
  right: 0;
  bottom: 0;
  left: var(--sidebar-width);
  display: flex;
  background: #1e1e2e;
  z-index: 10;
}

/* 左侧栏 */
.sidebar {
  width: 260px;
  background: #181825;
  border-right: 1px solid #313244;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 0;
  border: none;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #313244;
  height: 52px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cdd6f4;
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
}

.toggle-btn {
  color: #a6adc8;
}

.toggle-btn:hover {
  color: #cdd6f4;
}

.new-conv-btn {
  margin: 10px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.conv-list::-webkit-scrollbar {
  width: 4px;
}

.conv-list::-webkit-scrollbar-thumb {
  background: #45475a;
  border-radius: 4px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  color: #bac2de;
}

.conv-item:hover {
  background: #313244;
}

.conv-item.active {
  background: #45475a;
  color: #cdd6f4;
}

.conv-icon {
  flex-shrink: 0;
  font-size: 16px;
  color: #a6adc8;
}

.conv-item.active .conv-icon {
  color: #89b4fa;
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.del-btn {
  opacity: 0;
  color: #f38ba8;
  flex-shrink: 0;
  padding: 0 2px;
}

.conv-item:hover .del-btn {
  opacity: 1;
}

.empty-text {
  text-align: center;
  color: #6c7086;
  font-size: 12px;
  padding: 20px 0;
}

/* 右侧主区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #1e1e2e;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  border-bottom: 1px solid #313244;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  color: #a6adc8;
}

.model-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a6adc8;
  font-size: 13px;
}

.model-select {
  width: 150px;
}

.model-select :deep(.el-input__wrapper) {
  background: #313244;
  border-color: #45475a;
}

.model-select :deep(.el-input__inner) {
  color: #cdd6f4;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right .el-button {
  color: #a6adc8;
}

.header-right .el-button:hover {
  color: #f38ba8;
}

/* 消息区域 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #45475a;
  border-radius: 4px;
}

/* 欢迎屏幕 */
.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.welcome-icon {
  margin-bottom: 16px;
}

.welcome-screen h2 {
  font-size: 24px;
  color: #cdd6f4;
  margin: 0 0 8px;
  font-weight: 700;
}

.welcome-screen p {
  color: #a6adc8;
  font-size: 14px;
  margin: 0 0 32px;
}

.suggestion-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-width: 520px;
  width: 100%;
}

.suggestion-item {
  padding: 10px 14px;
  background: #313244;
  border: 1px solid #45475a;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #bac2de;
  transition: all 0.15s;
  text-align: center;
}

.suggestion-item:hover {
  background: #45475a;
  color: #cdd6f4;
  border-color: #585b70;
}

/* 消息列表 */
.message-list {
  max-width: 740px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.ai-avatar {
  background: #313244 !important;
  color: #89b4fa !important;
  border: 1px solid #45475a;
}

.message-content {
  max-width: 80%;
  min-width: 0;
}

.message-role {
  font-size: 11px;
  font-weight: 600;
  color: #6c7086;
  margin-bottom: 4px;
}

.message.user .message-role {
  text-align: right;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message.user .message-text {
  background: #45475a;
  color: #cdd6f4;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: transparent;
  color: #cdd6f4;
  padding: 0;
  border-radius: 0;
}

/* Markdown */
.markdown :deep(p) { margin: 0 0 8px; }
.markdown :deep(p:last-child) { margin-bottom: 0; }
.markdown :deep(pre) {
  background: #181825;
  color: #cdd6f4;
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0;
  border: 1px solid #313244;
}
.markdown :deep(code) {
  background: #313244;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #f5c2e7;
}
.markdown :deep(pre code) { background: none; padding: 0; color: inherit; }
.markdown :deep(ul), .markdown :deep(ol) { margin: 8px 0; padding-left: 24px; }
.markdown :deep(li) { margin: 4px 0; }
.markdown :deep(blockquote) {
  border-left: 3px solid #89b4fa;
  padding: 4px 0 4px 12px;
  margin: 8px 0;
  color: #a6adc8;
}
.markdown :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; }
.markdown :deep(th), .markdown :deep(td) {
  border: 1px solid #45475a;
  padding: 8px 12px;
  text-align: left;
  font-size: 13px;
  color: #cdd6f4;
}
.markdown :deep(th) { background: #313244; font-weight: 600; }
.markdown :deep(strong) { color: #f5c2e7; }
.markdown :deep(h1), .markdown :deep(h2), .markdown :deep(h3) {
  color: #cdd6f4;
  margin: 16px 0 8px;
}
.markdown :deep(a) { color: #89b4fa; text-decoration: none; }
.markdown :deep(a:hover) { text-decoration: underline; }

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #89b4fa;
  animation: blink 0.8s infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 输入区 */
.input-area {
  padding: 12px 16px 16px;
  flex-shrink: 0;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 740px;
  margin: 0 auto;
  background: #313244;
  border: 1px solid #45475a;
  border-radius: 14px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.15s;
}

.input-box:focus-within {
  border-color: #89b4fa;
  box-shadow: 0 0 0 3px rgba(137, 180, 250, 0.15);
}

.chat-input { flex: 1; }

.chat-input :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 4px 0 !important;
  font-size: 14px;
  color: #cdd6f4;
  resize: none;
}

.chat-input :deep(.el-textarea__inner)::placeholder {
  color: #6c7086;
}

.send-btn {
  flex-shrink: 0;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: #6c7086;
  margin-top: 6px;
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-chat-fullscreen {
    left: 0;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    bottom: 0;
    z-index: 100;
    width: 280px;
  }

  .sidebar.collapsed {
    width: 0;
  }

  .suggestion-grid {
    grid-template-columns: 1fr;
  }

  .message-text {
    font-size: 13px;
  }
}
</style>
