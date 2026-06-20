import request from '@/utils/request'

export function getAnomalyRecords(params) {
  return request({
    url: '/api/anomaly/records',
    method: 'get',
    params
  })
}

export function getAnomalyRecord(id) {
  return request({
    url: `/api/anomaly/records/${id}`,
    method: 'get'
  })
}

export function confirmAnomaly(id, data) {
  return request({
    url: `/api/anomaly/records/${id}/confirm`,
    method: 'post',
    data
  })
}

export function closeAnomaly(id, note) {
  return request({
    url: `/api/anomaly/records/${id}/close`,
    method: 'post',
    params: { note }
  })
}
