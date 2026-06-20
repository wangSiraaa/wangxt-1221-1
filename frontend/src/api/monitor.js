import request from '@/utils/request'

export function getMonitorTypes() {
  return request({
    url: '/api/monitor/types',
    method: 'get'
  })
}

export function getMonitorPoints(params) {
  return request({
    url: '/api/monitor/points',
    method: 'get',
    params
  })
}

export function getMonitorPoint(id) {
  return request({
    url: `/api/monitor/points/${id}`,
    method: 'get'
  })
}

export function createMonitorPoint(data) {
  return request({
    url: '/api/monitor/points',
    method: 'post',
    data
  })
}

export function createMonitorData(data) {
  return request({
    url: '/api/monitor/data',
    method: 'post',
    data
  })
}

export function batchCreateMonitorData(data) {
  return request({
    url: '/api/monitor/data/batch',
    method: 'post',
    data
  })
}

export function queryMonitorData(params) {
  return request({
    url: '/api/monitor/data',
    method: 'get',
    params
  })
}

export function getLatestMonitorData(params) {
  return request({
    url: '/api/monitor/data/latest',
    method: 'get',
    params
  })
}

export function getAlertSummary() {
  return request({
    url: '/api/monitor/alerts/summary',
    method: 'get'
  })
}
