<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  APPROVAL_LABEL, APPROVAL_TAG_TYPE,
  computePreview,
  createTimesheetRange, deleteTimesheet, listTimesheets,
  type ApprovalStatus, type SlotCode, type Timesheet, type TimesheetRangePayload,
} from '@/api/timesheets'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<Timesheet[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const tab = ref<'pending' | 'approved' | 'rejected' | 'all'>('all')

const dialog = ref(false)
const today = () => new Date().toISOString().slice(0, 10)
const form = reactive<TimesheetRangePayload>({
  engineer_id: 0,  // 服务端会强制改为当前 engineer_id，传 0 即可
  project_id: 0,
  start_date: today(), end_date: today(),
  slots: ['morning', 'afternoon'],
  description: '',
})

async function load() {
  loading.value = true
  try {
    rows.value = await listTimesheets()
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  if (tab.value === 'all') return rows.value
  return rows.value.filter((t) => t.approval_status === tab.value)
})

const pendingCount = computed(() => rows.value.filter((t) => t.approval_status === 'pending').length)
const approvedCount = computed(() => rows.value.filter((t) => t.approval_status === 'approved').length)
const rejectedCount = computed(() => rows.value.filter((t) => t.approval_status === 'rejected').length)

const totalApprovedWeighted = computed(() =>
  rows.value
    .filter((t) => t.approval_status === 'approved')
    .reduce((acc, t) => acc + Number(t.weighted_days), 0)
    .toFixed(2),
)

function openCreate() {
  Object.assign(form, {
    engineer_id: 0, project_id: projects.value[0]?.id || 0,
    start_date: today(), end_date: today(),
    slots: ['morning', 'afternoon'] as SlotCode[],
    description: '',
  })
  dialog.value = true
}

const preview = computed(() =>
  computePreview(form.start_date, form.end_date, form.slots as SlotCode[]),
)

async function onSubmit() {
  if (!form.project_id) { ElMessage.warning('请选择项目'); return }
  if (form.slots.length === 0) { ElMessage.warning('请至少选择一个时段'); return }
  const result = await createTimesheetRange(form)
  if (result.skipped.length > 0) {
    ElMessage.warning(`提交 ${result.created.length} 天，跳过 ${result.skipped.length} 天（重复日）`)
  } else {
    ElMessage.success(`已提交 ${result.created.length} 天工时（${result.total_weighted_days} 加权人天），等管理者审批`)
  }
  dialog.value = false
  await load()
}

async function onDelete(t: Timesheet) {
  if (t.approval_status === 'approved') {
    ElMessage.warning('已审通过的工时不能删，请联系管理者撤回')
    return
  }
  await ElMessageBox.confirm(`删除 ${t.work_date} 的工时记录？`, '提示', { type: 'warning' })
  await deleteTimesheet(t.id)
  ElMessage.success('已删除')
  await load()
}

function slotBadges(t: Timesheet): { label: string; type: 'primary' | 'danger' }[] {
  const out: { label: string; type: 'primary' | 'danger' }[] = []
  if (t.has_morning) out.push({ label: '上午', type: 'primary' })
  if (t.has_afternoon) out.push({ label: '下午', type: 'primary' })
  if (t.has_evening) out.push({ label: '晚上', type: 'danger' })
  return out
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">我的工时</span>
        <span style="color: #909399; font-size: 12px">
          待审 <strong style="color: #e6a23c">{{ pendingCount }}</strong> ·
          已审 <strong style="color: #67c23a">{{ approvedCount }}</strong> ·
          已拒 <strong style="color: #f56c6c">{{ rejectedCount }}</strong> ·
          已审累计加权 <strong style="color: #67c23a">{{ totalApprovedWeighted }}</strong> 人天
        </span>
      </div>
    </template>

    <div style="display: flex; gap: 12px; margin-bottom: 16px; align-items: center">
      <el-radio-group v-model="tab">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="pending">
          待审
          <el-badge v-if="pendingCount > 0" :value="pendingCount" type="warning" />
        </el-radio-button>
        <el-radio-button label="rejected">
          已拒
          <el-badge v-if="rejectedCount > 0" :value="rejectedCount" type="danger" />
        </el-radio-button>
        <el-radio-button label="approved">已审</el-radio-button>
      </el-radio-group>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">📝 录入工时</el-button>
    </div>

    <el-table :data="filtered" v-loading="loading" stripe>
      <el-table-column prop="work_date" label="日期" width="110" sortable />
      <el-table-column label="工作日" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_workday ? 'info' : 'warning'" size="small" effect="plain">
            {{ row.is_workday ? '工作日' : '非工作日' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="project_name" label="项目" min-width="180" />
      <el-table-column label="时段" width="160">
        <template #default="{ row }">
          <el-tag v-for="b in slotBadges(row)" :key="b.label"
                  :type="b.type" size="small" style="margin-right: 4px">
            {{ b.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="加权人天" width="100">
        <template #default="{ row }">
          <strong :style="{ color: Number(row.weighted_days) > Number(row.natural_days) ? '#e6a23c' : '#303133' }">
            {{ row.weighted_days }}
          </strong>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="APPROVAL_TAG_TYPE[row.approval_status as ApprovalStatus]" size="small">
            {{ APPROVAL_LABEL[row.approval_status as ApprovalStatus] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="拒绝理由" min-width="220">
        <template #default="{ row }">
          <span v-if="row.approval_status === 'rejected' && row.reject_reason"
                style="color: #f56c6c; font-size: 13px">
            {{ row.reject_reason }}
          </span>
          <span v-else-if="row.description" style="color: #909399; font-size: 12px">
            {{ row.description }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.approval_status !== 'approved'"
                     link type="danger" size="small" @click="onDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 录入对话框（与 admin 同结构，但无工程师选择） -->
    <el-dialog v-model="dialog" title="录入我的工时" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" filterable style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="起始日期" required>
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止日期" required>
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="时段" required>
          <el-checkbox-group v-model="form.slots">
            <el-checkbox label="morning">上午</el-checkbox>
            <el-checkbox label="afternoon">下午</el-checkbox>
            <el-checkbox label="evening">晚上</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-alert
          v-if="preview.days > 0"
          :type="preview.weighted > preview.natural ? 'warning' : 'info'"
          :closable="false" show-icon
          style="margin: 0 0 12px"
        >
          <template #title>
            将提交 <strong>{{ preview.days }}</strong> 天 ·
            自然 <strong>{{ preview.natural }}</strong> ·
            <span style="color: #e6a23c">加权 <strong>{{ preview.weighted }}</strong></span>
          </template>
          <div style="font-size: 12px; color: #909399">
            提交后状态为「待审」，管理者批准后即生效。如被拒，理由会显示在列表
          </div>
        </el-alert>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2"
                    placeholder="说明做了什么 — 例如：中环现场调试 BSS 升级 / 周末加班修复故障" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :disabled="preview.days === 0" @click="onSubmit">提交审批</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>
