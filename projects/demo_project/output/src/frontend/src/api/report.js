import request from '@/utils/request'

// 获取统计数据
export function getStatistics(params) {
  return request({
    url: '/reports/statistics',
    method: 'get',
    params
  })
}
