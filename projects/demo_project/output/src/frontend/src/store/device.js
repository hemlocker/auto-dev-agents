import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'
import { getAllDeviceTypes } from '@/api/deviceType'

export const useDeviceStore = defineStore('device', () => {
  const deviceTypes = ref([])
  const deviceStatuses = ref([
    '在用',
    '闲置',
    '报废'
  ])

  // 从 API 加载设备类型
  const loadDeviceTypes = async () => {
    try {
      const res = await getAllDeviceTypes()
      deviceTypes.value = res.data.map(item => item.type_name)
    } catch (error) {
      console.error('加载设备类型失败:', error)
    }
  }

  // 初始化时加载
  loadDeviceTypes()

  return {
    deviceTypes,
    deviceStatuses,
    loadDeviceTypes
  }
})
