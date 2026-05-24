<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { updateProject } from '@/api/projects'
import { listEngineers, type Engineer } from '@/api/engineers'
import ProjectInteractionDrawer from './ProjectInteractionDrawer.vue'

const cockpit = axios.create({ baseURL: '/api/cockpit', timeout: 10000 })

interface InProgressProject {
  project_id: number
  name: string
  status: string
  planned_start: string | null
  planned_end: string | null
  overdue: boolean
  contact_engineer_id: number | null
  contact_engineer_name: string | null
  summary: string | null
  comment_count: number
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
const engineers = ref<Engineer[]>([])

// 内联编辑状态
const editingSummaryId = ref<number | null>(null)
const editingSummaryText = ref('')
const editingEngineerId = ref<number | null>(null)

// 互动 drawer
const drawerOpen = ref(false)
const drawerProjectId = ref<number | null>(null)
const drawerProjectName = ref('')

async function load() {
  loading.value = true
  try {
    const [r, engs] = await Promise.all([
      cockpit.get<EfficiencyStats>('/efficiency-stats'),
      listEngineers({ status_filter: 'active' }),
    ])
    stats.value = r.data
    engineers.value = engs
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

// 摘要内联编辑
function startEditSummary(p: InProgressProject) {
  editingSummaryId.value = p.project_id
  editingSummaryText.value = p.summary || ''
}
async function saveSummary(p: InProgressProject) {
  const text = editingSummaryText.value.trim()
  try {
    await updateProject(p.project_id, { summary: text || null })
    p.summary = text || null
    ElMessage.success('摘要已保存')
  } finally {
    editingSummaryId.value = null
  }
}
function cancelEditSummary() {
  editingSummaryId.value = null
}

// 对接工程师内联编辑
function startEditEngineer(p: InProgressProject) {
  editingEngineerId.value = p.project_id
}
async function saveEngineer(p: InProgressProject, engId: number | null) {
  try {
    await updateProject(p.project_id, { contact_engineer_id: engId })
    p.contact_engineer_id = engId
    p.contact_engineer_name = engId
      ? (engineers.value.find((e) => e.id === engId)?.full_name || null)
      : null
    ElMessage.success('对接工程师已保存')
  } finally {
    editingEngineerId.value = null
  }
}

function openInteraction(p: InProgressProject) {
  drawerProjectId.value = p.project_id
  drawerProjectName.value = p.name
  drawerOpen.value = true
}
async function onDrawerRefreshed() {
  // 刷新表格中的 comment_count
  await load()
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
        <el-table-column prop="name" label="项目名" min-width="200" sortable />
        <el-table-column label="状态" width="90" sortable :sort-method="(a, b) => a.status.localeCompare(b.status)">
          <template #default="{ row }">
            <el-tag :type="STATUS_TYPE[row.status] || 'primary'" size="small">
              {{ STATUS_LABEL[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="对接工程师" width="160">
          <template #default="{ row }">
            <el-select
              v-if="editingEngineerId === row.project_id"
              :model-value="row.contact_engineer_id"
              filterable clearable size="small"
              placeholder="选择工程师"
              style="width: 100%"
              @change="(v: number | null) => saveEngineer(row, v ?? null)"
              @blur="editingEngineerId = null"
            >
              <el-option
                v-for="e in engineers" :key="e.id"
                :label="e.full_name" :value="e.id"
              />
            </el-select>
            <span v-else style="cursor: pointer" @click="startEditEngineer(row)">
              <span v-if="row.contact_engineer_name">{{ row.contact_engineer_name }}</span>
              <span v-else style="color: #c0c4cc">点击指定</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="项目摘要" min-width="240">
          <template #default="{ row }">
            <div v-if="editingSummaryId === row.project_id" style="display: flex; gap: 4px">
              <el-input
                v-model="editingSummaryText" type="textarea" :rows="2" size="small"
                placeholder="一句话描述项目"
                @keydown.enter.prevent.ctrl="saveSummary(row)"
              />
              <div style="display: flex; flex-direction: column; gap: 4px">
                <el-button size="small" type="primary" @click="saveSummary(row)">存</el-button>
                <el-button size="small" @click="cancelEditSummary">×</el-button>
              </div>
            </div>
            <span v-else style="cursor: pointer; white-space: pre-wrap" @click="startEditSummary(row)">
              <span v-if="row.summary">{{ row.summary }}</span>
              <span v-else style="color: #c0c4cc">点击录入摘要…</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_end" label="计划止" width="110" sortable />
        <el-table-column label="到期" width="120">
          <template #default="{ row }">
            <el-tag :type="dueTagType(row)" size="small" effect="plain">{{ dueLabel(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="互动" width="120" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openInteraction(row)">
              留言
              <el-badge
                v-if="row.comment_count > 0"
                :value="row.comment_count" type="warning"
                style="margin-left: 6px"
              />
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <ProjectInteractionDrawer
      v-model="drawerOpen"
      :project-id="drawerProjectId"
      :project-name="drawerProjectName"
      @refreshed="onDrawerRefreshed"
    />
  </el-card>
</template>

<style scoped>
.kpi-label { color: #909399; font-size: 13px; }
.kpi-value { font-size: 28px; font-weight: 600; margin-top: 6px; color: #303133; }
.kpi-sub { color: #c0c4cc; font-size: 11px; margin-top: 4px; }
</style>
