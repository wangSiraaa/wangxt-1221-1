import request from '@/utils/request'

export function getDischargePlans(params) {
  return request({
    url: '/api/discharge',
    method: 'get',
    params
  })
}

export function getDischargePlan(id) {
  return request({
    url: `/api/discharge/${id}`,
    method: 'get'
  })
}

export function createDischargePlan(data) {
  return request({
    url: '/api/discharge',
    method: 'post',
    data
  })
}

export function approveDischargePlan(id, data) {
  return request({
    url: `/api/discharge/${id}/approve`,
    method: 'post',
    data
  })
}

export function executeDischargePlan(id) {
  return request({
    url: `/api/discharge/${id}/execute`,
    method: 'post'
  })
}

export function completeDischargePlan(id, actualVolume) {
  return request({
    url: `/api/discharge/${id}/complete`,
    method: 'post',
    params: { actual_volume: actualVolume }
  })
}

export function cancelDischargePlan(id) {
  return request({
    url: `/api/discharge/${id}/cancel`,
    method: 'post'
  })
}
