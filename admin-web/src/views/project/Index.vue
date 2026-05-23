<script setup lang="ts">
import { ref } from 'vue'
import ProjectList from './ProjectList.vue'
import NeedPartyList from './NeedPartyList.vue'
import SalesPersonList from './SalesPersonList.vue'

const tab = ref<'projects' | 'need_parties' | 'sales_persons'>('projects')
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">项目和客户管理</span>
      </div>
    </template>
    <el-tabs v-model="tab">
      <el-tab-pane label="项目列表" name="projects"><ProjectList v-if="tab === 'projects'" /></el-tab-pane>
      <el-tab-pane label="客户列表" name="need_parties"><NeedPartyList v-if="tab === 'need_parties'" /></el-tab-pane>
      <el-tab-pane label="销售人员" name="sales_persons"><SalesPersonList v-if="tab === 'sales_persons'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
