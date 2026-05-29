<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  createEngineer, deleteEngineer, listEngineers, updateEngineer,
  type Engineer, type EngineerPayload,
} from '@/api/engineers'
import { listVendors, type Vendor } from '@/api/vendors'
import { listSkills, type Skill } from '@/api/skills'
import EngineerDrawer from './EngineerDrawer.vue'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const auth = useAuthStore()
const isLead = computed(() => auth.role === 'lead' || auth.role === 'admin' || auth.role === 'finance')

const rows = ref<Engineer[]>([])
const vendors = ref<Vendor[]>([])
const skills = ref<Skill[]>([])
const loading = ref(false)
const filter = reactive<{ vendor_id?: number; status_filter?: string }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<EngineerPayload>({
  vendor_id: 0,
  employment_form: 'vendor_via_labor',
  labor_company: '',
  full_name: '',
  english_name: '',
  gender: '',
  mobile: '',
  email: '',
  id_doc_type: 'HKID',
  id_doc_number: '',
  status: 'active',
  monthly_cost_to_telecom: undefined,
  initial_skill_ids: [],
})

const drawerOpen = ref(false)
const drawerId = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    rows.value = await listEngineers(filter)
    if (vendors.value.length === 0) vendors.value = await listVendors()
    if (skills.value.length === 0) skills.value = await listSkills()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    vendor_id: vendors.value[0]?.id || 0,
    employment_form: 'vendor_via_labor',
    labor_company: '', full_name: '', english_name: '', gender: '', mobile: '', email: '',
    id_doc_type: 'HKID', id_doc_number: '',
    status: 'active',
    monthly_cost_to_telecom: undefined,
    initial_skill_ids: [],
  })
  dialog.value = true
}

