<template>
  <div class="device-detail-container">
    <div class="header">
      <h1>设备详情</h1>
      <div>
        <el-button @click="handleBack">返回列表</el-button>
        <el-button type="primary" @click="handleEdit">编辑</el-button>
      </div>
    </div>

    <div class="detail-container" v-loading="loading">
      <el-descriptions title="设备信息" :column="2" border>
        <el-descriptions-item label="设备编号">{{ device.device_id }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ device.device_name }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ device.device_type }}</el-descriptions-item>
        <el-descriptions-item label="规格型号">{{ device.specification || '-' }}</el-descriptions-item>
        <el-descriptions-item label="购买日期">{{ device.purchase_date }}</el-descriptions-item>
        <el-descriptions-item label="使用部门">{{ device.department }}</el-descriptions-item>
        <el-descriptions-item label="使用人">{{ device.user_name }}</el-descriptions-item>
        <el-descriptions-item label="设备状态">
          <el-tag :type="getStatusType(device.status)">{{ device.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="存放位置">{{ device.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ device.remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getDeviceDetail } from '@/api/device'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const device = reactive({
  device_id: '',
  device_name: '',
  device_type: '',
  specification: '',
  purchase_date: '',
  department: '',
  user_name: '',
  status: '',
  location: '',
  remark: ''
})

// 加载设备详情
const loadDevice = async () => {
  loading.value = true
  try {
    const res = await getDeviceDetail(route.params.id)
    Object.assign(device, res.data)
  } catch (error) {
    console.error('加载设备详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 返回
const handleBack = () => {
  router.push('/')
}

// 编辑
const handleEdit = () => {
  router.push(`/device/edit/${device.device_id}`)
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
  loadDevice()
})
</script>

<style scoped>
.device-detail-container {
  padding: 20px;
  max-width: 1000px;
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

.detail-container {
  background: #fff;
  padding: 30px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
