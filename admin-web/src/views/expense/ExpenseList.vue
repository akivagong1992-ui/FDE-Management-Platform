<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  approveExpense, createExpense, deleteExpense, listExpenses, markPaid, rejectExpense, updateExpense,
  type ExpensePayload, type ExpenseRequest, type ExpenseStatus,
} from '@/api/expenses'
import { listSuppliers, type Supplier } from '@/api/suppliers'
import { listProjects, type Project } from '@/api/projects'
import { listDict, type DictItem } from '@/api/dataDict'

const auth = useAuthStore()
const isApprover = computed(() => ['admin', 'lead', 'finance'].includes(auth.role || ''))

const rows = ref<ExpenseRequest[]>([])
const suppliers = ref<Supplier[]>([])
const projects = ref<Project[]>([])
const types = ref<DictItem[]>([])
const loading = ref(false)
const filter = reactive<{ project_id?: number; expense_type?: string; status_filter?: ExpenseStatus }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<ExpensePayload>({
  project_id: 0, supplier_id: null, expense_type: 'material', title: '', amount: 0,
  expense_date: new Date().toISOString().slice(0, 10), description: '',
})

const STATUS_LABEL: Record<string, string> = { pending: '待审批', approved: '已批准', rejected: '已驳回', paid: '已支付' }
const STATUS_TYPE: Record<string, string> = { pending: 'warning', approved: 'success', rejected: 'info', paid: '' }

async function load() {
  loading.value = true
  try {
    rows.value = await listExpenses(filter)
    if (suppliers.value.length === 0) suppliers.value = await listSuppliers()
    if (projects.value.length === 0) projects.value = await listProjects()
    if (types.value.length === 0) types.value = await listDict('expense_type')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    project_id: projects.value[0]?.id || 0,
    supplier_id: null, expense_type: 'material', title: '', amount: 0,
    expense_date: new Date().toISOString().slice(0, 10), description: '',
  })
  dialog.value = true
}

function openEdit(e: ExpenseRequest) {
  editingId.value = e.id
  Object.assign(form, {
    project_id: e.project_id, supplier_id: e.supplier_id,
    expense_type: e.expense_type, title: e.title,
    amount: Number(e.amount), expense_date: e.expense_date || undefined,
    description: e.description || '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.project_id || !form.title || !form.amount) {
    ElMessage.warning('项目 / 标题 / 金额 必填')
    return
  }
  if (editingId.value === null) await createExpense(form)
  else await updateExpense(editingId.value, form)
  ElMessage.success('已保存（待审批）')
  dialog.value = false
  await load()
}

async function onApprove(e: ExpenseRequest) {
  const { value } = await ElMessageBox.prompt('批准备注（可选）', '批准支出', { inputType: 'textarea', confirmButtonText: '批准' }).catch(() => ({ value: null }))
  if (value === null) return
  await approveExpense(e.id, value as string)
  ElMessage.success('已批准')
  await load()
}

async function onReject(e: ExpenseRequest) {
  const { value } = await ElMessageBox.prompt('驳回原因（必填）', '驳回支出', { inputType: 'textarea', confirmButtonText: '驳回', inputValidator: (v) => !!v || '原因必填' }).catch(() => ({ value: null }))
  if (value === null) return
  await rejectExpense(e.id, value as string)
  ElMessage.success('已驳回')
  await load()
}

async function onMarkPaid(e: ExpenseRequest) {
  await ElMessageBox.confirm(`将 "${e.title}" 标记为已支付？`, '提示', { type: 'warning' })
  await markPaid(e.id)
  ElMessage.success('已标记为已支付')
  await load()
}

async function onDelete(e: ExpenseRequest) {
  await ElMessageBox.confirm(`删除支出单 "${e.title}"？`, '提示', { type: 'warning' })
  await deleteExpense(e.id)
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
      <el-select v-model="filter.expense_type" placeholder="按类型筛选" clearable style="width: 200px" @change="load">
        <el-option v-for="t in types" :key="t.code" :label="t.label" :value="t.code" />
      </el-select>
      <el-select v-model="filter.status_filter" placeholder="按状态筛选" clearable style="width: 140px" @change="load">
        <el-option v-for="(v, k) in STATUS_LABEL" :key="k" :label="v" :value="k" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增支出申请</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="类型" width="140">
        <template #default="{ row }">
          <el-tag>{{ row.expense_type_label || row.expense_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="project_name" label="项目" min-width="160" />
      <el-table-column prop="supplier_name" label="供应商" width="140" />
      <el-table-column label="金额" width="120">
        <template #default="{ row }">HK$ {{ row.amount }}</template>
      </el-table-column>
      <el-table-column prop="expense_date" label="发生日" width="110" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status] as any">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" link size="small" @click="openEdit(row)">编辑</el-button>
          <template v-if="isApprover && row.status === 'pending'">
            <el-button link type="success" size="small" @click="onApprove(row)">批准</el-button>
            <el-button link type="warning" size="small" @click="onReject(row)">驳回</el-button>
          </template>
          <el-button v-if="isApprover && row.status === 'approved'" link type="primary" size="small" @click="onMarkPaid(row)">标记已付</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增支出申请' : '编辑支出申请'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" filterable style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="支出类型" required>
          <el-select v-model="form.expense_type" style="width: 100%">
            <el-option v-for="t in types" :key="t.code" :label="t.label" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="form.supplier_id" clearable filterable placeholder="可选" style="width: 100%">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="金额 (HKD)" required>
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 220px" />
        </el-form-item>
        <el-form-item label="发生日">
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
