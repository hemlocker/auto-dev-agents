<template>
  <div class="device-form-container">
    <div class="header">
      <h1>新增设备</h1>
      <div>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </div>
    </div>

    <div class="form-container">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        style="max-width: 600px"
      >
        <el-form-item label="设备编号" prop="device_id">
          <el-input v-model="form.device_id" placeholder="请输入设备编号" />
        </el-form-item>

        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="form.device_name" placeholder="请输入设备名称" />
        </el-form-item>

        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="form.device_type" placeholder="请选择设备类型" style="width: 100%">
            <el-option
              v-for="type in deviceTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="规格型号" prop="specification">
          <el-input v-model="form.specification" placeholder="请输入规格型号" />
        </el-form-item>

        <el-form-item label="购买日期" prop="purchase_date">
          <el-date-picker
            v-model="form.purchase_date"
            type="date"
            placeholder="选择购买日期"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="使用部门" prop="department">
          <el-input v-model="form.department" placeholder="请输入使用部门" />
        </el-form-item>

        <el-form-item label="使用人" prop="user_name">
          <el-input v-model="form.user_name" placeholder="请输入使用人" />
        </el-form-item>

        <el-form-item label="设备状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="在用">在用</el-radio>
            <el-radio label="闲置">闲置</el-radio>
            <el-radio label="报废">报废</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="存放位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入存放位置" />
        </el-form-item>

        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createDevice } from '@/api/device'
import { useDeviceStore } from '@/store/device'

const router = useRouter()
const deviceStore = useDeviceStore()
const { deviceTypes } = deviceStore

const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  device_id: '',
  device_name: '',
  device_type: '',
  specification: '',
  purchase_date: '',
  department: '',
  user_name: '',
  status: '闲置',
  location: '',
  remark: ''
})

const rules = {
  device_id: [
    { required: true, message: '请输入设备编号', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  device_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  device_type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  purchase_date: [
    { required: true, message: '请选择购买日期', trigger: 'change' }
  ],
  department: [
    { required: true, message: '请输入使用部门', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  user_name: [
    { required: true, message: '请输入使用人', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择设备状态', trigger: 'change' }
  ]
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await createDevice(form)
      ElMessage.success('新增成功')
      router.push('/')
    } catch (error) {
      console.error('新增失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

// 取消
const handleCancel = () => {
  router.push('/')
}
</script>

<style scoped>
.device-form-container {
  padding: 20px;
  max-width: 800px;
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

.form-container {
  background: #fff;
  padding: 30px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
