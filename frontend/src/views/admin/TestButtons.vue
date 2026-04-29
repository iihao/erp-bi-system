<template>
  <div style="padding: 40px;">
    <h1>按钮测试页面 - 纯文字</h1>
    
    <el-card style="margin-top: 20px;">
      <template #header>Element Plus 按钮测试</template>
      
      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <el-button type="primary">主要按钮</el-button>
        <el-button type="success">成功按钮</el-button>
        <el-button type="warning">警告按钮</el-button>
        <el-button type="danger">危险按钮</el-button>
        <el-button type="info">信息按钮</el-button>
      </div>
      
      <div style="margin-top: 20px;">
        <h3>小按钮:</h3>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <el-button size="small" type="primary">预览</el-button>
          <el-button size="small" type="success">同步</el-button>
          <el-button size="small">测试</el-button>
          <el-button size="small" type="danger">删除</el-button>
        </div>
      </div>
      
      <div style="margin-top: 20px;">
        <h3>操作栏按钮 (模拟表格):</h3>
        <el-table :data="[{name: '测试数据'}]" style="width: 100%">
          <el-table-column prop="name" label="名称" />
          <el-table-column label="操作" width="300">
            <template #default>
              <el-button size="small" type="primary">预览</el-button>
              <el-button size="small" type="success">同步</el-button>
              <el-button size="small">编辑</el-button>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
console.log('✅ 按钮测试页面已加载')
</script>
