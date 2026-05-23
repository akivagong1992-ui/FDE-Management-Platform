<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRevenue, deleteRevenue, listRevenues, updateRevenue,
  type ProjectRevenue, type RevenuePayload, type RevenueStatus,
} from '@/api/projectRevenues'
import { listProjects, type Project } from '@/api/projects'

const rows = ref<ProjectRevenue[]>([])
const projects = ref<Project[]>([])
const revenueProjects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ project_id?: number; status_filter?: RevenueStatus }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<RevenuePayload>({
  project_id: 0, amount: 0, recognized_date: new Date().toISOString().slice(0, 10),
  invoice_no: '', description: '', status: 'pending',
})

const STATUS_LABEL: Record<string, string> = { pending: '待回款', received: '已到账', written_off: '坏账核销' }
const STATUS_TYPE: Record<string, string> = { pending: 'warning', received: 'success', written_off: 'info' }

async function load() {
  loading.value = true
  try {
    rows.value = await listRevenues(filter)
    if (projects.value.length === 0) {
      projects.value = await listProjects()
      revenueProjects.value = projects.value.filter((p) => p.kind === 'revenue')
    }
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    project_id: revenueProjects.value[0]?.id || 0,
    amount: 0, recognized_date: new Date().toISOString().slice(0, 10),
    invoice_no: '', description: '', status: 'pending',
  })
  dialog.value = true
}

function openEdit(r: ProjectRevenue) {
  editingId.value = r.id
  Object.assign(form, {
    project_id: r.project_id, amount: Number(r.amount),
    recognized_date: r.recognized_date, invoice_no: r.invoice_no || '',
    description: r.description || '', status: r.status,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.project_id || !form.amount || !form.recognized_date) {
    ElMessage.warning('项目 / 金额 / 确认日期 必填')
    return
  }
  if (editingId.value === null) await createRevenue(form)
  else {
    const { project_id, ...rest } = form
    void project_id
    await updateRevenue(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(r: ProjectRevenue) {
  await ElMessageBox.confirm(`删除收入记录 #${r.id} (HK$ ${r.amount})？`, '提示', { type: 'warning' })
  await deleteRevenue(r.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <el-select v-model="filter.project_id" placeholder="按项目筛选" clearable filterable style="width: 220px" @change="load">
        <el-option v-for="p in revenueProjects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="filter.status_filter" placeholder="按状态" clearable style="width: 130px" @change="load">
        <el-option v-for="(v, k) in STATUS_LABEL" :key="k" :label="v" :value="k" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增收入记录</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="recognized_date" label="确认日期" width="120" sortable />
      <el-table-column prop="project_name" label="项目" min-width="200" />
      <el-table-column label="金额" width="140" align="right">
        <template #default="{ row }">HK$ {{ row.amount }}</template>
      </el-table-column>
      <el-table-column prop="invoice_no" label="发票号" width="140" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status] as any">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="received_at" label="到账时间" width="180" />
      <el-table-column prop="description" label="备注" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增收入记录' : '编辑收入记录'" width="560px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" :disabled="editingId !== null" filterable style="width: 100%">
            <el-option v-for="p in revenueProjects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">仅"有收入项目"可登记收入</div>
        </el-form-item>
        <el-form-item label="金额 (HKD)" required>
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="确认日期" required>
          <el-date-picker v-model="form.recognized_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="发票号"><el-input v-model="form.invoice_no" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="(v, k) in STATUS_LABEL" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
