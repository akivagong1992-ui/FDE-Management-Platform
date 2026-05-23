<script setup lang="ts">
defineProps<{ dimension: string; title: string; description: string; planSection: string }>()
</script>

<template>
  <el-card>
    <template #header>
      <span style="font-weight: 600">{{ dimension }} · {{ title }}</span>
    </template>
    <el-empty :description="`${description}`">
      <template #image>
        <div style="font-size: 48px; color: #c0c4cc">🚧</div>
      </template>
      <el-tag>{{ planSection }}</el-tag>
      <p style="margin-top: 12px; color: #606266">本模块在 Phase 0 仅占位，具体实现见 PLAN.md 对应章节。</p>
    </el-empty>
  </el-card>
</template>
