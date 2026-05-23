<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createSkill, deleteSkill, listSkills, updateSkill, type Skill, type SkillPayload } from '@/api/skills'

const rows = ref<Skill[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<SkillPayload>>({
  name: '', category: '网络能力', description: '', is_active: true,
})

const grouped = computed(() => {
  const map: Record<string, Skill[]> = {}
  for (const s of rows.value) (map[s.category] ||= []).push(s)
  return map
})

async function load() {
  loading.value = true
  try { rows.value = await listSkills() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', category: '网络能力', description: '', is_active: true })
  dialog.value = true
}

function openEdit(s: Skill) {
  editingId.value = s.id
  Object.assign(form, s)
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('技能名必填'); return }
  if (editingId.value === null) await createSkill(form)
  else await updateSkill(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(s: Skill) {
  await ElMessageBox.confirm(`删除技能 "${s.name}"？`, '提示', { type: 'warning' })
  await deleteSkill(s.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
      <div style="color: #606266; font-size: 13px">
        能力矩阵管理 — 工程师档案中「技能清单」的选项来源
      </div>
      <el-button type="primary" @click="openCreate">新增技能</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="技能" width="180" />
      <el-table-column prop="category" label="分类" width="140">
        <template #default="{ row }"><el-tag>{{ row.category }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="description" label="说明" />
      <el-table-column prop="is_active" label="启用" width="80">
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

    <el-dialog v-model="dialog" :title="editingId === null ? '新增技能' : '编辑技能'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="网络能力" value="网络能力" />
            <el-option label="安全能力" value="安全能力" />
            <el-option label="弱电能力" value="弱电能力" />
            <el-option label="云能力" value="云能力" />
            <el-option label="数据能力" value="数据能力" />
            <el-option label="AI 能力" value="AI 能力" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
