<template>
  <div class="treehole-page">
    <div class="treehole-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            树洞
          </h1>
          <p class="page-description">在这里匿名分享你的心事、吐槽、秘密...</p>
        </div>
      </div>

      <!-- 标签页 -->
      <el-card class="content-card">
        <el-tabs v-model="activeTab" class="treehole-tabs" @tab-change="handleTabChange">
          <el-tab-pane name="all">
            <template #label>
              <span class="tab-label">
                <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 6h16M4 10h16M4 14h16M4 18h16" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                全部树洞
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="hot">
            <template #label>
              <span class="tab-label">
                <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                热门树洞
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane name="my">
            <template #label>
              <span class="tab-label">
                <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                我的树洞
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>

        <!-- 发布表单（仅在全部/热门标签页显示） -->
        <ConfessionForm v-if="activeTab !== 'my'" @submitted="handleConfessionSubmitted" />

        <!-- 树洞列表 -->
        <div class="treehole-list">
          <!-- 加载中 -->
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>

          <!-- 空状态 -->
          <div v-else-if="treeholes.length === 0" class="empty-container">
            <el-empty :description="emptyText">
              <template #image>
                <svg class="empty-image" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </template>
              <el-button v-if="activeTab !== 'my'" type="primary" @click="scrollToForm">
                写第一条树洞
              </el-button>
            </el-empty>
          </div>

          <!-- 列表内容 -->
          <div v-else class="list-container">
            <ConfessionItem
              v-for="item in treeholes"
              :key="item.post_id"
              :confession="item"
              :showDelete="activeTab === 'my'"
              @deleted="handleConfessionDeleted"
            />
          </div>

          <!-- 分页 -->
          <div v-if="treeholes.length > 0" class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="loadTreeholes"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import treeholeApi from '@/api/treehole'
import ConfessionForm from '@/components/ConfessionForm.vue'
import ConfessionItem from '@/components/ConfessionItem.vue'

const activeTab = ref('all')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(15)
const total = ref(0)
const treeholes = ref([])

// 空状态文本
const emptyText = computed(() => {
  if (activeTab.value === 'my') {
    return '暂无发布的树洞，去分享你的心事吧~'
  }
  return '暂无树洞，来成为第一个分享的人吧~'
})

// 加载树洞列表
const loadTreeholes = async () => {
  loading.value = true
  try {
    let result
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (activeTab.value === 'my') {
      result = await treeholeApi.getMyList(params)
    } else {
      params.sort_by = activeTab.value === 'hot' ? 'hot' : 'created_at'
      result = await treeholeApi.getList(params)
    }

    if (result.success) {
      treeholes.value = result.data.list
      total.value = result.data.total
    }
  } catch (error) {
    console.error('加载树洞失败:', error)
    const message = error.detail?.message || error.message || '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 处理标签页切换
const handleTabChange = () => {
  currentPage.value = 1
  loadTreeholes()
}

// 处理发布成功
const handleConfessionSubmitted = () => {
  // 刷新列表
  currentPage.value = 1
  loadTreeholes()
  // 滚动到列表顶部
  scrollToTop()
}

// 处理删除成功
const handleConfessionDeleted = (postId) => {
  // 从列表中移除
  treeholes.value = treeholes.value.filter(item => item.post_id !== postId)
  total.value--
}

// 滚动到表单
const scrollToForm = () => {
  const formElement = document.querySelector('.confession-form')
  if (formElement) {
    formElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// 滚动到顶部
const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 初始化
onMounted(() => {
  loadTreeholes()
})
</script>

<style scoped>
.treehole-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f4ff 0%, #e8ecff 100%);
  padding: 24px;
}

.treehole-container {
  max-width: 800px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.header-content {
  display: inline-block;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.title-icon {
  width: 36px;
  height: 36px;
  color: #6366f1;
}

.page-description {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

/* 内容卡片 */
.content-card {
  border-radius: 16px;
  min-height: 600px;
}

.treehole-tabs {
  padding: 0 20px 20px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 20px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
}

.tab-icon {
  width: 18px;
  height: 18px;
}

/* 列表 */
.treehole-list {
  padding: 0 20px 20px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-image {
  width: 120px;
  height: 120px;
  color: #cbd5e1;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  margin-top: 24px;
  border-top: 1px solid #e2e8f0;
}

/* 响应式 */
@media (max-width: 768px) {
  .treehole-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .title-icon {
    width: 28px;
    height: 28px;
  }

  .content-card {
    border-radius: 12px;
  }

  .treehole-tabs {
    padding: 0 12px 12px;
  }

  .treehole-list {
    padding: 0 12px 12px;
  }
}
</style>
