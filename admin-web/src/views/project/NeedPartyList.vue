<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CLIENT_TYPES,
  createNeedParty, deleteNeedParty, listNeedParties, updateNeedParty, uploadFile,
  type NeedParty, type NeedPartyPayload,
} from '@/api/needParties'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const rows = ref<NeedParty[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const blankForm = (): Partial<NeedPartyPayload> => ({
  name: '', party_type: '外资企业',
  contact_person: '', contact_phone: '', contact_email: '', notes: '',
  show_in_cockpit: false, logo_path: null,
})
const form = reactive<Partial<NeedPartyPayload>>(blankForm())
const uploading = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

async function load() {
  loading.value = true
  try { rows.value = await listNeedParties() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, blankForm())
  dialog.value = true
}

function openEdit(np: NeedParty) {
  editingId.value = np.id
  Object.assign(form, blankForm(), np)
  dialog.value = true
}

async function onUploadLogo(rawFile: File) {
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.warning('请上传图片文件 (PNG / JPG / SVG)')
    return
  }
  uploading.value = true
  try {
    const { saved_path } = await uploadFile(rawFile)
    form.logo_path = saved_path
    ElMessage.success('Logo 已上传')
  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
  }
}

function triggerFilePicker() {
  fileInputRef.value?.click()
}

function onLogoChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) onUploadLogo(file)
  input.value = ''
}

async function onToggleShow(np: NeedParty, val: string | number | boolean) {
  const flag = Boolean(val)
  if (flag && !np.logo_path) {
    ElMessage.warning('请先打开编辑、上传 Logo 后再开启展示')
    return
  }
  await updateNeedParty(np.id, { show_in_cockpit: flag })
  ElMessage.success(flag ? '已开启驾驶舱展示' : '已关闭')
  await load()
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('名称必填'); return }
  if (form.show_in_cockpit && !form.logo_path) {
    ElMessage.warning('开启「驾驶舱展示」需先上传 Logo')
    return
  }
  // 空字符串归一为 null（后端 EmailStr 不接受 ""）
  const payload: Partial<NeedPartyPayload> = { ...form }
  for (const k of ['contact_person', 'contact_phone', 'contact_email', 'notes'] as const) {
    if (payload[k] === '') payload[k] = null
  }
  if (editingId.value === null) await createNeedParty(payload)
  else await updateNeedParty(editingId.value, payload)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(np: NeedParty) {
  await ElMessageBox.confirm(`删除客户 "${np.name}"？`, '提示', { type: 'warning' })
  await deleteNeedParty(np.id)
  ElMessage.success('已删除')
  await load()
}

const logoUrl = (path?: string | null) => (path ? `/api/uploads/${path}` : '')

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'id', label: 'ID' },
  { key: 'logo_path', label: 'Logo' },
  { key: 'name', label: '名称' },
  { key: 'party_type', label: '类型' },
  { key: 'show_in_cockpit', label: '驾驶舱展示' },
  { key: 'contact_person', label: '联系人' },
  { key: 'contact_phone', label: '电话' },
  { key: 'contact_email', label: '邮箱' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['name', 'party_type', 'contact_person']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: NeedParty, key: string): string {
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
    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-bottom: 12px">
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button type="primary" @click="openCreate">新增客户</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('logo_path')" label="Logo" width="80">
        <template #default="{ row }">
          <el-image
            v-if="row.logo_path"
            :src="logoUrl(row.logo_path)"
            style="width: 48px; height: 48px; object-fit: contain"
            fit="contain"
          />
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('name')" label="名称" min-width="200">
        <template #header>
          名称
          <ColumnFilterMenu :options="distinctValues('name')" v-model="filters.name" :width="240" />
        </template>
        <template #default="{ row }">{{ row.name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('party_type')" label="类型" width="130">
        <template #header>
          类型
          <ColumnFilterMenu :options="distinctValues('party_type')" v-model="filters.party_type" />
        </template>
        <template #default="{ row }">
          <el-tag type="info">{{ row.party_type || '—' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('show_in_cockpit')" label="驾驶舱展示" width="120">
        <template #default="{ row }">
          <el-switch
            :model-value="row.show_in_cockpit"
            :disabled="!row.logo_path"
            @change="(v) => onToggleShow(row, v)"
          />
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('contact_person')" label="联系人" width="110">
        <template #header>
          联系人
          <ColumnFilterMenu :options="distinctValues('contact_person')" v-model="filters.contact_person" />
        </template>
        <template #default="{ row }">{{ row.contact_person }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('contact_phone')" prop="contact_phone" label="电话" width="130" />
      <el-table-column v-if="visibleCols.has('contact_email')" prop="contact_email" label="邮箱" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增客户' : '编辑客户'" width="560px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.party_type" style="width: 100%" filterable allow-create default-first-option>
            <el-option v-for="t in CLIENT_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.contact_email" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>

        <el-form-item label="客户 Logo">
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
            <el-image
              v-if="form.logo_path"
              :src="logoUrl(form.logo_path)"
              style="width: 80px; height: 80px; border: 1px solid #e4e7ed; border-radius: 8px; object-fit: contain; background: #fafafa"
              fit="contain"
            />
            <span v-else style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; border: 1px dashed #dcdfe6; border-radius: 8px; color: #c0c4cc">无</span>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              style="display: none"
              @change="onLogoChange"
            />
            <el-button :loading="uploading" type="primary" plain @click="triggerFilePicker">
              {{ form.logo_path ? '更换 Logo' : '上传 Logo' }}
            </el-button>
            <el-button v-if="form.logo_path" link type="danger" @click="form.logo_path = null">移除</el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            支持 PNG / JPG / SVG，建议 200×200 以上，背景透明
          </div>
        </el-form-item>

        <el-form-item label="驾驶舱展示">
          <el-switch v-model="form.show_in_cockpit" :disabled="!form.logo_path" />
          <span style="margin-left: 12px; color: #909399; font-size: 12px">
            开启后此客户名 + Logo 会出现在驾驶舱总览「已交付客户」区
            <template v-if="!form.logo_path">（需先上传 Logo）</template>
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

