<template>
  <div class="device-list-container">
    <div class="header">
      <h1>设备管理系统</h1>
      <div>
        <el-button @click="goToDeviceType">
          <el-icon><Setting /></el-icon>
          设备类型管理
        </el-button>
        <el-button type="primary" @click="handleNew">
          <el-icon><Plus /></el-icon>
          新增设备
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.keyword"
            placeholder="设备名称/编号"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="searchForm.device_type" placeholder="全部" clearable style="width: 150px">
            <el-option
              v-for="type in deviceTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option
              v-for="status in deviceStatuses"
              :key="status"
              :label="status"
              :value="status"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用部门">
          <el-input
            v-model="searchForm.department"
            placeholder="部门名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="使用人">
          <el-input
            v-model="searchForm.user_name"
            placeholder="使用人姓名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 设备表格 -->
    <div class="table-container">
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="device_id" label="设备编号" width="120" />
        <el-table-column prop="device_name" label="设备名称" width="180" />
        <el-table-column prop="device_type" label="设备类型" width="100" />
        <el-table-column prop="department" label="使用部门" width="120" />
        <el-table-column prop="user_name" label="使用人" width="100" />
        <el-table-column prop="status" label="设备状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDeviceList, deleteDevice } from '@/api/device'
import { useDeviceStore } from '@/store/device'

const router = useRouter()
const deviceStore = useDeviceStore()

// 跳转到设备类型管理
const goToDeviceType = () => {
  router.push('/device-type')
}

const { deviceTypes, deviceStatuses } = deviceStore

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  keyword: '',
  device_type: '',
  status: '',
  department: '',
  user_name: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 获取设备列表
const fetchDevices = async () => {
  loading.value = true
  try {
    const params = {
      ...searchForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    }
    const res = await getDeviceList(params)
    tableData.value = res.data.list
    pagination.total = res.data.total
  } catch (error) {
    console.error('获取设备列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchDevices()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.device_type = ''
  searchForm.status = ''
  searchForm.department = ''
  searchForm.user_name = ''
  pagination.page = 1
  fetchDevices()
}

// 新增
const handleNew = () => {
  router.push('/device/new')
}

// 查看
const handleView = (row) => {
  router.push(`/device/detail/${row.device_id}`)
}

// 编辑
const handleEdit = (row) => {
  router.push(`/device/edit/${row.device_id}`)
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该设备吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDevice(row.device_id)
      ElMessage.success('删除成功')
      fetchDevices()
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

// 分页
const handleSizeChange = () => {
  fetchDevices()
}

const handleCurrentChange = () => {
  fetchDevices()
}

// 状态标签类型
const getStatusType = (status) => {
  const types = {
    '在用': 'success',
    '闲置': 'warning',
    '报废': 'danger'
  }
  return types[status] || 'info'
}

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-list-container {
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
