<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createSalesPerson, deleteSalesPerson, listSalesPersons, updateSalesPerson,
  type SalesPerson, type SalesPersonPayload,
} from '@/api/salesPersons'

const rows = ref<SalesPerson[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<SalesPersonPayload>>({
  name: '', employee_id: '', department: '', email: '', mobile: '', is_active: true, notes: '',
})

async function load() {
  loading.value = true
  try { rows.value = await listSalesPersons() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', employee_id: '', department: '', email: '', mobile: '', is_active: true, notes: '' })
  dialog.value = true
}

function openEdit(sp: SalesPerson) {
  editingId.value = sp.id
  Object.assign(form, sp)
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('姓名必填'); return }
  if (editingId.value === null) await createSalesPerson(form)
  else await updateSalesPerson(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(sp: SalesPerson) {
  await ElMessageBox.confirm(
    `删除销售 "${sp.name}"？若仍有项目挂在他名下会被外键阻止；建议改用"停用"。`,
    '提示', { type: 'warning' },
  )
  await deleteSalesPerson(sp.id)
  ElMessage.success('已删除')
  await load()
}

async function onToggleActive(sp: SalesPerson) {
  await updateSalesPerson(sp.id, { is_active: !sp.is_active })
  ElMessage.success(sp.is_active ? '已停用（仍可被历史项目引用，新立项不可选）' : '已恢复')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
      <div style="color: #606266; font-size: 13px">
        销售人员 = 项目的销售归属（一项目一销售）。利润口径 B 的"按销售人员汇总"维度。
        <strong>离职处理：</strong>在项目详情点"转移销售"按钮把项目转给他人后，再把此人停用。
      </div>
      <el-button type="primary" @click="openCreate">新增销售人员</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="employee_id" label="工号" width="100" />
      <el-table-column prop="department" label="部门" width="140" />
      <el-table-column prop="mobile" label="手机" width="140" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '在岗' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="onToggleActive(row)">
            {{ row.is_active ? '停用' : '恢复' }}
          </el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增销售人员' : '编辑销售人员'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="工号"><el-input v-model="form.employee_id" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="form.mobile" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="在岗"><el-switch v-model="form.is_active" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
