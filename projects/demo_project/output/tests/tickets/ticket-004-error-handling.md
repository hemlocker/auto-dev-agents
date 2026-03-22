# Ticket #004 - 错误处理不完善

## 问题描述
打印功能中，对于无效请求体格式等错误场景，错误处理不够完善，返回 500 而非 400。

## 影响范围
- POST /api/devices/print-batch - 批量打印接口
- JSON 解析错误场景
- 其他输入验证场景

## 错误信息
```
expected 400 "Bad Request", got 500 "Internal Server Error"
```

## 测试用例
```javascript
test('应该正确处理无效的请求体格式', async () => {
  const response = await request(server)
    .post('/api/devices/print-batch')
    .send('invalid json')
    .set('Content-Type', 'application/json')
    .expect(400);  // 期望 400，实际得到 500
});
```

## 根本原因
1. Express 的 body-parser 在解析无效 JSON 时抛出错误
2. 控制器中缺少全局错误处理
3. 错误中间件可能未正确配置

## 建议修复方案

### 方案 1: 添加错误处理中间件
```javascript
// app.js
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({
      code: 400,
      message: '无效的 JSON 格式',
      data: null
    });
  }
  // 其他错误处理...
});
```

### 方案 2: 在控制器中添加 try-catch
```javascript
// printController.js
exports.printBatchLabels = async (req, res) => {
  try {
    const { device_ids } = req.body;
    
    if (!device_ids || !Array.isArray(device_ids)) {
      return res.status(400).json({
        code: 400,
        message: '请提供设备 ID 列表',
        data: null
      });
    }
    
    // ... 其余逻辑 ...
  } catch (error) {
    console.error('批量打印失败:', error);
    res.status(500).json({
      code: 500,
      message: '批量打印失败',
      data: null
    });
  }
};
```

### 方案 3: 配置 body-parser 错误处理
```javascript
// app.js
app.use(bodyParser.json({
  strict: true,
  type: 'application/json'
}));

// 添加专门的 JSON 错误处理
app.use((err, req, res, next) => {
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({
      code: 400,
      message: '请求体格式错误',
      data: null
    });
  }
  next(err);
});
```

## 优先级
低

## 预计工作量
1 小时

## 相关文件
- `/src/backend/src/app.js`
- `/src/backend/src/controllers/printController.js`
- `/tests/backend/print.test.js`

## 创建时间
2026-03-21 23:55 GMT+8
