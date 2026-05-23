<script setup lang="ts">
import { ref } from 'vue'
import ExpenseList from './ExpenseList.vue'
import VendorFeeList from './VendorFeeList.vue'
import SupplierList from './SupplierList.vue'
import VendorList from '../engineer/VendorList.vue'

type Tab = 'vendor_fees' | 'expenses' | 'suppliers' | 'vendors'
const tab = ref<Tab>('vendor_fees')
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="Vendor 服务费" name="vendor_fees"><VendorFeeList v-if="tab === 'vendor_fees'" /></el-tab-pane>
      <el-tab-pane label="其他支出管理" name="expenses"><ExpenseList v-if="tab === 'expenses'" /></el-tab-pane>
      <el-tab-pane label="供应商管理" name="suppliers"><SupplierList v-if="tab === 'suppliers'" /></el-tab-pane>
      <el-tab-pane label="Vendor 管理" name="vendors"><VendorList v-if="tab === 'vendors'" /></el-tab-pane>
    </el-tabs>
  </el-card>
</template>
