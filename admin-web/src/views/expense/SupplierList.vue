<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createSupplier, deleteSupplier, listSuppliers, updateSupplier,
  type Supplier, type SupplierPayload,
} from '@/api/suppliers'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const rows = ref<Supplier[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<SupplierPayload>>({
  name: '', category: '耗材', contact_person: '', contact_phone: '', contact_email: '',
  payment_terms: '月结30天', is_active: true, notes: '',
})

const CATEGORIES = ['耗材', '分包', '临时人力', '许可', '差旅', '综合']

async function load() {
  loading.value = true
  try { rows.value = await listSuppliers() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', category: '耗材', contact_person: '', contact_phone: '', contact_email: '', payment_terms: '月结30天', is_active: true, notes: '' })
  dialog.value = true
}

function openEdit(s: Supplier) {
  editingId.value = s.id
  Object.assign(form, s)
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('名称必填'); return }
  if (editingId.value === null) await createSupplier(form)
  else await updateSupplier(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(s: Supplier) {
  await ElMessageBox.confirm(`删除供应商 "${s.name}"？`, '提示', { type: 'warning' })
  await deleteSupplier(s.id)
  ElMessage.success('已删除')
  await load()
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '名称' },
  { key: 'category', label: '类别' },
  { key: 'contact_person', label: '联系人' },
  { key: 'contact_phone', label: '电话' },
  { key: 'payment_terms', label: '结算条件' },
  { key: 'is_active', label: '状态' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['name', 'category', 'contact_person', 'payment_terms', 'is_active']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: Supplier, key: string): string {
  if (key === 'is_active') return r.is_active ? '启用' : '停用'
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
        其他支出供应商（耗材 / 分包 / 临时人力 / 许可 / 差旅）。<strong>与 Vendor 区分</strong>——Vendor 是供人公司。
      </div>
      <div style="display: flex; gap: 8px">
        <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
        <el-button type="primary" @click="openCreate">新增供应商</el-button>
      </div>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('name')" label="名称" min-width="200">
        <template #header>
          名称
          <ColumnFilterMenu :options="distinctValues('name')" v-model="filters.name" :width="240" />
        </template>
        <template #default="{ row }">{{ row.name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('category')" label="类别" width="120">
        <template #header>
          类别
          <ColumnFilterMenu :options="distinctValues('category')" v-model="filters.category" />
        </template>
        <template #default="{ row }"><el-tag>{{ row.category || '—' }}</el-tag></template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('contact_person')" label="联系人" width="130">
        <template #header>
          联系人
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
      <el-table-column v-if="visibleCols.has('is_active')" label="状态" width="100">
        <template #header>
          状态
          <ColumnFilterMenu :options="distinctValues('is_active')" v-model="filters.is_active" />
        </template>
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增供应商' : '编辑供应商'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="c in CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.contact_email" /></el-form-item>
        <el-form-item label="结算条件"><el-input v-model="form.payment_terms" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
