<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createNeedParty, deleteNeedParty, listNeedParties, updateNeedParty,
  type NeedParty, type NeedPartyPayload,
} from '@/api/needParties'

const rows = ref<NeedParty[]>([])
const loading = ref(false)
const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<Partial<NeedPartyPayload>>({
  name: '', party_type: 'external_company', contact_person: '', contact_phone: '', contact_email: '', notes: '',
})

async function load() {
  loading.value = true
  try { rows.value = await listNeedParties() } finally { loading.value = false }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', party_type: 'external_company', contact_person: '', contact_phone: '', contact_email: '', notes: '' })
  dialog.value = true
}

function openEdit(np: NeedParty) {
  editingId.value = np.id
  Object.assign(form, np)
  dialog.value = true
}

async function onSubmit() {
  if (!form.name) { ElMessage.warning('名称必填'); return }
  if (editingId.value === null) await createNeedParty(form)
  else await updateNeedParty(editingId.value, form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

async function onDelete(np: NeedParty) {
  await ElMessageBox.confirm(`删除需求方 "${np.name}"？`, '提示', { type: 'warning' })
  await deleteNeedParty(np.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 12px">
      <el-button type="primary" @click="openCreate">新增客户</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="200" />
      <el-table-column prop="party_type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.party_type === 'internal_dept' ? 'success' : 'warning'">
            {{ row.party_type === 'internal_dept' ? '内部部门' : '外部合同方' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="contact_person" label="联系人" width="120" />
      <el-table-column prop="contact_phone" label="电话" width="140" />
      <el-table-column prop="contact_email" label="邮箱" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editingId === null ? '新增客户' : '编辑客户'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.party_type" style="width: 100%">
            <el-option label="电信集团内部部门" value="internal_dept" />
            <el-option label="外部合同方" value="external_company" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.contact_email" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
