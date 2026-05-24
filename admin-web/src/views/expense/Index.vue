<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import ExpenseList from './ExpenseList.vue'
import VendorFeeList from './VendorFeeList.vue'
import SupplierList from './SupplierList.vue'
import VendorList from '../engineer/VendorList.vue'

type Tab = 'vendor_fees' | 'expenses' | 'suppliers' | 'vendors'
const auth = useAuthStore()
const isVendor = computed(() => auth.role === 'vendor')

// vendor 角色只看 Vendor 支出管理；其他角色看全部
const tab = ref<Tab>(isVendor.value ? 'expenses' : 'vendor_fees')

onMounted(() => {
  if (isVendor.value) tab.value = 'expenses'
})
</script>

<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane v-if="!isVendor" label="Vendor 服务费" name="vendor_fees">
        <VendorFeeList v-if="tab === 'vendor_fees'" />
      </el-tab-pane>
      <el-tab-pane label="Vendor 支出管理" name="expenses">
        <ExpenseList v-if="tab === 'expenses'" />
      </el-tab-pane>
      <el-tab-pane v-if="!isVendor" label="供应商管理" name="suppliers">
        <SupplierList v-if="tab === 'suppliers'" />
      </el-tab-pane>
      <el-tab-pane v-if="!isVendor" label="Vendor 管理" name="vendors">
        <VendorList v-if="tab === 'vendors'" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>
