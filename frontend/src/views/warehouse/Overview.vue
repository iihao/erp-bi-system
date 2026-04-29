<template>
  <div class="warehouse-overview">
    <div class="page-header">
      <h1>🗄️ 数仓概览</h1>
      <p>数据仓库分层架构与数据状态</p>
    </div>

    <!-- 数仓架构图 -->
    <div class="architecture">
      <h2>📐 数仓分层架构</h2>
      <div class="arch-diagram">
        <div class="arch-layer ads">
          <div class="layer-title">ADS 层</div>
          <div class="layer-desc">应用数据层 - 报表指标</div>
          <div class="layer-stats">7 张表 · {{ stats.ads }} 条数据</div>
        </div>
        <div class="arrow">⬆</div>
        <div class="arch-layer dws">
          <div class="layer-title">DWS 层</div>
          <div class="layer-desc">汇总层 - 主题聚合</div>
          <div class="layer-stats">5 张表 · {{ stats.dws }} 条数据</div>
        </div>
        <div class="arrow">⬆</div>
        <div class="arch-layer dwd">
          <div class="layer-title">DWD 层</div>
          <div class="layer-desc">明细层 - 清洗标准化</div>
          <div class="layer-stats">7 张表 · {{ stats.dwd }} 条数据</div>
        </div>
        <div class="arrow">⬆</div>
        <div class="arch-layer ods">
          <div class="layer-title">ODS 层</div>
          <div class="layer-desc">原始数据层 - 保持原貌</div>
          <div class="layer-stats">9 张表 · {{ stats.ods }} 条数据</div>
        </div>
        <div class="arrow">⬆</div>
        <div class="arch-layer source">
          <div class="layer-title">数据源</div>
          <div class="layer-desc">SQLite · SAP ERP · Excel</div>
        </div>
      </div>
    </div>

    <!-- 数据状态 -->
    <div class="data-status">
      <h2>📊 数据状态</h2>
      <el-row :gutter="20">
        <el-col :span="6" v-for="layer in layers" :key="layer.name">
          <el-card shadow="hover" class="status-card">
            <div class="status-header" :class="layer.color">
              <span class="status-icon">{{ layer.icon }}</span>
              <span class="status-name">{{ layer.name }}</span>
            </div>
            <div class="status-body">
              <div class="status-value">{{ layer.tables }}<small>张表</small></div>
              <div class="status-detail">{{ layer.records }} 条数据</div>
              <div class="status-update">更新于：2026-03-19 05:00</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2>⚡ 快捷操作</h2>
      <el-space>
        <el-button type="primary" @click="refreshData">🔄 刷新数据</el-button>
        <el-button type="success" @click="runETL">▶️ 执行 ETL</el-button>
        <el-button type="warning" @click="viewLogs">📝 查看日志</el-button>
        <el-button type="info" @click="exportData">📤 导出数据</el-button>
      </el-space>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const stats = reactive({
  ods: 29,
  dwd: 17,
  dws: 5,
  ads: 4
})

const layers = [
  { name: 'ODS 层', icon: '📦', color: 'ods', tables: 9, records: 29 },
  { name: 'DWD 层', icon: '🔍', color: 'dwd', tables: 7, records: 17 },
  { name: 'DWS 层', icon: '📊', color: 'dws', tables: 5, records: 5 },
  { name: 'ADS 层', icon: '📈', color: 'ads', tables: 7, records: 4 }
]

const refreshData = () => {
  ElMessage.success('数据刷新成功')
}

const runETL = () => {
  ElMessage.info('ETL 执行中...')
}

const viewLogs = () => {
  ElMessage.info('跳转到日志页面')
}

const exportData = () => {
  ElMessage.success('数据导出成功')
}
</script>

<style scoped>
.warehouse-overview {
  padding: 24px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #1e293b;
}

.page-header p {
  color: #64748b;
  margin: 0;
}

.architecture {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 30px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.architecture h2 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #1e293b;
}

.arch-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.arch-layer {
  width: 100%;
  max-width: 600px;
  padding: 16px 24px;
  border-radius: 8px;
  text-align: center;
  color: white;
  transition: transform 0.2s;
}

.arch-layer:hover {
  transform: scale(1.02);
}

.arch-layer.ods { background: linear-gradient(135deg, #10b981, #059669); }
.arch-layer.dwd { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.arch-layer.dws { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.arch-layer.ads { background: linear-gradient(135deg, #f59e0b, #d97706); }
.arch-layer.source { background: linear-gradient(135deg, #64748b, #475569); }

.layer-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.layer-desc {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.layer-stats {
  font-size: 13px;
  background: rgba(255,255,255,0.2);
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-block;
}

.arrow {
  font-size: 24px;
  color: #94a3b8;
}

.data-status h2 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #1e293b;
}

.status-card {
  margin-bottom: 20px;
}

.status-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  border-radius: 8px 8px 0 0;
}

.status-header.ods { background: #10b981; }
.status-header.dwd { background: #3b82f6; }
.status-header.dws { background: #8b5cf6; }
.status-header.ads { background: #f59e0b; }

.status-icon {
  font-size: 20px;
}

.status-name {
  font-size: 16px;
  font-weight: 600;
}

.status-body {
  padding: 16px;
}

.status-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}

.status-value small {
  font-size: 14px;
  color: #64748b;
  font-weight: normal;
}

.status-detail {
  font-size: 14px;
  color: #64748b;
  margin: 8px 0;
}

.status-update {
  font-size: 12px;
  color: #94a3b8;
}

.quick-actions {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.quick-actions h2 {
  font-size: 20px;
  margin: 0 0 20px 0;
  color: #1e293b;
}
</style>
