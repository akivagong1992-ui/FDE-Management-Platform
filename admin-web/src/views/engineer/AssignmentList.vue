<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  APPROVAL_LABEL, APPROVAL_TAG_TYPE,
  createAssignment, deleteAssignment, endAssignment, listAssignments, updateAssignment,
  type ApprovalStatus, type Assignment, type AssignmentPayload, type AssignmentStatus,
} from '@/api/assignments'
import { listEngineers, type Engineer } from '@/api/engineers'
import { listProjects, type Project } from '@/api/projects'
import AssignmentDrawer from './AssignmentDrawer.vue'

const rows = ref<Assignment[]>([])
const engineers = ref<Engineer[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{
  engineer_id?: number; project_id?: number
  status_filter?: AssignmentStatus; approval_filter?: ApprovalStatus
}>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<AssignmentPayload>({
  engineer_id: 0, project_id: 0, role: '',
  planned_start_date: undefined, planned_end_date: undefined,
  actual_start_date: undefined, actual_end_date: undefined,
  status: 'planned', notes: '', initial_message: '',
})

const drawerOpen = ref(false)
const drawerAssignmentId = ref<number | null>(null)

const STATUS_OPTS: { label: string; value: AssignmentStatus; type: 'info' | 'success' | 'warning' | 'danger' | 'primary' }[] = [
  { label: '计划中', value: 'planned', type: 'info' },
  { label: '进行中', value: 'in_progress', type: 'success' },
  { label: '已结束', value: 'ended', type: 'primary' },
  { label: '已取消', value: 'cancelled', type: 'danger' },
]
const STATUS_LABEL: Record<string, string> = Object.fromEntries(STATUS_OPTS.map((o) => [o.value, o.label]))
const STATUS_TYPE: Record<string, 'info' | 'success' | 'warning' | 'danger' | 'primary'> = Object.fromEntries(STATUS_OPTS.map((o) => [o.value, o.type])) as never

async function load() {
  loading.value = true
  try {
    rows.value = await listAssignments(filter)
    if (engineers.value.length === 0) engineers.value = await listEngineers()
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    engineer_id: engineers.value[0]?.id || 0,
    project_id: projects.value[0]?.id || 0,
    role: '',
    planned_start_date: undefined, planned_end_date: undefined,
    actual_start_date: undefined, actual_end_date: undefined,
    status: 'planned', notes: '', initial_message: '',
  })
  dialog.value = true
}

function openEdit(a: Assignment) {
  editingId.value = a.id
  Object.assign(form, {
    engineer_id: a.engineer_id,
    project_id: a.project_id,
    role: a.role || '',
    planned_start_date: a.planned_start_date || undefined,
    planned_end_date: a.planned_end_date || undefined,
    actual_start_date: a.actual_start_date || undefined,
    actual_end_date: a.actual_end_date || undefined,
    status: a.status,
    notes: a.notes || '',
    initial_message: '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.engineer_id || !form.project_id) {
    ElMessage.warning('工程师 + 项目 必填')
    return
  }
  if (editingId.value === null) {
    await createAssignment(form)
  } else {
    const { engineer_id, project_id, initial_message, ...rest } = form
    void engineer_id; void project_id; void initial_message
    await updateAssignment(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onEnd(a: Assignment) {
  await ElMessageBox.confirm(`将派单 #${a.id} 标记为已结束？`, '提示', { type: 'warning' })
  await endAssignment(a.id)
  ElMessage.success('已结束')
  await load()
}

async function onDelete(a: Assignment) {
  await ElMessageBox.confirm(`删除派单 #${a.id}？此操作连同对话留痕一并清除。`, '提示', { type: 'warning' })
  await deleteAssignment(a.id)
  ElMessage.success('已删除')
  await load()
}

function openDrawer(a: Assignment) {
  drawerAssignmentId.value = a.id
  drawerOpen.value = true
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <el-select v-model="filter.engineer_id" placeholder="按工程师筛选" clearable filterable style="width: 200px" @change="load">
        <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
      </el-select>
      <el-select v-model="filter.project_id" placeholder="按项目筛选" clearable filterable style="width: 220px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filter.status_filter" placeholder="阶段" clearable style="width: 120px" @change="load">
        <el-option v-for="o in STATUS_OPTS" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="filter.approval_filter" placeholder="工程师确认" clearable style="width: 140px" @change="load">
        <el-option label="待确认" value="pending" />
        <el-option label="已接单" value="accepted" />
        <el-option label="已拒单" value="rejected" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增派单</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="engineer_name" label="工程师" width="100" />
      <el-table-column label="项目" min-width="200">
        <template #default="{ row }">
          <span v-if="row.project_code" style="color: #909399">[{{ row.project_code }}]</span>
          {{ row.project_name }}
        </template>
      </el-table-column>
      <el-table-column prop="role" label="角色" width="110" />
      <el-table-column label="阶段" width="90">
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status]" size="small">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="工程师确认" width="130">
        <template #default="{ row }">
          <el-tag :type="APPROVAL_TAG_TYPE[row.approval_status as ApprovalStatus]" size="small">
            {{ APPROVAL_LABEL[row.approval_status as ApprovalStatus] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="planned_start_date" label="计划起" width="115" />
      <el-table-column prop="planned_end_date" label="计划止" width="115" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDrawer(row)">
            对话 ({{ row.message_count }})
          </el-button>
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status !== 'ended' && row.status !== 'cancelled'"
                     link type="warning" size="small" @click="onEnd(row)">结束</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增派单' : '编辑派单'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="工程师" required>
              <el-select v-model="form.engineer_id" filterable :disabled="editingId !== null" style="width: 100%">
                <el-option v-for="e in engineers" :key="e.id"
                  :label="`${e.full_name} (${e.vendor_name})`" :value="e.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目" required>
              <el-select v-model="form.project_id" filterable :disabled="editingId !== null" style="width: 100%">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="角色">
              <el-input v-model="form.role" placeholder="如 开发/测试/PM/架构师" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阶段">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="o in STATUS_OPTS" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="计划开始">
              <el-date-picker v-model="form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划结束">
              <el-date-picker v-model="form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
        <el-form-item v-if="editingId === null" label="首条说明">
          <el-input v-model="form.initial_message" type="textarea" :rows="2"
                    placeholder="可选：派单时直接附一条说明给工程师（如「现场在中环，请带工具」）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <AssignmentDrawer
      v-model="drawerOpen"
      :assignment-id="drawerAssignmentId"
      @changed="load"
    />
  </div>
</template>
