/**
 * 设备控制器测试
 * 测试 deviceController.js 中的所有方法
 */

const Device = require('../../backend/models/Device');
const deviceController = require('../../backend/src/controllers/deviceController');
const sequelize = require('../../backend/config/database');

describe('Device Controller Tests', () => {
  // 测试数据
  const testDeviceData = {
    device_id: 'TEST001',
    device_name: '测试笔记本电脑',
    device_type: '电脑',
    specification: 'MacBook Pro 2024',
    purchase_date: '2024-01-15',
    department: '技术部',
    user_name: '张三',
    status: '在用',
    location: '北京办公室',
    remark: '测试设备'
  };

  // 每个测试前清空数据库
  beforeEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  // 每个测试后清理
  afterEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  describe('getDevices - 获取设备列表', () => {
    test('应该返回空列表当没有设备时', async () => {
      const mockReq = { query: {} };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDevices(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          message: 'success',
          data: expect.objectContaining({
            list: [],
            total: 0,
            page: 1,
            pageSize: 10
          })
        })
      );
    });

    test('应该返回设备列表当有设备时', async () => {
      await Device.create(testDeviceData);

      const mockReq = { query: {} };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDevices(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          data: expect.objectContaining({
            total: 1,
            list: expect.arrayContaining([
              expect.objectContaining({
                device_id: 'TEST001',
                device_name: '测试笔记本电脑'
              })
            ])
          })
        })
      );
    });

    test('应该支持关键词搜索', async () => {
      await Device.create(testDeviceData);
      await Device.create({
        ...testDeviceData,
        device_id: 'TEST002',
        device_name: '测试台式机'
      });

      const mockReq = { query: { keyword: '笔记本' } };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDevices(mockReq, mockRes);

      const responseData = mockRes.json.mock.calls[0][0].data;
      expect(responseData.total).toBe(1);
      expect(responseData.list[0].device_name).toContain('笔记本');
    });

    test('应该支持按设备类型筛选', async () => {
      await Device.create(testDeviceData);
      await Device.create({
        ...testDeviceData,
        device_id: 'TEST002',
        device_type: '打印机'
      });

      const mockReq = { query: { device_type: '电脑' } };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDevices(mockReq, mockRes);

      const responseData = mockRes.json.mock.calls[0][0].data;
      expect(responseData.total).toBe(1);
      expect(responseData.list[0].device_type).toBe('电脑');
    });

    test('应该支持分页', async () => {
      // 创建 15 个测试设备
      for (let i = 1; i <= 15; i++) {
        await Device.create({
          ...testDeviceData,
          device_id: `TEST${String(i).padStart(3, '0')}`
        });
      }

      const mockReq = { query: { page: 1, pageSize: 10 } };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDevices(mockReq, mockRes);

      const responseData = mockRes.json.mock.calls[0][0].data;
      expect(responseData.total).toBe(15);
      expect(responseData.list.length).toBe(10);
      expect(responseData.page).toBe(1);
      expect(responseData.pageSize).toBe(10);
    });

    test('应该处理错误情况', async () => {
      const mockReq = { query: {} };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      // 模拟数据库错误
      Device.findAndCountAll = jest.fn().mockRejectedValue(new Error('Database error'));

      await deviceController.getDevices(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(500);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 500,
          message: '服务器内部错误'
        })
      );
    });
  });

  describe('getDeviceById - 获取设备详情', () => {
    test('应该返回设备详情', async () => {
      await Device.create(testDeviceData);

      const mockReq = { params: { id: 'TEST001' } };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.getDeviceById(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          data: expect.objectContaining({
            device_id: 'TEST001',
            device_name: '测试笔记本电脑'
          })
        })
      );
    });

    test('应该返回 404 当设备不存在时', async () => {
      const mockReq = { params: { id: 'NON_EXISTENT' } };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      await deviceController.getDeviceById(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(404);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 404,
          message: '设备不存在'
        })
      );
    });
  });

  describe('createDevice - 新增设备', () => {
    test('应该成功创建设备', async () => {
      const mockReq = {
        body: testDeviceData
      };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.createDevice(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          message: '新增成功',
          data: expect.objectContaining({
            device_id: 'TEST001'
          })
        })
      );

      // 验证设备确实被创建
      const device = await Device.findByPk('TEST001');
      expect(device).toBeTruthy();
      expect(device.device_name).toBe('测试笔记本电脑');
    });

    test('应该拒绝重复的设备编号', async () => {
      await Device.create(testDeviceData);

      const mockReq = {
        body: testDeviceData
      };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      await deviceController.createDevice(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(400);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 400,
          message: '设备编号已存在'
        })
      );
    });

    test('应该处理创建时的错误', async () => {
      const mockReq = {
        body: testDeviceData
      };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      // 模拟数据库错误
      Device.findByPk = jest.fn().mockRejectedValue(new Error('Database error'));

      await deviceController.createDevice(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(500);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 500,
          message: '服务器内部错误'
        })
      );
    });
  });

  describe('updateDevice - 更新设备', () => {
    test('应该成功更新设备', async () => {
      await Device.create(testDeviceData);

      const mockReq = {
        params: { id: 'TEST001' },
        body: {
          device_name: '更新后的设备名称',
          status: '报废'
        }
      };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.updateDevice(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          message: '更新成功'
        })
      );

      // 验证更新
      const updatedDevice = await Device.findByPk('TEST001');
      expect(updatedDevice.device_name).toBe('更新后的设备名称');
      expect(updatedDevice.status).toBe('报废');
      expect(updatedDevice.device_id).toBe('TEST001'); // device_id 不应被修改
    });

    test('应该返回 404 当更新不存在的设备', async () => {
      const mockReq = {
        params: { id: 'NON_EXISTENT' },
        body: { device_name: '新名称' }
      };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      await deviceController.updateDevice(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(404);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 404,
          message: '设备不存在'
        })
      );
    });

    test('应该不允许修改设备编号', async () => {
      await Device.create(testDeviceData);

      const mockReq = {
        params: { id: 'TEST001' },
        body: {
          device_id: 'NEW_ID', // 这个应该被忽略
          device_name: '新名称'
        }
      };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.updateDevice(mockReq, mockRes);

      const updatedDevice = await Device.findByPk('TEST001');
      expect(updatedDevice.device_id).toBe('TEST001'); // 保持不变
      expect(updatedDevice.device_name).toBe('新名称');
    });
  });

  describe('deleteDevice - 删除设备', () => {
    test('应该成功删除设备', async () => {
      await Device.create(testDeviceData);

      const mockReq = { params: { id: 'TEST001' } };
      const mockRes = {
        json: jest.fn()
      };

      await deviceController.deleteDevice(mockReq, mockRes);

      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 200,
          message: '删除成功'
        })
      );

      // 验证设备已被删除
      const deletedDevice = await Device.findByPk('TEST001');
      expect(deletedDevice).toBeNull();
    });

    test('应该返回 404 当删除不存在的设备', async () => {
      const mockReq = { params: { id: 'NON_EXISTENT' } };
      const mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      await deviceController.deleteDevice(mockReq, mockRes);

      expect(mockRes.status).toHaveBeenCalledWith(404);
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 404,
          message: '设备不存在'
        })
      );
    });
  });
});
