<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta?.title as string) || 'FDE管理系统')
const isEngineer = computed(() => auth.role === 'engineer')
const isVendor = computed(() => auth.role === 'vendor')
const isPm = computed(() => auth.role === 'pm')

function handleLogout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #001428">
      <div style="color: #fff; padding: 20px; font-size: 16px; font-weight: 600">
        FDE管理系统
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001428"
        text-color="#a3b1c6"
        active-text-color="#409eff"
        router
      >
        <!-- vendor 视角：只看「成本和支出管理」一项；进去默认到 Vendor 支出 tab -->
        <template v-if="isVendor">
          <el-menu-item index="/expense"><span>成本和支出管理</span></el-menu-item>
        </template>

        <!-- 工程师视角：只看自己的派单 / 工时 / 支出 / 档期 -->
        <template v-else-if="isEngineer">
          <el-menu-item index="/my-assignments"><span>我的派单</span></el-menu-item>
          <el-menu-item index="/my-timesheets"><span>我的工时</span></el-menu-item>
          <el-menu-item index="/my-expenses"><span>我的支出</span></el-menu-item>
          <el-menu-item index="/availability"><span>我的档期</span></el-menu-item>
        </template>

        <!-- PM 视角：项目执行相关 7 项，不含财务/用户/派单 -->
        <template v-else-if="isPm">
          <el-menu-item index="/dashboard"><span>首页</span></el-menu-item>
          <el-menu-item index="/project"><span>项目和客户管理</span></el-menu-item>
          <el-menu-item index="/availability"><span>工程师档期</span></el-menu-item>
          <el-menu-item index="/efficiency"><span>项目效率管理</span></el-menu-item>
          <el-menu-item index="/knowledge"><span>FDE知识库</span></el-menu-item>
          <el-menu-item index="/capability"><span>培训管理</span></el-menu-item>
          <el-menu-item index="/relationship"><span>关键项目复盘管理</span></el-menu-item>
        </template>

        <!-- lead / admin / finance：全部菜单 -->
        <template v-else>
          <el-menu-item index="/dashboard"><span>首页</span></el-menu-item>
          <el-menu-item index="/project"><span>项目和客户管理</span></el-menu-item>
          <el-menu-item index="/engineer"><span>派单和工时管理</span></el-menu-item>
          <el-menu-item index="/availability"><span>工程师档期</span></el-menu-item>
          <el-menu-item index="/profit"><span>利润管理</span></el-menu-item>
          <el-menu-item index="/expense"><span>成本和支出管理</span></el-menu-item>
          <el-menu-item index="/efficiency"><span>项目效率管理</span></el-menu-item>
          <el-menu-item index="/knowledge"><span>FDE知识库</span></el-menu-item>
          <el-menu-item index="/capability"><span>培训管理</span></el-menu-item>
          <el-menu-item index="/relationship"><span>关键项目复盘管理</span></el-menu-item>
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
