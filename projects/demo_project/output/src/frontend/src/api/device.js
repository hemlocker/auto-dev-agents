import request from '@/utils/request'

// 获取设备列表
export function getDeviceList(params) {
  return request({
    url: '/devices',
    method: 'get',
    params
  })
}

// 获取设备详情
export function getDeviceDetail(id) {
  return request({
    url: `/devices/${id}`,
    method: 'get'
  })
}

// 新增设备
export function createDevice(data) {
  return request({
    url: '/devices',
    method: 'post',
    data
  })
}

// 更新设备
export function updateDevice(id, data) {
  return request({
    url: `/devices/${id}`,
    method: 'put',
    data
  })
}

// 删除设备
export function deleteDevice(id) {
  return request({
    url: `/devices/${id}`,
    method: 'delete'
  })
}
