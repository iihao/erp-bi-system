<template>
  <div style="padding: 40px; background: #fff; min-height: 100vh;">
    <h1 style="color: red; font-size: 32px;">如果看到这个页面，说明 Vue 渲染正常</h1>
    
    <div style="margin: 20px 0;">
      <el-button type="primary">测试按钮 1</el-button>
      <el-button type="success">测试按钮 2</el-button>
      <el-button type="danger">测试按钮 3</el-button>
    </div>
    
    <el-card style="margin-top: 20px;">
      <template #header>测试表格</template>
      <p>纯文字按钮测试</p>
      <el-table :data="[{name: '测试 1'}, {name: '测试 2'}]" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column label="操作" width="200">
          <template #default>
            <el-button size="small" type="primary">预览</el-button>
            <el-button size="small" type="danger">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <div style="margin-top: 20px;">
      <el-button type="primary" @click="$router.push('/admin/datasources')">
        跳转到数据源管理
      </el-button>
    </div>
  </div>
</template>

<script setup>
console.log('✅ SimpleTest 页面已加载')
</script>
