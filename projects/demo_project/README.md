# Demo Project

基于 NestJS + React 的企业级数据管理与服务平台。

## 技术栈

### 后端
- **框架:** NestJS 10+
- **语言:** Node.js 20+ / TypeScript
- **数据库:** MySQL 8.0
- **缓存:** Redis 7.0
- **搜索引擎:** Elasticsearch 8.x
- **对象存储:** AWS S3 / 阿里云 OSS
- **认证:** JWT + Refresh Token

### 前端
- **框架:** React 18+
- **状态管理:** Redux Toolkit
- **UI 组件:** Ant Design 5.x
- **构建工具:** Vite
- **HTTP 客户端:** Axios

## 项目结构

```
demo_project/
├── output/
│   ├── design/          # 设计文档
│   │   ├── architecture_design.md
│   │   └── detailed_design.md
│   └── src/             # 源代码
│       ├── backend/     # NestJS 后端
│       │   ├── src/
│       │   │   ├── auth/        # 认证模块
│       │   │   ├── search/      # 搜索模块
│       │   │   ├── export/      # 导出模块
│       │   │   ├── notify/      # 通知模块
│       │   │   ├── user/        # 用户模块
│       │   │   ├── config/      # 配置
│       │   │   ├── common/      # 公共组件
│       │   │   └── database/    # 数据库实体
│       │   ├── package.json
│       │   └── tsconfig.json
│       └── frontend/    # React 前端
│           ├── src/
│           │   ├── components/  # 组件
│           │   ├── pages/       # 页面
│           │   ├── store/       # Redux
│           │   ├── services/    # API 服务
│           │   └── hooks/       # 自定义 Hooks
│           ├── package.json
│           └── vite.config.ts
```

## 快速开始

### 后端

```bash
cd output/src/backend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息

# 启动开发服务器
npm run start:dev

# 构建生产版本
npm run build
npm run start:prod
```

### 前端

```bash
cd output/src/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## API 文档

启动后端后，访问 http://localhost:3000/docs 查看 Swagger API 文档。

## 核心功能

### 1. 认证模块 (Auth)
- 用户登录/注册
- JWT 令牌认证
- 刷新令牌
- 账号锁定机制

### 2. 搜索模块 (Search)
- 全文搜索
- 多条件筛选
- 搜索结果分页
- 关键词高亮

### 3. 导出模块 (Export)
- CSV/Excel 格式导出
- 同步/异步模式
- 导出任务管理

### 4. 通知模块 (Notify)
- 站内消息
- 邮件通知
- 短信通知
- 通知偏好设置

### 5. 用户模块 (User)
- 个人资料管理
- 头像上传
- 登录历史

## 数据库设计

主要数据表：
- `users` - 用户表
- `user_profiles` - 用户资料表
- `user_accounts` - 第三方账号表
- `login_logs` - 登录日志表
- `notifications` - 通知表
- `notification_settings` - 通知设置表
- `export_tasks` - 导出任务表

## 环境变量

### 后端 (.env)
```bash
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=demo_project

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Elasticsearch
ES_NODE=http://localhost:9200

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=24h
JWT_REFRESH_EXPIRES_IN=7d

# OSS
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your-access-key
OSS_ACCESS_KEY_SECRET=your-secret-key
OSS_BUCKET=demo-project
```

## 安全特性

- 密码 bcrypt 加密存储
- JWT 令牌认证
- 防 SQL 注入（参数化查询）
- 防 XSS 攻击（输入过滤）
- 账号锁定机制（5 次失败锁定 30 分钟）
- HTTPS 加密通信

## 性能优化

- Redis 缓存热点数据
- Elasticsearch 全文搜索
- 异步导出任务处理
- 数据库索引优化
- 分页查询

## License

MIT
