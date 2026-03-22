# Ticket #002 - URL 编码问题

## 问题描述
在导出功能测试中，包含中文字符的查询参数导致错误:
```
TypeError: Request path contains unescaped characters
```

## 影响范围
- GET /api/devices/export?device_type=打印机
- GET /api/devices/export?status=闲置
- GET /api/devices/export?department=技术部
- 所有包含中文参数的导出请求

## 错误信息
```
TypeError: Request path contains unescaped characters
at Test.request (../node_modules/superagent/src/node/index.js:808:22)
```

## 根本原因
supertest/superagent 要求 URL 中的特殊字符必须正确编码，但测试中直接使用了中文字符。

## 建议修复方案

### 修复测试文件
```javascript
// importExport.test.js

// 错误写法
const response = await request(server)
  .get('/api/devices/export?device_type=打印机')
  .expect(200);

// 正确写法 - 使用 encodeURIComponent
const response = await request(server)
  .get('/api/devices/export?device_type=' + encodeURIComponent('打印机'))
  .expect(200);

// 或使用 query 方法
const response = await request(server)
  .get('/api/devices/export')
  .query({ device_type: '打印机' })  // supertest 会自动编码
  .expect(200);
```

## 优先级
中

## 预计工作量
30 分钟

## 相关文件
- `/tests/backend/importExport.test.js`

## 创建时间
2026-03-21 23:55 GMT+8
