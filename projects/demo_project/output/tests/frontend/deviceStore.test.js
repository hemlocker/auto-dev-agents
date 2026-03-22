/**
 * 设备 Store 测试
 * 测试 Pinia store device.js
 */

import { setActivePinia, createPinia } from 'pinia';
import { useDeviceStore } from '@/store/device';

describe('Device Store Tests', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDeviceStore();
  });

  describe('初始化测试', () => {
    test('应该正确初始化 store', () => {
      expect(store).toBeDefined();
    });

    test('应该有设备类型列表', () => {
      expect(store.deviceTypes).toBeDefined();
      expect(Array.isArray(store.deviceTypes)).toBe(true);
    });

    test('应该有设备状态列表', () => {
      expect(store.deviceStatuses).toBeDefined();
      expect(Array.isArray(store.deviceStatuses)).toBe(true);
    });
  });

  describe('设备类型测试', () => {
    test('应该包含默认的设备类型', () => {
      const expectedTypes = [
        '电脑',
        '打印机',
        '投影仪',
        '办公桌椅',
        '网络设备',
        '其他'
      ];

      expectedTypes.forEach(type => {
        expect(store.deviceTypes).toContain(type);
      });
    });

    test('设备类型应该是响应式的', () => {
      expect(store.deviceTypes.length).toBe(6);
      
      // 添加新类型
      store.deviceTypes.push('测试设备类型');
      
      expect(store.deviceTypes.length).toBe(7);
      expect(store.deviceTypes).toContain('测试设备类型');
    });

    test('设备类型应该可以被过滤', () => {
      const filtered = store.deviceTypes.filter(type => type.includes('电'));
      expect(filtered).toContain('电脑');
      expect(filtered).toContain('网络设备');
    });
  });

  describe('设备状态测试', () => {
    test('应该包含默认的设备状态', () => {
      const expectedStatuses = [
        '在用',
        '闲置',
        '报废'
      ];

      expectedStatuses.forEach(status => {
        expect(store.deviceStatuses).toContain(status);
      });
    });

    test('设备状态应该是响应式的', () => {
      expect(store.deviceStatuses.length).toBe(3);
      
      // 添加新状态
      store.deviceStatuses.push('维修中');
      
      expect(store.deviceStatuses.length).toBe(4);
      expect(store.deviceStatuses).toContain('维修中');
    });

    test('设备状态应该可以被过滤', () => {
      const filtered = store.deviceStatuses.filter(status => status === '在用');
      expect(filtered.length).toBe(1);
      expect(filtered[0]).toBe('在用');
    });
  });

  describe('Store 方法测试', () => {
    test('应该能获取设备类型映射', () => {
      const typeMap = store.deviceTypes.reduce((acc, type) => {
        acc[type] = type;
        return acc;
      }, {});

      expect(typeMap['电脑']).toBe('电脑');
      expect(typeMap['打印机']).toBe('打印机');
    });

    test('应该能获取设备状态映射', () => {
      const statusMap = store.deviceStatuses.reduce((acc, status) => {
        acc[status] = status;
        return acc;
      }, {});

      expect(statusMap['在用']).toBe('在用');
      expect(statusMap['闲置']).toBe('闲置');
      expect(statusMap['报废']).toBe('报废');
    });
  });

  describe('响应式测试', () => {
    test('应该能监听设备类型变化', () => {
      let changeCount = 0;
      const originalLength = store.deviceTypes.length;

      // 模拟监听
      store.deviceTypes.push('新类型');
      expect(store.deviceTypes.length).toBe(originalLength + 1);
    });

    test('应该能监听设备状态变化', () => {
      let changeCount = 0;
      const originalLength = store.deviceStatuses.length;

      // 模拟监听
      store.deviceStatuses.push('新状态');
      expect(store.deviceStatuses.length).toBe(originalLength + 1);
    });
  });

  describe('数据验证测试', () => {
    test('设备类型应该都是字符串', () => {
      store.deviceTypes.forEach(type => {
        expect(typeof type).toBe('string');
        expect(type.length).toBeGreaterThan(0);
      });
    });

    test('设备状态应该都是字符串', () => {
      store.deviceStatuses.forEach(status => {
        expect(typeof status).toBe('string');
        expect(status.length).toBeGreaterThan(0);
      });
    });

    test('设备类型不应该有重复', () => {
      const uniqueTypes = new Set(store.deviceTypes);
      expect(uniqueTypes.size).toBe(store.deviceTypes.length);
    });

    test('设备状态不应该有重复', () => {
      const uniqueStatuses = new Set(store.deviceStatuses);
      expect(uniqueStatuses.size).toBe(store.deviceStatuses.length);
    });
  });
});
