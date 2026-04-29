<template>
  <div class="table-preview-container">
    <el-card class="preview-card">
      <template #header>
        <div class="card-header">
          <span>📊 数据表预览</span>
          <el-select v-model="selectedTable" @change="loadTableData" class="table-select">
            <el-option
              v-for="table in tables"
              :key="table.name"
              :label="table.label"
              :value="table.name"
            />
          </el-select>
        </div>
      </template>

      <!-- 表信息 -->
      <div class="table-info">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="表名">{{ selectedTable }}</el-descriptions-item>
          <el-descriptions-item label="记录数">{{ total }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ tableDescription }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
        class="data-table"
        max-height="600"
      >
        <el-table-column
          v-for="col in columns"
          :key="col"
          :prop="col"
          :label="col"
          :min-width="120"
        />
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="loadTableData"
          @current-change="loadTableData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const selectedTable = ref('products')
const loading = ref(false)
const tableData = ref([])
const columns = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const tables = [
  { name: 'products', label: '产品表 (products)' },
  { name: 'customers', label: '客户表 (customers)' },
  { name: 'sales_orders', label: '销售订单表 (sales_orders)' },
  { name: 'sales_order_items', label: '订单明细表 (sales_order_items)' },
  { name: 'suppliers', label: '供应商表 (suppliers)' }
]

const tableDescription = ref('')

const mockData = {
  products: [
    { id: 1, product_code: 'P001', product_name: '笔记本电脑 Pro 15', category: '电子产品', unit_price: 8999.00, stock_quantity: 150 },
    { id: 2, product_code: 'P002', product_name: '无线蓝牙鼠标', category: '电子产品', unit_price: 199.00, stock_quantity: 500 },
    { id: 3, product_code: 'P003', product_name: '机械键盘 RGB', category: '电子产品', unit_price: 599.00, stock_quantity: 300 },
    { id: 4, product_code: 'P004', product_name: '办公桌椅套装', category: '办公家具', unit_price: 2599.00, stock_quantity: 80 },
    { id: 5, product_code: 'P005', product_name: '文件柜三层', category: '办公家具', unit_price: 899.00, stock_quantity: 120 },
  ],
  customers: [
    { id: 1, customer_code: 'C001', customer_name: '北京科技有限公司', contact_person: '张三', contact_phone: '13800138001', customer_type: '企业' },
    { id: 2, customer_code: 'C002', customer_name: '上海贸易股份公司', contact_person: '李四', contact_phone: '13800138002', customer_type: '企业' },
    { id: 3, customer_code: 'C003', customer_name: '广州制造工厂', contact_person: '王五', contact_phone: '13800138003', customer_type: '企业' },
    { id: 4, customer_code: 'C004', customer_name: '深圳电子商行', contact_person: '赵六', contact_phone: '13800138004', customer_type: '企业' },
    { id: 5, customer_code: 'C005', customer_name: '杭州网络公司', contact_person: '钱七', contact_phone: '13800138005', customer_type: '企业' },
  ],
  sales_orders: [
    { id: 1, order_no: 'SO202601001', customer_id: 1, order_date: '2026-01-05', final_amount: 28616.74, order_status: 'completed' },
    { id: 2, order_no: 'SO202601002', customer_id: 2, order_date: '2026-01-08', final_amount: 5505.84, order_status: 'completed' },
    { id: 3, order_no: 'SO202601003', customer_id: 3, order_date: '2026-01-12', final_amount: 53978.40, order_status: 'shipped' },
    { id: 4, order_no: 'SO202602001', customer_id: 4, order_date: '2026-02-03', final_amount: 3884.76, order_status: 'processing' },
    { id: 5, order_no: 'SO202602002', customer_id: 5, order_date: '2026-02-10', final_amount: 19969.20, order_status: 'shipped' },
  ],
  sales_order_items: [
    { id: 1, order_id: 1, product_id: 1, quantity: 3, unit_price: 8999.00, subtotal: 26997.00 },
    { id: 2, order_id: 2, product_id: 2, quantity: 10, unit_price: 199.00, subtotal: 1990.00 },
    { id: 3, order_id: 2, product_id: 3, quantity: 5, unit_price: 599.00, subtotal: 2995.00 },
    { id: 4, order_id: 3, product_id: 1, quantity: 5, unit_price: 8999.00, subtotal: 44995.00 },
    { id: 5, order_id: 3, product_id: 8, quantity: 1, unit_price: 4599.00, subtotal: 4599.00 },
  ],
  suppliers: [
    { id: 1, supplier_code: 'S001', supplier_name: '深圳科技供应有限公司', contact_person: '刘经理', contact_phone: '13900139001', category: '电子产品' },
    { id: 2, supplier_code: 'S002', supplier_name: '广州家具制造厂', contact_person: '陈厂长', contact_phone: '13900139002', category: '办公家具' },
    { id: 3, supplier_code: 'S003', supplier_name: '义乌文具批发商行', contact_person: '王老板', contact_phone: '13900139003', category: '办公用品' },
    { id: 4, supplier_code: 'S004', supplier_name: '海尔电器经销商', contact_person: '张经理', contact_phone: '13900139004', category: '电器设备' },
    { id: 5, supplier_code: 'S005', supplier_name: '上海包装材料公司', contact_person: '李总', contact_phone: '13900139005', category: '包装材料' },
  ]
}

const tableDescMap = {
  products: '产品基础信息，包含价格、库存、分类等',
  customers: '客户信息，包含联系方式、行业、信用额度等',
  sales_orders: '销售订单主表，包含订单金额、状态、日期等',
  sales_order_items: '订单明细，关联订单和产品，记录数量和小计',
  suppliers: '供应商信息，包含联系方式、类别、信用评级等'
}

const loadTableData = () => {
  loading.value = true
  
  // 模拟数据加载
  setTimeout(() => {
    tableData.value = mockData[selectedTable.value] || []
    columns.value = tableData.value.length > 0 ? Object.keys(tableData.value[0]) : []
    total.value = 10 // 模拟总数
    tableDescription.value = tableDescMap[selectedTable.value] || ''
    loading.value = false
  }, 500)
}

onMounted(() => {
  loadTableData()
})
</script>

<style scoped>
.table-preview-container {
  padding: 24px;
  background-color: var(--bg-body);
  min-height: 100vh;
}

.preview-card {
  max-width: 1400px;
  margin: 0 auto;
  border: 1px solid var(--border);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.table-select {
  width: 300px;
}

.table-info {
  margin-bottom: 20px;
}

.data-table {
  margin-top: 10px;
}

.data-table :deep(.el-table__header th) {
  background-color: #f8fafc;
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 13px;
}

.data-table :deep(.el-table__row:hover) {
  background-color: #f0f7ff;
}

.data-table :deep(.el-table__cell) {
  padding: 12px 16px;
  font-size: 13px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
}

/* 描述列表样式 */
:deep(.el-descriptions__header) {
  margin-bottom: 16px;
}

:deep(.el-descriptions__label) {
  background-color: #f8fafc;
  color: var(--text-secondary);
  font-weight: 500;
  width: 120px;
}

:deep(.el-descriptions__content) {
  color: var(--text-primary);
}
</style>
