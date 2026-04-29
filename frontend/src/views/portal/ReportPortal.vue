<template>
  <div class="report-portal-page">
    <el-container class="page-container">
      <!-- 顶部导航 -->
      <el-header class="portal-header">
        <div class="header-content">
          <div class="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
              <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
            <span>AI数据融合平台</span>
          </div>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="$router.push('/admin/reports')">
              📊 报表管理
            </el-button>
            <el-button type="success" size="small" @click="$router.push('/admin/reports/designer')">
              ✏️ 设计报表
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="portal-main">
        <!-- 报表分类 -->
        <div class="category-tabs">
          <el-tabs v-model="activeCategory" @change="filterReports">
            <el-tab-pane label="全部报表" name="all" />
            <el-tab-pane label="销售分析" name="sales" />
            <el-tab-pane label="财务报表" name="finance" />
            <el-tab-pane label="运营监控" name="operations" />
            <el-tab-pane label="管理驾驶舱" name="dashboard" />
          </el-tabs>
        </div>

        <!-- 报表网格 -->
        <div class="report-grid" v-loading="loading">
          <div v-if="filteredReports.length === 0" class="empty-state">
            <el-empty description="暂无已发布的报表" />
          </div>

          <el-card
            v-for="report in filteredReports"
            :key="report.id"
            class="report-card"
            hoverable
            @click="viewReport(report)"
          >
            <template #header>
              <div class="report-card-header">
                <div class="report-title">
                  <svg class="report-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="14 2 14 8 20 8" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <span>{{ report.name }}</span>
                </div>
                <el-tag size="small" type="success">已发布</el-tag>
              </div>
            </template>

            <div class="report-card-body">
              <p class="report-description">{{ report.description || '暂无描述' }}</p>
              
              <div class="report-meta">
                <div class="meta-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  <span>{{ formatDate(report.created_at) }}</span>
                </div>
                <div class="meta-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                    <path d="M16 3.13a4 4 0 010 7.75"/>
                  </svg>
                  <span>{{ report.created_by || '管理员' }}</span>
                </div>
              </div>

              <div class="report-widgets-preview">
                <div class="widget-count">
                  <el-tag size="small" effect="plain">
                    📊 {{ report.config?.widgets?.length || 0 }} 个图表
                  </el-tag>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="report-card-footer">
                <el-button type="primary" size="small" @click.stop="viewReport(report)">
                  👁️ 查看报表
                </el-button>
                <el-button size="small" @click.stop="downloadReport(report)">
                  📥 导出
                </el-button>
              </div>
            </template>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <!-- 报表查看对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      :title="currentReport?.name"
      width="95%"
      class="report-view-dialog"
      :fullscreen="true"
    >
      <div class="report-view-container" v-if="currentReport">
        <div class="report-view-header">
          <div>
            <h2>{{ currentReport.name }}</h2>
            <p class="report-desc">{{ currentReport.description }}</p>
          </div>
          <div class="report-actions">
            <el-button @click="refreshReportData">🔄 刷新数据</el-button>
            <el-button type="primary" @click="downloadReport(currentReport)">📥 导出 PDF</el-button>
            <el-button @click="viewDialogVisible = false">✕ 关闭</el-button>
          </div>
        </div>

        <div class="report-widgets-grid">
          <div
            v-for="widget in currentReport.config?.widgets"
            :key="widget.id"
            class="report-widget"
            :style="{ width: widget.width + 'px', height: widget.height + 'px' }"
          >
            <div class="widget-header">
              <span class="widget-title">{{ widget.title }}</span>
            </div>
            <div class="widget-content">
              <div v-if="widgetData[widget.id]" class="chart-container">
                <!-- 柱状图 -->
                <div v-if="widget.type === 'bar'" class="bar-chart">
                  <div class="bar-chart-container">
                    <div
                      v-for="(item, idx) in widgetData[widget.id]"
                      :key="idx"
                      class="bar-item"
                      :style="{ height: getBarHeight(item[widget.measureField]) + '%' }"
                    >
                      <div class="bar-label">{{ item[widget.dimensionField] }}</div>
                      <div class="bar-value">{{ item[widget.measureField] }}</div>
                    </div>
                  </div>
                </div>

                <!-- 折线图 -->
                <div v-else-if="widget.type === 'line'" class="line-chart">
                  <svg class="line-chart-svg" :viewBox="'0 0 ' + widget.width + ' ' + (widget.height - 60)">
                    <polyline
                      :points="getLinePoints(widgetData[widget.id], widget.measureField, widget.width, widget.height)"
                      fill="none"
                      stroke="#5470c6"
                      stroke-width="3"
                    />
                  </svg>
                </div>

                <!-- 饼图 -->
                <div v-else-if="widget.type === 'pie'" class="pie-chart">
                  <svg :viewBox="'-100 -100 200 200'">
                    <path
                      v-for="(slice, idx) in getPieSlices(widgetData[widget.id], widget.measureField)"
                      :key="idx"
                      :d="slice.path"
                      :fill="slice.color"
                      stroke="white"
                      stroke-width="1"
                    />
                  </svg>
                </div>

                <!-- 表格 -->
                <div v-else-if="widget.type === 'table'" class="table-chart">
                  <el-table :data="widgetData[widget.id]" stripe size="small" max-height="200">
                    <el-table-column
                      v-for="field in Object.keys(widgetData[widget.id][0] || {})"
                      :key="field"
                      :prop="field"
                      :label="field"
                    />
                  </el-table>
                </div>
              </div>
              <div v-else class="widget-loading">
                <el-loading-spinner />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const activeCategory = ref('all')
