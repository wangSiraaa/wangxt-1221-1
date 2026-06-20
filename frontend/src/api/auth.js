import request from '@/utils/request'

export function login(username, password) {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  return request({
    url: '/api/auth/login',
    method: 'post',
    data: formData
  })
}

export function getMe() {
  return request({
    url: '/api/auth/me',
    method: 'get'
  })
}
