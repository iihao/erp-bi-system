<template>
  <div class="report-list">
    <div class="page-header">
      <h1>📁 我的报表</h1>
      <p>查看和管理已保存的报表</p>
    </div>

    <el-empty description="暂无报表，请先使用报表设计器创建" :image-size="200">
      <el-button type="primary" @click="createReport">🎨 创建报表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const createReport = () => {
  router.push('/admin/bi/dashboard')
}
</script>

<style scoped>
.report-list {
  padding: 24px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0 0 8px 0;
  color: #1e293b;
}

.page-header p {
  color: #64748b;
  margin: 0;
}
</style>
