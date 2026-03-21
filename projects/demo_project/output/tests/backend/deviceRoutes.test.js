/**
 * 设备 API 路由测试
 * 测试 deviceRoutes.js 中的路由配置
 * 使用 supertest 进行 HTTP 请求测试
 */

const request = require('supertest');
const app = require('../../backend/src/app');
const Device = require('../../backend/models/Device');
const sequelize = require('../../backend/config/database');

describe('Device API Routes Tests', () => {
  // 测试基础数据
  const testDevice = {
    device_id: 'API_TEST001',
    device_name: 'API 测试设备',
    device_type: '电脑',
    specification: '测试规格',
    purchase_date: '2024-01-01',
    department: '测试部门',
    user_name: '测试用户',
    status: '闲置',
    location: '测试位置',
    remark: '测试备注'
  };

  // 每个测试前清空数据库
  beforeEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  afterEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  describe('GET /api/devices - 获取设备列表', () => {
    test('应该返回 200 和空列表', async () => {
      const response = await request(app)
        .get('/api/devices')
        .expect(200);

      expect(response.body).toMatchObject({
        code: 200,
        message: 'success',
        data: {
          list: [],
          total: 0,
          page: 1,
          pageSize: 10
        }
      });
    });

    test('应该返回设备列表', async () => {
      await Device.create(testDevice);

      const response = await request(app)
        .get('/api/devices')
        .expect(200);

      expect(response.body.data.total).toBe(1);
      expect(response.body.data.list[0].device_id).toBe('API_TEST001');
    });

    test('应该支持分页参数', async () => {
      // 创建多个设备
      for (let i = 0; i < 15; i++) {
        await Device.create({
          ...testDevice,
          device_id: `API_TEST${String(i).padStart(3, '0')}`
        });
      }

      const response = await request(app)
        .get('/api/devices')
        .query({ page: 1, pageSize: 10 })
        .expect(200);

      expect(response.body.data.total).toBe(15);
      expect(response.body.data.list.length).toBe(10);
    });

    test('应该支持关键词搜索', async () => {
      await Device.create(testDevice);
      await Device.create({
        ...testDevice,
        device_id: 'API_TEST002',
        device_name: '另一个设备'
      });

      const response = await request(app)
        .get('/api/devices')
        .query({ keyword: 'API 测试' })
        .expect(200);

      expect(response.body.data.total).toBe(1);
      expect(response.body.data.list[0].device_name).toContain('API 测试');
    });

    test('应该支持按状态筛选', async () => {
      await Device.create(testDevice);
      await Device.create({
        ...testDevice,
        device_id: 'API_TEST002',
        status: '在用'
      });

      const response = await request(app)
        .get('/api/devices')
        .query({ status: '闲置' })
        .expect(200);

      expect(response.body.data.total).toBe(1);
      expect(response.body.data.list[0].status).toBe('闲置');
    });
  });

  describe('POST /api/devices - 创建设备', () => {
    test('应该成功创建设备并返回 200', async () => {
      const response = await request(app)
        .post('/api/devices')
        .send(testDevice)
        .expect(200);

      expect(response.body).toMatchObject({
        code: 200,
        message: '新增成功',
        data: {
          device_id: 'API_TEST001'
        }
      });

      // 验证设备已创建
      const device = await Device.findByPk('API_TEST001');
      expect(device).toBeTruthy();
    });

    test('应该拒绝重复的设备编号并返回 400', async () => {
      await Device.create(testDevice);

      const response = await request(app)
        .post('/api/devices')
        .send(testDevice)
        .expect(400);

      expect(response.body).toMatchObject({
        code: 400,
        message: '设备编号已存在'
      });
    });

    test('应该拒绝缺少必填字段的请求', async () => {
      const invalidDevice = {
        device_id: 'INVALID001'
        // 缺少其他必填字段
      };

      const response = await request(app)
        .post('/api/devices')
        .send(invalidDevice)
        .expect(500); // Sequelize 验证错误会触发 500

      // 或者根据实际验证逻辑可能是 400
      expect(response.body.code).toBeOneOf([400, 500]);
    });
  });

  describe('GET /api/devices/:id - 获取设备详情', () => {
    test('应该返回设备详情', async () => {
      await Device.create(testDevice);

      const response = await request(app)
        .get('/api/devices/API_TEST001')
        .expect(200);

      expect(response.body).toMatchObject({
        code: 200,
        message: 'success',
        data: expect.objectContaining({
          device_id: 'API_TEST001',
          device_name: 'API 测试设备'
        })
      });
    });

    test('应该返回 404 当设备不存在', async () => {
      const response = await request(app)
        .get('/api/devices/NON_EXISTENT')
        .expect(404);

      expect(response.body).toMatchObject({
        code: 404,
        message: '设备不存在'
      });
    });
  });

  describe('PUT /api/devices/:id - 更新设备', () => {
    test('应该成功更新设备', async () => {
      await Device.create(testDevice);

      const updateData = {
        device_name: '更新后的名称',
        status: '在用'
      };

      const response = await request(app)
        .put('/api/devices/API_TEST001')
        .send(updateData)
        .expect(200);

      expect(response.body).toMatchObject({
        code: 200,
        message: '更新成功'
      });

      // 验证更新
      const updated = await Device.findByPk('API_TEST001');
      expect(updated.device_name).toBe('更新后的名称');
      expect(updated.status).toBe('在用');
    });

    test('应该返回 404 当更新不存在的设备', async () => {
      const response = await request(app)
        .put('/api/devices/NON_EXISTENT')
        .send({ device_name: '新名称' })
        .expect(404);

      expect(response.body).toMatchObject({
        code: 404,
        message: '设备不存在'
      });
    });

    test('应该忽略 device_id 字段的修改', async () => {
      await Device.create(testDevice);

      const response = await request(app)
        .put('/api/devices/API_TEST001')
        .send({
          device_id: 'NEW_ID', // 这个应该被忽略
          device_name: '新名称'
        })
        .expect(200);

      const updated = await Device.findByPk('API_TEST001');
      expect(updated.device_id).toBe('API_TEST001'); // 保持不变
    });
  });

  describe('DELETE /api/devices/:id - 删除设备', () => {
    test('应该成功删除设备', async () => {
      await Device.create(testDevice);

      const response = await request(app)
        .delete('/api/devices/API_TEST001')
        .expect(200);

      expect(response.body).toMatchObject({
        code: 200,
        message: '删除成功'
      });

      // 验证已删除
      const deleted = await Device.findByPk('API_TEST001');
      expect(deleted).toBeNull();
    });

    test('应该返回 404 当删除不存在的设备', async () => {
      const response = await request(app)
        .delete('/api/devices/NON_EXISTENT')
        .expect(404);

      expect(response.body).toMatchObject({
        code: 404,
        message: '设备不存在'
      });
    });
  });

  describe('错误处理测试', () => {
    test('应该处理 JSON 解析错误', async () => {
      const response = await request(app)
        .post('/api/devices')
        .set('Content-Type', 'application/json')
        .send('invalid json')
        .expect(400); // Express 会返回 400 对于无效的 JSON
    });

    test('应该处理未定义的路由', async () => {
      const response = await request(app)
        .get('/api/undefined-route')
        .expect(404); // Express 会返回 404
    });
  });
});

// Jest 扩展匹配器
expect.extend({
  toBeOneOf(received, array) {
    const pass = array.includes(received);
    if (pass) {
      return {
        message: () => `expected ${received} not to be one of ${array.join(', ')}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be one of ${array.join(', ')}`,
        pass: false,
      };
    }
  },
});
