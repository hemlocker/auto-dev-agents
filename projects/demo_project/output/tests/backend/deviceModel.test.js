/**
 * 设备模型测试
 * 测试 Device.js 模型定义和数据库操作
 */

const Device = require('../../backend/models/Device');
const sequelize = require('../../backend/config/database');

describe('Device Model Tests', () => {
  const testDeviceData = {
    device_id: 'MODEL_TEST001',
    device_name: '模型测试设备',
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

  describe('模型定义测试', () => {
    test('应该正确定义 Device 模型', () => {
      expect(Device).toBeDefined();
      expect(Device.tableName).toBe('devices');
    });

    test('应该有正确的字段定义', async () => {
      const device = await Device.create(testDeviceData);
      
      expect(device.device_id).toBe('MODEL_TEST001');
      expect(device.device_name).toBe('模型测试设备');
      expect(device.device_type).toBe('电脑');
      expect(device.specification).toBe('测试规格');
      expect(device.purchase_date).toBe('2024-01-01');
      expect(device.department).toBe('测试部门');
      expect(device.user_name).toBe('测试用户');
      expect(device.status).toBe('闲置');
      expect(device.location).toBe('测试位置');
      expect(device.remark).toBe('测试备注');
    });
  });

  describe('必填字段验证', () => {
    test('应该拒绝缺少 device_id 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.device_id;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 device_name 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.device_name;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 device_type 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.device_type;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 purchase_date 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.purchase_date;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 department 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.department;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 user_name 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.user_name;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });

    test('应该拒绝缺少 status 的设备', async () => {
      const invalidDevice = { ...testDeviceData };
      delete invalidDevice.status;

      await expect(Device.create(invalidDevice)).rejects.toThrow();
    });
  });

  describe('可选字段测试', () => {
    test('应该允许缺少 specification 的设备', async () => {
      const deviceData = { ...testDeviceData };
      delete deviceData.specification;

      const device = await Device.create(deviceData);
      expect(device.device_id).toBe('MODEL_TEST001');
      expect(device.specification).toBeNull();
    });

    test('应该允许缺少 location 的设备', async () => {
      const deviceData = { ...testDeviceData };
      delete deviceData.location;

      const device = await Device.create(deviceData);
      expect(device.location).toBeNull();
    });

    test('应该允许缺少 remark 的设备', async () => {
      const deviceData = { ...testDeviceData };
      delete deviceData.remark;

      const device = await Device.create(deviceData);
      expect(device.remark).toBeNull();
    });
  });

  describe('默认值测试', () => {
    test('status 字段应该有默认值 "闲置"', async () => {
      const deviceData = {
        device_id: 'DEFAULT_TEST',
        device_name: '默认值测试',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '测试部门',
        user_name: '测试用户'
      };

      const device = await Device.create(deviceData);
      expect(device.status).toBe('闲置');
    });
  });

  describe('CRUD 操作测试', () => {
    test('应该成功创建设备 (Create)', async () => {
      const device = await Device.create(testDeviceData);
      expect(device.device_id).toBe('MODEL_TEST001');
      expect(device.createdAt).toBeDefined();
    });

    test('应该成功查询设备 (Read)', async () => {
      await Device.create(testDeviceData);
      
      const device = await Device.findByPk('MODEL_TEST001');
      expect(device).toBeTruthy();
      expect(device.device_name).toBe('模型测试设备');
    });

    test('应该成功更新设备 (Update)', async () => {
      await Device.create(testDeviceData);
      
      const device = await Device.findByPk('MODEL_TEST001');
      await device.update({
        device_name: '更新后的名称',
        status: '在用'
      });

      const updated = await Device.findByPk('MODEL_TEST001');
      expect(updated.device_name).toBe('更新后的名称');
      expect(updated.status).toBe('在用');
    });

    test('应该成功删除设备 (Delete)', async () => {
      await Device.create(testDeviceData);
      
      const device = await Device.findByPk('MODEL_TEST001');
      await device.destroy();

      const deleted = await Device.findByPk('MODEL_TEST001');
      expect(deleted).toBeNull();
    });
  });

  describe('查询方法测试', () => {
    test('应该支持 findAndCountAll 进行分页查询', async () => {
      // 创建多个设备
      for (let i = 0; i < 15; i++) {
        await Device.create({
          ...testDeviceData,
          device_id: `MODEL_TEST${String(i).padStart(3, '0')}`
        });
      }

      const { count, rows } = await Device.findAndCountAll({
        offset: 0,
        limit: 10,
        order: [['device_id', 'ASC']]
      });

      expect(count).toBe(15);
      expect(rows.length).toBe(10);
    });

    test('应该支持 where 条件查询', async () => {
      await Device.create(testDeviceData);
      await Device.create({
        ...testDeviceData,
        device_id: 'MODEL_TEST002',
        device_type: '打印机'
      });

      const devices = await Device.findAll({
        where: { device_type: '电脑' }
      });

      expect(devices.length).toBe(1);
      expect(devices[0].device_type).toBe('电脑');
    });

    test('应该支持排序', async () => {
      await Device.create({ ...testDeviceData, device_id: 'MODEL_TEST003' });
      await Device.create({ ...testDeviceData, device_id: 'MODEL_TEST001' });
      await Device.create({ ...testDeviceData, device_id: 'MODEL_TEST002' });

      const devices = await Device.findAll({
        order: [['device_id', 'ASC']]
      });

      expect(devices[0].device_id).toBe('MODEL_TEST001');
      expect(devices[1].device_id).toBe('MODEL_TEST002');
      expect(devices[2].device_id).toBe('MODEL_TEST003');
    });
  });

  describe('数据完整性测试', () => {
    test('device_id 应该是主键且唯一', async () => {
      await Device.create(testDeviceData);

      await expect(
        Device.create({
          ...testDeviceData,
          device_name: '重复的设备'
        })
      ).rejects.toThrow();
    });

    test('purchase_date 应该是有效的日期格式', async () => {
      const device = await Device.create({
        ...testDeviceData,
        purchase_date: '2024-12-31'
      });

      expect(device.purchase_date).toBe('2024-12-31');
    });

    test('status 应该是预定义的值之一', async () => {
      const validStatuses = ['在用', '闲置', '报废'];

      for (const status of validStatuses) {
        const device = await Device.create({
          ...testDeviceData,
          device_id: `STATUS_${status}`,
          status
        });
        expect(device.status).toBe(status);
      }
    });
  });
});
