# 最佳实践

## 代码设计原则

### SOLID 原则

| 原则 | 含义 | 示例 |
|------|------|------|
| **S**ingle Responsibility | 单一职责 | 一个类只负责一件事 |
| **O**pen/Closed | 开闭原则 | 对扩展开放，对修改关闭 |
| **L**iskov Substitution | 里氏替换 | 子类可以替换父类 |
| **I**nterface Segregation | 接口隔离 | 接口要小而专一 |
| **D**ependency Inversion | 依赖倒置 | 依赖抽象，不依赖具体 |

### 其他原则

- **KISS**: Keep It Simple, Stupid - 保持简单
- **DRY**: Don't Repeat Yourself - 不要重复
- **YAGNI**: You Aren't Gonna Need It - 不要过度设计

---

## 分层架构最佳实践

### Controller 层

```java
// ✅ 正确：Controller 只做请求转发
@RestController
public class DeviceController {
    private final DeviceService service;
    
    @GetMapping("/devices/{id}")
    public ApiResponse<DeviceVO> getById(@PathVariable Long id) {
        return ApiResponse.success(service.getById(id));
    }
}

// ❌ 错误：Controller 包含业务逻辑
@GetMapping("/devices/{id}")
public ApiResponse<DeviceVO> getById(@PathVariable Long id) {
    Device device = repository.findById(id).orElse(null);
    if (device == null) {
        return ApiResponse.error("设备不存在");
    }
    DeviceVO vo = new DeviceVO();
    // 复杂的转换逻辑...
    return ApiResponse.success(vo);
}
```

### Service 层

```java
// ✅ 正确：Service 处理业务逻辑
@Service
public class DeviceServiceImpl implements DeviceService {
    
    @Transactional
    public DeviceVO create(DeviceCreateDTO dto) {
        // 1. 参数校验
        validateCreateRequest(dto);
        
        // 2. 业务检查
        if (repository.existsByDeviceCode(dto.getDeviceCode())) {
            throw new BusinessException("设备编号已存在");
        }
        
        // 3. 创建实体
        Device device = new Device();
        BeanUtils.copyProperties(dto, device);
        
        // 4. 保存
        device = repository.save(device);
        
        // 5. 返回
        return toVO(device);
    }
}
```

### Repository 层

```java
// ✅ 正确：Repository 只负责数据访问
public interface DeviceRepository extends JpaRepository<Device, Long> {
    Optional<Device> findByDeviceCode(String deviceCode);
    boolean existsByDeviceCode(String deviceCode);
    List<Device> findByDeviceTypeId(Long typeId);
}

// ❌ 错误：Repository 包含业务逻辑
@Query("SELECT d FROM Device d WHERE d.status = 'ACTIVE'")
List<Device> findActiveDevices();  // 状态判断应在 Service 层
```

---

## 异常处理最佳实践

### 自定义异常

```java
// 业务异常
public class BusinessException extends RuntimeException {
    private final String code;
    
    public BusinessException(String message) {
        super(message);
        this.code = "BUSINESS_ERROR";
    }
    
    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
    }
}

// 资源不存在异常
public class ResourceNotFoundException extends BusinessException {
    public ResourceNotFoundException(String resource) {
        super("RESOURCE_NOT_FOUND", resource + "不存在");
    }
}
```

### 全局异常处理

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public ApiResponse<Void> handleBusinessException(BusinessException e) {
        log.warn("业务异常: {}", e.getMessage());
        return ApiResponse.error(e.getCode(), e.getMessage());
    }
    
    @ExceptionHandler(ResourceNotFoundException.class)
    public ApiResponse<Void> handleResourceNotFoundException(ResourceNotFoundException e) {
        log.warn("资源不存在: {}", e.getMessage());
        return ApiResponse.error(404, e.getMessage());
    }
    
    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return ApiResponse.error("系统繁忙，请稍后重试");
    }
}
```

---

## 事务处理最佳实践

### 事务注解使用

```java
// ✅ 正确：只在 Service 层使用事务
@Service
public class OrderServiceImpl implements OrderService {
    
    @Transactional
    public OrderVO createOrder(OrderCreateDTO dto) {
        // 创建订单
        Order order = createOrderEntity(dto);
        
        // 扣减库存
        inventoryService.deductStock(dto.getProductId(), dto.getQuantity());
        
        // 创建支付记录
        paymentService.createPaymentRecord(order.getId());
        
        return toVO(order);
    }
}

// ❌ 错误：事务嵌套问题
@Transactional
public void methodA() {
    methodB();  // 同类调用，@Transactional 不生效
}

@Transactional
public void methodB() {
    // ...
}
```

### 事务传播行为

```java
// 默认：REQUIRED - 有事务就加入，没有就新建
@Transactional
public void normalMethod() {}

// REQUIRES_NEW - 总是新建事务
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void independentMethod() {}

// NESTED - 嵌套事务
@Transactional(propagation = Propagation.NESTED)
public void nestedMethod() {}
```

---

## 查询优化最佳实践

### N+1 问题

```java
// ❌ N+1 问题
List<Order> orders = orderRepository.findAll();
for (Order order : orders) {
    order.getUser().getName();  // 每次循环都查一次用户
}

