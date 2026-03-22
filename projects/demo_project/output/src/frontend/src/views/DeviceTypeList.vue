<template>
  <div class="device-type-container">
    <div class="header">
      <h1>设备类型管理</h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增设备类型
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.keyword"
            placeholder="类型名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 设备类型表格 -->
    <div class="table-container">
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="type_id" label="ID" width="80" />
        <el-table-column prop="type_name" label="类型名称" width="150" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="类型名称" prop="type_name">
          <el-input v-model="form.type_name" placeholder="请输入类型名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="form.is_active">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDeviceTypeList,
  createDeviceType,
  updateDeviceType,
  deleteDeviceType
} from '@/api/deviceType'
import { useDeviceStore } from '@/store/device'

const deviceStore = useDeviceStore()

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增设备类型')
const formRef = ref(null)

const searchForm = reactive({
  keyword: '',
  is_active: undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  type_id: null,
  type_name: '',
  description: '',
  sort_order: 0,
  is_active: true
})

const rules = {
  type_name: [
    { required: true, message: '请输入类型名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// 获取设备类型列表
const fetchDeviceTypes = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    }
    const res = await getDeviceTypeList(params)
    tableData.value = res.data.list
    pagination.total = res.data.total
  } catch (error) {
    console.error('获取设备类型列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchDeviceTypes()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.is_active = undefined
  pagination.page = 1
  fetchDeviceTypes()
}

// 新增
const handleAdd = () => {
  dialogTitle.value = '新增设备类型'
  form.type_id = null
  form.type_name = ''
  form.description = ''
  form.sort_order = 0
  form.is_active = true
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  dialogTitle.value = '编辑设备类型'
  form.type_id = row.type_id
  form.type_name = row.type_name
  form.description = row.description || ''
  form.sort_order = row.sort_order
  form.is_active = row.is_active
  dialogVisible.value = true
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该设备类型吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDeviceType(row.type_id)
      ElMessage.success('删除成功')
      // 刷新设备类型列表
      deviceStore.loadDeviceTypes()
      fetchDeviceTypes()
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (form.type_id) {
        await updateDeviceType(form.type_id, form)
        ElMessage.success('更新成功')
      } else {
        await createDeviceType(form)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      // 刷新设备类型列表
      deviceStore.loadDeviceTypes()
      fetchDeviceTypes()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 对话框关闭
const handleDialogClose = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 分页
const handleSizeChange = () => {
  fetchDeviceTypes()
}

const handleCurrentChange = () => {
  fetchDeviceTypes()
}

onMounted(() => {
  fetchDeviceTypes()
})
</script>

<style scoped>
.device-type-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 24px;
  color: #303133;
}

.search-bar {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.table-container {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
