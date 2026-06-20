import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from './auth'
import router from '@/router'

const service = axios.create({
  baseURL: '/',
  timeout: 30000
})

service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('Response error:', error)
    if (error.response) {
      if (error.response.status === 401) {
        removeToken()
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      } else if (error.response.status === 403) {
        ElMessage.error('无权限执行此操作')
      } else if (error.response.data && error.response.data.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('请求失败，请稍后重试')
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default service
