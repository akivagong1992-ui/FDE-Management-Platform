<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createExpense, listExpenses,
  type ExpensePayload, type ExpenseRequest, type ExpenseStatus,
} from '@/api/expenses'
import { listProjects, type Project } from '@/api/projects'
import { listDict, type DictItem } from '@/api/dataDict'

const STATUS_LABEL: Record<ExpenseStatus, string> = {
  pending: '待审', approved: '已批准', rejected: '已拒', paid: '已支付',
}
const STATUS_TYPE: Record<ExpenseStatus, 'warning' | 'success' | 'danger' | 'info'> = {
  pending: 'warning', approved: 'success', rejected: 'danger', paid: 'info',
}

const rows = ref<ExpenseRequest[]>([])
const projects = ref<Project[]>([])
const types = ref<DictItem[]>([])
const loading = ref(false)
const tab = ref<'all' | ExpenseStatus>('all')

const dialog = ref(false)
const today = () => new Date().toISOString().slice(0, 10)
const form = reactive<ExpensePayload>({
  project_id: 0, supplier_id: null, expense_type: 'material',
  title: '', amount: 0,
  expense_date: today(), description: '',
})

async function load() {
  loading.value = true
  try {
    rows.value = await listExpenses()
    if (projects.value.length === 0) projects.value = await listProjects()
    if (types.value.length === 0) types.value = await listDict('expense_type')
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  if (tab.value === 'all') return rows.value
  return rows.value.filter((r) => r.status === tab.value)
})
const pendingCount = computed(() => rows.value.filter((r) => r.status === 'pending').length)
const rejectedCount = computed(() => rows.value.filter((r) => r.status === 'rejected').length)
const approvedCount = computed(() => rows.value.filter((r) => r.status === 'approved').length)
const totalApproved = computed(() =>
  rows.value
    .filter((r) => r.status === 'approved' || r.status === 'paid')
    .reduce((acc, r) => acc + Number(r.amount), 0)
    .toLocaleString('zh-CN', { maximumFractionDigits: 2 }),
)

function openCreate() {
  Object.assign(form, {
    project_id: projects.value[0]?.id || 0,
    supplier_id: null,
    expense_type: types.value[0]?.code || 'material',
    title: '', amount: 0,
    expense_date: today(), description: '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.project_id) { ElMessage.warning('请选择项目'); return }
  if (!form.expense_type) { ElMessage.warning('请选择支出类型'); return }
  if (!form.title.trim()) { ElMessage.warning('标题必填'); return }
  if (!form.amount || form.amount <= 0) { ElMessage.warning('金额必须 > 0'); return }
  const payload: any = { ...form }
  if (!payload.supplier_id) payload.supplier_id = null
  if (!payload.description) payload.description = null
  await createExpense(payload)
  ElMessage.success('已提交支出申请，等管理者审批')
  dialog.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600">我的支出申请</span>
        <span style="color: #909399; font-size: 12px">
          待审 <strong style="color: #e6a23c">{{ pendingCount }}</strong> ·
          已批 <strong style="color: #67c23a">{{ approvedCount }}</strong> ·
          已拒 <strong style="color: #f56c6c">{{ rejectedCount }}</strong> ·
          已批准累计 <strong style="color: #67c23a">HK$ {{ totalApproved }}</strong>
        </span>
      </div>
    </template>

    <div style="display: flex; gap: 12px; margin-bottom: 16px; align-items: center">
      <el-radio-group v-model="tab">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="pending">
          待审 <el-badge v-if="pendingCount > 0" :value="pendingCount" type="warning" />
        </el-radio-button>
        <el-radio-button label="rejected">
          已拒 <el-badge v-if="rejectedCount > 0" :value="rejectedCount" type="danger" />
        </el-radio-button>
        <el-radio-button label="approved">已批准</el-radio-button>
        <el-radio-button label="paid">已支付</el-radio-button>
      </el-radio-group>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">💰 申请支出</el-button>
    </div>

    <el-table :data="filtered" v-loading="loading" stripe>
      <el-table-column prop="id" label="单号" width="70" />
      <el-table-column prop="created_at" label="提交时间" width="160">
        <template #default="{ row }">{{ row.created_at?.slice(0, 16).replace('T', ' ') }}</template>
      </el-table-column>
      <el-table-column label="项目" min-width="160">
        <template #default="{ row }">{{ row.project_name }}</template>
      </el-table-column>
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ row.expense_type_label || row.expense_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column label="金额" width="120" align="right">
        <template #default="{ row }">
          <strong>HK$ {{ Number(row.amount).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) }}</strong>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status as ExpenseStatus]" size="small">
            {{ STATUS_LABEL[row.status as ExpenseStatus] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="管理者批注 / 拒绝理由" min-width="200">
        <template #default="{ row }">
          <span v-if="row.status === 'rejected' && row.approval_note"
                style="color: #f56c6c; font-size: 13px">
            ✗ {{ row.approval_note }}
          </span>
          <span v-else-if="row.status === 'approved' && row.approval_note"
                style="color: #67c23a; font-size: 13px">
            ✓ {{ row.approval_note }}
          </span>
          <span v-else style="color: #c0c4cc; font-size: 12px">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="申请支出" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" filterable style="width: 100%">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="类型" required>
              <el-select v-model="form.expense_type" style="width: 100%">
                <el-option v-for="t in types" :key="t.code" :label="t.label" :value="t.code" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="金额 (HKD)" required>
              <el-input-number v-model="form.amount" :min="0" :precision="2" :step="100" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="例如：中环现场出差打车 / 项目机房备件采购" />
        </el-form-item>
        <el-form-item label="发生日期">
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" style="width: 220px" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="3"
                    placeholder="详细说明 — 越详细越快通过审批（用途、必要性、是否事先口头确认 etc.）" />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon style="margin-top: 4px">
          <template #title>
            提交后状态为「待审」。管理者批准 / 拒绝后，结果与批注/拒绝理由会显示在列表
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">提交审批</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>
