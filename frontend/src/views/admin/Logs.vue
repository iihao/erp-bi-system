<template>
  <div class="system-logs">
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="操作日志" name="operation">
          <el-table :data="operationLogs" style="width: 100%">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="user" label="用户" width="120" />
            <el-table-column prop="action" label="操作" width="200" />
            <el-table-column prop="module" label="模块" width="150" />
            <el-table-column prop="ip" label="IP 地址" width="140" />
            <el-table-column prop="result" label="结果">
              <template #default="{ row }">
                <el-tag :type="row.result === '成功' ? 'success' : 'danger'">
                  {{ row.result }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="异常日志" name="error">
          <el-table :data="errorLogs" style="width: 100%">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getErrorType(row.level)">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="module" label="模块" width="150" />
            <el-table-column prop="message" label="错误信息" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="登录日志" name="login">
          <el-table :data="loginLogs" style="width: 100%">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="user" label="用户" width="120" />
            <el-table-column prop="ip" label="IP 地址" width="140" />
            <el-table-column prop="location" label="地点" width="200" />
            <el-table-column prop="device" label="设备" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Warning, Lock } from '@element-plus/icons-vue'

const activeTab = ref('operation')

const operationLogs = [
  { time: '2026-03-19 10:30:00', user: 'admin', action: '用户登录', module: '系统管理', ip: '192.168.1.100', result: '成功' },
  { time: '2026-03-19 10:25:00', user: 'admin', action: '修改用户信息', module: '用户管理', ip: '192.168.1.100', result: '成功' },
  { time: '2026-03-19 10:20:00', user: 'user1', action: '查看报表', module: 'BI 报表', ip: '192.168.1.101', result: '成功' },
  { time: '2026-03-19 10:15:00', user: 'user2', action: '执行 ETL', module: 'ETL 调度', ip: '192.168.1.102', result: '失败' }
]

const errorLogs = [
  { time: '2026-03-19 10:15:00', level: 'ERROR', module: 'ETL 调度', message: '数据库连接超时' },
  { time: '2026-03-19 09:30:00', level: 'WARNING', module: 'AI 问数', message: 'API 调用频率超限' },
  { time: '2026-03-19 08:45:00', level: 'ERROR', module: '数据源', message: 'SAP ERP 连接失败' }
]

const loginLogs = [
  { time: '2026-03-19 10:30:00', user: 'admin', ip: '192.168.1.100', location: '上海办公室', device: 'Chrome / Windows' },
  { time: '2026-03-19 09:15:00', user: 'user1', ip: '192.168.1.101', location: '北京办公室', device: 'Firefox / Mac' },
  { time: '2026-03-19 08:30:00', user: 'user2', ip: '192.168.1.102', location: '深圳办公室', device: 'Safari / iPhone' }
]

const getErrorType = (level) => {
  const types = { 'ERROR': 'danger', 'WARNING': 'warning', 'INFO': 'info' }
  return types[level] || 'info'
}
</script>

<style scoped>
.system-logs {
  padding: 24px;
}
</style>
