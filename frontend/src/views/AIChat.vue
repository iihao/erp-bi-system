<template>
  <div class="ai-chat-fullscreen" :class="{ dark: isDark }">
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
          <el-button text size="small" @click="toggleTheme" class="theme-btn" :title="isDark ? '切换亮色' : '切换暗色'">
            <el-icon><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </el-button>
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
  User, Cpu, Top, Fold, Expand, Menu, Sunny, Moon
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
const CONV_TYPE = 'chat'
const API_BASE = '/ai-chat/conversations'

const sidebarCollapsed = ref(false)
const isMobile = ref(false)
const isDark = ref(false)

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

const toggleTheme = () => {
  isDark.value = !isDark.value
  try { localStorage.setItem('ai-chat-theme', isDark.value ? 'dark' : 'light') } catch {}
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
    const resp = await fetch(`${API_BASE}?type=${CONV_TYPE}`, {
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
    const resp = await fetch(`${API_BASE}/${convId}?type=${CONV_TYPE}`, {
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
    await fetch(`${API_BASE}/${convId}?type=${CONV_TYPE}`, {
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
  try { const saved = localStorage.getItem('ai-chat-theme'); if (saved === 'dark') isDark.value = true } catch {}
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
  left: var(--sidebar-width, 200px);
  display: flex;
  z-index: 10;
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --sidebar-bg: #f1f5f9;
  --sidebar-border: #e2e8f0;
  --sidebar-text: #334155;
  --sidebar-text-muted: #64748b;
  --sidebar-hover: #e2e8f0;
  --sidebar-active: #dbeafe;
  --sidebar-active-icon: #3b82f6;
  --border-color: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --msg-user-bg: #3b82f6;
  --msg-user-text: #ffffff;
  --ai-avatar-bg: #dbeafe;
  --ai-avatar-color: #3b82f6;
  --ai-avatar-border: #e2e8f0;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --input-focus-border: #3b82f6;
  --input-focus-shadow: rgba(59, 130, 246, 0.15);
  --suggestion-bg: #ffffff;
  --suggestion-border: #e2e8f0;
  --suggestion-hover-bg: #dbeafe;
  --suggestion-hover-border: #3b82f6;
  --suggestion-hover-text: #1e40af;
  --code-bg: #f1f5f9;
  --code-color: #0f172a;
  --code-border: #e2e8f0;
  --inline-code-bg: #e2e8f0;
  --inline-code-color: #9d174d;
  --blockquote-border: #3b82f6;
  --blockquote-color: #64748b;
  --table-border: #e2e8f0;
  --table-header-bg: #f1f5f9;
  --scrollbar-thumb: #cbd5e1;
  --model-select-bg: #f1f5f9;
  --model-select-border: #e2e8f0;
  --del-color: #ef4444;
  --typing-cursor: #3b82f6;
  --strong-color: #9d174d;
  --link-color: #3b82f6;
  background: var(--bg-primary);
}

.ai-chat-fullscreen.dark {
  --bg-primary: #1e1e2e;
  --bg-secondary: #181825;
  --sidebar-bg: #181825;
  --sidebar-border: #313244;
  --sidebar-text: #cdd6f4;
  --sidebar-text-muted: #a6adc8;
  --sidebar-hover: #313244;
  --sidebar-active: #45475a;
  --sidebar-active-icon: #89b4fa;
  --border-color: #313244;
  --text-primary: #cdd6f4;
  --text-secondary: #bac2de;
  --text-muted: #6c7086;
  --msg-user-bg: #45475a;
  --msg-user-text: #cdd6f4;
  --ai-avatar-bg: #313244;
  --ai-avatar-color: #89b4fa;
  --ai-avatar-border: #45475a;
  --input-bg: #313244;
  --input-border: #45475a;
  --input-focus-border: #89b4fa;
  --input-focus-shadow: rgba(137, 180, 250, 0.15);
  --suggestion-bg: #313244;
  --suggestion-border: #45475a;
  --suggestion-hover-bg: #45475a;
  --suggestion-hover-border: #585b70;
  --suggestion-hover-text: #cdd6f4;
  --code-bg: #181825;
  --code-color: #cdd6f4;
  --code-border: #313244;
  --inline-code-bg: #313244;
  --inline-code-color: #f5c2e7;
  --blockquote-border: #89b4fa;
  --blockquote-color: #a6adc8;
  --table-border: #45475a;
  --table-header-bg: #313244;
  --scrollbar-thumb: #45475a;
  --model-select-bg: #313244;
  --model-select-border: #45475a;
  --del-color: #f38ba8;
  --typing-cursor: #89b4fa;
  --strong-color: #f5c2e7;
  --link-color: #89b4fa;
}

/* 左侧栏 */
.sidebar {
  width: 260px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease, background 0.3s ease, border-color 0.3s ease;
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
  border-bottom: 1px solid var(--sidebar-border);
  height: 52px;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--sidebar-text);
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
}

.toggle-btn {
  color: var(--sidebar-text-muted);
}

.toggle-btn:hover {
  color: var(--sidebar-text);
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
  background: var(--scrollbar-thumb);
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
  color: var(--sidebar-text);
}

.conv-item:hover {
  background: var(--sidebar-hover);
}

.conv-item.active {
  background: var(--sidebar-active);
  color: var(--sidebar-text);
}

.conv-icon {
  flex-shrink: 0;
  font-size: 16px;
  color: var(--sidebar-text-muted);
}

.conv-item.active .conv-icon {
  color: var(--sidebar-active-icon);
}

.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.del-btn {
  opacity: 0;
  color: var(--del-color);
  flex-shrink: 0;
  padding: 0 2px;
}

.conv-item:hover .del-btn {
  opacity: 1;
}

.empty-text {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  padding: 20px 0;
}

/* 右侧主区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  color: var(--sidebar-text-muted);
}

.model-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--sidebar-text-muted);
  font-size: 13px;
}

.model-select {
  width: 150px;
}

.model-select :deep(.el-input__wrapper) {
  background: var(--model-select-bg);
  border-color: var(--model-select-border);
}

.model-select :deep(.el-input__inner) {
  color: var(--sidebar-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right .el-button {
  color: var(--sidebar-text-muted);
}

.header-right .el-button:hover {
  color: var(--del-color);
}

.theme-btn:hover {
  color: #3b82f6 !important;
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
  background: var(--scrollbar-thumb);
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
  color: var(--text-primary);
  margin: 0 0 8px;
  font-weight: 700;
}

.welcome-screen p {
  color: var(--text-secondary);
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
  background: var(--suggestion-bg);
  border: 1px solid var(--suggestion-border);
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s;
  text-align: center;
}

.suggestion-item:hover {
  background: var(--suggestion-hover-bg);
  color: var(--suggestion-hover-text);
  border-color: var(--suggestion-hover-border);
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
  background: var(--ai-avatar-bg) !important;
  color: var(--ai-avatar-color) !important;
  border: 1px solid var(--ai-avatar-border);
}

.message-content {
  max-width: 80%;
  min-width: 0;
}

.message-role {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
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
  background: var(--msg-user-bg);
  color: var(--msg-user-text);
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: transparent;
  color: var(--text-primary);
  padding: 0;
  border-radius: 0;
}

/* Markdown */
.markdown :deep(p) { margin: 0 0 8px; }
.markdown :deep(p:last-child) { margin-bottom: 0; }
.markdown :deep(pre) {
  background: var(--code-bg);
  color: var(--code-color);
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  margin: 8px 0;
  border: 1px solid var(--code-border);
}
.markdown :deep(code) {
  background: var(--inline-code-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: var(--inline-code-color);
}
.markdown :deep(pre code) { background: none; padding: 0; color: inherit; }
.markdown :deep(ul), .markdown :deep(ol) { margin: 8px 0; padding-left: 24px; }
.markdown :deep(li) { margin: 4px 0; }
.markdown :deep(blockquote) {
  border-left: 3px solid var(--blockquote-border);
  padding: 4px 0 4px 12px;
  margin: 8px 0;
  color: var(--blockquote-color);
}
.markdown :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; }
.markdown :deep(th), .markdown :deep(td) {
  border: 1px solid var(--table-border);
  padding: 8px 12px;
  text-align: left;
  font-size: 13px;
  color: var(--text-primary);
}
.markdown :deep(th) { background: var(--table-header-bg); font-weight: 600; }
.markdown :deep(strong) { color: var(--strong-color); }
.markdown :deep(h1), .markdown :deep(h2), .markdown :deep(h3) {
  color: var(--text-primary);
  margin: 16px 0 8px;
}
.markdown :deep(a) { color: var(--link-color); text-decoration: none; }
.markdown :deep(a:hover) { text-decoration: underline; }

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: var(--typing-cursor);
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
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 14px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.15s, background 0.3s ease;
}

.input-box:focus-within {
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
}

.chat-input { flex: 1; }

.chat-input :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 4px 0 !important;
  font-size: 14px;
  color: var(--text-primary);
  resize: none;
}

.chat-input :deep(.el-textarea__inner)::placeholder {
  color: var(--text-muted);
}

.send-btn {
  flex-shrink: 0;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
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
