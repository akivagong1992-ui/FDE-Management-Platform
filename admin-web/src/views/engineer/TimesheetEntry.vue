<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createTimesheet, deleteTimesheet, downloadTemplate, importExcel, listTimesheets,
  type ImportResult, type Timesheet, type TimesheetPayload,
} from '@/api/timesheets'
import { listEngineers, type Engineer } from '@/api/engineers'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<Timesheet[]>([])
const engineers = ref<Engineer[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ engineer_id?: number; project_id?: number; date_from?: string; date_to?: string }>({})

const dialog = ref(false)
const form = reactive<TimesheetPayload>({
  engineer_id: 0, project_id: 0, work_date: new Date().toISOString().slice(0, 10),
  hours: 8, description: '',
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
    work_date: new Date().toISOString().slice(0, 10),
    hours: 8, description: '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.engineer_id || !form.project_id || !form.work_date || !form.hours) {
    ElMessage.warning('工程师/项目/日期/工时 必填')
    return
  }
  await createTimesheet(form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(t: Timesheet) {
  await ElMessageBox.confirm(`删除 ${t.work_date} ${t.engineer_name} 的 ${t.hours}h 工时？`, '提示', { type: 'warning' })
  await deleteTimesheet(t.id)
  ElMessage.success('已删除')
  await load()
}

async function onDownloadTemplate() {
  await downloadTemplate()
  ElMessage.success('模板已下载，按表头填写后上传导入')
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
      <div style="flex: 1" />
      <el-button @click="onDownloadTemplate">下载 Excel 模板</el-button>
      <el-button type="warning" @click="openImport">Excel 批量导入</el-button>
      <el-button type="primary" @click="openCreate">单条录入</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="work_date" label="日期" width="110" sortable />
      <el-table-column prop="engineer_name" label="工程师" width="100" />
      <el-table-column prop="project_name" label="项目" min-width="200" />
      <el-table-column label="工时" width="80">
        <template #default="{ row }">{{ row.hours }}h</template>
      </el-table-column>
      <el-table-column prop="description" label="描述" />
      <el-table-column label="审核" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_approved ? 'success' : 'info'">
            {{ row.is_approved ? '已审' : '未审' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 单条录入 -->
    <el-dialog v-model="dialog" title="单条录入工时" width="520px">
      <el-form :model="form" label-width="80px">
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
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.work_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="工时" required>
          <el-input-number v-model="form.hours" :min="0.25" :max="24" :step="0.25" :precision="2" controls-position="right" />
          <span style="margin-left: 8px; color: #909399">小时</span>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Excel 导入 -->
    <el-dialog v-model="importDialog" title="Excel 批量导入工时" width="560px">
      <div style="margin-bottom: 16px; color: #606266; font-size: 13px">
        <p>步骤：</p>
        <ol style="margin: 4px 0 8px 20px; padding: 0">
          <li>点击下方"选择文件"按钮，上传一份 .xlsx 文件</li>
          <li>表头列顺序：<code>工程师姓名 | 项目编号或名称 | 工作日期(YYYY-MM-DD) | 工时 | 描述</code></li>
          <li>工程师按姓名精确匹配；项目优先按编号匹配，否则按名称</li>
          <li>导入逐行进行，失败行不影响成功行；末尾显示错误清单</li>
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
  </div>
</template>
