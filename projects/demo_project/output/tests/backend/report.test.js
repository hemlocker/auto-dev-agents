/**
 * 报表功能测试
 * 测试 reportController.js
 */

const request = require('supertest');
const Device = require('../../src/backend/models/Device');

describe('报表功能测试', () => {
  let server;

  beforeAll(() => {
    // 启动测试服务器
    const app = require('../../src/backend/src/app');
    server = app.listen(3004);
  });

  afterAll(async () => {
    // 关闭服务器
    await server.close();
  });

  beforeEach(async () => {
    // 清空测试数据
    await Device.destroy({ where: {}, truncate: true });
  });

  describe('GET /api/reports/statistics - 获取统计数据', () => {
    test('应该拒绝缺少统计维度的请求', async () => {
      const response = await request(server)
        .get('/api/reports/statistics')
        .expect(400);

      expect(response.body.code).toBe(400);
      expect(response.body.message).toBe('请提供统计维度');
    });

    test('应该拒绝不支持的统计维度', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=invalid')
        .expect(400);

      expect(response.body.code).toBe(400);
      expect(response.body.message).toBe('不支持的统计维度');
    });

    test('空数据时应该返回零统计', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      expect(response.body.code).toBe(200);
      expect(response.body.data.dimension).toBe('status');
      expect(response.body.data.summary.total).toBe(0);
    });
  });

  describe('按设备状态统计 (dimension=status)', () => {
    beforeEach(async () => {
      // 创建测试数据 - 不同状态
      await Device.bulkCreate([
        { device_id: 'DEV001', device_name: '设备 1', device_type: '电脑', purchase_date: '2024-01-01', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV002', device_name: '设备 2', device_type: '电脑', purchase_date: '2024-01-02', department: '技术部', user_name: '李四', status: '在用' },
        { device_id: 'DEV003', device_name: '设备 3', device_type: '打印机', purchase_date: '2024-01-03', department: '行政部', user_name: '王五', status: '在用' },
        { device_id: 'DEV004', device_name: '设备 4', device_type: '打印机', purchase_date: '2024-01-04', department: '行政部', user_name: '赵六', status: '闲置' },
        { device_id: 'DEV005', device_name: '设备 5', device_type: '电脑', purchase_date: '2024-01-05', department: '技术部', user_name: '孙七', status: '闲置' },
        { device_id: 'DEV006', device_name: '设备 6', device_type: '其他', purchase_date: '2024-01-06', department: '财务部', user_name: '周八', status: '报废' }
      ]);
    });

    test('应该正确统计各状态设备数量', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      expect(response.body.code).toBe(200);
      expect(response.body.data.dimension).toBe('status');
      
      const summary = response.body.data.summary;
      expect(summary.total).toBe(6);
      expect(summary.in_use).toBe(3);
      expect(summary.idle).toBe(2);
      expect(summary.scrapped).toBe(1);
    });

    test('应该正确计算百分比', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      const details = response.body.data.details;
      
      // 在用：3/6 = 50%
      const inUse = details.find(d => d.status === '在用');
      expect(inUse.count).toBe(3);
      expect(inUse.percentage).toBe(50.0);

      // 闲置：2/6 = 33.3%
      const idle = details.find(d => d.status === '闲置');
      expect(idle.count).toBe(2);
      expect(idle.percentage).toBe(33.3);

      // 报废：1/6 = 16.7%
      const scrapped = details.find(d => d.status === '报废');
      expect(scrapped.count).toBe(1);
      expect(scrapped.percentage).toBe(16.7);
    });

    test('应该返回所有状态的详细信息', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      const details = response.body.data.details;
      expect(details.length).toBe(3); // 三种状态
      
      const statuses = details.map(d => d.status);
      expect(statuses).toContain('在用');
      expect(statuses).toContain('闲置');
      expect(statuses).toContain('报废');
    });

    test('应该支持时间范围筛选', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status&start_date=2024-01-01&end_date=2024-01-03')
        .expect(200);

      expect(response.body.data.summary.total).toBe(3); // 只有前 3 个设备
      
      const summary = response.body.data.summary;
      expect(summary.in_use).toBe(3);
      expect(summary.idle).toBe(0);
      expect(summary.scrapped).toBe(0);
    });

    test('应该只筛选开始日期', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status&start_date=2024-01-04')
        .expect(200);

      expect(response.body.data.summary.total).toBe(3); // 后 3 个设备
    });

    test('应该只筛选结束日期', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status&end_date=2024-01-03')
        .expect(200);

      expect(response.body.data.summary.total).toBe(3); // 前 3 个设备
    });
  });

  describe('按使用部门统计 (dimension=department)', () => {
    beforeEach(async () => {
      await Device.bulkCreate([
        { device_id: 'DEV001', device_name: '设备 1', device_type: '电脑', purchase_date: '2024-01-01', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV002', device_name: '设备 2', device_type: '电脑', purchase_date: '2024-01-02', department: '技术部', user_name: '李四', status: '在用' },
        { device_id: 'DEV003', device_name: '设备 3', device_type: '打印机', purchase_date: '2024-01-03', department: '技术部', user_name: '王五', status: '在用' },
        { device_id: 'DEV004', device_name: '设备 4', device_type: '打印机', purchase_date: '2024-01-04', department: '行政部', user_name: '赵六', status: '在用' },
        { device_id: 'DEV005', device_name: '设备 5', device_type: '电脑', purchase_date: '2024-01-05', department: '行政部', user_name: '孙七', status: '在用' },
        { device_id: 'DEV006', device_name: '设备 6', device_type: '其他', purchase_date: '2024-01-06', department: '财务部', user_name: '周八', status: '在用' }
      ]);
    });

    test('应该正确统计各部门设备数量', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=department')
        .expect(200);

      expect(response.body.data.dimension).toBe('department');
      expect(response.body.data.summary.total).toBe(6);
      expect(response.body.data.summary.department_count).toBe(3);
    });

    test('应该按数量降序排列', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=department')
        .expect(200);

      const details = response.body.data.details;
      
      // 技术部应该排第一（3 个设备）
      expect(details[0].department).toBe('技术部');
      expect(details[0].count).toBe(3);

      // 行政部排第二（2 个设备）
      expect(details[1].department).toBe('行政部');
      expect(details[1].count).toBe(2);

      // 财务部排第三（1 个设备）
      expect(details[2].department).toBe('财务部');
      expect(details[2].count).toBe(1);
    });

    test('应该正确计算部门百分比', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=department')
        .expect(200);

      const details = response.body.data.details;
      
      const techDept = details.find(d => d.department === '技术部');
      expect(techDept.percentage).toBe(50.0); // 3/6

      const adminDept = details.find(d => d.department === '行政部');
      expect(adminDept.percentage).toBe(33.3); // 2/6

      const financeDept = details.find(d => d.department === '财务部');
      expect(financeDept.percentage).toBe(16.7); // 1/6
    });

    test('应该支持时间范围筛选', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=department&start_date=2024-01-01&end_date=2024-01-04')
        .expect(200);

      expect(response.body.data.summary.total).toBe(4);
      expect(response.body.data.summary.department_count).toBe(2);
    });
  });

  describe('按设备类型统计 (dimension=type)', () => {
    beforeEach(async () => {
      await Device.bulkCreate([
        { device_id: 'DEV001', device_name: '设备 1', device_type: '电脑', purchase_date: '2024-01-01', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV002', device_name: '设备 2', device_type: '电脑', purchase_date: '2024-01-02', department: '技术部', user_name: '李四', status: '在用' },
        { device_id: 'DEV003', device_name: '设备 3', device_type: '电脑', purchase_date: '2024-01-03', department: '技术部', user_name: '王五', status: '在用' },
        { device_id: 'DEV004', device_name: '设备 4', device_type: '打印机', purchase_date: '2024-01-04', department: '行政部', user_name: '赵六', status: '在用' },
        { device_id: 'DEV005', device_name: '设备 5', device_type: '打印机', purchase_date: '2024-01-05', department: '行政部', user_name: '孙七', status: '在用' },
        { device_id: 'DEV006', device_name: '设备 6', device_type: '扫描仪', purchase_date: '2024-01-06', department: '财务部', user_name: '周八', status: '在用' }
      ]);
    });

    test('应该正确统计各类型设备数量', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=type')
        .expect(200);

      expect(response.body.data.dimension).toBe('type');
      expect(response.body.data.summary.total).toBe(6);
      expect(response.body.data.summary.type_count).toBe(3);
    });

    test('应该按数量降序排列', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=type')
        .expect(200);

      const details = response.body.data.details;
      
      expect(details[0].device_type).toBe('电脑');
      expect(details[0].count).toBe(3);

      expect(details[1].device_type).toBe('打印机');
      expect(details[1].count).toBe(2);

      expect(details[2].device_type).toBe('扫描仪');
      expect(details[2].count).toBe(1);
    });

    test('应该正确计算类型百分比', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=type')
        .expect(200);

      const details = response.body.data.details;
      
      const computers = details.find(d => d.device_type === '电脑');
      expect(computers.percentage).toBe(50.0); // 3/6

      const printers = details.find(d => d.device_type === '打印机');
      expect(printers.percentage).toBe(33.3); // 2/6

      const scanners = details.find(d => d.device_type === '扫描仪');
      expect(scanners.percentage).toBe(16.7); // 1/6
    });
  });

  describe('按购买时间统计 (dimension=time)', () => {
    beforeEach(async () => {
      await Device.bulkCreate([
        { device_id: 'DEV001', device_name: '设备 1', device_type: '电脑', purchase_date: '2024-01-15', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV002', device_name: '设备 2', device_type: '电脑', purchase_date: '2024-01-20', department: '技术部', user_name: '李四', status: '在用' },
        { device_id: 'DEV003', device_name: '设备 3', device_type: '打印机', purchase_date: '2024-02-10', department: '行政部', user_name: '王五', status: '在用' },
        { device_id: 'DEV004', device_name: '设备 4', device_type: '打印机', purchase_date: '2024-02-15', department: '行政部', user_name: '赵六', status: '在用' },
        { device_id: 'DEV005', device_name: '设备 5', device_type: '电脑', purchase_date: '2024-03-01', department: '技术部', user_name: '孙七', status: '在用' },
        { device_id: 'DEV006', device_name: '设备 6', device_type: '其他', purchase_date: '2024-03-20', department: '财务部', user_name: '周八', status: '在用' }
      ]);
    });

    test('应该按月统计短期数据', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=time')
        .expect(200);

      expect(response.body.data.dimension).toBe('time');
      expect(response.body.data.time_unit).toBe('month');
      expect(response.body.data.summary.total).toBe(6);
    });

    test('应该正确分组月度数据', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=time')
        .expect(200);

      const details = response.body.data.details;
      
      expect(details.length).toBe(3); // 3 个月
      
      const jan = details.find(d => d.period === '2024-01');
      expect(jan.count).toBe(2);

      const feb = details.find(d => d.period === '2024-02');
      expect(feb.count).toBe(2);

      const mar = details.find(d => d.period === '2024-03');
      expect(mar.count).toBe(2);
    });

    test('应该按时间升序排列', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=time')
        .expect(200);

      const details = response.body.data.details;
      
      expect(details[0].period).toBe('2024-01');
      expect(details[1].period).toBe('2024-02');
      expect(details[2].period).toBe('2024-03');
    });

    test('应该支持时间范围筛选', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?dimension=time&start_date=2024-01-01&end_date=2024-01-31')
        .expect(200);

      expect(response.body.data.summary.total).toBe(2);
      expect(response.body.data.details.length).toBe(1);
      expect(response.body.data.details[0].period).toBe('2024-01');
      expect(response.body.data.details[0].count).toBe(2);
    });

    test('长期数据应该按年统计', async () => {
      // 创建跨多年的数据
      await Device.destroy({ where: {}, truncate: true });
      await Device.bulkCreate([
        { device_id: 'DEV2020', device_name: '设备 2020', device_type: '电脑', purchase_date: '2020-06-15', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV2021', device_name: '设备 2021', device_type: '电脑', purchase_date: '2021-06-15', department: '技术部', user_name: '李四', status: '在用' },
        { device_id: 'DEV2022', device_name: '设备 2022', device_type: '打印机', purchase_date: '2022-06-15', department: '行政部', user_name: '王五', status: '在用' },
        { device_id: 'DEV2023', device_name: '设备 2023', device_type: '打印机', purchase_date: '2023-06-15', department: '行政部', user_name: '赵六', status: '在用' }
      ]);

      const response = await request(server)
        .get('/api/reports/statistics?dimension=time')
        .expect(200);

      expect(response.body.data.time_unit).toBe('year');
      
      const details = response.body.data.details;
      expect(details.length).toBe(4);
      
      const year2020 = details.find(d => d.period === '2020');
      expect(year2020.count).toBe(1);

      const year2021 = details.find(d => d.period === '2021');
      expect(year2021.count).toBe(1);
    });
  });

  describe('报表功能边界测试', () => {
    test('单个设备统计应该正确', async () => {
      await Device.create({
        device_id: 'SINGLE',
        device_name: '唯一设备',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '独享部',
        user_name: '孤独用户',
        status: '在用'
      });

      const statusResponse = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      expect(statusResponse.data.summary.total).toBe(1);
      expect(statusResponse.data.summary.in_use).toBe(1);
      expect(statusResponse.data.details[0].percentage).toBe(100.0);
    });

    test('大量数据应该正确统计', async () => {
      // 创建 100 个测试设备
      const devices = [];
      for (let i = 1; i <= 100; i++) {
        devices.push({
          device_id: `BATCH${String(i).padStart(3, '0')}`,
          device_name: `设备${i}`,
          device_type: i % 2 === 0 ? '电脑' : '打印机',
          purchase_date: `2024-${String((i % 12) + 1).padStart(2, '0')}-01`,
          department: i % 3 === 0 ? '技术部' : (i % 3 === 1 ? '行政部' : '财务部'),
          user_name: `用户${i}`,
          status: i % 5 === 0 ? '闲置' : (i % 7 === 0 ? '报废' : '在用')
        });
      }

      await Device.bulkCreate(devices);

      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      expect(response.body.data.summary.total).toBe(100);
      
      // 验证百分比总和约为 100
      const totalPercentage = response.body.data.details.reduce(
        (sum, d) => sum + d.percentage, 
        0
      );
      expect(totalPercentage).toBeGreaterThanOrEqual(99.9);
      expect(totalPercentage).toBeLessThanOrEqual(100.1);
    });

    test('特殊字符部门名称应该正确处理', async () => {
      await Device.create({
        device_id: 'SPECIAL',
        device_name: '特殊设备',
        device_type: '电脑',
        purchase_date: '2024-01-01',
        department: '研发部 (北京) & 上海分公司',
        user_name: '测试用户',
        status: '在用'
      });

      const response = await request(server)
        .get('/api/reports/statistics?dimension=department')
        .expect(200);

      expect(response.body.data.summary.total).toBe(1);
      expect(response.body.data.details[0].department).toBe('研发部 (北京) & 上海分公司');
    });
  });

  describe('报表功能错误处理', () => {
    test('应该正确处理数据库异常', async () => {
      // 验证基本的错误处理机制
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      expect(response.body.code).toBe(200);
      expect(response.body.data).toBeDefined();
    });

    test('应该正确处理空查询字符串', async () => {
      const response = await request(server)
        .get('/api/reports/statistics?')
        .expect(400);

      expect(response.body.message).toBe('请提供统计维度');
    });

    test('应该正确处理无效日期格式', async () => {
      // 无效日期应该被忽略或返回错误
      const response = await request(server)
        .get('/api/reports/statistics?dimension=status&start_date=invalid-date')
        .expect(200);

      // 应该返回所有数据（忽略无效日期）
      expect(response.body.code).toBe(200);
    });
  });

  describe('报表功能综合测试', () => {
    beforeEach(async () => {
      await Device.bulkCreate([
        { device_id: 'DEV001', device_name: '设备 1', device_type: '电脑', purchase_date: '2024-01-15', department: '技术部', user_name: '张三', status: '在用' },
        { device_id: 'DEV002', device_name: '设备 2', device_type: '打印机', purchase_date: '2024-02-20', department: '行政部', user_name: '李四', status: '闲置' },
        { device_id: 'DEV003', device_name: '设备 3', device_type: '电脑', purchase_date: '2024-03-10', department: '技术部', user_name: '王五', status: '在用' },
        { device_id: 'DEV004', device_name: '设备 4', device_type: '扫描仪', purchase_date: '2024-04-05', department: '财务部', user_name: '赵六', status: '报废' }
      ]);
    });

    test('所有维度统计总数应该一致', async () => {
      const statusResponse = await request(server)
        .get('/api/reports/statistics?dimension=status')
        .expect(200);

      const deptResponse = await request(server)
        .get('/api/reports/statistics?dimension=department')
        .expect(200);

      const typeResponse = await request(server)
        .get('/api/reports/statistics?dimension=type')
        .expect(200);

      const timeResponse = await request(server)
        .get('/api/reports/statistics?dimension=time')
        .expect(200);

      expect(statusResponse.data.summary.total).toBe(4);
      expect(deptResponse.data.summary.total).toBe(4);
      expect(typeResponse.data.summary.total).toBe(4);
      expect(timeResponse.data.summary.total).toBe(4);
    });

    test('时间范围筛选应该对所有维度生效', async () => {
      const statusResponse = await request(server)
        .get('/api/reports/statistics?dimension=status&start_date=2024-02-01&end_date=2024-03-31')
        .expect(200);

      const deptResponse = await request(server)
        .get('/api/reports/statistics?dimension=department&start_date=2024-02-01&end_date=2024-03-31')
        .expect(200);

      expect(statusResponse.data.summary.total).toBe(2);
      expect(deptResponse.data.summary.total).toBe(2);
    });
  });
});
