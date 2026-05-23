<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: 'admin', password: 'admin123' })
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } catch {
    /* http interceptor already showed error */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <div class="title">FDE管理系统</div>
      <div class="subtitle">电信国际香港事业部</div>
      <el-form @submit.prevent="onSubmit" :model="form" label-position="top" style="margin-top: 24px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button :loading="loading" type="primary" style="width: 100%" @click="onSubmit">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #061327 0%, #0a1929 100%);
}
.login-card { width: 380px; padding: 8px 4px; }
.title { font-size: 22px; font-weight: 600; text-align: center; }
.subtitle { font-size: 13px; color: #909399; text-align: center; margin-top: 8px; }
</style>
