<template>
  <div class="like-test-page">
    <h1>点赞功能测试页面</h1>

    <el-card class="test-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试帖子 1</span>
          <el-tag type="info">ID: 1</el-tag>
        </div>
      </template>
      <div class="post-content">
        <p>这是一个测试帖子的内容，用于测试点赞功能。</p>
        <div class="like-wrapper">
          <span class="label">点赞:</span>
          <LikeButton
            target-type="post"
            :target-id="1"
            :initial-count="10"
            :initial-liked="false"
            @like-change="onLikeChange"
          />
        </div>
      </div>
    </el-card>

    <el-card class="test-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试帖子 2</span>
          <el-tag type="info">ID: 2</el-tag>
        </div>
      </template>
      <div class="post-content">
        <p>这是另一个测试帖子，已经点赞过了。</p>
        <div class="like-wrapper">
          <span class="label">点赞:</span>
          <LikeButton
            target-type="post"
            :target-id="2"
            :initial-count="25"
            :initial-liked="true"
            @like-change="onLikeChange"
          />
        </div>
      </div>
    </el-card>

    <el-card class="test-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试评论</span>
          <el-tag type="warning">评论 ID: 1</el-tag>
        </div>
      </template>
      <div class="post-content">
        <p>这是一条测试评论的内容。</p>
        <div class="like-wrapper">
          <span class="label">点赞:</span>
          <LikeButton
            target-type="comment"
            :target-id="1"
            :initial-count="5"
            :initial-liked="false"
            size="small"
            @like-change="onLikeChange"
          />
        </div>
      </div>
    </el-card>

    <el-card class="test-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试报表</span>
          <el-tag type="success">报表 ID: 1</el-tag>
        </div>
      </template>
      <div class="post-content">
        <p>这是一个测试报表。</p>
        <div class="like-wrapper">
          <span class="label">点赞:</span>
          <LikeButton
            target-type="report"
            :target-id="1"
            :initial-count="100"
            :initial-liked="false"
            size="large"
            @like-change="onLikeChange"
          />
        </div>
      </div>
    </el-card>

    <el-card class="test-card" shadow="hover">
      <template #header>
        <span>点赞日志</span>
      </template>
      <div class="log-container">
        <div v-for="(log, index) in logs" :key="index" class="log-item">
          <el-tag :type="log.isLiked ? 'danger' : 'info'" size="small">{{ log.isLiked ? '点赞' : '取消' }}</el-tag>
          <span>目标类型：{{ log.targetType }}, ID: {{ log.targetId }}, 当前计数：{{ log.count }}</span>
          <span class="log-time">{{ log.time }}</span>
        </div>
        <div v-if="logs.length === 0" class="no-logs">暂无日志</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LikeButton from '@/components/LikeButton.vue'

const logs = ref([])

const onLikeChange = (data) => {
  const now = new Date()
  logs.value.unshift({
    targetType: data.targetType,
    targetId: data.targetId,
    isLiked: data.isLiked,
    count: data.count,
    time: now.toLocaleTimeString()
  })
  // 只保留最近 10 条
  if (logs.value.length > 10) {
    logs.value.pop()
  }
}
</script>

<style scoped>
.like-test-page {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 24px;
  text-align: center;
}

.test-card {
  margin-bottom: 16px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-content {
  padding: 8px 0;
}

.post-content p {
  color: #4b5563;
  margin-bottom: 16px;
}

.like-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.log-container {
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  color: #374151;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  margin-left: auto;
  color: #9ca3af;
  font-size: 12px;
}

.no-logs {
  text-align: center;
  color: #9ca3af;
  padding: 24px;
}
</style>