// ✅ 使用 JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.user")
List<Order> findAllWithUser();

// ✅ 使用 EntityGraph
@EntityGraph(attributePaths = {"user"})
List<Order> findAll();
```

### 分页查询

```java
// ✅ 使用 Pageable
public Page<Device> list(DeviceQueryDTO query) {
    Pageable pageable = PageRequest.of(query.getPage() - 1, query.getSize());
    Specification<Device> spec = buildSpecification(query);
    return repository.findAll(spec, pageable);
}
```

---

## 前端最佳实践

### 组件设计

```vue
<!-- ✅ 正确：组件职责单一 -->
<template>
  <el-select v-model="modelValue" :options="options" />
</template>

<script setup>
// DeviceTypeSelect - 只负责设备类型选择
defineProps<{
  modelValue: number;
  options: TypeOption[];
}>();

defineEmits<{
  'update:modelValue': [value: number];
}>();
</script>

<!-- ❌ 错误：组件职责过多 -->
<template>
  <!-- 包含搜索、筛选、分页等过多功能 -->
</template>
```

### 状态管理

```typescript
// ✅ 使用 Pinia 管理全局状态
export const useDeviceStore = defineStore('device', () => {
  const devices = ref<Device[]>([]);
  const currentDevice = ref<Device | null>(null);
  
  const fetchDevices = async () => {
    const res = await deviceApi.list({ page: 1, size: 100 });
    devices.value = res.list;
  };
  
  return { devices, currentDevice, fetchDevices };
});

// 组件中使用
const deviceStore = useDeviceStore();
await deviceStore.fetchDevices();
```

### API 调用

```typescript
// ✅ 封装 API 调用，统一错误处理
export const useDeviceApi = () => {
  const loading = ref(false);
  
  const fetchList = async (params: DeviceQuery) => {
    loading.value = true;
    try {
      return await deviceApi.list(params);
    } catch (error) {
      ElMessage.error('加载设备列表失败');
      throw error;
    } finally {
      loading.value = false;
    }
  };
  
  return { loading, fetchList };
};
```

---

## 安全最佳实践

### 输入验证

```java
// ✅ 使用 Bean Validation
@Data
public class DeviceCreateDTO {
    @NotBlank(message = "设备编号不能为空")
    @Pattern(regexp = "^[A-Z]{2}\\d{6}$", message = "设备编号格式不正确")
    private String deviceCode;
    
    @NotBlank(message = "设备名称不能为空")
    @Size(max = 100, message = "设备名称不能超过100字符")
    private String name;
    
    @Min(value = 1, message = "设备类型必须指定")
    private Long typeId;
}
```

### SQL 注入防护

```java
// ✅ 参数化查询
@Query("SELECT d FROM Device d WHERE d.deviceCode = :code")
Device findByDeviceCode(@Param("code") String code);

// ❌ 字符串拼接（危险）
String jpql = "SELECT d FROM Device d WHERE d.deviceCode = '" + code + "'";
```

### XSS 防护

```java
// ✅ 输出转义
import org.springframework.web.util.HtmlUtils;

String safeName = HtmlUtils.htmlEscape(userInput);
```

---

## 测试最佳实践

### 单元测试

```java
@ExtendWith(MockitoExtension.class)
class DeviceServiceTest {
    
    @Mock
    private DeviceRepository repository;
    
    @InjectMocks
    private DeviceServiceImpl service;
    
    @Test
    void should_create_device_successfully() {
        // Given
        DeviceCreateDTO dto = new DeviceCreateDTO();
        dto.setDeviceCode("AB123456");
        
        Device device = new Device();
        device.setId(1L);
        
        when(repository.existsByDeviceCode(any())).thenReturn(false);
        when(repository.save(any())).thenReturn(device);
        
        // When
        DeviceVO result = service.create(dto);
        
        // Then
        assertNotNull(result);
        assertEquals(1L, result.getId());
        verify(repository).save(any());
    }
}
```

---

## 文档最佳实践

### API 文档

```java
@RestController
@RequestMapping("/api/devices")
@Tag(name = "设备管理", description = "设备的增删改查接口")
public class DeviceController {
    
    @Operation(summary = "获取设备列表", description = "分页查询设备")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "成功"),
        @ApiResponse(responseCode = "400", description = "参数错误")
    })
    @GetMapping
    public ApiResponse<PageResponse<DeviceVO>> list(DeviceQueryDTO query) {
        // ...
    }
}
```

---

## 总结

| 场景 | 最佳实践 |
|------|----------|
| 分层设计 | Controller 只转发，Service 处理逻辑，Repository 只查数据 |
| 异常处理 | 自定义异常 + 全局异常处理 |
| 事务管理 | 在 Service 层使用，注意传播行为 |
| 查询优化 | 避免 N+1，使用 JOIN FETCH |
| 安全防护 | 输入验证 + 参数化查询 + 输出转义 |
| 测试 | Mock 依赖，测试核心逻辑 |