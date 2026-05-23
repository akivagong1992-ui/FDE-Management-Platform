<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  createProject, deleteProject, listProjects, updateProject,
  DISTRICT_LABELS, BENCHMARK_BASIS_LABELS,
  type BenchmarkBasis, type HKDistrict,
  type Project, type ProjectPayload, type ProjectStatus, type ProjectKind,
} from '@/api/projects'
import { listNeedParties, type NeedParty } from '@/api/needParties'
import { listSalesPersons, type SalesPerson } from '@/api/salesPersons'
import ProjectDrawer from './ProjectDrawer.vue'

const auth = useAuthStore()
const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin')

const rows = ref<Project[]>([])
const needParties = ref<NeedParty[]>([])
const salesPersons = ref<SalesPerson[]>([])
const loading = ref(false)

const filter = reactive<{ kind?: ProjectKind; status_filter?: ProjectStatus; sales_person_id?: number; need_party_id?: number }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<ProjectPayload>({
  name: '', need_party_id: 0, sales_person_id: 0, kind: 'revenue',
  outsource_benchmark_amount: undefined, value_created_basis: undefined, value_created_note: '',
  status: 'drafting', code: '', planned_start_date: undefined, planned_end_date: undefined,
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
  { label: '收尾', value: 'closing' },
  { label: '归档', value: 'archived' },
  { label: '跑单 / 取消', value: 'cancelled' },
]
const STATUS_LABEL: Record<string, string> = Object.fromEntries(STATUS_OPTIONS.map((o) => [o.value, o.label]))

const BASIS_OPTIONS = [
  { label: '等同外包成本（默认）', value: 'outsource_equiv' },
  { label: '替代外部审计/咨询费', value: 'replace_audit_fee' },
  { label: '避免合规罚款', value: 'avoid_penalty' },
  { label: '节省工时折算', value: 'save_hours' },
  { label: '战略储备', value: 'strategic_reserve' },
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
    status: 'drafting',
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
      <el-select v-model="filter.kind" placeholder="项目类型" clearable style="width: 130px" @change="load">
        <el-option label="有收入" value="revenue" />
        <el-option label="无收入" value="no_revenue" />
      </el-select>
      <el-select v-model="filter.status_filter" placeholder="状态" clearable style="width: 130px" @change="load">
        <el-option v-for="o in STATUS_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="filter.need_party_id" placeholder="按需求方" clearable filterable style="width: 200px" @change="load">
        <el-option v-for="np in needParties" :key="np.id" :label="np.name" :value="np.id" />
      </el-select>
      <el-select v-model="filter.sales_person_id" placeholder="按销售人员" clearable filterable style="width: 180px" @change="load">
        <el-option v-for="sp in salesPersons" :key="sp.id" :label="sp.name" :value="sp.id" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增项目</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe highlight-current-row @row-click="openDetail">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="code" label="编号" width="100" />
      <el-table-column prop="name" label="项目名称" min-width="180" />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="row.kind === 'revenue' ? 'success' : 'warning'">
            {{ row.kind === 'revenue' ? '有收入' : '无收入' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><el-tag>{{ STATUS_LABEL[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="need_party_name" label="需求方" min-width="150" />
      <el-table-column label="销售" width="120">
        <template #default="{ row }">
          {{ row.sales_person_name }}
          <el-tag v-if="!row.sales_person_active" type="info" size="small">停用</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="外包估算" width="120">
        <template #default="{ row }">
          <span v-if="row.outsource_benchmark_amount">HK$ {{ row.outsource_benchmark_amount }}</span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column label="创造价值" width="120">
        <template #default="{ row }">
          <span v-if="row.value_created_computed" style="color: #e6a23c">HK$ {{ row.value_created_computed }}</span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="planned_end_date" label="计划完成" width="120" />
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
            勾选后：项目状态改为收尾或归档时，创造价值 = 外包服务商报价（计入驾驶舱降本）
          </span>
        </el-form-item>

        <el-form-item label="外部服务商报价">
          <el-input-number
            v-model="form.outsource_benchmark_amount" :min="0" :precision="2" style="width: 240px"
            placeholder="HK$"
          />
        </el-form-item>
        <el-form-item label="估算依据" v-if="form.outsource_benchmark_amount">
          <el-select v-model="form.benchmark_basis" clearable style="width: 100%" placeholder="选择依据，越靠前越可信">
            <el-option v-for="(label, code) in BENCHMARK_BASIS_LABELS" :key="code" :label="label" :value="code" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.benchmark_basis" label="依据说明">
          <el-input v-model="form.benchmark_basis_note" placeholder="如：参考 2024 同类项目 P-2024-005 / Gartner 报告链接" />
        </el-form-item>

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
