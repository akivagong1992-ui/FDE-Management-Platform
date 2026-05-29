<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAsset, deleteAsset, getAsset, listAssets, updateAsset,
  type Confidentiality, type KnowledgeAsset, type KnowledgeAssetPayload,
} from '@/api/knowledgeAssets'
import {
  createReference, deleteReference, listReferences,
  type AssetReference,
} from '@/api/assetReferences'
import { listProjects, type Project } from '@/api/projects'
import { listDict, type DictItem } from '@/api/dataDict'
import ColumnVisibilityMenu from '@/components/ColumnVisibilityMenu.vue'
import ColumnFilterMenu from '@/components/ColumnFilterMenu.vue'

const rows = ref<KnowledgeAsset[]>([])
const projects = ref<Project[]>([])
const categories = ref<DictItem[]>([])
const loading = ref(false)
const filter = reactive<{ category?: string; project_id?: number; keyword?: string }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<KnowledgeAssetPayload>({
  project_id: null, category: 'design_doc', title: '', summary: '', content: '',
  external_url: '', file_path: '', tags: '', confidentiality: 'internal',
})

const detailOpen = ref(false)
const detail = ref<KnowledgeAsset | null>(null)

const CONF_LABEL: Record<Confidentiality, string> = {
  public: '公开', internal: '内部', confidential: '机密',
}
const CONF_TYPE: Record<Confidentiality, string> = {
  public: 'success', internal: 'info', confidential: 'danger',
}

const TAG_LIST = computed(() => (rows.value || []).flatMap((a) => (a.tags || '').split(',').map((t) => t.trim()).filter(Boolean)))
const UNIQUE_TAGS = computed(() => Array.from(new Set(TAG_LIST.value)))

async function load() {
  loading.value = true
  try {
    rows.value = await listAssets(filter)
    if (projects.value.length === 0) projects.value = await listProjects()
    if (categories.value.length === 0) categories.value = await listDict('asset_category')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    project_id: null, category: 'design_doc', title: '', summary: '', content: '',
    external_url: '', file_path: '', tags: '', confidentiality: 'internal',
  })
  dialog.value = true
}

