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
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'
import { fmt2 } from '@/utils/format'

const auth = useAuthStore()
const isApprover = computed(() => ['admin', 'lead', 'finance'].includes(auth.role || ''))
const isVendor = computed(() => auth.role === 'vendor')

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

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'id', label: 'ID' },
  { key: 'expense_type', label: '类型' },
  { key: 'title', label: '标题' },
  { key: 'project_name', label: '项目' },
  { key: 'supplier_name', label: '供应商' },
  { key: 'amount', label: '金额' },
  { key: 'expense_date', label: '发生日' },
  { key: 'status', label: '状态' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['expense_type', 'title', 'project_name', 'supplier_name', 'status']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: ExpenseRequest, key: string): string {
  switch (key) {
    case 'expense_type': return r.expense_type_label || r.expense_type || ''
    case 'status': return STATUS_LABEL[r.status] || r.status
    default: {
      const v = (r as unknown as Record<string, unknown>)[key]
      return v == null ? '' : String(v)
    }
  }
}
function distinctValues(key: string): string[] {
  const set = new Set<string>()
  rows.value.forEach((r) => { const v = cellText(r, key); if (v !== '') set.add(v) })
  return Array.from(set).sort()
}
const filteredRows = computed(() =>
  rows.value.filter((row) => {
    for (const [key, sel] of Object.entries(filters.value)) {
      if (sel.size === 0) continue
      if (!sel.has(cellText(row, key))) return false
    }
    return true
  }),
)

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button v-if="isVendor" type="primary" @click="openCreate">新增支出申请</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('expense_type')" label="类型" width="160">
        <template #header>
          类型
          <ColumnFilterMenu :options="distinctValues('expense_type')" v-model="filters.expense_type" />
        </template>
        <template #default="{ row }">
          <el-tag>{{ row.expense_type_label || row.expense_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('title')" label="标题" min-width="180">
        <template #header>
          标题
          <ColumnFilterMenu :options="distinctValues('title')" v-model="filters.title" :width="260" />
        </template>
        <template #default="{ row }">{{ row.title }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('project_name')" label="项目" min-width="160">
        <template #header>
          项目
          <ColumnFilterMenu :options="distinctValues('project_name')" v-model="filters.project_name" :width="260" />
        </template>
        <template #default="{ row }">{{ row.project_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('supplier_name')" label="供应商" width="150">
        <template #header>
          供应商
          <ColumnFilterMenu :options="distinctValues('supplier_name')" v-model="filters.supplier_name" />
        </template>
        <template #default="{ row }">{{ row.supplier_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('amount')" label="金额" width="120">
        <template #default="{ row }">HK$ {{ fmt2(row.amount) }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('expense_date')" prop="expense_date" label="发生日" width="110" />
      <el-table-column v-if="visibleCols.has('status')" label="状态" width="120">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('status')" v-model="filters.status" />
        </template>
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status] as any">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <!-- vendor 可编辑/删除自己 pending 的；不能审批 -->
          <el-button v-if="isVendor && row.status === 'pending'" link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="isVendor && row.status === 'pending'" link type="danger" size="small" @click="onDelete(row)">撤回</el-button>
          <!-- approver 看见审批按钮 -->
          <template v-if="isApprover && row.status === 'pending'">
            <el-button link type="success" size="small" @click="onApprove(row)">批准</el-button>
            <el-button link type="warning" size="small" @click="onReject(row)">驳回</el-button>
          </template>
          <el-button v-if="isApprover && row.status === 'approved'" link type="primary" size="small" @click="onMarkPaid(row)">标记已付</el-button>
          <el-button v-if="isApprover" link type="danger" size="small" @click="onDelete(row)">删除</el-button>
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
