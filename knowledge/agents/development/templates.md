# 代码模板

## Java 模板

### 实体类 (Entity)

```java
package com.example.app.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * {实体名称}实体
 */
@Data
@Entity
@Table(name = "{table_name}")
public class {EntityName} {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 50)
    private String name;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

### DTO (数据传输对象)

```java
package com.example.app.dto;

import jakarta.validation.constraints.*;
import lombok.Data;

/**
 * {实体名称}创建请求
 */
@Data
public class {EntityName}CreateDTO {
    
    @NotBlank(message = "名称不能为空")
    @Size(max = 50, message = "名称长度不能超过50")
    private String name;
    
    @NotNull(message = "类型不能为空")
    private Long typeId;
    
    private String description;
}
```

### Repository

```java
package com.example.app.repository;

import com.example.app.entity.{EntityName};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;
import java.util.Optional;

/**
 * {实体名称}数据访问
 */
public interface {EntityName}Repository extends 
    JpaRepository<{EntityName}, Long>, 
    JpaSpecificationExecutor<{EntityName}> {
    
    /**
     * 根据名称查找
     */
    Optional<{EntityName}> findByName(String name);
    
    /**
     * 检查名称是否存在
     */
    boolean existsByName(String name);
    
    /**
     * 根据类型查找
     */
    List<{EntityName}> findByTypeId(Long typeId);
    
    /**
     * 批量查询
     */
    @Query("SELECT e FROM {EntityName} e WHERE e.id IN :ids")
    List<{EntityName}> findByIds(@Param("ids") List<Long> ids);
}
```

### Service 接口

```java
package com.example.app.service;

import com.example.app.dto.*;
import com.example.app.vo.*;
import org.springframework.data.domain.Page;
import java.util.List;

/**
 * {实体名称}服务接口
 */
public interface {EntityName}Service {
    
    /**
     * 分页查询
     */
    Page<{EntityName}VO> list({EntityName}QueryDTO query);
    
    /**
     * 获取详情
     */
    {EntityName}VO getById(Long id);
    
    /**
     * 创建
     */
    {EntityName}VO create({EntityName}CreateDTO dto);
    
    /**
     * 更新
     */
    {EntityName}VO update(Long id, {EntityName}UpdateDTO dto);
    
    /**
     * 删除
     */
    void delete(Long id);
    
    /**
     * 批量删除
     */
    void batchDelete(List<Long> ids);
}
```

### Service 实现

```java
package com.example.app.service.impl;

import com.example.app.dto.*;
import com.example.app.entity.{EntityName};
import com.example.app.exception.BusinessException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.{EntityName}Repository;
import com.example.app.service.{EntityName}Service;
import com.example.app.vo.{EntityName}VO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * {实体名称}服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class {EntityName}ServiceImpl implements {EntityName}Service {
    
    private final {EntityName}Repository repository;
    
    @Override
    public Page<{EntityName}VO> list({EntityName}QueryDTO query) {
        Specification<{EntityName}> spec = buildSpecification(query);
        PageRequest pageRequest = PageRequest.of(query.getPage() - 1, query.getSize());
        return repository.findAll(spec, pageRequest).map(this::toVO);
    }
    
    @Override
    public {EntityName}VO getById(Long id) {
        {EntityName} entity = repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{实体名称}不存在"));
        return toVO(entity);
    }
    
    @Override
    @Transactional
    public {EntityName}VO create({EntityName}CreateDTO dto) {
        // 检查重复
        if (repository.existsByName(dto.getName())) {
            throw new BusinessException("{实体名称}已存在");
        }
        
        {EntityName} entity = new {EntityName}();
        // 设置属性...
        
        entity = repository.save(entity);
        log.info("{实体名称}创建成功, id={}", entity.getId());
        return toVO(entity);
    }
    
    @Override
    @Transactional
    public {EntityName}VO update(Long id, {EntityName}UpdateDTO dto) {
        {EntityName} entity = repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{实体名称}不存在"));
        
        // 更新属性...
        
        entity = repository.save(entity);
        log.info("{实体名称}更新成功, id={}", entity.getId());
        return toVO(entity);
    }
    
    @Override
    @Transactional
    public void delete(Long id) {
        if (!repository.existsById(id)) {
            throw new ResourceNotFoundException("{实体名称}不存在");
        }
        repository.deleteById(id);
        log.info("{实体名称}删除成功, id={}", id);
    }
    
    @Override
    @Transactional
    public void batchDelete(List<Long> ids) {
        repository.deleteAllById(ids);
        log.info("{实体名称}批量删除成功, count={}", ids.size());
    }
    
    // 私有方法
    private {EntityName}VO toVO({EntityName} entity) {
        // 转换逻辑...
        return new {EntityName}VO();
    }
    
    private Specification<{EntityName}> buildSpecification({EntityName}QueryDTO query) {
        // 构建查询条件...
        return null;
    }
}
```

### Controller

```java
package com.example.app.controller;

import com.example.app.dto.*;
import com.example.app.response.ApiResponse;
import com.example.app.response.PageResponse;
import com.example.app.service.{EntityName}Service;
import com.example.app.vo.{EntityName}VO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * {实体名称}控制器
 */
