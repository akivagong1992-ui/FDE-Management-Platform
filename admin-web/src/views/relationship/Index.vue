<script setup lang="ts">
import { ref } from 'vue'
import RetroList from './RetroList.vue'
import AttemptList from './AttemptList.vue'

type Tab = 'retros' | 'attempts'
const tab = ref<Tab>('retros')
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">⑧ 需求方关系 / 项目复盘 ⭐</span>
      </div>
    </template>
    <el-tabs v-model="tab">
      <el-tab-pane label="项目复盘 (满意度 + 行动项)" name="retros"><RetroList v-if="tab === 'retros'" /></el-tab-pane>
      <el-tab-pane label="续单跟踪 (赢/输/原因)" name="attempts"><AttemptList v-if="tab === 'attempts'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
