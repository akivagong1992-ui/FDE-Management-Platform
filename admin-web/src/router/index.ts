import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', component: () => import('@/views/login/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('@/views/dashboard/Home.vue'), meta: { title: '首页' } },
      { path: 'project', component: () => import('@/views/project/Index.vue'), meta: { title: '项目管理' } },
      { path: 'engineer', component: () => import('@/views/engineer/Index.vue'), meta: { title: '员工派单' } },
      { path: 'profit', component: () => import('@/views/profit/Index.vue'), meta: { title: '利润管理' } },
      { path: 'expense', component: () => import('@/views/expense/Index.vue'), meta: { title: '外部支出管理' } },
      { path: 'efficiency', component: () => import('@/views/efficiency/Index.vue'), meta: { title: '项目完成效率' } },
      { path: 'knowledge', component: () => import('@/views/knowledge/Index.vue'), meta: { title: '技术沉淀 / 知识资产' } },
      { path: 'capability', component: () => import('@/views/capability/Index.vue'), meta: { title: '工程师能力建设' } },
      { path: 'relationship', component: () => import('@/views/relationship/Index.vue'), meta: { title: '需求方关系 / 复盘' } },
      { path: 'users', component: () => import('@/views/users/UserManage.vue'), meta: { title: '用户管理' } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.token) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})

export default router
