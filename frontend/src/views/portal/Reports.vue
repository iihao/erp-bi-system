<template>
  <div class="portal-reports">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">报表中心</h1>
        <p class="page-subtitle">根据您的权限查看可访问的报表</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshReports" :loading="loading" circle>
          <svg class="button-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </el-button>
      </div>
    </div>

    <!-- 报表分类标签 -->
    <div class="category-tabs">
      <button
        :class="['tab-btn', { active: currentCategory === 'all' }]"
        @click="currentCategory = 'all'"
      >
        全部
      </button>
      <button
        :class="['tab-btn', { active: currentCategory === 'basic' }]"
        @click="currentCategory = 'basic'"
      >
        基础报表
      </button>
      <button
        :class="['tab-btn', { active: currentCategory === 'analysis' }]"
        @click="currentCategory = 'analysis'"
      >
        分析报表
      </button>
      <button
        :class="['tab-btn', { active: currentCategory === 'advanced' }]"
        @click="currentCategory = 'advanced'"
      >
        高级报表
      </button>
    </div>

    <!-- 报表列表 -->
    <div class="reports-grid" v-loading="loading">
      <el-card
        v-for="report in filteredReports"
        :key="report.report_id"
        class="report-card"
        shadow="hover"
        @click="navigateToReport(report.report_id)"
      >
        <div class="report-icon-wrapper" :class="getCategoryColor(report.category)">
          <svg class="report-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <line x1="10" y1="9" x2="8" y2="9"/>
          </svg>
        </div>

        <h3 class="report-name">{{ report.report_name }}</h3>
        <p class="report-description">{{ report.description }}</p>

        <div class="report-footer">
          <span class="report-category" :class="'category-' + report.category">
            {{ getCategoryName(report.category) }}
          </span>
          <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9,18 15,12 9,6"/>
          </svg>
        </div>
      </el-card>

      <!-- 空状态 -->
      <div v-if="filteredReports.length === 0 && !loading" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <p class="empty-text">该分类下暂无报表</p>
        <el-button @click="currentCategory = 'all'" type="primary">查看全部</el-button>
      </div>
    </div>

    <!-- 权限提示 -->
    <div class="permission-tip">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <span>当前显示的是您权限范围内可访问的报表，如需更多报表权限请联系管理员</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const reports = ref([])
const currentCategory = ref('all')

// 报表分类名称
const categoryNames = {
  basic: '基础报表',
  analysis: '分析报表',
  advanced: '高级报表'
}

// 筛选后的报表列表
const filteredReports = computed(() => {
  if (currentCategory.value === 'all') {
    return reports.value
  }
  return reports.value.filter(r => r.category === currentCategory.value)
})

// 获取分类名称
const getCategoryName = (category) => {
  return categoryNames[category] || category
}

// 获取分类颜色
const getCategoryColor = (category) => {
  const colors = {
    basic: 'color-blue',
    analysis: 'color-green',
    advanced: 'color-purple'
  }
  return colors[category] || 'color-blue'
}

// 加载报表列表
const loadReports = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/portal/reports', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        router.push('/portal/login')
        return
      }
      throw new Error('加载报表列表失败')
    }

    const data = await response.json()
    reports.value = data
  } catch (error) {
    console.error('加载报表列表失败:', error)
    ElMessage.error('加载报表列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新报表列表
const refreshReports = async () => {
  await loadReports()
  ElMessage.success('刷新成功')
}

// 跳转到报表详情
const navigateToReport = (reportId) => {
  router.push(`/portal/report/${reportId}`)
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.portal-reports {
  max-width: 1400px;
  margin: 0 auto;
  padding: 4px 0 12px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 64, 175, 0.94) 100%);
  padding: 24px 26px;
  border-radius: 20px;
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.14);
  color: #fff;
}

.header-content .page-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 6px 0;
}

.header-content .page-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.82);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.button-icon {
  width: 18px;
  height: 18px;
  color: currentColor;
}

/* 分类标签 */
.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  padding: 10px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.tab-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 999px;
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  border-color: rgba(37, 99, 235, 0.32);
  color: #1d4ed8;
  transform: translateY(-1px);
}

.tab-btn.active {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-color: #2563eb;
  color: #fff;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
}

/* 报表网格 */
.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.report-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.95);
}

.report-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
  border-color: rgba(37, 99, 235, 0.28);
}

.report-icon-wrapper {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 16px;
}

.report-icon-wrapper.color-blue {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.report-icon-wrapper.color-green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.report-icon-wrapper.color-purple {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.report-icon {
  width: 28px;
  height: 28px;
  color: #fff;
}

.report-name {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.report-description {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 16px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.report-category {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.report-category.category-basic {
  background-color: #dbeafe;
  color: #2563eb;
}

.report-category.category-analysis {
  background-color: #d1fae5;
  color: #059669;
}

.report-category.category-advanced {
  background-color: #ede9fe;
  color: #7c3aed;
}

.arrow-icon {
  width: 18px;
  height: 18px;
  color: #cbd5e1;
  transition: transform 0.3s;
}

.report-card:hover .arrow-icon {
  transform: translateX(4px);
  color: #3b82f6;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  border: 1px dashed rgba(148, 163, 184, 0.3);
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: #cbd5e1;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  color: #94a3b8;
  margin: 0 0 20px 0;
}

/* 权限提示 */
.permission-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 14px;
  color: #1d4ed8;
  font-size: 13px;
}

.permission-tip svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
    text-align: center;
  }

  .header-content {
    text-align: center;
  }

  .reports-grid {
    grid-template-columns: 1fr;
  }

  .category-tabs {
    justify-content: center;
  }
}
</style>
