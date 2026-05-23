<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta?.title as string) || '人力管理平台')
const isEngineer = computed(() => auth.role === 'engineer')

function handleLogout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #001428">
      <div style="color: #fff; padding: 20px; font-size: 16px; font-weight: 600">
        人力管理平台
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001428"
        text-color="#a3b1c6"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard"><span>首页</span></el-menu-item>

        <!-- 工程师视角：只看自己的派单 / 工时 / 支出 -->
        <template v-if="isEngineer">
          <el-menu-item index="/my-assignments"><span>📥 我的派单</span></el-menu-item>
          <el-menu-item index="/my-timesheets"><span>⏱ 我的工时</span></el-menu-item>
          <el-menu-item index="/my-expenses"><span>💰 我的支出申请</span></el-menu-item>
        </template>

        <!-- 管理者视角（pm / lead / admin / finance）-->
        <template v-else>
          <el-menu-item index="/project"><span>① 项目管理</span></el-menu-item>
          <el-menu-item index="/engineer"><span>② 员工派单</span></el-menu-item>
          <el-menu-item index="/profit"><span>③ 利润管理</span></el-menu-item>
          <el-menu-item index="/expense"><span>④ 外部支出</span></el-menu-item>
          <el-menu-item index="/efficiency"><span>⑤ 项目效率</span></el-menu-item>
          <el-menu-item index="/knowledge"><span>⑥ 技术沉淀 ⭐</span></el-menu-item>
          <el-menu-item index="/capability"><span>⑦ 能力建设 ⭐</span></el-menu-item>
          <el-menu-item index="/relationship"><span>⑧ 需求方关系 ⭐</span></el-menu-item>
          <el-menu-item index="/users"><span>系统设置 · 用户</span></el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header
        style="background: #fff; border-bottom: 1px solid #e4e7ed;
               display: flex; align-items: center; justify-content: space-between"
      >
        <div style="font-size: 16px; font-weight: 500">{{ currentTitle }}</div>
        <div>
          <el-tag size="small" type="info" style="margin-right: 8px">
            {{ auth.role }}
          </el-tag>
          <span style="margin-right: 12px">{{ auth.username }}</span>
          <el-button size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main style="background: #f5f7fa">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
