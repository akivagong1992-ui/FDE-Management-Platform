<script setup lang="ts">
import RetroList from './RetroList.vue'
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">⑧ 项目复盘（满意度 + 改进行动项）</span>
      </div>
    </template>
    <RetroList />
  </el-card>
</template>
