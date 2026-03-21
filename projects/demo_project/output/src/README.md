# 设备管理系统

一个基于 Vue 3 + Node.js + SQLite 的设备管理系统，支持设备的增删改查和搜索筛选功能。

## 技术栈

### 后端
- Node.js + Express
- SQLite 数据库
- Sequelize ORM

### 前端
- Vue 3 + Vite
- Element Plus UI 组件库
- Vue Router 路由
- Pinia 状态管理
- Axios HTTP 客户端

## 项目结构

```
output/src/
├── backend/                 # 后端项目
│   ├── src/
│   │   ├── controllers/    # 控制器
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # 路由
│   │   ├── config/         # 配置
│   │   └── app.js          # 应用入口
│   ├── database/
│   │   └── schema.sql      # 数据库脚本
│   └── package.json
│
└── frontend/               # 前端项目
    ├── src/
    │   ├── api/           # API 接口
    │   ├── views/         # 页面组件
    │   ├── router/        # 路由配置
    │   ├── store/         # 状态管理
    │   ├── utils/         # 工具函数
    │   ├── App.vue
    │   └── main.js
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 安装依赖
npm install

# 启动服务（默认端口 3000）
npm start
```

### 2. 启动前端（开发模式）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认端口 5173）
npm run dev
```

### 3. 访问系统

浏览器打开：http://localhost:5173

## API 接口

### 获取设备列表
```
GET /api/devices
参数：keyword, device_type, status, department, page, pageSize
```

### 获取设备详情
```
GET /api/devices/:id
```

### 新增设备
```
POST /api/devices
Body: { device_id, device_name, device_type, ... }
```

### 更新设备
```
PUT /api/devices/:id
Body: { device_name, status, ... }
```

### 删除设备
```
DELETE /api/devices/:id
```

## 设备字段

| 字段 | 类型 | 说明 |
|------|------|------|
| device_id | VARCHAR(50) | 设备编号（主键） |
| device_name | VARCHAR(100) | 设备名称 |
| device_type | VARCHAR(50) | 设备类型 |
| specification | VARCHAR(200) | 规格型号 |
| purchase_date | DATE | 购买日期 |
| department | VARCHAR(100) | 使用部门 |
| user_name | VARCHAR(50) | 使用人 |
| status | VARCHAR(20) | 设备状态（在用/闲置/报废） |
| location | VARCHAR(200) | 存放位置 |
| remark | TEXT | 备注 |

## 功能特性

- ✅ 设备列表展示
- ✅ 新增设备
- ✅ 编辑设备
- ✅ 删除设备
- ✅ 设备详情查看
- ✅ 关键词搜索（设备名称/编号）
- ✅ 多条件筛选（类型/状态/部门）
- ✅ 分页功能
- ✅ 响应式布局

## 开发说明

### 后端开发
- 修改代码后自动重启：`npm run dev`
- 数据库文件：`backend/database/device.db`

### 前端开发
- 热重载开发：`npm run dev`
- 构建生产版本：`npm run build`

## 注意事项

1. 首次运行需要安装前后端依赖
2. 后端服务必须先启动
3. 设备编号必须唯一
4. 开发环境使用 SQLite，生产环境可切换到 MySQL
