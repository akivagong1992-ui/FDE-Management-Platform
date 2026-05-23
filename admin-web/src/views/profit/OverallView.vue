<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getOverall, type OverallProfit } from '@/api/profit'

const data = ref<OverallProfit | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try { data.value = await getOverall() } finally { loading.value = false }
}

function fmt(n: number): string {
  return new Intl.NumberFormat('en-HK', { minimumFractionDigits: 2 }).format(n)
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div v-if="data">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">总收入</div>
            <div style="font-size: 26px; font-weight: 600; color: #67c23a; margin-top: 8px">
              HK$ {{ fmt(data.total_revenue) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">Vendor 服务费</div>
            <div style="font-size: 26px; font-weight: 600; color: #f56c6c; margin-top: 8px">
              HK$ {{ fmt(data.total_vendor_service_fees) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">外部支出</div>
            <div style="font-size: 26px; font-weight: 600; color: #f56c6c; margin-top: 8px">
              HK$ {{ fmt(data.total_external_expenses) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">团队毛利</div>
            <div :style="{
              fontSize: '26px', fontWeight: 600, marginTop: '8px',
              color: data.team_margin >= 0 ? '#67c23a' : '#f56c6c',
            }">
              HK$ {{ fmt(data.team_margin) }}
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>
