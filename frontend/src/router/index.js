import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '监测概览' }
      },
      {
        path: 'monitor/data-entry',
        name: 'MonitorDataEntry',
        component: () => import('@/views/monitor/DataEntry.vue'),
        meta: { title: '监测数据录入', roles: ['DISPATCH', 'GEOLOGIST'] }
      },
      {
        path: 'monitor/chart',
        name: 'MonitorChart',
        component: () => import('@/views/monitor/ChartView.vue'),
        meta: { title: '监测曲线' }
      },
      {
        path: 'anomaly/list',
        name: 'AnomalyList',
        component: () => import('@/views/anomaly/List.vue'),
        meta: { title: '异常预警' }
      },
      {
        path: 'anomaly/:id',
        name: 'AnomalyDetail',
        component: () => import('@/views/anomaly/Detail.vue'),
        meta: { title: '异常详情' }
      },
      {
        path: 'instruction/list',
        name: 'InstructionList',
        component: () => import('@/views/instruction/List.vue'),
        meta: { title: '处置指令' }
      },
      {
        path: 'instruction/create',
        name: 'InstructionCreate',
        component: () => import('@/views/instruction/Create.vue'),
        meta: { title: '签发指令', roles: ['SAFETY_HEAD'] }
      },
      {
        path: 'discharge/list',
        name: 'DischargeList',
        component: () => import('@/views/discharge/List.vue'),
        meta: { title: '排放计划' }
      },
      {
        path: 'discharge/create',
        name: 'DischargeCreate',
        component: () => import('@/views/discharge/Create.vue'),
        meta: { title: '新增排放计划', roles: ['DISPATCH', 'SAFETY_HEAD'] }
      },
      {
        path: 'disposal/list',
        name: 'DisposalList',
        component: () => import('@/views/disposal/List.vue'),
        meta: { title: '处置记录' }
      },
      {
        path: 'disposal/:id',
        name: 'DisposalDetail',
        component: () => import('@/views/disposal/Detail.vue'),
        meta: { title: '处置记录详情' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth !== false && !userStore.isLoggedIn) {
    next('/login')
    return
  }

  if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
    return
  }

  if (to.meta.roles && to.meta.roles.length > 0) {
    if (!to.meta.roles.some(r => userStore.hasRole(r))) {
      next('/')
      return
    }
  }

  next()
})

export default router
