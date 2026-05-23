<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser, type User, type UserPayload } from '@/api/users'

const users = ref<User[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<UserPayload>({
  username: '',
  password: '',
  full_name: '',
  email: '',
  role: 'pm',
  is_active: true,
})

async function load() {
  loading.value = true
  try {
    users.value = await listUsers()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { username: '', password: '', full_name: '', email: '', role: 'pm', is_active: true })
  dialogVisible.value = true
}

function openEdit(u: User) {
  editingId.value = u.id
  Object.assign(form, {
    username: u.username,
    password: '',
    full_name: u.full_name || '',
    email: u.email || '',
    role: u.role,
    is_active: u.is_active,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  if (editingId.value === null) {
    await createUser(form)
    ElMessage.success('已创建')
  } else {
    const payload: Partial<UserPayload> = { ...form }
    if (!payload.password) delete payload.password
    await updateUser(editingId.value, payload)
    ElMessage.success('已更新')
  }
  dialogVisible.value = false
  await load()
}

async function onDelete(u: User) {
  await ElMessageBox.confirm(`确定删除用户 ${u.username}？`, '提示', { type: 'warning' })
  await deleteUser(u.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span>用户管理</span>
        <el-button type="primary" @click="openCreate">新增用户</el-button>
      </div>
    </template>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="full_name" label="姓名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag>{{ row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '是' : '否' }}
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

    <el-dialog v-model="dialogVisible" :title="editingId === null ? '新增用户' : '编辑用户'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="editingId !== null" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="团队负责人 (lead)" value="lead" />
            <el-option label="项目经理 (pm)" value="pm" />
            <el-option label="财务 (finance)" value="finance" />
            <el-option label="工程师 (engineer)" value="engineer" />
            <el-option label="管理员 (admin)" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId === null ? '必填' : '留空表示不修改'"
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>
