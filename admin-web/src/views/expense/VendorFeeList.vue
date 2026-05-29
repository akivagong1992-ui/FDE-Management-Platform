<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createFee, deleteFee, listFees, updateFee,
  type VendorServiceFee, type VsfPayload, type VsfStatus,
} from '@/api/vendorServiceFees'
import { listVendors, type Vendor } from '@/api/vendors'
import { listEngineers, type Engineer } from '@/api/engineers'
import { listProjects, type Project } from '@/api/projects'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'
import { fmt2 } from '@/utils/format'

const rows = ref<VendorServiceFee[]>([])
const vendors = ref<Vendor[]>([])
const engineers = ref<Engineer[]>([])
const projects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ vendor_id?: number; project_id?: number; status_filter?: VsfStatus }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<VsfPayload>({
  vendor_id: 0, engineer_id: null, project_id: null, fee_type: 'monthly_per_engineer',
  period_start: '', period_end: '', amount: 0, description: '', status: 'draft',
})

const STATUS_LABEL: Record<string, string> = { draft: '草稿', billed: '已开票', paid: '已支付' }
const STATUS_TYPE: Record<string, string> = { draft: 'info', billed: 'warning', paid: 'success' }

async function load() {
  loading.value = true
  try {
    rows.value = await listFees(filter)
    if (vendors.value.length === 0) vendors.value = await listVendors()
    if (engineers.value.length === 0) engineers.value = await listEngineers()
    if (projects.value.length === 0) projects.value = await listProjects()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    vendor_id: vendors.value[0]?.id || 0, engineer_id: null, project_id: null,
    fee_type: 'monthly_per_engineer', period_start: '', period_end: '',
    amount: 0, description: '', status: 'draft',
  })
  dialog.value = true
}

function openEdit(v: VendorServiceFee) {
  editingId.value = v.id
  Object.assign(form, {
    vendor_id: v.vendor_id, engineer_id: v.engineer_id, project_id: v.project_id,
    fee_type: v.fee_type, period_start: v.period_start, period_end: v.period_end,
    amount: Number(v.amount),
    description: v.description || '', status: v.status,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.vendor_id || !form.period_start || !form.period_end || !form.amount) {
    ElMessage.warning('Vendor / 期始 / 期末 / 金额 必填')
    return
  }
  if (editingId.value === null) await createFee(form)
  else {
    const { vendor_id, engineer_id, project_id, ...rest } = form
    void vendor_id; void engineer_id; void project_id
    await updateFee(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(v: VendorServiceFee) {
  await ElMessageBox.confirm(`删除服务费记录 #${v.id} (HK$ ${v.amount})？`, '提示', { type: 'warning' })
  await deleteFee(v.id)
  ElMessage.success('已删除')
  await load()
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'engineer_name', label: '工程师' },
  { key: 'project_name', label: '项目' },
  { key: 'period', label: '期间' },
  { key: 'amount', label: '金额' },
  { key: 'status', label: '状态' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['vendor_name', 'engineer_name', 'project_name', 'status']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: VendorServiceFee, key: string): string {
  if (key === 'status') return STATUS_LABEL[r.status] || r.status
  const v = (r as unknown as Record<string, unknown>)[key]
  return v == null ? '' : String(v)
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
    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px">
      <template #title>
        VSF 由 ProjectRevenue 自动镜像（pass-through 模型）——录入收入时选 vendor 即可，这里只读对账。
      </template>
    </el-alert>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('vendor_name')" label="Vendor" width="160">
        <template #header>
          Vendor
          <ColumnFilterMenu :options="distinctValues('vendor_name')" v-model="filters.vendor_name" />
        </template>
        <template #default="{ row }">{{ row.vendor_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('engineer_name')" label="工程师" width="120">
        <template #header>
          工程师
          <ColumnFilterMenu :options="distinctValues('engineer_name')" v-model="filters.engineer_name" />
        </template>
        <template #default="{ row }">{{ row.engineer_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('project_name')" label="项目" min-width="180">
        <template #header>
          项目
          <ColumnFilterMenu :options="distinctValues('project_name')" v-model="filters.project_name" :width="260" />
        </template>
        <template #default="{ row }">{{ row.project_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('period')" label="期间" width="220">
        <template #default="{ row }">{{ row.period_start }} ~ {{ row.period_end }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('amount')" label="金额 (HKD)" width="140" align="right">
        <template #default="{ row }">{{ fmt2(row.amount) }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('status')" label="状态" width="120">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('status')" v-model="filters.status" />
        </template>
        <template #default="{ row }">
          <el-tag :type="STATUS_TYPE[row.status] as any">{{ STATUS_LABEL[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增服务费记录' : '编辑服务费记录'" width="640px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="Vendor" required>
              <el-select v-model="form.vendor_id" :disabled="editingId !== null" filterable style="width: 100%">
                <el-option v-for="v in vendors" :key="v.id" :label="v.name" :value="v.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="form.fee_type" style="width: 100%">
                <el-option label="按工程师月度" value="monthly_per_engineer" />
                <el-option label="按项目里程碑" value="project_milestone" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="工程师">
              <el-select v-model="form.engineer_id" :disabled="editingId !== null" clearable filterable placeholder="可选" style="width: 100%">
                <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目">
              <el-select v-model="form.project_id" :disabled="editingId !== null" clearable filterable placeholder="可选 (挂项目做成本归集)" style="width: 100%">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="期间开始" required>
              <el-date-picker v-model="form.period_start" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期间结束" required>
              <el-date-picker v-model="form.period_end" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="金额 (HKD)" required>
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="(lab, k) in STATUS_LABEL" :key="k" :label="lab" :value="k" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
