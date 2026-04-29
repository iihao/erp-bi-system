<template>
  <div class="placeholder-page">
    <div class="placeholder-content">
      <div class="placeholder-icon">📦</div>
      <h1>ODS 层数据</h1>
      <p>原始数据层 - 保持源系统数据原貌</p>
      
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>📊 数据表列表</span>
          </div>
        </template>
        <el-table :data="tables" style="width: 100%">
          <el-table-column prop="name" label="表名" width="200" />
          <el-table-column prop="cn_name" label="中文名" width="200" />
          <el-table-column prop="records" label="数据量" width="100" />
          <el-table-column prop="update_time" label="更新时间" />
          <el-table-column label="操作" width="200">
            <template #default>
              <el-button size="small" type="primary">查看</el-button>
              <el-button size="small" type="success">导出</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
const tables = [
  { name: 'ods_room', cn_name: '房间明细表', records: 17, update_time: '2026-03-19 05:00' },
  { name: 'ods_trade', cn_name: '销售明细表', records: 5, update_time: '2026-03-19 05:00' },
  { name: 'ods_payment', cn_name: '回款明细表', records: 7, update_time: '2026-03-19 05:00' },
  { name: 'ods_pay', cn_name: '付款登记表', records: 0, update_time: '-' },
  { name: 'ods_account', cn_name: '科目表', records: 0, update_time: '-' },
  { name: 'ods_contract', cn_name: '合同表', records: 0, update_time: '-' },
  { name: 'ods_bseg', cn_name: '凭证表', records: 0, update_time: '-' },
  { name: 'ods_gl_actual', cn_name: '总账实际业务表', records: 0, update_time: '-' },
  { name: 'ods_other', cn_name: '其他数据表', records: 0, update_time: '-' }
]
</script>

<style scoped>
.placeholder-page {
  padding: 24px;
}

.placeholder-content {
  max-width: 1200px;
  margin: 0 auto;
}

.placeholder-content h1 {
  font-size: 24px;
  margin: 0 0 8px 0;
  color: #1e293b;
}

.placeholder-content p {
  color: #64748b;
  margin: 0 0 20px 0;
}

.info-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
