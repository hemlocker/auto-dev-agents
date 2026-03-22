<template>
  <div class="print-preview-container">
    <div class="header">
      <h1>打印设备标签</h1>
      <div>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <el-button type="primary" @click="handlePrint" :loading="printing">
          <el-icon><Printer /></el-icon>
          打印
        </el-button>
      </div>
    </div>

    <div class="print-content">
      <!-- 单台设备打印 -->
      <div class="single-print" v-if="!isBatch">
        <el-card class="preview-card">
          <template #header>
            <span>打印预览</span>
          </template>
          
          <div class="label-preview" v-if="labelData">
            <div class="device-label">
              <div class="label-title">设备标签</div>
              <div class="label-divider"></div>
              <div class="label-content">
                <div class="label-item">
                  <span class="label-key">设备编号：</span>
                  <span class="label-value">{{ labelData.device_id }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">设备名称：</span>
                  <span class="label-value">{{ labelData.device_name }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">设备类型：</span>
                  <span class="label-value">{{ labelData.device_type }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">规格型号：</span>
                  <span class="label-value">{{ labelData.specification || '-' }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">使用部门：</span>
                  <span class="label-value">{{ labelData.department }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">使用人：</span>
                  <span class="label-value">{{ labelData.user_name }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">购买日期：</span>
                  <span class="label-value">{{ labelData.purchase_date }}</span>
                </div>
                <div class="label-item">
                  <span class="label-key">设备状态：</span>
                  <span class="label-value">{{ labelData.status }}</span>
                </div>
              </div>
              <div class="label-qr" v-if="labelData.qr_code">
                <img :src="labelData.qr_code" alt="QR Code" />
              </div>
            </div>
          </div>

          <div class="print-settings">
            <h3>打印设置</h3>
            <el-form :inline="true">
              <el-form-item label="纸张大小">
                <el-select v-model="printSettings.paperSize">
                  <el-option label="A4" value="A4" />
                  <el-option label="A5" value="A5" />
                </el-select>
              </el-form-item>
              <el-form-item label="每页数量">
                <el-select v-model="printSettings.labelsPerPage">
                  <el-option label="4 个" :value="4" />
                  <el-option label="8 个" :value="8" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </div>

      <!-- 批量打印选择 -->
      <div class="batch-print" v-else>
        <el-card>
          <template #header>
            <span>已选择 {{ selectedDevices.length }} 台设备</span>
          </template>
          
          <el-table :data="selectedDevices" border stripe>
            <el-table-column prop="device_id" label="设备编号" width="120" />
            <el-table-column prop="device_name" label="设备名称" width="180" />
            <el-table-column prop="device_type" label="设备类型" width="100" />
            <el-table-column prop="department" label="使用部门" width="120" />
            <el-table-column prop="user_name" label="使用人" width="100" />
            <el-table-column prop="status" label="设备状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Printer } from '@element-plus/icons-vue'
import { getLabelData, printBatchLabels } from '@/api/print'
import { getDeviceDetail } from '@/api/device'

const router = useRouter()
const route = useRoute()

const isBatch = ref(false)
const labelData = ref(null)
const selectedDevices = ref([])
const printing = ref(false)

const printSettings = reactive({
  paperSize: 'A4',
  labelsPerPage: 4
})

onMounted(async () => {
  const { deviceIds } = route.query
  
  if (deviceIds) {
    // 批量打印
    isBatch.value = true
    const ids = deviceIds.split(',')
    await loadBatchDevices(ids)
  } else if (route.params.id) {
    // 单台打印
    isBatch.value = false
    await loadSingleDevice(route.params.id)
  } else {
    ElMessage.error('未指定设备')
    router.push('/')
  }
})

// 加载单台设备
const loadSingleDevice = async (id) => {
  try {
    const res = await getLabelData(id)
    labelData.value = res.data
  } catch (error) {
    console.error('加载设备失败:', error)
    ElMessage.error('加载设备失败')
  }
}

// 加载批量设备
const loadBatchDevices = async (ids) => {
  try {
    const promises = ids.map(id => getDeviceDetail(id))
    const results = await Promise.all(promises)
    selectedDevices.value = results.map(res => res.data)
  } catch (error) {
    console.error('加载设备失败:', error)
    ElMessage.error('加载设备失败')
  }
}

// 打印
const handlePrint = async () => {
  printing.value = true
  try {
    if (isBatch.value) {
      // 批量打印
      const device_ids = selectedDevices.value.map(d => d.device_id)
      const blob = await printBatchLabels({ device_ids })
      downloadBlob(blob, `设备标签_${Date.now()}.pdf`)
      ElMessage.success('打印任务已生成')
    } else {
      // 单台打印 - 调用浏览器打印
      window.print()
    }
  } catch (error) {
    console.error('打印失败:', error)
    ElMessage.error('打印失败')
  } finally {
    printing.value = false
  }
}

// 下载 Blob
const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

// 返回
const goBack = () => {
  router.push('/')
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
</script>

<style scoped>
.print-preview-container {
  padding: 20px;
  max-width: 1200px;
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

.print-content {
  max-width: 800px;
  margin: 0 auto;
}

.preview-card {
  margin-bottom: 20px;
}

.label-preview {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #f5f7fa;
}

.device-label {
  width: 350px;
  border: 2px solid #303133;
  border-radius: 8px;
  padding: 15px;
  background: #fff;
}

.label-title {
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 10px;
  color: #303133;
}

.label-divider {
  height: 1px;
  background: #303133;
  margin-bottom: 15px;
}

.label-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.label-key {
  font-weight: bold;
  color: #606266;
  min-width: 70px;
}

.label-value {
  color: #303133;
  flex: 1;
}

.label-qr {
  margin-top: 15px;
  text-align: center;
}

.label-qr img {
  width: 100px;
  height: 100px;
}

.print-settings {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #EBEEF5;
}

.print-settings h3 {
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

@media print {
  .header, .print-settings {
    display: none;
  }
  
  .print-preview-container {
    padding: 0;
  }
  
  .label-preview {
    background: #fff;
  }
}
</style>
