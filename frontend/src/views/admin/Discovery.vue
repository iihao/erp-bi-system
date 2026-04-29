<template>
  <div class="discovery-page">
    <div class="discovery-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <p class="page-description">探索热门内容和个性化推荐</p>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索感兴趣的内容..."
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="handleSearch">搜索</el-button>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 左侧边栏 - 分类导航 -->
        <div class="sidebar">
          <el-card class="category-card">
            <template #header>
              <span class="card-title">
                <el-icon><Folder /></el-icon>
                分类
              </span>
            </template>
            <div class="category-list">
              <div
                v-for="cat in categories"
                :key="cat.id"
                :class="['category-item', { active: currentCategory === cat.name }]"
                @click="selectCategory(cat.name)"
              >
              <span class="category-icon"><el-icon><component :is="getCategoryIcon(cat.icon)" /></el-icon></span>
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">{{ cat.content_count }}</span>
              </div>
            </div>
          </el-card>

          <!-- 热门标签 -->
          <el-card class="tags-card">
            <template #header>
              <span class="card-title">
                <el-icon><PriceTag /></el-icon>
                热门标签
              </span>
            </template>
            <div class="tag-cloud">
              <el-tag
                v-for="tag in tags"
                :key="tag.id"
                size="small"
                class="tag-item"
                @click="searchByTag(tag.name)"
              >
                {{ tag.name }}
              </el-tag>
            </div>
          </el-card>
        </div>

        <!-- 主内容区 -->
        <div class="content-area">
          <!-- 标签页 -->
          <el-card class="content-card">
            <el-tabs v-model="activeTab" class="discovery-tabs" @tab-change="handleTabChange">
              <el-tab-pane name="recommend">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Star /></el-icon>
                    为你推荐
                  </span>
                </template>
              </el-tab-pane>
              <el-tab-pane name="hot">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Operation /></el-icon>
                    热门
                  </span>
                </template>
              </el-tab-pane>
              <el-tab-pane name="treehole">
                <template #label>
                  <span class="tab-label">
                    <el-icon><ChatDotRound /></el-icon>
                    树洞
                  </span>
                </template>
              </el-tab-pane>
              <el-tab-pane name="report">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Document /></el-icon>
                    报表
                  </span>
                </template>
              </el-tab-pane>
            </el-tabs>

            <!-- 内容列表 -->
            <div class="content-list">
              <!-- 加载中 -->
              <div v-if="loading" class="loading-container">
                <el-skeleton :rows="10" animated />
              </div>

              <!-- 空状态 -->
              <div v-else-if="contentList.length === 0" class="empty-container">
                <el-empty description="暂无内容" />
              </div>

              <!-- 列表内容 -->
              <div v-else class="list-container" @scroll="handleScroll">
                <div
                  v-for="item in contentList"
                  :key="`${item.type}_${item.id}`"
                  class="content-item"
                  @click="navigateToContent(item)"
                >
                  <!-- 内容卡片 -->
                  <div class="content-card-inner">
                    <!-- 头部：作者信息 -->
                    <div class="card-header">
                      <div class="author-info">
                        <el-avatar :size="32" :src="item.author_avatar">
                          {{ item.author_name?.charAt(0) || 'U' }}
                        </el-avatar>
                        <div class="author-details">
                          <span class="author-name">{{ item.author_name }}</span>
                          <span class="content-type">{{ item.type === 'post' ? '帖子' : '报表' }}</span>
                        </div>
                      </div>
                      <el-tag :type="item.type === 'post' ? 'success' : 'warning'" size="small">
                        {{ item.type === 'post' ? '帖子' : '报表' }}
                      </el-tag>
                    </div>

                    <!-- 内容主体 -->
                    <div class="card-body">
                      <h3 class="content-title">{{ item.title || '无标题' }}</h3>
                      <p class="content-text">{{ item.content }}</p>
                    </div>

                    <!-- 底部：统计信息 -->
                    <div class="card-footer">
                      <div class="stats">
                        <span class="stat-item">
                          <el-icon><Star /></el-icon>
                          {{ formatNumber(item.like_count) }}
                        </span>
                        <span class="stat-item">
                          <el-icon><ChatDotRound /></el-icon>
                          {{ formatNumber(item.comment_count) }}
                        </span>
                        <span class="stat-item">
                          <el-icon><View /></el-icon>
                          {{ formatNumber(item.view_count) }}
                        </span>
                      </div>
                      <span class="post-time">{{ formatTime(item.created_at) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 加载更多 -->
                <div v-if="hasMore" class="load-more">
                  <el-button v-if="!loadingMore" text @click="loadMore">加载更多</el-button>
                  <el-skeleton v-else :rows="1" animated />
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Folder, PriceTag, Star, Operation, ChatDotRound, Document, View, TrendCharts, DataAnalysis } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

// 状态
const activeTab = ref('recommend')
const currentCategory = ref('all')
const searchKeyword = ref('')

// 分类数据
const categories = ref([])
const tags = ref([])

// 内容列表
const contentList = ref([])
const loading = ref(false)
const loadingMore = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hasMore = ref(true)

// 搜索状态
const isSearching = ref(false)

// 获取分类列表
async function loadCategories() {
  try {
    const res = await api.discovery.getCategories()
    if (res.success) {
      categories.value = res.data
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

// 获取热门标签
async function loadTags() {
  try {
    const res = await api.discovery.getTags({ limit: 15 })
    if (res.success) {
      tags.value = res.data
    }
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

// 获取内容列表
async function loadContent(reset = false) {
  if (reset) {
    currentPage.value = 1
    contentList.value = []
  }

  loading.value = true

  try {
    let res
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      category: currentCategory.value === 'all' ? null : currentCategory.value
    }

    if (isSearching.value && searchKeyword.value) {
      // 搜索模式
      res = await api.discovery.search({
        keyword: searchKeyword.value,
        page: params.page,
        page_size: params.page_size
      })
    } else if (activeTab.value === 'recommend') {
      // 推荐模式
      res = await api.discovery.getRecommendations({
        limit: params.page_size,
        personalized: true
      })
    } else if (activeTab.value === 'hot') {
      // 热门模式
      res = await api.discovery.getHotList({
        limit: params.page_size,
        content_type: currentCategory.value === 'report' ? 'report' : 'all'
      })
    } else {
      // 信息流模式
      params.category = activeTab.value
      res = await api.discovery.getFeed(params)
    }

    if (res.success) {
      const newList = res.data.list || []
      total.value = res.data.total || 0
      hasMore.value = res.data.has_more !== false && newList.length >= pageSize.value

      if (reset) {
        contentList.value = newList
      } else {
        contentList.value = [...contentList.value, ...newList]
      }
    }
  } catch (error) {
    console.error('加载内容失败:', error)
    ElMessage.error('加载失败，请重试')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 加载更多
function loadMore() {
  if (!hasMore.value || loading.value) return
  currentPage.value++
  loadingMore.value = true
  loadContent(false)
}

// 处理滚动
function handleScroll(e) {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  // 距离底部 100px 时加载更多
  if (scrollHeight - scrollTop - clientHeight < 100 && hasMore.value && !loading.value) {
    loadMore()
  }
}

// 切换标签页
async function handleTabChange(tab) {
  currentCategory.value = tab === 'recommend' ? 'recommend' : (tab === 'hot' ? 'all' : tab)
  isSearching.value = false
  searchKeyword.value = ''
  await loadContent(true)
}

// 选择分类
async function selectCategory(category) {
  currentCategory.value = category
  if (activeTab.value !== 'hot' && activeTab.value !== 'recommend') {
    activeTab.value = 'hot'
  }
  await loadContent(true)
}

// 搜索
function handleSearch() {
  if (!searchKeyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  isSearching.value = true
  loadContent(true)
}

// 按标签搜索
function searchByTag(tagName) {
  searchKeyword.value = tagName
  isSearching.value = true
  activeTab.value = 'hot'
  loadContent(true)
}

// 获取分类图标
function getCategoryIcon(icon) {
  const icons = {
    all: 'Document',
    hot: 'TrendCharts',
    treehole: 'ChatDotRound',
    dynamic: 'ChatDotRound',
    report: 'DataAnalysis'
  }
  return icons[icon] || 'Document'
}

// 格式化数字
function formatNumber(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num
}

// 格式化时间
function formatTime(timeStr) {
  const time = new Date(timeStr)
  const now = new Date()
  const diff = now - time

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day
  const year = 365 * day

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)}分钟前`
  } else if (diff < day) {
    return `${Math.floor(diff / hour)}小时前`
  } else if (diff < month) {
    return `${Math.floor(diff / day)}天前`
  } else if (diff < year) {
    return `${Math.floor(diff / month)}个月前`
  } else {
    return `${Math.floor(diff / year)}年前`
  }
}

// 导航到内容详情
function navigateToContent(item) {
  if (item.type === 'post') {
    // 跳转到树洞/帖子详情
    router.push(`/treehole?post_id=${item.id}`)
  } else if (item.type === 'report') {
    // 跳转到报表详情
    router.push(`/reports/${item.id}`)
  }
}

// 初始化
onMounted(() => {
  loadCategories()
  loadTags()
  loadContent(true)
})
</script>

<style scoped>
.discovery-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.discovery-container {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
  font-size: 28px;
  font-weight: 600;
  margin: 0;
}

.title-icon {
  width: 32px;
  height: 32px;
}

.page-description {
  color: rgba(255, 255, 255, 0.9);
  margin: 8px 0 0 44px;
  font-size: 14px;
}

.search-box {
  max-width: 500px;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.search-box :deep(.el-icon) {
  color: #999;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

/* 侧边栏 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-card,
.tags-card {
  border-radius: 12px;
  overflow: hidden;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.card-title .el-icon {
  color: #667eea;
}

/* 分类列表 */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background: #f5f7fa;
}

.category-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.category-icon .el-icon {
  font-size: 18px;
  margin-right: 12px;
}

.category-name {
  flex: 1;
  font-size: 14px;
}

.category-count {
  font-size: 12px;
  opacity: 0.7;
}

/* 标签云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s;
}

.tag-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 内容区 */
.content-area {
  min-height: calc(100vh - 160px);
}

.content-card {
  border-radius: 12px;
  min-height: 600px;
}

.discovery-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-label .el-icon {
  margin-right: 4px;
}

/* 内容列表 */
.content-list {
  min-height: 400px;
}

.loading-container,
.empty-container {
  padding: 40px;
  text-align: center;
}

.empty-container {
  padding: 40px;
  text-align: center;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  padding-right: 8px;
}

/* 内容卡片 */
.content-item {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.content-item:hover {
  transform: translateY(-2px);
}

.content-card-inner {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.2s;
}

.content-item:hover .content-card-inner {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.content-type {
  font-size: 12px;
  color: #999;
}

/* 卡片主体 */
.card-body {
  margin-bottom: 16px;
}

.content-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.content-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #999;
}

.stat-item .el-icon {
  width: 16px;
  height: 16px;
}

.post-time {
  font-size: 12px;
  color: #999;
}

/* 加载更多 */
.load-more {
  text-align: center;
  padding: 20px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .sidebar {
    flex-direction: row;
  }

  .category-card,
  .tags-card {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .sidebar {
    flex-direction: column;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .page-description {
    margin-left: 0;
  }

  .search-box {
    max-width: 100%;
  }
}
</style>
