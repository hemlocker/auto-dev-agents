# 架构设计知识库

## 架构设计原则

### SOLID 原则

| 原则 | 含义 | 应用示例 |
|------|------|----------|
| **S**RP | 单一职责 | 一个类只负责一个功能 |
| **O**CP | 开闭原则 | 对扩展开放，对修改关闭 |
| **L**SP | 里氏替换 | 子类可替换父类 |
| **ISP | 接口隔离 | 接口要小而专一 |
| **D**IP | 依赖倒置 | 依赖抽象不依赖具体 |

### 其他原则

```
KISS - Keep It Simple, Stupid
DRY - Don't Repeat Yourself
YAGNI - You Aren't Gonna Need It
高内聚，低耦合
```

---

## 架构风格选择

| 架构风格 | 适用场景 | 优点 | 缺点 |
|----------|----------|------|------|
| **单体架构** | 小型项目 | 简单、易部署 | 扩展性差 |
| **分层架构** | 中型项目 | 职责清晰 | 性能开销 |
| **微服务** | 大型项目 | 可扩展、独立部署 | 复杂度高 |
| **事件驱动** | 高并发 | 异步处理 | 调试困难 |

---

## 技术选型指南

### 后端技术栈

| 项目规模 | 语言 | 框架 | 数据库 |
|----------|------|------|--------|
| 小型 | Node.js/Python | Express/FastAPI | MySQL |
| 中型 | Java/Go | Spring Boot/Gin | MySQL+Redis |
| 大型 | Java/Go | Spring Cloud | PostgreSQL+Redis+ES |

### 前端技术栈

| 项目规模 | 框架 | UI库 | 状态管理 |
|----------|------|------|----------|
| 小型 | Vue 3 | Element Plus | Pinia |
| 中型 | Vue 3/React | Ant Design | Pinia/Redux |
| 大型 | React | Ant Design Pro | Redux Toolkit |

---

## 数据库设计

### 设计原则

```sql
1. 范式设计
   - 第一范式: 字段不可分割
   - 第二范式: 完全依赖主键
   - 第三范式: 消除传递依赖

2. 反范式优化
   - 适当冗余减少 JOIN
   - 空间换时间

3. 索引设计
   - 主键索引
   - 唯一索引
   - 组合索引
   - 注意索引选择性
```

### 表设计模板

```sql
CREATE TABLE `device` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `device_code` VARCHAR(50) NOT NULL COMMENT '设备编号',
  `device_name` VARCHAR(100) NOT NULL COMMENT '设备名称',
  `device_type_id` BIGINT NOT NULL COMMENT '设备类型ID',
  `device_status_id` BIGINT NOT NULL COMMENT '设备状态ID',
  `department_id` BIGINT COMMENT '所属部门ID',
  `user_id` BIGINT COMMENT '使用人ID',
  `purchase_date` DATE COMMENT '购买日期',
  `description` TEXT COMMENT '描述',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除标志',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_code` (`device_code`),
  KEY `idx_device_type` (`device_type_id`),
  KEY `idx_device_status` (`device_status_id`),
  KEY `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';
```

---

## API 设计规范

### RESTful API 设计

```
GET    /api/devices        # 获取设备列表
GET    /api/devices/{id}   # 获取设备详情
POST   /api/devices        # 创建设备
PUT    /api/devices/{id}   # 更新设备（全量）
PATCH  /api/devices/{id}   # 更新设备（部分）
DELETE /api/devices/{id}   # 删除设备
GET    /api/devices/statistics # 设备统计
```

### 响应格式

```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "设备名称"
  }
}

// 分页响应
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "size": 10
  }
}

// 错误响应
{
  "code": 40001,
  "message": "设备不存在",
  "data": null
}
```

---

## 接口文档模板

```markdown
## 接口: 获取设备列表

### 基本信息
- **URL**: `/api/devices`
- **Method**: `GET`
- **认证**: Bearer Token

### 请求参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认10 |
| keyword | string | 否 | 搜索关键词 |
| typeId | long | 否 | 设备类型ID |

### 响应示例
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [...],
    "total": 100
  }
}
```

### 错误码
| 错误码 | 说明 |
|--------|------|
| 40001 | 参数错误 |
| 50001 | 系统错误 |
```

---

## 安全设计

### 认证授权

```
1. 认证方式
   - JWT Token
   - OAuth 2.0
   - Session

2. 权限控制
   - RBAC (基于角色)
   - ABAC (基于属性)

3. 安全措施
   - HTTPS
   - XSS 防护
   - CSRF 防护
   - SQL 注入防护
```

---

## 架构设计检查清单

- [ ] 架构风格选择合理
- [ ] 技术选型有依据
- [ ] 数据库设计规范
- [ ] API 设计符合 RESTful
- [ ] 安全措施完备
- [ ] 可扩展性考虑
- [ ] 高可用设计