<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  bulkImportSkills, createSkill, deleteSkill, listSkills, updateSkill,
  type Skill, type SkillBulkItem, type SkillLevel, type SkillPayload,
} from '@/api/skills'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const CATEGORIES = ['网络能力', '安全能力', '弱电能力', '云能力', '数据能力', 'AI 能力']
const LEVELS: SkillLevel[] = ['L1', 'L2', 'L3']

const rows = ref<Skill[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<SkillPayload>>({
  name: '', category: '网络能力', issuer: '', level: null, is_active: true,
})

// 批量导入 dialog
const importDialog = ref(false)
const importForm = reactive<{ category: string; raw: string }>({ category: '网络能力', raw: '' })
const importing = ref(false)

async function load() {
  loading.value = true
  try { rows.value = await listSkills() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', category: '网络能力', issuer: '', level: null, is_active: true })
  dialog.value = true
}

function openEdit(s: Skill) {
  editingId.value = s.id
  Object.assign(form, {
    name: s.name, category: s.category,
    issuer: s.issuer || '', level: s.level || null,
    is_active: s.is_active,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('认证名称必填'); return }
  if (editingId.value === null) await createSkill(form)
  else await updateSkill(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(s: Skill) {
  await ElMessageBox.confirm(`删除认证 "${s.name}"？`, '提示', { type: 'warning' })
  await deleteSkill(s.id)
  ElMessage.success('已删除')
  await load()
}

function openImport() {
  importForm.category = '网络能力'
  importForm.raw = '华为, HCIE-WLAN, L3\nCisco, CCIE 安全, L3'
  importDialog.value = true
}

async function onSubmitImport() {
  const lines = importForm.raw.split('\n').map((l) => l.trim()).filter(Boolean)
  const items: SkillBulkItem[] = []
  const errors: string[] = []
  for (const line of lines) {
    const parts = line.split(/[,，\t]/).map((p) => p.trim())
    if (parts.length < 3) { errors.push(`不足 3 列: ${line}`); continue }
    const [issuer, name, level] = parts
    if (!['L1', 'L2', 'L3'].includes(level)) { errors.push(`等级非法: ${line}`); continue }
    items.push({ issuer, name, level: level as SkillLevel })
  }
  if (errors.length) { ElMessage.warning(`${errors.length} 行有问题，已跳过`); console.warn(errors) }
  if (!items.length) { ElMessage.warning('没有有效行可导入'); return }
  importing.value = true
  try {
    const r = await bulkImportSkills({ category: importForm.category, items })
    ElMessage.success(`成功导入 ${r.created} 条${r.skipped > 0 ? `，重名跳过 ${r.skipped} 条` : ''}`)
    importDialog.value = false
    await load()
  } finally { importing.value = false }
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '认证名称' },
  { key: 'category', label: '分类' },
  { key: 'issuer', label: '厂商' },
  { key: 'level', label: '等级' },
  { key: 'is_active', label: '启用' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['name', 'category', 'issuer', 'level', 'is_active']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: Skill, key: string): string {
  if (key === 'is_active') return r.is_active ? '是' : '否'
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
        技能 / 认证目录 — 每条 = 认证名称 + 分类 + 厂商 + 等级；工程师挂技能即引用此处
      </div>
      <div style="display: flex; gap: 8px">
        <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
        <el-button @click="openImport">批量导入</el-button>
        <el-button type="primary" @click="openCreate">新增认证</el-button>
      </div>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe>
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('name')" label="认证名称" min-width="220">
        <template #header>
          认证名称
          <ColumnFilterMenu :options="distinctValues('name')" v-model="filters.name" :width="280" />
        </template>
        <template #default="{ row }">{{ row.name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('category')" label="分类" width="140">
        <template #header>
          分类
          <ColumnFilterMenu :options="distinctValues('category')" v-model="filters.category" />
        </template>
        <template #default="{ row }"><el-tag>{{ row.category }}</el-tag></template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('issuer')" label="厂商" width="140">
        <template #header>
          厂商
          <ColumnFilterMenu :options="distinctValues('issuer')" v-model="filters.issuer" />
        </template>
        <template #default="{ row }">{{ row.issuer || '—' }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('level')" label="等级" width="100">
        <template #header>
          等级
          <ColumnFilterMenu :options="distinctValues('level')" v-model="filters.level" />
        </template>
        <template #default="{ row }">
          <el-tag v-if="row.level" size="small"
                  :type="row.level === 'L3' ? 'success' : row.level === 'L2' ? 'warning' : 'info'">
            {{ row.level }}
          </el-tag>
          <span v-else style="color: #c0c4cc">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('is_active')" label="启用" width="100">
        <template #header>
          启用
          <ColumnFilterMenu :options="distinctValues('is_active')" v-model="filters.is_active" />
        </template>
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 单个新增/编辑 -->
    <el-dialog v-model="dialog" :title="editingId === null ? '新增认证' : '编辑认证'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="认证名称" required>
          <el-input v-model="form.name" placeholder="如 CCIE 路由交换 / HCIE-WLAN" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="c in CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="厂商">
          <el-input v-model="form.issuer" placeholder="如 Cisco / 华为 / CNCF" />
        </el-form-item>
        <el-form-item label="等级">
          <el-select v-model="form.level" clearable style="width: 100%" placeholder="选 L1 / L2 / L3">
            <el-option v-for="l in LEVELS" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="importDialog" title="批量导入认证目录" width="640px">
      <el-form label-width="100px">
        <el-form-item label="分类">
          <el-select v-model="importForm.category" style="width: 100%">
            <el-option v-for="c in CATEGORIES" :key="c" :label="c" :value="c" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            此批所有认证共用该分类
          </div>
        </el-form-item>
        <el-form-item label="数据">
          <el-input
            v-model="importForm.raw" type="textarea" :rows="10"
            placeholder="每行一条，逗号分隔 3 列：厂商, 认证名称, 等级&#10;例：&#10;华为, HCIE-WLAN, L3&#10;Cisco, CCIE 安全, L3&#10;CNCF, CKA, L2"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            等级仅支持 L1 / L2 / L3；重名（与已有认证 name 相同）将自动跳过
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="onSubmitImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>
