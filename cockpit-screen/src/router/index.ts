import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/CockpitFrame.vue'),
    redirect: '/overview',
    children: [
      { path: 'overview', component: () => import('@/views/overview/Overview.vue'), meta: { title: '总览视图', n: 1 } },
      { path: 'profit-compare', component: () => import('@/views/profit-compare/ProfitCompare.vue'), meta: { title: '降本视图', n: 2 } },
      // 工程师视图：从 nav 隐藏（工程师总数已并入团队能力视图），路由保留供直接 URL 访问
      { path: 'engineer', component: () => import('@/views/engineer/EngineerView.vue'), meta: { title: '工程师视图', hidden: true } },
      { path: 'efficiency', component: () => import('@/views/efficiency/Efficiency.vue'), meta: { title: '项目进度视图', n: 3 } },
      { path: 'knowledge', component: () => import('@/views/knowledge/Knowledge.vue'), meta: { title: '技术沉淀视图', n: 4 } },
      { path: 'capability', component: () => import('@/views/capability/Capability.vue'), meta: { title: '团队能力视图', n: 5 } },
    ],
  },
]

export default createRouter({ history: createWebHistory(), routes })