function openEdit(a: KnowledgeAsset) {
  editingId.value = a.id
  Object.assign(form, {
    project_id: a.project_id, category: a.category, title: a.title,
    summary: a.summary || '', content: a.content || '',
    external_url: a.external_url || '', file_path: a.file_path || '',
    tags: a.tags || '', confidentiality: a.confidentiality,
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.title || !form.category) {
    ElMessage.warning('标题 + 分类必填')
    return
  }
  if (editingId.value === null) await createAsset(form)
  else await updateAsset(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(a: KnowledgeAsset) {
  await ElMessageBox.confirm(`删除知识资产 "${a.title}"？`, '提示', { type: 'warning' })
  await deleteAsset(a.id)
  ElMessage.success('已删除')
  await load()
}

const refs = ref<AssetReference[]>([])
const refForm = reactive<{ project_id: number | null; estimated_hours_saved: number | null; notes: string }>({
  project_id: null, estimated_hours_saved: 8, notes: '',
})

async function openDetail(a: KnowledgeAsset) {
  detail.value = await getAsset(a.id)
  refs.value = await listReferences(a.id)
  refForm.project_id = projects.value[0]?.id || null
  refForm.estimated_hours_saved = 8
  refForm.notes = ''
  detailOpen.value = true
}

async function onAddRef() {
  if (!detail.value || !refForm.project_id) {
    ElMessage.warning('请选择项目'); return
  }
  await createReference(detail.value.id, {
    project_id: refForm.project_id,
    estimated_hours_saved: refForm.estimated_hours_saved ?? undefined,
    notes: refForm.notes || undefined,
  })
  refs.value = await listReferences(detail.value.id)
  ElMessage.success('已添加引用')
}

async function onDelRef(r: AssetReference) {
  if (!detail.value) return
  await ElMessageBox.confirm(`删除引用记录 #${r.id}？`, '提示', { type: 'warning' })
  await deleteReference(detail.value.id, r.id)
  refs.value = await listReferences(detail.value.id)
}

// ─ Column visibility + per-column filter ─────────────────────────
const COL_DEFS = [
  { key: 'category', label: '分类' },
  { key: 'title', label: '标题' },
  { key: 'project_name', label: '来源项目' },
  { key: 'tags', label: '标签' },
  { key: 'confidentiality', label: '保密' },
  { key: 'created_at', label: '创建时间' },
]
const visibleCols = ref<Set<string>>(new Set(COL_DEFS.map((c) => c.key)))
const FILTERABLE_KEYS = ['category', 'title', 'project_name', 'confidentiality']
const filters = ref<Record<string, Set<string | number>>>(
  Object.fromEntries(FILTERABLE_KEYS.map((k) => [k, new Set()])),
)
function cellText(r: KnowledgeAsset, key: string): string {
  switch (key) {
    case 'category': return r.category_label || r.category || ''
    case 'confidentiality': return CONF_LABEL[r.confidentiality as Confidentiality] || r.confidentiality
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
  <el-card>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap">
      <el-input
        v-model="filter.keyword" placeholder="关键词搜索（标题/摘要/标签）"
        clearable style="width: 280px" @change="load" @clear="load"
      />
      <div style="flex: 1" />
      <ColumnVisibilityMenu :columns="COL_DEFS" v-model="visibleCols" />
      <el-button type="primary" @click="openCreate">新增知识资产</el-button>
    </div>

    <el-table :data="filteredRows" v-loading="loading" stripe highlight-current-row @row-click="openDetail">
      <el-table-column v-if="visibleCols.has('id')" prop="id" label="ID" width="60" />
      <el-table-column v-if="visibleCols.has('category')" label="分类" width="160">
        <template #header>
          分类
          <ColumnFilterMenu :options="distinctValues('category')" v-model="filters.category" />
        </template>
        <template #default="{ row }">
          <el-tag>{{ row.category_label || row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('title')" label="标题" min-width="240">
        <template #header>
          标题
          <ColumnFilterMenu :options="distinctValues('title')" v-model="filters.title" :width="320" />
        </template>
        <template #default="{ row }">{{ row.title }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('project_name')" label="来源项目" width="180">
        <template #header>
          来源项目
          <ColumnFilterMenu :options="distinctValues('project_name')" v-model="filters.project_name" :width="260" />
        </template>
        <template #default="{ row }">{{ row.project_name }}</template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('tags')" label="标签" width="200">
        <template #default="{ row }">
          <span v-if="row.tags">
            <el-tag v-for="t in row.tags.split(',').map((s: string) => s.trim()).filter(Boolean)"
                    :key="t" size="small" effect="plain" style="margin-right: 4px">
              {{ t }}
            </el-tag>
          </span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('confidentiality')" label="保密" width="110">
        <template #header>
          保密
          <ColumnFilterMenu :options="distinctValues('confidentiality')" v-model="filters.confidentiality" />
        </template>
        <template #default="{ row }">
          <el-tag :type="CONF_TYPE[row.confidentiality as Confidentiality] as any">
            {{ CONF_LABEL[row.confidentiality as Confidentiality] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="visibleCols.has('created_at')" prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click.stop="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click.stop="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create / edit -->
    <el-dialog v-model="dialog" :title="editingId === null ? '新增知识资产' : '编辑知识资产'" width="720px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="14"><el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item></el-col>
          <el-col :span="10">
            <el-form-item label="分类" required>
              <el-select v-model="form.category" style="width: 100%">
                <el-option v-for="c in categories" :key="c.code" :label="c.label" :value="c.code" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="来源项目">
              <el-select v-model="form.project_id" clearable filterable placeholder="可选" style="width: 100%">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="保密级别">
              <el-select v-model="form.confidentiality" style="width: 100%">
                <el-option label="公开（所有人可见）" value="public" />
                <el-option label="内部（默认；登录用户可见）" value="internal" />
                <el-option label="机密（仅 admin / lead / pm / finance 可见）" value="confidential" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="摘要"><el-input v-model="form.summary" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="逗号分隔，如：5G,拓扑,基站" />
        </el-form-item>
        <el-form-item label="外部链接">
          <el-input v-model="form.external_url" placeholder="如 Confluence / Git / 内网链接" />
        </el-form-item>
        <el-form-item label="正文（可选）">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="支持 Markdown / 纯文本" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- Detail drawer -->
    <el-drawer v-model="detailOpen" direction="rtl" size="640px" :title="detail ? detail.title : '加载中…'">
      <div v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="分类">{{ detail.category_label || detail.category }}</el-descriptions-item>
          <el-descriptions-item label="保密">
            <el-tag :type="CONF_TYPE[detail.confidentiality] as any">
              {{ CONF_LABEL[detail.confidentiality] }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源项目" :span="2">{{ detail.project_name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">{{ detail.tags || '—' }}</el-descriptions-item>
          <el-descriptions-item label="外链" :span="2">
            <a v-if="detail.external_url" :href="detail.external_url" target="_blank">{{ detail.external_url }}</a>
            <span v-else style="color: #909399">—</span>
          </el-descriptions-item>
          <el-descriptions-item label="附件" :span="2">{{ detail.file_path || '—' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="detail.summary" style="margin-top: 16px">
          <div style="font-weight: 600; margin-bottom: 8px">摘要</div>
          <div style="color: #606266">{{ detail.summary }}</div>
        </div>

        <div v-if="detail.content" style="margin-top: 16px">
          <div style="font-weight: 600; margin-bottom: 8px">正文</div>
          <pre style="white-space: pre-wrap; word-break: break-all; background: #f7f9fc; padding: 12px; border-radius: 4px">{{ detail.content }}</pre>
        </div>

        <!-- 复用记录 -->
        <div style="margin-top: 24px">
          <div style="font-weight: 600; margin-bottom: 8px">
            复用记录
            <el-tag size="small" type="success" style="margin-left: 8px">{{ refs.length }} 次</el-tag>
            <el-tag size="small" type="info" v-if="refs.length > 0" style="margin-left: 4px">
              累计节省 {{ refs.reduce((s, r) => s + Number(r.estimated_hours_saved || 0), 0) }} 工时
            </el-tag>
          </div>
          <el-table :data="refs" size="small" v-if="refs.length > 0">
            <el-table-column prop="project_name" label="项目" min-width="160" />
            <el-table-column label="节省工时" width="90">
              <template #default="{ row }">{{ row.estimated_hours_saved || '—' }}</template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" />
            <el-table-column label="操作" width="70">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="onDelRef(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else :image-size="60" description="还没复用记录" />

          <div style="display: grid; grid-template-columns: 1.5fr 100px 1fr auto; gap: 8px; margin-top: 12px">
            <el-select v-model="refForm.project_id" filterable placeholder="选项目">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <el-input-number v-model="refForm.estimated_hours_saved" :min="0" :max="10000"
                             :step="4" :precision="1" controls-position="right" placeholder="节省工时" />
            <el-input v-model="refForm.notes" placeholder="备注（可选）" />
            <el-button type="primary" @click="onAddRef">添加</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- Unique tag cloud (lightweight) -->
    <el-card v-if="UNIQUE_TAGS.length > 0" shadow="never" style="margin-top: 16px">
      <template #header>已有标签</template>
      <el-tag
        v-for="t in UNIQUE_TAGS" :key="t" size="small" effect="plain"
        style="margin-right: 6px; margin-bottom: 6px; cursor: pointer"
        @click="filter.keyword = t; load()"
      >{{ t }}</el-tag>
    </el-card>
  </el-card>
</template>
