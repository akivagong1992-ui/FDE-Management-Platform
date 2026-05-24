<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRevenue, deleteRevenue, listRevenues, updateRevenue,
  type ProjectRevenue, type RevenuePayload,
} from '@/api/projectRevenues'
import {
  listProjects, updateProject, BENCHMARK_BASIS_LABELS,
  type BenchmarkBasis, type Project,
} from '@/api/projects'

const rows = ref<ProjectRevenue[]>([])
const projects = ref<Project[]>([])
const revenueProjects = ref<Project[]>([])
const loading = ref(false)
const filter = reactive<{ project_id?: number }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<RevenuePayload>({
  project_id: 0, amount: 0, gross_amount: undefined, non_service_expense: undefined,
  recognized_date: new Date().toISOString().slice(0, 10),
  invoice_no: '', description: '',
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
    amount: 0, gross_amount: undefined, non_service_expense: undefined,
    recognized_date: new Date().toISOString().slice(0, 10),
    invoice_no: '', description: '',
  })
  syncBenchmarkFromProject(form.project_id)
  dialog.value = true
}

function openEdit(r: ProjectRevenue) {
  editingId.value = r.id
  Object.assign(form, {
    project_id: r.project_id,
    amount: Number(r.amount),
    gross_amount: r.gross_amount == null ? undefined : Number(r.gross_amount),
    non_service_expense: r.non_service_expense == null ? undefined : Number(r.non_service_expense),
    recognized_date: r.recognized_date, invoice_no: r.invoice_no || '',
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
  if (!form.gross_amount || Number(form.gross_amount) <= 0) {
    ElMessage.warning('客户付款总额 必填 — 公司毛利率统计需要此字段')
    return
  }
  if (!form.non_service_expense || Number(form.non_service_expense) <= 0) {
    ElMessage.warning('非服务开销 必填 — 公司毛利率公式需要此字段（占客户付款约 65-75%）')
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
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增收入记录</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="recognized_date" label="确认日期" width="120" sortable />
      <el-table-column prop="project_name" label="项目" min-width="160" />
      <el-table-column label="客户名称" min-width="140">
        <template #default="{ row }">{{ projectMeta(row.project_id).need_party }}</template>
      </el-table-column>
      <el-table-column label="销售" width="110">
        <template #default="{ row }">{{ projectMeta(row.project_id).sales_person }}</template>
      </el-table-column>
      <el-table-column label="客户付款总额" width="140" align="right">
        <template #default="{ row }">
          <span v-if="row.gross_amount != null">HK$ {{ row.gross_amount }}</span>
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column label="非服务开销" width="140" align="right">
        <template #default="{ row }">
          <span v-if="row.non_service_expense != null">HK$ {{ row.non_service_expense }}</span>
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column label="团队入账" width="140" align="right">
        <template #default="{ row }">HK$ {{ row.amount }}</template>
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
            通常占客户付款 65-75%；公司毛利率 = (客户付款 − 团队入账 − 非服务开销) / 客户付款
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
        <el-form-item label="发票号"><el-input v-model="form.invoice_no" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