@RestController
@RequestMapping("/api/{entity_names}")
@RequiredArgsConstructor
public class {EntityName}Controller {
    
    private final {EntityName}Service service;
    
    /**
     * 分页查询
     */
    @GetMapping
    public ApiResponse<PageResponse<{EntityName}VO>> list({EntityName}QueryDTO query) {
        Page<{EntityName}VO> page = service.list(query);
        return ApiResponse.success(PageResponse.of(page));
    }
    
    /**
     * 获取详情
     */
    @GetMapping("/{id}")
    public ApiResponse<{EntityName}VO> getById(@PathVariable Long id) {
        return ApiResponse.success(service.getById(id));
    }
    
    /**
     * 创建
     */
    @PostMapping
    public ApiResponse<{EntityName}VO> create(@Valid @RequestBody {EntityName}CreateDTO dto) {
        return ApiResponse.success(service.create(dto));
    }
    
    /**
     * 更新
     */
    @PutMapping("/{id}")
    public ApiResponse<{EntityName}VO> update(
        @PathVariable Long id,
        @Valid @RequestBody {EntityName}UpdateDTO dto) {
        return ApiResponse.success(service.update(id, dto));
    }
    
    /**
     * 删除
     */
    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return ApiResponse.success();
    }
    
    /**
     * 批量删除
     */
    @DeleteMapping("/batch")
    public ApiResponse<Void> batchDelete(@RequestBody List<Long> ids) {
        service.batchDelete(ids);
        return ApiResponse.success();
    }
}
```

---

## Vue 模板

### API 封装

```typescript
// api/{entityName}.ts
import request from './request';
import type { PageResponse, ApiResponse } from './types';

export interface {EntityName}VO {
  id: number;
  name: string;
  // 其他字段...
}

export interface {EntityName}Query {
  page: number;
  size: number;
  keyword?: string;
}

export interface {EntityName}CreateDTO {
  name: string;
  // 其他字段...
}

export const {entityName}Api = {
  /**
   * 分页查询
   */
  list(params: {EntityName}Query): Promise<PageResponse<{EntityName}VO>> {
    return request.get('/api/{entity_names}', { params });
  },

  /**
   * 获取详情
   */
  getDetail(id: number): Promise<{EntityName}VO> {
    return request.get(`/api/{entity_names}/${id}`);
  },

  /**
   * 创建
   */
  create(data: {EntityName}CreateDTO): Promise<{EntityName}VO> {
    return request.post('/api/{entity_names}', data);
  },

  /**
   * 更新
   */
  update(id: number, data: Partial<{EntityName}CreateDTO>): Promise<{EntityName}VO> {
    return request.put(`/api/{entity_names}/${id}`, data);
  },

  /**
   * 删除
   */
  delete(id: number): Promise<void> {
    return request.delete(`/api/{entity_names}/${id}`);
  },

  /**
   * 批量删除
   */
  batchDelete(ids: number[]): Promise<void> {
    return request.delete('/api/{entity_names}/batch', { data: { ids } });
  }
};
```

### Vue 组件

```vue
<!-- views/{entityName}/{EntityName}List.vue -->
<template>
  <div class="{entity-name}-list">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="请输入关键词" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="toolbar-card">
      <el-button type="primary" @click="handleAdd">新增</el-button>
      <el-button 
        type="danger" 
        :disabled="!selectedIds.length"
        @click="handleBatchDelete">
        批量删除
      </el-button>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table 
        :data="tableData" 
        v-loading="loading"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        @change="fetchData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { {entityName}Api, type {EntityName}VO } from '@/api/{entityName}';

// 数据
const loading = ref(false);
const tableData = ref<{EntityName}VO[]>([]);
const total = ref(0);
const selectedIds = ref<number[]>([]);

const queryParams = reactive({
  page: 1,
  size: 10,
  keyword: ''
});

// 方法
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await {entityName}Api.list(queryParams);
    tableData.value = res.list;
    total.value = res.total;
  } catch (error) {
    ElMessage.error('加载失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  queryParams.page = 1;
  fetchData();
};

const handleReset = () => {
  queryParams.keyword = '';
  handleSearch();
};

const handleAdd = () => {
  // 打开新增对话框
};

const handleEdit = (row: {EntityName}VO) => {
  // 打开编辑对话框
};

const handleDelete = async (row: {EntityName}VO) => {
  await ElMessageBox.confirm('确定要删除吗？', '提示');
  await {entityName}Api.delete(row.id);
  ElMessage.success('删除成功');
  fetchData();
};

const handleBatchDelete = async () => {
  await ElMessageBox.confirm('确定要批量删除吗？', '提示');
  await {entityName}Api.batchDelete(selectedIds.value);
  ElMessage.success('删除成功');
  fetchData();
};

const handleSelectionChange = (selection: {EntityName}VO[]) => {
  selectedIds.value = selection.map(item => item.id);
};

// 初始化
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.search-card, .toolbar-card {
  margin-bottom: 16px;
}
</style>
```

---

## 配置文件模板

### application.yml

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/{database_name}
    username: root
    password: ${DB_PASSWORD}
    driver-class-name: com.mysql.cj.jdbc.Driver
  
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
    properties:
      hibernate.format_sql: true
  
  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD}

server:
  port: 8080

logging:
  level:
    com.example: DEBUG
```