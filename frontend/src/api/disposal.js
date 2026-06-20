import request from '@/utils/request'

export function getDisposalRecords(params) {
  return request({
    url: '/api/disposal',
    method: 'get',
    params
  })
}

export function getDisposalRecord(id) {
  return request({
    url: `/api/disposal/${id}`,
    method: 'get'
  })
}

export function getDisposalSnapshotData(id) {
  return request({
    url: `/api/disposal/${id}/snapshot-data`,
    method: 'get'
  })
}

export function createDisposalRecord(data) {
  return request({
    url: '/api/disposal',
    method: 'post',
    data
  })
}
