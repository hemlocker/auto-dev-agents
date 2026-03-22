import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'DeviceList',
    component: () => import('@/views/DeviceList.vue')
  },
  {
    path: '/device/new',
    name: 'DeviceNew',
    component: () => import('@/views/DeviceNew.vue')
  },
  {
    path: '/device/edit/:id',
    name: 'DeviceEdit',
    component: () => import('@/views/DeviceEdit.vue')
  },
  {
    path: '/device/detail/:id',
    name: 'DeviceDetail',
    component: () => import('@/views/DeviceDetail.vue')
  },
  {
    path: '/device-type',
    name: 'DeviceTypeList',
    component: () => import('@/views/DeviceTypeList.vue')
  },
  {
    path: '/device/import-export',
    name: 'ImportExport',
    component: () => import('@/views/ImportExport.vue')
  },
  {
    path: '/device/print/:id',
    name: 'PrintPreview',
    component: () => import('@/views/PrintPreview.vue')
  },
  {
    path: '/device/print-batch',
    name: 'BatchPrint',
    component: () => import('@/views/PrintPreview.vue')
  },
  {
    path: '/reports',
    name: 'ReportDashboard',
    component: () => import('@/views/ReportDashboard.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