const viewDialogVisible = ref(false)
const currentReport = ref(null)
const widgetData = ref({})

const reports = ref([])

const filteredReports = computed(() => {
  if (activeCategory.value === 'all') {
    return reports.value
  }
  return reports.value.filter(r => {
    const name = (r.name || '').toLowerCase()
    const desc = (r.description || '').toLowerCase()
    return name.includes(activeCategory.value) || desc.includes(activeCategory.value)
  })
})

// 加载已发布的报表
const loadPublishedReports = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/admin/reports?status=published', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    reports.value = data.items || []
  } catch (error) {
    ElMessage.error('加载报表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 过滤报表
const filterReports = () => {
  // 已通过 computed 实现
}

// 查看报表
const viewReport = async (report) => {
  currentReport.value = report
  viewDialogVisible.value = true
  widgetData.value = {}
  
  // 加载每个组件的数据
  if (report.config?.widgets) {
    for (const widget of report.config.widgets) {
      if (widget.dataSource && widget.dimensionField && widget.measureField) {
        await loadWidgetData(widget)
      }
    }
  }
}

// 加载组件数据
const loadWidgetData = async (widget) => {
  try {
    const token = localStorage.getItem('token')
    const sql = `SELECT \`${widget.dimensionField}\`, \`${widget.measureField}\` FROM \`${widget.dataSource}\` LIMIT 100`
    
    const res = await fetch('/api/admin/datasources/1/query', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ sql, limit: 100 })
    })
    const data = await res.json()
    
    if (data.success) {
      widgetData.value[widget.id] = data.data
    }
  } catch (error) {
    console.error('加载组件数据失败', error)
  }
}

// 刷新报表数据
const refreshReportData = async () => {
  ElMessage.info('刷新数据中...')
  if (currentReport.value) {
    await viewReport(currentReport.value)
    ElMessage.success('数据已刷新')
  }
}

