/**
 * 设备 API 测试
 * 测试前端 API 层 device.js
 */

import request from '@/utils/request';
import {
  getDeviceList,
  getDeviceDetail,
  createDevice,
  updateDevice,
  deleteDevice
} from '@/api/device';

// 模拟 request 模块
jest.mock('@/utils/request');

describe('Device API Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getDeviceList - 获取设备列表', () => {
    test('应该调用正确的 API 端点', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          message: 'success',
          data: {
            list: [],
            total: 0
          }
        }
      });

      await getDeviceList();

      expect(request).toHaveBeenCalledWith({
        url: '/devices',
        method: 'get',
        params: undefined
      });
    });

    test('应该支持传递查询参数', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          data: { list: [], total: 0 }
        }
      });

      const params = {
        keyword: '测试',
        device_type: '电脑',
        status: '闲置',
        page: 1,
        pageSize: 10
      };

      await getDeviceList(params);

      expect(request).toHaveBeenCalledWith({
        url: '/devices',
        method: 'get',
        params
      });
    });

    test('应该返回 API 响应数据', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: 'success',
          data: {
            list: [
              { device_id: '001', device_name: '设备 1' },
              { device_id: '002', device_name: '设备 2' }
            ],
            total: 2,
            page: 1,
            pageSize: 10
          }
        }
      };

      request.mockResolvedValue(mockResponse);

      const result = await getDeviceList();

      expect(result).toEqual(mockResponse.data);
      expect(result.data.list.length).toBe(2);
    });

    test('应该处理 API 错误', async () => {
      request.mockRejectedValue(new Error('Network Error'));

      await expect(getDeviceList()).rejects.toThrow('Network Error');
    });
  });

  describe('getDeviceDetail - 获取设备详情', () => {
    test('应该调用正确的 API 端点', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          data: {}
        }
      });

      await getDeviceDetail('001');

      expect(request).toHaveBeenCalledWith({
        url: '/devices/001',
        method: 'get'
      });
    });

    test('应该返回设备详情数据', async () => {
      const mockDevice = {
        device_id: '001',
        device_name: '测试设备',
        device_type: '电脑',
        status: '在用'
      };

      request.mockResolvedValue({
        data: {
          code: 200,
          message: 'success',
          data: mockDevice
        }
      });

      const result = await getDeviceDetail('001');

      expect(result.data).toEqual(mockDevice);
    });

    test('应该处理 404 错误', async () => {
      request.mockRejectedValue({
        response: {
          status: 404,
          data: {
            code: 404,
            message: '设备不存在'
          }
        }
      });

      await expect(getDeviceDetail('NON_EXISTENT')).rejects.toEqual(
        expect.objectContaining({
          response: expect.objectContaining({
            status: 404
          })
        })
      );
    });
  });

  describe('createDevice - 新增设备', () => {
    test('应该调用正确的 API 端点', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          message: '新增成功'
        }
      });

      const newDevice = {
        device_id: 'NEW001',
        device_name: '新设备',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '技术部',
        user_name: '张三',
        status: '闲置'
      };

      await createDevice(newDevice);

      expect(request).toHaveBeenCalledWith({
        url: '/devices',
        method: 'post',
        data: newDevice
      });
    });

    test('应该返回创建结果', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: '新增成功',
          data: {
            device_id: 'NEW001'
          }
        }
      };

      request.mockResolvedValue(mockResponse);

      const result = await createDevice({ device_id: 'NEW001' });

      expect(result).toEqual(mockResponse.data);
      expect(result.data.device_id).toBe('NEW001');
    });

    test('应该处理重复设备编号错误', async () => {
      request.mockRejectedValue({
        response: {
          status: 400,
          data: {
            code: 400,
            message: '设备编号已存在'
          }
        }
      });

      await expect(createDevice({ device_id: 'EXISTING' })).rejects.toEqual(
        expect.objectContaining({
          response: expect.objectContaining({
            status: 400
          })
        })
      );
    });
  });

  describe('updateDevice - 更新设备', () => {
    test('应该调用正确的 API 端点', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          message: '更新成功'
        }
      });

      const updateData = {
        device_name: '更新后的名称',
        status: '在用'
      };

      await updateDevice('001', updateData);

      expect(request).toHaveBeenCalledWith({
        url: '/devices/001',
        method: 'put',
        data: updateData
      });
    });

    test('应该返回更新结果', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: '更新成功',
          data: {
            device_id: '001'
          }
        }
      };

      request.mockResolvedValue(mockResponse);

      const result = await updateDevice('001', { device_name: '新名称' });

      expect(result).toEqual(mockResponse.data);
    });

    test('应该处理 404 错误', async () => {
      request.mockRejectedValue({
        response: {
          status: 404,
          data: {
            code: 404,
            message: '设备不存在'
          }
        }
      });

      await expect(updateDevice('NON_EXISTENT', {})).rejects.toEqual(
        expect.objectContaining({
          response: expect.objectContaining({
            status: 404
          })
        })
      );
    });
  });

  describe('deleteDevice - 删除设备', () => {
    test('应该调用正确的 API 端点', async () => {
      request.mockResolvedValue({
        data: {
          code: 200,
          message: '删除成功'
        }
      });

      await deleteDevice('001');

      expect(request).toHaveBeenCalledWith({
        url: '/devices/001',
        method: 'delete'
      });
    });

    test('应该返回删除结果', async () => {
      const mockResponse = {
        data: {
          code: 200,
          message: '删除成功',
          data: null
        }
      };

      request.mockResolvedValue(mockResponse);

      const result = await deleteDevice('001');

      expect(result).toEqual(mockResponse.data);
      expect(result.data).toBeNull();
    });

    test('应该处理 404 错误', async () => {
      request.mockRejectedValue({
        response: {
          status: 404,
          data: {
            code: 404,
            message: '设备不存在'
          }
        }
      });

      await expect(deleteDevice('NON_EXISTENT')).rejects.toEqual(
        expect.objectContaining({
          response: expect.objectContaining({
            status: 404
          })
        })
      );
    });
  });
});
