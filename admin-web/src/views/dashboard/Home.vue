<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { getOverall, type OverallProfit } from '@/api/profit'

// 公共驾驶舱接口（无需登录），admin 首页直接复用
const cockpit = axios.create({ baseURL: '/api/cockpit', timeout: 10000 })

interface OverviewKpi {
  active_projects: number
  team_size: number
  on_time_delivery_rate: number
  delivered_clients: string[]
  by_status: { label: string; count: number }[]
}
interface SavingsAndValue {
  total_savings: number
  total_value_created: number
  total_c_view: number
}

const auth = useAuthStore()
const canSeeMargin = computed(() => ['lead', 'finance', 'admin'].includes(auth.role || ''))

const overview = ref<OverviewKpi | null>(null)
const savings = ref<SavingsAndValue | null>(null)
const profit = ref<OverallProfit | null>(null)
const loading = ref(true)

const STATUS_LABEL: Record<string, string> = {
  drafting: '草拟中', accepting: '验收中', closing: '收尾中',
  in_progress: '进行中', archived: '已归档', cancelled: '已取消',
}

async function load() {
  loading.value = true
  const tasks: Promise<unknown>[] = [
    cockpit.get<OverviewKpi>('/overview').then((r) => (overview.value = r.data)).catch(() => {}),
    cockpit.get<SavingsAndValue>('/savings-and-value').then((r) => (savings.value = r.data)).catch(() => {}),
  ]
  if (canSeeMargin.value) {
    tasks.push(getOverall().then((p) => (profit.value = p)).catch(() => {}))
  }
  await Promise.all(tasks)
  loading.value = false
}

onMounted(load)

const wan = (n: number | null | undefined) =>
  n == null ? '—' : (n / 10000).toLocaleString('zh-CN', { maximumFractionDigits: 1 })
</script>

<template>
  <el-row :gutter="16" v-loading="loading">
    <el-col :span="6">
      <el-card shadow="hover">
        <div class="kpi-label">在管项目</div>
        <div class="kpi-value">{{ overview?.active_projects ?? '—' }}</div>
        <div class="kpi-sub">含进行中 / 验收 / 收尾 / 草拟</div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover">
        <div class="kpi-label">团队规模（在册）</div>
        <div class="kpi-value">{{ overview?.team_size ?? '—' }}</div>
        <div class="kpi-sub">active 状态工程师</div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover">
        <div class="kpi-label">累计降本 (HKD 万)</div>
        <div class="kpi-value">{{ wan(savings?.total_savings) }}</div>
        <div class="kpi-sub">R13 口径，含无收入项目可加值</div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card shadow="hover">
        <div class="kpi-label">
          团队累计毛利 (HKD 万)
          <el-tag v-if="!canSeeMargin" size="small" type="info" style="margin-left: 6px">无权限</el-tag>
        </div>
        <div class="kpi-value">
          {{ canSeeMargin ? wan(profit?.team_margin) : '—' }}
        </div>
        <div class="kpi-sub">口径 A，仅 lead/finance/admin 可见</div>
      </el-card>
    </el-col>
  </el-row>

  <el-row :gutter="16" style="margin-top: 16px" v-loading="loading">
    <el-col :span="14">
      <el-card>
        <template #header>项目状态分布</template>
        <div v-if="!overview?.by_status?.length" class="empty">暂无项目</div>
        <div v-else class="status-list">
          <div v-for="s in overview.by_status" :key="s.label" class="status-row">
            <span class="status-label">{{ STATUS_LABEL[s.label] || s.label }}</span>
            <div class="status-bar">
              <div
                class="status-fill"
                :style="{ width: `${(s.count / Math.max(...overview.by_status.map((x) => x.count))) * 100}%` }"
              />
            </div>
            <span class="status-num">{{ s.count }}</span>
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :span="10">
      <el-card>
        <template #header>
          已交付客户
          <span class="header-sub">{{ overview?.delivered_clients?.length ?? 0 }} 家</span>
        </template>
        <div v-if="!overview?.delivered_clients?.length" class="empty">暂无已交付客户</div>
        <div v-else class="client-chips">
          <el-tag
            v-for="(name, i) in overview.delivered_clients"
            :key="i"
            type="success"
            effect="plain"
            style="margin: 4px 4px 4px 0"
          >
            {{ name }}
          </el-tag>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.kpi-label { color: #909399; font-size: 13px; }
.kpi-value { font-size: 28px; font-weight: 600; margin-top: 6px; color: #303133; }
.kpi-sub { color: #c0c4cc; font-size: 11px; margin-top: 4px; }

.empty { color: #909399; padding: 20px; text-align: center; }

.status-list { display: flex; flex-direction: column; gap: 10px; }
.status-row { display: grid; grid-template-columns: 90px 1fr 50px; gap: 12px; align-items: center; }
.status-label { color: #606266; font-size: 13px; }
.status-bar { height: 14px; background: #f0f2f5; border-radius: 999px; overflow: hidden; }
.status-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  transition: width 0.6s ease;
}
.status-num { font-family: 'Courier New', monospace; color: #409eff; font-weight: 600; text-align: right; }

.client-chips { padding: 4px; }
.header-sub { color: #909399; font-size: 12px; margin-left: 8px; }
</style>
