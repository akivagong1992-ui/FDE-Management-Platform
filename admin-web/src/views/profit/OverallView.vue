<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getMarginLift, getOverall, type MarginLift, type OverallProfit } from '@/api/profit'

const data = ref<OverallProfit | null>(null)
const lift = ref<MarginLift | null>(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [d, l] = await Promise.all([getOverall(), getMarginLift()])
    data.value = d
    lift.value = l
  } finally { loading.value = false }
}

function fmt(n: number): string {
  return new Intl.NumberFormat('en-HK', { minimumFractionDigits: 2 }).format(n)
}
function pct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <!-- 第一组：基础四件套 -->
    <div v-if="data">
      <el-row :gutter="16">
        <el-col :span="12" style="margin-bottom: 16px">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">总收入</div>
            <div style="font-size: 26px; font-weight: 600; color: #67c23a; margin-top: 8px">
              HK$ {{ fmt(data.total_revenue) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="12" style="margin-bottom: 16px">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">Vendor 服务费</div>
            <div style="font-size: 26px; font-weight: 600; color: #f56c6c; margin-top: 8px">
              HK$ {{ fmt(data.total_vendor_service_fees) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="12" style="margin-bottom: 16px">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">其他支出</div>
            <div style="font-size: 26px; font-weight: 600; color: #f56c6c; margin-top: 8px">
              HK$ {{ fmt(data.total_external_expenses) }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="12" style="margin-bottom: 16px">
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

    <!-- 第二组：FDE 利润率对比（基于已收款 + 客户付款总额 gross_amount） -->
    <div v-if="lift && lift.counted_projects > 0">
      <div style="margin: 20px 0 12px; font-weight: 600; color: #303133">
        FDE 利润率对比
        <span style="color: #909399; font-size: 12px; font-weight: normal; margin-left: 8px">
          已收款项目 {{ lift.counted_projects }} 个 · 客户付款合计
          HK$ {{ fmt(lift.total_gross_revenue) }}
        </span>
      </div>
      <el-row :gutter="16">
        <el-col :span="8" style="margin-bottom: 16px">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">老外包模式 毛利率（假设）</div>
            <div :style="{
              fontSize: '26px', fontWeight: 600, marginTop: '8px',
              color: lift.outsource_margin_pct >= 0 ? '#909399' : '#f56c6c',
            }">
              {{ pct(lift.outsource_margin_pct) }}
            </div>
            <div style="color: #c0c4cc; font-size: 12px; margin-top: 4px">
              = (客户付款 − 外部服务商报价) / 客户付款
            </div>
          </el-card>
        </el-col>
        <el-col :span="8" style="margin-bottom: 16px">
          <el-card shadow="hover">
            <div style="color: #909399; font-size: 13px">FDE 模式 毛利率（实际）</div>
            <div :style="{
              fontSize: '26px', fontWeight: 600, marginTop: '8px',
              color: lift.fde_margin_pct >= 0 ? '#67c23a' : '#f56c6c',
            }">
              {{ pct(lift.fde_margin_pct) }}
            </div>
            <div style="color: #c0c4cc; font-size: 12px; margin-top: 4px">
              = (客户付款 − 团队实际成本) / 客户付款
            </div>
          </el-card>
        </el-col>
        <el-col :span="8" style="margin-bottom: 16px">
          <el-card shadow="hover" style="border: 2px solid #e6a23c">
            <div style="color: #e6a23c; font-size: 13px; font-weight: 600">★ 利润率提升</div>
            <div :style="{
              fontSize: '26px', fontWeight: 700, marginTop: '8px',
              color: lift.margin_lift_pct >= 0 ? '#e6a23c' : '#f56c6c',
            }">
              {{ pct(lift.margin_lift_pct) }} 个百分点
            </div>
            <div style="color: #e6a23c; font-size: 12px; margin-top: 4px">
              多挣 <strong>HK$ {{ fmt(lift.extra_profit) }}</strong>（vendor markup 吸收回来的）
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    <el-alert v-else-if="lift" type="info" :closable="false" show-icon style="margin-top: 16px">
      <template #title>
        暂无可对比项目 — 需要在「项目收入明细」录入 client 已付款的收入并填写
        <strong>客户付款总额</strong> 才能算 FDE vs 老外包利润率对比
      </template>
    </el-alert>
  </div>
</template>
