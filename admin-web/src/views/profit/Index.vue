<script setup lang="ts">
import { ref } from 'vue'
import OverallView from './OverallView.vue'
import BySalesView from './BySalesView.vue'
import ByClientView from './ByClientView.vue'
import RevenueList from './RevenueList.vue'

type Tab = 'overall' | 'by_sales' | 'by_client' | 'revenues'
const tab = ref<Tab>('overall')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="口径 A · 团队总览" name="overall"><OverallView v-if="tab === 'overall'" /></el-tab-pane>
      <el-tab-pane label="口径 B · 按销售人员" name="by_sales"><BySalesView v-if="tab === 'by_sales'" /></el-tab-pane>
      <el-tab-pane label="口径 B · 按客户" name="by_client"><ByClientView v-if="tab === 'by_client'" /></el-tab-pane>
      <el-tab-pane label="项目收入登记" name="revenues"><RevenueList v-if="tab === 'revenues'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
