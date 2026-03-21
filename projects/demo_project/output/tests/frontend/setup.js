/**
 * 前端测试设置文件
 * 配置 Vue Test Utils 和测试全局环境
 */

import { config } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import ElementPlus from 'element-plus';

// 创建 Pinia 实例
const pinia = createPinia();

// 创建路由器实例
const routes = [
  { path: '/', component: { template: '<div>Home</div>' } },
  { path: '/device/new', component: { template: '<div>New Device</div>' } },
  { path: '/device/edit/:id', component: { template: '<div>Edit Device</div>' } },
  { path: '/device/detail/:id', component: { template: '<div>Device Detail</div>' } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 全局配置 Vue Test Utils
config.global.plugins = [pinia, router, ElementPlus];

// 全局模拟的组件
config.global.components = {};

// 全局提供的依赖
config.global.provide = {
  // 在这里添加全局提供的依赖
};

// 全局模拟的 API
globalThis.mockApi = {
  device: {
    getDeviceList: jest.fn().mockResolvedValue({
      data: {
        code: 200,
        message: 'success',
        data: {
          list: [],
          total: 0,
          page: 1,
          pageSize: 10
        }
      }
    }),
    getDeviceDetail: jest.fn().mockResolvedValue({
      data: {
        code: 200,
        message: 'success',
        data: {}
      }
    }),
    createDevice: jest.fn().mockResolvedValue({
      data: {
        code: 200,
        message: '新增成功',
        data: {}
      }
    }),
    updateDevice: jest.fn().mockResolvedValue({
      data: {
        code: 200,
        message: '更新成功',
        data: {}
      }
    }),
    deleteDevice: jest.fn().mockResolvedValue({
      data: {
        code: 200,
        message: '删除成功',
        data: null
      }
    })
  }
};

// 测试工具函数
globalThis.testUtils = {
  // 创建测试设备数据
  createTestDevice: (overrides = {}) => ({
    device_id: `TEST_${Date.now()}`,
    device_name: '测试设备',
    device_type: '电脑',
    specification: '测试规格',
    purchase_date: '2024-01-01',
    department: '测试部门',
    user_name: '测试用户',
    status: '闲置',
    location: '测试位置',
    remark: '测试备注',
    ...overrides
  }),
  
  // 等待异步操作
  waitForTick: () => new Promise(resolve => setTimeout(resolve, 0)),
  
  // 模拟路由导航
  mockRouteNavigate: (path) => {
    router.push(path);
  }
};

// 每个测试后清理
afterEach(() => {
  // 重置所有模拟
  jest.clearAllMocks();
  
  // 重置路由
  router.push('/');
});
