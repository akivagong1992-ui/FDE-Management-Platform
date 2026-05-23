<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const cockpit = axios.create({ baseURL: '/api/cockpit', timeout: 10000 })

interface InProgressProject {
  project_id: number
  name: string
  status: string
  planned_start: string | null
  planned_end: string | null
  overdue: boolean
}
interface EfficiencyStats {
  active_count: number
  completed_this_month: number
  delivered_total: number
  due_soon_count: number
  in_progress_projects: InProgressProject[]
  today: string
}

const STATUS_LABEL: Record<string, string> = {
  drafting: '立项', in_progress: '进行中', accepting: '验收',
  closing: '收尾', archived: '归档',
}
const STATUS_TYPE: Record<string, 'primary' | 'success' | 'info' | 'warning' | 'danger'> = {
  drafting: 'info', in_progress: 'primary', accepting: 'warning',
  closing: 'success', archived: 'success',
}

const stats = ref<EfficiencyStats | null>(null)
const loading = ref(true)
const filter = ref<'all' | 'overdue' | 'due_soon'>('all')

async function load() {
  loading.value = true
  try {
    const r = await cockpit.get<EfficiencyStats>('/efficiency-stats')
    stats.value = r.data
  } finally {
    loading.value = false
  }
}
onMounted(load)

function daysToDue(p: InProgressProject): number | null {
  if (!p.planned_end || !stats.value) return null
  const end = new Date(p.planned_end).getTime()
  const today = new Date(stats.value.today).getTime()
  return Math.round((end - today) / 86400000)
}

function progressPct(p: InProgressProject): number {
  if (!p.planned_start || !p.planned_end || !stats.value) return 0
  const start = new Date(p.planned_start).getTime()
  const end = new Date(p.planned_end).getTime()
  const today = new Date(stats.value.today).getTime()
  if (end <= start) return 100
  return Math.max(0, Math.min(100, Math.round(((today - start) / (end - start)) * 100)))
}

const overdueCount = computed(() =>
  (stats.value?.in_progress_projects || []).filter((p) => p.overdue).length,
)
const dueSoonInListCount = computed(() =>
  (stats.value?.in_progress_projects || []).filter((p) => {
    const d = daysToDue(p)
    return d !== null && d >= 0 && d <= 14
  }).length,
)

const filteredProjects = computed(() => {
  const all = stats.value?.in_progress_projects || []
  if (filter.value === 'overdue') return all.filter((p) => p.overdue)
  if (filter.value === 'due_soon') {
    return all.filter((p) => {
      const d = daysToDue(p)
      return d !== null && d >= 0 && d <= 14
    })
  }
  return all
})

const dueLabel = (p: InProgressProject) => {
  const d = daysToDue(p)
  if (d === null) return '—'
  if (d < 0) return `逾期 ${-d} 天`
  if (d === 0) return '今天到期'
  return `还有 ${d} 天`
}
const dueTagType = (p: InProgressProject) => {
  const d = daysToDue(p)
  if (d === null) return 'info'
  if (d < 0) return 'danger'
  if (d <= 14) return 'warning'
  return 'success'
}
</script>

<template>
  <el-card v-loading="loading">
    <div style="display: flex; justify-content: flex-end; color: #909399; font-size: 12px; margin-bottom: 8px">
      数据日期 {{ stats?.today || '—' }}
    </div>

    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="kpi-label">在管项目</div>
          <div class="kpi-value">{{ stats?.active_count ?? '—' }}</div>
          <div class="kpi-sub">含立项 / 进行中 / 验收</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="kpi-label">本月完成</div>
          <div class="kpi-value">{{ stats?.completed_this_month ?? '—' }}</div>
          <div class="kpi-sub">actual_end 落在本月</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="kpi-label">14 天内到期</div>
          <div class="kpi-value" style="color: #e6a23c">{{ stats?.due_soon_count ?? '—' }}</div>
          <div class="kpi-sub">含已逾期，需重点关注</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="kpi-label">累计已交付</div>
          <div class="kpi-value" style="color: #67c23a">{{ stats?.delivered_total ?? '—' }}</div>
          <div class="kpi-sub">收尾 + 归档</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: 600">在管项目进度</span>
          <el-radio-group v-model="filter" size="small">
            <el-radio-button label="all">全部 ({{ stats?.in_progress_projects.length ?? 0 }})</el-radio-button>
            <el-radio-button label="overdue">已逾期 ({{ overdueCount }})</el-radio-button>
            <el-radio-button label="due_soon">14 天内到期 ({{ dueSoonInListCount }})</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="filteredProjects" stripe>
        <el-table-column prop="name" label="项目名" min-width="240" sortable />
        <el-table-column label="状态" width="100" sortable :sort-method="(a, b) => a.status.localeCompare(b.status)">
          <template #default="{ row }">
            <el-tag :type="STATUS_TYPE[row.status] || 'primary'" size="small">
              {{ STATUS_LABEL[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="planned_start" label="计划起" width="120" sortable />
        <el-table-column prop="planned_end" label="计划止" width="120" sortable />
        <el-table-column label="时间进度" min-width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="progressPct(row)"
              :status="row.overdue ? 'exception' : (progressPct(row) >= 100 ? 'warning' : '')"
              :stroke-width="14"
            />
          </template>
        </el-table-column>
        <el-table-column label="到期" width="130">
          <template #default="{ row }">
            <el-tag :type="dueTagType(row)" size="small" effect="plain">{{ dueLabel(row) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </el-card>
</template>

<style scoped>
.kpi-label { color: #909399; font-size: 13px; }
.kpi-value { font-size: 28px; font-weight: 600; margin-top: 6px; color: #303133; }
.kpi-sub { color: #c0c4cc; font-size: 11px; margin-top: 4px; }
</style>
