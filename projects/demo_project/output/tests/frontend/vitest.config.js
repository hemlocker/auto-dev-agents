/**
 * 前端测试配置文件
 * Vitest 配置用于测试 Vue 3 + Vite 前端应用
 */

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  
  test: {
    // 测试环境
    environment: 'jsdom',
    
    // 测试文件匹配模式
    include: ['**/tests/frontend/**/*.test.{js,ts}'],
    
    // 覆盖率报告配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: [
        'src/frontend/src/**/*.{js,ts,vue}'
      ],
      exclude: [
        'src/frontend/src/main.js',
        '**/*.test.{js,ts}',
        '**/node_modules/**'
      ],
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        }
      }
    },
    
    // 全局超时时间
    testTimeout: 10000,
    
    // 设置文件
    setupFiles: ['./tests/frontend/setup.js'],
    
    // 全局测试钩子
    globals: true,
    
    // 模拟依赖
    mockReset: true,
    
    // 监听模式
    watch: false,
    
    // 最大并发数
    maxConcurrency: 5,
    
    // 序列异步测试
    sequence: {
      concurrent: false
    }
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../src/frontend/src')
    }
  }
});
