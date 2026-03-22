# Ticket #001 - 流式响应问题

## 问题描述
在导入导出功能和打印功能中，使用流式响应 (streaming response) 时出现 500 Internal Server Error。

## 影响范围
- GET /api/devices/import-template - Excel 模板下载
- GET /api/devices/export - Excel 数据导出
- POST /api/devices/print-batch - PDF 批量打印

## 错误信息
```
expected 200 "OK", got 500 "Internal Server Error"
```

## 根本原因
控制器使用流式写入:
```javascript
XLSX.write(wb, res, { type: 'node', bookType: 'xlsx' });
```

在 supertest 测试环境中，流式响应可能无法正确处理。

## 建议修复方案

### 方案 1: 使用 Buffer (推荐)
```javascript
// importController.js
exports.downloadTemplate = async (req, res) => {
  try {
    // ... 创建 workbook ...
    
    // 改为使用 buffer
    const buffer = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' });
    
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="设备导入模板.xlsx"');
    
    res.send(buffer);
  } catch (error) {
    // ... 错误处理 ...
  }
};
```

### 方案 2: 修复测试中的流处理
在测试中使用特殊处理来接收流式响应。

## 优先级
高

## 预计工作量
2 小时

## 相关文件
- `/src/backend/src/controllers/importController.js`
- `/src/backend/src/controllers/exportController.js`
- `/src/backend/src/controllers/printController.js`

## 创建时间
2026-03-21 23:55 GMT+8
