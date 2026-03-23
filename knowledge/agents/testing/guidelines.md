# 测试知识库

## 测试类型

| 类型 | 范围 | 覆盖率目标 | 负责人 |
|------|------|------------|--------|
| **单元测试** | 函数/方法 | ≥ 80% | 开发 |
| **集成测试** | 模块交互 | ≥ 60% | 开发+测试 |
| **E2E 测试** | 完整流程 | ≥ 40% | 测试 |

---

## 测试框架

### 后端测试

```java
// JUnit 5 + Mockito
@ExtendWith(MockitoExtension.class)
class DeviceServiceTest {
    
    @Mock
    private DeviceRepository repository;
    
    @InjectMocks
    private DeviceServiceImpl service;
    
    @Test
    @DisplayName("创建设备 - 成功")
    void should_create_device_successfully() {
        // Given
        DeviceCreateDTO dto = new DeviceCreateDTO();
        dto.setDeviceCode("DEV-001");
        
        when(repository.existsByDeviceCode(any())).thenReturn(false);
        when(repository.save(any())).thenReturn(createMockDevice());
        
        // When
        DeviceVO result = service.create(dto);
        
        // Then
        assertNotNull(result);
        assertEquals("DEV-001", result.getDeviceCode());
    }
    
    @Test
    @DisplayName("创建设备 - 编号重复应抛异常")
    void should_throw_when_code_exists() {
        // Given
        DeviceCreateDTO dto = new DeviceCreateDTO();
        dto.setDeviceCode("DEV-001");
        
        when(repository.existsByDeviceCode("DEV-001")).thenReturn(true);
        
        // When & Then
        assertThrows(BusinessException.class, () -> service.create(dto));
    }
}
```

### 前端测试

```typescript
// Vitest + Vue Test Utils
import { mount } from '@vue/test-utils';
import DeviceList from '@/views/device/DeviceList.vue';

describe('DeviceList', () => {
  it('should render device list', async () => {
    const wrapper = mount(DeviceList, {
      global: {
        mocks: {
          $api: {
            device: {
              list: vi.fn().mockResolvedValue({ list: [], total: 0 })
            }
          }
        }
      }
    });
    
    await wrapper.vm.$nextTick();
    
    expect(wrapper.find('.device-list').exists()).toBe(true);
  });
});
```

---

## 测试用例设计

### 测试用例模板

```markdown
## 测试用例: TC-001

**用例名称**: 创建设备 - 正常流程

**前置条件**:
- 用户已登录
- 具有创建设备权限

**测试步骤**:
1. 进入设备列表页面
2. 点击"新增"按钮
3. 填写设备信息
4. 点击"保存"按钮

**测试数据**:
| 字段 | 值 |
|------|-----|
| 设备编号 | DEV-001 |
| 设备名称 | 测试设备 |
| 设备类型 | 服务器 |

**预期结果**:
- 提示"创建成功"
- 列表中显示新建设备
- 设备信息正确

**优先级**: P0
```

### 测试数据设计

```
1. 正常数据
   - 满足所有约束的数据
   - 边界值数据

2. 异常数据
   - 空值/Null
   - 超长字符串
   - 非法字符
   - 格式错误

3. 边界数据
   - 最小值
   - 最大值
   - 边界临界值
```

---

## 测试报告模板

```markdown
# 测试报告

**项目**: {项目名称}  
**版本**: v1.0.0  
**测试日期**: {YYYY-MM-DD}  
**测试人员**: {姓名}

---

## 测试概览

| 指标 | 数值 |
|------|------|
| 测试用例总数 | 100 |
| 通过用例数 | 95 |
| 失败用例数 | 3 |
| 阻塞用例数 | 2 |
| 通过率 | 95% |

---

## 测试范围

- [x] 功能测试
- [x] 接口测试
- [x] 性能测试
- [ ] 安全测试

---

## 缺陷统计

| 严重级别 | 数量 | 已修复 | 待修复 |
|----------|------|--------|--------|
| 致命 | 0 | 0 | 0 |
| 严重 | 2 | 1 | 1 |
| 一般 | 5 | 3 | 2 |
| 轻微 | 3 | 3 | 0 |

---

## 测试结论

- [ ] 通过，可以发布
- [ ] 有风险，建议修复后发布
- [ ] 不通过，需要修复后重新测试

**问题列表**:
1. BUG-001: 设备列表分页异常 (严重)
2. BUG-002: 导入功能失败 (严重)
```

---

## 性能测试

### 性能指标

| 指标 | 目标值 |
|------|--------|
| 响应时间 | < 2s (P99) |
| 吞吐量 | ≥ 100 TPS |
| 并发用户 | ≥ 100 |
| 错误率 | < 0.1% |

### JMeter 测试脚本

```xml
<TestPlan>
  <ThreadGroup>
    <stringProp name="ThreadGroup.num_threads">100</stringProp>
    <stringProp name="ThreadGroup.ramp_time">10</stringProp>
    <stringProp name="ThreadGroup.duration">300</stringProp>
    
    <HTTPSamplerProxy>
      <stringProp name="HTTPSampler.domain">localhost</stringProp>
      <stringProp name="HTTPSampler.port">8080</stringProp>
      <stringProp name="HTTPSampler.path">/api/devices</stringProp>
      <stringProp name="HTTPSampler.method">GET</stringProp>
    </HTTPSamplerProxy>
  </ThreadGroup>
</TestPlan>
```

---

## 测试检查清单

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 接口测试全部通过
- [ ] 性能测试达标
- [ ] 无 P0/P1 级别缺陷
- [ ] 测试报告已生成