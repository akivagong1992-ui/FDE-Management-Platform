<script setup lang="ts">
import RetroList from './RetroList.vue'
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">关键项目复盘管理</span>
      </div>
    </template>
    <RetroList />
  </el-card>
</template>
