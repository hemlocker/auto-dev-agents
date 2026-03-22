<template>
  <div class="import-export-container">
    <div class="header">
      <h1>批量导入导出</h1>
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 导入功能 -->
      <el-tab-pane label="批量导入" name="import">
        <div class="import-panel">
          <!-- 步骤 1: 下载模板 -->
          <el-card class="step-card">
            <template #header>
              <div class="card-header">
                <span class="step-number">1</span>
                <span>下载导入模板</span>
              </div>
            </template>
            <p class="step-desc">模板包含字段说明和示例数据，请先下载并填写</p>
            <el-button type="primary" @click="downloadTemplate">
              <el-icon><Download /></el-icon>
              下载模板
            </el-button>
          </el-card>

          <!-- 步骤 2: 上传文件 -->
          <el-card class="step-card">
            <template #header>
              <div class="card-header">
                <span class="step-number">2</span>
                <span>上传 Excel 文件</span>
              </div>
            </template>
            <el-upload
              ref="uploadRef"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleRemove"
              :limit="1"
              accept=".xlsx"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持格式：.xlsx，文件大小：最大 10MB
                </div>
              </template>
            </el-upload>
            <div class="upload-actions" v-if="selectedFile">
              <p>已选择文件：{{ selectedFile.name }}</p>
              <el-button type="primary" @click="handleUpload" :loading="uploading">
                开始导入
              </el-button>
            </div>
          </el-card>

          <!-- 步骤 3: 导入结果 -->
          <el-card class="step-card" v-if="importResult">
            <template #header>
              <div class="card-header">
                <span class="step-number">3</span>
                <span>导入结果</span>
              </div>
            </template>
            <div class="result-summary">
              <el-statistic title="总计" :value="importResult.total" />
              <el-statistic title="成功" :value="importResult.success" value-style="color: #67C23A" />
              <el-statistic title="失败" :value="importResult.failed" value-style="color: #F56C6C" />
            </div>
            
            <div class="error-details" v-if="importResult.errors && importResult.errors.length > 0">
              <h4>失败详情：</h4>
              <el-table :data="importResult.errors" border stripe>
                <el-table-column prop="row" label="行号" width="80" />
                <el-table-column prop="device_id" label="设备编号" width="150" />
                <el-table-column prop="reason" label="失败原因" />
              </el-table>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 导出功能 -->
      <el-tab-pane label="数据导出" name="export">
        <div class="export-panel">
          <el-card>
            <h3>导出范围</h3>
            <el-radio-group v-model="exportScope">
              <el-radio label="all">全部设备</el-radio>
              <el-radio label="filtered">按筛选条件导出</el-radio>
            </el-radio-group>

            <div class="filter-options" v-if="exportScope === 'filtered'">
              <el-form :inline="true">
                <el-form-item label="设备类型">
                  <el-select v-model="exportFilters.device_type" placeholder="全部" clearable>
                    <el-option
                      v-for="type in deviceTypes"
                      :key="type"
                      :label="type"
                      :value="type"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="设备状态">
                  <el-select v-model="exportFilters.status" placeholder="全部" clearable>
                    <el-option
                      v-for="status in deviceStatuses"
                      :key="status"
                      :label="status"
                      :value="status"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="使用部门">
                  <el-input v-model="exportFilters.department" placeholder="部门名称" clearable />
                </el-form-item>
                <el-form-item label="关键词">
                  <el-input v-model="exportFilters.keyword" placeholder="设备名称/编号" clearable />
                </el-form-item>
              </el-form>
            </div>

            <div class="export-actions">
              <el-button type="primary" @click="handleExport" :loading="exporting">
                <el-icon><Download /></el-icon>
                确认导出
              </el-button>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, UploadFilled, ArrowLeft } from '@element-plus/icons-vue'
import { downloadImportTemplate, importDevices, exportDevices } from '@/api/importExport'
import { useDeviceStore } from '@/store/device'

const router = useRouter()
const deviceStore = useDeviceStore()
const { deviceTypes, deviceStatuses } = deviceStore

const activeTab = ref('import')
const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const exporting = ref(false)
const importResult = ref(null)
const exportScope = ref('all')

const exportFilters = reactive({
  device_type: '',
  status: '',
  department: '',
  keyword: ''
})

const goBack = () => {
  router.push('/')
}

// 下载模板
const downloadTemplate = async () => {
  try {
    const blob = await downloadImportTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '设备导入模板.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    ElMessage.error('下载模板失败')
  }
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 移除文件
const handleRemove = () => {
  selectedFile.value = null
  importResult.value = null
}

// 上传导入
const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  uploading.value = true
  try {
    const res = await importDevices(formData)
    importResult.value = res.data
    ElMessage.success('导入完成')
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  } finally {
    uploading.value = false
  }
}

// 导出数据
const handleExport = async () => {
  exporting.value = true
  try {
    const params = exportScope === 'filtered' ? exportFilters : {}
    const blob = await exportDevices(params)
    const timestamp = new Date().getTime()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `设备列表_${timestamp}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.import-export-container {
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

.import-panel, .export-panel {
  max-width: 800px;
  margin: 0 auto;
}

.step-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409EFF;
  color: #fff;
  font-size: 12px;
  font-weight: bold;
}

.step-desc {
  color: #909399;
  margin-bottom: 15px;
}

.upload-actions {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.result-summary {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
}

.error-details {
  margin-top: 20px;
}

.error-details h4 {
  margin-bottom: 10px;
  color: #F56C6C;
}

.filter-options {
  margin: 20px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.export-actions {
  margin-top: 20px;
  text-align: center;
}
</style>
