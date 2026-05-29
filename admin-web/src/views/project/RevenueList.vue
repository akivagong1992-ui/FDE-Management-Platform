<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRevenue, deleteRevenue, listRevenues, updateRevenue,
  type ProjectRevenue, type RevenuePayload,
} from '@/api/projectRevenues'
import {
  listProjects, updateProject, BENCHMARK_BASIS_LABELS,
  type BenchmarkBasis, type Project,
} from '@/api/projects'
import { listVendors, type Vendor } from '@/api/vendors'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'
import { fmt2 } from '@/utils/format'

const rows = ref<ProjectRevenue[]>([])
const projects = ref<Project[]>([])
const revenueProjects = ref<Project[]>([])
const vendors = ref<Vendor[]>([])
const loading = ref(false)
const filter = reactive<{ project_id?: number }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<RevenuePayload>({
  project_id: 0, vendor_id: 0, amount: 0, gross_amount: undefined, non_service_expense: undefined,
  recognized_date: new Date().toISOString().slice(0, 10),
  description: '',
})
// 报价相关字段直接读写 Project；保存时单独 PATCH project（不属于 ProjectRevenue 数据）
const benchmarkForm = reactive<{ amount: number | undefined; basis: BenchmarkBasis | undefined }>({
  amount: undefined, basis: undefined,
})

async function load() {
  loading.value = true
  try {
    rows.value = await listRevenues(filter)
    projects.value = await listProjects()  // 刷新 — benchmark 可能刚被改
    revenueProjects.value = projects.value.filter((p) => p.kind === 'revenue')
    if (vendors.value.length === 0) vendors.value = await listVendors()
  } finally {
    loading.value = false
  }
}

function syncBenchmarkFromProject(projectId: number) {
  const p = revenueProjects.value.find((x) => x.id === projectId)
  benchmarkForm.amount = p?.outsource_benchmark_amount == null
    ? undefined : Number(p.outsource_benchmark_amount)
  benchmarkForm.basis = (p?.benchmark_basis as BenchmarkBasis | null) || undefined
}

// 切换项目时自动拉对应项目的当前 benchmark
watch(() => form.project_id, (pid) => {
  if (pid && dialog.value) syncBenchmarkFromProject(pid)
})

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    project_id: revenueProjects.value[0]?.id || 0,
    vendor_id: vendors.value[0]?.id || 0,
    amount: 0, gross_amount: undefined, non_service_expense: undefined,
    recognized_date: new Date().toISOString().slice(0, 10),
    description: '',
  })
  syncBenchmarkFromProject(form.project_id)
  dialog.value = true
}

function openEdit(r: ProjectRevenue) {
  editingId.value = r.id
  Object.assign(form, {
    project_id: r.project_id,
    vendor_id: r.vendor_id,
    amount: Number(r.amount),
    gross_amount: r.gross_amount == null ? undefined : Number(r.gross_amount),
    non_service_expense: r.non_service_expense == null ? undefined : Number(r.non_service_expense),
    recognized_date: r.recognized_date,
    description: r.description || '',
  })
  syncBenchmarkFromProject(r.project_id)
  dialog.value = true
}

