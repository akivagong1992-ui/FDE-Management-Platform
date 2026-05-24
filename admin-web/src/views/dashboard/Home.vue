<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getOverall, type OverallProfit } from '@/api/profit'
import { listProjects, type BidOutcome, type Project } from '@/api/projects'
import { listRevenues, type ProjectRevenue } from '@/api/projectRevenues'
import { fmtWan } from '@/utils/format'

const cockpit = axios.create({ baseURL: '/api/cockpit', timeout: 10000 })
const router = useRouter()
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
interface EfficiencyStats {
  due_soon_count: number
  due_soon: { project_id: number; name: string; days_to_due: number; overdue: boolean }[]
  on_time_rate: number
}

const overview = ref<OverviewKpi | null>(null)
const savings = ref<SavingsAndValue | null>(null)
const profit = ref<OverallProfit | null>(null)
const efficiency = ref<EfficiencyStats | null>(null)
const projects = ref<Project[]>([])
const revenues = ref<ProjectRevenue[]>([])
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

async function load() {
  loading.value = true
  const tasks: Promise<unknown>[] = [
    cockpit.get<OverviewKpi>('/overview').then((r) => (overview.value = r.data)).catch(() => {}),
    cockpit.get<SavingsAndValue>('/savings-and-value').then((r) => (savings.value = r.data)).catch(() => {}),
    cockpit.get<EfficiencyStats>('/efficiency-stats').then((r) => (efficiency.value = r.data)).catch(() => {}),
    listProjects().then((p) => (projects.value = p)).catch(() => {}),
    listRevenues().then((r) => (revenues.value = r)).catch(() => {}),
  ]
  if (canSeeMargin.value) {
    tasks.push(getOverall().then((p) => (profit.value = p)).catch(() => {}))
  }
  await Promise.all(tasks)
  loading.value = false
}

onMounted(load)

const wan = (n: number | null | undefined) => fmtWan(n)

// ─ Section 1 KPIs ───────────────────────────────────────────
const wonInProgress = computed(() =>
  projects.value.filter(
    (p) => p.bid_outcome === 'won' && ['drafting', 'in_progress', 'accepting'].includes(p.status),
  ).length,
)

const wonWithoutBench = computed(() =>
  projects.value.filter(
    (p) => p.bid_outcome === 'won' && p.kind === 'revenue' && p.outsource_benchmark_amount == null,
  ).length,
)

const riskCount = computed(() => (efficiency.value?.due_soon_count ?? 0) + wonWithoutBench.value)

// ─ Section 2 · 项目盘面 ─────────────────────────────────────
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

// ─ Section 3 · 财务 ─────────────────────────────────────────
// 最近 6 个月（YYYY-MM）的累计团队入账
const revenueTrend = computed(() => {
  const buckets: Record<string, number> = {}
  for (const r of revenues.value) {
    if (!r.recognized_date) continue
    const ym = r.recognized_date.slice(0, 7)
    buckets[ym] = (buckets[ym] || 0) + Number(r.amount || 0)
  }
  const keys = Object.keys(buckets).sort()
  return keys.slice(-6).map((ym) => ({ ym, amount: buckets[ym] }))
})

const maxRevenue = computed(() => Math.max(1, ...revenueTrend.value.map((d) => d.amount)))

