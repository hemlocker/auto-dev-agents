import request from '@/utils/request'

// 下载导入模板
export function downloadImportTemplate() {
  return request({
    url: '/devices/import-template',
    method: 'get',
    responseType: 'blob'
  })
}

// 批量导入设备
export function importDevices(data) {
  return request({
    url: '/devices/import',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 导出设备数据
export function exportDevices(params) {
  return request({
    url: '/devices/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
