# 编码规范

## 命名规范

### 变量命名
- **小驼峰**：`userName`, `deviceList`, `totalCount`
- **常量**：全大写下划线 `MAX_SIZE`, `DEFAULT_PAGE_SIZE`
- **私有变量**：下划线前缀 `_privateVar`

### 函数命名
- **动词开头**：`getUser()`, `createDevice()`, `updateStatus()`
- **布尔返回**：`is*`, `has*`, `can*` → `isValid()`, `hasPermission()`
- **事件处理**：`on*`, `handle*` → `onClick()`, `handleSubmit()`

### 类命名
- **大驼峰**：`UserController`, `DeviceService`, `OrderRepository`
- **接口**：`I` 前缀或 `able` 后缀 → `IUserService`, `Serializable`
- **抽象类**：`Abstract` 前缀 → `AbstractHandler`

### 文件命名
- **类文件**：与类名一致 `UserService.java`
- **组件文件**：大驼峰 `DeviceList.vue`
- **工具文件**：小写 `utils.js`, `helpers.ts`

---

## 代码结构

### Java 后端结构
```
src/main/java/com/example/app/
├── config/          # 配置类
│   ├── SecurityConfig.java
│   └── RedisConfig.java
├── controller/      # 控制器层
├── service/         # 业务逻辑层
│   └── impl/        # 实现类
├── repository/      # 数据访问层
├── entity/          # 实体类
├── dto/             # 数据传输对象
├── vo/              # 视图对象
├── enums/           # 枚举类
├── exception/       # 异常处理
├── response/        # 响应封装
└── util/            # 工具类
```

### Vue 前端结构
```
src/
├── api/             # API 封装
├── components/      # 公共组件
│   ├── common/      # 通用组件
│   └── business/    # 业务组件
├── views/           # 页面视图
├── store/           # 状态管理
├── router/          # 路由配置
├── utils/           # 工具函数
└── types/           # 类型定义
```

---

## 代码质量标准

### 函数标准
- **单一职责**：一个函数只做一件事
- **长度限制**：不超过 50 行
- **参数限制**：不超过 4 个参数
- **嵌套深度**：不超过 3 层

### 注释规范

**Java:**
```java
/**
 * 创建新设备
 * @param dto 设备创建请求
 * @return 创建的设备信息
 * @throws BusinessException 当设备编号重复时抛出
 */
public DeviceVO create(DeviceCreateDTO dto) {
    // 实现...
}
```

**TypeScript:**
```typescript
/**
 * 创建新设备
 * @param dto - 设备创建请求
 * @returns 创建的设备信息
 */
async create(dto: DeviceCreateDTO): Promise<DeviceVO> {
  // 实现...
}
```

---

## 错误处理

### Java 异常处理
```java
try {
    Device device = deviceRepository.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("设备不存在"));
    return device;
} catch (BusinessException e) {
    log.error("业务异常: {}", e.getMessage());
    throw e;
} catch (Exception e) {
    log.error("系统异常", e);
    throw new SystemException("系统繁忙，请稍后重试");
}
```

### TypeScript 错误处理
```typescript
try {
  const response = await api.createDevice(dto);
  return response.data;
} catch (error) {
  if (error instanceof AxiosError) {
    message.error(error.response?.data?.message || '请求失败');
  } else {
    message.error('系统错误');
  }
  throw error;
}
```

---

## 日志规范

### 日志级别
- **ERROR**: 错误信息，需要立即处理
- **WARN**: 警告信息，可能存在问题
- **INFO**: 重要业务信息
- **DEBUG**: 调试信息

### 日志格式
```java
// 推荐：结构化日志
log.info("设备创建成功, deviceId={}, deviceCode={}", device.getId(), device.getDeviceCode());

// 避免：字符串拼接
log.info("设备创建成功: " + device.toString());
```

---

## 安全编码

### SQL 注入防护
```java
// ✅ 正确：参数化查询
@Query("SELECT d FROM Device d WHERE d.deviceCode = :code")
Device findByDeviceCode(@Param("code") String code);

// ❌ 错误：字符串拼接
String sql = "SELECT * FROM device WHERE code = '" + code + "'";
```

### XSS 防护
```java
// 输出时转义
String safeContent = HtmlUtils.htmlEscape(userInput);
```

### 敏感信息处理
```java
// 日志脱敏
log.info("用户登录, phone={}", maskPhone(phone));

private String maskPhone(String phone) {
    return phone.substring(0, 3) + "****" + phone.substring(7);
}
```

---

## 代码审查清单

- [ ] 代码编译通过
- [ ] 无语法错误和警告
- [ ] 遵循命名规范
- [ ] 函数长度适中
- [ ] 有适当注释
- [ ] 错误处理完善
- [ ] 无安全漏洞
- [ ] 日志记录合理