async function onSubmit() {
  if (!form.project_id || !form.amount || !form.recognized_date) {
    ElMessage.warning('项目 / 团队入账 / 确认日期 必填')
    return
  }
  if (!form.vendor_id) {
    ElMessage.warning('经办 Vendor 必填 — 决定这笔钱 pass-through 到哪家')
    return
  }
  if (!form.gross_amount || Number(form.gross_amount) <= 0) {
    ElMessage.warning('客户付款总额 必填 — 公司毛利率统计需要此字段')
    return
  }
  if (form.non_service_expense == null) {
    ElMessage.warning('非服务开销 必填 — 纯服务项目请填 0')
    return
  }
  if (Number(form.non_service_expense) < 0) {
    ElMessage.warning('非服务开销不能为负数')
    return
  }
  if (Number(form.non_service_expense) >= Number(form.gross_amount)) {
    ElMessage.warning('非服务开销不能 ≥ 客户付款总额')
    return
  }
  if (!benchmarkForm.amount || benchmarkForm.amount <= 0) {
    ElMessage.warning('外部服务商报价 必填 — 建了收入意味着已经询过价，必须录入')
    return
  }
  if (!benchmarkForm.basis) {
    ElMessage.warning('价格来源依据 必填')
    return
  }
  // 1) 先同步 project 的 benchmark 字段（若用户改了/填了）
  const proj = revenueProjects.value.find((p) => p.id === form.project_id)
  const currentBench = proj?.outsource_benchmark_amount == null ? null : Number(proj.outsource_benchmark_amount)
  const currentBasis = (proj?.benchmark_basis as BenchmarkBasis | null) || null
  const nextBench = benchmarkForm.amount == null ? null : Number(benchmarkForm.amount)
  const nextBasis = benchmarkForm.basis || null
  if (nextBench !== currentBench || nextBasis !== currentBasis) {
    await updateProject(form.project_id, {
      outsource_benchmark_amount: nextBench,
      benchmark_basis: nextBasis,
    })
  }
  // 2) 再 POST / PATCH 收入记录
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

function projectMeta(projectId: number): { need_party: string; sales_person: string } {
  const p = projects.value.find((x) => x.id === projectId)
  return {
    need_party: p?.need_party_name || '—',
    sales_person: p?.sales_person_name || '—',
  }
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'recognized_date', label: '确认日期' },
  { key: 'project_name', label: '项目' },
  { key: 'need_party_name', label: '客户名称' },
  { key: 'sales_person_name', label: '销售' },
  { key: 'vendor_name', label: '经办 Vendor' },
  { key: 'gross_amount', label: '客户付款总额' },
  { key: 'non_service_expense', label: '非服务开销' },
  { key: 'amount', label: '团队入账' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['project_name', 'need_party_name', 'sales_person_name', 'vendor_name']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: ProjectRevenue, key: string): string {
  switch (key) {
    case 'need_party_name': return projectMeta(r.project_id).need_party
    case 'sales_person_name': return projectMeta(r.project_id).sales_person
    case 'project_name': return r.project_name || ''
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
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button type="primary" @click="openCreate">新增收入记录</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('recognized_date')" prop="recognized_date" label="确认日期" width="120" sortable />
      <el-table-column v-if="visibleCols.has('project_name')" label="项目" min-width="160">
        <template #header>
          项目
          <ColumnFilterMenu :options="distinctValues('project_name')" v-model="filters.project_name" :width="260" />
        </template>
        <template #default="{ row }">{{ row.project_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('need_party_name')" label="客户名称" min-width="140">
        <template #header>
          客户名称
          <ColumnFilterMenu :options="distinctValues('need_party_name')" v-model="filters.need_party_name" :width="240" />
        </template>
        <template #default="{ row }">{{ projectMeta(row.project_id).need_party }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('sales_person_name')" label="销售" width="130">
        <template #header>
          销售
          <ColumnFilterMenu :options="distinctValues('sales_person_name')" v-model="filters.sales_person_name" />
        </template>
        <template #default="{ row }">{{ projectMeta(row.project_id).sales_person }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('gross_amount')" label="客户付款总额" width="140" align="right">
        <template #default="{ row }">
          <span v-if="row.gross_amount != null">HK$ {{ fmt2(row.gross_amount) }}</span>
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('vendor_name')" label="经办 Vendor" width="140">
        <template #header>
          经办 Vendor
          <ColumnFilterMenu :options="distinctValues('vendor_name')" v-model="filters.vendor_name" />
        </template>
        <template #default="{ row }">{{ row.vendor_name || '—' }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('non_service_expense')" label="非服务开销" width="140" align="right">
        <template #default="{ row }">
          <span v-if="row.non_service_expense != null">HK$ {{ fmt2(row.non_service_expense) }}</span>
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('amount')" label="团队入账" width="140" align="right">
        <template #default="{ row }">HK$ {{ fmt2(row.amount) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增收入记录' : '编辑收入记录'" width="600px">
      <el-form :model="form" label-width="130px">
        <el-form-item label="项目" required>
          <el-select v-model="form.project_id" :disabled="editingId !== null" filterable style="width: 100%">
            <el-option v-for="p in revenueProjects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">仅"有收入项目"可登记收入</div>
        </el-form-item>

        <el-form-item label="经办 Vendor" required>
          <el-select v-model="form.vendor_id" filterable style="width: 100%">
            <el-option v-for="v in vendors" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            这笔团队入账 pass-through 到哪家 vendor — 保存时自动建一笔等额 VSF 镜像。多 vendor 项目录多条。
          </div>
        </el-form-item>

        <el-form-item label="外部服务商报价" required>
          <el-input-number v-model="benchmarkForm.amount" :min="0" :precision="2" style="width: 100%"
                           placeholder="HK$（vendor 真实询价金额）" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            建立收入即代表已询价 — 保存后写回项目，取代列表的「还未询价」占位
          </div>
        </el-form-item>
        <el-form-item label="价格来源依据" required>
          <el-select v-model="benchmarkForm.basis" clearable style="width: 100%" placeholder="选择来源">
            <el-option v-for="(label, code) in BENCHMARK_BASIS_LABELS" :key="code" :label="label" :value="code" />
          </el-select>
        </el-form-item>

        <el-form-item label="客户付款总额 (HKD)" required>
          <el-input-number v-model="form.gross_amount" :min="0" :precision="2" style="width: 100%"
                           placeholder="客户实际付公司的总钱数（销售切除前）" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            公司毛利率统计必填 — 团队入账通常占客户付款约 20%（销售切除 80%）
          </div>
        </el-form-item>
        <el-form-item label="非服务开销 (HKD)" required>
          <el-input-number v-model="form.non_service_expense" :min="0" :precision="2" style="width: 100%"
                           placeholder="硬件采购 / 第三方软件 / 物料 / 销售切除非工程师服务的部分" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            含硬件/物料/第三方等非服务部分；纯服务项目填 0。公式：毛利率 = (客户付款 − 团队入账 − 非服务开销) / 客户付款
          </div>
        </el-form-item>
        <el-form-item label="团队入账 (HKD)" required>
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            销售切除后流到工程师团队的部分（= 转给 Vendor 的金额）
          </div>
        </el-form-item>
        <el-form-item label="确认日期" required>
          <el-date-picker v-model="form.recognized_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
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
