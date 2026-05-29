<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import {
  getOverall, getBySalesPerson, getByNeedParty,
  type OverallProfit, type BySalesRow, type ByNeedPartyRow,
} from '@/api/profit'
import { listProjects, type BidOutcome, type Project } from '@/api/projects'
import { listRevenues, type ProjectRevenue } from '@/api/projectRevenues'
import { listExpenses, type ExpenseRequest } from '@/api/expenses'
import { listFees, type VendorServiceFee } from '@/api/vendorServiceFees'
import { fmtWan } from '@/utils/format'

const cockpit = axios.create({
  baseURL: '/api/cockpit', timeout: 10000,
  headers: { 'X-Cockpit-Token': 'cockpit-dev-token' },
})
const auth = useAuthStore()
const canSeeMargin = computed(() => ['lead', 'finance', 'admin'].includes(auth.role || ''))

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

const overview = ref<OverviewKpi | null>(null)
const savings = ref<SavingsAndValue | null>(null)
const profit = ref<OverallProfit | null>(null)
const projects = ref<Project[]>([])
const revenues = ref<ProjectRevenue[]>([])
const expenses = ref<ExpenseRequest[]>([])
const vsfs = ref<VendorServiceFee[]>([])
const bySales = ref<BySalesRow[]>([])
const byClient = ref<ByNeedPartyRow[]>([])
const loading = ref(true)

const STATUS_LABEL: Record<string, string> = {
  drafting: '草拟', in_progress: '进行中', accepting: '验收',
  closing: '收尾', archived: '已归档', cancelled: '已取消',
}
const BID_OUTCOME_LABEL: Record<BidOutcome, string> = {
  pending: '投标中', won: '已中标', lost: '已丢标', escaped: '中标后跑单',
}
const BID_COLORS: Record<BidOutcome, string> = {
  won: '#67c23a', pending: '#909399', lost: '#f56c6c', escaped: '#e6a23c',
}
const EXPENSE_TYPE_LABEL: Record<string, string> = {
  material: '耗材',
  subcontract: '对外分包高级服务',
  temp_labor: '临时人力补充',
  license: '第三方平台 / 许可证',
  travel: '差旅 / 外勤',
  training: '外部培训费',
  other: '其他',
  outsource_engineer: '外包工程师支出',
}

async function load() {
  loading.value = true
  const tasks: Promise<unknown>[] = [
    cockpit.get<OverviewKpi>('/overview').then((r) => (overview.value = r.data)).catch(() => {}),
    cockpit.get<SavingsAndValue>('/savings-and-value').then((r) => (savings.value = r.data)).catch(() => {}),
    listProjects().then((p) => (projects.value = p)).catch(() => {}),
    listRevenues().then((r) => (revenues.value = r)).catch(() => {}),
    listExpenses().then((r) => (expenses.value = r)).catch(() => {}),
    listFees().then((r) => (vsfs.value = r)).catch(() => {}),
  ]
  if (canSeeMargin.value) {
    tasks.push(getOverall().then((p) => (profit.value = p)).catch(() => {}))
    tasks.push(getBySalesPerson().then((r) => (bySales.value = r)).catch(() => {}))
    tasks.push(getByNeedParty().then((r) => (byClient.value = r)).catch(() => {}))
  }
  await Promise.all(tasks)
  loading.value = false
}

onMounted(load)

const wan = (n: number | null | undefined) => fmtWan(n)

// ─ KPI 计算 ──────────────────────────────────────────────────
const wonInProgress = computed(() =>
  projects.value.filter(
    (p) => p.bid_outcome === 'won' && ['drafting', 'in_progress', 'accepting'].includes(p.status),
  ).length,
)

