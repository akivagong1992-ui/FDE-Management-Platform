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
      // engineer 专属
      {
        path: 'my-assignments',
        component: () => import('@/views/my-assignments/MyAssignments.vue'),
        meta: { title: '我的派单', engineerOnly: true },
      },
      {
        path: 'my-timesheets',
        component: () => import('@/views/my-timesheets/MyTimesheets.vue'),
        meta: { title: '我的工时', engineerOnly: true },
      },
      {
        path: 'my-expenses',
        component: () => import('@/views/my-expenses/MyExpenses.vue'),
        meta: { title: '我的支出申请', engineerOnly: true },
      },
      // 管理者侧（pm / lead / admin / finance）
      { path: 'project', component: () => import('@/views/project/Index.vue'), meta: { title: '项目管理', pmSide: true } },
      { path: 'engineer', component: () => import('@/views/engineer/Index.vue'), meta: { title: '派单工时管理', pmSide: true } },
      { path: 'profit', component: () => import('@/views/profit/Index.vue'), meta: { title: '利润管理', pmSide: true } },
      { path: 'expense', component: () => import('@/views/expense/Index.vue'), meta: { title: '外部支出管理', pmSide: true } },
      { path: 'efficiency', component: () => import('@/views/efficiency/Index.vue'), meta: { title: '项目完成效率', pmSide: true } },
      { path: 'knowledge', component: () => import('@/views/knowledge/Index.vue'), meta: { title: '技术沉淀 / 知识资产', pmSide: true } },
      { path: 'capability', component: () => import('@/views/capability/Index.vue'), meta: { title: '工程师能力建设', pmSide: true } },
      { path: 'relationship', component: () => import('@/views/relationship/Index.vue'), meta: { title: '需求方关系 / 复盘', pmSide: true } },
      { path: 'users', component: () => import('@/views/users/UserManage.vue'), meta: { title: '用户管理', pmSide: true } },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.token) return { path: '/login', query: { redirect: to.fullPath } }

  // role 守门
  const role = auth.role
  if (role === 'engineer') {
    // engineer 只能进首页 + 我的派单
    if (to.meta.pmSide) return { path: '/my-assignments' }
  } else {
    // 非 engineer 角色访问 engineer-only 页面 → 退回首页
    if (to.meta.engineerOnly) return { path: '/dashboard' }
  }
  return true
})

export default router
