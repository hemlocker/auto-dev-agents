/**
 * 导入导出功能测试
 * 测试 importController.js 和 exportController.js
 */

const request = require('supertest');
const path = require('path');
const fs = require('fs');
const XLSX = require('xlsx');
const app = require('../../src/backend/src/app');
const Device = require('../../src/backend/models/Device');

// Helper function to create Excel buffer
function createExcelBuffer(data, sheetName = 'Sheet1') {
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(data);
  XLSX.utils.book_append_sheet(wb, ws, sheetName);
  return XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
}

describe('导入导出功能测试', () => {
  let server;
  let testDevices = [];

  beforeAll((done) => {
    // 启动测试服务器
    server = app.listen(3002, () => {
      done();
    });
  });

  afterAll(async () => {
    // 关闭服务器
    await server.close();
  });

  beforeEach(async () => {
    // 清空测试数据
    await Device.destroy({ where: {}, truncate: true });
    testDevices = [];
  });

  describe('GET /api/devices/import-template - 下载导入模板', () => {
    test('应该成功下载 Excel 模板', async () => {
      const response = await request(server)
        .get('/api/devices/import-template')
        .expect(200);

      // 验证响应头
      expect(response.headers['content-type']).toBe(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
      expect(response.headers['content-disposition']).toContain('attachment');
      expect(response.headers['content-disposition']).toContain('设备导入模板.xlsx');

      // 验证文件内容
      expect(response.body).toBeDefined();
      expect(response.body.length).toBeGreaterThan(0);
    });

    test('模板应该包含正确的表头', async () => {
      const response = await request(server)
        .get('/api/devices/import-template')
        .expect(200);

      // 读取 Excel 内容
      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

      // 验证表头
      const headers = jsonData[0];
      expect(headers).toEqual([
        '设备编号', '设备名称', '设备类型', '规格型号', '购买日期',
        '使用部门', '使用人', '设备状态', '存放位置', '备注'
      ]);

      // 验证示例数据存在
      expect(jsonData.length).toBeGreaterThan(1);
      expect(jsonData[1]).toBeDefined();
    });

    test('模板应该包含示例数据', async () => {
      const response = await request(server)
        .get('/api/devices/import-template')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBeGreaterThanOrEqual(2);
      expect(jsonData[0]).toHaveProperty('设备编号', 'DEV001');
      expect(jsonData[0]).toHaveProperty('设备名称', '联想 ThinkPad X1');
    });
  });

  describe('POST /api/devices/import - 批量导入设备', () => {
    test('应该拒绝空文件上传', async () => {
      const response = await request(server)
        .post('/api/devices/import')
        .expect(400);

      expect(response.body.code).toBe(400);
      expect(response.body.message).toContain('请上传 Excel 文件');
    });

    test('应该成功导入有效的 Excel 文件', async () => {
      // 创建测试 Excel 文件
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV001', '测试设备 1', '电脑', 'i7/16G', '2024-01-15', '技术部', '张三', '在用', 'A 栋 301', '测试备注'],
        ['DEV002', '测试设备 2', '打印机', 'HP LaserJet', '2024-02-20', '行政部', '李四', '闲置', 'B 栋 102', '']
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_import.xlsx')
        .expect(200);

      expect(response.body.code).toBe(200);
      expect(response.body.message).toBe('导入完成');
      expect(response.body.data.total).toBe(2);
      expect(response.body.data.success).toBe(2);
      expect(response.body.data.failed).toBe(0);
      expect(response.body.data.errors).toEqual([]);

      // 验证设备已保存到数据库
      const devices = await Device.findAll();
      expect(devices.length).toBe(2);
    });

    test('应该报告验证错误 - 缺少必填字段', async () => {
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['', '测试设备', '电脑', '', '2024-01-15', '技术部', '张三', '在用', '', ''] // 缺少设备编号
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_invalid.xlsx')
        .expect(200);

      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors[0].reason).toContain('设备编号不能为空');
    });

    test('应该报告验证错误 - 设备编号格式不正确', async () => {
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV@001', '测试设备', '电脑', '', '2024-01-15', '技术部', '张三', '在用', '', ''] // 包含特殊字符
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_invalid_id.xlsx')
        .expect(200);

      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors[0].reason).toContain('设备编号只能包含字母、数字、下划线、中划线');
    });

    test('应该报告验证错误 - 日期格式不正确', async () => {
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV001', '测试设备', '电脑', '', '2024/01/15', '技术部', '张三', '在用', '', ''] // 错误日期格式
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_invalid_date.xlsx')
        .expect(200);

      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors[0].reason).toContain('购买日期格式不正确');
    });

    test('应该报告验证错误 - 设备状态无效', async () => {
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV001', '测试设备', '电脑', '', '2024-01-15', '技术部', '张三', '未知状态', '', ''] // 无效状态
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_invalid_status.xlsx')
        .expect(200);

      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors[0].reason).toContain('设备状态必须是在用、闲置或报废');
    });

    test('应该报告重复的设备编号', async () => {
      // 先创建一个设备
      await Device.create({
        device_id: 'DEV001',
        device_name: '已有设备',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '技术部',
        user_name: '张三',
        status: '在用'
      });

      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV001', '新设备', '电脑', '', '2024-01-15', '技术部', '李四', '在用', '', ''] // 重复编号
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_duplicate.xlsx')
        .expect(200);

      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors[0].reason).toBe('设备编号已存在');
    });

    test('应该部分成功导入 - 混合有效和无效数据', async () => {
      const testData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['DEV001', '有效设备', '电脑', '', '2024-01-15', '技术部', '张三', '在用', '', ''], // 有效
        ['', '无效设备', '电脑', '', '2024-01-15', '技术部', '张三', '在用', '', ''], // 缺少编号
        ['DEV002', '有效设备 2', '打印机', '', '2024-02-20', '行政部', '李四', '闲置', '', ''] // 有效
      ];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_mixed.xlsx')
        .expect(200);

      expect(response.body.data.total).toBe(3);
      expect(response.body.data.success).toBe(2);
      expect(response.body.data.failed).toBe(1);
      expect(response.body.data.errors.length).toBe(1);
    });

    test('应该拒绝空文件', async () => {
      const testData = [['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注']];

      const buffer = createExcelBuffer(testData);

      const response = await request(server)
        .post('/api/devices/import')
        .attach('file', buffer, 'test_empty.xlsx')
        .expect(400);

      expect(response.body.message).toContain('Excel 文件为空');
    });
  });

  describe('GET /api/devices/export - 导出设备数据', () => {
    beforeEach(async () => {
      // 创建测试数据
      await Device.bulkCreate([
        {
          device_id: 'DEV001',
          device_name: '联想 ThinkPad X1',
          device_type: '电脑',
          specification: 'i7/16G/512G',
          purchase_date: '2024-01-15',
          department: '技术部',
          user_name: '张三',
          status: '在用',
          location: 'A 栋 301'
        },
        {
          device_id: 'DEV002',
          device_name: '惠普打印机',
          device_type: '打印机',
          specification: 'LaserJet Pro',
          purchase_date: '2024-03-20',
          department: '行政部',
          user_name: '李四',
          status: '闲置',
          location: 'B 栋 102'
        },
        {
          device_id: 'DEV003',
          device_name: '戴尔显示器',
          device_type: '电脑',
          specification: '27 寸 4K',
          purchase_date: '2024-02-10',
          department: '技术部',
          user_name: '王五',
          status: '在用',
          location: 'A 栋 302'
        }
      ]);
    });

    test('应该导出所有设备', async () => {
      const response = await request(server)
        .get('/api/devices/export')
        .expect(200);

      expect(response.headers['content-type']).toBe(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
      expect(response.headers['content-disposition']).toContain('attachment');
      expect(response.headers['content-disposition']).toContain('设备列表_');
      expect(response.headers['content-disposition']).toContain('.xlsx');

      // 验证导出内容
      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(3);
    });

    test('应该按关键词筛选导出', async () => {
      const response = await request(server)
        .get('/api/devices/export?keyword=联想')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(1);
      expect(jsonData[0].设备名称).toBe('联想 ThinkPad X1');
    });

    test('应该按设备类型筛选导出', async () => {
      const response = await request(server)
        .get('/api/devices/export?device_type=打印机')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(1);
      expect(jsonData[0].设备类型).toBe('打印机');
    });

    test('应该按状态筛选导出', async () => {
      const response = await request(server)
        .get('/api/devices/export?status=闲置')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(1);
      expect(jsonData[0].设备状态).toBe('闲置');
    });

    test('应该按部门筛选导出', async () => {
      const response = await request(server)
        .get('/api/devices/export?department=技术部')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(2);
      jsonData.forEach(device => {
        expect(device.使用部门).toBe('技术部');
      });
    });

    test('应该支持多条件组合筛选', async () => {
      const response = await request(server)
        .get('/api/devices/export?device_type=电脑&status=在用&department=技术部')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(2);
    });

    test('导出空结果应该返回空文件', async () => {
      const response = await request(server)
        .get('/api/devices/export?keyword=不存在的设备')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(0);
    });

    test('导出文件应该包含正确的列', async () => {
      const response = await request(server)
        .get('/api/devices/export')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

      const headers = jsonData[0];
      expect(headers).toEqual([
        '设备编号', '设备名称', '设备类型', '规格型号', '购买日期',
        '使用部门', '使用人', '设备状态', '存放位置', '备注'
      ]);
    });

    test('导出应该按设备编号排序', async () => {
      const response = await request(server)
        .get('/api/devices/export')
        .expect(200);

      const workbook = XLSX.read(response.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData[0].设备编号).toBe('DEV001');
      expect(jsonData[1].设备编号).toBe('DEV002');
      expect(jsonData[2].设备编号).toBe('DEV003');
    });
  });

  describe('导入导出集成测试', () => {
    test('导入的数据应该可以被导出', async () => {
      // 先导入数据
      const importData = [
        ['设备编号', '设备名称', '设备类型', '规格型号', '购买日期', '使用部门', '使用人', '设备状态', '存放位置', '备注'],
        ['IMPORT001', '导入设备 1', '电脑', '', '2024-05-01', '研发部', '赵六', '在用', '', '']
      ];

      const importBuffer = createExcelBuffer(importData);

      await request(server)
        .post('/api/devices/import')
        .attach('file', importBuffer, 'import_test.xlsx')
        .expect(200);

      // 然后导出数据
      const exportResponse = await request(server)
        .get('/api/devices/export?keyword=IMPORT001')
        .expect(200);

      const workbook = XLSX.read(exportResponse.body, { type: 'buffer' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      expect(jsonData.length).toBe(1);
      expect(jsonData[0].设备编号).toBe('IMPORT001');
      expect(jsonData[0].设备名称).toBe('导入设备 1');
    });
  });
});
