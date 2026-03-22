# 测试文档 - 设备管理系统

## 📁 测试目录结构

```
tests/
├── backend/                    # 后端测试
│   ├── jest.config.js         # Jest 配置文件
│   ├── setup.js               # 测试环境设置
│   ├── deviceController.test.js  # 控制器测试
│   ├── deviceRoutes.test.js      # API 路由测试
│   └── deviceModel.test.js       # 数据模型测试
├── frontend/                   # 前端测试
│   ├── vitest.config.js       # Vitest 配置文件
│   ├── setup.js               # 测试环境设置
│   ├── deviceApi.test.js      # API 层测试
│   ├── deviceStore.test.js    # Pinia Store 测试
│   └── router.test.js         # 路由配置测试
└── package.json               # 测试依赖配置
```

## 🚀 运行测试

### 安装依赖

```bash
cd output/tests
npm install
```

### 运行所有测试

```bash
# 运行后端和前端所有测试
npm test

# 仅运行后端测试
npm run test:backend

# 仅运行前端测试
npm run test:frontend
```

### 监听模式

```bash
# 后端监听模式
npm run test:backend:watch

# 前端监听模式
npm run test:frontend:watch
```

### 生成覆盖率报告

```bash
# 后端覆盖率
npm run test:backend:coverage

# 前端覆盖率
npm run test:frontend:coverage
```

### 运行特定测试

```bash
# 仅运行 API 路由测试
npm run test:api

# 仅运行控制器测试
npm run test:controller

# 仅运行模型测试
npm run test:model
```

## 📊 测试覆盖率

### 后端覆盖率目标
- 语句覆盖率：≥ 70%
- 分支覆盖率：≥ 70%
- 函数覆盖率：≥ 70%
- 行覆盖率：≥ 70%

### 前端覆盖率目标
- 语句覆盖率：≥ 70%
- 分支覆盖率：≥ 70%
- 函数覆盖率：≥ 70%
- 行覆盖率：≥ 70%

## 🧪 测试用例说明

### 后端测试

#### 1. Device Controller 测试 (`deviceController.test.js`)
测试 `deviceController.js` 中的所有方法：

- **getDevices**
  - ✅ 返回空列表
  - ✅ 返回设备列表
  - ✅ 关键词搜索
  - ✅ 按设备类型筛选
  - ✅ 分页功能
  - ✅ 错误处理

- **getDeviceById**
  - ✅ 返回设备详情
  - ✅ 404 错误处理

- **createDevice**
  - ✅ 成功创建设备
  - ✅ 拒绝重复设备编号
  - ✅ 错误处理

- **updateDevice**
  - ✅ 成功更新设备
  - ✅ 404 错误处理
  - ✅ 不允许修改 device_id

- **deleteDevice**
  - ✅ 成功删除设备
  - ✅ 404 错误处理

#### 2. Device Routes 测试 (`deviceRoutes.test.js`)
使用 `supertest` 进行 HTTP 请求测试：

- **GET /api/devices**
  - ✅ 返回 200 和空列表
  - ✅ 返回设备列表
  - ✅ 分页参数
  - ✅ 关键词搜索
  - ✅ 按状态筛选

- **POST /api/devices**
  - ✅ 成功创建设备
  - ✅ 拒绝重复编号
  - ✅ 验证必填字段

- **GET /api/devices/:id**
  - ✅ 返回设备详情
  - ✅ 404 错误

- **PUT /api/devices/:id**
  - ✅ 成功更新
  - ✅ 404 错误
  - ✅ 忽略 device_id 修改

- **DELETE /api/devices/:id**
  - ✅ 成功删除
  - ✅ 404 错误

- **错误处理**
  - ✅ JSON 解析错误
  - ✅ 未定义路由

#### 3. Device Model 测试 (`deviceModel.test.js`)
测试 Sequelize 模型定义和数据库操作：

- **模型定义**
  - ✅ 正确的模型定义
  - ✅ 字段定义验证

- **必填字段验证**
  - ✅ device_id
  - ✅ device_name
  - ✅ device_type
  - ✅ purchase_date
  - ✅ department
  - ✅ user_name
  - ✅ status

- **可选字段**
  - ✅ specification
  - ✅ location
  - ✅ remark

- **默认值**
  - ✅ status 默认值 "闲置"

- **CRUD 操作**
  - ✅ Create
  - ✅ Read
  - ✅ Update
  - ✅ Delete

- **查询方法**
  - ✅ findAndCountAll 分页
  - ✅ where 条件查询
  - ✅ 排序

