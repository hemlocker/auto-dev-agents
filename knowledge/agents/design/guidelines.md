# Design 智能体知识库

## 角色定位

Design（架构师）负责：
- 系统架构设计
- 技术选型
- 数据库设计
- API 接口定义
- 前端设计

---

## 架构设计原则

### SOLID 原则
- **S**ingle Responsibility - 单一职责
- **O**pen/Closed - 开闭原则
- **L**iskov Substitution - 里氏替换
- **I**nterface Segregation - 接口隔离
- **D**ependency Inversion - 依赖倒置

### 设计原则
1. **KISS** - Keep It Simple, Stupid
2. **DRY** - Don't Repeat Yourself
3. **YAGNI** - You Aren't Gonna Need It
4. **高内聚，低耦合**

---

## 架构风格选择

| 场景 | 推荐架构 | 理由 |
|------|----------|------|
| 小型项目 | 单体架构 | 简单、部署方便 |
| 中型项目 | 分层架构 | 职责清晰 |
| 大型项目 | 微服务 | 可扩展、独立部署 |
| 高并发 | 事件驱动 | 异步处理 |

---

## 技术栈推荐

### 后端技术栈

| 类型 | 简单项目 | 中型项目 | 大型项目 |
|------|----------|----------|----------|
| 语言 | Node.js/Python | Node.js/Java/Go | Java/Go |
| 框架 | Express/FastAPI | NestJS/Spring | Spring Boot |
| 数据库 | SQLite/MySQL | MySQL/PostgreSQL | PostgreSQL + Redis |
| ORM | Sequelize/Prisma | Prisma/TypeORM | MyBatis/JPA |

### 前端技术栈

| 类型 | 简单项目 | 中型项目 | 大型项目 |
|------|----------|----------|----------|
| 框架 | Vue 3 | Vue 3/React | React/Next.js |
| UI 库 | Element Plus | Element Plus/Ant Design | Ant Design |
| 状态管理 | Pinia | Pinia/Redux | Redux/Zustand |
| 构建 | Vite | Vite | Next.js/Vite |

---

## 数据库设计规范

### 表命名
- 使用小写字母和下划线
- 使用单数形式：`user`, `device`, `order`
- 关联表：`user_role`, `order_item`

### 字段命名
- 主键：`id` (自增) 或 `uuid`
- 外键：`{table}_id`
- 时间：`created_at`, `updated_at`
- 状态：`status`, `is_active`

### 索引设计
- 主键自动索引
- 外键建立索引
- 常用查询字段建立索引
- 组合索引注意顺序

---

## API 设计规范

### RESTful API

| 操作 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 列表 | GET | /api/resources | 分页列表 |
| 详情 | GET | /api/resources/:id | 单条记录 |
| 创建 | POST | /api/resources | 新增 |
| 更新 | PUT | /api/resources/:id | 全量更新 |
| 部分更新 | PATCH | /api/resources/:id | 部分更新 |
| 删除 | DELETE | /api/resources/:id | 删除 |

### 响应格式

**成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**列表响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [...],
    "total": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

**错误响应：**
```json
{
  "code": 40001,
  "message": "参数错误",
  "data": null
}
```

---

## 设计文档模板

### 架构设计文档结构

```markdown
# 系统架构设计

## 1. 项目概述
- 项目背景
- 项目目标
- 功能范围

## 2. 架构设计
- 架构风格
- 系统架构图
- 组件说明

## 3. 技术选型
- 后端技术栈
- 前端技术栈
- 数据库
- 中间件

## 4. 数据库设计
- ER 图
- 表结构
- 索引设计

## 5. API 接口设计
- 接口列表
- 接口详情

## 6. 前端设计
- 页面列表
- 页面原型
- 组件结构

## 7. 非功能需求
- 性能要求
- 安全要求
- 可用性要求
```

---

## 常见设计模式

### 创建型模式
- 工厂模式 - 对象创建
- 单例模式 - 全局唯一实例
- 建造者模式 - 复杂对象构建

### 结构型模式
- 适配器模式 - 接口转换
- 装饰器模式 - 功能增强
- 代理模式 - 访问控制

### 行为型模式
- 策略模式 - 算法切换
- 观察者模式 - 事件通知
- 责任链模式 - 请求处理

---

## 检查清单

设计完成后必须检查：
- [ ] 覆盖所有需求
- [ ] 技术选型合理
- [ ] 数据库设计规范
- [ ] API 设计符合 RESTful
- [ ] 考虑非功能需求
- [ ] 有架构图说明
- [ ] 有开发计划

---

## 相关文件

- 提示词：`prompts/design/system.md`
- 检查清单：`knowledge/checklists/design-checklist.md`