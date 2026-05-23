<script setup lang="ts">
import { ref } from 'vue'
import GrowthView from './GrowthView.vue'
import TrainingList from './TrainingList.vue'
import IDPList from './IDPList.vue'

type Tab = 'growth' | 'trainings' | 'idps'
const tab = ref<Tab>('growth')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="成长曲线 / 季度快照" name="growth"><GrowthView v-if="tab === 'growth'" /></el-tab-pane>
      <el-tab-pane label="培训记录" name="trainings"><TrainingList v-if="tab === 'trainings'" /></el-tab-pane>
      <el-tab-pane label="IDP 个人发展计划" name="idps"><IDPList v-if="tab === 'idps'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
