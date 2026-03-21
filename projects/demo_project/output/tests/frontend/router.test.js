/**
 * 路由配置测试
 * 测试 Vue Router 配置
 */

import { createRouter, createWebHistory } from 'vue-router';
import routes from '@/router/index';

describe('Router Configuration Tests', () => {
  let router;

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes
    });
  });

  describe('路由定义测试', () => {
    test('应该定义首页路由', () => {
      const homeRoute = routes.find(route => route.path === '/');
      
      expect(homeRoute).toBeDefined();
      expect(homeRoute.name).toBe('DeviceList');
    });

    test('应该定义新增设备路由', () => {
      const newRoute = routes.find(route => route.path === '/device/new');
      
      expect(newRoute).toBeDefined();
      expect(newRoute.name).toBe('DeviceNew');
    });

    test('应该定义编辑设备路由', () => {
      const editRoute = routes.find(route => route.path === '/device/edit/:id');
      
      expect(editRoute).toBeDefined();
      expect(editRoute.name).toBe('DeviceEdit');
    });

    test('应该定义设备详情路由', () => {
      const detailRoute = routes.find(route => route.path === '/device/detail/:id');
      
      expect(detailRoute).toBeDefined();
      expect(detailRoute.name).toBe('DeviceDetail');
    });
  });

  describe('路由导航测试', () => {
    test('应该能导航到首页', async () => {
      await router.push('/');
      expect(router.currentRoute.value.path).toBe('/');
      expect(router.currentRoute.value.name).toBe('DeviceList');
    });

    test('应该能导航到新增设备页面', async () => {
      await router.push('/device/new');
      expect(router.currentRoute.value.path).toBe('/device/new');
      expect(router.currentRoute.value.name).toBe('DeviceNew');
    });

    test('应该能导航到编辑设备页面', async () => {
      await router.push('/device/edit/001');
      expect(router.currentRoute.value.path).toBe('/device/edit/001');
      expect(router.currentRoute.value.name).toBe('DeviceEdit');
      expect(router.currentRoute.value.params.id).toBe('001');
    });

    test('应该能导航到设备详情页面', async () => {
      await router.push('/device/detail/001');
      expect(router.currentRoute.value.path).toBe('/device/detail/001');
      expect(router.currentRoute.value.name).toBe('DeviceDetail');
      expect(router.currentRoute.value.params.id).toBe('001');
    });
  });

  describe('路由参数测试', () => {
    test('编辑路由应该接受 id 参数', async () => {
      await router.push('/device/edit/TEST123');
      
      expect(router.currentRoute.value.params).toEqual({
        id: 'TEST123'
      });
    });

    test('详情路由应该接受 id 参数', async () => {
      await router.push('/device/detail/TEST456');
      
      expect(router.currentRoute.value.params).toEqual({
        id: 'TEST456'
      });
    });

    test('路由参数应该是字符串类型', async () => {
      await router.push('/device/edit/123');
      
      expect(typeof router.currentRoute.value.params.id).toBe('string');
    });
  });

  describe('路由懒加载测试', () => {
    test('首页组件应该是懒加载的', () => {
      const homeRoute = routes.find(route => route.path === '/');
      
      expect(homeRoute.component).toBeDefined();
      expect(typeof homeRoute.component).toBe('function');
    });

    test('新增设备组件应该是懒加载的', () => {
      const newRoute = routes.find(route => route.path === '/device/new');
      
      expect(newRoute.component).toBeDefined();
      expect(typeof newRoute.component).toBe('function');
    });

    test('编辑设备组件应该是懒加载的', () => {
      const editRoute = routes.find(route => route.path === '/device/edit/:id');
      
      expect(editRoute.component).toBeDefined();
      expect(typeof editRoute.component).toBe('function');
    });

    test('设备详情组件应该是懒加载的', () => {
      const detailRoute = routes.find(route => route.path === '/device/detail/:id');
      
      expect(detailRoute.component).toBeDefined();
      expect(typeof detailRoute.component).toBe('function');
    });
  });

  describe'路由历史记录测试', () => {
    test('应该能使用浏览器的后退功能', async () => {
      await router.push('/device/new');
      expect(router.currentRoute.value.path).toBe('/device/new');
      
      await router.back();
      expect(router.currentRoute.value.path).toBe('/');
    });

    test('应该能使用浏览器的前进功能', async () => {
      await router.push('/device/new');
      await router.back();
      expect(router.currentRoute.value.path).toBe('/');
      
      await router.forward();
      expect(router.currentRoute.value.path).toBe('/device/new');
    });

    test('应该能替换当前历史记录', async () => {
      await router.push('/device/new');
      await router.replace('/device/list');
      
      expect(router.currentRoute.value.path).toBe('/device/list');
      
      await router.back();
      // 因为使用了 replace，应该还在 /device/list
      expect(router.currentRoute.value.path).toBe('/device/list');
    });
  });

  describe'路由守卫测试（预留）', () => {
    test('应该支持添加路由守卫', () => {
      const beforeEachSpy = jest.fn();
      
      router.beforeEach((to, from, next) => {
        beforeEachSpy(to.path);
        next();
      });
      
      router.push('/device/new');
      
      // 路由守卫会被调用
      expect(beforeEachSpy).toHaveBeenCalled();
    });
  });
});
