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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
