import request from '@/utils/request'

export function getRetestDashboardSummary() {
  return request({
    url: '/api/retest/dashboard/summary',
    method: 'get'
  })
}

export function getRetestPlans(params) {
  return request({
    url: '/api/retest/plans',
    method: 'get',
    params
  })
}

export function getRetestPlan(id) {
  return request({
    url: `/api/retest/plans/${id}`,
    method: 'get'
  })
}

export function createRetestPlan(data) {
  return request({
    url: '/api/retest/plans',
    method: 'post',
    data
  })
}

export function updateRetestPlan(id, data) {
  return request({
    url: `/api/retest/plans/${id}`,
    method: 'put',
    data
  })
}

export function startRetest(id) {
  return request({
    url: `/api/retest/plans/${id}/start`,
    method: 'post'
  })
}

export function completeRetest(id, data) {
  return request({
    url: `/api/retest/plans/${id}/complete`,
    method: 'post',
    data
  })
}

export function cancelRetest(id) {
  return request({
    url: `/api/retest/plans/${id}/cancel`,
    method: 'post'
  })
}