// 客户 Top5（按累计团队入账）
const topCustomers = computed(() => {
  const projMap: Record<number, Project> = {}
  for (const p of projects.value) projMap[p.id] = p

  const agg: Record<string, { name: string; team_revenue: number; projects: Set<number> }> = {}
  for (const r of revenues.value) {
    const p = projMap[r.project_id]
    if (!p) continue
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
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- ① 6 KPI 横排 ─────────────────────────────────────── -->
    <el-row :gutter="12" class="kpi-row">
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">在管项目</div>
          <div class="kpi-value">{{ overview?.active_projects ?? '—' }}</div>
          <div class="kpi-sub">进行中 / 验收 / 收尾</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">已中标待执行</div>
          <div class="kpi-value" style="color: #67c23a">{{ wonInProgress }}</div>
          <div class="kpi-sub">需派工程师跟进</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">累计降本 (HKD 万)</div>
          <div class="kpi-value" style="color: #e6a23c">{{ wan(savings?.total_c_view) }}</div>
          <div class="kpi-sub">C 口径 · 含无收入项目</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">
            团队真实利润 (HKD 万)
            <el-tooltip v-if="canSeeMargin" placement="top">
              <template #content>
                <div style="max-width: 320px; line-height: 1.6">
                  <strong>= VSF − 全部支出</strong>（vendor markup 视角）<br /><br />
                  vendor 是受控壳，它从 VSF 自留的 markup = 团队真实利润。<br /><br />
                  <span style="color: #e6a23c">⚠</span> 依赖「外包工程师支出」录入完整度；未录全 → 数字偏高。
                </div>
              </template>
              <span style="cursor: help; color: #c0c4cc; font-size: 11px; margin-left: 2px">ⓘ</span>
            </el-tooltip>
            <el-tag v-if="!canSeeMargin" size="small" type="info" style="margin-left: 4px">无权限</el-tag>
          </div>
          <div class="kpi-value"
               :style="canSeeMargin && (profit?.team_margin ?? 0) < 0 ? { color: '#f56c6c' } : { color: '#67c23a' }">
            {{ canSeeMargin ? wan(profit?.team_margin) : '—' }}
          </div>
          <div class="kpi-sub">vendor markup · lead/finance/admin</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">团队规模</div>
          <div class="kpi-value">{{ overview?.team_size ?? '—' }}</div>
          <div class="kpi-sub">在职工程师</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card" :class="{ alert: riskCount > 0 }">
          <div class="kpi-label">风险预警</div>
          <div class="kpi-value" :style="{ color: riskCount > 0 ? '#f56c6c' : '#67c23a' }">
            {{ riskCount }}
          </div>
          <div class="kpi-sub">即将到期 + 缺报价</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ②③ 项目盘面 + 财务 ─────────────────────────────────── -->
    <el-row :gutter="16" class="middle-row">
      <el-col :span="14">
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

      <el-col :span="10">
        <el-card class="block-card" style="margin-bottom: 16px">
          <template #header>
            <span class="card-title">近 6 月团队入账</span>
            <span class="card-sub">按 recognized_date 月度聚合</span>
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
    </el-row>

    <!-- ④ 风险预警 + 关键指标横排 ─────────────────────────── -->
    <el-card class="block-card risk-card">
      <template #header><span class="card-title">⚠️ 风险与关键指标</span></template>
      <el-row :gutter="12">
        <el-col :span="6">
          <div
            class="risk-item"
            :class="{ alert: (efficiency?.due_soon_count ?? 0) > 0 }"
            @click="router.push('/project')"
          >
            <div class="risk-num">{{ efficiency?.due_soon_count ?? 0 }}</div>
            <div class="risk-label">14 天内到期项目</div>
            <div class="risk-sub">含已逾期，需要催办</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div
            class="risk-item"
            :class="{ alert: wonWithoutBench > 0 }"
            @click="router.push('/project')"
          >
            <div class="risk-num">{{ wonWithoutBench }}</div>
            <div class="risk-label">已中标缺报价</div>
            <div class="risk-sub">savings 暂被低估</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="risk-item positive">
            <div class="risk-num">{{ ((efficiency?.on_time_rate ?? 0) * 100).toFixed(0) }}%</div>
            <div class="risk-label">按时交付率</div>
            <div class="risk-sub">已 close/archived 项目</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="risk-item positive">
            <div class="risk-num">{{ overview?.delivered_clients?.length ?? 0 }}</div>
            <div class="risk-label">已交付客户</div>
            <div class="risk-sub">累计累积</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 16px; }

/* ─ KPI cards (slim, 6 in a row) ───────── */
.kpi-card { padding: 4px 6px; }
.kpi-card.alert { border-color: #fbc4c4; background: linear-gradient(180deg, #fff8f8 0%, #fff 100%); }
.kpi-label { color: #909399; font-size: 12px; display: flex; align-items: center; }
.kpi-value { font-size: 26px; font-weight: 600; margin-top: 6px; color: #303133; line-height: 1.1; }
.kpi-sub { color: #c0c4cc; font-size: 11px; margin-top: 4px; }

/* ─ Middle row (project board + finance) ─ */
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

/* customer rank */
.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-row {
  display: grid; grid-template-columns: 36px 1fr 70px 80px; gap: 8px;
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

/* risk row */
.risk-item {
  padding: 16px; border-radius: 6px; background: #fafbfc;
  cursor: pointer; transition: all 0.2s;
  border: 1px solid transparent;
}
.risk-item:hover { background: #f5f7fa; transform: translateY(-1px); }
.risk-item.alert {
  background: linear-gradient(180deg, #fff5f5 0%, #fff 100%);
  border-color: #fbc4c4;
}
.risk-item.positive { cursor: default; }
.risk-item.positive:hover { transform: none; background: #fafbfc; }
.risk-num {
  font-size: 28px; font-weight: 600; color: #303133; line-height: 1;
}
.risk-item.alert .risk-num { color: #f56c6c; }
.risk-item.positive .risk-num { color: #67c23a; }
.risk-label { color: #606266; font-size: 13px; margin-top: 6px; font-weight: 500; }
.risk-sub { color: #c0c4cc; font-size: 11px; margin-top: 2px; }
</style>
