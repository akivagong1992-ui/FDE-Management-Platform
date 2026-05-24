<script setup lang="ts">
import { ref } from 'vue'
import OverallView from './OverallView.vue'
import BySalesView from './BySalesView.vue'
import ByClientView from './ByClientView.vue'

type Tab = 'overall' | 'by_sales' | 'by_client'
const tab = ref<Tab>('overall')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="总体利润一览" name="overall"><OverallView v-if="tab === 'overall'" /></el-tab-pane>
      <el-tab-pane label="每销售利润" name="by_sales"><BySalesView v-if="tab === 'by_sales'" /></el-tab-pane>
      <el-tab-pane label="每客户利润" name="by_client"><ByClientView v-if="tab === 'by_client'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
