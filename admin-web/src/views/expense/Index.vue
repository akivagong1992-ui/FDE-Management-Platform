<script setup lang="ts">
import { ref } from 'vue'
import ExpenseList from './ExpenseList.vue'
import VendorFeeList from './VendorFeeList.vue'
import SupplierList from './SupplierList.vue'

type Tab = 'expenses' | 'vendor_fees' | 'suppliers'
const tab = ref<Tab>('expenses')
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">④ 外部支出管理 + Vendor 服务费</span>
      </div>
    </template>
    <el-tabs v-model="tab">
      <el-tab-pane label="外部支出（6 类）" name="expenses"><ExpenseList v-if="tab === 'expenses'" /></el-tab-pane>
      <el-tab-pane label="Vendor 服务费" name="vendor_fees"><VendorFeeList v-if="tab === 'vendor_fees'" /></el-tab-pane>
      <el-tab-pane label="供应商档案" name="suppliers"><SupplierList v-if="tab === 'suppliers'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