// 欠款仅算 status ∈ {accepting, closing, archived} 的项目：
// 验收/收尾/已归档视为已交付，款项理应到位，负 margin 即为欠款
// 进行中/草拟款项还在路上不算；cancelled 已取消不算
const SETTLED_STATUS = new Set(['accepting', 'closing', 'archived'])
const salesDebt = computed(() =>
  bySales.value.reduce((acc, s) => {
    const settledMargin = s.projects
      .filter((p) => SETTLED_STATUS.has(p.status))
      .reduce((sum, p) => sum + p.margin, 0)
    return acc + (settledMargin < 0 ? -settledMargin : 0)
  }, 0),
)
const clientDebt = computed(() =>
  byClient.value.reduce((acc, c) => {
    const settledMargin = c.projects
      .filter((p) => SETTLED_STATUS.has(p.status))
      .reduce((sum, p) => sum + p.margin, 0)
    return acc + (settledMargin < 0 ? -settledMargin : 0)
  }, 0),
)

// ─ 项目盘面 ──────────────────────────────────────────────────
const bidOutcomeStats = computed(() => {
  const counts: Record<BidOutcome, number> = { won: 0, pending: 0, lost: 0, escaped: 0 }
  for (const p of projects.value) {
    if (p.kind === 'revenue') counts[p.bid_outcome] = (counts[p.bid_outcome] || 0) + 1
  }
  const total = counts.won + counts.pending + counts.lost + counts.escaped
  return { counts, total }
})

const statusMax = computed(() =>
  Math.max(1, ...(overview.value?.by_status || []).map((x) => x.count)),
)

// 最近 6 个月（YYYY-MM）的累计团队入账
// 仅算 kind=revenue 且 bid_outcome=won 的项目（与首页"团队利润"口径 A 一致）
const revenueTrend = computed(() => {
  const projMap: Record<number, Project> = {}
  for (const p of projects.value) projMap[p.id] = p

  const buckets: Record<string, number> = {}
  for (const r of revenues.value) {
    if (!r.recognized_date) continue
    const p = projMap[r.project_id]
    if (!p || p.kind !== 'revenue' || p.bid_outcome !== 'won') continue
    const ym = r.recognized_date.slice(0, 7)
    buckets[ym] = (buckets[ym] || 0) + Number(r.amount || 0)
  }
  const keys = Object.keys(buckets).sort()
  return keys.slice(-6).map((ym) => ({ ym, amount: buckets[ym] }))
})

const maxRevenue = computed(() => Math.max(1, ...revenueTrend.value.map((d) => d.amount)))

// 客户 Top5（按累计团队入账）—— 与口径 A 一致，仅算 won-revenue 项目
const topCustomers = computed(() => {
  const projMap: Record<number, Project> = {}
  for (const p of projects.value) projMap[p.id] = p

  const agg: Record<string, { name: string; team_revenue: number; projects: Set<number> }> = {}
  for (const r of revenues.value) {
    const p = projMap[r.project_id]
    if (!p || p.kind !== 'revenue' || p.bid_outcome !== 'won') continue
    const name = p.need_party_name || `#${p.need_party_id}`
    if (!agg[name]) agg[name] = { name, team_revenue: 0, projects: new Set() }
    agg[name].team_revenue += Number(r.amount || 0)
    agg[name].projects.add(p.id)
  }
  return Object.values(agg)
    .map((x) => ({ name: x.name, team_revenue: x.team_revenue, project_count: x.projects.size }))
    .sort((a, b) => b.team_revenue - a.team_revenue)
    .slice(0, 5)
})

// 成本开销排名（按 expense_type 分组，不含 rejected）
const topExpensesByType = computed(() => {
  const agg: Record<string, { code: string; label: string; total: number; count: number }> = {}
  for (const e of expenses.value) {
    if (e.status === 'rejected') continue
    const code = e.expense_type
    const label = e.expense_type_label || EXPENSE_TYPE_LABEL[code] || code
    if (!agg[code]) agg[code] = { code, label, total: 0, count: 0 }
    agg[code].total += Number(e.amount || 0)
    agg[code].count += 1
  }
  return Object.values(agg)
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
})

