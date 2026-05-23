import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/CockpitFrame.vue'),
    redirect: '/overview',
    children: [
      { path: 'overview', component: () => import('@/views/overview/Overview.vue'), meta: { title: '总览', n: 1 } },
      { path: 'profit-compare', component: () => import('@/views/profit-compare/ProfitCompare.vue'), meta: { title: '利润对比', n: 2 } },
      { path: 'engineer', component: () => import('@/views/engineer/EngineerView.vue'), meta: { title: '工程师视图', n: 3 } },
      { path: 'efficiency', component: () => import('@/views/efficiency/Efficiency.vue'), meta: { title: '项目进度视图', n: 4 } },
      { path: 'knowledge', component: () => import('@/views/knowledge/Knowledge.vue'), meta: { title: '技术沉淀', n: 5 } },
      { path: 'capability', component: () => import('@/views/capability/Capability.vue'), meta: { title: '团队能力', n: 6 } },
    ],
  },
]

export default createRouter({ history: createWebHistory(), routes })
