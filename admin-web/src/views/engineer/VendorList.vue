<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createVendor, deleteVendor, listVendors, updateVendor,
  type Vendor, type VendorPayload,
} from '@/api/vendors'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const rows = ref<Vendor[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<VendorPayload>>({
  name: '', short_name: '', contact_person: '', contact_phone: '', contact_email: '',
  payment_terms: '月结30天', cooperation_status: 'active', notes: '',
})

async function load() {
  loading.value = true
  try { rows.value = await listVendors() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '', short_name: '', contact_person: '', contact_phone: '', contact_email: '',
    payment_terms: '月结30天', cooperation_status: 'active', notes: '',
  })
  dialog.value = true
}

function openEdit(v: Vendor) {
  editingId.value = v.id
  Object.assign(form, v)
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('Vendor 名称必填'); return }
  if (editingId.value === null) await createVendor(form)
  else await updateVendor(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(v: Vendor) {
  await ElMessageBox.confirm(`确定删除 Vendor "${v.name}"？`, '提示', { type: 'warning' })
  await deleteVendor(v.id)
  ElMessage.success('已删除')
  await load()
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'name', label: '名称' },
  { key: 'short_name', label: '简称' },
  { key: 'contact_person', label: '对接人' },
  { key: 'contact_phone', label: '电话' },
  { key: 'payment_terms', label: '结算条件' },
  { key: 'cooperation_status', label: '状态' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['name', 'short_name', 'contact_person', 'payment_terms', 'cooperation_status']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: Vendor, key: string): string {
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
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
      <div style="color: #606266; font-size: 13px">
        Vendor = 与电信签项目服务合同的供人公司（PLAN §4.2）
      </div>
      <div style="display: flex; gap: 8px">
        <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
        <el-button type="primary" @click="openCreate">新增 Vendor</el-button>
      </div>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('name')" label="名称" min-width="180">
        <template #header>
          名称
          <ColumnFilterMenu :options="distinctValues('name')" v-model="filters.name" :width="240" />
        </template>
        <template #default="{ row }">{{ row.name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('short_name')" label="简称" width="110">
        <template #header>
          简称
          <ColumnFilterMenu :options="distinctValues('short_name')" v-model="filters.short_name" />
        </template>
        <template #default="{ row }">{{ row.short_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('contact_person')" label="对接人" width="110">
        <template #header>
          对接人
          <ColumnFilterMenu :options="distinctValues('contact_person')" v-model="filters.contact_person" />
        </template>
        <template #default="{ row }">{{ row.contact_person }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('contact_phone')" prop="contact_phone" label="电话" width="140" />
      <el-table-column v-if="visibleCols.has('payment_terms')" label="结算条件" width="130">
        <template #header>
          结算条件
          <ColumnFilterMenu :options="distinctValues('payment_terms')" v-model="filters.payment_terms" />
        </template>
        <template #default="{ row }">{{ row.payment_terms }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('cooperation_status')" label="状态" width="110">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('cooperation_status')" v-model="filters.cooperation_status" />
        </template>
        <template #default="{ row }">
          <el-tag :type="row.cooperation_status === 'active' ? 'success' : 'info'">
            {{ row.cooperation_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增 Vendor' : '编辑 Vendor'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="简称"><el-input v-model="form.short_name" /></el-form-item>
        <el-form-item label="对接人"><el-input v-model="form.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.contact_email" /></el-form-item>
        <el-form-item label="结算条件"><el-input v-model="form.payment_terms" /></el-form-item>
        <el-form-item label="合作状态">
          <el-select v-model="form.cooperation_status" style="width: 100%">
            <el-option label="合作中" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="已终止" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
