/**
 * 后端 API 测试配置文件
 * Jest 配置用于测试 Node.js + Express + Sequelize 后端应用
 */

module.exports = {
  // 测试环境
  testEnvironment: 'node',
  
  // 测试文件匹配模式
  testMatch: ['**/tests/backend/**/*.test.js'],
  
  // 覆盖率报告配置
  collectCoverage: true,
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/backend/**/*.js',
    '!src/backend/config/database.js',
    '!**/node_modules/**',
    '!**/vendor/**'
  ],
  
  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  
  // 测试超时时间 (毫秒)
  testTimeout: 10000,
  
  // 详细输出
  verbose: true,
  
  // 测试失败时停止
  bail: false,
  
  // 模块映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/backend/$1'
  },
  
  // 设置测试前后的全局配置
  setupFilesAfterEnv: ['./tests/backend/setup.js'],
  
  // 监听模式配置
  watchPathIgnorePatterns: ['/node_modules/', '/database/'],
  
  // 最大工作进程数
  maxWorkers: '50%'
};