function openEdit(e: Engineer) {
  editingId.value = e.id
  Object.assign(form, {
    vendor_id: e.vendor_id,
    employment_form: e.employment_form,
    labor_company: e.labor_company || '',
    full_name: e.full_name,
    english_name: e.english_name || '',
    gender: e.gender || '',
    mobile: e.mobile || '',
    email: e.email || '',
    id_doc_type: e.id_doc_type || 'HKID',
    id_doc_number: '',  // never preload; user types if they want to update
    status: e.status,
    entry_date: e.entry_date || undefined,
    exit_date: e.exit_date || undefined,
    monthly_cost_to_telecom: e.monthly_cost_to_telecom == null ? undefined : Number(e.monthly_cost_to_telecom),
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.vendor_id || !form.full_name) {
    ElMessage.warning('Vendor + 姓名必填')
    return
  }
  if (form.employment_form === 'vendor_via_labor' && !form.labor_company) {
    ElMessage.warning('vendor_via_labor 需填写劳务公司')
    return
  }
  const payload: any = { ...form }
  if (!payload.id_doc_number) delete payload.id_doc_number  // don't overwrite to empty
  if (editingId.value === null) await createEngineer(payload)
  else await updateEngineer(editingId.value, payload)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(e: Engineer) {
  await ElMessageBox.confirm(`删除工程师 "${e.full_name}"？`, '提示', { type: 'warning' })
  await deleteEngineer(e.id)
  ElMessage.success('已删除')
  await load()
}

function openDetail(e: Engineer) {
  drawerId.value = e.id
  drawerOpen.value = true
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'full_name', label: '姓名' },
  { key: 'employment_form', label: '签约' },
  { key: 'vendor_name', label: 'Vendor' },
  { key: 'labor_company', label: '劳务公司' },
  { key: 'status', label: '状态' },
  { key: 'id_doc_number_masked', label: '证件号(脱敏)' },
  { key: 'monthly_cost_to_telecom', label: '月服务费' },
  { key: 'mobile', label: '手机' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['full_name', 'employment_form', 'vendor_name', 'labor_company', 'status']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: Engineer, key: string): string {
  switch (key) {
    case 'employment_form': return r.employment_form === 'vendor_direct' ? 'Vendor 直签' : 'Vendor + 劳务'
    case 'status': return r.status === 'active' ? '在职' : '已离职'
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
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px">
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button type="primary" @click="openCreate">新增工程师</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe @row-click="openDetail" highlight-current-row>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('full_name')" label="姓名" width="120">
        <template #header>
          姓名
          <ColumnFilterMenu :options="distinctValues('full_name')" v-model="filters.full_name" />
        </template>
        <template #default="{ row }">{{ row.full_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('employment_form')" label="签约" width="130">
        <template #header>
          签约
          <ColumnFilterMenu :options="distinctValues('employment_form')" v-model="filters.employment_form" />
        </template>
        <template #default="{ row }">
          <el-tag size="small">{{ row.employment_form === 'vendor_direct' ? 'Vendor 直签' : 'Vendor + 劳务' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('vendor_name')" label="Vendor" min-width="150">
        <template #header>
          Vendor
          <ColumnFilterMenu :options="distinctValues('vendor_name')" v-model="filters.vendor_name" :width="240" />
        </template>
        <template #default="{ row }">{{ row.vendor_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('labor_company')" label="劳务公司" min-width="160">
        <template #header>
          劳务公司
          <ColumnFilterMenu :options="distinctValues('labor_company')" v-model="filters.labor_company" :width="240" />
        </template>
        <template #default="{ row }">{{ row.labor_company }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('status')" label="状态" width="100">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('status')" v-model="filters.status" />
        </template>
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
            {{ row.status === 'active' ? '在职' : '已离职' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('id_doc_number_masked')" prop="id_doc_number_masked" label="证件号(脱敏)" width="130" />
      <el-table-column v-if="isLead && visibleCols.has('monthly_cost_to_telecom')" label="月服务费" width="110">
        <template #default="{ row }">
          <span v-if="row.monthly_cost_to_telecom">HK$ {{ row.monthly_cost_to_telecom }}</span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('mobile')" prop="mobile" label="手机" width="140" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click.stop="openDetail(row)">详情</el-button>
          <el-button link size="small" @click.stop="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click.stop="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增工程师' : '编辑工程师'" width="720px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="Vendor" required>
              <el-select v-model="form.vendor_id" style="width: 100%" placeholder="选择 Vendor">
                <el-option v-for="v in vendors" :key="v.id" :label="v.name" :value="v.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="签约形态" required>
              <el-select v-model="form.employment_form" style="width: 100%">
                <el-option label="Vendor 直签" value="vendor_direct" />
                <el-option label="Vendor 通过劳务公司" value="vendor_via_labor" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="form.employment_form === 'vendor_via_labor'" label="劳务公司" required>
          <el-input v-model="form.labor_company" placeholder="例如：香港人力中介有限公司" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="姓名" required><el-input v-model="form.full_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="英文名"><el-input v-model="form.english_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机"><el-input v-model="form.mobile" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item></el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="证件类型">
              <el-select v-model="form.id_doc_type" style="width: 100%">
                <el-option label="香港身份证 HKID" value="HKID" />
                <el-option label="护照 Passport" value="passport" />
                <el-option label="内地身份证" value="mainland_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="证件号">
              <el-input v-model="form.id_doc_number" :placeholder="editingId === null ? '将加密存储' : '留空表示不修改'" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 220px">
            <el-option label="在职" value="active" />
            <el-option label="已离职" value="departed" />
          </el-select>
        </el-form-item>

        <!-- 仅新增时显示技能等级初选；编辑后续在抽屉里维护 -->
        <el-form-item v-if="editingId === null" label="技能等级">
          <el-select
            v-model="form.initial_skill_ids" multiple filterable
            collapse-tags collapse-tags-tooltip
            placeholder="从能力矩阵中勾选（可空，后续在工程师详情抽屉补充）"
            style="width: 100%"
          >
            <el-option
              v-for="s in skills" :key="s.id"
              :label="`[${s.category}] ${s.name}${s.level ? ' · ' + s.level : ''}${s.issuer ? ' — ' + s.issuer : ''}`"
              :value="s.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            来自「派单工时管理 → 能力矩阵管理」。每条 = 认证名称 + 厂商 + 等级（L1-L3）
          </div>
        </el-form-item>

        <el-form-item v-if="isLead" label="月服务费">
          <el-input-number v-model="form.monthly_cost_to_telecom" :min="0" :precision="2" style="width: 240px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <EngineerDrawer v-model="drawerOpen" :engineer-id="drawerId" />
  </div>
</template>
