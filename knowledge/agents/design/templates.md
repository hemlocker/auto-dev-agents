# 设计文档模板

## 架构设计文档模板

```markdown
# 系统架构设计文档

**项目名称**: {项目名称}  
**版本**: 1.0  
**日期**: {YYYY-MM-DD}

---

## 1. 架构概述

### 1.1 设计目标
{系统要达成的目标}

### 1.2 架构风格
{选择的架构风格及原因}

### 1.3 技术选型
| 层次 | 技术选型 | 版本 | 理由 |
|------|----------|------|------|
| 前端 | Vue 3 | 3.4 | 响应式、组件化 |
| 后端 | Spring Boot | 3.2 | 成熟稳定 |
| 数据库 | MySQL | 8.0 | 关系型数据库 |

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────┐
│                   用户界面                    │
├─────────────────────────────────────────────┤
│           Nginx (负载均衡 + 反向代理)           │
├──────────────────┬──────────────────────────┤
│     前端 Vue 3    │     后端 Spring Boot     │
├──────────────────┴──────────────────────────┤
│              Redis (缓存)                    │
├─────────────────────────────────────────────┤
│              MySQL (数据库)                  │
└─────────────────────────────────────────────┘
```

---

## 3. 模块设计

### 3.1 模块划分
| 模块名称 | 职责 | 依赖 |
|----------|------|------|
| 用户模块 | 用户认证授权 | - |
| 设备模块 | 设备信息管理 | 用户模块 |

### 3.2 模块交互
{模块之间的调用关系}

---

## 4. 数据架构

### 4.1 数据库设计
{ER 图或表结构}

### 4.2 数据字典
{详细字段定义}

### 4.3 数据流
{数据流转过程}

---

## 5. 接口设计

### 5.1 API 列表
| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 登录 | POST | /api/auth/login | 用户登录 |
| 设备列表 | GET | /api/devices | 获取设备列表 |

### 5.2 接口规范
{详细接口定义}

---

## 6. 安全设计

### 6.1 认证授权
{认证方式、权限模型}

### 6.2 数据安全
{加密、脱敏策略}

---

## 7. 部署架构

### 7.1 部署拓扑
{部署架构图}

### 7.2 环境配置
{各环境配置说明}
```

---

## 详细设计文档模板

```markdown
# 详细设计文档

## 模块: {模块名称}

---

## 1. 模块概述

### 1.1 功能描述
{模块功能说明}

### 1.2 设计目标
{要达成的目标}

---

## 2. 类设计

### 2.1 类图
```
┌─────────────────┐
│   DeviceService │
├─────────────────┤
│ - repository    │
├─────────────────┤
│ + create()      │
│ + update()      │
│ + delete()      │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ DeviceRepository│
├─────────────────┤
│ + save()        │
│ + findById()    │
└─────────────────┘
```

### 2.2 类职责
| 类名 | 职责 |
|------|------|
| DeviceService | 设备业务逻辑处理 |
| DeviceRepository | 设备数据访问 |

---

## 3. 接口设计

### 3.1 Service 接口
```java
public interface DeviceService {
    DeviceVO create(DeviceCreateDTO dto);
    DeviceVO update(Long id, DeviceUpdateDTO dto);
    void delete(Long id);
    Page<DeviceVO> list(DeviceQueryDTO query);
}
```

### 3.2 API 接口
```java
@RestController
@RequestMapping("/api/devices")
public class DeviceController {
    @PostMapping
    public ApiResponse<DeviceVO> create(@RequestBody DeviceCreateDTO dto);
    
    @GetMapping("/{id}")
    public ApiResponse<DeviceVO> getById(@PathVariable Long id);
}
```

---

## 4. 数据结构

### 4.1 DTO 定义
```java
@Data
public class DeviceCreateDTO {
    @NotBlank
    private String deviceCode;
    
    @NotBlank
    private String deviceName;
    
    @NotNull
    private Long typeId;
}
```

### 4.2 Entity 定义
```java
@Data
@Entity
@Table(name = "device")
public class Device {
    @Id
    @GeneratedValue(strategy = IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String deviceCode;
    
    @Column(nullable = false)
    private String deviceName;
}
```

---

## 5. 业务流程

### 5.1 流程图
```
开始 → 参数校验 → 业务检查 → 数据处理 → 保存 → 返回结果
         │           │
         ▼           ▼
      校验失败    业务异常
```

### 5.2 流程说明
1. 参数校验: 验证输入参数合法性
2. 业务检查: 检查业务规则约束
3. 数据处理: 转换数据格式
4. 保存: 持久化数据
5. 返回: 返回处理结果

---

## 6. 异常处理

| 异常类型 | 触发条件 | 处理方式 |
|----------|----------|----------|
| BusinessException | 业务规则违反 | 返回错误信息 |
| ResourceNotFoundException | 资源不存在 | 返回 404 |

---

## 7. 测试要点

### 7.1 单元测试
- 正常流程测试
- 异常流程测试
- 边界条件测试

### 7.2 集成测试
- 接口联调测试
- 数据库交互测试
```

---

## 数据库设计模板

```markdown
# 数据库设计文档

## 1. 数据库概述

### 1.1 数据库选型
{选择的数据库及理由}

### 1.2 命名规范
- 表名: 小写下划线，如 `device_info`
- 字段名: 小写下划线，如 `device_code`
- 索引名: `idx_` 前缀，如 `idx_device_code`

---

## 2. ER 图

{实体关系图}

---

## 3. 表结构

### 3.1 设备表 (device)

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | BIGINT | 是 | AUTO | 主键 |
| device_code | VARCHAR(50) | 是 | - | 设备编号 |
| device_name | VARCHAR(100) | 是 | - | 设备名称 |
| created_at | DATETIME | 是 | NOW() | 创建时间 |

**索引:**
- PRIMARY KEY (id)
- UNIQUE KEY uk_device_code (device_code)
- KEY idx_created_at (created_at)

---

## 4. 数据字典

### 4.1 枚举值定义

**设备状态:**
| 值 | 名称 | 说明 |
|----|------|------|
| 1 | 在用 | 设备正在使用 |
| 2 | 闲置 | 设备未使用 |
| 3 | 维修 | 设备维修中 |
| 4 | 报废 | 设备已报废 |

---

## 5. 初始化脚本

```sql
CREATE DATABASE IF NOT EXISTS `device_management`;
USE `device_management`;

CREATE TABLE `device` (
  -- 表结构...
);

-- 初始化数据
INSERT INTO `device_type` VALUES (1, '服务器', 'SERVER');
INSERT INTO `device_status` VALUES (1, '在用', 'IN_USE');
```
```

---

## API 接口文档模板

```markdown
# API 接口文档

## 基础信息

- **Base URL**: `https://api.example.com`
- **认证方式**: Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON

---

## 通用响应格式

### 成功响应
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

### 错误响应
```json
{
  "code": 40001,
  "message": "参数错误",
  "data": null
}
```

---

## 接口列表

### 1. 用户登录

**POST** `/api/auth/login`

**请求参数:**
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例:**
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 7200
  }
}
```

---

### 2. 获取设备列表

**GET** `/api/devices`

**请求参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认10 |

**响应示例:**
```json
{
  "code": 0,
  "data": {
    "list": [
      {"id": 1, "name": "设备1"},
      {"id": 2, "name": "设备2"}
    ],
    "total": 100
  }
}
```
```