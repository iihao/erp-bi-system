<template>
  <div class="pro-list">
    <!-- 页面头部 -->
    <div class="pro-list-header" v-if="$slots.header || title">
      <slot name="header">
        <div class="header-content">
          <h1 class="page-title" v-if="title">
            <svg v-if="titleIcon" class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <component :is="titleIcon" />
            </svg>
            {{ title }}
          </h1>
          <p class="page-description" v-if="description">{{ description }}</p>
        </div>
      </slot>
    </div>

    <!-- 搜索筛选区 -->
    <el-card class="pro-list-search" shadow="sm" v-if="$slots.search">
      <div class="search-wrapper">
        <slot name="search" />
      </div>
    </el-card>

    <!-- 数据表格区 -->
    <el-card class="pro-list-table" shadow="sm">
      <!-- 表格工具栏 -->
      <div class="table-toolbar" v-if="$slots.toolbar || showTotal">
        <div class="toolbar-left">
          <slot name="toolbar-left">
            <span class="toolbar-title" v-if="toolbarTitle">{{ toolbarTitle }}</span>
            <el-tag type="info" class="total-count" v-if="showTotal && total > 0">共 {{ total }} 条</el-tag>
          </slot>
        </div>
        <div class="toolbar-right">
          <slot name="toolbar-right">
            <el-button @click="onRefresh" :loading="loading" circle v-if="showRefresh">
              <svg class="btn-icon" :class="{ 'spinning': loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </el-button>
          </slot>
        </div>
      </div>

      <!-- 表格 -->
      <el-table
        :data="data"
        v-loading="loading"
        :border="border"
        :stripe="stripe"
        class="pro-data-table"
        :header-cell-class-name="headerCellClassName"
        v-bind="$attrs"
      >
        <slot />
      </el-table>

      <!-- 分页 -->
      <div class="table-pagination" v-if="pagination">
        <div class="batch-actions" v-if="$slots.batchActions">
          <slot name="batchActions" />
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="pageSizes"
          :layout="paginationLayout"
          @size-change="onSizeChange"
          @current-change="onPageChange"
          class="pagination"
          v-if="showPagination"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 标题相关
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  titleIcon: { type: String, default: '' },
  
  // 工具栏
  toolbarTitle: { type: String, default: '数据列表' },
  showTotal: { type: Boolean, default: true },
  showRefresh: { type: Boolean, default: true },
  
  // 表格
  data: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  border: { type: Boolean, default: true },
  stripe: { type: Boolean, default: true },
  
  // 分页
  pagination: { type: Boolean, default: true },
  currentPage: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
  paginationLayout: { type: String, default: 'total, sizes, prev, pager, next, jumper' },
  showPagination: { type: Boolean, default: true }
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'refresh', 'page-change', 'size-change'])

const headerCellClassName = () => 'table-header-cell'

const onRefresh = () => {
  emit('refresh')
}

const onPageChange = (page) => {
  emit('update:currentPage', page)
  emit('page-change', page)
}

const onSizeChange = (size) => {
  emit('update:pageSize', size)
  emit('size-change', size)
}
</script>

<style scoped>
/* ========================================
   专业列表组件 - ProList
   ======================================== */

.pro-list {
  max-width: 100%;
}

/* 页面头部 */
.pro-list-header {
  margin-bottom: var(--spacing-6);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  width: 28px;
  height: 28px;
  color: var(--primary);
}

.page-description {
  font-size: var(--text-base);
  color: var(--text-tertiary);
  margin: 0;
}

/* 搜索卡片 */
.pro-list-search {
  margin-bottom: var(--spacing-4);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.search-wrapper {
  padding: var(--spacing-2) 0;
}

/* 表格卡片 */
.pro-list-table {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

/* 表格工具栏 */
.table-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: var(--spacing-4);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.toolbar-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.total-count {
  font-size: var(--text-sm);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 数据表格 */
.pro-data-table {
  font-size: var(--text-base);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.pro-data-table :deep(.el-table__header th) {
  background: linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%);
  color: var(--text-secondary);
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  padding: 14px 16px;
  border-bottom: 2px solid var(--border);
}

.pro-data-table :deep(.el-table__header th.table-header-cell) {
  background: linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%);
}

.pro-data-table :deep(.el-table__body td) {
  padding: 14px 16px;
  color: var(--text-secondary);
}

.pro-data-table :deep(.el-table__body tr:hover) {
  background-color: var(--primary-50) !important;
}

.pro-data-table :deep(.el-table__body tr.el-table__row--striped td) {
  background: var(--slate-50);
}

.pro-data-table :deep(.el-table__body tr.el-table__row--striped:hover td) {
  background: var(--primary-50) !important;
}

/* 分页 */
.table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-light);
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.pagination :deep(.el-pagination__total) {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.pagination :deep(.el-pager li) {
  border-radius: var(--radius);
  font-weight: var(--font-medium);
}

.pagination :deep(.el-pager li.active) {
  background: var(--primary);
  color: #ffffff;
}

.pagination :deep(.el-pager li:hover) {
  background: var(--primary-50);
  color: var(--primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .table-toolbar {
    flex-direction: column;
    gap: var(--spacing-3);
    align-items: flex-start;
  }

  .toolbar-right {
    width: 100%;
    justify-content: flex-start;
  }

  .table-pagination {
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .batch-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