- **数据完整性**
  - ✅ 主键唯一性
  - ✅ 日期格式
  - ✅ 状态值验证

### 前端测试

#### 1. Device API 测试 (`deviceApi.test.js`)
测试前端 API 层：

- **getDeviceList**
  - ✅ 正确的 API 端点
  - ✅ 查询参数支持
  - ✅ 返回数据格式
  - ✅ 错误处理

- **getDeviceDetail**
  - ✅ 正确的 API 端点
  - ✅ 返回详情数据
  - ✅ 404 错误处理

- **createDevice**
  - ✅ 正确的 API 端点
  - ✅ 返回创建结果
  - ✅ 重复编号错误

- **updateDevice**
  - ✅ 正确的 API 端点
  - ✅ 返回更新结果
  - ✅ 404 错误处理

- **deleteDevice**
  - ✅ 正确的 API 端点
  - ✅ 返回删除结果
  - ✅ 404 错误处理

#### 2. Device Store 测试 (`deviceStore.test.js`)
测试 Pinia Store：

- **初始化**
  - ✅ Store 正确初始化
  - ✅ deviceTypes 存在
  - ✅ deviceStatuses 存在

- **设备类型**
  - ✅ 默认类型列表
  - ✅ 响应式更新
  - ✅ 过滤功能

- **设备状态**
  - ✅ 默认状态列表
  - ✅ 响应式更新
  - ✅ 过滤功能

- **数据验证**
  - ✅ 类型都是字符串
  - ✅ 状态都是字符串
  - ✅ 无重复值

#### 3. Router 测试 (`router.test.js`)
测试 Vue Router 配置：

- **路由定义**
  - ✅ 首页路由
  - ✅ 新增设备路由
  - ✅ 编辑设备路由
  - ✅ 设备详情路由

- **路由导航**
  - ✅ 导航到首页
  - ✅ 导航到新增页面
  - ✅ 导航到编辑页面
  - ✅ 导航到详情页面

- **路由参数**
  - ✅ id 参数传递
  - ✅ 参数类型验证

- **懒加载**
  - ✅ 组件懒加载配置

- **历史记录**
  - ✅ 后退功能
  - ✅ 前进功能
  - ✅ replace 功能

## 🔧 测试工具

### 后端测试工具
- **Jest**: 测试框架
- **Supertest**: HTTP 请求测试
- **Sequelize**: 数据库 ORM
- **SQLite3**: 测试数据库

### 前端测试工具
- **Vitest**: 测试框架（Vite 原生）
- **@vue/test-utils**: Vue 组件测试工具
- **jsdom**: 浏览器环境模拟
- **Pinia**: 状态管理测试

## 📝 编写新测试

### 后端测试模板

```javascript
const Device = require('../../backend/models/Device');
const deviceController = require('../../backend/src/controllers/deviceController');

describe('New Feature Tests', () => {
  beforeEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  afterEach(async () => {
    await Device.destroy({ where: {}, truncate: true });
  });

  test('应该测试新功能', async () => {
    // 测试代码
  });
});
```

### 前端测试模板

```javascript
import { setActivePinia, createPinia } from 'pinia';
import { useDeviceStore } from '@/store/device';

describe('New Feature Tests', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDeviceStore();
  });

  test('应该测试新功能', () => {
    // 测试代码
  });
});
```

## 🐛 常见问题

### 1. 测试数据库无法创建
**解决方案**: 确保 `database/` 目录存在且有写权限

```bash
mkdir -p output/database
chmod 755 output/database
```

### 2. 前端测试导入错误
**解决方案**: 检查 `vitest.config.js` 中的路径别名配置

```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, '../src/frontend/src')
  }
}
```

### 3. 测试超时
**解决方案**: 增加超时时间或在 `jest.config.js` / `vitest.config.js` 中调整

```javascript
testTimeout: 10000 // 10 秒
```

## 📈 持续改进

- [ ] 添加前端组件测试（DeviceList.vue, DeviceNew.vue 等）
- [ ] 添加 E2E 测试（使用 Playwright 或 Cypress）
- [ ] 添加性能测试
- [ ] 集成 CI/CD 自动化测试
- [ ] 添加测试覆盖率门禁

## 📚 参考资源

- [Jest 官方文档](https://jestjs.io/)
- [Vitest 官方文档](https://vitest.dev/)
- [Vue Test Utils 官方文档](https://test-utils.vuejs.org/)
- [Supertest 官方文档](https://github.com/ladjs/supertest)
- [Sequelize 官方文档](https://sequelize.org/)
