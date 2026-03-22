/**
 * 测试环境设置文件
 * 在每个测试文件运行前执行
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 测试数据库路径
const testDbPath = path.join(__dirname, '../../database/test_device.db');

// 全局设置
beforeAll(async () => {
  // 确保测试数据库目录存在
  const dbDir = path.dirname(testDbPath);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  
  // 如果存在旧的测试数据库，删除它
  if (fs.existsSync(testDbPath)) {
    fs.unlinkSync(testDbPath);
  }
  
  // 设置测试环境变量
  process.env.NODE_ENV = 'test';
  process.env.DATABASE_PATH = testDbPath;
  process.env.PORT = '3001'; // 使用不同端口避免冲突
});

// 每个测试后清理
afterEach(async () => {
  // 可以在这里添加每个测试后的清理逻辑
});

// 全部测试结束后清理
afterAll(async () => {
  // 删除测试数据库
  if (fs.existsSync(testDbPath)) {
    fs.unlinkSync(testDbPath);
  }
});

// 全局测试工具函数
global.testHelpers = {
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
  
  // 模拟响应对象
  createMockResponse: () => {
    const res = {
      statusCode: 200,
      jsonData: null,
      json: jest.fn(function(data) {
        this.jsonData = data;
        return this;
      }),
      status: jest.fn(function(code) {
        this.statusCode = code;
        return this;
      }),
      send: jest.fn(function() {
        return this;
      })
    };
    return res;
  },
  
  // 模拟请求对象
  createMockRequest: (params = {}, query = {}, body = {}) => ({
    params,
    query,
    body
  })
};
