<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRetro, deleteRetro, listRetros, updateRetro,
  type Retrospective, type RetrospectivePayload,
} from '@/api/retrospectives'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<Retrospective[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ project_id?: number; is_closed?: boolean }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<RetrospectivePayload>({
  project_id: 0, satisfaction_score: 5,
  what_went_well: '', what_to_improve: '', action_items: '',
  next_review_date: undefined, is_closed: false,
})

async function load() {
  loading.value = true
  try {
    rows.value = await listRetros(filter)
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    project_id: projects.value[0]?.id || 0, satisfaction_score: 5,
    what_went_well: '', what_to_improve: '', action_items: '',
    next_review_date: undefined, is_closed: false,
  })
  dialog.value = true
}

function openEdit(r: Retrospective) {
  editingId.value = r.id
  Object.assign(form, {
    project_id: r.project_id,
    satisfaction_score: r.satisfaction_score,
    what_went_well: r.what_went_well || '',
    what_to_improve: r.what_to_improve || '',
    action_items: r.action_items || '',
    next_review_date: r.next_review_date || undefined,
    is_closed: r.is_closed,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.project_id) { ElMessage.warning('请选择项目'); return }
  if (editingId.value === null) await createRetro(form)
  else {
    const { project_id, ...rest } = form
    void project_id
    await updateRetro(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onToggleClosed(r: Retrospective) {
  await updateRetro(r.id, { is_closed: !r.is_closed })
  await load()
}

async function onDelete(r: Retrospective) {
  await ElMessageBox.confirm(`删除复盘记录 #${r.id}？`, '提示', { type: 'warning' })
  await deleteRetro(r.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>

    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <el-select v-model="filter.project_id" placeholder="按项目筛选" clearable filterable style="width: 220px" @change="load">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filter.is_closed" placeholder="按闭环状态" clearable style="width: 140px" @change="load">
        <el-option label="已闭环" :value="true" />
        <el-option label="进行中" :value="false" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增复盘</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="project_name" label="项目" min-width="180" />
      <el-table-column label="满意度" width="160">
        <template #default="{ row }">
          <el-rate :model-value="row.satisfaction_score" disabled show-score />
        </template>
      </el-table-column>
      <el-table-column prop="what_went_well" label="做对了" min-width="160" />
      <el-table-column prop="what_to_improve" label="要改进" min-width="160" />
      <el-table-column prop="next_review_date" label="下次复盘" width="120" />
      <el-table-column label="闭环" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.is_closed" @change="onToggleClosed(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增复盘' : '编辑复盘'" width="640px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" :disabled="editingId !== null" filterable style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="满意度">
          <el-rate v-model="form.satisfaction_score" :max="5" show-score />
        </el-form-item>
        <el-form-item label="做对了">
          <el-input v-model="form.what_went_well" type="textarea" :rows="2" placeholder="项目里做对的事..." />
        </el-form-item>
        <el-form-item label="要改进">
          <el-input v-model="form.what_to_improve" type="textarea" :rows="2" placeholder="下次要避免的问题..." />
        </el-form-item>
        <el-form-item label="行动项">
          <el-input v-model="form.action_items" type="textarea" :rows="3" placeholder="一行一条行动项..." />
        </el-form-item>
        <el-form-item label="下次复盘">
          <el-date-picker v-model="form.next_review_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="已闭环">
          <el-switch v-model="form.is_closed" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
