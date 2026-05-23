<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createIDP, deleteIDP, listIDPs, updateIDP,
  type IDP, type IDPPayload, type IDPStatus,
} from '@/api/idps'
import { listEngineers, type Engineer } from '@/api/engineers'

const rows = ref<IDP[]>([])
const engineers = ref<Engineer[]>([])
const loading = ref(false)
const filter = reactive<{ engineer_id?: number; status_filter?: IDPStatus }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<IDPPayload>({
  engineer_id: 0, title: '', target_skills: '', target_certs: '',
  plan_actions: '', due_date: undefined, status: 'draft',
})

const STATUS_LABEL: Record<IDPStatus, string> = {
  draft: '草稿', in_progress: '进行中', completed: '已完成', cancelled: '已取消',
}
const STATUS_TYPE: Record<IDPStatus, string> = {
  draft: 'info', in_progress: 'warning', completed: 'success', cancelled: '',
}

async function load() {
  loading.value = true
  try {
    rows.value = await listIDPs(filter)
    if (engineers.value.length === 0) engineers.value = await listEngineers()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    engineer_id: engineers.value[0]?.id || 0, title: '',
    target_skills: '', target_certs: '', plan_actions: '',
    due_date: undefined, status: 'draft',
  })
  dialog.value = true
}

function openEdit(i: IDP) {
  editingId.value = i.id
  Object.assign(form, {
    engineer_id: i.engineer_id, title: i.title,
    target_skills: i.target_skills || '', target_certs: i.target_certs || '',
    plan_actions: i.plan_actions || '',
    due_date: i.due_date || undefined, status: i.status,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.engineer_id || !form.title) { ElMessage.warning('工程师 + 标题必填'); return }
  if (editingId.value === null) await createIDP(form)
  else {
    const { engineer_id, ...rest } = form
    void engineer_id
    await updateIDP(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(i: IDP) {
  await ElMessageBox.confirm(`删除 IDP "${i.title}"？`, '提示', { type: 'warning' })
  await deleteIDP(i.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px">
      <el-select v-model="filter.engineer_id" placeholder="按工程师" clearable filterable style="width: 200px" @change="load">
        <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
      </el-select>
      <el-select v-model="filter.status_filter" placeholder="按状态" clearable style="width: 140px" @change="load">
        <el-option v-for="(v, k) in STATUS_LABEL" :key="k" :label="v" :value="k" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增 IDP</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="engineer_name" label="工程师" width="100" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="target_skills" label="目标技能" min-width="160" />
      <el-table-column prop="target_certs" label="目标证书" width="160" />
      <el-table-column prop="due_date" label="到期" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status as IDPStatus] as any">{{ STATUS_LABEL[row.status as IDPStatus] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增 IDP' : '编辑 IDP'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="工程师" required>
          <el-select v-model="form.engineer_id" :disabled="editingId !== null" filterable style="width: 100%">
            <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="例如：L4 → L5 成长路径" />
        </el-form-item>
        <el-form-item label="目标技能"><el-input v-model="form.target_skills" placeholder="逗号分隔" /></el-form-item>
        <el-form-item label="目标证书"><el-input v-model="form.target_certs" placeholder="如 CCIE / CISSP" /></el-form-item>
        <el-form-item label="行动项"><el-input v-model="form.plan_actions" type="textarea" :rows="3" placeholder="一行一条" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="到期"><el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="(v, k) in STATUS_LABEL" :key="k" :label="v" :value="k" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
