<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAttempt, deleteAttempt, listAttempts, updateAttempt,
  LOST_REASON_LABELS,
  type LostReason, type RenewalAttempt, type RenewalAttemptPayload, type RenewalOutcome,
} from '@/api/renewalAttempts'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<RenewalAttempt[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ outcome?: RenewalOutcome }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<RenewalAttemptPayload>({
  previous_project_id: 0, attempt_date: new Date().toISOString().slice(0, 10),
  outcome: 'pending', won_project_id: null,
  lost_reason: null, lost_reason_note: '', notes: '',
})

const OUTCOME_LABEL: Record<RenewalOutcome, string> = {
  pending: '商务洽谈中', won: '已赢单', lost: '已输单',
}
const OUTCOME_TYPE: Record<RenewalOutcome, string> = {
  pending: 'warning', won: 'success', lost: 'danger',
}

async function load() {
  loading.value = true
  try {
    rows.value = await listAttempts(filter.outcome)
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    previous_project_id: projects.value[0]?.id || 0,
    attempt_date: new Date().toISOString().slice(0, 10),
    outcome: 'pending', won_project_id: null,
    lost_reason: null, lost_reason_note: '', notes: '',
  })
  dialog.value = true
}

function openEdit(a: RenewalAttempt) {
  editingId.value = a.id
  Object.assign(form, {
    previous_project_id: a.previous_project_id,
    attempt_date: a.attempt_date,
    outcome: a.outcome,
    won_project_id: a.won_project_id || null,
    lost_reason: a.lost_reason || null,
    lost_reason_note: a.lost_reason_note || '',
    notes: a.notes || '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.previous_project_id) { ElMessage.warning('请选择源项目'); return }
  if (form.outcome === 'won' && !form.won_project_id) {
    ElMessage.warning('outcome=won 必须指定新项目'); return
  }
  if (form.outcome === 'lost' && !form.lost_reason) {
    ElMessage.warning('outcome=lost 必须填原因'); return
  }
  if (editingId.value === null) await createAttempt(form)
  else {
    const { previous_project_id, ...rest } = form
    void previous_project_id
    await updateAttempt(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(a: RenewalAttempt) {
  await ElMessageBox.confirm(`删除续单记录 #${a.id}？`, '提示', { type: 'warning' })
  await deleteAttempt(a.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px">
      <el-select v-model="filter.outcome" placeholder="按结果筛选" clearable style="width: 140px" @change="load">
        <el-option v-for="(v, k) in OUTCOME_LABEL" :key="k" :label="v" :value="k" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增续单跟踪</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="attempt_date" label="尝试日期" width="120" />
      <el-table-column prop="previous_project_name" label="源项目" min-width="180" />
      <el-table-column label="结果" width="120">
        <template #default="{ row }">
          <el-tag :type="OUTCOME_TYPE[row.outcome as RenewalOutcome] as any">
            {{ OUTCOME_LABEL[row.outcome as RenewalOutcome] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="续单项目 / 原因" min-width="200">
        <template #default="{ row }">
          <span v-if="row.outcome === 'won'">✓ {{ row.won_project_name || '—' }}</span>
          <span v-else-if="row.outcome === 'lost'" style="color: #f56c6c">
            ✗ {{ LOST_REASON_LABELS[row.lost_reason as LostReason] || row.lost_reason }}
          </span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="lost_reason_note" label="备注" min-width="160" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增续单跟踪' : '编辑续单跟踪'" width="640px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="源项目" required>
          <el-select v-model="form.previous_project_id" :disabled="editingId !== null"
                     filterable placeholder="选择被续的历史项目" style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="`${p.code || ''} ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="尝试日期">
          <el-date-picker v-model="form.attempt_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结果">
          <el-radio-group v-model="form.outcome">
            <el-radio-button label="pending">商务洽谈中</el-radio-button>
            <el-radio-button label="won">已赢单</el-radio-button>
            <el-radio-button label="lost">已输单</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.outcome === 'won'" label="新项目 ID *">
          <el-select v-model="form.won_project_id" filterable placeholder="赢的项目（新立项）" style="width: 100%">
            <el-option v-for="p in projects" :key="p.id"
                       :label="`${p.code || ''} ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <template v-if="form.outcome === 'lost'">
          <el-form-item label="输的原因 *">
            <el-select v-model="form.lost_reason" style="width: 100%">
              <el-option v-for="(label, code) in LOST_REASON_LABELS" :key="code" :label="label" :value="code" />
            </el-select>
          </el-form-item>
          <el-form-item label="原因说明">
            <el-input v-model="form.lost_reason_note" type="textarea" :rows="2"
                      placeholder="例如：竞品报价低 15%" />
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