// 下载报表
const downloadReport = (report) => {
  ElMessage.success('正在生成 PDF，请稍候...')
  // TODO: 实现 PDF 导出功能
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 图表渲染辅助函数
const getBarHeight = (value) => {
  if (!currentReport.value) return 0
  const widget = currentReport.value.config?.widgets?.find(w => w.data)
  if (!widget?.data) return 0
  const max = Math.max(...widget.data.map(d => d[widget.measureField] || 0), 1)
  return (value / max) * 80
}

const getLinePoints = (data, field, width, height) => {
  if (!data || data.length === 0) return ''
  const max = Math.max(...data.map(d => d[field] || 0), 1)
  return data.map((item, idx) => {
    const x = 40 + (idx / (data.length - 1 || 1)) * (width - 80)
    const y = (height - 60) - ((item[field] / max) * (height - 80)) - 10
    return `${x},${y}`
  }).join(' ')
}

const getPieSlices = (data, field) => {
  if (!data || data.length === 0) return []
  const total = data.reduce((sum, item) => sum + (item[field] || 0), 0)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
  
  let startAngle = 0
  return data.map((item, idx) => {
    const percentage = (item[field] || 0) / total
    const angle = percentage * 360
    const endAngle = startAngle + angle
    
    const startRad = (startAngle - 90) * Math.PI / 180
    const endRad = (endAngle - 90) * Math.PI / 180
    const x1 = Math.cos(startRad) * 80
    const y1 = Math.sin(startRad) * 80
    const x2 = Math.cos(endRad) * 80
    const y2 = Math.sin(endRad) * 80
    const largeArc = angle > 180 ? 1 : 0
    
    const path = `M 0 0 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`
    startAngle = endAngle
    return { path, color: colors[idx % colors.length] }
  })
}

onMounted(() => {
  loadPublishedReports()
})
</script>

<style scoped>
.report-portal-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 26%),
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.1), transparent 22%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

.page-container {
  height: auto;
  min-height: 100vh;
}

.portal-header {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  padding: 0;
  height: 60px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1d4ed8;
}

.logo svg {
  width: 28px;
  height: 28px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.portal-main {
  padding: 24px;
}

.category-tabs {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.86);
  padding: 14px 18px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  backdrop-filter: blur(12px);
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 24px;
}

.report-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.96);
}

.report-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.12);
}

.report-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.report-icon {
  width: 20px;
  height: 20px;
  color: #2563eb;
}

.report-card-body {
  padding: 8px 0;
}

.report-description {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 16px;
  line-height: 1.5;
  min-height: 40px;
}

.report-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #64748b;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-item svg {
  width: 14px;
  height: 14px;
}

.report-widgets-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-card-footer {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.report-view-dialog {
  .el-dialog__body {
    padding: 0;
  }
}

.report-view-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.report-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.report-view-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.report-desc {
  margin: 0;
  color: #909399;
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-widgets-grid {
  flex: 1;
  padding: 24px;
  background: #f5f7fa;
  overflow: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-content: flex-start;
}

.report-widget {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.widget-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 600;
  font-size: 14px;
}

.widget-content {
  padding: 16px;
  height: calc(100% - 50px);
}

.chart-container {
  width: 100%;
  height: 100%;
}

.widget-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

/* 图表样式 */
.bar-chart {
  width: 100%;
  height: 100%;
}

.bar-chart-container {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 100%;
  padding: 20px 10px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
  margin: 0 4px;
  background: linear-gradient(to top, #5470c6, #91cc75);
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
  min-height: 20px;
}

.bar-label {
  font-size: 11px;
  color: #606266;
  margin-top: 4px;
  transform: rotate(-45deg);
  transform-origin: top center;
}

.bar-value {
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  padding: 2px 6px;
  margin-bottom: 4px;
}

.line-chart {
  width: 100%;
  height: 100%;
}

.line-chart-svg {
  width: 100%;
  height: 100%;
}

.pie-chart {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pie-chart svg {
  width: 200px;
  height: 200px;
}

.table-chart {
  width: 100%;
  height: 100%;
  overflow: auto;
}
</style>
