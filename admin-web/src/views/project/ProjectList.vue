<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  createProject, deleteProject, listProjects, updateProject,
  DISTRICT_LABELS, BENCHMARK_BASIS_LABELS, BID_OUTCOME_LABELS, BID_OUTCOME_TYPES,
  type BenchmarkBasis, type BidOutcome, type HKDistrict,
  type Project, type ProjectPayload, type ProjectStatus, type ProjectKind,
} from '@/api/projects'
import { listNeedParties, type NeedParty } from '@/api/needParties'
import { listSalesPersons, type SalesPerson } from '@/api/salesPersons'
import ProjectDrawer from './ProjectDrawer.vue'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'
import { fmt2 } from '@/utils/format'

const auth = useAuthStore()
const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin')

const rows = ref<Project[]>([])
const needParties = ref<NeedParty[]>([])
const salesPersons = ref<SalesPerson[]>([])
const loading = ref(false)

const filter = reactive<{ kind?: ProjectKind; status_filter?: ProjectStatus; sales_person_id?: number; need_party_id?: number }>({})

// ─ Column visibility + per-column filter (Excel-style) ──────────────
const COL_DEFS: { key: string; label: string }[] = [
  { key: 'code', label: '编号' },
  { key: 'name', label: '项目名称' },
  { key: 'kind', label: '类型' },
  { key: 'status', label: '状态' },
  { key: 'bid_outcome', label: '投标结果' },
  { key: 'need_party_name', label: '客户名称' },
  { key: 'sales_person_name', label: '销售' },
  { key: 'outsource_benchmark_amount', label: '服务商价格' },
  { key: 'value_created_computed', label: '效益金额' },
  { key: 'planned_end_date', label: '计划完成' },
]
// 默认隐藏 ID 列（仅作为内部主键，用户不需要看；可通过"显示列"菜单打开）
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))

// 仅枚举/字符串列支持 ▾ 过滤；金额/日期不处理
const FILTERABLE_KEYS = ['code', 'name', 'kind', 'status', 'bid_outcome', 'need_party_name', 'sales_person_name']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)

// 把行的原始值格式化成显示文本（filter / 过滤都用这个文本）
function cellText(r: Project, key: string): string {
  switch (key) {
    case 'kind': return r.kind === 'revenue' ? '有收入' : '无收入'
    case 'status': return STATUS_LABEL[r.status] || r.status
    case 'bid_outcome':
      return r.kind === 'no_revenue' ? 'NA' : (BID_OUTCOME_LABELS[r.bid_outcome as BidOutcome] || r.bid_outcome)
    default: {
      const v = (r as unknown as Record<string, unknown>)[key]
      return v == null ? '' : String(v)
    }
  }
}

function distinctValues(key: string): string[] {
  const set = new Set<string>()
  rows.value.forEach((r) => {
    const v = cellText(r, key)
    if (v !== '') set.add(v)
  })
  return Array.from(set).sort()
}

const filteredRows = computed(() => {
  return rows.value.filter((row) => {
    for (const [key, sel] of Object.entries(filters.value)) {
      if (sel.size === 0) continue
      if (!sel.has(cellText(row, key))) return false
    }
    return true
  })
})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<ProjectPayload>({
  name: '', need_party_id: 0, sales_person_id: 0, kind: 'revenue',
  outsource_benchmark_amount: undefined, value_created_basis: undefined, value_created_note: '',
  status: 'drafting', bid_outcome: 'pending',
  code: '', planned_start_date: undefined, planned_end_date: undefined,
  actual_start_date: undefined, actual_end_date: undefined, description: '',
  district: null, rework_count: 0, change_count: 0, renewal_of_project_id: null,
  benchmark_basis: null, benchmark_basis_note: '',
})

const drawerOpen = ref(false)
const drawerId = ref<number | null>(null)

const STATUS_OPTIONS: { label: string; value: ProjectStatus }[] = [
  { label: '立项', value: 'drafting' },
  { label: '进行中', value: 'in_progress' },
  { label: '验收', value: 'accepting' },
  { label: '归档', value: 'archived' },
  { label: '跑单 / 取消', value: 'cancelled' },
]
const STATUS_LABEL: Record<string, string> = Object.fromEntries(STATUS_OPTIONS.map((o) => [o.value, o.label]))

const BID_OUTCOME_OPTIONS: { label: string; value: BidOutcome }[] = [
  { label: '投标中 / 未定', value: 'pending' },
  { label: '已中标', value: 'won' },
  { label: '已丢标', value: 'lost' },
  { label: '中标后跑单', value: 'escaped' },
]

const BASIS_OPTIONS = [
  { label: '等同外包服务所抵消的成本（默认）', value: 'outsource_equiv' },
  { label: '其他（备注必填）', value: 'other' },
]

