# Development 智能体知识库

## 角色定位

Development（开发工程师）负责：
- 根据设计文档编写代码
- 实现业务逻辑
- 编写可维护、可测试的代码
- 遵循编码规范

---

## 编码规范

### 命名规范

**变量命名：**
- 小驼峰：`userName`, `deviceList`
- 常量：`MAX_SIZE`, `DEFAULT_PAGE`

**函数命名：**
- 动词开头：`getUser`, `createDevice`, `updateStatus`

**类命名：**
- 大驼峰：`UserController`, `DeviceService`

### 代码结构

**后端：**
```
src/
├── controllers/     # 控制器
├── services/        # 业务逻辑
├── models/          # 数据模型
├── routes/          # 路由定义
└── app.js           # 入口
```

**前端：**
```
src/
├── views/           # 页面组件
├── components/      # 公共组件
├── api/             # API 封装
├── store/           # 状态管理
└── main.js          # 入口
```

---

## 代码质量标准

### 函数标准
- 单一职责：一个函数只做一件事
- 长度限制：不超过 50 行
- 参数限制：不超过 4 个

### 错误处理
```javascript
try {
  const result = await riskyOperation();
  return { success: true, data: result };
} catch (error) {
  console.error('Failed:', error);
  return { success: false, error: error.message };
}
```

---

## 常用代码模板

### CRUD 控制器
```javascript
// 列表
exports.getList = async (req, res) => {
  const { page = 1, pageSize = 10 } = req.query;
  const result = await Service.getList({ page, pageSize });
  res.json({ code: 0, data: result });
};

// 创建
exports.create = async (req, res) => {
  const data = await Service.create(req.body);
  res.json({ code: 0, data });
};

// 更新
exports.update = async (req, res) => {
  const data = await Service.update(req.params.id, req.body);
  res.json({ code: 0, data });
};

// 删除
exports.delete = async (req, res) => {
  await Service.delete(req.params.id);
  res.json({ code: 0 });
};
```

### 前端 API 封装
```javascript
import request from '@/utils/request';

export default {
  getList(params) { return request.get('/api/resources', { params }); },
  getDetail(id) { return request.get(`/api/resources/${id}`); },
  create(data) { return request.post('/api/resources', data); },
  update(id, data) { return request.put(`/api/resources/${id}`, data); },
  delete(id) { return request.delete(`/api/resources/${id}`); }
};
```

---

## 安全编码

- **SQL 注入防护**：使用参数化查询
- **XSS 防护**：输出时转义
- **密码加密**：bcrypt
- **敏感信息**：日志脱敏

---

## 检查清单

- [ ] 代码编译通过
- [ ] 无语法错误
- [ ] 遵循编码规范
- [ ] 有适当注释
- [ ] 错误处理完善
- [ ] 安全检查通过

---

**相关文件**
- 提示词：`prompts/development/system.md`
- 检查清单：`knowledge/checklists/development-checklist.md`