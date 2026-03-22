import request from '@/utils/request'

// 获取设备标签数据
export function getLabelData(id) {
  return request({
    url: `/devices/${id}/label`,
    method: 'get'
  })
}

// 批量打印设备标签
export function printBatchLabels(data) {
  return request({
    url: '/devices/print-batch',
    method: 'post',
    data,
    responseType: 'blob'
  })
}