async function load() {
  loading.value = true
  try {
    rows.value = await listProjects(filter)
    if (needParties.value.length === 0) needParties.value = await listNeedParties()
    if (salesPersons.value.length === 0) salesPersons.value = await listSalesPersons()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '', code: '',
    need_party_id: needParties.value[0]?.id || 0,
    sales_person_id: salesPersons.value.find((s) => s.is_active)?.id || 0,
    kind: 'revenue',
    outsource_benchmark_amount: undefined,
    value_created_basis: 'outsource_equiv', value_created_note: '',
    status: 'drafting', bid_outcome: 'pending',
    planned_start_date: undefined, planned_end_date: undefined,
    actual_start_date: undefined, actual_end_date: undefined,
    description: '',
    district: null, rework_count: 0, change_count: 0, renewal_of_project_id: null,
    benchmark_basis: null, benchmark_basis_note: '',
  })
  dialog.value = true
}

function openEdit(p: Project) {
  editingId.value = p.id
  Object.assign(form, {
    code: p.code || '',
    name: p.name,
    need_party_id: p.need_party_id,
    sales_person_id: p.sales_person_id,
    pm_user_id: p.pm_user_id,
    kind: p.kind,
    outsource_benchmark_amount: p.outsource_benchmark_amount == null ? undefined : Number(p.outsource_benchmark_amount),
    value_created_basis: p.value_created_basis || 'outsource_equiv',
    value_created_note: p.value_created_note || '',
    status: p.status,
    bid_outcome: p.bid_outcome,
    planned_start_date: p.planned_start_date || undefined,
    planned_end_date: p.planned_end_date || undefined,
    actual_start_date: p.actual_start_date || undefined,
    actual_end_date: p.actual_end_date || undefined,
    description: p.description || '',
    district: p.district || null,
    rework_count: p.rework_count || 0,
    change_count: p.change_count || 0,
    renewal_of_project_id: p.renewal_of_project_id || null,
    benchmark_basis: p.benchmark_basis || null,
    benchmark_basis_note: p.benchmark_basis_note || '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.name || !form.need_party_id || !form.sales_person_id) {
    ElMessage.warning('名称 + 客户名称 + 销售人员必填')
    return
  }
  if (form.kind === 'no_revenue' && form.value_created_basis === 'other' && !form.value_created_note) {
    ElMessage.warning('价值依据=其他 时必须填备注')
    return
  }
  if (editingId.value === null) {
    await createProject(form)
  } else {
    // sales_person_id is not allowed via PATCH; transfer-sales is the path
    const { sales_person_id, ...rest } = form
    void sales_person_id
    await updateProject(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(p: Project) {
  await ElMessageBox.confirm(`删除项目 "${p.name}"？`, '提示', { type: 'warning' })
  await deleteProject(p.id)
  ElMessage.success('已删除')
  await load()
}

function openDetail(p: Project) {
  drawerId.value = p.id
  drawerOpen.value = true
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button type="primary" @click="openCreate">新增项目</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe highlight-current-row @row-click="openDetail">
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('code')" label="编号" width="100">
        <template #header>
          编号
          <ColumnFilterMenu :options="distinctValues('code')" v-model="filters.code" />
        </template>
        <template #default="{ row }">{{ row.code }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('name')" label="项目名称" min-width="180">
        <template #header>
          项目名称
          <ColumnFilterMenu :options="distinctValues('name')" v-model="filters.name" :width="260" />
        </template>
        <template #default="{ row }">{{ row.name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('kind')" label="类型" width="110">
        <template #header>
          类型
          <ColumnFilterMenu :options="distinctValues('kind')" v-model="filters.kind" />
        </template>
        <template #default="{ row }">
          <el-tag :type="row.kind === 'revenue' ? 'success' : 'warning'">
            {{ row.kind === 'revenue' ? '有收入' : '无收入' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('status')" label="状态" width="110">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('status')" v-model="filters.status" />
        </template>
        <template #default="{ row }"><el-tag>{{ STATUS_LABEL[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('bid_outcome')" label="投标结果" width="130">
        <template #header>
          投标结果
          <ColumnFilterMenu :options="distinctValues('bid_outcome')" v-model="filters.bid_outcome" />
        </template>
        <template #default="{ row }">
          <span v-if="row.kind === 'no_revenue'" style="color: #c0c4cc">NA</span>
          <el-tag v-else :type="BID_OUTCOME_TYPES[row.bid_outcome as BidOutcome]" size="small">
            {{ BID_OUTCOME_LABELS[row.bid_outcome as BidOutcome] || row.bid_outcome }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('need_party_name')" label="客户名称" min-width="170">
        <template #header>
          客户名称
          <ColumnFilterMenu :options="distinctValues('need_party_name')" v-model="filters.need_party_name" :width="240" />
        </template>
        <template #default="{ row }">{{ row.need_party_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('sales_person_name')" label="销售" width="140">
        <template #header>
          销售
          <ColumnFilterMenu :options="distinctValues('sales_person_name')" v-model="filters.sales_person_name" />
        </template>
        <template #default="{ row }">
          {{ row.sales_person_name }}
          <el-tag v-if="!row.sales_person_active" type="info" size="small">停用</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('outsource_benchmark_amount')" label="服务商价格 (HKD)" width="160">
        <template #default="{ row }">
          <span v-if="row.outsource_benchmark_amount">{{ fmt2(row.outsource_benchmark_amount) }}</span>
          <span v-else style="color: #c0c4cc; font-size: 12px">还未询价</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('value_created_computed')" label="效益金额 (HKD)" width="170">
        <template #header>
          <el-tooltip placement="top">
            <template #content>
              <div style="max-width: 280px; line-height: 1.5">
                有收入项目：<strong>服务商价格 − 团队入账</strong>，须 <strong>投标结果=已中标</strong><br />
                无收入项目：<strong>= 服务商价格</strong>（状态验收/归档时）
              </div>
            </template>
            <span style="cursor: help">效益金额 (HKD) <span style="color: #909399; font-size: 11px">ⓘ</span></span>
          </el-tooltip>
        </template>
        <template #default="{ row }">
          <span v-if="row.value_created_computed" style="color: #e6a23c">{{ fmt2(row.value_created_computed) }}</span>
          <span v-else style="color: #c0c4cc; font-size: 12px">还未形成实际效益</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('planned_end_date')" prop="planned_end_date" label="计划完成" width="120" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click.stop="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click.stop="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialog"
      :title="editingId === null ? '新增项目' : '编辑项目'"
      width="760px"
    >
      <el-form :model="form" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="16"><el-form-item label="项目名称" required><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="编号"><el-input v-model="form.code" placeholder="可选" /></el-form-item></el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.need_party_id" filterable style="width: 100%">
                <el-option v-for="np in needParties" :key="np.id" :label="np.name" :value="np.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="销售人员" required>
              <el-select
                v-model="form.sales_person_id" filterable style="width: 100%"
                :disabled="editingId !== null"
                :placeholder="editingId !== null ? '在详情页用「转移销售」修改' : '选择销售'"
              >
                <el-option
                  v-for="sp in salesPersons.filter((s) => s.is_active)"
                  :key="sp.id" :label="sp.name" :value="sp.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="无收入项目">
          <el-tooltip :disabled="isLead" content="仅团队负责人 (lead/admin) 可勾选" placement="top">
            <el-switch
              v-model="form.kind"
              :disabled="!isLead"
              active-value="no_revenue" inactive-value="revenue"
            />
          </el-tooltip>
          <span style="margin-left: 12px; color: #909399; font-size: 13px">
            勾选后：项目状态改为验收或归档时，效益金额 = 服务商价格（计入驾驶舱降本）
          </span>
        </el-form-item>

        <template v-if="form.kind === 'no_revenue'">
          <el-form-item label="外部服务商报价 (HKD)">
            <el-input-number
              v-model="form.outsource_benchmark_amount" :min="0" :precision="2" style="width: 240px"
            />
          </el-form-item>
          <el-form-item label="价格来源依据" v-if="form.outsource_benchmark_amount">
            <el-select v-model="form.benchmark_basis" clearable style="width: 100%" placeholder="选择依据">
              <el-option v-for="(label, code) in BENCHMARK_BASIS_LABELS" :key="code" :label="label" :value="code" />
            </el-select>
          </el-form-item>
        </template>

        <template v-if="form.kind === 'no_revenue'">
          <el-form-item label="价值依据">
            <el-select v-model="form.value_created_basis" style="width: 100%">
              <el-option v-for="o in BASIS_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item :label="form.value_created_basis === 'other' ? '依据说明 *' : '依据说明'">
            <el-input v-model="form.value_created_note" type="textarea" :rows="2" />
          </el-form-item>
        </template>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="o in STATUS_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.kind === 'revenue'">
            <el-form-item label="投标结果">
              <el-select v-model="form.bid_outcome" style="width: 100%">
                <el-option v-for="o in BID_OUTCOME_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
              <div style="color: #909399; font-size: 12px; margin-top: 4px; line-height: 1.5">
                必须同时满足 <strong>投标结果=已中标</strong> 且 <strong>已录入收入记录</strong>，
                项目入账才计入团队收入 / 驾驶舱降本
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地区">
              <el-select v-model="form.district" clearable placeholder="未指定" style="width: 100%">
                <el-option v-for="(label, code) in DISTRICT_LABELS" :key="code" :label="label" :value="code" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划开始">
              <el-date-picker v-model="form.planned_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计划完成">
              <el-date-picker v-model="form.planned_end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <ProjectDrawer v-model="drawerOpen" :project-id="drawerId" @refresh="load" />
  </div>
</template>