// Vendor 收入项目排名（按 Vendor 公司分组 VSF 金额）
const topVendorsByIncome = computed(() => {
  const agg: Record<number, { vendor_id: number; name: string; total: number; count: number }> = {}
  for (const v of vsfs.value) {
    const vid = v.vendor_id
    const name = v.vendor_name || `Vendor #${vid}`
    if (!agg[vid]) agg[vid] = { vendor_id: vid, name, total: 0, count: 0 }
    agg[vid].total += Number(v.amount || 0)
    agg[vid].count += 1
  }
  return Object.values(agg)
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
})

const maxExpenseType = computed(() => Math.max(1, ...topExpensesByType.value.map((x) => x.total)))
const maxVendorIncome = computed(() => Math.max(1, ...topVendorsByIncome.value.map((x) => x.total)))
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- ① 8 KPI 横排 ─────────────────────────────────────── -->
    <el-row :gutter="12" class="kpi-row">
      <el-col :span="3">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">在管项目</div>
          <div class="kpi-value">{{ overview?.active_projects ?? '—' }}</div>
        </el-card>
      </el-col>
      <el-col :span="3">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">中标待执行</div>
          <div class="kpi-value" style="color: #67c23a">{{ wonInProgress }}</div>
        </el-card>
      </el-col>
      <el-col v-if="canSeeMargin" :span="3">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">团队利润 (万)</div>
          <div class="kpi-value"
               :style="(profit?.team_margin ?? 0) < 0 ? { color: '#f56c6c' } : { color: '#67c23a' }">
            {{ wan(profit?.team_margin) }}
          </div>
        </el-card>
      </el-col>
      <el-col v-if="canSeeMargin" :span="3">
        <el-card shadow="hover" class="kpi-card" :class="{ alert: salesDebt > 0 }">
          <div class="kpi-label">销售欠款 (万)</div>
          <div class="kpi-value" :style="{ color: salesDebt > 0 ? '#f56c6c' : '#909399' }">
            {{ wan(salesDebt) }}
          </div>
        </el-card>
      </el-col>
      <el-col v-if="canSeeMargin" :span="3">
        <el-card shadow="hover" class="kpi-card" :class="{ alert: clientDebt > 0 }">
          <div class="kpi-label">客户欠款 (万)</div>
          <div class="kpi-value" :style="{ color: clientDebt > 0 ? '#f56c6c' : '#909399' }">
            {{ wan(clientDebt) }}
          </div>
        </el-card>
      </el-col>
      <el-col v-if="canSeeMargin" :span="3">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">服务费支出 (万)</div>
          <div class="kpi-value" style="color: #409eff">{{ wan(profit?.total_vendor_service_fees) }}</div>
        </el-card>
      </el-col>
      <el-col v-if="canSeeMargin" :span="3">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">vendor 支出 (万)</div>
          <div class="kpi-value" style="color: #e6a23c">{{ wan(profit?.total_external_expenses) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ②③ 项目盘面 + 财务 ─────────────────────────────────── -->
    <el-row :gutter="16" class="middle-row">
      <el-col :span="canSeeMargin ? 14 : 24">
        <el-card class="block-card">
          <template #header>
            <span class="card-title">项目盘面</span>
            <span class="card-sub">投标结果 + 执行状态</span>
          </template>

          <div class="section-h">投标结果（仅 revenue 项目，{{ bidOutcomeStats.total }} 个）</div>
          <div v-if="bidOutcomeStats.total === 0" class="empty">暂无</div>
          <template v-else>
            <div class="stacked-bar">
              <div
                v-for="key in (['won','pending','lost','escaped'] as BidOutcome[])"
                :key="key"
                v-show="bidOutcomeStats.counts[key] > 0"
                class="stacked-seg"
                :style="{
                  width: `${(bidOutcomeStats.counts[key] / bidOutcomeStats.total) * 100}%`,
                  background: BID_COLORS[key],
                }"
                :title="`${BID_OUTCOME_LABEL[key]}: ${bidOutcomeStats.counts[key]}`"
              />
            </div>
            <div class="legend-row">
              <span
                v-for="key in (['won','pending','lost','escaped'] as BidOutcome[])"
                :key="key" class="legend-item"
              >
                <span class="legend-dot" :style="{ background: BID_COLORS[key] }" />
                {{ BID_OUTCOME_LABEL[key] }} <strong>{{ bidOutcomeStats.counts[key] }}</strong>
              </span>
            </div>
          </template>

          <el-divider style="margin: 16px 0" />

          <div class="section-h">执行状态（全部项目，{{ projects.length }} 个）</div>
          <div v-if="!overview?.by_status?.length" class="empty">暂无</div>
          <div v-else class="status-list">
            <div v-for="s in overview.by_status" :key="s.label" class="status-row">
              <span class="status-label">{{ STATUS_LABEL[s.label] || s.label }}</span>
              <div class="status-bar">
                <div class="status-fill" :style="{ width: `${(s.count / statusMax) * 100}%` }" />
              </div>
              <span class="status-num">{{ s.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col v-if="canSeeMargin" :span="10">
        <el-card class="block-card">
          <template #header>
            <span class="card-title">近 6 月团队入账</span>
            <span class="card-sub">按 recognized_date 月度聚合（万 HKD）</span>
          </template>
          <div v-if="!revenueTrend.length" class="empty">暂无收入记录</div>
          <div v-else class="trend-chart">
            <div v-for="d in revenueTrend" :key="d.ym" class="trend-col">
              <div class="trend-num">{{ wan(d.amount) }}</div>
              <div class="trend-bar" :style="{ height: `${(d.amount / maxRevenue) * 100}%` }" />
              <div class="trend-x">{{ d.ym.slice(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ④ 三大排名榜 ─────────────────────────────────────── -->
    <el-row v-if="canSeeMargin" :gutter="16">
      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <span class="card-title">客户 Top 5 入账</span>
            <span class="card-sub">累计团队入账（万 HKD）</span>
          </template>
          <div v-if="!topCustomers.length" class="empty">暂无数据</div>
          <div v-else class="rank-list">
            <div v-for="(c, i) in topCustomers" :key="c.name" class="rank-row">
              <span class="rank-no" :class="`rank-${i + 1}`">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="rank-name">{{ c.name }}</span>
              <span class="rank-meta">{{ c.project_count }} 项目</span>
              <span class="rank-amount">{{ wan(c.team_revenue) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <span class="card-title">成本开销 Top 5</span>
            <span class="card-sub">按支出类型聚合（万 HKD）</span>
          </template>
          <div v-if="!topExpensesByType.length" class="empty">暂无支出</div>
          <div v-else class="rank-list">
            <div v-for="(e, i) in topExpensesByType" :key="e.code" class="rank-row-bar">
              <span class="rank-no" :class="`rank-${i + 1}`">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="rank-name">{{ e.label }}</span>
              <div class="rank-bar">
                <div class="rank-bar-fill expense"
                     :style="{ width: `${(e.total / maxExpenseType) * 100}%` }" />
              </div>
              <span class="rank-amount expense">{{ wan(e.total) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="block-card">
          <template #header>
            <span class="card-title">Vendor 收入 Top 5</span>
            <span class="card-sub">VSF 累计（万 HKD）</span>
          </template>
          <div v-if="!topVendorsByIncome.length" class="empty">暂无 VSF 记录</div>
          <div v-else class="rank-list">
            <div v-for="(v, i) in topVendorsByIncome" :key="v.vendor_id" class="rank-row-bar">
              <span class="rank-no" :class="`rank-${i + 1}`">{{ String(i + 1).padStart(2, '0') }}</span>
              <span class="rank-name">{{ v.name }}</span>
              <div class="rank-bar">
                <div class="rank-bar-fill vendor"
                     :style="{ width: `${(v.total / maxVendorIncome) * 100}%` }" />
              </div>
              <span class="rank-amount">{{ wan(v.total) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 16px; }

/* ─ KPI cards (8 in a row, slim) ──────── */
.kpi-card { padding: 4px 6px; }
.kpi-card.alert { border-color: #fbc4c4; background: linear-gradient(180deg, #fff8f8 0%, #fff 100%); }
.kpi-label {
  color: #909399; font-size: 12px;
  display: flex; align-items: center;
  min-height: 18px; white-space: nowrap;
}
.kpi-value { font-size: 24px; font-weight: 600; margin-top: 6px; color: #303133; line-height: 1.1; }
.kpi-sub { color: #c0c4cc; font-size: 11px; margin-top: 4px; }

/* ─ Cards ─ */
.block-card { height: 100%; }
.card-title { font-weight: 600; color: #303133; }
.card-sub { color: #909399; font-size: 12px; margin-left: 8px; font-weight: normal; }
.section-h { color: #606266; font-size: 13px; font-weight: 500; margin-bottom: 8px; }
.empty { color: #c0c4cc; padding: 20px; text-align: center; font-size: 13px; }

/* stacked bar */
.stacked-bar {
  display: flex; height: 22px; border-radius: 6px; overflow: hidden;
  background: #f0f2f5;
}
.stacked-seg { transition: width 0.5s ease; }
.legend-row {
  display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px;
  font-size: 12px; color: #606266;
}
.legend-item { display: inline-flex; align-items: center; gap: 4px; }
.legend-dot {
  display: inline-block; width: 10px; height: 10px;
  border-radius: 2px; vertical-align: middle;
}
.legend-item strong { color: #303133; margin-left: 2px; }

/* status horizontal bars */
.status-list { display: flex; flex-direction: column; gap: 8px; }
.status-row { display: grid; grid-template-columns: 70px 1fr 40px; gap: 12px; align-items: center; }
.status-label { color: #606266; font-size: 13px; }
.status-bar { height: 12px; background: #f0f2f5; border-radius: 999px; overflow: hidden; }
.status-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  transition: width 0.6s ease;
}
.status-num {
  font-family: 'Courier New', monospace; color: #409eff;
  font-weight: 600; text-align: right; font-size: 13px;
}

/* trend mini-bars */
.trend-chart {
  display: flex; align-items: flex-end; gap: 12px;
  height: 140px; padding: 8px 4px 0;
}
.trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.trend-num {
  font-size: 11px; color: #909399; margin-bottom: 4px;
  font-family: 'Courier New', monospace;
}
.trend-bar {
  width: 100%; max-width: 32px;
  background: linear-gradient(180deg, #409eff, #67c23a);
  border-radius: 4px 4px 0 0;
  transition: height 0.6s ease;
  min-height: 2px;
}
.trend-x { color: #909399; font-size: 11px; margin-top: 6px; }

/* ─ rank lists ─ */
.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-row {
  display: grid; grid-template-columns: 36px 1fr 70px 80px; gap: 8px;
  align-items: center; font-size: 13px;
}
.rank-row-bar {
  display: grid; grid-template-columns: 36px 100px 1fr 80px; gap: 8px;
  align-items: center; font-size: 13px;
}
.rank-no {
  font-family: 'Courier New', monospace; font-weight: 700;
  text-align: center; color: #c0c4cc;
}
.rank-1 { color: #e6a23c; }
.rank-2 { color: #909399; }
.rank-3 { color: #c97a3a; }
.rank-name { color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-meta { color: #909399; font-size: 12px; text-align: right; }
.rank-amount {
  font-family: 'Courier New', monospace; color: #67c23a;
  font-weight: 600; text-align: right;
}
.rank-amount.expense { color: #e6a23c; }
.rank-bar {
  height: 10px; background: #f0f2f5; border-radius: 999px; overflow: hidden;
}
.rank-bar-fill {
  height: 100%; transition: width 0.6s ease;
}
.rank-bar-fill.expense {
  background: linear-gradient(90deg, #f78989, #e6a23c);
}
.rank-bar-fill.vendor {
  background: linear-gradient(90deg, #409eff, #00bcd4);
}
</style>
