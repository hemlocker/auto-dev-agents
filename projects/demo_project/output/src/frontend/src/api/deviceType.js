import request from '@/utils/request'

// 获取设备类型列表
export function getDeviceTypeList(params) {
  return request({
    url: '/device-types',
    method: 'get',
    params
  })
}

// 获取所有设备类型（用于下拉选择器）
export function getAllDeviceTypes() {
  return request({
    url: '/device-types/all',
    method: 'get'
  })
}

// 获取设备类型详情
export function getDeviceTypeDetail(id) {
  return request({
    url: `/device-types/${id}`,
    method: 'get'
  })
}

// 新增设备类型
export function createDeviceType(data) {
  return request({
    url: '/device-types',
    method: 'post',
    data
  })
}

// 更新设备类型
export function updateDeviceType(id, data) {
  return request({
    url: `/device-types/${id}`,
    method: 'put',
    data
  })
}

// 删除设备类型
export function deleteDeviceType(id) {
  return request({
    url: `/device-types/${id}`,
    method: 'delete'
  })
}
