<script setup lang="ts">
import { ref } from 'vue'
import ProjectList from './ProjectList.vue'
import RevenueList from './RevenueList.vue'
import NeedPartyList from './NeedPartyList.vue'
import SalesPersonList from './SalesPersonList.vue'

const tab = ref<'projects' | 'revenues' | 'need_parties' | 'sales_persons'>('projects')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="项目列表" name="projects"><ProjectList v-if="tab === 'projects'" /></el-tab-pane>
      <el-tab-pane label="收入列表" name="revenues"><RevenueList v-if="tab === 'revenues'" /></el-tab-pane>
      <el-tab-pane label="客户列表" name="need_parties"><NeedPartyList v-if="tab === 'need_parties'" /></el-tab-pane>
      <el-tab-pane label="销售人员" name="sales_persons"><SalesPersonList v-if="tab === 'sales_persons'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
