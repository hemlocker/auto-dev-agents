# Ticket #003 - SQLite 日期函数兼容性问题

## 问题描述
在报表功能的时间维度统计测试中，SQLite 的 strftime 函数行为与预期不符。

## 影响范围
- GET /api/reports/statistics?dimension=time
- 按购买时间统计的所有测试用例

## 错误信息
测试失败：
- 应该按月统计短期数据
- 应该正确分组月度数据
- 应该按时间升序排列

## 根本原因
可能原因:
1. SQLite 的 strftime 函数在测试数据库中的行为不一致
2. 日期格式存储或查询有问题
3. 测试数据库与实际数据库配置不同

## 调试步骤

### 1. 检查数据库中的日期格式
```sql
SELECT purchase_date, strftime('%Y-%m', purchase_date) as period 
FROM devices 
LIMIT 10;
```

### 2. 检查控制器代码
```javascript
// reportController.js
[
  Device.sequelize.fn(
    'strftime',
    timeUnit === 'month' ? '%Y-%m' : '%Y',
    Device.sequelize.col('purchase_date')
  ),
  'period'
]
```

### 3. 验证日期存储格式
确保日期以 'YYYY-MM-DD' 格式存储。

## 建议修复方案

### 方案 1: 使用 Sequelize 内置日期函数
```javascript
// 使用 Sequelize 的 date_trunc 或类似函数
[
  Device.sequelize.fn(
    'DATE_FORMAT',  // MySQL 风格
    Device.sequelize.col('purchase_date'),
    '%Y-%m'
  ),
  'period'
]
```

### 方案 2: 在应用层分组
在获取数据后在 JavaScript 中进行日期分组。

### 方案 3: 修复测试期望
如果功能实际正常，调整测试期望值。

## 优先级
中

## 预计工作量
1 小时

## 相关文件
- `/src/backend/src/controllers/reportController.js`
- `/tests/backend/report.test.js`

## 创建时间
2026-03-21 23:55 GMT+8
