import request from '@/utils/request'

export function checkStopDischarge() {
  return request({
    url: '/api/instruction/stop-check',
    method: 'get'
  })
}

export function getInstructions(params) {
  return request({
    url: '/api/instruction',
    method: 'get',
    params
  })
}

export function getInstruction(id) {
  return request({
    url: `/api/instruction/${id}`,
    method: 'get'
  })
}

export function createInstruction(data) {
  return request({
    url: '/api/instruction',
    method: 'post',
    data
  })
}

export function issueInstruction(id) {
  return request({
    url: `/api/instruction/${id}/issue`,
    method: 'post'
  })
}

export function liftInstruction(id, data) {
  return request({
    url: `/api/instruction/${id}/lift`,
    method: 'post',
    data
  })
}

export function cancelInstruction(id) {
  return request({
    url: `/api/instruction/${id}/cancel`,
    method: 'post'
  })
}
