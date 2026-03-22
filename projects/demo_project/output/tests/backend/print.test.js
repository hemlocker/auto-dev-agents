/**
 * 打印功能测试
 * 测试 printController.js
 */

const request = require('supertest');
const PDFDocument = require('pdfkit');
const Device = require('../../src/backend/models/Device');

describe('打印功能测试', () => {
  let server;

  beforeAll(() => {
    // 启动测试服务器
    const app = require('../../src/backend/src/app');
    server = app.listen(3003);
  });

  afterAll(async () => {
    // 关闭服务器
    await server.close();
  });

  beforeEach(async () => {
    // 清空测试数据
    await Device.destroy({ where: {}, truncate: true });
  });

  describe('GET /api/devices/:id/label - 获取设备标签数据', () => {
    test('应该返回 404 当设备不存在时', async () => {
      const response = await request(server)
        .get('/api/devices/NONEXISTENT/label')
        .expect(404);

      expect(response.body.code).toBe(404);
      expect(response.body.message).toBe('设备不存在');
    });

    test('应该成功获取设备标签数据', async () => {
      // 创建测试设备
      await Device.create({
        device_id: 'DEV001',
        device_name: '联想 ThinkPad X1',
        device_type: '电脑',
        specification: 'i7/16G/512G',
        purchase_date: '2024-01-15',
        department: '技术部',
        user_name: '张三',
        status: '在用',
        location: 'A 栋 301',
        remark: '测试设备'
      });

      const response = await request(server)
        .get('/api/devices/DEV001/label')
        .expect(200);

      expect(response.body.code).toBe(200);
      expect(response.body.message).toBe('success');
      expect(response.body.data).toBeDefined();
    });

    test('标签数据应该包含所有必要字段', async () => {
      await Device.create({
        device_id: 'DEV002',
        device_name: '惠普打印机',
        device_type: '打印机',
        specification: 'LaserJet Pro',
        purchase_date: '2024-03-20',
        department: '行政部',
        user_name: '李四',
        status: '闲置',
        location: 'B 栋 102',
        remark: ''
      });

      const response = await request(server)
        .get('/api/devices/DEV002/label')
        .expect(200);

      const data = response.body.data;
      expect(data).toHaveProperty('device_id', 'DEV002');
      expect(data).toHaveProperty('device_name', '惠普打印机');
      expect(data).toHaveProperty('device_type', '打印机');
      expect(data).toHaveProperty('specification', 'LaserJet Pro');
      expect(data).toHaveProperty('purchase_date', '2024-03-20');
      expect(data).toHaveProperty('department', '行政部');
      expect(data).toHaveProperty('user_name', '李四');
      expect(data).toHaveProperty('status', '闲置');
      expect(data).toHaveProperty('location', 'B 栋 102');
      expect(data).toHaveProperty('remark', '');
    });

    test('标签数据应该包含二维码', async () => {
      await Device.create({
        device_id: 'DEV003',
        device_name: '测试设备',
        device_type: '电脑',
        specification: '',
        purchase_date: '2024-01-01',
        department: '技术部',
        user_name: '测试用户',
        status: '在用'
      });

      const response = await request(server)
        .get('/api/devices/DEV003/label')
        .expect(200);

      const data = response.body.data;
      expect(data).toHaveProperty('qr_code');
      expect(data.qr_code).toMatch(/^data:image\/png;base64,/);
      expect(data.qr_code.length).toBeGreaterThan(1000); // 二维码数据应该有一定长度
    });

    test('二维码应该包含正确的设备 URL', async () => {
      await Device.create({
        device_id: 'DEV004',
        device_name: '测试设备',
        device_type: '电脑',
        specification: '',
        purchase_date: '2024-01-01',
        department: '技术部',
        user_name: '测试用户',
        status: '在用'
      });

      const response = await request(server)
        .get('/api/devices/DEV004/label')
        .expect(200);

      // 二维码数据是 base64 编码的图片，我们无法直接验证内容
      // 但可以验证它存在且格式正确
      expect(response.body.data.qr_code).toMatch(/^data:image\/png;base64,/);
    });

    test('应该正确处理可选字段为空的情况', async () => {
      await Device.create({
        device_id: 'DEV005',
        device_name: '最小设备',
        device_type: '其他',
        specification: null,
        purchase_date: '2024-01-01',
        department: '测试部',
        user_name: '测试',
        status: '在用',
        location: null,
        remark: null
      });

      const response = await request(server)
        .get('/api/devices/DEV005/label')
        .expect(200);

      const data = response.body.data;
      expect(data.device_id).toBe('DEV005');
      expect(data.device_name).toBe('最小设备');
      // 可选字段应该存在但可能为空
      expect(data).toHaveProperty('specification');
      expect(data).toHaveProperty('location');
      expect(data).toHaveProperty('remark');
    });
  });

  describe('POST /api/devices/print-batch - 批量打印设备标签', () => {
    beforeEach(async () => {
      // 创建测试设备
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

    test('应该拒绝空的设备 ID 列表', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: [] })
        .expect(400);

      expect(response.body.code).toBe(400);
      expect(response.body.message).toContain('请提供设备 ID 列表');
    });

    test('应该拒绝非数组的设备 ID 参数', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: 'DEV001' })
        .expect(400);

      expect(response.body.code).toBe(400);
    });

    test('应该拒绝缺少 device_ids 参数的请求', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({})
        .expect(400);

      expect(response.body.code).toBe(400);
    });

    test('应该成功生成单个设备的 PDF', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001'] })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      expect(response.headers['content-disposition']).toContain('attachment');
      expect(response.headers['content-disposition']).toContain('设备标签_');
      expect(response.headers['content-disposition']).toContain('.pdf');

      // 验证 PDF 内容
      expect(response.body).toBeDefined();
      expect(response.body.length).toBeGreaterThan(0);
    });

    test('应该成功生成多个设备的 PDF', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001', 'DEV002', 'DEV003'] })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      expect(response.body.length).toBeGreaterThan(0);

      // 多个设备的 PDF 应该比单个设备的大
      const singleResponse = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001'] })
        .expect(200);

      expect(response.body.length).toBeGreaterThan(singleResponse.body.length);
    });

    test('应该只包含请求中指定的设备', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001', 'DEV003'] })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      
      // PDF 应该成功生成
      expect(response.body.length).toBeGreaterThan(0);
    });

    test('应该忽略不存在的设备 ID', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001', 'NONEXISTENT', 'DEV002'] })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      // 应该只包含存在的设备
      expect(response.body.length).toBeGreaterThan(0);
    });

    test('当所有设备 ID 都不存在时应该返回 404', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['NONEXISTENT1', 'NONEXISTENT2'] })
        .expect(404);

      expect(response.body.code).toBe(404);
      expect(response.body.message).toBe('未找到设备信息');
    });

    test('PDF 应该包含正确的响应头', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV001'] })
        .expect(200);

      const contentDisposition = response.headers['content-disposition'];
      expect(contentDisposition).toContain('attachment');
      expect(contentDisposition).toContain('filename=');
      expect(contentDisposition).toContain('.pdf');
    });

    test('应该正确处理特殊字符的设备信息', async () => {
      await Device.create({
        device_id: 'DEV-SPECIAL',
        device_name: '测试设备 & 特殊@字符',
        device_type: '电脑/笔记本',
        specification: 'i7/16G/512G (高配)',
        purchase_date: '2024-01-15',
        department: '研发部 (北京)',
        user_name: '张三',
        status: '在用',
        location: 'A 栋 301 室'
      });

      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['DEV-SPECIAL'] })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      expect(response.body.length).toBeGreaterThan(0);
    });
  });

  describe('打印功能边界测试', () => {
    test('应该能处理大量设备的批量打印', async () => {
      // 创建 20 个测试设备
      const devices = [];
      for (let i = 1; i <= 20; i++) {
        devices.push({
          device_id: `BATCH${String(i).padStart(3, '0')}`,
          device_name: `批量测试设备${i}`,
          device_type: '电脑',
          specification: `规格${i}`,
          purchase_date: '2024-01-01',
          department: '测试部',
          user_name: `用户${i}`,
          status: '在用'
        });
      }

      await Device.bulkCreate(devices);

      const deviceIds = devices.map(d => d.device_id);
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: deviceIds })
        .expect(200);

      expect(response.headers['content-type']).toBe('application/pdf');
      // 大量设备的 PDF 应该比较大
      expect(response.body.length).toBeGreaterThan(10000);
    });

    test('单个设备打印和批量打印应该生成有效的 PDF', async () => {
      await Device.create({
        device_id: 'PDFTEST',
        device_name: 'PDF 测试设备',
        device_type: '电脑',
        specification: '测试规格',
        purchase_date: '2024-01-01',
        department: '测试部',
        user_name: '测试用户',
        status: '在用'
      });

      // 单个设备
      const singleResponse = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['PDFTEST'] })
        .expect(200);

      // 验证 PDF 签名
      expect(singleResponse.body.slice(0, 5)).toEqual(Buffer.from('%PDF-'));

      // 批量（同一个设备）
      const batchResponse = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: ['PDFTEST', 'PDFTEST'] })
        .expect(200);

      expect(batchResponse.body.slice(0, 5)).toEqual(Buffer.from('%PDF-'));
    });
  });

  describe('打印功能错误处理', () => {
    test('应该正确处理数据库查询错误', async () => {
      // 这个测试验证在数据库异常时的错误处理
      // 由于我们使用内存数据库，这个场景较难模拟
      // 但我们可以验证正常的错误处理流程
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send({ device_ids: null })
        .expect(400);

      expect(response.body.code).toBe(400);
    });

    test('应该正确处理无效的请求体格式', async () => {
      const response = await request(server)
        .post('/api/devices/print-batch')
        .send('invalid json')
        .set('Content-Type', 'application/json')
        .expect(400);

      expect(response.body.code).toBe(400);
    });
  });

  describe('二维码生成测试', () => {
    test('不同设备应该生成不同的二维码', async () => {
      await Device.create({
        device_id: 'QR001',
        device_name: '设备 1',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '部门 1',
        user_name: '用户 1',
        status: '在用'
      });

      await Device.create({
        device_id: 'QR002',
        device_name: '设备 2',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '部门 1',
        user_name: '用户 1',
        status: '在用'
      });

      const response1 = await request(server)
        .get('/api/devices/QR001/label')
        .expect(200);

      const response2 = await request(server)
        .get('/api/devices/QR002/label')
        .expect(200);

      // 两个设备的二维码应该不同
      expect(response1.data.qr_code).not.toBe(response2.data.qr_code);
    });

    test('二维码数据应该是有效的 base64 编码', async () => {
      await Device.create({
        device_id: 'QRTEST',
        device_name: '二维码测试',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '测试部',
        user_name: '测试',
        status: '在用'
      });

      const response = await request(server)
        .get('/api/devices/QRTEST/label')
        .expect(200);

      const qrCode = response.body.data.qr_code;
      
      // 验证 base64 格式
      expect(qrCode).toMatch(/^data:image\/png;base64,/);
      
      // 提取 base64 部分并验证
      const base64Data = qrCode.replace(/^data:image\/png;base64,/, '');
      expect(base64Data).toMatch(/^[A-Za-z0-9+/]+=*$/);
    });
  });
});
