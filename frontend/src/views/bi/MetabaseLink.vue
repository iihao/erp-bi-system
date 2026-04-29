<template>
  <div class="metabase-link">
    <div class="link-header">
      <h1>🔗 Metabase BI</h1>
      <p>专业商业智能分析工具</p>
      <el-button type="primary" @click="openMetabase" size="large">
        🚀 打开 Metabase
      </el-button>
    </div>

    <div class="metabase-panel">
      <div class="panel-card">
        <h3>访问地址</h3>
        <p class="panel-url">{{ metabaseUrl }}</p>
        <p class="panel-tip">如果浏览器拦截内嵌页面，请直接使用上方按钮在新窗口打开。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getMetabaseUrl } from '@/utils/metabase'

const metabaseUrl = getMetabaseUrl()

const openMetabase = () => {
  window.open(metabaseUrl, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.metabase-link {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.link-header {
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 20px;
}

.link-header h1 {
  font-size: 24px;
  margin: 0;
  color: #1e293b;
}

.link-header p {
  color: #64748b;
  margin: 0;
  flex: 1;
}

.metabase-panel {
  flex: 1;
  width: 100%;
  height: 100%;
  padding: 20px 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
}

.panel-card {
  max-width: 760px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}

.panel-card h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #0f172a;
}

.panel-url {
  margin: 0 0 8px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8fafc;
  color: #2563eb;
  font-weight: 600;
  word-break: break-all;
}

.panel-tip {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}
</style>
