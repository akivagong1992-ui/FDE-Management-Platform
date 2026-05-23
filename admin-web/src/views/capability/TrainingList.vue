<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  createTraining, deleteTraining, listTrainings, updateTraining,
  type Training, type TrainingPayload,
} from '@/api/trainings'
import { listEngineers, type Engineer } from '@/api/engineers'

const auth = useAuthStore()
const canSeeCost = computed(() => ['lead', 'admin', 'finance'].includes(auth.role || ''))

const rows = ref<Training[]>([])
const engineers = ref<Engineer[]>([])
const loading = ref(false)
const filter = reactive<{ engineer_id?: number }>({})

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<TrainingPayload>({
  engineer_id: 0, course_name: '', provider: '', category: '内训',
  training_date: new Date().toISOString().slice(0, 10),
  hours: 8, cost: undefined, passed: true, notes: '',
})

async function load() {
  loading.value = true
  try {
    rows.value = await listTrainings(filter.engineer_id)
    if (engineers.value.length === 0) engineers.value = await listEngineers()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    engineer_id: engineers.value[0]?.id || 0,
    course_name: '', provider: '', category: '内训',
    training_date: new Date().toISOString().slice(0, 10),
    hours: 8, cost: undefined, passed: true, notes: '',
  })
  dialog.value = true
}

function openEdit(t: Training) {
  editingId.value = t.id
  Object.assign(form, {
    engineer_id: t.engineer_id,
    course_name: t.course_name, provider: t.provider || '', category: t.category || '内训',
    training_date: t.training_date, hours: Number(t.hours),
    cost: t.cost == null ? undefined : Number(t.cost),
    passed: t.passed, notes: t.notes || '',
  })
  dialog.value = true
}

async function onSubmit() {
  if (!form.engineer_id || !form.course_name) { ElMessage.warning('工程师 + 课程名必填'); return }
  if (editingId.value === null) await createTraining(form)
  else {
    const { engineer_id, ...rest } = form
    void engineer_id
    await updateTraining(editingId.value, rest)
  }
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(t: Training) {
  await ElMessageBox.confirm(`删除培训记录 #${t.id}？`, '提示', { type: 'warning' })
  await deleteTraining(t.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px">
      <el-select v-model="filter.engineer_id" placeholder="按工程师筛选" clearable filterable style="width: 220px" @change="load">
        <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
      </el-select>
      <div style="flex: 1" />
      <el-button type="primary" @click="openCreate">新增培训记录</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="training_date" label="日期" width="110" sortable />
      <el-table-column prop="engineer_name" label="工程师" width="100" />
      <el-table-column prop="course_name" label="课程" min-width="180" />
      <el-table-column prop="provider" label="机构 / 讲师" width="140" />
      <el-table-column prop="category" label="类别" width="80">
        <template #default="{ row }"><el-tag>{{ row.category || '—' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="学时" width="80">
        <template #default="{ row }">{{ row.hours }}h</template>
      </el-table-column>
      <el-table-column v-if="canSeeCost" label="费用" width="100">
        <template #default="{ row }">
          <span v-if="row.cost">HK$ {{ row.cost }}</span>
          <span v-else style="color: #909399">—</span>
        </template>
      </el-table-column>
      <el-table-column label="通过" width="80">
        <template #default="{ row }">
          <el-tag :type="row.passed ? 'success' : 'danger'">{{ row.passed ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增培训记录' : '编辑培训记录'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="工程师" required>
          <el-select v-model="form.engineer_id" :disabled="editingId !== null" filterable style="width: 100%">
            <el-option v-for="e in engineers" :key="e.id" :label="e.full_name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程名" required><el-input v-model="form.course_name" /></el-form-item>
        <el-form-item label="机构/讲师"><el-input v-model="form.provider" /></el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="内训" value="内训" />
            <el-option label="外训" value="外训" />
            <el-option label="在线" value="在线" />
            <el-option label="会议" value="会议" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="日期"><el-date-picker v-model="form.training_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学时"><el-input-number v-model="form.hours" :min="0.5" :max="200" :step="1" :precision="1" controls-position="right" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="canSeeCost" label="费用 (HKD)">
          <el-input-number v-model="form.cost" :min="0" :precision="2" controls-position="right" style="width: 220px" />
          <span style="margin-left: 8px; color: #909399; font-size: 12px">仅 lead/finance 可见</span>
        </el-form-item>
        <el-form-item label="通过"><el-switch v-model="form.passed" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
