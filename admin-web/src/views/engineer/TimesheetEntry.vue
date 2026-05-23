<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  APPROVAL_LABEL, APPROVAL_TAG_TYPE,
  approveTimesheet, computePreview,
  createTimesheetRange, deleteTimesheet, downloadTemplate, importExcel, listTimesheets,
  rejectTimesheet,
  type ApprovalStatus, type ImportResult, type SlotCode, type Timesheet, type TimesheetRangePayload,
} from '@/api/timesheets'
import { listEngineers, type Engineer } from '@/api/engineers'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<Timesheet[]>([])
const engineers = ref<Engineer[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{
  engineer_id?: number; project_id?: number
  date_from?: string; date_to?: string
  approval_filter?: ApprovalStatus
}>({})

const dialog = ref(false)
const today = () => new Date().toISOString().slice(0, 10)
const form = reactive<TimesheetRangePayload>({
  engineer_id: 0, project_id: 0,
  start_date: today(), end_date: today(),
  slots: ['morning', 'afternoon'],
  description: '',
})

const importDialog = ref(false)
const importing = ref(false)
const importResult = ref<ImportResult | null>(null)
const fileRef = ref<HTMLInputElement | null>(null)

async function load() {
  loading.value = true
  try {
    rows.value = await listTimesheets(filter)
    if (engineers.value.length === 0) engineers.value = await listEngineers()
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    engineer_id: engineers.value[0]?.id || 0,
    project_id: projects.value[0]?.id || 0,
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
  if (!form.engineer_id || !form.project_id) {
    ElMessage.warning('工程师 / 项目必填')
    return
  }
  if (!form.start_date || !form.end_date) {
    ElMessage.warning('请选择起止日期')
    return
  }
  if (form.slots.length === 0) {
    ElMessage.warning('请至少选择一个时段')
    return
  }
  const result = await createTimesheetRange(form)
  if (result.skipped.length > 0) {
    ElMessage.warning(`成功 ${result.created.length} 天，跳过 ${result.skipped.length} 天（多为重复日）`)
  } else {
    ElMessage.success(`成功录入 ${result.created.length} 天，共加权 ${result.total_weighted_days} 人天`)
  }
  dialog.value = false
  await load()
}

async function onDelete(t: Timesheet) {
  await ElMessageBox.confirm(
    `删除 ${t.work_date} ${t.engineer_name} 的 ${t.weighted_days} 加权人天记录？`,
    '提示', { type: 'warning' },
  )
  await deleteTimesheet(t.id)
  ElMessage.success('已删除')
  await load()
}

async function onApprove(t: Timesheet) {
  await approveTimesheet(t.id)
  ElMessage.success(`已批准 #${t.id}`)
  await load()
}

// 拒绝弹框
const rejectVisible = ref(false)
const rejectTarget = ref<Timesheet | null>(null)
const rejectReason = ref('')

function openReject(t: Timesheet) {
  rejectTarget.value = t
  rejectReason.value = ''
  rejectVisible.value = true
}

async function onSubmitReject() {
  if (!rejectTarget.value || !rejectReason.value.trim()) {
    ElMessage.warning('拒绝理由必填')
    return
  }
  await rejectTimesheet(rejectTarget.value.id, rejectReason.value.trim())
  ElMessage.success('已拒绝，工程师将看到理由')
  rejectVisible.value = false
  await load()
}

async function onDownloadTemplate() {
  await downloadTemplate()
  ElMessage.success('模板已下载（新版含上午/下午/晚上 3 列）')
}

function openImport() {
  importResult.value = null
  importDialog.value = true
}

async function onPickFile(ev: Event) {
  const target = ev.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  importing.value = true
  try {
    importResult.value = await importExcel(file)
    if (importResult.value.created > 0) ElMessage.success(`成功导入 ${importResult.value.created} 条`)
    if (importResult.value.skipped > 0) ElMessage.warning(`跳过 ${importResult.value.skipped} 条（详情见下方）`)
    await load()
  } finally {
    importing.value = false
    target.value = ''
  }
}

function slotBadges(t: Timesheet): { label: string; type: 'primary' | 'warning' | 'danger' }[] {
  const out: { label: string; type: 'primary' | 'warning' | 'danger' }[] = []
  if (t.has_morning) out.push({ label: '上午', type: 'primary' })
  if (t.has_afternoon) out.push({ label: '下午', type: 'primary' })
  if (t.has_evening) out.push({ label: '晚上', type: 'danger' })
  return out
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <el-select v-model="filter.engineer_id" placeholder="按工程师" clearable filterable style="width: 180px" @change="load">
        <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
      </el-select>
      <el-select v-model="filter.project_id" placeholder="按项目" clearable filterable style="width: 220px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-date-picker
        v-model="filter.date_from" type="date" placeholder="起始日" value-format="YYYY-MM-DD"
        style="width: 140px" @change="load"
      />
      <el-date-picker
        v-model="filter.date_to" type="date" placeholder="截止日" value-format="YYYY-MM-DD"
        style="width: 140px" @change="load"
      />
      <el-select v-model="filter.approval_filter" placeholder="审批状态" clearable style="width: 130px" @change="load">
        <el-option label="待审" value="pending" />
        <el-option label="已审" value="approved" />
        <el-option label="已拒" value="rejected" />
      </el-select>
      <div style="flex: 1" />
      <el-button @click="onDownloadTemplate">下载 Excel 模板</el-button>
      <el-button type="warning" @click="openImport">Excel 批量导入</el-button>
      <el-button type="primary" @click="openCreate">录入工时</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="work_date" label="日期" width="110" sortable />
      <el-table-column label="工作日" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_workday ? 'info' : 'warning'" size="small" effect="plain">
            {{ row.is_workday ? '工作日' : '非工作日' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="engineer_name" label="工程师" width="100" />
      <el-table-column prop="project_name" label="项目" min-width="180" />
      <el-table-column label="时段" width="160">
        <template #default="{ row }">
          <el-tag v-for="b in slotBadges(row)" :key="b.label"
                  :type="b.type" size="small" style="margin-right: 4px">
            {{ b.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="自然人天" width="90">
        <template #default="{ row }">{{ row.natural_days }}</template>
      </el-table-column>
      <el-table-column label="加权人天" width="100">
        <template #default="{ row }">
          <span :style="{ color: Number(row.weighted_days) > Number(row.natural_days) ? '#e6a23c' : '#303133', fontWeight: 600 }">
            {{ row.weighted_days }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="160" />
      <el-table-column label="状态" width="170">
        <template #default="{ row }">
          <el-tag :type="APPROVAL_TAG_TYPE[row.approval_status as ApprovalStatus]" size="small">
            {{ APPROVAL_LABEL[row.approval_status as ApprovalStatus] }}
          </el-tag>
          <el-tooltip v-if="row.approval_status === 'rejected' && row.reject_reason"
                      :content="row.reject_reason" placement="top">
            <span style="margin-left: 4px; color: #f56c6c; cursor: help; font-size: 12px">⚠</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.approval_status === 'pending'"
                     link type="success" size="small" @click="onApprove(row)">批准</el-button>
          <el-button v-if="row.approval_status === 'pending'"
                     link type="warning" size="small" @click="openReject(row)">拒绝</el-button>
          <el-button v-if="row.approval_status === 'rejected'"
                     link type="success" size="small" @click="onApprove(row)">改批准</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 录入工时（按起止日期 + 时段） -->
    <el-dialog v-model="dialog" title="录入工时" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="工程师" required>
          <el-select v-model="form.engineer_id" filterable style="width: 100%">
            <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
          </el-select>
        </el-form-item>
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

        <!-- 实时预览：覆盖天数 / 自然人天 / 加权人天 -->
        <el-alert
          v-if="preview.days > 0"
          :type="preview.weighted > preview.natural ? 'warning' : 'info'"
          :closable="false" show-icon
          style="margin: 0 0 12px"
        >
          <template #title>
            将创建 <strong>{{ preview.days }}</strong> 天工时记录 ·
            自然人天 <strong>{{ preview.natural }}</strong> ·
            <span style="color: #e6a23c">加权人天 <strong>{{ preview.weighted }}</strong></span>
          </template>
          <div style="font-size: 12px; color: #909399">
            规则：上下午（工作日 1.0× / 非工作日 1.5×）· 晚上始终 1.5×
          </div>
        </el-alert>
        <el-alert v-else type="error" :closable="false" show-icon style="margin: 0 0 12px"
                  title="请检查日期范围 + 时段选择" />

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2"
                    placeholder="例如：中环现场调试 / 周末加班补救故障" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :disabled="preview.days === 0" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Excel 导入 -->
    <el-dialog v-model="importDialog" title="Excel 批量导入工时" width="600px">
      <div style="margin-bottom: 16px; color: #606266; font-size: 13px">
        <p>步骤：</p>
        <ol style="margin: 4px 0 8px 20px; padding: 0">
          <li>点击下方"选择 Excel 文件"，上传 .xlsx</li>
          <li>表头列顺序：<code>工程师姓名 | 项目编号或名称 | 工作日期 | 上午(0/1) | 下午(0/1) | 晚上(0/1) | 描述</code></li>
          <li>工程师按姓名精确匹配；项目优先按编号匹配，否则按名称</li>
          <li>上午/下午/晚上 至少有一列填 1（或 true/yes/是）</li>
          <li>失败行不影响成功行；末尾显示错误清单</li>
        </ol>
      </div>

      <input ref="fileRef" type="file" accept=".xlsx,.xls" style="display: none" @change="onPickFile" />
      <el-button :loading="importing" type="primary" @click="fileRef?.click()">选择 Excel 文件</el-button>

      <div v-if="importResult" style="margin-top: 16px">
        <el-alert
          :title="`成功 ${importResult.created} 条；跳过 ${importResult.skipped} 条`"
          :type="importResult.errors.length === 0 ? 'success' : 'warning'"
          :closable="false"
        />
        <el-table v-if="importResult.errors.length > 0" :data="importResult.errors" size="small" style="margin-top: 12px">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="message" label="错误" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="importDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝工时弹框 -->
    <el-dialog v-model="rejectVisible" title="拒绝工时" width="460px">
      <div v-if="rejectTarget" style="margin-bottom: 12px; color: #606266; font-size: 13px">
        <strong>{{ rejectTarget.engineer_name }}</strong>
        {{ rejectTarget.work_date }} · {{ rejectTarget.project_name }}
      </div>
      <el-input
        v-model="rejectReason" type="textarea" :rows="3"
        placeholder="拒绝理由（工程师将看到此内容）— 例如：项目不在该时段排期 / 描述过简 / 已超出本月预算 …"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :disabled="!rejectReason.trim()" @click="onSubmitReject">
          确认拒绝
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
